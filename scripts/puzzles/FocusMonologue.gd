## Hiện một câu độc thoại nội tâm khi tâm ngắm rọi trúng Interactable cha lần đầu.
##
## Gắn làm con của một Interactable (ví dụ cuốn sổ trong hộc bàn). Chỉ chạy
## một lần duy nhất rồi tự ngắt kết nối.
class_name FocusMonologue
extends Node

@export var monologue_key: String
@export var duration: float = 3.5

var _done := false


func _ready() -> void:
	EventBus.interaction_focus_changed.connect(_on_focus_changed)


func _exit_tree() -> void:
	if EventBus.interaction_focus_changed.is_connected(_on_focus_changed):
		EventBus.interaction_focus_changed.disconnect(_on_focus_changed)


func _on_focus_changed(target: Node) -> void:
	if _done or target == null or target != get_parent() or monologue_key.is_empty():
		return
	_done = true
	EventBus.inner_monologue_requested.emit(tr(monologue_key), duration)
	EventBus.interaction_focus_changed.disconnect(_on_focus_changed)
