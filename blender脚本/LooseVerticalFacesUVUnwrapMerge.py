# ============================================================
# 脚本名称: LooseVerticalFacesUVUnwrapMerge (带缝合线优化)
# 英文名: LooseVerticalFacesUVUnwrapWithSeams
# 
# 功能描述:
#   针对由多个独立竖直面（松散块）组成的网格模型（无顶底面），
#   对每个松散块进行以下三步处理：
#     1. 首先尝试沿活动四边面展开 (follow_active_quads)，
#        若失败则降级为智能展开 (smart_project)。
#     2. 根据展开后的 UV 边界（即 UV 岛边缘）自动生成缝合线，
#        包括外边界和因 UV 链断裂而产生的内部边。
#     3. 基于缝合线重新执行标准角度展开 (unwrap)，
#        使每个松散块的 UV 岛边界清晰、拉伸最小。
# 
# 使用前提:
#   - 所有面必须为四边形，否则第一步会降级为 smart_project。
#   - 网格物体处于选中状态。
# 
# 优化特性:
#   - 运行期间自动禁用全局撤销，大幅降低内存占用，防止崩溃。
#   - 在系统控制台显示详细处理进度（当前块/总块数，含面数、缝合线数量）。
#   - 显示总用时（分/秒）。
# 
# 作者: (用户定制)
# 日期: 2026-06-29
# ============================================================
import bpy
import bmesh
import time

def unwrap_loose_islands():
    obj = bpy.context.active_object
    if obj is None or obj.type != 'MESH':
        print("❌ 请选中一个网格物体")
        return

    start_time = time.perf_counter()

    original_undo = bpy.context.preferences.edit.use_global_undo
    bpy.context.preferences.edit.use_global_undo = False

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

    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name="UVMap")

    # 统计松散块（岛屿）总数
    temp_processed = set()
    total_islands = 0
    for f in bm.faces:
        if f.index not in temp_processed:
            total_islands += 1
            bpy.ops.mesh.select_all(action='DESELECT')
            f.select = True
            bpy.ops.mesh.select_linked()
            for ff in bm.faces:
                if ff.select:
                    temp_processed.add(ff.index)
            bpy.ops.mesh.select_all(action='DESELECT')
    print(f"🔍 共找到 {total_islands} 个松散块（岛屿）")

    processed = set()
    island_count = 0

    for face in bm.faces:
        if face.index in processed:
            continue

        island_count += 1
        # 选中当前岛屿
        bpy.ops.mesh.select_all(action='DESELECT')
        face.select = True
        bpy.ops.mesh.select_linked()
        bm.faces.active = face
        bmesh.update_edit_mesh(obj.data)

        # ========== 步骤①：首次展开 ==========
        bpy.ops.uv.select_all(action='SELECT')
        try:
            bpy.ops.uv.follow_active_quads()
            first_method = "follow_active_quads"
        except RuntimeError:
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)
            first_method = "smart_project"
        print(f"   ↳ 第 {island_count} 个岛屿：第一次展开完成（{first_method}）")

        # ========== 步骤②：基于 UV 岛屿边界生成缝合线 ==========
        # 清除该岛屿现有的缝合线（防止残留）
        selected_faces = {f for f in bm.faces if f.select}
        for f in selected_faces:
            for edge in f.edges:
                edge.seam = False
        bmesh.update_edit_mesh(obj.data)

        # 使用 Blender 内置操作符，根据 UV 岛边界标记缝合线
        bpy.ops.uv.seams_from_islands()

        # 统计标记了多少条缝合线（可选）
        seam_count = sum(1 for e in bm.edges if e.seam)
        print(f"   ↳ 第 {island_count} 个岛屿：基于 UV 标记了 {seam_count} 条缝合线")

        # ========== 步骤③：基于缝合线二次展开 ==========
        bpy.ops.uv.select_all(action='SELECT')
        try:
            bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
            second_method = "unwrap_with_seams"
        except RuntimeError:
            bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)
            second_method = "smart_project_fallback"

        # 记录已处理面
        for f in bm.faces:
            if f.select:
                processed.add(f.index)

        print(f"   ✅ 第 {island_count}/{total_islands} 个岛屿最终方法：{second_method} (基于 {first_method})")

        bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.preferences.edit.use_global_undo = original_undo

    elapsed = time.perf_counter() - start_time
    minutes = int(elapsed // 60)
    seconds = elapsed % 60
    if minutes > 0:
        print(f"⏱️ 总用时: {minutes} 分 {seconds:.2f} 秒")
    else:
        print(f"⏱️ 总用时: {seconds:.2f} 秒")

    print("🎉 全部处理完成！")

# 执行
unwrap_loose_islands()