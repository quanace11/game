## Bối cảnh chiếc xe khách (scenes/levels/Bus.tscn, sinh bằng tools/bus_blockout.py).
##
## Ba lớp nhìn (xem [enum Layer]):
## - [code]Day[/code]: xe thật năm 2006, chiều muộn, đông khách, xe đang chạy.
## - [code]Derelict[/code]: xác chiếc xe năm 1999 nằm ở bãi sông, mục nát, vắng tanh.
## - [code]Night1999[/code]: khoảnh khắc ngay trước tai nạn đêm 14/04/1999, thời gian
##   đứng yên, mưa treo giữa trời, thành cầu ngay trước mũi xe.
## Level chỉ lo phần nhìn của từng lớp; các đạo diễn phân cảnh quyết định khi nào đổi.
class_name BusLevel
extends Node3D

enum Layer { DAY, DERELICT, NIGHT }

@export var day_environment: Environment
@export var derelict_environment: Environment
@export var night_environment: Environment

@export_group("Mưa đứng yên (Đêm 1999)")
@export var rain_count: int = 1400
## Vùng rải mưa quanh xe (tâm và nửa kích thước, mét).
@export var rain_center: Vector3 = Vector3(0.0, 2.0, -6.0)
@export var rain_extents: Vector3 = Vector3(9.0, 3.2, 16.0)
## Mỗi nhịp thời gian nhích lên, hạt mưa rơi xuống thêm bấy nhiêu mét.
@export var rain_step: float = 0.22
## Mỗi nhịp thời gian, thành cầu trước mũi xe lại gần thêm bấy nhiêu mét.
@export var rail_step: float = 0.9

var layer: Layer = Layer.DAY
var is_derelict: bool:
	get:
		return layer == Layer.DERELICT

@onready var _day: Node3D = get_node_or_null(^"Day")
@onready var _derelict: Node3D = get_node_or_null(^"Derelict")
@onready var _night: Node3D = get_node_or_null(^"Night1999")
@onready var _world_env: WorldEnvironment = get_node_or_null(^"WorldEnvironment")
@onready var _scenery: ScrollingScenery = get_node_or_null(^"Day/Outside/Scenery")
@onready var _tube_light: Light3D = get_node_or_null(^"Derelict/TubeLight")
@onready var _glimpse: Node3D = get_node_or_null(^"Day/Glimpse")
@onready var _old_woman: Node3D = get_node_or_null(^"Day/Passengers/OldWoman")
@onready var _paper_basket: Array[Node3D] = _find_children(^"Day/Props", "PaperBasket", "PaperGoods")
@onready var _rain: Node3D = get_node_or_null(^"Night1999/Rain")
@onready var _rail: Node3D = get_node_or_null(^"Night1999/Outside/BridgeRail")
@onready var _stop_sign: Node3D = get_node_or_null(^"Night1999/Outside/StopSign")

var _rail_origin := Vector3.ZERO


func _ready() -> void:
	if _rail:
		_rail_origin = _rail.position
	_build_rain()
	set_layer(Layer.DAY)


## Đổi toàn bộ phần nhìn sang lớp [param value].
func set_layer(value: Layer) -> void:
	layer = value
	if _day:
		_day.visible = value == Layer.DAY
	if _derelict:
		_derelict.visible = value == Layer.DERELICT
	if _night:
		_night.visible = value == Layer.NIGHT
	if _scenery:
		_scenery.set_process(value == Layer.DAY)
	if _world_env:
		var env: Environment = [day_environment, derelict_environment, night_environment][value]
		if env:
			_world_env.environment = env


## Giữ cho code cũ: true = xác xe, false = xe ban ngày.
func set_derelict(value: bool) -> void:
	set_layer(Layer.DERELICT if value else Layer.DAY)


## Xe lăn bánh / dừng lại (cảnh ngoài cửa sổ tăng tốc hoặc chậm dần).
func set_moving(value: bool, instant: bool = false) -> void:
	if _scenery:
		_scenery.set_moving(value, instant)


