import bpy

def make_materials_single_user():
    """
    为选中的网格物体创建材质的单用户副本。
    若物体使用的某个材质被多个物体共享（用户数 > 1），则复制该材质并仅赋给当前物体；
    若物体所有材质均为独享（用户数 == 1），则跳过该物体。
    """
    selected = bpy.context.selected_objects
    if not selected:
        print("提示：没有选中任何物体")
        return

    processed_objs = 0
    for obj in selected:
        if obj.type != 'MESH':
            continue
        if not obj.material_slots:
            continue

        # 收集该物体使用的所有唯一材质
        used_mats = {slot.material for slot in obj.material_slots if slot.material}
        if not used_mats:
            continue

        # 检查哪些材质需要复制（用户数 > 1）
        mat_map = {}          # {原始材质: 复制的新材质}
        need_copy = False
        for mat in used_mats:
            if mat.users > 1:   # 被其他物体共享
                need_copy = True
                new_mat = mat.copy()
                # 新材质名称添加 "SU" 后缀，SU = Sole use（独享使用）
                new_mat.name = mat.name + ".SU"
                mat_map[mat] = new_mat
                print(f"复制材质: '{mat.name}' → '{new_mat.name}'")

        if not need_copy:
            # 该物体所有材质均已独享，无需处理
            print(f"物体 '{obj.name}' 所有材质均为独享，已跳过")
            continue

        # 替换该物体所有材质槽中的共享材质为独立副本
        for slot in obj.material_slots:
            if slot.material and slot.material in mat_map:
                slot.material = mat_map[slot.material]

        processed_objs += 1
        print(f"已处理物体: '{obj.name}'")

    print(f"\n处理完成，共处理 {processed_objs} 个物体。")

# 运行脚本
if __name__ == "__main__":
    make_materials_single_user()