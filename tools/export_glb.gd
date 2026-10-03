## Xuất các level ra .glb để chỉnh trong Blender (vòng Godot -> Blender -> Godot).
##
## Chạy (không cần mở editor):
##   godot --headless --path . --import
##   godot --headless --path . -s tools/export_glb.gd
##   python3 tools/glb_dedupe.py exports/*.glb
## Kết quả: res://exports/<TênLevel>.glb (texture nhúng sẵn trong file).
##
## Chỉ xuất phần nhìn thấy: CSG được "nướng" thành mesh thường, UV triplanar được tính lại
## thành UV thật để texture không bị kéo giãn trong Blender. Đèn, môi trường, Player,
## collision, particle và script bị bỏ; Interactable chỉ còn là Empty cùng tên chứa mesh con.
## Những thứ đó Claude gắn lại khi nhận .glb đã sửa.
extends SceneTree

const LEVELS := [
	"res://scenes/levels/OldHouse.tscn",
	"res://scenes/levels/DreamBedroom.tscn",
]
const OUT := "res://exports/"

var _flat_cache := {}
## Node name -> how many times it appears in the level being exported.
var _name_counts := {}


func _init() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	_run.call_deferred()


func _run() -> void:
	for path in LEVELS:
		var packed := load(path) as PackedScene
		if packed == null:
			push_error("Cannot load %s" % path)
			continue
		var level := packed.instantiate() as Node3D
		root.add_child(level)
		# CSG builds its mesh on the next frames.
		await process_frame
		await process_frame
		_name_counts.clear()
		_count_names(level)
		var clean := Node3D.new()
		clean.name = level.name
		for child in level.get_children():
			_convert(child, clean, Transform3D.IDENTITY)
		var out_path := OUT + String(level.name) + ".glb"
		var err := _write_glb(clean, out_path)
		print("%s -> %s (%s)" % [path, out_path, error_string(err)])
		clean.free()
		level.queue_free()
		await process_frame
	quit()


func _count_names(node: Node) -> void:
	for child in node.get_children():
		_name_counts[child.name] = int(_name_counts.get(child.name, 0)) + 1
		_count_names(child)


## Blender needs globally unique object names, so repeated short names such as
## "Top" or "Leg" become "WindowFrame2_Top" instead of an arbitrary numbered suffix.
func _export_name(node: Node, parent: Node3D) -> String:
	if int(_name_counts.get(node.name, 0)) > 1 and parent.get_parent() != null:
		return "%s_%s" % [parent.name, node.name]
	return node.name


## Copies the visual part of `node` under `parent`. `carry` is the transform of
## dropped ancestors (e.g. a StaticBody3D) so children keep their world position.
func _convert(node: Node, parent: Node3D, carry: Transform3D) -> void:
	if not node is Node3D:
		return
	var n3 := node as Node3D
	if not n3.visible:
		return
	if node is Light3D or node is GPUParticles3D or node is CPUParticles3D \
			or node is CollisionShape3D or node is Camera3D or node is Decal:
		return
	if node.scene_file_path != "":
		return # instanced sub-scenes (Player) are runtime-only
	var xf := carry * n3.transform

	if node is CSGShape3D:
		var csg := node as CSGShape3D
		if not csg.is_root_shape():
			return # already merged into its root
		var baked := csg.bake_static_mesh()
		if baked == null or baked.get_surface_count() == 0:
			return
		var mi := MeshInstance3D.new()
		mi.name = _export_name(node, parent)
		mi.transform = xf
		mi.mesh = _bake_uvs(baked, null, csg.global_transform)
		parent.add_child(mi)
		_convert_children_of_csg(csg, mi)
		return

	if node is MeshInstance3D:
		var src := node as MeshInstance3D
		if src.mesh == null:
			return
		var mi := MeshInstance3D.new()
		mi.name = _export_name(node, parent)
		mi.transform = xf
		mi.mesh = _bake_uvs(src.mesh, src.material_override, src.global_transform)
		parent.add_child(mi)
		for child in node.get_children():
			_convert(child, mi, Transform3D.IDENTITY)
		return

	if node is CollisionObject3D and not node is Area3D:
		# Physics bodies are re-added in Godot; keep only their visuals.
		for child in node.get_children():
			_convert(child, parent, xf)
		return

	# Plain Node3D, Interactable (Area3D) and other groups become an Empty.
	var empty := Node3D.new()
	empty.name = _export_name(node, parent)
	empty.transform = xf
	parent.add_child(empty)
	for child in node.get_children():
		_convert(child, empty, Transform3D.IDENTITY)
	if empty.get_child_count() == 0:
		empty.free()


