## Cắt guốc mã rồi hóa: tờ giấy vàng in sẵn ba mẫu guốc (trẻ con / đàn bà / đàn ông, quai cá /
## hoa mai / chữ Thọ) và mảnh giấy điều để đề tên người nhận bằng bút lông.
##
## - Chuột: bấm một mẫu guốc để chọn; bấm hai mũi tên hai bên mảnh giấy điều để đổi tên.
## - Bàn phím: W/S chuyển giữa hàng mẫu guốc và tên; A/D đổi; E cắt rồi hóa.
## Xác nhận là đốt luôn (đúng hay sai đều cháy thành tro, như giấy thật).
class_name ClogPatternView
extends PuzzleView

const SHEET_SIZE := Vector2(880, 380)
const SHEET_CENTER := Vector2(640, 270)
const SLIP_SIZE := Vector2(470, 110)
const SLIP_CENTER := Vector2(640, 548)
const MOTIFS: Array[int] = [Pictograms.Kind.FISH, Pictograms.Kind.PLUM, Pictograms.Kind.THO]
const SCALES: Array[float] = [0.78, 1.0, 1.22]

var _sheet: PaperSheet
var _slip: PaperSheet
var _row := 0
var _cut := false
var _hover := -1
var _time := 0.0
var _marks: Control


func _setup() -> void:
	var look := {"paper_color": Color(0.90, 0.74, 0.34), "age_color": Color(0.6, 0.42, 0.2), "age": 0.35,
			"grain": 0.9, "foxing": 0.15, "tear": 1.5, "ink_grain": 0.1, "stain_shift": Vector2(0.33, 0.21),
			"light_pos": Vector2(0.4, 0.2)}
	_sheet = PaperSheet.new(SHEET_SIZE, look, _draw_sheet)
	_sheet.place(SHEET_CENTER, -1.0)
	add_child(_sheet)
	var slip_look := {"paper_color": Color(0.70, 0.10, 0.08), "age_color": Color(0.4, 0.2, 0.1), "age": 0.3,
			"grain": 0.9, "foxing": 0.0, "tear": 2.5, "tear_freq": 1.8, "ink_grain": 0.25,
			"stain_shift": Vector2(0.71, 0.4), "light_pos": Vector2(0.5, 0.2)}
	_slip = PaperSheet.new(SLIP_SIZE, slip_look, _draw_slip)
	_slip.place(SLIP_CENTER, 1.5)
	add_child(_slip)
	_marks = Control.new()
	_marks.size = size
	_marks.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_marks)
	_marks.draw.connect(_draw_marks)


func hint_text() -> String:
	return tr(&"UI_BURN_HINT")


func _process(delta: float) -> void:
	_time += delta
	_marks.queue_redraw()


func _template_center(i: int) -> Vector2:
	return Vector2(SHEET_SIZE.x * (0.2 + i * 0.3), SHEET_SIZE.y * 0.44)


func _draw_sheet(ci: CanvasItem) -> void:
	# Ô kim nhũ in mờ trên giấy vàng.
	for gx in 14:
		for gy in 6:
			ci.draw_rect(Rect2(14 + gx * 62, 12 + gy * 62, 40, 40), Color(0.72, 0.5, 0.12, 0.18), false, 1.2)
	var label := InkWriter.new(PaperFonts.get_font(PaperFonts.PENCIL), 30, DocumentStyles.INK_PENCIL)
	label.jitter = 1.0
	label.align = HORIZONTAL_ALIGNMENT_CENTER
	var opts := options(0)
	for i in mini(opts.size(), 3):
		var c := _template_center(i)
		var s := SCALES[i]
		if _cut and i == selection[0]:
			# Đôi guốc đã cắt rời bằng giấy điều, nằm nhấc lên khỏi tờ mẫu.
			for k in 2:
				var cc := c + Vector2(-27 + 54 * k, -4 + 8 * k) * s
				var pts := DocumentStyles.clog_points(cc + Vector2(8, 10), s, -1.0 if k == 0 else 1.0)
				ci.draw_colored_polygon(pts, Color(0, 0, 0, 0.35))
			DocumentStyles.clog_outline(ci, c, s, Color(0.95, 0.8, 0.4), MOTIFS[i], 2.0, Color(0.72, 0.1, 0.08))
		else:
			DocumentStyles.clog_outline(ci, c, s, Color(0.25, 0.22, 0.2, 0.85), MOTIFS[i], 1.6)
		label.write_line(ci, String(opts[i]), Vector2(c.x, SHEET_SIZE.y - 30))


func _draw_slip(ci: CanvasItem) -> void:
	var opts := options(1)
	if opts.is_empty():
		return
	var name := String(opts[clampi(selection[1], 0, opts.size() - 1)])
	var brush := InkWriter.new(PaperFonts.get_font(PaperFonts.PEN, 700), 40, Color(0.06, 0.04, 0.03, 0.92))
	brush.jitter = 0.8
	brush.align = HORIZONTAL_ALIGNMENT_CENTER
	brush.write_line(ci, name, Vector2(SLIP_SIZE.x * 0.5, SLIP_SIZE.y * 0.5 + 14))


