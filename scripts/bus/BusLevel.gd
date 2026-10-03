## Bối cảnh chiếc xe khách (scenes/levels/Bus.tscn, sinh bằng tools/bus_blockout.py).
##
## Hai trạng thái nhìn: [code]Day[/code] (chiều muộn, đông khách, xe đang chạy) và
## [code]Derelict[/code] (xe bỏ hoang, vắng tanh, đỗ trong sương đêm). Level chỉ lo
## phần nhìn của từng trạng thái; đạo diễn phân cảnh (BusRideDirector) quyết định
## khi nào đổi.
class_name BusLevel
extends Node3D

@export var day_environment: Environment
@export var derelict_environment: Environment

var is_derelict := false

@onready var _day: Node3D = get_node_or_null(^"Day")
@onready var _derelict: Node3D = get_node_or_null(^"Derelict")
@onready var _world_env: WorldEnvironment = get_node_or_null(^"WorldEnvironment")
@onready var _scenery: ScrollingScenery = get_node_or_null(^"Day/Outside/Scenery")
@onready var _tube_light: Light3D = get_node_or_null(^"Derelict/TubeLight")


func _ready() -> void:
	set_derelict(false)


## Đổi toàn bộ phần nhìn sang xe hoang tàn ([param value] = true) hoặc xe ban ngày.
func set_derelict(value: bool) -> void:
	is_derelict = value
	if _day:
		_day.visible = not value
	if _derelict:
		_derelict.visible = value
	if _scenery:
		_scenery.set_process(not value)
	if _world_env:
		var env := derelict_environment if value else day_environment
		if env:
			_world_env.environment = env


## Xe lăn bánh / dừng lại (cảnh ngoài cửa sổ tăng tốc hoặc chậm dần).
func set_moving(value: bool, instant: bool = false) -> void:
	if _scenery:
		_scenery.set_moving(value, instant)


## Bật/tắt bóng đèn tuýp còn sống trên xe hoang (dùng cho khoảnh khắc mất điện).
func set_power(on: bool) -> void:
	if _tube_light:
		_tube_light.visible = on
