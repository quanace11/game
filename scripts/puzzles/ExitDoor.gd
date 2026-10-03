## Cửa ra khỏi một cảnh: bấm E để hé cửa, màn hình tối dần rồi chuyển sang
## [member next_scene_path].
##
## Cửa chỉ mở khi GameManager đã có cờ [member required_flag] (để trống = luôn mở).
## Chưa đủ điều kiện thì cửa rung nhẹ, kêu cạch và An nói [member not_ready_monologue_key].
##
## Phần nhìn thấy của cánh cửa có thể nằm trong level gốc: liệt kê các node đó
## trong [member leaf_nodes], cửa sẽ chuyển chúng vào node bản lề lúc chạy
## (giữ nguyên vị trí) để xoay cùng bản lề mà không phải sửa scene level.
class_name ExitDoor
extends Interactable

## Phát ngay trước khi đổi scene (sau khi màn hình đã tối hẳn).
signal leaving

@export_file("*.tscn") var next_scene_path: String
@export var required_flag: StringName
@export var not_ready_monologue_key: String = "MORNING_MONO_DOOR_NOT_YET"

@export_group("Cánh cửa")
## Node bản lề, cánh cửa xoay quanh trục Y của node này.
@export var hinge: Node3D
## Các node mesh của cánh cửa (thường nằm trong level gốc) sẽ được gắn vào [member hinge].
@export var leaf_nodes: Array[NodePath] = []
## Góc hé cửa (độ). Âm = mở vào trong phòng (về phía +Z cục bộ).
@export var open_angle_degrees: float = -28.0
@export var open_duration: float = 1.4
@export var fade_duration: float = 1.2
## Biên độ rung (độ) khi cửa chưa mở được.
@export var rattle_degrees: float = 1.2

@export_group("Âm thanh")
@export var open_sfx: StringName = &"sfx_door_open"
@export var locked_sfx: StringName = &"sfx_door_locked"

var _tween: Tween
var _leaving := false


func _ready() -> void:
	super()
	if prompt_text_key.is_empty():
		prompt_text_key = "PROMPT_OPEN_DOOR"
	# Đợi level gốc dựng xong rồi mới chuyển các node cánh cửa sang bản lề.
	_attach_leaf_nodes.call_deferred()


func _exit_tree() -> void:
	if _tween:
		_tween.kill()


func is_ready_to_leave() -> bool:
	return required_flag.is_empty() or GameManager.has_flag(required_flag)


func interact(actor: Node) -> bool:
	if not enabled or _leaving:
		return false
	interacted.emit(actor)
	EventBus.interaction_requested.emit(self, actor)
	if not is_ready_to_leave():
		_rattle()
		return true
	_leave()
	return true


func _rattle() -> void:
	if not locked_sfx.is_empty():
		EventBus.sfx_requested.emit(locked_sfx, global_position)
	if not not_ready_monologue_key.is_empty():
		var text := tr(not_ready_monologue_key)
		EventBus.inner_monologue_requested.emit(text, maxf(3.0, text.length() * 0.06))
	if hinge == null:
		return
	if _tween:
		_tween.kill()
	var a := deg_to_rad(rattle_degrees)
	_tween = create_tween()
	_tween.tween_property(hinge, "rotation:y", -a, 0.05)
	_tween.tween_property(hinge, "rotation:y", a * 0.5, 0.05)
	_tween.tween_property(hinge, "rotation:y", 0.0, 0.06)


func _leave() -> void:
	_leaving = true
	enabled = false
	EventBus.player_controls_locked.emit(true)
	EventBus.subtitles_cleared.emit()
	if not open_sfx.is_empty():
		EventBus.sfx_requested.emit(open_sfx, global_position)
	if _tween:
		_tween.kill()
	_tween = create_tween().set_parallel()
	if hinge:
		_tween.tween_property(hinge, "rotation:y", deg_to_rad(open_angle_degrees), open_duration) \
				.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	# Màn hình tối dần ngay khi cửa bắt đầu hé (không để lộ khoảng trống sau cửa).
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, fade_duration)
	_tween.tween_interval(maxf(open_duration, fade_duration) + 0.3)
	await _tween.finished
	if not is_inside_tree():
		return
	leaving.emit()
	if next_scene_path.is_empty():
		push_warning("ExitDoor %s: chưa gán next_scene_path." % name)
		return
	get_tree().change_scene_to_file(next_scene_path)


func _attach_leaf_nodes() -> void:
	if hinge == null:
		return
	for path in leaf_nodes:
		var node := get_node_or_null(path) as Node3D
		if node == null:
			push_warning("ExitDoor %s: không thấy node cánh cửa %s." % [name, path])
			continue
		node.reparent(hinge, true)
