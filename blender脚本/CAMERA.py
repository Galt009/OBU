import bpy
import os

# 获取场景中的所有对象
all_objects = bpy.data.objects 

# 遍历所有对象
for obj in all_objects:
    # 查找名为"Camera"的集合
    if obj.type == 'CAMERA':
        # 遍历集合中的所有对象
        # 设置渲染设置
        bpy.context.scene.camera = obj
        bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
                
        # 生成保存路径及文件名
        save_dir = "D:\cs"
        file_name = f"{obj.name}.png"
        save_path = os.path.join(save_dir, file_name)
        
        bpy.context.scene.render.filepath = save_path
                
        # 渲染并保存图像
        bpy.ops.render.render(write_still=True)