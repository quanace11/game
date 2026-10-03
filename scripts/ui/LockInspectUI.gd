## Giao diện soi cận cảnh ổ khóa tròn trên hộc bàn (CanvasLayer).
##
## Mở khi nhận [signal EventBus.lock_inspect_requested]. Khóa điều khiển của An
## và giữ chuột bị khóa (giao diện chỉ dùng bàn phím).
## - Phím số 1-5: dùng vật trong ô Hotbar tương ứng. Đúng chìa thì chạy hoạt ảnh
##   chìa bay khớp vào lỗ (Tween vị trí), tra vào, tự vặn 90 độ (Tween xoay),
##   tiếng tách chốt, tự đóng giao diện rồi phát [signal EventBus.lock_opened].
##   Sai vật thì ổ khóa rung nhẹ.
## - E hoặc Esc: thoát, camera trở lại bình thường.
## Dùng _input (chạy trước _unhandled_input) để phím không lọt xuống người chơi.
class_name LockInspectUI
extends CanvasLayer

const BRASS := Color(0.85, 0.68, 0.38)
const BRASS_DARK := Color(0.52, 0.38, 0.18)
const BRASS_LIGHT := Color(1.0, 0.9, 0.62)
const WOOD := Color(0.86, 0.82, 0.74)
const WOOD_DARK := Color(0.62, 0.56, 0.47)
const HOLE := Color(0.03, 0.025, 0.02)
## Tâm lỗ khóa so với tâm mặt ổ khóa (pixel).
const KEYHOLE_OFFSET := Vector2(0, -26)
const PLATE_RADIUS := 120.0
const KEY_LENGTH := 150.0
const BOW_RADIUS := 44.0

@export var show_cursor: bool = false
@export var fly_duration: float = 0.7
@export var insert_duration: float = 0.35
@export var turn_duration: float = 0.45
@export var key_sfx: StringName = &"sfx_key_insert"
@export var unlock_sfx: StringName = &"sfx_lock_click"
@export var wrong_sfx: StringName = &"sfx_drawer_locked"

@onready var _lock_art: Control = %LockArt
@onready var _key_art: Control = %KeyArt
@onready var _title: Label = %Title
@onready var _hint: Label = %Hint

var _lock_id: StringName
var _key_item_id: StringName
var _busy := false
var _tween: Tween
## Độ tra chìa vào ổ: 0 = chưa vào, 1 = đã vào hết (chuôi sát mặt ổ).
var _insert := 0.0


func _ready() -> void:
	visible = false
	_key_art.visible = false
	_lock_art.draw.connect(_draw_lock)
	_key_art.draw.connect(_draw_key)
	EventBus.lock_inspect_requested.connect(open)


func _exit_tree() -> void:
	if EventBus.lock_inspect_requested.is_connected(open):
		EventBus.lock_inspect_requested.disconnect(open)
	if _tween:
		_tween.kill()
	if visible:
		UIModal.close()


func is_open() -> bool:
	return visible


func open(lock_id: StringName, key_item_id: StringName) -> void:
	if visible:
		return
	_lock_id = lock_id
	_key_item_id = key_item_id
	_busy = false
	_insert = 0.0
	_key_art.visible = false
	_key_art.rotation = 0.0
	_lock_art.scale = Vector2.ONE
	_title.text = tr(&"UI_LOCK_TITLE")
	_update_hint()
	visible = true
	_lock_art.pivot_offset = _lock_art.size * 0.5
	UIModal.open(show_cursor)
	# Phóng to cận cảnh: ổ khóa "lao" tới từ nhỏ đến lớn.
	_lock_art.scale = Vector2.ONE * 0.6
	_lock_art.modulate.a = 0.0
	_tween = create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_tween.tween_property(_lock_art, "scale", Vector2.ONE, 0.3)
	_tween.tween_property(_lock_art, "modulate:a", 1.0, 0.2)


func close() -> void:
	if not visible:
		return
	if _tween:
		_tween.kill()
	visible = false
	_busy = false
	UIModal.close()