## Bật/tắt bóng đèn tuýp còn sống trên xe hoang (dùng cho khoảnh khắc mất điện).
func set_power(on: bool) -> void:
	if _tube_light:
		_tube_light.visible = on


## Xe 2006 trong cảnh nhìn thấy một lần: thân xác An gục ở ghế 07, ghế bà cụ chỉ còn tro.
## [param body_visible] = false khi An đã tỉnh lại trong chính thân xác ấy (cuối chương).
func set_glimpse(on: bool, body_visible: bool = true) -> void:
	if _glimpse:
		_glimpse.visible = on
		for node_name in ["Cup", "WaterDrop", "BridgeBeam", "BridgePost"]:
			for child in _glimpse.get_children():
				if String(child.name).begins_with(node_name):
					(child as Node3D).visible = body_visible
		var body := _glimpse.get_node_or_null(^"AnBody") as Node3D
		if body:
			body.visible = body_visible
	set_old_woman_gone(on)


## Bà cụ biến mất khỏi ghế, giỏ hàng mã cũng không còn.
func set_old_woman_gone(gone: bool) -> void:
	if _old_woman:
		_old_woman.visible = not gone
	for node in _paper_basket:
		node.visible = not gone


## Đêm 1999: thời gian nhích lên ([param tick] > 0) hoặc lùi lại. Mưa rơi xuống một
## đoạn, thành cầu trước mũi xe lại gần thêm.
func set_night_time(tick: int, duration: float = 0.8) -> void:
	var tween := create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	if _rain:
		tween.tween_property(_rain, "position:y", -rain_step * tick, duration)
	if _rail:
		var forward := Vector3(0.0, 0.0, rail_step * tick)
		tween.tween_property(_rail, "position", _rail_origin + forward, duration)


## Biển "Bến Thôn Đoài" bên kia cầu hiện ra trong ánh đèn pha.
func show_stop_sign(on: bool) -> void:
	if _stop_sign:
		_stop_sign.visible = on


func _find_children(parent_path: NodePath, a: String, b: String) -> Array[Node3D]:
	var found: Array[Node3D] = []
	var parent := get_node_or_null(parent_path)
	if parent == null:
		return found
	for child in parent.get_children():
		var n := String(child.name)
		if n.begins_with(a) or n.begins_with(b):
			found.append(child as Node3D)
	return found


## Rải các hạt mưa đứng yên quanh xe (bỏ trống lòng xe) bằng MultiMesh.
func _build_rain() -> void:
	if _rain == null or rain_count <= 0:
		return
	var drop := BoxMesh.new()
	drop.size = Vector3(0.006, 0.2, 0.006)
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(0.75, 0.85, 0.9, 0.55)
	mat.emission_enabled = true
	mat.emission = Color(0.35, 0.45, 0.5)
	mat.emission_energy_multiplier = 0.4
	mat.roughness = 0.1
	drop.material = mat
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = drop
	multimesh.instance_count = rain_count
	var rng := RandomNumberGenerator.new()
	rng.seed = 140499
	var i := 0
	while i < rain_count:
		var p := rain_center + Vector3(rng.randf_range(-1, 1) * rain_extents.x,
				rng.randf_range(-1, 1) * rain_extents.y, rng.randf_range(-1, 1) * rain_extents.z)
		# Không cho mưa lọt vào trong lòng xe.
		if absf(p.x) < 1.45 and p.z > -5.3 and p.z < 4.9:
			continue
		var basis := Basis(Vector3.RIGHT, deg_to_rad(rng.randf_range(-6.0, 6.0)))
		multimesh.set_instance_transform(i, Transform3D(basis, p))
		i += 1
	var instance := MultiMeshInstance3D.new()
	instance.name = "Drops"
	instance.multimesh = multimesh
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_rain.add_child(instance)
