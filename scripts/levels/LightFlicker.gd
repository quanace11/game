## Làm đèn chập chờn: phần lớn thời gian sáng ổn định, thỉnh thoảng nháy một chuỗi ngắn.
##
## Gắn vào OmniLight3D/SpotLight3D. Nếu [member emissive_mesh] được gán, độ phát sáng
## của mesh bóng đèn cũng tắt/sáng theo để nhìn khớp với ánh sáng.
class_name LightFlicker
extends Light3D

## Biên độ dao động liên tục (0 = đứng yên, 0.1 = rung nhẹ như bóng sợi đốt điện yếu).
@export_range(0.0, 1.0) var hum: float = 0.04
## Khoảng nghỉ (giây) giữa hai lần nháy, chọn ngẫu nhiên trong khoảng này.
@export var calm_range: Vector2 = Vector2(4.0, 12.0)
## Số lần chớp tắt trong một đợt nháy.
@export var burst_count: Vector2i = Vector2i(2, 6)
## Mức sáng thấp nhất khi chớp (tỉ lệ so với mức gốc).
@export_range(0.0, 1.0) var dip: float = 0.05
## Mesh bóng đèn (MeshInstance3D hoặc GeometryInstance3D) để tắt sáng cùng đèn. Có thể để trống.
@export var emissive_mesh: NodePath

var _base_energy: float
var _timer := 0.0
var _burst_left := 0
var _rng := RandomNumberGenerator.new()
var _mesh: GeometryInstance3D


func _ready() -> void:
	_base_energy = light_energy
	_rng.randomize()
	_timer = _rng.randf_range(calm_range.x, calm_range.y)
	if not emissive_mesh.is_empty():
		_mesh = get_node_or_null(emissive_mesh) as GeometryInstance3D


func _process(delta: float) -> void:
	_timer -= delta
	var level := 1.0 + (_rng.randf() * 2.0 - 1.0) * hum
	if _burst_left > 0:
		if _timer <= 0.0:
			_burst_left -= 1
			_timer = _rng.randf_range(0.03, 0.18)
		# Chớp: nửa đầu mỗi nhịp tắt, nửa sau sáng lại.
		level = dip if int(_timer * 30.0) % 2 == 0 else 1.0
		if _burst_left == 0:
			_timer = _rng.randf_range(calm_range.x, calm_range.y)
	elif _timer <= 0.0:
		_burst_left = _rng.randi_range(burst_count.x, burst_count.y)
		_timer = _rng.randf_range(0.03, 0.18)
	light_energy = _base_energy * level
	if _mesh:
		_mesh.transparency = clampf(1.0 - level, 0.0, 0.8)
