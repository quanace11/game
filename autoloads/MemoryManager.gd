## MemoryManager (Autoload): xử lý các Memory Trigger.
##
## Lắng nghe [signal EventBus.interaction_requested]. Khi vật được tương tác là
## Memory Trigger chưa mở khóa, nó:
##   1. phát [signal EventBus.memory_unlocked],
##   2. phát [signal EventBus.inner_monologue_requested] với câu đã dịch bằng tr(),
##   3. phát [signal EventBus.memory_effect_requested] để bật sương mờ/vignette.
## UI và hiệu ứng chỉ cần lắng nghe EventBus, không cần biết MemoryManager.
extends Node

## Thời gian mặc định (giây) cho monologue và hiệu ứng ký ức.
@export var monologue_duration: float = 3.5
@export var effect_duration: float = 4.0

var _unlocked: Dictionary[StringName, bool] = {}


func _ready() -> void:
	EventBus.interaction_requested.connect(_on_interaction_requested)


func is_unlocked(memory_id: StringName) -> bool:
	return _unlocked.has(memory_id)


func get_unlocked_ids() -> Array[StringName]:
	var ids: Array[StringName] = []
	ids.assign(_unlocked.keys())
	return ids


## Mở khóa ký ức. Trả về false nếu đã mở trước đó (không phát lại hiệu ứng).
func unlock_memory(memory_id: StringName, monologue_key: String = "") -> bool:
	if memory_id.is_empty() or is_unlocked(memory_id):
		return false
	_unlocked[memory_id] = true
	EventBus.memory_unlocked.emit(memory_id)
	if not monologue_key.is_empty():
		EventBus.inner_monologue_requested.emit(tr(monologue_key), monologue_duration)
	EventBus.memory_effect_requested.emit(memory_id, effect_duration)
	return true


func _on_interaction_requested(interactable: Node, _actor: Node) -> void:
	var target := interactable as Interactable
	if target == null or not target.is_memory_trigger():
		return
	unlock_memory(target.item_id, target.monologue_key)
