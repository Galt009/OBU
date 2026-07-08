bl_info = {
    "name": "机场开发工具",
    "author": "Your Name",
    "version": (1, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > 机场开发工具",
    "description": "整合常用材质、顶点、纹理、网格及游标模式工具",
    "category": "Tool",
}

import bpy
import bmesh
from mathutils import Vector


# ==================== 1. 删除未使用材质槽（极速版） ====================
class OBJECT_OT_clean_unused_material_slots(bpy.types.Operator):
    bl_idname = "object.clean_unused_material_slots"
    bl_label = "删除未用材质槽"
    bl_description = "删除选中网格物体上未被任何面使用的材质槽（直接数据操作，极速）"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        processed = 0
        for obj in selected:
            if obj.type != 'MESH' or not obj.material_slots:
                continue

            mesh = obj.data
            if not mesh.polygons:
                # 没有多边形，直接清空材质槽
                mesh.materials.clear()
                processed += 1
                continue

            # 收集所有面使用的材质索引
            used_indices = set()
            for poly in mesh.polygons:
                used_indices.add(poly.material_index)

            # 从后往前删除未使用的材质槽
            for idx in range(len(mesh.materials) - 1, -1, -1):
                if idx not in used_indices:
                    mesh.materials.pop(index=idx)
            processed += 1

        self.report({'INFO'}, f"已清理 {processed} 个物体")
        return {'FINISHED'}


# ==================== 2. 设置透明（顶点颜色 → Alpha） ====================
class MATERIAL_OT_vertex_color_to_alpha(bpy.types.Operator):
    bl_idname = "material.vertex_color_to_alpha"
    bl_label = "设置透明"
    bl_description = "将选中物体的顶点颜色连接到原理化BSDF的Alpha通道"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = context.selected_objects
        if not objects:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        vcol_name = "Col"
        # 确保每个物体都有名为 "Col" 的顶点颜色层
        for obj in objects:
            if obj.type != 'MESH':
                continue
            mesh = obj.data
            if mesh.vertex_colors.active:
                if mesh.vertex_colors.active.name != vcol_name:
                    mesh.vertex_colors.active.name = vcol_name
            else:
                if len(mesh.vertex_colors) > 0:
                    if mesh.vertex_colors[0].name != vcol_name:
                        mesh.vertex_colors[0].name = vcol_name
                    mesh.vertex_colors.active = mesh.vertex_colors[0]
                else:
                    mesh.vertex_colors.new(name=vcol_name)

        # 收集材质
        materials = set()
        for obj in objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material:
                        materials.add(slot.material)

        for mat in materials:
            if mat.node_tree is None:
                mat.use_nodes = True
            node_tree = mat.node_tree

            # 查找或创建原理化BSDF
            principled = None
            for node in node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    principled = node
                    break
            if principled is None:
                principled = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
                output = node_tree.nodes.get('Material Output')
                if output is None:
                    output = node_tree.nodes.new(type='ShaderNodeOutputMaterial')
                node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])

            # 连接 Attribute 节点到 Alpha
            alpha_input = principled.inputs['Alpha']
            attr_node = None
            if alpha_input.is_linked:
                src = alpha_input.links[0].from_node
                if src.type == 'ATTRIBUTE' and src.attribute_name == vcol_name:
                    attr_node = src
            if attr_node is None:
                attr_node = node_tree.nodes.new(type='ShaderNodeAttribute')
                attr_node.attribute_name = vcol_name
                for link in alpha_input.links:
                    node_tree.links.remove(link)
                node_tree.links.new(attr_node.outputs['Color'], alpha_input)

        self.report({'INFO'}, "顶点颜色已连接至 Alpha")
        return {'FINISHED'}


# ==================== 3. 取消透明（断开 Alpha 连接） ====================
class MATERIAL_OT_vertex_color_clear_alpha(bpy.types.Operator):
    bl_idname = "material.vertex_color_clear_alpha"
    bl_label = "取消透明"
    bl_description = "断开选中物体材质中顶点颜色到Alpha的连接，恢复Alpha为1.0"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = context.selected_objects
        if not objects:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        materials = set()
        for obj in objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    if slot.material:
                        materials.add(slot.material)

        for mat in materials:
            if mat.node_tree is None:
                continue
            node_tree = mat.node_tree
            # 查找连接到 Alpha 的 Attribute 节点
            attr_nodes = []
            for node in node_tree.nodes:
                if node.type == 'ATTRIBUTE' and node.attribute_name == 'Col':
                    # 检查是否连接到某个 BSDF 的 Alpha
                    for output in node.outputs:
                        if output.links:
                            for link in output.links:
                                if link.to_socket.name == 'Alpha' and link.to_node.type == 'BSDF_PRINCIPLED':
                                    attr_nodes.append(node)
                                    break
            for node in attr_nodes:
                # 断开所有连接
                for output in node.outputs:
                    for link in output.links:
                        node_tree.links.remove(link)
                # 删除节点
                node_tree.nodes.remove(node)

            # 将原理化BSDF的Alpha设为1.0
            for node in node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    node.inputs['Alpha'].default_value = 1.0

        self.report({'INFO'}, "已断开顶点颜色与Alpha的连接")
        return {'FINISHED'}


