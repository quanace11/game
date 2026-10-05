## Giao diện đọc cuốn sổ chi tiêu năm 1999 (CanvasLayer).
##
## Mở khi nhận [signal EventBus.book_requested] với [member book_id] khớp (lúc
## nhặt sổ trong hộc bàn, hoặc bấm phím số của ô Hotbar giữ sổ).
## - A/D hoặc mũi tên Trái/Phải: lật trang.
## - E hoặc Esc: gập sổ, cất vào người, phát [signal EventBus.book_closed].
##
## Mỗi trang có một tỷ lệ bị xé trong [member torn_ratios]:
##   0.0 nguyên vẹn, 0.25 rách một góc, 0.5 mất nửa trang,
##   0.75 chỉ còn một mẩu nhỏ, 1.0 xé sạch sát gáy (chỉ còn răng cưa).
## Phần giấy còn lại được vẽ bằng đa giác có mép răng cưa; chữ trên trang bị
## cắt theo đúng hình giấy nhờ [member CanvasItem.clip_children].
class_name ExpenseBookUI
extends CanvasLayer

const PAPER := Color(0.87, 0.82, 0.69)
const PAPER_EDGE := Color(0.97, 0.94, 0.85)
const RULE := Color(0.4, 0.5, 0.68, 0.3)
const MARGIN_LINE := Color(0.72, 0.28, 0.25, 0.45)
const COVER := Color(0.26, 0.11, 0.09)
const COVER_DARK := Color(0.15, 0.06, 0.05)
const STUB_WIDTH := 12.0
const RULE_SPACING := 33.0
const RULE_TOP := 52.0

@export var book_id: StringName = &"expense_book_1999"
@export var title_key: String = "ITEM_EXPENSE_BOOK_NAME"
@export var page_keys: Array[String] = [
	"EXPENSE_PAGE_1", "EXPENSE_PAGE_2", "EXPENSE_PAGE_3", "EXPENSE_PAGE_4",
	"EXPENSE_PAGE_5", "EXPENSE_PAGE_6", "EXPENSE_PAGE_7",
]
## Tỷ lệ bị xé của từng trang, cùng thứ tự với [member page_keys].
@export var torn_ratios: Array[float] = [0.0, 1.0, 0.0, 0.5, 0.75, 0.0, 0.25]
@export var show_cursor: bool = false
@export var flip_sfx: StringName = &"sfx_page_flip"

@onready var _cover: Control = %Cover
@onready var _paper: Control = %Paper
@onready var _lines: Control = %Lines
@onready var _body: Label = %Body
@onready var _title: Label = %Title
@onready var _page_label: Label = %PageLabel
@onready var _hint: Label = %Hint

var _index := 0
var _tween: Tween


func _ready() -> void:
	visible = false
	_cover.draw.connect(_draw_cover)
	_paper.draw.connect(_draw_paper)
	_lines.draw.connect(_draw_lines)
	_apply_handwriting()
	_paper.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	EventBus.book_requested.connect(_on_book_requested)


## Chữ trong sổ là nét bút bi viết tay, mỗi dòng ngồi đúng lên dòng kẻ của trang giấy.
func _apply_handwriting() -> void:
	var font := PaperFonts.get_font(PaperFonts.BALLPOINT)
	var size := 21
	_body.add_theme_font_override("font", font)
	_body.add_theme_font_size_override("font_size", size)
	_body.add_theme_color_override("font_color", Color(0.12, 0.17, 0.42, 0.92))
	_body.add_theme_constant_override("line_spacing", int(round(RULE_SPACING - font.get_height(size))))
	_body.offset_top = RULE_TOP - 4.0 - font.get_ascent(size)


func _exit_tree() -> void:
	if EventBus.book_requested.is_connected(_on_book_requested):
		EventBus.book_requested.disconnect(_on_book_requested)
	if _tween:
		_tween.kill()
	if visible:
		UIModal.close()


func is_open() -> bool:
	return visible


func get_page_index() -> int:
	return _index


