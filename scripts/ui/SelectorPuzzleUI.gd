## Giao diện câu đố "cầm đồ vật lên tay" (CanvasLayer): hộp tôn khóa số, bảng lộ trình,
## vé bấm lỗ, giấy cắt guốc mã, dây chuông, trả đồ cho hình nhân...
##
## Mở khi nhận [signal EventBus.selector_requested]. Mỗi [code]puzzle_id[/code] có một
## [PuzzleView] vẽ đồ vật thật (xem [method _make_view]); id lạ dùng [PaperFormView] (tờ giấy
## ghi các hàng lựa chọn). View tự xử lý chuột/phím; Esc luôn là thôi, không tính gì.
## - Có đáp án: sai thì view diễn phản hồi vật lý (khóa không nhả, biển lắc, vé bị vò...) rồi
##   giữ nguyên (hoặc đóng luôn nếu [code]close_on_wrong[/code]); đúng thì diễn rồi đóng.
## - Không có đáp án: đóng ngay sau khi view diễn xong và trả lựa chọn về.
## Kết quả trả qua [signal EventBus.selector_submitted] (cùng định dạng như trước).
class_name SelectorPuzzleUI
extends CanvasLayer

const COLOR_WRONG := Color(0.95, 0.55, 0.45)
const COLOR_RIGHT := Color(0.7, 0.9, 0.6)

@export var wrong_sfx: StringName = &"sfx_keypad_error"
@export var right_sfx: StringName = &"sfx_lock_click"

var _puzzle_id: StringName
var _answer: Array = []
var _close_on_wrong := false
var _busy := false
var _tween: Tween
var _status_tween: Tween

var _stage: UIStage
var _view: PuzzleView
var _title: Label
var _status: Label
var _hint: Label


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


## Đồ vật đang mở (để kiểm thử).
func get_view() -> PuzzleView:
	return _view


## [param rows]: mỗi phần tử là Dictionary {"label": String, "options": Array[String]} đã dịch.
## [param answer]: chỉ số lựa chọn đúng của từng hàng; rỗng = không kiểm tra.
func open(puzzle_id: StringName, title: String, rows: Array, answer: Array, close_on_wrong: bool) -> void:
	if visible or rows.is_empty():
		return
	_puzzle_id = puzzle_id
	_answer = answer
	_close_on_wrong = close_on_wrong
	_busy = false
	if _view:
		_view.queue_free()
	_view = _make_view(puzzle_id)
	_stage.add_child(_view)
	_stage.move_child(_view, 0)
	_view.setup(puzzle_id, title, rows, _stage)
	_view.submit_requested.connect(_submit)
	_view.status_requested.connect(_show_status.bind(Color(0.9, 0.86, 0.78)))
	_title.text = title
	_hint.text = _view.hint_text()
	_status.text = ""
	visible = true
	UIModal.open(true)


func close() -> void:
	if not visible:
		return
	if _tween:
		_tween.kill()
	visible = false
	_busy = false
	if _view:
		_view.queue_free()
		_view = null
	UIModal.close()


func get_selection() -> Array[int]:
	return _view.get_selection() if _view else ([] as Array[int])


func _make_view(puzzle_id: StringName) -> PuzzleView:
	var id := String(puzzle_id)
	match id:
		"tin_box":
			return TinBoxView.new()
		"route":
			return RouteBoardView.new()
		"punch":
			return TicketPunchView.new()
		"burn_clogs":
			return ClogPatternView.new()
		"bell":
			return BellRopeView.new()
	if id.begins_with("give_"):
		return GiveItemView.new()
	return PaperFormView.new()


func _input(event: InputEvent) -> void:
	if not visible:
		return
	if _busy:
		if event is InputEventKey or event is InputEventMouseButton:
			get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed(&"ui_cancel"):
		close()
		get_viewport().set_input_as_handled()
		return
	if _view and _view.handle_input(event):
		get_viewport().set_input_as_handled()
	elif event is InputEventKey or event is InputEventMouseButton:
		# Không để phím/chuột lọt xuống người chơi khi đang cầm đồ vật.
		get_viewport().set_input_as_handled()


