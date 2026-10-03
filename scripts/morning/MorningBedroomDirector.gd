## Đạo diễn phân cảnh buổi sáng trong phòng ngủ của An (bố mẹ đã đi vắng).
##
## Chuỗi câu đố: nhấc gối lấy chìa khóa đồng -> mở hộc bàn có khóa -> đọc sổ
## chi tiêu 1999 (các trang bị xé theo mức 100% / 75% / 50% / 25%) -> nhập mật mã
## 2547 vào két sắt -> nhặt mảnh giấy ghi địa chỉ nhà cũ ở Thôn Đoài.
##
## Director chỉ điều phối trạng thái và lời dẫn (độc thoại, mục tiêu) qua EventBus.
## Các vật tương tác (PillowInteraction, Drawer, SafeBox) và giao diện
## (LockInspectUI, ExpenseBookUI, SafeKeypadUI) tự xử lý phần của mình.
class_name MorningBedroomDirector
extends Node3D

enum State {
	MORNING_START,    ## Fade-in, độc thoại mở đầu.
	SEARCHING,        ## Tìm manh mối trong phòng.
	KEY_FOUND,        ## Đã nhặt chìa khóa đồng dưới gối.
	DRAWER_UNLOCKED,  ## Đã mở hộc bàn có khóa.
	BOOK_READ,        ## Đã đọc sổ chi tiêu 1999.
	SAFE_OPENED,      ## Đã nhập đúng mật mã két sắt.
	ADDRESS_FOUND,    ## Đã có địa chỉ nhà cũ, sẵn sàng lên đường.
}

## Node của level gốc (DreamBedroom) bị gỡ bỏ vì đã được thay bằng bản tương tác
## (gối + gối tựa đặt trên nó, ba hộc bàn trang điểm, két sắt). Đường dẫn tính từ node [member level].
@export var removed_level_nodes: Array[NodePath] = [
	^"Bed_King/Pillow1", ^"Bed_King/Cushion",
	^"Vanity/Drawer1", ^"Vanity/Pull1",
	^"Vanity/Drawer2", ^"Vanity/Pull2",
	^"Vanity/Drawer3", ^"Vanity/Pull3",
	^"Safe",
]
@export var level: Node3D
## Chỗ An đứng khi vào cảnh (tọa độ thế giới) và hướng nhìn.
@export var spawn_position: Vector3 = Vector3(0.9, 0.05, 0.6)
@export var spawn_yaw_degrees: float = 25.0

@export_group("ID câu đố")
@export var key_item_id: StringName = &"cabinet_key"
@export var lock_id: StringName = &"desk_drawer_lock"
@export var book_id: StringName = &"expense_book_1999"
@export var safe_id: StringName = &"bedroom_safe"
@export var address_item_id: StringName = &"address_note"

@export_group("Lời dẫn")
@export var intro_delay: float = 1.2
@export var start_monologue_key: String = "MORNING_MONO_START"
@export var start_objective_key: String = "OBJ_SEARCH_ROOM"
## Độc thoại gợi ý sau lần đầu gập sổ. Để trống nếu không muốn gợi ý.
@export var book_hint_monologue_key: String = "MORNING_MONO_BOOK_TORN"
@export var final_objective_key: String = "OBJ_RIDE_TO_THON_DOAI"

var state: State = State.MORNING_START
var _player: PlayerController
var _final_objective_pending := false


func _ready() -> void:
	_remove_level_nodes()
	_place_player()
	EventBus.item_picked_up.connect(_on_item_picked_up)
	EventBus.lock_opened.connect(_on_lock_opened)
	EventBus.book_closed.connect(_on_book_closed)
	EventBus.safe_unlocked.connect(_on_safe_unlocked)
	EventBus.document_closed.connect(_on_document_closed)
	_play_intro()


func _exit_tree() -> void:
	var links := {
		EventBus.item_picked_up: _on_item_picked_up,
		EventBus.lock_opened: _on_lock_opened,
		EventBus.book_closed: _on_book_closed,
		EventBus.safe_unlocked: _on_safe_unlocked,
		EventBus.document_closed: _on_document_closed,
	}
	for sig: Signal in links:
		if sig.is_connected(links[sig]):
			sig.disconnect(links[sig])


func _play_intro() -> void:
	_set_state(State.MORNING_START)
	EventBus.player_controls_locked.emit(true)
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 0.0)
	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 2.0)
	await get_tree().create_timer(intro_delay).timeout
	if not is_inside_tree():
		return
	_monologue(start_monologue_key)
	EventBus.objective_updated.emit(tr(start_objective_key), true)
	EventBus.player_controls_locked.emit(false)
	_set_state(State.SEARCHING)


func _on_item_picked_up(item: ItemData, _slot: int) -> void:
	if item == null:
		return
	if item.id == key_item_id:
		_advance(State.KEY_FOUND)
	elif item.id == address_item_id:
		_advance(State.ADDRESS_FOUND)
		# Mục tiêu mới hiện sau khi người chơi đọc xong mảnh giấy.
		_final_objective_pending = true


func _on_lock_opened(id: StringName) -> void:
	if id == lock_id:
		_advance(State.DRAWER_UNLOCKED)


func _on_book_closed(id: StringName) -> void:
	if id != book_id or state >= State.BOOK_READ:
		return
	_advance(State.BOOK_READ)
	_monologue(book_hint_monologue_key)


func _on_safe_unlocked(id: StringName) -> void:
	if id == safe_id:
		_advance(State.SAFE_OPENED)


func _on_document_closed() -> void:
	if not _final_objective_pending:
		return
	_final_objective_pending = false
	EventBus.objective_updated.emit(tr(final_objective_key), true)
	GameManager.set_flag(&"objective_ride_to_thon_doai")


## Chỉ tiến lên, không lùi trạng thái (ví dụ đọc lại sổ sau khi đã mở két).
func _advance(new_state: State) -> void:
	if new_state > state:
		_set_state(new_state)


func _set_state(new_state: State) -> void:
	state = new_state
	EventBus.morning_state_changed.emit(new_state)


func _monologue(key: String) -> void:
	if key.is_empty():
		return
	var text := tr(key)
	EventBus.inner_monologue_requested.emit(text, maxf(3.0, text.length() * 0.06))


func _remove_level_nodes() -> void:
	if level == null:
		push_error("MorningBedroomDirector: chưa gán node level.")
		return
	for path in removed_level_nodes:
		var node := level.get_node_or_null(path)
		if node == null:
			push_warning("MorningBedroomDirector: không thấy node %s trong level." % path)
			continue
		# Gỡ hẳn (không chỉ ẩn) để va chạm CSG của bản gốc không che bản tương tác.
		node.get_parent().remove_child(node)
		node.queue_free()


func _place_player() -> void:
	_player = level.get_node_or_null(^"Player") as PlayerController if level else null
	if _player == null:
		push_error("MorningBedroomDirector: level thiếu node Player.")
		return
	_player.global_position = spawn_position
	_player.rotation = Vector3(0.0, deg_to_rad(spawn_yaw_degrees), 0.0)