func open() -> void:
	if visible or page_keys.is_empty():
		return
	_index = 0
	_title.text = tr(title_key)
	_hint.text = tr(&"UI_BOOK_HINT")
	visible = true
	UIModal.open(show_cursor)
	_show_page(0)
	GameManager.set_flag(&"read_expense_book")


func close() -> void:
	if not visible:
		return
	if _tween:
		_tween.kill()
	visible = false
	UIModal.close()
	EventBus.book_closed.emit(book_id)


func flip(step: int) -> void:
	var next := clampi(_index + step, 0, page_keys.size() - 1)
	if next == _index:
		return
	_index = next
	EventBus.ui_sfx_requested.emit(flip_sfx)
	_show_page(step)


func get_torn_ratio(index: int) -> float:
	return torn_ratios[index] if index >= 0 and index < torn_ratios.size() else 0.0


func _on_book_requested(id: StringName) -> void:
	if id == book_id:
		open()


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


func _show_page(direction: int) -> void:
	_body.text = tr(page_keys[_index])
	_page_label.text = tr(&"UI_DOC_PAGE").format({"current": _index + 1, "total": page_keys.size()})
	_paper.queue_redraw()
	_lines.queue_redraw()
	if _tween:
		_tween.kill()
	_paper.modulate.a = 0.0 if direction != 0 else 1.0
	_paper.position.x = 24.0 * signf(direction)
	_tween = create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	_tween.tween_property(_paper, "modulate:a", 1.0, 0.22)
	_tween.tween_property(_paper, "position:x", 0.0, 0.25)


# --- Hình dạng trang bị xé ------------------------------------------------------

## Đa giác phần giấy còn lại của một trang kích thước [param size], gáy sổ ở
## cạnh trái (x = 0). [param seed_value] giữ mép răng cưa cố định cho từng trang.
## Trả về danh sách đa giác (trang bị xé gần hết còn thêm dải giấy sát gáy).
static func torn_polygons(ratio: float, size: Vector2, seed_value: int) -> Array[PackedVector2Array]:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value * 7919 + 17
	var w := size.x
	var h := size.y
	var result: Array[PackedVector2Array] = []
	if ratio <= 0.01:
		result.append(PackedVector2Array([Vector2.ZERO, Vector2(w, 0), size, Vector2(0, h)]))
		return result

	var poly := PackedVector2Array()
	if ratio < 0.375:
		# Rách một góc: mất tam giác góc trên-ngoài có diện tích = ratio.
		var k := sqrt(2.0 * ratio)
		poly.append(Vector2.ZERO)
		poly.append(Vector2(w * (1.0 - k), 0))
		poly.append_array(_jagged(Vector2(w * (1.0 - k), 0), Vector2(w, h * k), rng, 7.0))
		poly.append(size)
		poly.append(Vector2(0, h))
	elif ratio < 0.625:
		# Mất một dải dọc phía ngoài, giữ lại (1 - ratio) bề ngang, mép hơi xiên.
		var keep := w * (1.0 - ratio)
		poly.append(Vector2.ZERO)
		poly.append(Vector2(keep + 14.0, 0))
		poly.append_array(_jagged(Vector2(keep + 14.0, 0), Vector2(keep - 14.0, h), rng, 8.0))
		poly.append(Vector2(0, h))
	elif ratio < 0.99:
		# Chỉ còn một mẩu tam giác ở góc dưới sát gáy, diện tích = 1 - ratio.
		var k := sqrt(2.0 * (1.0 - ratio))
		poly.append(Vector2(0, h * (1.0 - k)))
		poly.append_array(_jagged(Vector2(0, h * (1.0 - k)), Vector2(w * k, h), rng, 8.0))
		poly.append(Vector2(0, h))
	if not poly.is_empty():
		result.append(poly)

	if ratio >= 0.625:
		# Dải giấy răng cưa còn dính ở gáy.
		var stub := PackedVector2Array([Vector2.ZERO, Vector2(STUB_WIDTH * 0.6, 0)])
		stub.append_array(_jagged(Vector2(STUB_WIDTH * 0.6, 0), Vector2(STUB_WIDTH * 0.6, h), rng, 5.0, 9.0))
		stub.append(Vector2(0, h))
		result.append(stub)
	return result


