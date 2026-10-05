## Trình đọc giấy tờ (CanvasLayer): hiện tài liệu như vật thật cầm trên tay.
##
## Mở khi nhận [signal EventBus.document_requested] (tự chọn kiểu giấy theo nội dung, xem
## [DocumentStyles]) hoặc [signal EventBus.styled_document_requested] (chỉ định kiểu).
## Mỗi trang dựng thành tờ giấy / tấm biển / cuống vé thật; lời dẫn trong ngoặc đơn hiện
## thành chú thích phía dưới. Khóa điều khiển của An.
## A/D hoặc mũi tên Trái/Phải để lật trang; E hoặc Esc để gập lại, phát [signal EventBus.document_closed].
## Dùng _input (chạy trước _unhandled_input) để phím E/Esc không lọt xuống
## người chơi: E không mở lại tài liệu, Esc không nhả chuột.
class_name DocumentViewer
extends CanvasLayer

@export var flip_sfx: StringName = &"sfx_page_flip"
@export var open_sfx: StringName = &"sfx_paper"

var _pages: Array[String] = []
var _styles: Array[StringName] = []
var _title_text := ""
var _index := 0
var _tween: Tween
var _fit_offset := Vector2.ZERO

var _stage: UIStage
var _content: Control
var _title: Label
var _captions: Label
var _hint: Label
var _page_label: Label


func _ready() -> void:
	layer = 10
	visible = false
	_build()
	EventBus.document_requested.connect(open)
	EventBus.styled_document_requested.connect(open_styled)


func _exit_tree() -> void:
	if EventBus.document_requested.is_connected(open):
		EventBus.document_requested.disconnect(open)
	if EventBus.styled_document_requested.is_connected(open_styled):
		EventBus.styled_document_requested.disconnect(open_styled)
	if _tween:
		_tween.kill()


func is_open() -> bool:
	return visible


func get_page_index() -> int:
	return _index


## Kiểu giấy đang dùng cho từng trang (để kiểm thử).
func get_styles() -> Array[StringName]:
	return _styles.duplicate()


func open(title: String, pages: Array[String]) -> void:
	open_styled(title, pages, &"")


func open_styled(title: String, pages: Array[String], style: StringName) -> void:
	if pages.is_empty():
		return
	_pages = pages
	_title_text = title
	_styles.clear()
	for page in pages:
		_styles.append(style if style != &"" else DocumentStyles.style_for(page, title))
	_index = 0
	_title.text = title
	_hint.text = tr(&"UI_PAPER_HINT_PAGES") if pages.size() > 1 else tr(&"UI_PAPER_HINT_SINGLE")
	var was_open := visible
	visible = true
	_show_page(0)
	if not was_open:
		EventBus.ui_sfx_requested.emit(open_sfx)
		EventBus.player_controls_locked.emit(true)


func close() -> void:
	if not visible:
		return
	if _tween:
		_tween.kill()
	visible = false
	_clear()
	EventBus.player_controls_locked.emit(false)
	EventBus.document_closed.emit()


func flip(step: int) -> void:
	var next := clampi(_index + step, 0, _pages.size() - 1)
	if next != _index:
		_index = next
		EventBus.ui_sfx_requested.emit(flip_sfx)
		_show_page(step)


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


func _clear() -> void:
	for child in _content.get_children():
		child.queue_free()


func _show_page(direction: int) -> void:
	_clear()
	var page := DocumentStyles.build(_styles[_index], _pages[_index], _title_text)
	for item: Control in page["items"]:
		_content.add_child(item)
	var captions: PackedStringArray = page["captions"]
	_captions.text = "\n".join(captions)
	_captions.visible = not captions.is_empty()
	_fit_content(page["items"], captions)
	_page_label.text = tr(&"UI_DOC_PAGE").format({"current": _index + 1, "total": _pages.size()}) \
			if _pages.size() > 1 else ""
	# Tờ giấy được đưa lên trước mặt: trượt vào, xoay nhẹ rồi nằm yên.
	if _tween:
		_tween.kill()
	_content.modulate.a = 0.0
	_content.position = _fit_offset + Vector2(60.0 * signf(direction), 26.0 if direction == 0 else 0.0)
	_content.rotation_degrees = 1.2 * (signf(direction) if direction != 0 else 1.0)
	_tween = create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_tween.tween_property(_content, "modulate:a", 1.0, 0.25)
	_tween.tween_property(_content, "position", _fit_offset, 0.35)
	_tween.tween_property(_content, "rotation_degrees", 0.0, 0.45)


