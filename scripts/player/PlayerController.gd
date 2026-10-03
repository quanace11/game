## Điều khiển nhân vật An ở góc nhìn thứ nhất.
##
## - WASD để di chuyển, chuột để nhìn quanh.
## - Chuột bị khóa khi chơi; Esc để nhả chuột, click chuột trái để khóa lại.
## - Yaw (xoay trái/phải) quay cả thân; pitch (nhìn lên/xuống) chỉ quay node Head.
class_name PlayerController
extends CharacterBody3D

@export var walk_speed: float = 2.5
## Gia tốc khi bắt đầu/dừng đi, giúp chuyển động mềm hơn.
@export var acceleration: float = 12.0
## Độ nhạy chuột (radian trên mỗi pixel).
@export var mouse_sensitivity: float = 0.0025
## Giới hạn góc nhìn lên/xuống (độ).
@export_range(0.0, 89.0) var max_pitch_degrees: float = 85.0

@onready var head: Node3D = $Head
@onready var camera: Camera3D = $Head/Camera3D
@onready var flashlight: SpotLight3D = $Head/Camera3D/Flashlight


func _ready() -> void:
	capture_mouse()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_look(event.screen_relative)
	elif event.is_action_pressed(&"ui_cancel"):
		release_mouse()
	elif event is InputEventMouseButton and event.pressed \
			and event.button_index == MOUSE_BUTTON_LEFT \
			and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		capture_mouse()
		get_viewport().set_input_as_handled()


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta

	var input := Input.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")
	var direction := (transform.basis * Vector3(input.x, 0.0, input.y)).normalized()
	var target := direction * walk_speed
	var weight := clampf(acceleration * delta, 0.0, 1.0)
	velocity.x = lerpf(velocity.x, target.x, weight)
	velocity.z = lerpf(velocity.z, target.z, weight)

	move_and_slide()


func capture_mouse() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func release_mouse() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _look(relative: Vector2) -> void:
	rotate_y(-relative.x * mouse_sensitivity)
	head.rotate_x(-relative.y * mouse_sensitivity)
	var limit := deg_to_rad(max_pitch_degrees)
	head.rotation.x = clampf(head.rotation.x, -limit, limit)
