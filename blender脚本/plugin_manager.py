bl_info = {
    "name": "♥ 插件管理器",
    "author": "AI Assistant",
    "version": (3, 6),
    "blender": (4, 2, 0),
    "location": "View3D > N Panel > ♥",
    "description": "分组折叠管理，支持分组内批量启用/禁用插件",
    "category": "System",
}

import bpy
import addon_utils
from bpy.types import Panel, Operator, PropertyGroup, UIList
from bpy.props import StringProperty, IntProperty, CollectionProperty, BoolProperty

# ------------------------------------------------------------
# 数据属性
# ------------------------------------------------------------
class GroupItem(PropertyGroup):
    name: StringProperty(name="分组名", default="新分组")
    is_open: BoolProperty(default=True)

class AddonItem(PropertyGroup):
    name: StringProperty()
    module: StringProperty()
    is_enabled: BoolProperty()
    group_name: StringProperty(default="未分组")

# ------------------------------------------------------------
# 刷新插件列表
# ------------------------------------------------------------
class ADDON_OT_refresh_list(Operator):
    bl_idname = "addon.refresh_list"
    bl_label = "刷新列表"

    def execute(self, context):
        scene = context.scene
        existing_groups = {item.module: item.group_name for item in scene.addon_list}
        scene.addon_list.clear()
        addon_utils.modules(refresh=True)
        for mod in addon_utils.modules():
            mod_name = mod.__name__
            loaded, enabled = addon_utils.check(mod_name)
            info = getattr(mod, 'bl_info', {})
            display_name = info.get('name', mod_name)
            item = scene.addon_list.add()
            item.name = display_name
            item.module = mod_name
            item.is_enabled = enabled
            item.group_name = existing_groups.get(mod_name, "未分组")
        # 确保“未分组”存在
        if not any(g.name == "未分组" for g in scene.addon_groups):
            g = scene.addon_groups.add()
            g.name = "未分组"
        return {'FINISHED'}

# ------------------------------------------------------------
# 切换单个插件
# ------------------------------------------------------------
class ADDON_OT_toggle_addon(Operator):
    bl_idname = "addon.toggle_item"
    bl_label = "切换"
    module: StringProperty()

    def execute(self, context):
        loaded, enabled = addon_utils.check(self.module)
        if enabled:
            bpy.ops.preferences.addon_disable(module=self.module)
        else:
            bpy.ops.preferences.addon_enable(module=self.module)
        bpy.ops.addon.refresh_list()
        return {'FINISHED'}

# ------------------------------------------------------------
# 批量启用/禁用分组内所有插件
# ------------------------------------------------------------
class ADDON_OT_enable_group_all(Operator):
    bl_idname = "addon.enable_group_all"
    bl_label = "启用全部"
    bl_description = "启用当前分组内的所有插件"
    group_name: StringProperty()

    def execute(self, context):
        scene = context.scene
        for item in scene.addon_list:
            if item.group_name == self.group_name:
                loaded, enabled = addon_utils.check(item.module)
                if not enabled:
                    bpy.ops.preferences.addon_enable(module=item.module)
        bpy.ops.addon.refresh_list()
        self.report({'INFO'}, f"已启用分组 '{self.group_name}' 的全部插件")
        return {'FINISHED'}

class ADDON_OT_disable_group_all(Operator):
    bl_idname = "addon.disable_group_all"
    bl_label = "禁用全部"
    bl_description = "禁用当前分组内的所有插件"
    group_name: StringProperty()

    def execute(self, context):
        scene = context.scene
        for item in scene.addon_list:
            if item.group_name == self.group_name:
                loaded, enabled = addon_utils.check(item.module)
                if enabled:
                    bpy.ops.preferences.addon_disable(module=item.module)
        bpy.ops.addon.refresh_list()
        self.report({'INFO'}, f"已禁用分组 '{self.group_name}' 的全部插件")
        return {'FINISHED'}

# ------------------------------------------------------------
# 分组管理
# ------------------------------------------------------------
class ADDON_OT_add_group(Operator):
    bl_idname = "addon.add_group"
    bl_label = "添加分组"
    bl_description = "创建新分组（自动去重）"

    def execute(self, context):
        groups = context.scene.addon_groups
        base = "新分组"
        new = base
        c = 1
        while any(g.name == new for g in groups):
            new = f"{base}{c}"
            c += 1
        groups.add().name = new
        context.scene.active_group_index = len(groups) - 1
        self.report({'INFO'}, f"已添加分组: {new}")
        return {'FINISHED'}

