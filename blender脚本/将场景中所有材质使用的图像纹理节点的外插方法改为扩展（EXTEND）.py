import bpy

def set_image_extension_to_extend():
    """将场景中所有材质使用的图像纹理节点的外插方法改为扩展（EXTEND）"""
    
    modified_count = 0
    
    # 遍历场景中的所有材质
    for material in bpy.data.materials:
        if material is None or not material.use_nodes:
            continue
            
        # 获取材质节点树
        node_tree = material.node_tree
        if node_tree is None:
            continue
            
        # 遍历材质中的所有节点
        for node in node_tree.nodes:
            # 检查是否为图像纹理节点
            if node.type == 'TEX_IMAGE':
                # 关键修改：extension 是节点的属性，不是 image 的属性
                if node.extension != 'EXTEND':
                    node.extension = 'EXTEND'
                    modified_count += 1
                    print(f"已修改: {material.name} -> {node.name}")
    
    print(f"\n完成！共修改了 {modified_count} 个图像纹理节点的扩展模式为 EXTEND")

def set_image_extension_for_selected_objects():
    """将选中对象使用的材质中的图像纹理节点扩展模式改为扩展"""
    
    modified_count = 0
    
    selected_objects = bpy.context.selected_objects
    
    if not selected_objects:
        print("没有选中的对象！")
        return
    
    for obj in selected_objects:
        if obj.type == 'MESH':
            for material_slot in obj.material_slots:
                material = material_slot.material
                if material and material.use_nodes:
                    node_tree = material.node_tree
                    if node_tree:
                        for node in node_tree.nodes:
                            if node.type == 'TEX_IMAGE':
                                if node.extension != 'EXTEND':
                                    node.extension = 'EXTEND'
                                    modified_count += 1
                                    print(f"已修改: {obj.name} -> {material.name} -> {node.name}")
    
    print(f"\n完成！共修改了 {modified_count} 个图像纹理节点的扩展模式为 EXTEND")

# 运行脚本
set_image_extension_to_extend()