## Non-CSG nodes hanging under CSG nodes (rare) are kept, relative to the baked root.
func _convert_children_of_csg(csg: Node, holder: Node3D, carry := Transform3D.IDENTITY) -> void:
	for child in csg.get_children():
		if child is CSGShape3D:
			_convert_children_of_csg(child, holder, carry * (child as Node3D).transform)
		else:
			_convert(child, holder, carry)


## Returns an ArrayMesh with the active material on every surface. Surfaces whose
## material uses triplanar mapping get real UVs projected the same way, and a copy of
## the material without triplanar, so Blender shows the same tiling as Godot.
func _bake_uvs(mesh: Mesh, override: Material, global_xf: Transform3D) -> ArrayMesh:
	var out := ArrayMesh.new()
	for s in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(s)
		var mat: Material = override if override != null else mesh.surface_get_material(s)
		if mat != null and mat.resource_name == "":
			mat.resource_name = mat.get_scene_unique_id() # e.g. "Mat_FenceBrick"
		var std := mat as BaseMaterial3D
		if std != null and std.uv1_triplanar:
			var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
			var uvs := PackedVector2Array()
			uvs.resize(verts.size())
			var basis := global_xf.basis
			for i in verts.size():
				var p: Vector3 = global_xf * verts[i] if std.uv1_world_triplanar else verts[i]
				var nrm: Vector3 = (basis * normals[i]).normalized() if std.uv1_world_triplanar else normals[i]
				p = p * std.uv1_scale + std.uv1_offset
				var a := nrm.abs()
				if a.x >= a.y and a.x >= a.z:
					uvs[i] = Vector2(p.z * (-signf(nrm.x)), -p.y)
				elif a.y >= a.z:
					uvs[i] = Vector2(p.x, p.z)
				else:
					uvs[i] = Vector2(p.x * signf(nrm.z), -p.y)
			arrays[Mesh.ARRAY_TEX_UV] = uvs
			# Tangents no longer match the new UVs; drop them so the importer regenerates.
			arrays[Mesh.ARRAY_TANGENT] = null
			mat = _flat_material(std)
		elif std != null and (std.uv1_scale != Vector3.ONE or std.uv1_offset != Vector3.ZERO) \
				and arrays[Mesh.ARRAY_TEX_UV] != null:
			var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
			var scale := Vector2(std.uv1_scale.x, std.uv1_scale.y)
			var offset := Vector2(std.uv1_offset.x, std.uv1_offset.y)
			for i in uvs.size():
				uvs[i] = uvs[i] * scale + offset
			arrays[Mesh.ARRAY_TEX_UV] = uvs
			mat = _flat_material(std)
		var prim := (mesh as ArrayMesh).surface_get_primitive_type(s) if mesh is ArrayMesh else Mesh.PRIMITIVE_TRIANGLES
		out.add_surface_from_arrays(prim, arrays)
		out.surface_set_material(s, mat)
		var sname: String = (mesh as ArrayMesh).surface_get_name(s) if mesh is ArrayMesh else ""
		if sname != "":
			out.surface_set_name(s, sname)
	return out


## One UV-mapped copy per triplanar/scaled material, so the .glb keeps a single shared material.
func _flat_material(std: BaseMaterial3D) -> BaseMaterial3D:
	if _flat_cache.has(std):
		return _flat_cache[std]
	var flat := std.duplicate() as BaseMaterial3D
	flat.uv1_triplanar = false
	flat.uv1_world_triplanar = false
	flat.uv1_scale = Vector3.ONE
	flat.uv1_offset = Vector3.ZERO
	_flat_cache[std] = flat
	return flat


func _write_glb(scene_root: Node3D, out_path: String) -> Error:
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var err := doc.append_from_scene(scene_root, state)
	if err != OK:
		return err
	return doc.write_to_filesystem(state, ProjectSettings.globalize_path(out_path))

