import bpy, sys

# ===== 在这里修改数字范围 =====
START_NUM = 400
END_NUM   = 620
# =============================

group_spacing = 10.0  # 每组之间的X间距
digit_spacing = 1.6   # 数字之间的间距
digit_z = 1.10        # 数字在Z轴的高度

digit_map = {'0':'0_A','1':'1_A','2':'2_A','3':'3_A','4':'4_A',
             '5':'5_A','6':'6_A','7':'7_A','8':'8_A','9':'9_A'}

di_a = bpy.data.objects.get('DI_A')
if not di_a: print("错误: 找不到 DI_A"); sys.exit(1)

col_b = bpy.data.collections.get('b')
if col_b:
    for o in list(col_b.objects):
        col_b.objects.unlink(o)
else:
    col_b = bpy.data.collections.new('b')
    bpy.context.scene.collection.children.link(col_b)

total = END_NUM - START_NUM + 1

for idx, num in enumerate(range(START_NUM, END_NUM + 1)):
    number_str = str(num)
    tx = 8.0 + idx * group_spacing

    d_di = di_a.copy()
    d_di.data = di_a.data.copy()
    d_di.name = f'DI_{number_str}'
    col_b.objects.link(d_di)

    dv = d_di.data.vertices
    di_cx = (min(v.co.x for v in dv) + max(v.co.x for v in dv)) / 2
    di_cy = (min(v.co.y for v in dv) + max(v.co.y for v in dv)) / 2
    di_cz = (min(v.co.z for v in dv) + max(v.co.z for v in dv)) / 2
    for v in dv:
        v.co.x -= di_cx; v.co.y -= di_cy; v.co.z -= di_cz
    dv.update()
    d_di.location = (tx, 0, 0)

    first_obj = d_di
    sx = tx - (len(number_str) - 1) * digit_spacing / 2

    for i, ch in enumerate(number_str):
        src = bpy.data.objects.get(digit_map[ch])
        if not src: continue
        d = src.copy()
        d.data = src.data.copy()
        d.name = f'{ch}_{number_str}'
        col_b.objects.link(d)

        verts = d.data.vertices
        vcx = (min(v.co.x for v in verts) + max(v.co.x for v in verts)) / 2
        vcy = (min(v.co.y for v in verts) + max(v.co.y for v in verts)) / 2
        vcz = (min(v.co.z for v in verts) + max(v.co.z for v in verts)) / 2
        for v in verts:
            v.co.x -= vcx; v.co.y -= vcy; v.co.z -= vcz
        verts.update()
        d.location = (sx + i * digit_spacing, 0, digit_z)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in list(col_b.objects)[-4:]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = first_obj
    bpy.ops.object.join()
    merged = bpy.context.view_layer.objects.active
    merged.name = number_str

print(f"完成: 已生成 {START_NUM}~{END_NUM} 共 {total} 个")
print(f"集合a未动 Y=0")

bpy.ops.wm.save_as_mainfile(filepath=r'C:\Users\XGX\Desktop\机位.blend')
print("已保存到 机位.blend")
