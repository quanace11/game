## Inventory (Autoload): Hotbar 5 ô của An.
##
## Interactable gọi [method add_item] khi người chơi nhặt đồ. HUD lắng nghe
## [signal slot_changed] để vẽ lại ô tương ứng.
extends Node

const SLOT_COUNT := 5

## Một ô thay đổi. [param item] là null khi ô trống.
signal slot_changed(index: int, item: ItemData)

var _slots: Array[ItemData] = []


func _ready() -> void:
	_slots.resize(SLOT_COUNT)


## Thêm vào ô trống đầu tiên. Trả về chỉ số ô, hoặc -1 nếu Hotbar đã đầy.
func add_item(item: ItemData) -> int:
	var index := _slots.find(null)
	if index == -1:
		return -1
	_slots[index] = item
	slot_changed.emit(index, item)
	EventBus.item_picked_up.emit(item, index)
	return index


func get_item(index: int) -> ItemData:
	if index < 0 or index >= SLOT_COUNT:
		return null
	return _slots[index]


func remove_item(index: int) -> ItemData:
	var item := get_item(index)
	if item != null:
		_slots[index] = null
		slot_changed.emit(index, null)
	return item


func has_item(id: StringName) -> bool:
	return _slots.any(func(item: ItemData) -> bool: return item != null and item.id == id)


func is_full() -> bool:
	return _slots.find(null) == -1
