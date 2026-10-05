## Tiện ích vẽ đồ vật cho các câu đố cận cảnh: kim loại có texture, đồng thau đổ bóng,
## góc bo, ốc vít, vân gỗ.
class_name PuzzleArt
extends RefCounted

const TIN_TEX := preload("res://assets/ui/tin_metal.png")
const WOOD_TEX := preload("res://assets/ui/wood_grain.png")
const FIBER_TEX := preload("res://assets/ui/paper_fibers.png")

const BRASS_LIGHT := Color(0.86, 0.68, 0.36)
const BRASS := Color(0.62, 0.45, 0.20)
const BRASS_DARK := Color(0.30, 0.20, 0.08)


static func rounded_rect(rect: Rect2, radius: float, segments := 6) -> PackedVector2Array:
	var pts := PackedVector2Array()
	var r := minf(radius, minf(rect.size.x, rect.size.y) * 0.5)
	var corners := [
		[rect.position + Vector2(rect.size.x - r, r), -PI * 0.5],
		[rect.end - Vector2(r, r), 0.0],
		[rect.position + Vector2(r, rect.size.y - r), PI * 0.5],
		[rect.position + Vector2(r, r), PI],
	]
	for c in corners:
		for i in segments + 1:
			var a: float = c[1] + PI * 0.5 * i / segments
			pts.append(c[0] + Vector2(cos(a), sin(a)) * r)
	return pts


## Đa giác tô chuyển màu theo trục dọc (từ [param top] xuống [param bottom]).
static func grad_poly(ci: CanvasItem, pts: PackedVector2Array, top: Color, bottom: Color) -> void:
	var y0 := INF
	var y1 := -INF
	for p in pts:
		y0 = minf(y0, p.y)
		y1 = maxf(y1, p.y)
	var cols := PackedColorArray()
	for p in pts:
		cols.append(top.lerp(bottom, (p.y - y0) / maxf(y1 - y0, 1.0)))
	ci.draw_polygon(pts, cols)


## Đa giác dán texture lặp (CanvasItem phải bật texture_repeat), nhân màu [param tint].
static func tex_poly(ci: CanvasItem, pts: PackedVector2Array, tex: Texture2D, tint: Color,
		uv_scale := 1.0 / 512.0, uv_offset := Vector2.ZERO) -> void:
	var uvs := PackedVector2Array()
	for p in pts:
		uvs.append(p * uv_scale + uv_offset)
	ci.draw_colored_polygon(pts, tint, uvs, tex)


## Viền nổi: cạnh trên-trái sáng, cạnh dưới-phải tối.
static func bevel(ci: CanvasItem, pts: PackedVector2Array, light: Color, dark: Color, width := 2.0) -> void:
	var n := pts.size()
	for i in n:
		var a := pts[i]
		var b := pts[(i + 1) % n]
		var normal := Vector2(b.y - a.y, a.x - b.x).normalized()
		var lit := normal.dot(Vector2(-0.6, -0.8))
		var col := light if lit > 0.0 else dark
		col.a *= absf(lit)
		ci.draw_line(a, b, col, width, true)


static func screw(ci: CanvasItem, p: Vector2, r: float, angle: float) -> void:
	ci.draw_circle(p + Vector2(1, 1.5), r, Color(0, 0, 0, 0.45))
	ci.draw_circle(p, r, BRASS_DARK)
	ci.draw_circle(p - Vector2(r * 0.15, r * 0.15), r * 0.82, BRASS)
	var d := Vector2(cos(angle), sin(angle)) * r * 0.75
	ci.draw_line(p - d, p + d, BRASS_DARK, maxf(1.0, r * 0.28))


## Bóng mềm dạng elip dưới đồ vật.
static func soft_shadow(ci: CanvasItem, center: Vector2, radius: Vector2, alpha := 0.5) -> void:
	for i in 10:
		var k := 1.0 - i * 0.08
		var pts := PackedVector2Array()
		for j in 32:
			var a := TAU * j / 32.0
			pts.append(center + Vector2(cos(a) * radius.x, sin(a) * radius.y) * k)
		ci.draw_colored_polygon(pts, Color(0, 0, 0, alpha * 0.1))


## Chữ đặt giữa tại [param center] (tâm theo chiều cao chữ hoa).
static func text_center(ci: CanvasItem, font: Font, text: String, center: Vector2, font_size: int, color: Color) -> void:
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	ci.draw_string(font, center + Vector2(-w * 0.5, font_size * 0.36), text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