class ADDON_OT_remove_group(Operator):
    bl_idname = "addon.remove_group"
    bl_label = "删除分组"
    bl_description = "删除当前选中的分组（插件移至“未分组”）"

    def execute(self, context):
        scene = context.scene
        groups = scene.addon_groups
        idx = scene.active_group_index
        if idx < 0 or idx >= len(groups):
            self.report({'WARNING'}, "请先单击选中一个分组")
            return {'CANCELLED'}
        gname = groups[idx].name
        if gname == "未分组":
            self.report({'WARNING'}, "不能删除'未分组'")
            return {'CANCELLED'}
        for item in scene.addon_list:
            if item.group_name == gname:
                item.group_name = "未分组"
        groups.remove(idx)
        scene.active_group_index = min(idx, len(groups)-1)
        self.report({'INFO'}, f"已删除分组 '{gname}'")
        return {'FINISHED'}

class ADDON_OT_rename_group(Operator):
    bl_idname = "addon.rename_group"
    bl_label = "重命名分组"
    bl_description = "重命名当前选中的分组"
    new_name: StringProperty(name="新名称")

    def execute(self, context):
        scene = context.scene
        idx = scene.active_group_index
        if idx < 0 or idx >= len(scene.addon_groups):
            self.report({'WARNING'}, "请先单击选中一个分组")
            return {'CANCELLED'}
        old = scene.addon_groups[idx].name
        if old == "未分组":
            self.report({'WARNING'}, "不能重命名'未分组'")
            return {'CANCELLED'}
        new = self.new_name.strip()
        if not new:
            self.report({'WARNING'}, "名称不能为空")
            return {'CANCELLED'}
        if any(g.name == new for g in scene.addon_groups if g.name != old):
            self.report({'WARNING'}, "分组名已存在")
            return {'CANCELLED'}
        scene.addon_groups[idx].name = new
        for item in scene.addon_list:
            if item.group_name == old:
                item.group_name = new
        scene.rename_group_input = ""
        self.report({'INFO'}, f"已重命名为 '{new}'")
        return {'FINISHED'}

class ADDON_OT_move_group(Operator):
    bl_idname = "addon.move_group"
    bl_label = "移动分组"
    direction: bpy.props.EnumProperty(items=[('UP','上移',''),('DOWN','下移','')])

    def execute(self, context):
        scene = context.scene
        groups = scene.addon_groups
        idx = scene.active_group_index
        target = idx - 1 if self.direction == 'UP' else idx + 1
        if target < 0 or target >= len(groups):
            return {'CANCELLED'}
        groups.move(idx, target)
        scene.active_group_index = target
        return {'FINISHED'}

# ------------------------------------------------------------
# 折叠切换
# ------------------------------------------------------------
class ADDON_OT_toggle_group(Operator):
    bl_idname = "addon.toggle_group"
    bl_label = "折叠/展开分组"
    group_index: IntProperty()

    def execute(self, context):
        groups = context.scene.addon_groups
        if 0 <= self.group_index < len(groups):
            groups[self.group_index].is_open = not groups[self.group_index].is_open
        return {'FINISHED'}

