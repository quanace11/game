## Hình vẽ tay dùng chung cho giấy tờ và câu đố: biển bến (chuông, quang gánh, đầu tàu, con đò),
## hoa văn quai guốc (cá, hoa mai, chữ Thọ), đồ của hành khách (mũ cối, gói thuốc bắc,
## điếu cày), nét bút lông của lá bùa.
##
## Mọi hình vẽ trong ô 100x100 quanh tâm [param c], phóng theo [param s] (1 = 100px).
## Nét vẽ là nét bút (đầu nét thon, dày mỏng không đều) chứ không phải đường kẻ máy.
class_name Pictograms
extends RefCounted

enum Kind { BELL, POLE, TRAIN, BOAT, FISH, PLUM, THO, HELMET, HERBS, PIPE }


static func draw(ci: CanvasItem, kind: Kind, c: Vector2, s: float, color: Color, width: float = 3.0,
		fill := Color(0, 0, 0, 0)) -> void:
	match kind:
		Kind.BELL: _bell(ci, c, s, color, width, fill)
		Kind.POLE: _pole(ci, c, s, color, width, fill)
		Kind.TRAIN: _train(ci, c, s, color, width, fill)
		Kind.BOAT: _boat(ci, c, s, color, width, fill)
		Kind.FISH: _fish(ci, c, s, color, width, fill)
		Kind.PLUM: _plum(ci, c, s, color, width, fill)
		Kind.THO: _tho(ci, c, s, color, width, fill)
		Kind.HELMET: _helmet(ci, c, s, color, width, fill)
		Kind.HERBS: _herbs(ci, c, s, color, width, fill)
		Kind.PIPE: _pipe(ci, c, s, color, width, fill)


# --- Nét bút ------------------------------------------------------------------------

## Đường cong mượt (Catmull-Rom) qua các điểm điều khiển.
static func smooth(points: PackedVector2Array, steps: int = 8, closed := false) -> PackedVector2Array:
	var out := PackedVector2Array()
	var n := points.size()
	if n < 3:
		return points
	var count := n if closed else n - 1
	for i in count:
		var p0 := points[(i - 1 + n) % n] if (closed or i > 0) else points[i]
		var p1 := points[i]
		var p2 := points[(i + 1) % n]
		var p3 := points[(i + 2) % n] if (closed or i + 2 < n) else p2
		for k in steps:
			var t := float(k) / steps
			var t2 := t * t
			var t3 := t2 * t
			out.append(0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
					+ (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3))
	if not closed:
		out.append(points[n - 1])
	return out


## Nét bút: dải đa giác dọc theo [param pts], dày [param width], thon hai đầu nếu [param taper].
## [param wobble] làm mép nét hơi răng cưa như bút lông khô mực.
static func stroke(ci: CanvasItem, pts: PackedVector2Array, width: float, color: Color, taper := true,
		wobble := 0.0, seed_value := 0) -> void:
	var n := pts.size()
	if n < 2:
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value + n * 31
	var left := PackedVector2Array()
	var right := PackedVector2Array()
	for i in n:
		var a := pts[maxi(i - 1, 0)]
		var b := pts[mini(i + 1, n - 1)]
		var dir := (b - a).normalized()
		var normal := Vector2(-dir.y, dir.x)
		var t := float(i) / (n - 1)
		var w := width * 0.5
		if taper:
			w *= clampf(sin(t * PI) * 1.6, 0.25, 1.0)
		w *= 1.0 + rng.randf_range(-wobble, wobble)
		left.append(pts[i] + normal * w)
		right.append(pts[i] - normal * w)
	right.reverse()
	var poly := left + right
	if Geometry2D.triangulate_polygon(poly).is_empty():
		ci.draw_polyline(pts, color, width, true)
		return
	ci.draw_colored_polygon(poly, color)


## Nét bút qua các điểm điều khiển trong ô 100x100 (đã làm mượt).
static func _line(ci: CanvasItem, c: Vector2, s: float, ctrl: Array, color: Color, width: float,
		closed := false) -> void:
	var pts := PackedVector2Array()
	for p: Vector2 in ctrl:
		pts.append(c + p * s)
	var curve := smooth(pts, 6, closed) if pts.size() > 2 else pts
	if closed and curve.size() > 0:
		curve.append(curve[0])
	stroke(ci, curve, width, color, not closed, 0.12, int(ctrl[0].x * 13 + ctrl[0].y * 7))


