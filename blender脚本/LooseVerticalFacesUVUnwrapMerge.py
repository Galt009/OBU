# ============================================================
# 脚本名称: LooseVerticalFacesUVUnwrapFloodFill
# 功能描述:
#   针对大量松散块（无顶底面的竖直面组），
#   使用 bmesh flood fill 一次性收集所有松散块的面索引，
#   然后逐岛进行三步展开（follow_active_quads → 缝合线 → unwrap）。
#   完全避免分离/合并物体，无 select_linked 开销，
#   适合 50000+ 松散块，不会卡死。
# 使用前提: 网格物体处于选中状态。
# 优化特性: 禁用全局撤销，详细进度显示，总计时。
# ============================================================

import bpy
import bmesh
import time

def unwrap_floodfill():
    obj = bpy.context.active_object
    if obj is None or obj.type != 'MESH':
        print("❌ 请选中一个网格物体")
        return

    start_time = time.perf_counter()

    # 禁用全局撤销
    original_undo = bpy.context.preferences.edit.use_global_undo
    bpy.context.preferences.edit.use_global_undo = False

    # 进入编辑模式
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    if not bm.faces:
        print("⚠️ 网格无面")
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.preferences.edit.use_global_undo = original_undo
        return

    # 确保有 UV 层
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")
    uv_layer = bm.loops.layers.uv.verify()

    # ---------- 使用 bmesh flood fill 收集所有松散块 ----------
    print("🔍 正在识别松散块...")
    visited = set()
    islands = []  # 每个元素是该岛屿所有面的列表

    for face in bm.faces:
        if face.index in visited:
            continue
        # 用栈进行深度优先遍历
        stack = [face]
        island_faces = []
        while stack:
            f = stack.pop()
            if f.index in visited:
                continue
            visited.add(f.index)
            island_faces.append(f)
            # 通过边的相邻面扩展
            for edge in f.edges:
                for adj_face in edge.link_faces:
                    if adj_face.index not in visited:
                        stack.append(adj_face)
        islands.append(island_faces)

    total_islands = len(islands)
    print(f"🔍 共找到 {total_islands} 个松散块（岛屿）")

    if total_islands == 0:
        print("⚠️ 没有找到任何面")
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.preferences.edit.use_global_undo = original_undo
        return

    # ---------- 逐岛处理 ----------
    processed = set()
    island_count = 0

    for island_faces in islands:
        island_count += 1

        # 取消所有选择
        for f in bm.faces:
            f.select = False

        # 选中当前岛屿的所有面
        for f in island_faces:
            f.select = True
        bm.faces.active = island_faces[0]
        bmesh.update_edit_mesh(obj.data)

        # ========== 步骤①：首次展开 ==========
        bpy.ops.uv.select_all(action='SELECT')
        try:
            bpy.ops.uv.follow_active_quads()
            first_method = "follow_active_quads"
        except RuntimeError:
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)
            first_method = "smart_project"
        print(f"   ↳ 第 {island_count}/{total_islands} 个岛屿：第一次展开完成（{first_method}）")

        # ========== 步骤②：基于 UV 边界生成缝合线 ==========
        # 清除该岛屿所有边的旧 seam
        for f in island_faces:
            for edge in f.edges:
                edge.seam = False
        bmesh.update_edit_mesh(obj.data)

        # 使用 Blender 内置操作符：根据当前 UV 岛边界标记缝合线
        bpy.ops.uv.seams_from_islands()

        # 统计缝合线数量（可选）
        island_edge_set = set()
        for f in island_faces:
            for e in f.edges:
                island_edge_set.add(e)
        seam_count = sum(1 for e in island_edge_set if e.seam)
        print(f"   ↳ 第 {island_count} 个岛屿：基于 UV 标记了 {seam_count} 条缝合线")

        # ========== 步骤③：基于缝合线二次展开 ==========
        bpy.ops.uv.select_all(action='SELECT')
        try:
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            second_method = "unwrap_with_seams"
        except RuntimeError:
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)
            second_method = "smart_project_fallback"

        print(f"   ✅ 第 {island_count}/{total_islands} 个岛屿最终方法：{second_method} (基于 {first_method})")

        # 取消选择
        for f in bm.faces:
            f.select = False

    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.preferences.edit.use_global_undo = original_undo

    # 总用时
    elapsed = time.perf_counter() - start_time
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    if minutes > 0:
        print(f"⏱️ 总用时: {minutes} 分 {seconds:.2f} 秒")
    else:
        print(f"⏱️ 总用时: {seconds:.2f} 秒")

    print("🎉 全部处理完成！")

# 执行
unwrap_floodfill()