extends Node
## Chụp ảnh kiểm tra cho hai bối cảnh, chạy headless qua xvfb:
##   xvfb-run -a godot --path . --resolution 1280x720 res://tools/LevelShots.tscn -- <out_dir> [old|dream] [view]
## Mỗi góc chụp là (tên, vị trí camera, điểm nhìn). Player bị gỡ để HUD không che ảnh.

const LEVELS := {
	"dream": {
		"scene": "res://scenes/levels/DreamBedroom.tscn",
		"views": [
			["dream_1_spawn", Vector3(0.6, 1.6, 1.9), Vector3(0.0, 1.1, -2.5)],
			["dream_2_wardrobe_safe", Vector3(0.6, 1.6, 0.6), Vector3(-2.7, 1.0, -0.6)],
			["dream_3_window", Vector3(-0.3, 1.6, -1.2), Vector3(0.0, 1.4, 2.5)],
			["dream_4_vanity", Vector3(-0.8, 1.6, 0.6), Vector3(2.7, 1.1, -0.2)],
		],
	},
	"old": {
		"scene": "res://scenes/levels/OldHouse.tscn",
		"views": [
			["old_1_yard", Vector3(0.0, 1.6, 7.5), Vector3(0.0, 1.5, 0.0)],
			["old_2_altar", Vector3(0.0, 1.6, 2.2), Vector3(0.0, 1.3, -2.75)],
			["old_3_tv", Vector3(1.4, 1.6, 1.4), Vector3(-2.4, 1.0, -0.6)],
			["old_4_her_room", Vector3(4.3, 1.6, 2.3), Vector3(4.3, 0.0, -1.5)],
			["old_5_parents", Vector3(-4.3, 1.6, 2.3), Vector3(-4.3, 0.8, -2.0)],
			["old_6_kitchen", Vector3(0.0, 1.6, -3.3), Vector3(0.0, 0.9, -6.8)],
			["old_7_cellar", Vector3(4.3, -0.7, 2.3), Vector3(4.3, -1.6, -2.5)],
		],
	},
}

const WARMUP_FRAMES := 90
const SETTLE_FRAMES := 25

var view_filter := ""


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir: String = args[0] if args.size() > 0 else "user://shots"
	var only: String = args[1] if args.size() > 1 else ""
	view_filter = args[2] if args.size() > 2 else ""
	DirAccess.make_dir_recursive_absolute(out_dir)
	for key in LEVELS:
		if only != "" and key != only:
			continue
		await _shoot_level(LEVELS[key], out_dir)
	get_tree().quit()


func _shoot_level(level: Dictionary, out_dir: String) -> void:
	var root: Node3D = (load(level.scene) as PackedScene).instantiate()
	var player := root.get_node_or_null("Player")
	if player:
		root.remove_child(player)
		player.free()
	add_child(root)
	var cam := Camera3D.new()
	cam.fov = 75.0
	root.add_child(cam)
	cam.make_current()
	var first := true
	for v in level.views:
		if view_filter != "" and not String(v[0]).contains(view_filter):
			continue
		cam.position = v[1]
		cam.look_at(v[2])
		for i in (WARMUP_FRAMES if first else SETTLE_FRAMES):
			await get_tree().process_frame
		first = false
		var img := get_viewport().get_texture().get_image()
		img.save_png(out_dir.path_join(v[0] + ".png"))
		print("saved ", v[0])
	root.queue_free()
	await get_tree().process_frame
