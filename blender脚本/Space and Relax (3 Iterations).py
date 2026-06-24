import bpy

class LoopToolsSpaceRelaxOperator(bpy.types.Operator):
    bl_idname = "mesh.looptools_space_relax"
    bl_label = "Space and Relax (3 Iterations)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # 确保在编辑模式
        bpy.ops.object.mode_set(mode='EDIT')

        # 执行 Space 操作
        bpy.ops.mesh.looptools_space()

        # 执行 Relax 操作，迭代 3 次
        bpy.ops.mesh.looptools_relax(iterations='3')

        # 返回对象模式（可选）
#        bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

# 注册操作符
def register():
    bpy.utils.register_class(LoopToolsSpaceRelaxOperator)

# 注销操作符
def unregister():
    bpy.utils.unregister_class(LoopToolsSpaceRelaxOperator)

if __name__ == "__main__":
    register()

    # 测试运行
    bpy.ops.mesh.looptools_space_relax()
