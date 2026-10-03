## GameManager (Autoload): lưu các cờ trạng thái cốt truyện / câu đố.
##
## Tự đặt cờ "has_<item_id>" mỗi khi An nhặt một vật vào Hotbar, ví dụ nhặt
## chìa khóa đồng (item_id = cabinet_key) thì [member has_cabinet_key] = true.
## Các hệ thống khác đặt cờ riêng bằng [method set_flag] và lắng nghe
## [signal EventBus.story_flag_changed].
extends Node

var _flags: Dictionary[StringName, bool] = {}

## Đã nhặt chìa khóa đồng mở hộc bàn có khóa.
var has_cabinet_key: bool:
	get:
		return has_flag(&"has_cabinet_key")
	set(value):
		set_flag(&"has_cabinet_key", value)


func _ready() -> void:
	EventBus.item_picked_up.connect(_on_item_picked_up)


func has_flag(flag: StringName) -> bool:
	return _flags.get(flag, false)


func set_flag(flag: StringName, value: bool = true) -> void:
	if flag.is_empty() or has_flag(flag) == value:
		return
	_flags[flag] = value
	EventBus.story_flag_changed.emit(flag, value)


## Xóa toàn bộ cờ (bắt đầu ván mới).
func reset() -> void:
	_flags.clear()


func _on_item_picked_up(item: ItemData, _slot_index: int) -> void:
	if item != null and not item.id.is_empty():
		set_flag(StringName("has_%s" % item.id))
