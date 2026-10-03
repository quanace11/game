## Hộc bàn kéo ra / đẩy vào được, có thể bị khóa.
##
## Node gốc là Area3D (Interactable) đặt đúng vị trí mặt hộc khi đóng; hộc
## trượt theo trục +Z cục bộ của chính nó [member open_distance] mét.
##
## Hộc thường: [E] Kéo hộc tủ / [E] Đẩy hộc tủ, trượt bằng Tween kèm tiếng gỗ.
##
## Hộc có khóa ([member locked] = true):
## - Chưa có chìa trong Hotbar: hộc rung giật nhẹ + tiếng cạch kẹt, độc thoại
##   [member locked_monologue_key] (chỉ một lần), rồi tự mở LockInspectUI.
## - Đã có chìa: bấm E mở thẳng LockInspectUI.
## - LockInspectUI phát [signal EventBus.lock_opened] với [member lock_id] khớp
##   thì hộc mở khóa, hiện chìa cắm trong ổ và từ từ trượt ra.
##
## Các Interactable con (đồ trong hộc) chỉ bật tương tác khi hộc đang mở hẳn.
class_name Drawer
extends Interactable

signal opened
signal closed
signal unlocked

@export var open_distance: float = 0.3
@export var slide_duration: float = 0.55

@export_group("Ổ khóa")
@export var locked: bool = false
## ID ổ khóa, khớp với tín hiệu LockInspectUI phát ra.
@export var lock_id: StringName = &"desk_drawer_lock"
## ID vật phẩm mở được ổ này.
@export var key_item_id: StringName = &"cabinet_key"
@export var locked_monologue_key: String = "MORNING_MONO_DRAWER_LOCKED"
## Biên độ rung giật (mét) khi kéo hộc đang khóa.
@export var rattle_distance: float = 0.012

@export_group("Lời nhắc")
@export var pull_prompt_key: String = "PROMPT_DRAWER_PULL"
@export var push_prompt_key: String = "PROMPT_DRAWER_PUSH"
@export var inspect_lock_prompt_key: String = "PROMPT_DRAWER_INSPECT_LOCK"

@export_group("Âm thanh")
@export var slide_sfx: StringName = &"sfx_drawer_slide"
@export var locked_sfx: StringName = &"sfx_drawer_locked"

var is_open := false
var _closed_position: Vector3
var _tween: Tween
var _busy := false
## Người chơi đã thử kéo hộc khóa ít nhất một lần.
var _tried_locked := false

@onready var _keyhole: Node3D = get_node_or_null(^"Keyhole")
@onready var _inserted_key: Node3D = get_node_or_null(^"Keyhole/InsertedKey")


func _ready() -> void:
	super()
	_closed_position = position
	if _keyhole:
		_keyhole.visible = locked
	if _inserted_key:
		_inserted_key.visible = false
	_set_contents_enabled(false)
	EventBus.lock_opened.connect(_on_lock_opened)


func _exit_tree() -> void:
	if EventBus.lock_opened.is_connected(_on_lock_opened):
		EventBus.lock_opened.disconnect(_on_lock_opened)
	if _tween:
		_tween.kill()


func get_prompt_text() -> String:
	if locked and (_tried_locked or Inventory.has_item(key_item_id)):
		return tr(inspect_lock_prompt_key)
	return tr(push_prompt_key) if is_open else tr(pull_prompt_key)


func interact(actor: Node) -> bool:
	if not enabled or _busy:
		return false
	interacted.emit(actor)
	EventBus.interaction_requested.emit(self, actor)
	if locked:
		_try_locked()
	else:
		toggle()
	return true


## Kéo ra nếu đang đóng, đẩy vào nếu đang mở.
func toggle() -> void:
	if locked:
		return
	_busy = true
	is_open = not is_open
	if not is_open:
		_set_contents_enabled(false)
	EventBus.sfx_requested.emit(slide_sfx, global_position)
	var offset := _slide_axis() * (open_distance if is_open else 0.0)
	_tween = create_tween().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	_tween.tween_property(self, "position", _closed_position + offset, slide_duration)
	_tween.tween_callback(_on_slide_finished)


func _try_locked() -> void:
	if Inventory.has_item(key_item_id):
		_tried_locked = true
		EventBus.lock_inspect_requested.emit(lock_id, key_item_id)
		return

	# Chưa có chìa: hộc chỉ rung giật nhẹ rồi kẹt cứng.
	_busy = true
	EventBus.sfx_requested.emit(locked_sfx, global_position)
	EventBus.camera_shake_requested.emit(0.003, 0.2)
	if not _tried_locked and not locked_monologue_key.is_empty():
		EventBus.inner_monologue_requested.emit(tr(locked_monologue_key), 3.5)
	_tried_locked = true

	var axis := _slide_axis()
	_tween = create_tween().set_trans(Tween.TRANS_SINE)
	for amount: float in [1.0, -0.3, 0.7, 0.0]:
		_tween.tween_property(self, "position", _closed_position + axis * rattle_distance * amount, 0.05)
	_tween.tween_interval(0.25)
	_tween.tween_callback(_after_rattle)


func _after_rattle() -> void:
	_busy = false
	if locked and is_inside_tree():
		EventBus.lock_inspect_requested.emit(lock_id, key_item_id)


func _on_lock_opened(id: StringName) -> void:
	if id != lock_id or not locked:
		return
	locked = false
	if _inserted_key:
		_inserted_key.visible = true
	GameManager.set_flag(StringName("unlocked_%s" % lock_id))
	unlocked.emit()
	# Chờ giao diện soi ổ khóa đóng hẳn rồi mới trượt hộc ra.
	_busy = true
	_tween = create_tween()
	_tween.tween_interval(0.4)
	_tween.tween_callback(func() -> void:
		_busy = false
		if not is_open:
			toggle())


func _on_slide_finished() -> void:
	_busy = false
	if is_open:
		_set_contents_enabled(true)
		opened.emit()
	else:
		closed.emit()


func _slide_axis() -> Vector3:
	return transform.basis.z.normalized()


func _set_contents_enabled(value: bool) -> void:
	for node in find_children("*", "Interactable", true, false):
		(node as Interactable).enabled = value