func _input(event: InputEvent) -> void:
	if not visible:
		return
	if _busy:
		# Đang chạy hoạt ảnh mở khóa: nuốt mọi phím.
		if event is InputEventKey:
			get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed(&"interact") or event.is_action_pressed(&"ui_cancel"):
		close()
		get_viewport().set_input_as_handled()
		return
	for i in Inventory.SLOT_COUNT:
		if event.is_action_pressed(StringName("hotbar_%d" % (i + 1))):
			_use_slot(i)
			get_viewport().set_input_as_handled()
			return


func _use_slot(index: int) -> void:
	var item := Inventory.get_item(index)
	if item == null:
		return
	if item.id != _key_item_id:
		_rattle()
		return
	Inventory.remove_item(index)
	_play_unlock(index)


func _rattle() -> void:
	EventBus.ui_sfx_requested.emit(wrong_sfx)
	if _tween:
		_tween.kill()
	_tween = create_tween()
	for angle: float in [-2.5, 2.0, -1.0, 0.0]:
		_tween.tween_property(_lock_art, "rotation", deg_to_rad(angle), 0.04)


func _play_unlock(slot_index: int) -> void:
	_busy = true
	_hint.text = ""
	var keyhole := _keyhole_position()
	var viewport_size := get_viewport().get_visible_rect().size
	# Chìa bay lên từ đúng ô Hotbar đang giữ nó (Hotbar nằm giữa đáy màn hình).
	var from := Vector2(viewport_size.x * 0.5 + (slot_index - 2) * 84.0, viewport_size.y - 40.0)
	_insert = 0.0
	_key_art.position = from
	_key_art.rotation = deg_to_rad(-35.0)
	_key_art.scale = Vector2.ONE * 1.35
	_key_art.modulate.a = 0.0
	_key_art.visible = true
	_key_art.queue_redraw()

	if _tween:
		_tween.kill()
	_tween = create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	# 1. Bay khớp vào lỗ khóa.
	_tween.tween_property(_key_art, "modulate:a", 1.0, 0.15)
	_tween.parallel().tween_property(_key_art, "position", keyhole, fly_duration)
	_tween.parallel().tween_property(_key_art, "rotation", 0.0, fly_duration)
	_tween.parallel().tween_property(_key_art, "scale", Vector2.ONE, fly_duration)
	# 2. Tra chìa vào trong ổ.
	_tween.tween_callback(EventBus.ui_sfx_requested.emit.bind(key_sfx))
	_tween.tween_method(_set_insert, 0.0, 1.0, insert_duration).set_trans(Tween.TRANS_SINE)
	# 3. Tự vặn 90 độ, tách chốt.
	_tween.tween_interval(0.15)
	_tween.tween_property(_key_art, "rotation", deg_to_rad(90.0), turn_duration) \
			.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_callback(_on_unlatched)
	_tween.tween_property(_lock_art, "scale", Vector2.ONE * 1.04, 0.06)
	_tween.tween_property(_lock_art, "scale", Vector2.ONE, 0.12)
	_tween.tween_interval(0.55)
	_tween.tween_callback(_finish_unlock)


func _set_insert(value: float) -> void:
	_insert = value
	_key_art.queue_redraw()


func _on_unlatched() -> void:
	EventBus.ui_sfx_requested.emit(unlock_sfx)
	EventBus.camera_shake_requested.emit(0.002, 0.15)


func _finish_unlock() -> void:
	var lock_id := _lock_id
	close()
	EventBus.lock_opened.emit(lock_id)


func _keyhole_position() -> Vector2:
	return _lock_art.get_global_rect().get_center() + KEYHOLE_OFFSET


func _key_slot() -> int:
	for i in Inventory.SLOT_COUNT:
		var item := Inventory.get_item(i)
		if item != null and item.id == _key_item_id:
			return i
	return -1


func _update_hint() -> void:
	var slot := _key_slot()
	if slot == -1:
		_hint.text = tr(&"UI_LOCK_HINT_NO_KEY")
	else:
		var item := Inventory.get_item(slot)
		_hint.text = tr(&"UI_LOCK_HINT_USE").format({"slot": slot + 1, "item": item.get_display_name()})


# --- Vẽ -----------------------------------------------------------------------