# ==================== 4. 设置顶点颜色（支持颜色选择） ====================
class OBJECT_OT_set_vertex_color(bpy.types.Operator):
    bl_idname = "object.set_vertex_color"
    bl_label = "设置顶点颜色"
    bl_description = "将选中物体的顶点颜色设为指定的颜色（RGBA）"
    bl_options = {'REGISTER', 'UNDO'}

    color: bpy.props.FloatVectorProperty(
        name="颜色",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(0.0, 0.0, 0.0, 1.0),
        description="要设置的顶点颜色"
    )

    def execute(self, context):
        objects = context.selected_objects
        if not objects:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        # 从场景属性读取颜色（面板中调整的值）
        color = context.scene.vertex_color_value
        count = 0
        for obj in objects:
            if obj.type != 'MESH':
                continue
            mesh = obj.data
            vcol = mesh.vertex_colors.active
            if vcol is None:
                vcol = mesh.vertex_colors.new(name="Col")
            # 批量写入（极速）
            total = len(vcol.data)
            if total == 0:
                continue
            flat = [color[0], color[1], color[2], color[3]] * total
            vcol.data.foreach_set("color", flat)
            count += 1

        self.report({'INFO'}, f"已将 {count} 个物体的顶点颜色设为 ({color[0]:.2f}, {color[1]:.2f}, {color[2]:.2f}, {color[3]:.2f})")
        return {'FINISHED'}


# ==================== 5. Space + Relax (3次) ====================
class MESH_OT_looptools_space_relax(bpy.types.Operator):
    bl_idname = "mesh.looptools_space_relax"
    bl_label = "Space + Relax (×3)"
    bl_description = "运行 LoopTools 的 Space 然后 Relax（3次迭代）"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not hasattr(bpy.ops.mesh, 'looptools_space'):
            self.report({'ERROR'}, "LoopTools 插件未启用，请在偏好设置中启用")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.looptools_space()
        bpy.ops.mesh.looptools_relax(iterations='3')
        self.report({'INFO'}, "已执行 Space 和 Relax（3次）")
        return {'FINISHED'}


