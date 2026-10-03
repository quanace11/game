## Đung đưa nhẹ quanh gốc của node (bóng đèn treo, áo phơi, rèm). Gốc node = điểm treo.
class_name Sway
extends Node3D

## Góc lắc tối đa (độ) quanh trục X và Z.
@export var amplitude_deg: Vector2 = Vector2(2.0, 1.5)
## Tốc độ dao động (chu kỳ / giây).
@export var speed: float = 0.35

var _t := 0.0
var _phase := 0.0
var _rest: Basis


func _ready() -> void:
	_rest = transform.basis
	_phase = randf() * TAU


func _process(delta: float) -> void:
	_t += delta * speed * TAU
	# Hai sóng lệch nhau để chuyển động không đều như có gió lùa.
	var ax := deg_to_rad(amplitude_deg.x) * (sin(_t + _phase) * 0.7 + sin(_t * 0.37) * 0.3)
	var az := deg_to_rad(amplitude_deg.y) * sin(_t * 0.81 + _phase * 1.3)
	transform.basis = _rest * Basis.from_euler(Vector3(ax, 0.0, az))
