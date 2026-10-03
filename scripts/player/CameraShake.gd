## Rung camera theo [signal EventBus.camera_shake_requested].
##
## Gắn làm con của Camera3D. Chỉ đổi h_offset/v_offset nên không đụng tới
## góc nhìn chuột hay các tween di chuyển Head của phân cảnh.
class_name CameraShake
extends Node

## Tần số rung (lần/giây).
@export var frequency: float = 22.0

@onready var _camera: Camera3D = get_parent() as Camera3D

var _strength := 0.0
var _duration := 0.0
var _time_left := 0.0
var _phase := 0.0


func _ready() -> void:
	set_process(false)
	EventBus.camera_shake_requested.connect(_on_shake_requested)


func _exit_tree() -> void:
	if EventBus.camera_shake_requested.is_connected(_on_shake_requested):
		EventBus.camera_shake_requested.disconnect(_on_shake_requested)
	_reset_offsets()


func _process(delta: float) -> void:
	if _camera == null:
		return
	_time_left -= delta
	if _time_left <= 0.0:
		_reset_offsets()
		set_process(false)
		return
	_phase += delta * frequency
	var falloff := _time_left / _duration
	var amount := _strength * falloff * falloff
	_camera.h_offset = sin(_phase * 1.7) * cos(_phase * 0.6) * amount
	_camera.v_offset = sin(_phase * 2.3 + 1.1) * amount


func _on_shake_requested(strength: float, duration: float) -> void:
	if duration <= 0.0 or _camera == null:
		return
	_strength = maxf(strength, _strength if _time_left > 0.0 else 0.0)
	_duration = duration
	_time_left = duration
	set_process(true)


func _reset_offsets() -> void:
	if _camera:
		_camera.h_offset = 0.0
		_camera.v_offset = 0.0
