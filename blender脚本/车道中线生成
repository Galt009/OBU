import bpy
import bmesh
from mathutils import Vector

# ===== 用户可调整参数 =====
LINE_LENGTH = 2.0   # 单个线段长度（米）
LINE_WIDTH = 0.2    # 线段宽度（米）
GAP = 4.0           # 线段之间的净间隔（米）
# ==========================

def create_dashed_line_from_curve():
    selected = bpy.context.selected_objects
    curve_obj = None
    for obj in selected:
        if obj.type == 'CURVE':
            curve_obj = obj
            break

    if not curve_obj:
        print("❌ 请选中一条曲线后运行")
        return

    print(f"✅ 使用曲线: {curve_obj.name}")

    # ----- 1. 创建基础长方体（长度沿Z轴，宽度沿X轴，厚度沿Y轴）-----
    half_len = LINE_LENGTH / 2.0
    half_wid = LINE_WIDTH / 2.0
    half_thk = 0.025   # 厚度固定0.05米（可根据需要调整）

    bm = bmesh.new()
    verts = [
        Vector((-half_wid, -half_thk, -half_len)),  # 0
        Vector(( half_wid, -half_thk, -half_len)),  # 1
        Vector(( half_wid,  half_thk, -half_len)),  # 2
        Vector((-half_wid,  half_thk, -half_len)),  # 3
        Vector((-half_wid, -half_thk,  half_len)),  # 4
        Vector(( half_wid, -half_thk,  half_len)),  # 5
        Vector(( half_wid,  half_thk,  half_len)),  # 6
        Vector((-half_wid,  half_thk,  half_len)),  # 7
    ]
    for v in verts:
        bm.verts.new(v)
    bm.verts.ensure_lookup_table()

    faces = [
        (0,1,2,3),  # 底面 (Z负)
        (4,7,6,5),  # 顶面 (Z正)
        (0,4,5,1),  # Y负
        (1,5,6,2),  # X正
        (2,6,7,3),  # Y正
        (3,7,4,0),  # X负
    ]
    for f in faces:
        bm.faces.new([bm.verts[i] for i in f])

    # ----- 2. 沿长度方向（Z轴）环切 5 次（分成 6 段）-----
    segments_z = 6
    bm.edges.ensure_lookup_table()
    edges_to_sub = []
    for e in bm.edges:
        v1, v2 = e.verts[0], e.verts[1]
        if (abs(v1.co.x - v2.co.x) < 0.001 and 
            abs(v1.co.y - v2.co.y) < 0.001 and 
            abs(v1.co.z - v2.co.z) > 0.001):
            edges_to_sub.append(e)

    if not edges_to_sub:
        print("❌ 未找到沿Z方向的边，请检查模板方向。")
        return

    bmesh.ops.subdivide_edges(bm, edges=edges_to_sub, cuts=segments_z - 1, use_grid_fill=False)

    mesh_data = bpy.data.meshes.new("Dash_Segment_Mesh")
    bm.to_mesh(mesh_data)
    bm.free()

    seg_obj = bpy.data.objects.new("Dashed_Segment", mesh_data)
    bpy.context.collection.objects.link(seg_obj)
    seg_obj.location = (0,0,0)
    seg_obj.rotation_euler = (0,0,0)
    seg_obj.scale = (1,1,1)
    print("✅ 线段模板创建成功（基础长方体 + 5次环切）")

    # ----- 3. 几何节点（直接使用曲线旋转）-----
    if "Place_Dashes" in curve_obj.modifiers:
        curve_obj.modifiers.remove(curve_obj.modifiers["Place_Dashes"])

    mod = curve_obj.modifiers.new(name="Place_Dashes", type='NODES')
    node_group = bpy.data.node_groups.new("Dash_Placement", 'GeometryNodeTree')
    mod.node_group = node_group

    node_group.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    input_node = node_group.nodes.new('NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new('NodeGroupOutput')
    output_node.location = (500, 0)

    total_period = LINE_LENGTH + GAP

    curve_to_points = node_group.nodes.new('GeometryNodeCurveToPoints')
    curve_to_points.mode = 'LENGTH'
    curve_to_points.inputs['Length'].default_value = total_period
    curve_to_points.location = (-300, 0)

    instance_on_points = node_group.nodes.new('GeometryNodeInstanceOnPoints')
    instance_on_points.location = (-100, 0)

    realize_instances = node_group.nodes.new('GeometryNodeRealizeInstances')
    realize_instances.location = (100, 0)

    obj_info = node_group.nodes.new('GeometryNodeObjectInfo')
    obj_info.inputs['Object'].default_value = seg_obj
    obj_info.location = (-300, -200)

    node_group.links.new(input_node.outputs['Geometry'], curve_to_points.inputs['Curve'])
    node_group.links.new(curve_to_points.outputs['Points'], instance_on_points.inputs['Points'])
    node_group.links.new(curve_to_points.outputs['Rotation'], instance_on_points.inputs['Rotation'])
    node_group.links.new(obj_info.outputs['Geometry'], instance_on_points.inputs['Instance'])
    node_group.links.new(instance_on_points.outputs['Instances'], realize_instances.inputs['Geometry'])
    node_group.links.new(realize_instances.outputs['Geometry'], output_node.inputs['Geometry'])

    seg_obj.hide_set(True)

    print("\n🎉 虚线生成成功！")
    print(f"   📏 线段长: {LINE_LENGTH}米  |  宽: {LINE_WIDTH}米  |  间隔: {GAP}米  |  细分: {segments_z}段")
    print(f"   📁 路径: {curve_obj.name}")
    print(f"   📁 模板: {seg_obj.name} (已隐藏)")

if __name__ == "__main__":
    create_dashed_line_from_curve()