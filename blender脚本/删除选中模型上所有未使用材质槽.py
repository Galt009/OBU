import bpy

def clean_material_slots():
    # 获取当前场景中所有选中的物体
    selected = bpy.context.selected_objects

    # 如果没有选中任何物体，则给出提示并退出
    if not selected:
        print("提示：请先选中一个或多个需要处理的模型。")
        return

    # 遍历所有选中的物体
    for obj in selected:
        # 只处理网格物体，避免因材质槽导致非网格物体出错
        if obj.type != 'MESH':
            print(f"跳过非网格物体：{obj.name} (类型: {obj.type})")
            continue

        # 在清理前，先让Blender切换到编辑模式再切回，这能强制刷新材质分配信息，
        # 并确保bpy.ops.object.material_slot_remove_unused操作符能够正确执行。
        # 这种模式切换是解决该操作符在某些情况下失效的有效方法。
        
        # 确保当前处于对象模式
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # 记录当前选中的物体和活动物体
        originally_selected = bpy.context.selected_objects[:]
        original_active = bpy.context.view_layer.objects.active
        
        # 仅选中当前要处理的物体，并设为活动物体
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # 先进入编辑模式，再切回对象模式，刷新材质数据
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # 执行清理未使用材质槽的命令
        try:
            bpy.ops.object.material_slot_remove_unused()
            print(f"成功清理：{obj.name}")
        except Exception as e:
            print(f"清理失败：{obj.name}，错误：{e}")
        
        # 恢复原本的选中状态
        bpy.ops.object.select_all(action='DESELECT')
        for original_obj in originally_selected:
            original_obj.select_set(True)
        bpy.context.view_layer.objects.active = original_active

if __name__ == "__main__":
    clean_material_slots()