# ==================== 6. 堆叠UV岛到中心（0.5,0.5）- 基于UV边连通性 ====================
class MESH_OT_stack_uv_islands(bpy.types.Operator):
    bl_idname = "mesh.stack_uv_islands"
    bl_label = "堆叠UV岛(0.5)"
    bl_description = "将选中面所属的UV岛中心平移到(0.5,0.5)（基于UV边连通性，精准识别UV岛）"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'EDIT_MESH':
            self.report({'WARNING'}, "请进入编辑模式（面选择）")
            return {'CANCELLED'}

        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "活动物体不是网格")
            return {'CANCELLED'}

        mesh = obj.data
        if not mesh.uv_layers.active:
            self.report({'INFO'}, f"跳过 '{obj.name}'：无活动UV层")
            return {'CANCELLED'}

        target = Vector((0.5, 0.5))
        bm = bmesh.from_edit_mesh(mesh)
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            self.report({'ERROR'}, "无法获取UV层")
            return {'CANCELLED'}

        selected_faces = [f for f in bm.faces if f.select]
        if not selected_faces:
            self.report({'WARNING'}, "请至少选中一个面")
            return {'CANCELLED'}

        # ---- 构建 UV 连通图（基于共享边的 UV 坐标匹配） ----
        # 将每个面的边和对应的UV顶点坐标对存储起来，方便比较
        # 结构：{edge: [(face, uv1, uv2), ...]} 其中 uv1, uv2 是向量
        edge_faces = {}
        for face in bm.faces:
            # 获取面的所有循环（loop）
            loops = face.loops
            for i in range(len(loops)):
                loop1 = loops[i]
                loop2 = loops[(i + 1) % len(loops)]
                # 获取该边的两个顶点
                v1 = loop1.vert
                v2 = loop2.vert
                # 获取对应的UV坐标（注意顺序）
                uv1 = loop1[uv_layer].uv.copy()
                uv2 = loop2[uv_layer].uv.copy()
                # 用边（无序）作为键
                edge_key = tuple(sorted((v1.index, v2.index)))
                edge_faces.setdefault(edge_key, []).append((face, uv1, uv2))

        # 并查集合并UV连通的面
        all_faces = list(bm.faces)
        parent = {face: face for face in all_faces}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        # 对于每条边，检查所有连接的面，如果UV坐标匹配，则合并
        for edge_key, face_data in edge_faces.items():
            if len(face_data) < 2:
                continue
            # 两两比较
            for i in range(len(face_data)):
                for j in range(i + 1, len(face_data)):
                    face1, uv1_a, uv1_b = face_data[i]
                    face2, uv2_a, uv2_b = face_data[j]
                    # 检查UV坐标是否匹配（考虑顺序可能相反）
                    # 比较 (uv1_a, uv1_b) 与 (uv2_a, uv2_b) 或 (uv2_b, uv2_a)
                    match1 = (uv1_a - uv2_a).length < 1e-5 and (uv1_b - uv2_b).length < 1e-5
                    match2 = (uv1_a - uv2_b).length < 1e-5 and (uv1_b - uv2_a).length < 1e-5
                    if match1 or match2:
                        union(face1, face2)

        # 收集选中面所属的根
        selected_roots = set()
        for f in selected_faces:
            selected_roots.add(find(f))

        # 收集需要移动的岛（每个根对应一个岛的所有面）
        islands = []
        for root in selected_roots:
            island_faces = [f for f in all_faces if find(f) == root]
            islands.append(island_faces)

        if not islands:
            self.report({'INFO'}, "没有需要移动的UV岛")
            return {'FINISHED'}

        # ---- 平移每个岛到目标中心 ----
        for island in islands:
            uv_coords = []
            for face in island:
                for loop in face.loops:
                    uv = loop[uv_layer].uv
                    uv_coords.append(Vector((uv.x, uv.y)))
            if not uv_coords:
                continue
            center = sum(uv_coords, Vector((0.0, 0.0))) / len(uv_coords)
            offset = target - center
            for face in island:
                for loop in face.loops:
                    loop[uv_layer].uv.x += offset.x
                    loop[uv_layer].uv.y += offset.y

        bmesh.update_edit_mesh(mesh)
        mesh.update()
        self.report({'INFO'}, f"已堆叠 {len(islands)} 个UV岛到(0.5,0.5)")
        return {'FINISHED'}


# ==================== 7. 纹理扩展模式 → EXTEND ====================
class MATERIAL_OT_set_texture_extend_all(bpy.types.Operator):
    bl_idname = "material.set_texture_extend_all"
    bl_label = "所有材质纹理→扩展"
    bl_description = "将场景中所有材质的所有图像纹理节点的扩展模式改为 EXTEND"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        modified = 0
        for mat in bpy.data.materials:
            if mat and mat.use_nodes and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        if node.extension != 'EXTEND':
                            node.extension = 'EXTEND'
                            modified += 1
        self.report({'INFO'}, f"已修改 {modified} 个纹理节点为 EXTEND")
        return {'FINISHED'}


class MATERIAL_OT_set_texture_extend_selected(bpy.types.Operator):
    bl_idname = "material.set_texture_extend_selected"
    bl_label = "选中材质纹理→扩展"
    bl_description = "将选中物体所用材质的所有图像纹理节点扩展模式改为 EXTEND"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = context.selected_objects
        if not objects:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        modified = 0
        for obj in objects:
            if obj.type == 'MESH':
                for slot in obj.material_slots:
                    mat = slot.material
                    if mat and mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                if node.extension != 'EXTEND':
                                    node.extension = 'EXTEND'
                                    modified += 1
        self.report({'INFO'}, f"已修改 {modified} 个纹理节点为 EXTEND")
        return {'FINISHED'}


# ==================== 8. 材质转独享 (SU) ====================
class MATERIAL_OT_make_single_user(bpy.types.Operator):
    bl_idname = "material.make_single_user"
    bl_label = "转独享材质 (SU)"
    bl_description = "将选中物体共享的材质复制为独享副本（后缀 .SU）"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        processed_objs = 0
        for obj in selected:
            if obj.type != 'MESH' or not obj.material_slots:
                continue

            used_mats = {slot.material for slot in obj.material_slots if slot.material}
            if not used_mats:
                continue

            mat_map = {}
            need_copy = False
            for mat in used_mats:
                if mat.users > 1:
                    need_copy = True
                    new_mat = mat.copy()
                    new_mat.name = mat.name + ".SU"
                    mat_map[mat] = new_mat

            if not need_copy:
                continue

            for slot in obj.material_slots:
                if slot.material and slot.material in mat_map:
                    slot.material = mat_map[slot.material]

            processed_objs += 1

        self.report({'INFO'}, f"处理完成，共 {processed_objs} 个物体材质转为独享")
        return {'FINISHED'}


