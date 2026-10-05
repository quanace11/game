## Giao diện chọn đáp án nhiều hàng (CanvasLayer): khóa số, xếp biển bến, bấm vé...
##
## Mở khi nhận [signal EventBus.selector_requested]. Mỗi hàng là một danh sách lựa
## chọn, người chơi xoay vòng từng hàng rồi xác nhận.
## - W/S hoặc mũi tên Lên/Xuống: chọn hàng. A/D hoặc Trái/Phải: đổi lựa chọn.
## - E / Enter: xác nhận. Esc: thoát, không tính gì.
## - Có đáp án: sai thì nháy đỏ và giữ nguyên (hoặc đóng luôn nếu [code]close_on_wrong[/code]),
##   đúng thì nháy xanh rồi đóng. Không có đáp án: đóng ngay và trả lựa chọn về.
## Kết quả trả qua [signal EventBus.selector_submitted].
class_name SelectorPuzzleUI
extends CanvasLayer

const COLOR_ROW := Color(0.16, 0.15, 0.13)
const COLOR_ROW_SELECTED := Color(0.93, 0.9, 0.82)
const COLOR_TEXT := Color(0.9, 0.88, 0.82)
const COLOR_TEXT_SELECTED := Color(0.08, 0.07, 0.06)
const COLOR_WRONG := Color(0.9, 0.3, 0.25)
const COLOR_RIGHT := Color(0.45, 0.85, 0.5)

@export var right_hold: float = 0.7
@export var wrong_hold: float = 0.9
@export var tick_sfx: StringName = &"sfx_dial_tick"
@export var wrong_sfx: StringName = &"sfx_keypad_error"
@export var right_sfx: StringName = &"sfx_lock_click"

var _puzzle_id: StringName
var _rows: Array = []
var _answer: Array = []
var _close_on_wrong := false
var _selection: Array[int] = []
var _row := 0
var _busy := false
var _tween: Tween

var _title: Label
var _list: VBoxContainer
var _status: Label
var _hint: Label
var _row_panels: Array[PanelContainer] = []
var _row_values: Array[Label] = []
var _row_names: Array[Label] = []
var _row_arrows: Array[Array] = []


func _ready() -> void:
	layer = 4
	visible = false
	_build()
	EventBus.selector_requested.connect(open)


func _exit_tree() -> void:
	if EventBus.selector_requested.is_connected(open):
		EventBus.selector_requested.disconnect(open)
	if _tween:
		_tween.kill()
	if visible:
		UIModal.close()


func is_open() -> bool:
	return visible


## [param rows]: mỗi phần tử là Dictionary {"label": String, "options": Array[String]} đã dịch.
## [param answer]: chỉ số lựa chọn đúng của từng hàng; rỗng = không kiểm tra.
func open(puzzle_id: StringName, title: String, rows: Array, answer: Array, close_on_wrong: bool) -> void:
	if visible or rows.is_empty():
		return
	_puzzle_id = puzzle_id
	_rows = rows
	_answer = answer
	_close_on_wrong = close_on_wrong
	_busy = false
	_title.text = title
	_hint.text = tr(&"UI_SELECTOR_HINT")
	_status.text = ""
	_selection.clear()
	for child in _list.get_children():
		child.queue_free()
	_row_panels.clear()
	_row_values.clear()
	_row_names.clear()
	_row_arrows.clear()
	for row: Dictionary in rows:
		_selection.append(0)
		_add_row(String(row.get("label", "")))
	_row = 0
	_refresh()
	visible = true
	UIModal.open(false)


func close() -> void:
	if not visible:
		return
	if _tween:
		_tween.kill()
	visible = false
	_busy = false
	UIModal.close()


func get_selection() -> Array[int]:
	return _selection.duplicate()


func _input(event: InputEvent) -> void:
	if not visible:
		return
	if _busy:
		if event is InputEventKey or event is InputEventMouseButton:
			get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed(&"ui_cancel"):
		close()
	elif event.is_action_pressed(&"interact") or event.is_action_pressed(&"ui_accept"):
		_submit()
	elif event.is_action_pressed(&"move_forward") or event.is_action_pressed(&"ui_up"):
		_move_row(-1)
	elif event.is_action_pressed(&"move_back") or event.is_action_pressed(&"ui_down"):
		_move_row(1)
	elif event.is_action_pressed(&"move_left") or event.is_action_pressed(&"ui_left"):
		_cycle(-1)
	elif event.is_action_pressed(&"move_right") or event.is_action_pressed(&"ui_right"):
		_cycle(1)
	else:
		return
	get_viewport().set_input_as_handled()


func _move_row(step: int) -> void:
	_row = wrapi(_row + step, 0, _rows.size())
	_refresh()


func _cycle(step: int) -> void:
	var options: Array = _rows[_row].get("options", [])
	if options.is_empty():
		return
	_selection[_row] = wrapi(_selection[_row] + step, 0, options.size())
	EventBus.ui_sfx_requested.emit(tick_sfx)
	_status.text = ""
	_refresh()


