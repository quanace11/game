## Viết chữ lên giấy trong hàm _draw của một CanvasItem.
##
## Tự xuống dòng theo bề rộng, mỗi chữ (từ) lệch nhẹ, nghiêng nhẹ, đậm nhạt khác nhau
## như người viết tay thật; dòng chữ có thể dốc dần. Chữ in thì để [member jitter] = 0.
## Hạt ngẫu nhiên lấy từ nội dung nên mỗi lần mở cùng một trang vẫn y nguyên nét chữ.
##
##   var w := InkWriter.new(PaperFonts.get_font(PaperFonts.BALLPOINT), 26, ink)
##   w.jitter = 1.0
##   var y := w.write(self, text, Vector2(60, 90), 420)
class_name InkWriter
extends RefCounted

var font: Font
var size := 24
var color := Color.BLACK
## Khoảng cách giữa hai đường chân chữ (px). Giấy kẻ dòng thì đặt bằng khoảng kẻ.
var line_height := 32.0
## Khoảng cách thêm cho dòng trống giữa hai đoạn (tính theo số dòng).
var paragraph_gap := 1.0
## 0 = chữ in thẳng hàng; 1 = viết tay (lệch dọc ~1.5px, xoay ~1.5 độ mỗi từ).
var jitter := 0.0
## Độ đậm nhạt ngẫu nhiên của từng từ (0..1).
var pressure := 0.0
## Dòng chữ dốc dần (radian), người viết tay hay viết lệch dòng.
var slope := 0.0
## Thụt đầu dòng ngẫu nhiên tối đa (px).
var wander := 0.0
var align := HORIZONTAL_ALIGNMENT_LEFT
## Biến đổi gốc (ví dụ lật gương cho chữ in ngược trong vành nón).
var base := Transform2D.IDENTITY
var seed_value := 0

var _rng := RandomNumberGenerator.new()


func _init(p_font: Font = null, p_size: int = 24, p_color: Color = Color.BLACK) -> void:
	font = p_font if p_font else ThemeDB.fallback_font
	size = p_size
	color = p_color
	line_height = p_size * 1.35


## Chia [param text] thành các dòng vừa [param width]. Dòng trống giữ lại là "".
func wrap_lines(text: String, width: float) -> PackedStringArray:
	var lines := PackedStringArray()
	var space := font.get_string_size(" ", HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	for para in text.split("\n"):
		if para.strip_edges().is_empty():
			lines.append("")
			continue
		var lead := para.length() - para.lstrip(" ").length()
		var current := " ".repeat(lead)
		var current_w := space * lead
		for word in para.strip_edges().split(" ", false):
			var ww := font.get_string_size(word, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			if current.strip_edges().is_empty():
				current += word
				current_w += ww
			elif current_w + space + ww <= width:
				current += " " + word
				current_w += space + ww
			else:
				lines.append(current)
				current = word
				current_w = ww
		lines.append(current)
	return lines


## Chiều cao (px) khi viết [param text] trong bề rộng [param width].
func measure(text: String, width: float) -> float:
	var h := 0.0
	for line in wrap_lines(text, width):
		h += line_height * (paragraph_gap if line.is_empty() else 1.0)
	return h


func line_width(line: String) -> float:
	return font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x


## Viết [param text] từ góc trên trái [param pos] (đường chân chữ đầu tiên ở pos.y + size).
## Trả về y của đường chân chữ kế tiếp (để viết tiếp đoạn sau).
func write(ci: CanvasItem, text: String, pos: Vector2, width: float) -> float:
	_rng.seed = hash(text) ^ seed_value
	var space := font.get_string_size(" ", HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var y := pos.y + size
	for line in wrap_lines(text, width):
		if line.is_empty():
			y += line_height * paragraph_gap
			continue
		var lead := line.length() - line.lstrip(" ").length()
		var words := line.strip_edges().split(" ", false)
		var lw := line_width(line.strip_edges())
		var x := pos.x + space * lead + _rng.randf_range(0.0, wander)
		if align == HORIZONTAL_ALIGNMENT_CENTER:
			x = pos.x + (width - lw) * 0.5
		elif align == HORIZONTAL_ALIGNMENT_RIGHT:
			x = pos.x + width - lw
		var line_tilt := slope + _rng.randf_range(-0.004, 0.004) * jitter
		var x0 := x
		for word in words:
			var ww := font.get_string_size(word, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			var dy := (x - x0) * tan(line_tilt) + _rng.randf_range(-1.5, 1.5) * jitter
			var rot := _rng.randf_range(-0.026, 0.026) * jitter + line_tilt
			var c := color
			c.a *= 1.0 - _rng.randf() * pressure * 0.45
			var xf := base * Transform2D(rot, Vector2(x, y + dy))
			ci.draw_set_transform_matrix(xf)
			ci.draw_string(font, Vector2.ZERO, word, HORIZONTAL_ALIGNMENT_LEFT, -1, size, c)
			x += ww + space * (1.0 + _rng.randf_range(-0.15, 0.25) * jitter)
		y += line_height
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	return y - size


## Viết một dòng duy nhất không xuống dòng, căn theo [member align] quanh [param pos]
## (pos là điểm chân chữ: trái / giữa / phải tùy align).
func write_line(ci: CanvasItem, text: String, pos: Vector2) -> void:
	var lw := line_width(text)
	var start := pos
	if align == HORIZONTAL_ALIGNMENT_CENTER:
		start.x -= lw * 0.5
	elif align == HORIZONTAL_ALIGNMENT_RIGHT:
		start.x -= lw
	var saved := align
	align = HORIZONTAL_ALIGNMENT_LEFT
	write(ci, text, start - Vector2(0, size), 100000.0)
	align = saved