# ==================== 9. 游标模式切换 ====================
class SCENE_OT_toggle_cursor_mode(bpy.types.Operator):
    bl_idname = "scene.toggle_cursor_mode"
    bl_label = "切换游标模式"
    bl_description = "切换变换坐标系和轴心点：游标模式（游标/游标）或默认模式（全局/质心点）"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        tool_settings = context.tool_settings

        current_orientation = scene.transform_orientation_slots[0].type
        current_pivot = tool_settings.transform_pivot_point

        if current_orientation == 'CURSOR' and current_pivot == 'CURSOR':
            scene.transform_orientation_slots[0].type = 'GLOBAL'
            tool_settings.transform_pivot_point = 'MEDIAN_POINT'
            self.report({'INFO'}, "已切换到默认模式（全局/质心点）")
        else:
            scene.transform_orientation_slots[0].type = 'CURSOR'
            tool_settings.transform_pivot_point = 'CURSOR'
            self.report({'INFO'}, "已切换到游标模式（游标/游标）")

        context.area.tag_redraw()
        return {'FINISHED'}


# ==================== 面板 ====================
class VIEW3D_PT_airport_dev_tools(bpy.types.Panel):
    bl_label = "机场开发工具"
    bl_idname = "VIEW3D_PT_airport_dev_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "机场开发工具"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        tool_settings = context.tool_settings

        # ----- 游标模式 -----
        layout.label(text="游标模式", icon='PIVOT_CURSOR')
        orientation = scene.transform_orientation_slots[0].type
        pivot = tool_settings.transform_pivot_point
        if orientation == 'CURSOR' and pivot == 'CURSOR':
            mode_text = "当前：游标模式"
            mode_icon = 'PIVOT_CURSOR'
        else:
            mode_text = "当前：默认模式"
            mode_icon = 'PIVOT_MEDIAN'
        row = layout.row(align=True)
        row.label(text=mode_text, icon=mode_icon)
        row.operator("scene.toggle_cursor_mode", text="切换", icon='FILE_REFRESH')
        box = layout.box()
        col = box.column(align=True)
        col.label(text="变换坐标系: " + orientation.title())
        col.label(text="轴心点: " + pivot.title().replace('_', ' '))
        layout.separator()

        # ----- 材质工具 -----
        layout.label(text="材质工具", icon='MATERIAL')
        row = layout.row(align=True)
        row.operator("material.make_single_user", text="转独享(SU)")
        row.operator("object.clean_unused_material_slots", text="清未用槽")
        layout.separator()

        # ----- 顶点颜色工具 -----
        layout.label(text="顶点颜色工具", icon='VERTEXSEL')
        row = layout.row(align=True)
        row.operator("material.vertex_color_to_alpha", text="设置透明")
        row.operator("material.vertex_color_clear_alpha", text="取消透明")
        row = layout.row(align=True)
        row.prop(scene, "vertex_color_value", text="")
        row.operator("object.set_vertex_color", text="设置顶点颜色")
        layout.separator()

        # ----- 纹理工具 -----
        layout.label(text="纹理扩展模式", icon='TEXTURE')
        row = layout.row(align=True)
        row.operator("material.set_texture_extend_all", text="全部→扩展")
        row.operator("material.set_texture_extend_selected", text="选中→扩展")
        layout.separator()

        # ----- 网格工具 -----
        layout.label(text="网格工具", icon='MESH_DATA')
        layout.operator("mesh.looptools_space_relax", text="Space + Relax (×3)", icon='MOD_SMOOTH')
        layout.operator("mesh.stack_uv_islands", text="堆叠UV岛(0.5)", icon='UV')


# ==================== 注册与注销 ====================
classes = (
    OBJECT_OT_clean_unused_material_slots,
    MATERIAL_OT_vertex_color_to_alpha,
    MATERIAL_OT_vertex_color_clear_alpha,
    OBJECT_OT_set_vertex_color,
    MESH_OT_looptools_space_relax,
    MESH_OT_stack_uv_islands,
    MATERIAL_OT_set_texture_extend_all,
    MATERIAL_OT_set_texture_extend_selected,
    MATERIAL_OT_make_single_user,
    SCENE_OT_toggle_cursor_mode,
    VIEW3D_PT_airport_dev_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # 添加场景属性用于存储顶点颜色值
    bpy.types.Scene.vertex_color_value = bpy.props.FloatVectorProperty(
        name="顶点颜色",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(0.0, 0.0, 0.0, 1.0),
        description="设置顶点颜色时使用的颜色"
    )

def unregister():
    # 删除场景属性
    del bpy.types.Scene.vertex_color_value
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()