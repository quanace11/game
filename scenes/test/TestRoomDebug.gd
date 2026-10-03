## Script chỉ dùng cho phòng thử: in các sự kiện EventBus ra bảng Output.
extends Node3D


func _ready() -> void:
	EventBus.interaction_focus_changed.connect(
		func(target: Node) -> void: print("[Focus] ", target.name if target else "(không có)"))
	EventBus.interaction_requested.connect(
		func(interactable: Node, actor: Node) -> void:
			print("[Interact] ", interactable.name, " <- ", actor.name))
	EventBus.item_picked_up.connect(
		func(item: ItemData, slot: int) -> void:
			print("[Hotbar] Ô ", slot + 1, ": ", item.get_display_name()))
	EventBus.inventory_full.connect(func() -> void: print("[Hotbar] Đã đầy"))
	EventBus.document_requested.connect(
		func(title: String, pages: Array[String]) -> void:
			print("[Document] ", title, " (", pages.size(), " trang)"))
	EventBus.player_controls_locked.connect(
		func(locked: bool) -> void: print("[Controls] ", "khóa" if locked else "mở"))
	EventBus.memory_unlocked.connect(
		func(memory_id: StringName) -> void: print("[Memory] Mở khóa: ", memory_id))
	EventBus.inner_monologue_requested.connect(
		func(text: String, duration: float) -> void:
			print("[Monologue] ", text, " (", duration, "s)"))
