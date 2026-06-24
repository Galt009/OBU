import bpy

def set_vertex_color_to_black():
    """将所有选中网格物体的顶点颜色设置为纯黑色 (0, 0, 0, 1)"""
    selected_objects = bpy.context.selected_objects
    
    if not selected_objects:
        print("提示：没有选中任何物体")
        return

    processed_count = 0
    for obj in selected_objects:
        # 只处理网格物体
        if obj.type != 'MESH':
            continue
        
        mesh = obj.data
        
        # 获取当前激活的顶点颜色层，如果没有则新建一个
        vcol_layer = mesh.vertex_colors.active
        if vcol_layer is None:
            vcol_layer = mesh.vertex_colors.new(name="Col")
            print(f"物体 '{obj.name}' 没有顶点颜色层，已自动新建 'Col' 层")
        
        # 将该层的所有顶点颜色循环数据设为黑色 (RGBA)
        # 注意：顶点颜色存储在网格的每个面角（loop）上
        for loop_data in vcol_layer.data:
            loop_data.color = (0.0, 0.0, 0.0, 1.0)
        
        processed_count += 1
    
    print(f"完成！已将 {processed_count} 个网格物体的顶点颜色设置为黑色。")

# 运行脚本
if __name__ == "__main__":
    set_vertex_color_to_black()