static func _fill(ci: CanvasItem, c: Vector2, s: float, ctrl: Array, color: Color) -> void:
	if color.a <= 0.0:
		return
	var pts := PackedVector2Array()
	for p: Vector2 in ctrl:
		pts.append(c + p * s)
	var curve := smooth(pts, 6, true)
	if not Geometry2D.triangulate_polygon(curve).is_empty():
		ci.draw_colored_polygon(curve, color)


static func _ellipse(ci: CanvasItem, c: Vector2, radius: Vector2, color: Color, width: float,
		fill := Color(0, 0, 0, 0)) -> void:
	var pts := PackedVector2Array()
	for i in 33:
		var a := TAU * i / 32.0
		pts.append(c + Vector2(cos(a) * radius.x, sin(a) * radius.y))
	if fill.a > 0.0:
		ci.draw_colored_polygon(pts.slice(0, 32), fill)
	stroke(ci, pts, width, color, false, 0.1)


# --- Biển bến -------------------------------------------------------------------------

## Chuông chùa đồng: quai rồng trên đỉnh, thân hơi loe, đai ngang, núm đánh chuông.
static func _bell(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	var body := [Vector2(-22, -26), Vector2(-26, 0), Vector2(-30, 26), Vector2(-34, 34),
			Vector2(34, 34), Vector2(30, 26), Vector2(26, 0), Vector2(22, -26), Vector2(0, -30)]
	_fill(ci, c, s, body, fill)
	_line(ci, c, s, [Vector2(-22, -26), Vector2(-25, 0), Vector2(-29, 24), Vector2(-35, 34)], col, w)
	_line(ci, c, s, [Vector2(22, -26), Vector2(25, 0), Vector2(29, 24), Vector2(35, 34)], col, w)
	_line(ci, c, s, [Vector2(-36, 34), Vector2(0, 37), Vector2(36, 34)], col, w * 1.2)
	_line(ci, c, s, [Vector2(-22, -26), Vector2(0, -31), Vector2(22, -26)], col, w)
	_line(ci, c, s, [Vector2(-26, 2), Vector2(0, 4), Vector2(26, 2)], col, w * 0.7)
	_line(ci, c, s, [Vector2(-29, 22), Vector2(0, 24), Vector2(29, 22)], col, w * 0.7)
	_line(ci, c, s, [Vector2(-10, -30), Vector2(-12, -42), Vector2(0, -46), Vector2(12, -42), Vector2(10, -30)], col, w)
	_ellipse(ci, c + Vector2(0, 13) * s, Vector2(5, 5) * s, col, w * 0.7)
	_line(ci, c, s, [Vector2(0, -14), Vector2(0, -4)], col, w * 0.6)


## Đôi quang gánh: đòn gánh cong, dây quang, hai thúng.
static func _pole(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	_line(ci, c, s, [Vector2(-46, -28), Vector2(0, -36), Vector2(46, -28)], col, w * 1.3)
	for side: float in [-1.0, 1.0]:
		var x: float = 32.0 * side
		_line(ci, c, s, [Vector2(x, -30), Vector2(x - 14, 8)], col, w * 0.6)
		_line(ci, c, s, [Vector2(x, -30), Vector2(x + 14, 8)], col, w * 0.6)
		var basket := [Vector2(x - 18, 8), Vector2(x - 15, 26), Vector2(x, 32), Vector2(x + 15, 26), Vector2(x + 18, 8)]
		_fill(ci, c, s, basket, fill)
		_line(ci, c, s, basket, col, w)
		_line(ci, c, s, [Vector2(x - 18, 8), Vector2(x, 12), Vector2(x + 18, 8)], col, w)
		_line(ci, c, s, [Vector2(x - 16, 18), Vector2(x, 21), Vector2(x + 16, 18)], col, w * 0.5)


## Đầu tàu hơi nước nhìn ngang: nồi hơi, ống khói phun khói, cabin, bánh xe.
static func _train(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	var body := [Vector2(-36, -6), Vector2(14, -6), Vector2(14, -30), Vector2(40, -30), Vector2(40, 18), Vector2(-42, 18)]
	_fill(ci, c, s, body, fill)
	_line(ci, c, s, [Vector2(-38, -6), Vector2(-12, -8), Vector2(14, -6)], col, w)
	_line(ci, c, s, [Vector2(-38, -6), Vector2(-40, 6), Vector2(-38, 18)], col, w)
	_line(ci, c, s, [Vector2(14, -6), Vector2(14, -30), Vector2(42, -30), Vector2(42, 18)], col, w)
	_line(ci, c, s, [Vector2(-46, 18), Vector2(0, 19), Vector2(44, 18)], col, w)
	_line(ci, c, s, [Vector2(20, -24), Vector2(34, -24), Vector2(34, -12), Vector2(20, -12), Vector2(20, -24)], col, w * 0.6)
	_line(ci, c, s, [Vector2(-26, -8), Vector2(-27, -22)], col, w * 1.6)
	_line(ci, c, s, [Vector2(-32, -24), Vector2(-21, -24)], col, w)
	_line(ci, c, s, [Vector2(-50, 28), Vector2(-44, 18)], col, w)
	for puff: Vector3 in [Vector3(-30, -33, 5), Vector3(-36, -42, 7), Vector3(-44, -48, 9)]:
		_ellipse(ci, c + Vector2(puff.x, puff.y) * s, Vector2(puff.z, puff.z * 0.8) * s, col, w * 0.6)
	for x: float in [-30.0, -10.0, 26.0]:
		var r := 10.0 if x > 20.0 else 8.0
		_ellipse(ci, c + Vector2(x, 24) * s, Vector2(r, r) * s, col, w * 0.9, fill)
	_line(ci, c, s, [Vector2(-30, 24), Vector2(26, 24)], col, w * 0.6)


## Con đò: thân cong lưỡi liềm, mui tre ở giữa, sào chống, mặt nước.
static func _boat(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	var hull := [Vector2(-48, 0), Vector2(-24, 14), Vector2(24, 14), Vector2(48, 0), Vector2(0, 6)]
	_fill(ci, c, s, hull, fill)
	_line(ci, c, s, [Vector2(-48, -2), Vector2(-26, 14), Vector2(26, 14), Vector2(48, -2)], col, w)
	_line(ci, c, s, [Vector2(-48, -2), Vector2(0, 5), Vector2(48, -2)], col, w * 0.8)
	_line(ci, c, s, [Vector2(-18, 4), Vector2(-16, -14), Vector2(0, -20), Vector2(16, -14), Vector2(18, 4)], col, w)
	for x: float in [-8.0, 0.0, 8.0]:
		_line(ci, c, s, [Vector2(x, -18), Vector2(x * 1.4, 4)], col, w * 0.4)
	_line(ci, c, s, [Vector2(30, -36), Vector2(36, 26)], col, w * 0.8)
	_line(ci, c, s, [Vector2(-44, 24), Vector2(-30, 21), Vector2(-16, 24)], col, w * 0.5)
	_line(ci, c, s, [Vector2(4, 26), Vector2(18, 23), Vector2(32, 26)], col, w * 0.5)


# --- Hoa văn quai guốc --------------------------------------------------------------

static func _fish(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	var body := [Vector2(-34, 0), Vector2(-10, -18), Vector2(18, -10), Vector2(30, 0), Vector2(18, 10), Vector2(-10, 18)]
	_fill(ci, c, s, body, fill)
	_line(ci, c, s, [Vector2(-34, 0), Vector2(-10, -18), Vector2(16, -10), Vector2(30, 2)], col, w)
	_line(ci, c, s, [Vector2(-34, 0), Vector2(-10, 18), Vector2(16, 10), Vector2(30, -2)], col, w)
	_line(ci, c, s, [Vector2(30, 0), Vector2(44, -14), Vector2(40, 0), Vector2(44, 14), Vector2(30, 0)], col, w)
	_ellipse(ci, c + Vector2(-22, -3) * s, Vector2(2.5, 2.5) * s, col, w * 0.8, col)
	_line(ci, c, s, [Vector2(-14, -10), Vector2(-10, 0), Vector2(-14, 10)], col, w * 0.6)


static func _plum(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	for i in 5:
		var a := -PI * 0.5 + TAU * i / 5.0
		var pc := c + Vector2(cos(a), sin(a)) * 17.0 * s
		_ellipse(ci, pc, Vector2(13, 13) * s, col, w, fill)
	_ellipse(ci, c, Vector2(7, 7) * s, col, w * 0.8)
	for i in 5:
		var a := -PI * 0.3 + TAU * i / 5.0
		ci.draw_circle(c + Vector2(cos(a), sin(a)) * 6.0 * s, 1.8 * s, col)


## Chữ Thọ tròn (hoa văn cách điệu trên đồ mã): vòng tròn, các vạch ngang đối xứng, móc hai bên.
static func _tho(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	_ellipse(ci, c, Vector2(36, 36) * s, col, w, fill)
	_line(ci, c, s, [Vector2(0, -30), Vector2(0, 30)], col, w)
	for row: Vector2 in [Vector2(-20, -18), Vector2(-26, -4), Vector2(-20, 10), Vector2(-12, 22)]:
		_line(ci, c, s, [Vector2(row.x, row.y), Vector2(-row.x, row.y)], col, w * 0.9)
	for side: float in [-1.0, 1.0]:
		_line(ci, c, s, [Vector2(14 * side, -11), Vector2(22 * side, -11), Vector2(22 * side, 3)], col, w * 0.7)
		_line(ci, c, s, [Vector2(8 * side, 16), Vector2(8 * side, 28)], col, w * 0.7)


# --- Đồ của hành khách --------------------------------------------------------------

static func _helmet(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	var dome := [Vector2(-34, 10), Vector2(-30, -14), Vector2(0, -32), Vector2(30, -14), Vector2(34, 10)]
	_fill(ci, c, s, dome + [Vector2(0, 14)], fill)
	_line(ci, c, s, dome, col, w)
	_line(ci, c, s, [Vector2(-48, 18), Vector2(-30, 10), Vector2(0, 8), Vector2(30, 10), Vector2(48, 18)], col, w)
	_line(ci, c, s, [Vector2(-48, 18), Vector2(0, 24), Vector2(48, 18)], col, w)
	_line(ci, c, s, [Vector2(-33, 2), Vector2(0, -2), Vector2(33, 2)], col, w * 0.8)
	_ellipse(ci, c + Vector2(0, -33) * s, Vector2(5, 3) * s, col, w * 0.8)
	_line(ci, c, s, [Vector2(-14, -26), Vector2(-20, -4)], col, w * 0.4)
	_line(ci, c, s, [Vector2(14, -26), Vector2(20, -4)], col, w * 0.4)


static func _herbs(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	var box := [Vector2(-34, -22), Vector2(34, -24), Vector2(36, 22), Vector2(-36, 24)]
	_fill(ci, c, s, box, fill)
	_line(ci, c, s, box + [Vector2(-34, -22)], col, w)
	_line(ci, c, s, [Vector2(-34, -22), Vector2(0, -4), Vector2(34, -24)], col, w * 0.5)
	_line(ci, c, s, [Vector2(-2, -26), Vector2(0, 26)], Color(0.7, 0.1, 0.08, col.a), w * 1.1)
	_line(ci, c, s, [Vector2(-38, 0), Vector2(38, -2)], Color(0.7, 0.1, 0.08, col.a), w * 1.1)
	_line(ci, c, s, [Vector2(0, -2), Vector2(-10, -14), Vector2(-14, -6), Vector2(0, -2), Vector2(12, -14), Vector2(15, -5), Vector2(0, -2)],
			Color(0.7, 0.1, 0.08, col.a), w * 0.8)


static func _pipe(ci: CanvasItem, c: Vector2, s: float, col: Color, w: float, fill: Color) -> void:
	var tube := [Vector2(-8, -46), Vector2(8, -46), Vector2(9, 44), Vector2(-9, 44)]
	_fill(ci, c, s, tube, fill)
	_line(ci, c, s, [Vector2(-8, -46), Vector2(-9, 44)], col, w)
	_line(ci, c, s, [Vector2(8, -46), Vector2(9, 44)], col, w)
	_ellipse(ci, c + Vector2(0, -46) * s, Vector2(8, 3) * s, col, w * 0.8)
	_line(ci, c, s, [Vector2(-9, 44), Vector2(0, 46), Vector2(9, 44)], col, w)
	for y: float in [-18.0, 14.0]:
		_line(ci, c, s, [Vector2(-9, y), Vector2(0, y + 2), Vector2(9, y)], col, w * 0.7)
	_line(ci, c, s, [Vector2(8, 22), Vector2(24, 10), Vector2(28, 4)], col, w)
	_line(ci, c, s, [Vector2(8, 28), Vector2(26, 14), Vector2(32, 8)], col, w)
	_ellipse(ci, c + Vector2(30, 5) * s, Vector2(5, 3) * s, col, w * 0.8, col)


# --- Bùa -------------------------------------------------------------------------------

## Một đạo bùa vẽ bằng bút lông son: ba móc "tam thanh" trên đầu, nét sổ dọc uốn lượn
## kèm các vạch ngang, khung chữ và vòng xoắn ở chân. Sinh ngẫu nhiên theo [param seed_value]
## nhưng cố định cho cùng một hạt. Vẽ trong khung [param rect].
static func talisman_glyph(ci: CanvasItem, rect: Rect2, color: Color, seed_value: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var cx := rect.get_center().x
	var w := rect.size.x
	var top := rect.position.y
	var h := rect.size.y
	var bw := w * 0.075
	# Ba móc đầu bùa.
	for i in 3:
		var x := cx + (i - 1) * w * 0.22
		var pts := PackedVector2Array([Vector2(x - w * 0.05, top + h * 0.02), Vector2(x + w * 0.04, top + h * 0.035),
				Vector2(x, top + h * 0.07), Vector2(x - w * 0.03, top + h * 0.09)])
		stroke(ci, smooth(pts, 6), bw, color, true, 0.2, seed_value + i)
	# Nét ngang chụp.
	stroke(ci, smooth(PackedVector2Array([Vector2(rect.position.x + w * 0.1, top + h * 0.12),
			Vector2(cx, top + h * 0.105), Vector2(rect.end.x - w * 0.1, top + h * 0.125)]), 6), bw * 1.1, color, true, 0.25, seed_value + 5)
	# Thân bùa: nét sổ uốn lượn từ trên xuống, xen vạch ngang và khung chữ.
	var y := top + h * 0.16
	var spine := PackedVector2Array()
	while y < top + h * 0.82:
		spine.append(Vector2(cx + rng.randf_range(-w * 0.08, w * 0.08), y))
		var choice := rng.randi() % 4
		if choice == 0:
			var hw := w * rng.randf_range(0.18, 0.34)
			stroke(ci, PackedVector2Array([Vector2(cx - hw, y + 4), Vector2(cx, y + rng.randf_range(-3, 3)),
					Vector2(cx + hw, y + 2)]), bw * 0.8, color, true, 0.25, int(y))
		elif choice == 1:
			var bx := w * rng.randf_range(0.12, 0.2)
			var bh := h * 0.045
			var box := PackedVector2Array([Vector2(cx - bx, y), Vector2(cx + bx, y - 2), Vector2(cx + bx + 2, y + bh),
					Vector2(cx - bx, y + bh + 2), Vector2(cx - bx, y)])
			stroke(ci, box, bw * 0.55, color, false, 0.3, int(y) + 3)
			stroke(ci, PackedVector2Array([Vector2(cx - bx * 0.6, y + bh * 0.5), Vector2(cx + bx * 0.6, y + bh * 0.45)]),
					bw * 0.45, color, true, 0.3, int(y) + 4)
		elif choice == 2:
			var r := w * 0.09
			var loop := PackedVector2Array()
			for k in 14:
				var a := TAU * k / 12.0
				loop.append(Vector2(cx + cos(a) * r * (1.0 + k * 0.03), y + h * 0.02 + sin(a) * r * 0.7))
			stroke(ci, loop, bw * 0.55, color, true, 0.3, int(y) + 5)
		else:
			for side: float in [-1.0, 1.0]:
				stroke(ci, PackedVector2Array([Vector2(cx + side * w * 0.04, y), Vector2(cx + side * w * 0.2, y + h * 0.04)]),
						bw * 0.6, color, true, 0.3, int(y) + 7)
		y += h * rng.randf_range(0.05, 0.075)
	spine.append(Vector2(cx, top + h * 0.86))
	stroke(ci, smooth(spine, 5), bw * 0.9, color, true, 0.2, seed_value + 9)
	# Chân bùa: vòng xoắn ốc kéo dài.
	var tail := PackedVector2Array()
	for k in 30:
		var a := k * 0.5
		var r := w * 0.03 + k * w * 0.006
		tail.append(Vector2(cx + cos(a) * r, top + h * 0.9 + sin(a) * r * 0.6))
	stroke(ci, tail, bw * 0.6, color, true, 0.3, seed_value + 11)
