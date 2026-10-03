## Trình đọc sổ / tài liệu (CanvasLayer).
##
## Mở khi nhận [signal EventBus.document_requested], khóa điều khiển của An.
## A/D hoặc mũi tên Trái/Phải để lật trang; E hoặc Esc để gập sổ.
## Dùng _input (chạy trước _unhandled_input) để phím E/Esc không lọt xuống
## người chơi: E không mở lại sổ, Esc không nhả chuột.
class_name DocumentViewer
extends CanvasLayer

@onready var _title: Label = %Title
@onready var _body: Label = %Body
@onready var _page_label: Label = %PageLabel
@onready var _hint: Label = %Hint

var _pages: Array[String] = []
var _index := 0


func _ready() -> void:
	visible = false
	EventBus.document_requested.connect(open)


func is_open() -> bool:
	return visible


func open(title: String, pages: Array[String]) -> void:
	if pages.is_empty():
		return
	_pages = pages
	_index = 0
	_title.text = title
	_hint.text = tr(&"UI_DOC_HINT")
	_show_page()
	visible = true
	EventBus.player_controls_locked.emit(true)


func close() -> void:
	if not visible:
		return
	visible = false
	EventBus.player_controls_locked.emit(false)
	EventBus.document_closed.emit()


func flip(step: int) -> void:
	var next := clampi(_index + step, 0, _pages.size() - 1)
	if next != _index:
		_index = next
		_show_page()


func _input(event: InputEvent) -> void:
	if not visible:
		return
	if event.is_action_pressed(&"interact") or event.is_action_pressed(&"ui_cancel"):
		close()
	elif event.is_action_pressed(&"move_left") or event.is_action_pressed(&"ui_left"):
		flip(-1)
	elif event.is_action_pressed(&"move_right") or event.is_action_pressed(&"ui_right"):
		flip(1)
	else:
		return
	get_viewport().set_input_as_handled()


func _show_page() -> void:
	_body.text = _pages[_index]
	_page_label.text = tr(&"UI_DOC_PAGE").format({"current": _index + 1, "total": _pages.size()})
