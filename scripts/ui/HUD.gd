## HUD góc nhìn thứ nhất: chấm tâm ngắm, tên vật đang rọi, lời nhắc, Hotbar 5 ô
## và khung Inspect.
##
## - Tâm ngắm mờ (alpha [member idle_alpha]) khi không rọi gì, sáng rõ khi rọi
##   trúng Interactable.
## - Phím 1-5 mở khung Inspect của ô tương ứng (khóa điều khiển). Bấm lại số đó,
##   E hoặc Esc để đóng.
class_name HUD
extends CanvasLayer

@export_range(0.0, 1.0) var idle_alpha: float = 0.3

@onready var _crosshair: Control = %Crosshair
@onready var _focus_info: Control = %FocusInfo
@onready var _item_name: Label = %ItemName
@onready var _prompt: Label = %Prompt
@onready var _slots: HBoxContainer = %Slots
@onready var _inspect: Control = %InspectPanel
@onready var _inspect_title: Label = %InspectTitle
@onready var _inspect_icon: TextureRect = %InspectIcon
@onready var _inspect_desc: Label = %InspectDescription
@onready var _inspect_hint: Label = %InspectHint

var _inspect_index := -1
## Điều khiển đang bị UI khác (như DocumentViewer) khóa.
var _locked_by_other := false


func _ready() -> void:
	_inspect.visible = false
	_on_focus_changed(null)
	for i in Inventory.SLOT_COUNT:
		_update_slot(i, Inventory.get_item(i))
	EventBus.interaction_focus_changed.connect(_on_focus_changed)
	EventBus.player_controls_locked.connect(_on_controls_locked)
	Inventory.slot_changed.connect(_update_slot)


## Ẩn/hiện Hotbar (ví dụ ẩn trong phân cảnh mở đầu khi An chưa có đồ).
func set_hotbar_visible(value: bool) -> void:
	_slots.visible = value


func is_inspecting() -> bool:
	return _inspect_index != -1


func _input(event: InputEvent) -> void:
	if _locked_by_other:
		return
	for i in Inventory.SLOT_COUNT:
		if event.is_action_pressed(StringName("hotbar_%d" % (i + 1))):
			if _inspect_index == i:
				close_inspect()
			else:
				open_inspect(i)
			get_viewport().set_input_as_handled()
			return
	if is_inspecting() and (event.is_action_pressed(&"interact") or event.is_action_pressed(&"ui_cancel")):
		close_inspect()
		get_viewport().set_input_as_handled()


## Mở khung Inspect cho ô [param index]. Ô trống thì bỏ qua.
func open_inspect(index: int) -> void:
	var item := Inventory.get_item(index)
	if item == null:
		return
	var was_open := is_inspecting()
	_inspect_index = index
	_inspect_title.text = item.get_display_name()
	_inspect_icon.texture = item.icon
	_inspect_icon.visible = item.icon != null
	_inspect_desc.text = item.get_description()
	_inspect_hint.text = tr(&"UI_INSPECT_HINT")
	_inspect.visible = true
	_highlight_slot(index)
	if not was_open:
		_set_crosshair_visible(false)
		EventBus.player_controls_locked.emit(true)


func close_inspect() -> void:
	if not is_inspecting():
		return
	_inspect_index = -1
	_inspect.visible = false
	_highlight_slot(-1)
	_set_crosshair_visible(true)
	EventBus.player_controls_locked.emit(false)


func _on_focus_changed(target: Node) -> void:
	var interactable := target as Interactable
	if interactable == null:
		_crosshair.modulate.a = idle_alpha
		_focus_info.visible = false
		return
	_crosshair.modulate.a = 1.0
	_item_name.text = interactable.get_display_name()
	_prompt.text = interactable.get_prompt_text()
	_focus_info.visible = true


func _on_controls_locked(locked: bool) -> void:
	# Bỏ qua tín hiệu do chính khung Inspect phát.
	if is_inspecting():
		return
	_locked_by_other = locked
	_set_crosshair_visible(not locked)


func _set_crosshair_visible(value: bool) -> void:
	_crosshair.visible = value
	_focus_info.visible = value and _crosshair.modulate.a >= 1.0


func _update_slot(index: int, item: ItemData) -> void:
	var slot := _slots.get_child(index)
	var icon: TextureRect = slot.get_node("VBox/Icon")
	var label: Label = slot.get_node("VBox/Name")
	icon.texture = item.icon if item else null
	icon.visible = item != null and item.icon != null
	label.text = item.get_display_name() if item else ""
	if item == null and _inspect_index == index:
		close_inspect()


func _highlight_slot(index: int) -> void:
	for i in _slots.get_child_count():
		var slot: Control = _slots.get_child(i)
		slot.modulate = Color(1.0, 0.85, 0.6) if i == index else Color.WHITE
