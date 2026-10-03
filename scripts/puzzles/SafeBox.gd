## Két sắt có bàn phím mật mã.
##
## Bấm E: phát [signal EventBus.keypad_requested] để SafeKeypadUI mở. Khi nhận
## [signal EventBus.safe_unlocked] với [member safe_id] khớp, cánh cửa (xoay
## quanh node bản lề [member door_hinge]) tự mở hé ra, vùng tương tác của két
## tắt để tâm ngắm rọi được đồ bên trong, và đồ bên trong bật tương tác.
class_name SafeBox
extends Interactable

signal opened

@export var safe_id: StringName = &"bedroom_safe"
## Mật mã đúng (dãy số).
@export var code: String = "2547"
## Node bản lề, cánh cửa là con của node này.
@export var door_hinge: Node3D
## Góc mở hé (độ) quanh trục Y của bản lề. Âm = mở về phía trước két.
@export var open_angle_degrees: float = -80.0
@export var open_duration: float = 1.6
@export var door_sfx: StringName = &"sfx_safe_door"
## Đồ trong két (tắt tương tác cho tới khi cửa mở). Để trống thì tự tìm trong node "Contents".
@export var contents_root: Node3D

var is_opened := false
var _tween: Tween

@onready var _shape: CollisionShape3D = get_node_or_null(^"CollisionShape3D")


func _ready() -> void:
	super()
	if prompt_text_key.is_empty():
		prompt_text_key = "PROMPT_SAFE_KEYPAD"
	if contents_root == null:
		contents_root = get_node_or_null(^"Contents") as Node3D
	_set_contents_enabled(false)
	EventBus.safe_unlocked.connect(_on_safe_unlocked)


func _exit_tree() -> void:
	if EventBus.safe_unlocked.is_connected(_on_safe_unlocked):
		EventBus.safe_unlocked.disconnect(_on_safe_unlocked)
	if _tween:
		_tween.kill()


func interact(actor: Node) -> bool:
	if not enabled or is_opened:
		return false
	interacted.emit(actor)
	EventBus.interaction_requested.emit(self, actor)
	EventBus.keypad_requested.emit(safe_id, code)
	return true


func _on_safe_unlocked(id: StringName) -> void:
	if id != safe_id or is_opened:
		return
	is_opened = true
	enabled = false
	# Vùng tương tác bao mặt trước két: tắt đi để không che đồ bên trong.
	if _shape:
		_shape.set_deferred(&"disabled", true)
	GameManager.set_flag(StringName("opened_%s" % safe_id))
	EventBus.sfx_requested.emit(door_sfx, global_position)
	if door_hinge == null:
		_on_door_opened()
		return
	_tween = create_tween().set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	_tween.tween_interval(0.3)
	_tween.tween_property(door_hinge, "rotation:y", deg_to_rad(open_angle_degrees), open_duration)
	_tween.tween_callback(_on_door_opened)


func _on_door_opened() -> void:
	_set_contents_enabled(true)
	opened.emit()


func _set_contents_enabled(value: bool) -> void:
	if contents_root == null:
		return
	for node in contents_root.find_children("*", "Interactable", true, false):
		(node as Interactable).enabled = value
