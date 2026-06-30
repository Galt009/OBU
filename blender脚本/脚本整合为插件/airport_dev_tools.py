bl_info = {
    "name": "机场开发工具",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > 机场开发工具",
    "description": "整合常用材质、顶点、纹理、网格及游标模式工具",
    "category": "Tool",
}

import bpy


# ==================== 1. 删除未使用材质槽 ====================
class OBJECT_OT_clean_unused_material_slots(bpy.types.Operator):
    bl_idname = "object.clean_unused_material_slots"
    bl_label = "删除未用材质槽"
    bl_description = "删除选中网格物体上未被任何面使用的材质槽"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        processed = 0
        for obj in selected:
            if obj.type != 'MESH':
                continue
            # 保存当前选择状态
            original_selected = context.selected_objects[:]
            original_active = context.view_layer.objects.active

            # 仅选中当前物体
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            # 进入编辑模式再退出，刷新材质分配
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.mode_set(mode='OBJECT')

            # 删除未使用材质槽
            try:
                bpy.ops.object.material_slot_remove_unused()
                processed += 1
            except Exception as e:
                self.report({'ERROR'}, f"清理 {obj.name} 失败: {e}")

            # 恢复选择
            bpy.ops.object.select_all(action='DESELECT')
            for o in original_selected:
                o.select_set(True)
            context.view_layer.objects.active = original_active

        self.report({'INFO'}, f"已清理 {processed} 个物体")
        return {'FINISHED'}


# ==================== 2. 顶点颜色转 Alpha ====================
class MATERIAL_OT_vertex_color_to_alpha(bpy.types.Operator):
    bl_idname = "material.vertex_color_to_alpha"
    bl_label = "顶点颜色控透明"
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


# ==================== 3. 顶点颜色设为黑色 ====================
class OBJECT_OT_set_vertex_color_black(bpy.types.Operator):
    bl_idname = "object.set_vertex_color_black"
    bl_label = "顶点颜色归零（黑）"
    bl_description = "将选中物体的顶点颜色全部设为纯黑色（RGBA: 0,0,0,1）"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objects = context.selected_objects
        if not objects:
            self.report({'WARNING'}, "没有选中任何物体")
            return {'CANCELLED'}

        count = 0
        for obj in objects:
            if obj.type != 'MESH':
                continue
            mesh = obj.data
            vcol = mesh.vertex_colors.active
            if vcol is None:
                vcol = mesh.vertex_colors.new(name="Col")
            for loop in vcol.data:
                loop.color = (0.0, 0.0, 0.0, 1.0)
            count += 1

        self.report({'INFO'}, f"已将 {count} 个物体的顶点颜色设为黑色")
        return {'FINISHED'}


# ==================== 4. Space + Relax (3次) ====================
class MESH_OT_looptools_space_relax(bpy.types.Operator):
    bl_idname = "mesh.looptools_space_relax"
    bl_label = "Space + Relax (×3)"
    bl_description = "运行 LoopTools 的 Space 然后 Relax（3次迭代）"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 检查 LoopTools 是否启用
        if not hasattr(bpy.ops.mesh, 'looptools_space'):
            self.report({'ERROR'}, "LoopTools 插件未启用，请在偏好设置中启用")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.looptools_space()
        bpy.ops.mesh.looptools_relax(iterations='3')
        # 保持编辑模式，方便继续调整
        self.report({'INFO'}, "已执行 Space 和 Relax（3次）")
        return {'FINISHED'}


# ==================== 5. 纹理扩展模式 → EXTEND ====================
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


# ==================== 6. 材质转独享 (SU) ====================
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


# ==================== 7. 游标模式切换 ====================
class SCENE_OT_toggle_cursor_mode(bpy.types.Operator):
    bl_idname = "scene.toggle_cursor_mode"
    bl_label = "切换游标模式"
    bl_description = "切换变换坐标系和轴心点：游标模式（游标/游标）或默认模式（全局/质心点）"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        tool_settings = context.tool_settings

        # 获取当前变换坐标系（第一个槽）
        current_orientation = scene.transform_orientation_slots[0].type
        current_pivot = tool_settings.transform_pivot_point

        # 判断当前是否为游标模式（两者均为 CURSOR）
        if current_orientation == 'CURSOR' and current_pivot == 'CURSOR':
            # 切换到默认模式
            scene.transform_orientation_slots[0].type = 'GLOBAL'
            tool_settings.transform_pivot_point = 'MEDIAN_POINT'
            self.report({'INFO'}, "已切换到默认模式（全局/质心点）")
        else:
            # 切换到游标模式
            scene.transform_orientation_slots[0].type = 'CURSOR'
            tool_settings.transform_pivot_point = 'CURSOR'
            self.report({'INFO'}, "已切换到游标模式（游标/游标）")

        # 强制刷新界面
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
        # 获取当前设置
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
        # 显示详细设置（可选）
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

        # ----- 顶点颜色工具 -----
        layout.separator()
        layout.label(text="顶点颜色工具", icon='VERTEXSEL')
        row = layout.row(align=True)
        row.operator("material.vertex_color_to_alpha", text="控透明")
        row.operator("object.set_vertex_color_black", text="归零黑")

        # ----- 纹理工具 -----
        layout.separator()
        layout.label(text="纹理扩展模式", icon='TEXTURE')
        row = layout.row(align=True)
        row.operator("material.set_texture_extend_all", text="全部→扩展")
        row.operator("material.set_texture_extend_selected", text="选中→扩展")

        # ----- 网格工具 -----
        layout.separator()
        layout.label(text="网格工具", icon='MESH_DATA')
        layout.operator("mesh.looptools_space_relax", text="Space + Relax (×3)", icon='MOD_SMOOTH')


# ==================== 注册 ====================
classes = (
    OBJECT_OT_clean_unused_material_slots,
    MATERIAL_OT_vertex_color_to_alpha,
    OBJECT_OT_set_vertex_color_black,
    MESH_OT_looptools_space_relax,
    MATERIAL_OT_set_texture_extend_all,
    MATERIAL_OT_set_texture_extend_selected,
    MATERIAL_OT_make_single_user,
    SCENE_OT_toggle_cursor_mode,
    VIEW3D_PT_airport_dev_tools,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()