func _draw_lock() -> void:
	var c := _lock_art.size * 0.5
	# Mặt gỗ hộc bàn.
	var face := Rect2(Vector2(0, c.y - 150), Vector2(_lock_art.size.x, 300))
	_lock_art.draw_rect(face, WOOD)
	_lock_art.draw_rect(face, WOOD_DARK, false, 3.0)
	for i in 6:
		var y := face.position.y + 22.0 + i * 48.0
		_lock_art.draw_line(Vector2(8, y), Vector2(_lock_art.size.x - 8, y + 6), Color(WOOD_DARK, 0.25), 2.0)
	# Mặt ổ khóa tròn bằng đồng.
	_lock_art.draw_circle(c + Vector2(4, 6), PLATE_RADIUS, Color(0, 0, 0, 0.35))
	_lock_art.draw_circle(c, PLATE_RADIUS, BRASS_DARK)
	_lock_art.draw_circle(c, PLATE_RADIUS - 8, BRASS)
	_lock_art.draw_arc(c, PLATE_RADIUS - 20, PI * 1.05, PI * 1.6, 24, Color(BRASS_LIGHT, 0.7), 6.0)
	_lock_art.draw_arc(c, PLATE_RADIUS - 4, 0, TAU, 48, Color(BRASS_DARK, 0.9), 2.0)
	for angle: float in [PI * 0.25, PI * 0.75, PI * 1.25, PI * 1.75]:
		var screw := c + Vector2.from_angle(angle) * (PLATE_RADIUS - 24)
		_lock_art.draw_circle(screw, 7, BRASS_DARK)
		_lock_art.draw_line(screw - Vector2(5, 0).rotated(angle), screw + Vector2(5, 0).rotated(angle), HOLE, 2.0)
	# Lỗ tra chìa: lỗ tròn phía trên + rãnh thang phía dưới.
	var hole := c + KEYHOLE_OFFSET
	_lock_art.draw_circle(hole, 22, BRASS_DARK)
	_lock_art.draw_circle(hole, 17, HOLE)
	_lock_art.draw_colored_polygon(PackedVector2Array([
		hole + Vector2(-8, 8), hole + Vector2(8, 8), hole + Vector2(15, 66), hole + Vector2(-15, 66),
	]), HOLE)


## Chìa vẽ với gốc tọa độ ở đầu chìa (mũi chìa hướng lên). Khi tra vào
## ([member _insert] tăng), phần thân bị "nuốt" dần vào lỗ.
func _draw_key() -> void:
	var visible_shaft := KEY_LENGTH * (1.0 - 0.8 * _insert)
	# Răng chìa: chỉ thấy khi chìa còn ở ngoài ổ.
	if _insert <= 0.0:
		_key_art.draw_colored_polygon(PackedVector2Array([
			Vector2(5, 6), Vector2(22, 6), Vector2(22, 16), Vector2(15, 16),
			Vector2(15, 24), Vector2(24, 24), Vector2(24, 38), Vector2(5, 38),
		]), BRASS)
	# Thân chìa (chỉ phần còn ở ngoài lỗ, từ mũi tới chuôi).
	_key_art.draw_rect(Rect2(-6, 0, 12, visible_shaft), BRASS)
	_key_art.draw_rect(Rect2(-6, 0, 4, visible_shaft), BRASS_LIGHT)
	# Cổ chìa và chuôi tròn có lỗ xỏ dây.
	var bow := Vector2(0, visible_shaft + BOW_RADIUS - 6)
	_key_art.draw_rect(Rect2(-14, visible_shaft - 8, 28, 10), BRASS_DARK)
	_key_art.draw_circle(bow + Vector2(3, 4), BOW_RADIUS, Color(0, 0, 0, 0.3))
	_key_art.draw_circle(bow, BOW_RADIUS, BRASS)
	_key_art.draw_arc(bow, BOW_RADIUS - 6, PI * 1.1, PI * 1.6, 16, BRASS_LIGHT, 4.0)
	_key_art.draw_circle(bow, 15, Color(0.05, 0.04, 0.03, 0.85))
	# Lỗ khóa "nuốt" mũi chìa: phủ một vòng tối ở gốc khi đã tra vào.
	if _insert > 0.0:
		_key_art.draw_circle(Vector2.ZERO, 9.0 * _insert, HOLE)