## Các điểm răng cưa từ [param from] (không gồm) tới [param to] (gồm).
static func _jagged(from: Vector2, to: Vector2, rng: RandomNumberGenerator,
		amplitude: float, step: float = 12.0) -> PackedVector2Array:
	var points := PackedVector2Array()
	var length := from.distance_to(to)
	var count := maxi(int(length / step), 1)
	var normal := (to - from).orthogonal().normalized()
	for i in range(1, count):
		var t := float(i) / count
		var jitter := rng.randf_range(-amplitude, amplitude) * (1.0 if i % 2 == 0 else 0.6)
		points.append(from.lerp(to, t) + normal * jitter)
	points.append(to)
	return points


# --- Vẽ -----------------------------------------------------------------------

func _current_polygons() -> Array[PackedVector2Array]:
	return torn_polygons(get_torn_ratio(_index), _paper.size, _index)


func _draw_cover() -> void:
	var s := _cover.size
	_cover.draw_rect(Rect2(Vector2(-30, -16), s + Vector2(48, 32)), COVER_DARK)
	_cover.draw_rect(Rect2(Vector2(-24, -10), s + Vector2(36, 20)), COVER)
	# Gáy sổ có đường chỉ khâu.
	_cover.draw_rect(Rect2(Vector2(-30, -16), Vector2(26, s.y + 32)), COVER_DARK)
	var y := 6.0
	while y < s.y:
		_cover.draw_line(Vector2(-12, y), Vector2(-12, y + 9), Color(0.7, 0.62, 0.5, 0.6), 2.0)
		y += 22.0
	# Mép các trang phía sau, nhìn thấy khi trang hiện tại bị xé.
	_cover.draw_rect(Rect2(Vector2(4, 6), s - Vector2(10, 10)), Color(PAPER.darkened(0.45), 0.9))


func _draw_paper() -> void:
	for poly in _current_polygons():
		# Giấy có thớ sợi và ngả vàng dần về phía mép dưới.
		_paper.draw_colored_polygon(poly, PAPER)
		PuzzleArt.tex_poly(_paper, poly, PuzzleArt.FIBER_TEX, Color(1.75, 1.64, 1.38, 0.35), 1.0 / 420.0)
		PuzzleArt.grad_poly(_paper, poly, Color(0.55, 0.4, 0.15, 0.0), Color(0.55, 0.4, 0.15, 0.12))
		var edge := poly.duplicate()
		edge.append(poly[0])
		_paper.draw_polyline(edge, PAPER_EDGE, 2.0)


func _draw_lines() -> void:
	var s := _lines.size
	var y := RULE_TOP
	while y < s.y - 12.0:
		_lines.draw_line(Vector2(0, y), Vector2(s.x, y), RULE, 1.0)
		y += RULE_SPACING
	_lines.draw_line(Vector2(56, 0), Vector2(56, s.y), MARGIN_LINE, 1.5)
	# Vết ố vàng của giấy cũ.
	_tide_mark(Vector2(s.x * 0.78, s.y * 0.82), 46.0, 0.08)
	_tide_mark(Vector2(s.x * 0.2, s.y * 0.15), 30.0, 0.06)


## Vệt nước loang đã khô: lòng nhạt, viền đậm hơn, mép không tròn đều.
func _tide_mark(c: Vector2, r: float, alpha: float) -> void:
	var pts := PackedVector2Array()
	for i in 32:
		var a := TAU * i / 32.0
		pts.append(c + Vector2(cos(a), sin(a)) * r * (1.0 + 0.08 * sin(a * 3.0 + r) + 0.05 * sin(a * 7.0)))
	_lines.draw_colored_polygon(pts, Color(0.6, 0.45, 0.2, alpha * 0.5))
	pts.append(pts[0])
	_lines.draw_polyline(pts, Color(0.5, 0.35, 0.15, alpha * 1.6), 2.0, true)