# ------------------------------------------------------------
# UIList 自定义（去掉图标，纯文本，确保可见）
# ------------------------------------------------------------
class ADDON_UL_groups(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # 只显示纯文本，不添加图标，以免遮挡文字
        row = layout.row()
        row.label(text=item.name)
        if item.name == "未分组":
            row.label(text="(默认)")

# ------------------------------------------------------------
# 主面板
# ------------------------------------------------------------
class VIEW3D_PT_plugin_manager(Panel):
    bl_label = "♥"
    bl_idname = "VIEW3D_PT_plugin_manager"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "♥"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        groups = scene.addon_groups

        # ----- 顶部工具栏 -----
        row = layout.row(align=True)
        row.operator("addon.add_group", text="添加分组", icon='ADD')
        row.operator("addon.remove_group", text="删除分组", icon='REMOVE')
        row.operator("addon.refresh_list", text="刷新", icon='FILE_REFRESH')

        row = layout.row(align=True)
        row.prop(scene, "rename_group_input", text="")
        op = row.operator("addon.rename_group", text="重命名", icon='OUTLINER_DATA_GP_LAYER')
        op.new_name = scene.rename_group_input

        col = layout.column(align=True)
        row = col.row(align=True)
        op_up = row.operator("addon.move_group", text="", icon='TRIA_UP')
        op_up.direction = 'UP'
        op_down = row.operator("addon.move_group", text="", icon='TRIA_DOWN')
        op_down.direction = 'DOWN'

        layout.separator()

        # ----- 显示分组总数和当前选中 -----
        total = len(groups)
        row = layout.row()
        row.label(text=f"分组总数: {total}", icon='INFO')
        if total > 0 and 0 <= scene.active_group_index < total:
            current = groups[scene.active_group_index].name
            row.label(text=f"当前选中: {current}")
        else:
            row.label(text="当前选中: 无")

        # ----- 分组列表（单击选中）-----
        layout.template_list("ADDON_UL_groups", "", scene, "addon_groups", scene, "active_group_index", rows=3)

        # 如果列表为空但总数不为0，给出提示
        if total > 0:
            layout.label(text="（列表可能未刷新，请点击“刷新”或重开面板）", icon='ERROR')

        layout.separator()

        # ----- 遍历分组（折叠显示）-----
        for g_idx, group in enumerate(groups):
            box = layout.box()
            row = box.row(align=True)
            if group.is_open:
                icon = 'DISCLOSURE_TRI_DOWN'
            else:
                icon = 'DISCLOSURE_TRI_RIGHT'
            op = row.operator("addon.toggle_group", text=group.name, icon=icon, emboss=False)
            op.group_index = g_idx
            count = sum(1 for item in scene.addon_list if item.group_name == group.name)
            row.label(text=f"({count})")

            if count > 0:
                op_enable = row.operator("addon.enable_group_all", text="", icon='PLAY')
                op_enable.group_name = group.name
                op_disable = row.operator("addon.disable_group_all", text="", icon='PAUSE')
                op_disable.group_name = group.name
            else:
                row.label(text="  ")
                row.label(text="  ")

            if not group.is_open:
                continue

            addons_in_group = [item for item in scene.addon_list if item.group_name == group.name]
            if not addons_in_group:
                row = box.row()
                row.label(text="（没有插件）", icon='INFO')
                continue

            for item in addons_in_group:
                row = box.row(align=True)
                row.label(text=item.name)
                if item.is_enabled:
                    row.label(text="", icon='CHECKBOX_HLT')
                else:
                    row.label(text="", icon='CHECKBOX_DEHLT')
                op = row.operator("addon.toggle_item", text="", icon='PLAY')
                op.module = item.module
                row.prop_search(item, "group_name", scene, "addon_groups", text="")

        layout.separator()
        layout.label(text="💡 单击分组列表项即可选中", icon='INFO')
        layout.label(text="💡 点击分组名折叠/展开", icon='INFO')
        layout.label(text="💡 ▶ 启用全部  ⏸ 禁用全部", icon='INFO')

# ------------------------------------------------------------
# 注册/注销
# ------------------------------------------------------------
classes = (
    GroupItem,
    AddonItem,
    ADDON_OT_refresh_list,
    ADDON_OT_toggle_addon,
    ADDON_OT_enable_group_all,
    ADDON_OT_disable_group_all,
    ADDON_OT_add_group,
    ADDON_OT_remove_group,
    ADDON_OT_rename_group,
    ADDON_OT_move_group,
    ADDON_OT_toggle_group,
    ADDON_UL_groups,
    VIEW3D_PT_plugin_manager,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.addon_groups = CollectionProperty(type=GroupItem)
    bpy.types.Scene.active_group_index = IntProperty(default=0)
    bpy.types.Scene.addon_list = CollectionProperty(type=AddonItem)
    bpy.types.Scene.addon_list_index = IntProperty(default=0)
    bpy.types.Scene.rename_group_input = StringProperty(name="", default="")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.addon_groups
    del bpy.types.Scene.active_group_index
    del bpy.types.Scene.addon_list
    del bpy.types.Scene.addon_list_index
    del bpy.types.Scene.rename_group_input

if __name__ == "__main__":
    register()