## Viền chọn mẫu, mũi tên đổi tên, kéo cắt giấy (vẽ đè, không thấm vào giấy).
func _draw_marks() -> void:
	var ci := _marks
	if _cut:
		return
	var pulse := 0.55 + 0.25 * sin(_time * 4.0)
	for i in mini(options(0).size(), 3):
		var c := _sheet.paper_to_parent(_template_center(i))
		var r := Vector2(78, 92) * SCALES[i]
		if i == selection[0]:
			_dashed_ellipse(ci, c, r, Color(0.98, 0.95, 0.85, pulse if _row == 0 else 0.5))
			_scissors(ci, c + Vector2(r.x + 30, -r.y * 0.75))
		elif i == _hover:
			_dashed_ellipse(ci, c, r, Color(1, 0.95, 0.8, 0.3))
	var slip_c := _slip.get_paper_center()
	var col := Color(1.0, 0.86, 0.55, pulse if _row == 1 else 0.45)
	for side: float in [-1.0, 1.0]:
		var p := slip_c + Vector2(side * (SLIP_SIZE.x * 0.5 + 34), 0)
		ci.draw_colored_polygon(PackedVector2Array([p + Vector2(side * 14, 0), p + Vector2(-side * 8, -14),
				p + Vector2(-side * 8, 14)]), col)
	if _row == 1:
		ci.draw_rect(Rect2(slip_c - SLIP_SIZE * 0.5, SLIP_SIZE).grow(8), Color(1, 0.85, 0.5, 0.4), false, 1.5)


func _dashed_ellipse(ci: CanvasItem, c: Vector2, r: Vector2, col: Color) -> void:
	for k in 28:
		if k % 2 == 1:
			continue
		var a0 := TAU * k / 28.0 + _time * 0.3
		var a1 := TAU * (k + 1) / 28.0 + _time * 0.3
		ci.draw_line(c + Vector2(cos(a0) * r.x, sin(a0) * r.y), c + Vector2(cos(a1) * r.x, sin(a1) * r.y), col, 2.0, true)


func _scissors(ci: CanvasItem, p: Vector2) -> void:
	# Kéo cắt giấy hé mở, mũi chĩa vào mẫu guốc; cán sơn đỏ đã tróc.
	var open := 0.22 + 0.06 * sin(_time * 5.0)
	var steel := Color(0.78, 0.80, 0.83)
	ci.draw_set_transform(p, -0.5, Vector2.ONE * 1.15)
	for k: float in [-1.0, 1.0]:
		var rot := k * open
		var blade := PackedVector2Array([Vector2(0, -3), Vector2(-62, 0), Vector2(0, 5)])
		var handle_c := Vector2(30, k * 15)
		var tf := Transform2D(rot, Vector2.ZERO)
		ci.draw_colored_polygon(tf * blade, steel if k < 0 else steel.darkened(0.2))
		ci.draw_polyline(tf * PackedVector2Array([Vector2(-62, 0), Vector2(0, -3)]), Color(1, 1, 1, 0.6), 1.2, true)
		ci.draw_line(Vector2.ZERO, tf * (handle_c + Vector2(-12, 0)), Color(0.3, 0.3, 0.32), 5.0, true)
		var ring := PackedVector2Array()
		for i in 25:
			var a := TAU * i / 24.0
			ring.append(tf * (handle_c + Vector2(cos(a) * 15, sin(a) * 9)))
		ci.draw_polyline(ring, Color(0.12, 0.03, 0.02), 7.5, true)
		ci.draw_polyline(ring, Color(0.62, 0.1, 0.08), 5.0, true)
	ci.draw_circle(Vector2.ZERO, 3.5, Color(0.25, 0.24, 0.24))
	ci.draw_circle(Vector2.ZERO, 1.5, Color(0.8, 0.8, 0.8))
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


func handle_input(event: InputEvent) -> bool:
	if _busy:
		return true
	if event is InputEventMouseMotion:
		_hover = _template_at(stage_pos(event))
		return true
	if event is InputEventMouseButton and (event as InputEventMouseButton).pressed \
			and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var p := stage_pos(event)
		var t := _template_at(p)
		if t >= 0:
			_row = 0
			if selection[0] != t:
				selection[0] = t
				tick()
		else:
			var local := _slip.parent_to_paper(p)
			if local.y > -40 and local.y < SLIP_SIZE.y + 40 and local.x > -80 and local.x < SLIP_SIZE.x + 80:
				_row = 1
				_change(1, 1 if local.x > SLIP_SIZE.x * 0.5 else -1)
		_sheet.redraw()
		return true
	if pressed(event, UP) or pressed(event, DOWN):
		_row = 1 - _row
	elif pressed(event, LEFT):
		_change(_row, -1)
	elif pressed(event, RIGHT):
		_change(_row, 1)
	elif pressed(event, CONFIRM):
		submit_requested.emit()
	else:
		return false
	_sheet.redraw()
	_slip.redraw()
	return true


func _change(row: int, step: int) -> void:
	var count := mini(options(row).size(), 3) if row == 0 else options(row).size()
	if count == 0:
		return
	selection[row] = wrapi(selection[row] + step, 0, count)
	tick()
	_slip.redraw()


func _template_at(p: Vector2) -> int:
	var local := _sheet.parent_to_paper(p)
	for i in mini(options(0).size(), 3):
		var d := (local - _template_center(i)) / (Vector2(80, 95) * SCALES[i])
		if d.length() < 1.0:
			return i
	return -1


## Cắt đôi guốc ra khỏi tờ mẫu rồi hóa cả giấy lẫn tên (đúng sai đều cháy).
func _burn() -> float:
	_cut = true
	_sheet.redraw()
	EventBus.ui_sfx_requested.emit(&"sfx_scissors")
	var t := create_tween()
	t.tween_interval(0.6)
	t.tween_callback(func() -> void: EventBus.ui_sfx_requested.emit(&"sfx_paper_burn"))
	var burn := func(v: float) -> void:
		_sheet.set_param(&"burn", v)
		_slip.set_param(&"burn", clampf(v * 1.15, 0.0, 1.0))
	t.tween_method(burn, 0.0, 1.0, 1.4)
	return 2.1


func play_right() -> float:
	return _burn()


func play_wrong(_closing: bool) -> float:
	return _burn()
