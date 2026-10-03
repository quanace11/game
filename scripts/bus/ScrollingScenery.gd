## Giả lập xe đang chạy: xe đứng yên, cảnh vật bên ngoài trôi về phía sau.
##
## Mọi node con (cây, cột điện, nhà...) trôi theo +Z cục bộ và quay vòng lại phía
## trước khi đi quá nửa [member wrap_length]. Texture của mặt đất/đường trong
## [member scrolling_materials] trượt UV cùng tốc độ để mặt đất cũng trôi.
## Gọi [method set_moving] để tăng/giảm tốc mượt (xe lăn bánh hoặc dừng lại).
class_name ScrollingScenery
extends Node3D

## Tốc độ xe khi chạy đều (m/s).
@export var cruise_speed: float = 11.0
## Tốc độ thay đổi vận tốc (m/s²) khi tăng tốc hoặc phanh.
@export var acceleration: float = 2.5
## Chiều dài đoạn cảnh quay vòng (m), node con nằm trong khoảng [-wrap/2, wrap/2].
@export var wrap_length: float = 120.0
## Vật liệu mặt đất/đường cần trượt UV (dùng UV thường, không triplanar).
@export var scrolling_materials: Array[BaseMaterial3D] = []
## Chiều dài (m) theo trục Z của PlaneMesh mang các vật liệu trên, để đổi quãng đường ra UV.
@export var plane_length: float = 200.0
## Bắt đầu đang chạy.
@export var moving: bool = true

var speed: float = 0.0


func _ready() -> void:
	speed = cruise_speed if moving else 0.0


## [param instant] = true thì đổi tốc độ ngay, không tăng/giảm tốc.
func set_moving(value: bool, instant: bool = false) -> void:
	moving = value
	if instant:
		speed = cruise_speed if value else 0.0


func _process(delta: float) -> void:
	var target := cruise_speed if moving else 0.0
	speed = move_toward(speed, target, acceleration * delta)
	if is_zero_approx(speed):
		return
	var dz := speed * delta
	var half := wrap_length * 0.5
	for child in get_children():
		var node := child as Node3D
		if node == null:
			continue
		node.position.z += dz
		if node.position.z > half:
			node.position.z -= wrap_length
	for mat in scrolling_materials:
		if mat == null or is_zero_approx(mat.uv1_scale.y):
			continue
		# PlaneMesh: v tăng theo +Z, nên trừ offset để texture trôi về +Z.
		mat.uv1_offset.y = fposmod(mat.uv1_offset.y - dz * mat.uv1_scale.y / plane_length, 1.0)
