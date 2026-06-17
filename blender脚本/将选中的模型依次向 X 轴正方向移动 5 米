import bpy

def move_selected_along_x_by_outliner_order():
    # 获取大纲视图中的物体顺序
    outliner_order = bpy.context.view_layer.objects[:]
    # 筛选出选中的物体，保持大纲顺序
    selected_in_order = [obj for obj in outliner_order if obj.select_get()]
    
    if not selected_in_order:
        print("提示：请先选中一个或多个模型。")
        return
    
    for idx, obj in enumerate(selected_in_order):
        # 第一个物体 idx=0 -> 移动 0 米
        # 第二个物体 idx=1 -> 移动 5 米
        # 第三个物体 idx=2 -> 移动 10 米，以此类推
        distance = idx * 5.0
        obj.location.x += distance
        print(f"已移动物体 '{obj.name}' 沿 X 轴正方向 {distance} 米")
    
    print(f"完成！共移动了 {len(selected_in_order)} 个物体。")

if __name__ == "__main__":
    move_selected_along_x_by_outliner_order()