func _submit() -> void:
	var selection := get_selection()
	if _answer.is_empty():
		_finish(selection, true)
		return
	var correct := true
	for i in _answer.size():
		if i >= selection.size() or selection[i] != int(_answer[i]):
			correct = false
			break
	_busy = true
	if _tween:
		_tween.kill()
	_tween = create_tween()
	if correct:
		EventBus.ui_sfx_requested.emit(right_sfx)
		_set_status(tr(&"UI_SELECTOR_RIGHT"), COLOR_RIGHT)
		_tween.tween_interval(right_hold)
		_tween.tween_callback(_finish.bind(selection, true))
		return
	EventBus.ui_sfx_requested.emit(wrong_sfx)
	_set_status(tr(&"UI_SELECTOR_WRONG"), COLOR_WRONG)
	if _close_on_wrong:
		_tween.tween_interval(wrong_hold * 0.6)
		_tween.tween_callback(_finish.bind(selection, false))
		return
	for i in 3:
		_tween.tween_callback(_status.set_modulate.bind(Color(1, 1, 1, 0.3)))
		_tween.tween_interval(wrong_hold / 6.0)
		_tween.tween_callback(_status.set_modulate.bind(Color.WHITE))
		_tween.tween_interval(wrong_hold / 6.0)
	_tween.tween_callback(func() -> void: _busy = false)


func _finish(selection: Array[int], correct: bool) -> void:
	var id := _puzzle_id
	close()
	EventBus.selector_submitted.emit(id, selection, correct)


func _set_status(text: String, c: Color) -> void:
	_status.text = text
	_status.add_theme_color_override(&"font_color", c)
	_status.modulate = Color.WHITE


func _refresh() -> void:
	for i in _row_panels.size():
		var selected := i == _row
		var style := _row_panels[i].get_theme_stylebox(&"panel") as StyleBoxFlat
		style.bg_color = COLOR_ROW_SELECTED if selected else COLOR_ROW
		var text_color := COLOR_TEXT_SELECTED if selected else COLOR_TEXT
		_row_names[i].add_theme_color_override(&"font_color", text_color)
		_row_values[i].add_theme_color_override(&"font_color", text_color)
		for arrow: Label in _row_arrows[i]:
			arrow.add_theme_color_override(&"font_color", text_color)
		var options: Array = _rows[i].get("options", [])
		_row_values[i].text = String(options[_selection[i]]) if not options.is_empty() else ""


# --- Dựng giao diện -----------------------------------------------------------

func _build() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0.02, 0.015, 0.01, 0.75)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	var body := PanelContainer.new()
	body.custom_minimum_size = Vector2(560, 0)
	body.add_theme_stylebox_override(&"panel", _make_style(Color(0.09, 0.085, 0.075), Color(0.42, 0.36, 0.26), 26))
	center.add_child(body)
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override(&"separation", 14)
	body.add_child(vbox)

	_title = Label.new()
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_title.add_theme_font_size_override(&"font_size", 20)
	_title.add_theme_color_override(&"font_color", Color(0.85, 0.8, 0.68))
	vbox.add_child(_title)

	_list = VBoxContainer.new()
	_list.add_theme_constant_override(&"separation", 8)
	vbox.add_child(_list)

	_status = Label.new()
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status.add_theme_font_size_override(&"font_size", 18)
	_status.custom_minimum_size = Vector2(0, 26)
	vbox.add_child(_status)

	_hint = Label.new()
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hint.add_theme_font_size_override(&"font_size", 13)
	_hint.add_theme_color_override(&"font_color", Color(0.6, 0.58, 0.54))
	vbox.add_child(_hint)


func _add_row(label_text: String) -> void:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override(&"panel", _make_style(COLOR_ROW, Color(0.3, 0.27, 0.22), 10))
	_list.add_child(panel)
	var hbox := HBoxContainer.new()
	hbox.add_theme_constant_override(&"separation", 10)
	panel.add_child(hbox)
	var name_label := Label.new()
	name_label.text = label_text
	name_label.custom_minimum_size = Vector2(170, 0)
	name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	name_label.add_theme_font_size_override(&"font_size", 16)
	hbox.add_child(name_label)
	var left := _arrow("◀")
	hbox.add_child(left)
	var value := Label.new()
	value.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	value.add_theme_font_size_override(&"font_size", 20)
	hbox.add_child(value)
	var right := _arrow("▶")
	hbox.add_child(right)
	_row_panels.append(panel)
	_row_names.append(name_label)
	_row_values.append(value)
	_row_arrows.append([left, right])


func _arrow(text: String) -> Label:
	var arrow := Label.new()
	arrow.text = text
	arrow.add_theme_font_size_override(&"font_size", 18)
	return arrow


func _make_style(bg: Color, border: Color, margin: float) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.set_border_width_all(2)
	style.set_corner_radius_all(8)
	style.set_content_margin_all(margin)
	return style
