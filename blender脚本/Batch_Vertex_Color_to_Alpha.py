import bpy

def set_vertex_color_to_alpha():
    # 获取选中的物体
    objects = bpy.context.selected_objects
    if not objects:
        print("没有选中任何物体")
        return

    # 统一顶点颜色层的名称为 "Col"
    vcol_name = "Col"
    for obj in objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data

        # 检查顶点颜色层
        if mesh.vertex_colors.active:
            # 已有活动层，重命名为 "Col"
            if mesh.vertex_colors.active.name != vcol_name:
                mesh.vertex_colors.active.name = vcol_name
        else:
            # 没有活动层，尝试使用第一个
            if len(mesh.vertex_colors) > 0:
                if mesh.vertex_colors[0].name != vcol_name:
                    mesh.vertex_colors[0].name = vcol_name
                mesh.vertex_colors.active = mesh.vertex_colors[0]
            else:
                # 没有顶点颜色层，新建一个
                mesh.vertex_colors.new(name=vcol_name)

    # 收集所有材质（去重）
    materials = set()
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            if slot.material:
                materials.add(slot.material)

    # 处理每个材质
    for mat in materials:
        if mat.node_tree is None:
            mat.use_nodes = True
        node_tree = mat.node_tree

        # 查找原理化 BSDF
        principled = None
        for node in node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
        if principled is None:
            # 创建原理化 BSDF
            principled = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
            # 确保材质输出存在并连接
            output = node_tree.nodes.get('Material Output')
            if output is None:
                output = node_tree.nodes.new(type='ShaderNodeOutputMaterial')
            node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # 处理 Alpha 连接
        alpha_input = principled.inputs['Alpha']
        attr_node = None

        # 检查是否已有正确的 Attribute 节点连接到 Alpha
        if alpha_input.is_linked:
            src_node = alpha_input.links[0].from_node
            if src_node.type == 'ATTRIBUTE' and src_node.attribute_name == vcol_name:
                attr_node = src_node

        # 如果没有，则新建并连接
        if attr_node is None:
            attr_node = node_tree.nodes.new(type='ShaderNodeAttribute')
            attr_node.attribute_name = vcol_name
            # 断开 Alpha 上原有的连接
            if alpha_input.is_linked:
                for link in alpha_input.links:
                    node_tree.links.remove(link)
            # 连接 Attribute 的 Color 输出到 Alpha
            node_tree.links.new(attr_node.outputs['Color'], alpha_input)

    print("处理完成：所有选中物体的材质已添加顶点颜色控制 Alpha。")

# 运行脚本
if __name__ == "__main__":
    set_vertex_color_to_alpha()