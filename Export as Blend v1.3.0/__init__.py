import bpy, subprocess, os, json, tempfile
from os import path

bl_info = {
	"name": "Export as Blend",
	"author": "Tilapiatsu + Modified + Fixed",
	"description": "Side panel to organize objects into collections and export each as a clean .blend with transforms cleared.",
	"version": (1, 3, 0),
	"blender": (4, 5, 0),
	"location": "View3D > Sidebar > 缁勭粐瀵煎嚭",
	"warning": "",
	"category": "Import-Export"
}

# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# Panel
# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class VIEW3D_PT_ExportOrganize(bpy.types.Panel):
	bl_label = "缁勭粐 鈫?瀵煎嚭"
	bl_idname = "VIEW3D_PT_organize_export"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "缁勭粐瀵煎嚭"

	def draw(self, context):
		layout = self.layout
		col = layout.column(align=True)

		col.label(text="鏁寸悊", icon='OUTLINER_COLLECTION')
		col.scale_y = 1.4
		col.operator("object.object_to_collection", text="閫変腑 鈫?鍚勮嚜闆嗗悎", icon='COLLECTION_NEW')

		col.separator(factor=2)

		col.label(text="瀵煎嚭", icon='EXPORT')
		col.label(text="鎻愮ず锛氬彧瀵煎嚭鍚祫浜ф爣璁扮殑闆嗗悎", icon='ASSET_MANAGER')
		col.operator("export_scene.export_collections_clean", text="鎸夐泦鍚堝鍑?, icon='FILE_BLEND')

		col.separator(factor=1)
		col.label(text="鎻愮ず锛氬厛鏁寸悊鍐嶅鍑?, icon='INFO')
		col.label(text="瀵煎嚭浼氳嚜鍔ㄦ竻闄ゅ彉鎹紝鍘熸枃浠朵笉鍙楀奖鍝?)


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# Operator: organize objects into per-name collections
# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class OBJECT_OT_ObjectToCollection(bpy.types.Operator):
	bl_idname = "object.object_to_collection"
	bl_label = "Object to Collection"
	bl_description = "Move each selected object into a collection named after itself"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		return context.selected_objects

	def execute(self, context):
		for obj in context.selected_objects:
			coll_name = obj.name
			coll = bpy.data.collections.get(coll_name)
			if coll is None:
				coll = bpy.data.collections.new(coll_name)
				context.scene.collection.children.link(coll)
			for old_coll in list(obj.users_collection):
				old_coll.objects.unlink(obj)
			if obj.name not in coll.objects:
				coll.objects.link(obj)
		self.report({'INFO'}, f"宸叉暣鐞?{len(context.selected_objects)} 涓墿浣撳埌鍚勮嚜闆嗗悎")
		return {'FINISHED'}


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# Background script template
# This gets written to a temp file and executed via --python
# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
BACKGROUND_SCRIPT = r'''import bpy, json, os

# ---- read data file ----
data_path = {data_path!r}
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

source_path = data['source_path']
target_path = data['target_path']
object_names = data['object_names']
asset_names = set(data.get('asset_names', []))

# ---- clear factory-default objects ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# ---- append each object individually (more reliable than files=[]) ----
for name in object_names:
    filepath = os.path.join(source_path, 'Object', name)
    directory = os.path.join(source_path, 'Object')
    bpy.ops.wm.append(
        filepath=filepath,
        directory=directory,
        filename=name,
        link=False,
    )

# ---- mark objects as assets (only objects, not materials/etc) ----
for o in list(bpy.data.objects):
    base = o.name.split('.')[0]
    if o.name in asset_names or base in asset_names:
        try:
            o.asset_mark()
        except Exception:
            pass

# ---- remove asset status from materials (only objects should be assets) ----
for mat in list(bpy.data.materials):
    try:
        mat.asset_clear()
    except Exception:
        pass

# ---- purge orphaned data (unused materials, textures, images, etc.) ----
# First pass: remove materials not used by any object's material slot
used_materials = set()
for o in bpy.data.objects:
    if hasattr(o, 'material_slots'):
        for slot in o.material_slots:
            if slot.material:
                used_materials.add(slot.material.name)
for mat in list(bpy.data.materials):
    if mat.name not in used_materials:
        mat.user_clear()
        bpy.data.materials.remove(mat, do_unlink=True)

# Second pass: purge orphans (unused images, node groups, etc.)
# This catches data blocks with zero remaining users
bpy.data.orphans_purge()

# Track appended objects: they didn't exist before, so select all non-hidden
# (factory defaults were already deleted, so this is clean)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if not o.name.startswith("_"):
        o.select_set(True)

if bpy.context.selected_objects:
    for obj in bpy.context.selected_objects:
        obj.location = (0.0, 0.0, 0.0)
        obj.rotation_euler = (0.0, 0.0, 0.0)
        obj.scale = (1.0, 1.0, 1.0)
    bpy.ops.object.select_all(action='DESELECT')

# ---- save ----
bpy.ops.wm.save_as_mainfile(filepath=target_path)

# ---- cleanup ----
os.unlink(data_path)
'''


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# Operator: export each collection as a clean .blend
# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class EXPORT_OT_CollectionsClean(bpy.types.Operator):
	bl_idname = "export_scene.export_collections_clean"
	bl_label = "Export Collections as Clean .blend"
	bl_description = "Export each collection to a separate .blend file with transforms cleared"
	bl_options = {'REGISTER', 'INTERNAL'}

	directory: bpy.props.StringProperty(subtype='DIR_PATH', options={'HIDDEN', 'SKIP_SAVE'})
	skip_empty_collections: bpy.props.BoolProperty(name="Skip Empty", default=True)

	def invoke(self, context, event):
		# Default to current file's directory
		if bpy.data.filepath:
			self.directory = path.dirname(bpy.data.filepath) + path.sep
		else:
			self.directory = os.path.expanduser("~") + path.sep
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

	def draw(self, context):
		layout = self.layout
		layout.prop(self, "skip_empty_collections")

	def execute(self, context):
		# Save first so background process can read from disk
		if bpy.data.filepath:
			bpy.ops.wm.save_mainfile()
		else:
			self.report({'ERROR'}, "璇峰厛淇濆瓨褰撳墠鏂囦欢鍐嶅鍑?)
			return {'CANCELLED'}

		out_dir = self.directory
		if not out_dir:
			out_dir = path.dirname(bpy.data.filepath)

		collections_to_export = []
		for coll in bpy.data.collections:
			if coll.name == context.scene.collection.name:
				continue  # skip scene root
			if coll.name.startswith("_"):
				continue   # skip hidden/internal
			# 鍙鍑哄寘鍚嚦灏戜竴涓祫浜фā鍨嬬殑闆嗗悎
			objs = [o for o in coll.objects if not o.hide_get()]
			has_asset = any(getattr(o, 'asset_data', None) is not None for o in objs)
			if not has_asset:
				continue
			if self.skip_empty_collections and not objs:
				continue
			collections_to_export.append((coll.name, objs))

		if not collections_to_export:
			self.report({'WARNING'}, "娌℃湁鎵惧埌鍚祫浜фā鍨嬬殑闆嗗悎")
			return {'CANCELLED'}

		exported = []
		errors = []
		for coll_name, objs in collections_to_export:
			safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in coll_name)
			out_path = path.join(out_dir, f"{safe_name}.blend")
			try:
				self._export_collection(objs, out_path)
				exported.append(out_path)
			except Exception as e:
				errors.append(f"{coll_name}: {e}")

		if errors:
			self.report({'ERROR'}, f"瀵煎嚭瀹屾垚锛屼絾 {len(errors)} 涓け璐? {'; '.join(errors[:3])}")
		else:
			self.report({'INFO'}, f"宸叉垚鍔熷鍑?{len(exported)} 涓泦鍚堝埌: {out_dir}")
		return {'FINISHED'}

	def _export_collection(self, objects, out_path):
		"""Launch background Blender that appends objects and clears transforms."""
		obj_names = [o.name for o in objects]
		asset_names = [o.name for o in objects if getattr(o, 'asset_data', None) is not None]

		# 鈹€鈹€ write data JSON 鈹€鈹€
		data = {
			'source_path': bpy.data.filepath,
			'target_path': out_path,
			'object_names': obj_names,
			'asset_names': asset_names,
		}
		data_fp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
		json.dump(data, data_fp, ensure_ascii=False)
		data_path = data_fp.name
		data_fp.close()

		# 鈹€鈹€ write Python script 鈹€鈹€
		script_content = BACKGROUND_SCRIPT.format(data_path=data_path)
		script_fp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
		script_fp.write(script_content)
		script_path = script_fp.name
		script_fp.close()

		# 鈹€鈹€ launch background Blender 鈹€鈹€
		try:
			subprocess.check_call([
				bpy.app.binary_path,
				'--background',
				'--factory-startup',
				'--python', script_path,
			])
		except subprocess.CalledProcessError as e:
			raise RuntimeError(f"鍚庡彴 Blender 杩涚▼澶辫触 (杩斿洖鐮?{e.returncode})") from e
		finally:
			# Clean up temp script (data file is cleaned by the background process)
			try:
				os.unlink(script_path)
			except OSError:
				pass


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# Registration
# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
classes = (
	VIEW3D_PT_ExportOrganize,
	OBJECT_OT_ObjectToCollection,
	EXPORT_OT_CollectionsClean,
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)

if __name__ == "__main__":
	register()
