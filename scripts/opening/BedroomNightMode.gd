## Chuyển phòng ngủ ban ngày (DreamBedroom) sang ban đêm mà không sửa scene gốc.
##
## Tắt đèn chính và đèn ngủ, đổi mặt trời thành ánh trăng lam sẫm thấp, thêm
## một vệt trăng hắt qua khe rèm, và thay Environment bằng bản tối, ngột ngạt.
class_name BedroomNightMode
extends Node

## Các đèn cần tắt (đường dẫn tính từ gốc level). Mesh con tên "Bulb" cũng bị ẩn.
@export var lights_to_disable: Array[NodePath] = [
	^"CeilingLight", ^"WindowBounce", ^"Nightstand1/Lamp", ^"Nightstand2/Lamp",
]
## Các node cần ẩn hẳn (bụi nắng ban ngày...).
@export var nodes_to_hide: Array[NodePath] = [^"SunDust"]
@export var sun_path: NodePath = ^"Sun"
@export var environment_path: NodePath = ^"WorldEnvironment"

@export_group("Ánh trăng")
@export var moon_color: Color = Color(0.36, 0.46, 0.78)
@export var moon_energy: float = 0.6
## Hướng ánh trăng chung (độ): x = pitch, y = yaw.
@export var moon_rotation_degrees: Vector3 = Vector3(-22.0, 168.0, 0.0)
## Vệt trăng hắt qua khe rèm cửa sổ.
@export var shaft_position: Vector3 = Vector3(-1.05, 2.7, 4.6)
@export var shaft_target: Vector3 = Vector3(-0.6, 0.55, -0.6)
@export var shaft_energy: float = 6.0
@export var shaft_angle: float = 9.0

@export_group("Không khí")
@export var ambient_color: Color = Color(0.14, 0.18, 0.3)
@export var ambient_energy: float = 0.4
@export var fog_density: float = 0.035
@export var fog_albedo: Color = Color(0.45, 0.55, 0.75)


func apply(level: Node3D) -> void:
	if level == null:
		return
	for path in lights_to_disable:
		var light := level.get_node_or_null(path) as Light3D
		if light == null:
			continue
		light.light_energy = 0.0
		light.shadow_enabled = false
		var bulb := light.get_node_or_null(^"Bulb") as Node3D
		if bulb:
			bulb.visible = false
	for path in nodes_to_hide:
		var node := level.get_node_or_null(path) as Node3D
		if node:
			node.visible = false
	_apply_moon(level)
	_apply_environment(level)


func _apply_moon(level: Node3D) -> void:
	var sun := level.get_node_or_null(sun_path) as DirectionalLight3D
	if sun:
		sun.light_color = moon_color
		sun.light_energy = moon_energy
		sun.light_volumetric_fog_energy = 1.0
		sun.rotation_degrees = moon_rotation_degrees
	var shaft := SpotLight3D.new()
	shaft.name = "MoonShaft"
	shaft.light_color = moon_color
	shaft.light_energy = shaft_energy
	shaft.light_volumetric_fog_energy = 3.0
	shaft.spot_range = 12.0
	shaft.spot_angle = shaft_angle
	shaft.spot_angle_attenuation = 0.4
	shaft.shadow_enabled = true
	level.add_child(shaft)
	shaft.global_position = shaft_position
	shaft.look_at(shaft_target)


func _apply_environment(level: Node3D) -> void:
	var world := level.get_node_or_null(environment_path) as WorldEnvironment
	if world == null or world.environment == null:
		return
	var env := world.environment.duplicate() as Environment
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.01, 0.012, 0.022)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = ambient_color
	env.ambient_light_energy = ambient_energy
	env.tonemap_exposure = 1.25
	env.sdfgi_enabled = false
	env.glow_bloom = 0.0
	env.volumetric_fog_density = fog_density
	env.volumetric_fog_albedo = fog_albedo
	env.volumetric_fog_emission = Color.BLACK
	env.adjustment_saturation = 0.6
	world.environment = env