func _submit() -> void:
	if _busy or _view == null:
		return
	var selection := _view.get_selection()
	_busy = true
	_view.set_busy(true)
	if _tween:
		_tween.kill()
	_tween = create_tween()
	if _answer.is_empty():
		_tween.tween_interval(_view.play_right())
		_tween.tween_callback(_finish.bind(selection, true))
		return
	var correct := true
	for i in _answer.size():
		if i >= selection.size() or selection[i] != int(_answer[i]):
			correct = false
			break
	if correct:
		EventBus.ui_sfx_requested.emit(right_sfx)
		_tween.tween_interval(_view.play_right())
		_tween.tween_callback(_show_status.bind(tr(&"UI_SELECTOR_RIGHT"), COLOR_RIGHT))
		_tween.tween_interval(0.35)
		_tween.tween_callback(_finish.bind(selection, true))
		return
	EventBus.ui_sfx_requested.emit(wrong_sfx)
	var hold := _view.play_wrong(_close_on_wrong)
	_tween.tween_interval(hold * 0.5)
	_tween.tween_callback(_show_status.bind(tr(&"UI_SELECTOR_WRONG"), COLOR_WRONG))
	_tween.tween_interval(hold * 0.5)
	if _close_on_wrong:
		_tween.tween_interval(0.3)
		_tween.tween_callback(_finish.bind(selection, false))
		return
	_tween.tween_callback(func() -> void:
		_busy = false
		if _view:
			_view.set_busy(false))


func _finish(selection: Array[int], correct: bool) -> void:
	var id := _puzzle_id
	close()
	EventBus.selector_submitted.emit(id, selection, correct)


func _show_status(text: String, color: Color) -> void:
	_status.text = text
	_status.add_theme_color_override(&"font_color", color)
	_status.modulate.a = 1.0
	if _status_tween:
		_status_tween.kill()
	_status_tween = create_tween()
	_status_tween.tween_interval(1.8)
	_status_tween.tween_property(_status, "modulate:a", 0.0, 0.8)


# --- Dựng giao diện -----------------------------------------------------------

func _build() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0.012, 0.01, 0.008, 0.82)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	var vignette := TextureRect.new()
	vignette.texture = DocumentViewer._vignette_texture()
	vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	vignette.stretch_mode = TextureRect.STRETCH_SCALE
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vignette)
	_stage = UIStage.new()
	add_child(_stage)

	_title = _label(17, Color(0.86, 0.80, 0.68), HORIZONTAL_ALIGNMENT_CENTER)
	_title.position = Vector2(140, 18)
	_title.size = Vector2(1000, 30)
	_title.uppercase = true
	_stage.add_child(_title)
	_status = _label(20, Color.WHITE, HORIZONTAL_ALIGNMENT_CENTER)
	_status.position = Vector2(240, 640)
	_status.size = Vector2(800, 30)
	_stage.add_child(_status)
	_hint = _label(13, Color(0.62, 0.58, 0.52), HORIZONTAL_ALIGNMENT_CENTER)
	_hint.position = Vector2(40, 684)
	_hint.size = Vector2(1200, 22)
	_stage.add_child(_hint)


func _label(font_size: int, color: Color, align: HorizontalAlignment) -> Label:
	var label := Label.new()
	label.horizontal_alignment = align
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.add_theme_font_size_override(&"font_size", font_size)
	label.add_theme_color_override(&"font_color", color)
	label.add_theme_color_override(&"font_shadow_color", Color(0, 0, 0, 0.85))
	label.add_theme_constant_override(&"shadow_offset_x", 0)
	label.add_theme_constant_override(&"shadow_offset_y", 2)
	return label