## Thu nhỏ và căn giữa vật cho vừa khoảng giữa tên vật (trên) và lời dẫn (dưới).
func _fit_content(items: Array, captions: PackedStringArray) -> void:
	var bounds := Rect2()
	var first := true
	for item: Control in items:
		var inset := PaperSheet.MARGIN * 0.75 if item is PaperSheet else 0.0
		var xf := item.get_transform()
		for corner: Vector2 in [Vector2(inset, inset), Vector2(item.size.x - inset, inset),
				Vector2(item.size.x - inset, item.size.y - inset), Vector2(inset, item.size.y - inset)]:
			var p: Vector2 = xf * corner
			if first:
				bounds = Rect2(p, Vector2.ZERO)
				first = false
			else:
				bounds = bounds.expand(p)
	var lines := 0
	for c in captions:
		lines += 1 + int(c.length() / 95)
	var bottom := 668.0 - 26.0 * lines - 8.0 if lines > 0 else 676.0
	var area := Rect2(24, 52, 1232, bottom - 52)
	var k := 1.0
	if not first:
		k = minf(1.0, minf(area.size.x / bounds.size.x, area.size.y / bounds.size.y))
	_content.scale = Vector2.ONE * k
	# Tâm vùng vật sau khi thu nhỏ quanh pivot (giữa sân khấu) phải trùng tâm vùng trống.
	var pivot := _content.pivot_offset
	var center_after := pivot + (bounds.get_center() - pivot) * k
	_fit_offset = area.get_center() - center_after if not first else Vector2.ZERO


# --- Dựng giao diện -----------------------------------------------------------

func _build() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0.015, 0.012, 0.01, 0.72)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	var vignette := TextureRect.new()
	vignette.texture = _vignette_texture()
	vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	vignette.stretch_mode = TextureRect.STRETCH_SCALE
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vignette)

	_stage = UIStage.new()
	add_child(_stage)
	_content = Control.new()
	_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_content.size = UIStage.DESIGN
	_content.pivot_offset = UIStage.DESIGN * 0.5
	_stage.add_child(_content)

	_title = _label(17, Color(0.86, 0.80, 0.68), HORIZONTAL_ALIGNMENT_CENTER)
	_title.position = Vector2(240, 18)
	_title.size = Vector2(800, 30)
	_title.uppercase = true
	_title.add_theme_constant_override(&"outline_size", 0)
	_stage.add_child(_title)

	_captions = _label(17, Color(0.82, 0.78, 0.70), HORIZONTAL_ALIGNMENT_CENTER)
	_captions.position = Vector2(190, 612)
	_captions.size = Vector2(900, 60)
	_captions.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_captions.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_captions.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_stage.add_child(_captions)

	_hint = _label(13, Color(0.62, 0.58, 0.52), HORIZONTAL_ALIGNMENT_RIGHT)
	_hint.position = Vector2(640, 684)
	_hint.size = Vector2(610, 22)
	_stage.add_child(_hint)
	_page_label = _label(13, Color(0.62, 0.58, 0.52), HORIZONTAL_ALIGNMENT_LEFT)
	_page_label.position = Vector2(30, 684)
	_page_label.size = Vector2(200, 22)
	_stage.add_child(_page_label)


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


static func _vignette_texture() -> GradientTexture2D:
	var gradient := Gradient.new()
	gradient.set_color(0, Color(0, 0, 0, 0.0))
	gradient.set_color(1, Color(0, 0, 0, 0.85))
	gradient.add_point(0.55, Color(0, 0, 0, 0.15))
	var tex := GradientTexture2D.new()
	tex.gradient = gradient
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.05, 1.05)
	tex.width = 256
	tex.height = 256
	return tex
