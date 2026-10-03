## Script chỉ dùng cho phòng thử: in các sự kiện EventBus ra bảng Output
## để kiểm tra tương tác khi chưa có UI.
extends Node3D


func _ready() -> void:
	EventBus.interaction_prompt_changed.connect(
		func(text: String) -> void: print("[Prompt] ", text if text else "(ẩn)"))
	EventBus.interaction_requested.connect(
		func(interactable: Node, actor: Node) -> void:
			print("[Interact] ", interactable.name, " <- ", actor.name))
	EventBus.memory_unlocked.connect(
		func(memory_id: StringName) -> void: print("[Memory] Mở khóa: ", memory_id))
	EventBus.inner_monologue_requested.connect(
		func(text: String, duration: float) -> void:
			print("[Monologue] ", text, " (", duration, "s)"))
	EventBus.memory_effect_requested.connect(
		func(memory_id: StringName, duration: float) -> void:
			print("[Effect] Sương mờ/vignette cho ", memory_id, " trong ", duration, "s"))
