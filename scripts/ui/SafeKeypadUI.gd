## Bàn phím nhập mật mã két sắt (CanvasLayer).
##
## Mở khi nhận [signal EventBus.keypad_requested]; hiện con trỏ chuột
## (MOUSE_MODE_VISIBLE) và khóa điều khiển của An. Đóng thì khóa chuột lại.
## - Nút đang chọn được tô trắng nổi bật. Di chuyển bằng phím mũi tên / WASD
##   hoặc lia chuột lên nút.
## - E (hoặc Enter / click chuột): bấm nút đang chọn. 0-9 nhập số, C xóa, OK xác nhận.
## - Màn hình LCD hiện các số đã gõ, ví dụ "2 5 _ _".
## - Sai: LCD nháy đỏ "SAI", tiếng lỗi, tự xóa. Đúng: LCD xanh "MỞ", tiếng chốt
##   sắt, đóng giao diện rồi phát [signal EventBus.safe_unlocked].
## - Esc: thoát.
class_name SafeKeypadUI
extends CanvasLayer

const COLUMNS := 3
const CLEAR := "C"
const CONFIRM := "OK"
const LCD_IDLE := Color(0.16, 0.24, 0.16)
const LCD_WRONG := Color(0.55, 0.06, 0.05)
const LCD_RIGHT := Color(0.1, 0.5, 0.2)
const LCD_TEXT := Color(0.72, 0.95, 0.62)

@export var show_cursor: bool = true
@export var wrong_hold: float = 0.9
@export var right_hold: float = 0.8
@export var beep_sfx: StringName = &"sfx_keypad_beep"
@export var wrong_sfx: StringName = &"sfx_keypad_error"
@export var open_sfx: StringName = &"sfx_safe_bolt"

@onready var _grid: GridContainer = %Keys
@onready var _lcd: PanelContainer = %LCD
@onready var _lcd_label: Label = %LCDText
@onready var _title: Label = %Title
@onready var _hint: Label = %Hint

var _buttons: Array[Button] = []
var _values: Array[String] = []
var _index := 0
var _entered := ""
var _code := ""
var _safe_id: StringName
var _busy := false
var _tween: Tween
var _lcd_style: StyleBoxFlat
var _style_normal: StyleBoxFlat
var _style_selected: StyleBoxFlat


func _ready() -> void:
	visible = false
	_lcd_style = (_lcd.get_theme_stylebox(&"panel") as StyleBoxFlat).duplicate()
	_lcd.add_theme_stylebox_override(&"panel", _lcd_style)
	_style_normal = _make_style(Color(0.16, 0.17, 0.18), Color(0.32, 0.33, 0.34))
	_style_selected = _make_style(Color(0.96, 0.96, 0.94), Color.WHITE)
	for child in _grid.get_children():
		var button := child as Button
		if button == null:
			continue
		var value := String(button.name).trim_prefix("Key")
		_values.append(value)
		_buttons.append(button)
		button.focus_mode = Control.FOCUS_NONE
		if value == CLEAR:
			button.text = tr(&"UI_KEYPAD_CLEAR")
		elif value == CONFIRM:
			button.text = tr(&"UI_KEYPAD_OK")
		else:
			button.text = value
		var i := _buttons.size() - 1
		button.mouse_entered.connect(_select.bind(i))
		button.pressed.connect(_press.bind(i))
	EventBus.keypad_requested.connect(open)


func _exit_tree() -> void:
	if EventBus.keypad_requested.is_connected(open):
		EventBus.keypad_requested.disconnect(open)
	if _tween:
		_tween.kill()
	if visible:
		UIModal.close()


func is_open() -> bool:
	return visible


func get_entered() -> String:
	return _entered


func open(safe_id: StringName, code: String) -> void:
	if visible or code.is_empty():
		return
	_safe_id = safe_id
	_code = code
	_entered = ""
	_busy = false
	_title.text = tr(&"UI_KEYPAD_TITLE")
	_hint.text = tr(&"UI_KEYPAD_HINT")
	_set_lcd(_format_entry(), LCD_IDLE)
	_select(0)
	visible = true
	UIModal.open(show_cursor)


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
	if event.is_action_pressed(&"ui_cancel"):
		close()
	elif _busy:
		# Đang nháy SAI / MỞ: nuốt phím nhưng không xử lý.
		if not (event is InputEventKey or event is InputEventMouseButton):
			return
	elif event.is_action_pressed(&"interact") or event.is_action_pressed(&"ui_accept"):
		_press(_index)
	elif event.is_action_pressed(&"move_left") or event.is_action_pressed(&"ui_left"):
		_move(-1, 0)
	elif event.is_action_pressed(&"move_right") or event.is_action_pressed(&"ui_right"):
		_move(1, 0)
	elif event.is_action_pressed(&"move_forward") or event.is_action_pressed(&"ui_up"):
		_move(0, -1)
	elif event.is_action_pressed(&"move_back") or event.is_action_pressed(&"ui_down"):
		_move(0, 1)
	else:
		return
	get_viewport().set_input_as_handled()


## Bấm nút thứ [param i] (gọi từ phím E hoặc click chuột).
func _press(i: int) -> void:
	if _busy or i < 0 or i >= _values.size():
		return
	_select(i)
	var value := _values[i]
	EventBus.ui_sfx_requested.emit(beep_sfx)
	if value == CLEAR:
		_entered = ""
	elif value == CONFIRM:
		_submit()
		return
	elif _entered.length() < _code.length():
		_entered += value
	_set_lcd(_format_entry(), LCD_IDLE)


func _submit() -> void:
	_busy = true
	if _tween:
		_tween.kill()
	_tween = create_tween()
	if _entered == _code:
		EventBus.ui_sfx_requested.emit(open_sfx)
		_set_lcd(tr(&"UI_SAFE_OPEN"), LCD_RIGHT)
		_tween.tween_interval(right_hold)
		_tween.tween_callback(_finish_open)
		return
	# Sai: nháy đỏ ba nhịp rồi tự xóa.
	EventBus.ui_sfx_requested.emit(wrong_sfx)
	_set_lcd(tr(&"UI_SAFE_WRONG"), LCD_WRONG)
	for i in 3:
		_tween.tween_callback(_lcd.set_modulate.bind(Color(1, 1, 1, 0.35)))
		_tween.tween_interval(wrong_hold / 6.0)
		_tween.tween_callback(_lcd.set_modulate.bind(Color.WHITE))
		_tween.tween_interval(wrong_hold / 6.0)
	_tween.tween_callback(_reset_entry)


func _reset_entry() -> void:
	_entered = ""
	_busy = false
	_set_lcd(_format_entry(), LCD_IDLE)


func _finish_open() -> void:
	var safe_id := _safe_id
	close()
	EventBus.safe_unlocked.emit(safe_id)


func _move(dx: int, dy: int) -> void:
	var count := _buttons.size()
	var rows := ceili(float(count) / COLUMNS)
	var col := wrapi(_index % COLUMNS + dx, 0, COLUMNS)
	var row := wrapi(floori(float(_index) / COLUMNS) + dy, 0, rows)
	_select(mini(row * COLUMNS + col, count - 1))


func _select(i: int) -> void:
	if i < 0 or i >= _buttons.size():
		return
	_index = i
	for j in _buttons.size():
		var selected := j == i
		var style := _style_selected if selected else _style_normal
		var text_color := Color(0.06, 0.06, 0.06) if selected else Color(0.9, 0.9, 0.88)
		var button := _buttons[j]
		for state: StringName in [&"normal", &"hover", &"pressed", &"focus"]:
			button.add_theme_stylebox_override(state, style)
		for color_name: StringName in [&"font_color", &"font_hover_color", &"font_pressed_color"]:
			button.add_theme_color_override(color_name, text_color)


func _format_entry() -> String:
	var slots: PackedStringArray = []
	for i in _code.length():
		slots.append(_entered[i] if i < _entered.length() else "_")
	return " ".join(slots)


func _set_lcd(text: String, color: Color) -> void:
	_lcd_label.text = text
	_lcd_style.bg_color = color
	_lcd.modulate = Color.WHITE


func _make_style(bg: Color, border: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.set_border_width_all(2)
	style.set_corner_radius_all(6)
	style.set_content_margin_all(8)
	return style
