## Hộp tôn của bác tài nhìn cận cảnh: nắp tôn khắc "SỐ XE", ổ khóa đồng ba vòng số.
##
## Mỗi vòng số là một bánh xe lăn thật: số trên/dưới cong đi theo mặt trụ, mép bánh có khía.
## - A/D (Trái/Phải): chọn vòng. W/S (Lên/Xuống) hoặc lăn chuột trên vòng: xoay số.
##   Bấm nửa trên/dưới một vòng, hoặc kéo chuột lên xuống trên vòng, cũng xoay được.
## - E / Enter hoặc bấm vào khoen khóa: thử mở nắp.
## Sai: cả hộp giật cục, khoen khóa không nhả. Đúng: khoen bật lên, nắp hé mở.
class_name TinBoxView
extends PuzzleView

const BOX_CENTER := Vector2(640, 380)
const WHEEL_Y := 486.0
const WHEEL_SPACING := 108.0
const WINDOW := Vector2(78, 124)
const DIGIT_RADIUS := 80.0
const DRAG_STEP := 28.0

var _current := 0
var _shown: Array[float] = []
var _hover := -1
var _drag_wheel := -1
var _drag_acc := 0.0
var _hasp_lift := 0.0
var _lid_open := 0.0
var _time := 0.0
var _box: Control
var _font_digits: Font
var _font_scratch: Font


func _setup() -> void:
	texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	_font_digits = PaperFonts.get_font(PaperFonts.STAMP, 500)
	_font_scratch = PaperFonts.get_font(PaperFonts.PENCIL)
	_box = Control.new()
	_box.size = size
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	add_child(_box)
	_box.draw.connect(_draw_box)
	_shown.clear()
	for i in selection.size():
		_shown.append(float(selection[i]))


func hint_text() -> String:
	return tr(&"UI_TIN_HINT")


func _process(delta: float) -> void:
	_time += delta
	for i in _shown.size():
		var count := maxf(options(i).size(), 1.0)
		var diff := wrapf(selection[i] - _shown[i], -count * 0.5, count * 0.5)
		if absf(diff) > 0.001:
			_shown[i] = wrapf(_shown[i] + diff * minf(1.0, delta * 14.0), 0.0, count)
	# Vẽ lại mỗi khung: bánh số lăn, viền vòng đang chọn nhấp nháy theo ánh đèn.
	_box.queue_redraw()


func handle_input(event: InputEvent) -> bool:
	if _busy:
		return true
	if event is InputEventMouseMotion:
		var p := stage_pos(event)
		_hover = _wheel_at(p)
		if _drag_wheel >= 0:
			_drag_acc += (event as InputEventMouseMotion).relative.y / stage.scale.y
			while absf(_drag_acc) >= DRAG_STEP:
				# Kéo xuống: mặt bánh trôi xuống, số nhỏ hơn hiện lên.
				_roll(_drag_wheel, -1 if _drag_acc > 0.0 else 1)
				_drag_acc -= DRAG_STEP * signf(_drag_acc)
		return true
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		var p := stage_pos(event)
		var w := _wheel_at(p)
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed and w >= 0:
			_current = w
			_roll(w, 1)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed and w >= 0:
			_current = w
			_roll(w, -1)
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed and w >= 0:
				_current = w
				_drag_wheel = w
				_drag_acc = 0.0
			elif not mb.pressed and _drag_wheel >= 0:
				# Bấm nhả tại chỗ (không kéo): nửa trên lùi số, nửa dưới tiến số.
				if absf(_drag_acc) < 4.0 and _wheel_at(p) == _drag_wheel:
					_roll(_drag_wheel, 1 if p.y > WHEEL_Y else -1)
				_drag_wheel = -1
			elif mb.pressed and _hasp_rect().has_point(p):
				submit_requested.emit()
		return true
	if pressed(event, LEFT):
		_current = wrapi(_current - 1, 0, selection.size())
	elif pressed(event, RIGHT):
		_current = wrapi(_current + 1, 0, selection.size())
	elif pressed(event, UP):
		_roll(_current, 1)
	elif pressed(event, DOWN):
		_roll(_current, -1)
	elif pressed(event, CONFIRM):
		submit_requested.emit()
	else:
		return false
	_box.queue_redraw()
	return true


func _roll(wheel: int, step: int) -> void:
	var count := options(wheel).size()
	if count == 0:
		return
	selection[wheel] = wrapi(selection[wheel] + step, 0, count)
	tick()


func play_wrong(_closing: bool) -> float:
	var t := create_tween()
	t.tween_property(self, "_hasp_lift", 6.0, 0.06)
	t.tween_property(self, "_hasp_lift", 0.0, 0.08)
	t.tween_property(self, "_hasp_lift", 4.0, 0.06)
	t.tween_property(self, "_hasp_lift", 0.0, 0.1)
	var s := create_tween()
	shake(_box, s, 7.0, 4, 0.45)
	return 0.9


func play_right() -> float:
	var t := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(self, "_hasp_lift", 34.0, 0.25)
	t.tween_property(self, "_lid_open", 1.0, 0.55).set_trans(Tween.TRANS_CUBIC)
	return 0.85


func _wheel_center(i: int) -> Vector2:
	return Vector2(BOX_CENTER.x + (i - (selection.size() - 1) * 0.5) * WHEEL_SPACING, WHEEL_Y)


func _wheel_at(p: Vector2) -> int:
	for i in selection.size():
		var c := _wheel_center(i)
		if Rect2(c - WINDOW * 0.5 - Vector2(10, 10), WINDOW + Vector2(36, 20)).has_point(p):
			return i
	return -1


func _hasp_rect() -> Rect2:
	return Rect2(BOX_CENTER.x - 40, 300, 80, 110)


# --- Vẽ ------------------------------------------------------------------------------

func _draw_box() -> void:
	var ci := _box
	var lid_dy := -78.0 * _lid_open
	# Bóng hộp trên taplô.
	PuzzleArt.soft_shadow(ci, Vector2(650, 640), Vector2(430, 44), 0.8)
	# Mặt trước thân hộp.
	var front := PackedVector2Array([Vector2(282, 336), Vector2(998, 336), Vector2(990, 628), Vector2(290, 628)])
	PuzzleArt.tex_poly(ci, front, PuzzleArt.TIN_TEX, Color(0.55, 0.58, 0.52), 1.0 / 420.0)
	PuzzleArt.grad_poly(ci, front, Color(0, 0, 0, 0.0), Color(0, 0, 0, 0.45))
	# Đường gân dập ngang thân hộp.
	for y: float in [372.0, 600.0]:
		ci.draw_line(Vector2(288, y), Vector2(994, y), Color(1, 1, 1, 0.10), 2.0)
		ci.draw_line(Vector2(288, y + 3), Vector2(994, y + 3), Color(0, 0, 0, 0.35), 2.0)
	# Vệt gỉ chảy xuống từ mép nắp.
	var rng := RandomNumberGenerator.new()
	rng.seed = 9
	for i in 14:
		var x := rng.randf_range(300, 980)
		var len := rng.randf_range(20, 120)
		Pictograms.stroke(ci, PackedVector2Array([Vector2(x, 338), Vector2(x + rng.randf_range(-3, 3), 338 + len)]),
				rng.randf_range(3, 9), Color(0.35, 0.16, 0.05, 0.35), true, 0.3, i)
	if _lid_open > 0.0:
		# Lòng hộp tối khi nắp hé.
		ci.draw_colored_polygon(PackedVector2Array([Vector2(282, 336 + lid_dy), Vector2(998, 336 + lid_dy),
				Vector2(998, 338), Vector2(282, 338)]), Color(0.05, 0.035, 0.02))
		ci.draw_line(Vector2(300, 337), Vector2(980, 337), Color(1.0, 0.75, 0.4, 0.35 * _lid_open), 2.0)
	_draw_lid(ci, lid_dy)
	_draw_lock(ci)


func _draw_lid(ci: CanvasItem, dy: float) -> void:
	var o := Vector2(0, dy)
	var top := PackedVector2Array([Vector2(338, 150) + o, Vector2(942, 150) + o, Vector2(1016, 300) + o, Vector2(264, 300) + o])
	PuzzleArt.tex_poly(ci, top, PuzzleArt.TIN_TEX, Color(0.72, 0.75, 0.68), 1.0 / 380.0, Vector2(0.3, 0.1))
	# Ánh đèn bão rọi xiên lên nắp.
	PuzzleArt.grad_poly(ci, top, Color(0, 0, 0, 0.35), Color(1.0, 0.85, 0.6, 0.08))
	# Chữ khắc bằng mũi đinh: rãnh tối + mép sáng.
	var engr := "SỐ XE"
	var xf := Transform2D(Vector2(1.0, 0.0), Vector2(0.0, 0.62), Vector2(640, 238) + o)
	for pass_i in 2:
		var off := Vector2(0, 1.6) if pass_i == 0 else Vector2.ZERO
		var col := Color(1, 0.95, 0.85, 0.35) if pass_i == 0 else Color(0.12, 0.1, 0.08, 0.85)
		ci.draw_set_transform_matrix(xf * Transform2D(-0.04, off))
		var w := _font_scratch.get_string_size(engr, HORIZONTAL_ALIGNMENT_LEFT, -1, 78).x
		ci.draw_string(_font_scratch, Vector2(-w * 0.5, 26), engr, HORIZONTAL_ALIGNMENT_LEFT, -1, 78, col)
		ci.draw_line(Vector2(-w * 0.5 - 6, 40), Vector2(w * 0.5 + 10, 34), col, 2.0)
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	# Mép nắp cuộn tròn.
	var lip := PackedVector2Array([Vector2(262, 298) + o, Vector2(1018, 298) + o, Vector2(1018, 338) + o, Vector2(262, 338) + o])
	PuzzleArt.tex_poly(ci, lip, PuzzleArt.TIN_TEX, Color(0.6, 0.63, 0.57), 1.0 / 300.0, Vector2(0.7, 0.2))
	PuzzleArt.grad_poly(ci, lip, Color(1, 1, 1, 0.22), Color(0, 0, 0, 0.5))
	ci.draw_line(Vector2(262, 299) + o, Vector2(1018, 299) + o, Color(1, 0.95, 0.85, 0.35), 2.0)
	ci.draw_line(Vector2(262, 338) + o, Vector2(1018, 338) + o, Color(0, 0, 0, 0.6), 2.0)
	# Bản lề khoen gắn vào nắp, khoen cắm xuống ổ khóa.
	var hasp := Rect2(Vector2(BOX_CENTER.x - 30, 286) + o, Vector2(60, 70))
	PuzzleArt.grad_poly(ci, PuzzleArt.rounded_rect(hasp, 8), PuzzleArt.BRASS_LIGHT.darkened(0.15), PuzzleArt.BRASS_DARK)
	PuzzleArt.screw(ci, hasp.position + Vector2(14, 16), 5, 0.4)
	PuzzleArt.screw(ci, hasp.position + Vector2(46, 16), 5, 1.3)
	var loop_top := 352.0 - _hasp_lift + dy * 0.6
	ci.draw_arc(Vector2(BOX_CENTER.x, loop_top + 8), 16, PI, TAU, 16, Color(0.2, 0.2, 0.2), 9.0, true)
	ci.draw_arc(Vector2(BOX_CENTER.x, loop_top + 8), 16, PI, TAU, 16, Color(0.62, 0.6, 0.56), 5.0, true)
	for side: float in [-16.0, 16.0]:
		ci.draw_line(Vector2(BOX_CENTER.x + side, loop_top + 8), Vector2(BOX_CENTER.x + side, loop_top + 34),
				Color(0.62, 0.6, 0.56), 5.0)


func _draw_lock(ci: CanvasItem) -> void:
	var count := selection.size()
	var plate := Rect2(BOX_CENTER.x - WHEEL_SPACING * count * 0.5 - 30, 384, WHEEL_SPACING * count + 60, 200)
	var pts := PuzzleArt.rounded_rect(plate, 18)
	ci.draw_colored_polygon(PuzzleArt.rounded_rect(plate.grow(4).grow_individual(0, 0, 4, 6), 20), Color(0, 0, 0, 0.5))
	PuzzleArt.grad_poly(ci, pts, PuzzleArt.BRASS_LIGHT, PuzzleArt.BRASS.darkened(0.25))
	PuzzleArt.tex_poly(ci, pts, PuzzleArt.FIBER_TEX, Color(0.4, 0.3, 0.15, 0.25), 1.0 / 200.0)
	PuzzleArt.bevel(ci, pts, Color(1, 0.9, 0.7, 0.8), Color(0.1, 0.05, 0.0, 0.9), 2.0)
	# Khe nhận khoen trên đầu ổ khóa.
	ci.draw_rect(Rect2(BOX_CENTER.x - 24, plate.position.y + 8, 48, 14), Color(0.08, 0.05, 0.02))
	for k in 4:
		PuzzleArt.screw(ci, plate.position + Vector2(18 + (plate.size.x - 36) * (k % 2), 18 + (plate.size.y - 36) * (k / 2)),
				6, k * 0.9)
	for i in count:
		_draw_wheel(ci, i)


func _draw_wheel(ci: CanvasItem, i: int) -> void:
	var c := _wheel_center(i)
	var win := Rect2(c - WINDOW * 0.5, WINDOW)
	var selected := i == _current
	# Hốc cửa sổ: tối, có viền vát.
	ci.draw_rect(win.grow(5), Color(0.18, 0.12, 0.05))
	ci.draw_rect(win.grow(2), Color(0.04, 0.03, 0.02))
	# Mặt trụ bánh số.
	var face := win.grow(-3)
	PuzzleArt.grad_poly(ci, PackedVector2Array([face.position, Vector2(face.end.x, face.position.y),
			Vector2(face.end.x, face.get_center().y), Vector2(face.position.x, face.get_center().y)]),
			Color(0.05, 0.05, 0.05), Color(0.22, 0.21, 0.19))
	PuzzleArt.grad_poly(ci, PackedVector2Array([Vector2(face.position.x, face.get_center().y),
			Vector2(face.end.x, face.get_center().y), face.end, Vector2(face.position.x, face.end.y)]),
			Color(0.22, 0.21, 0.19), Color(0.05, 0.05, 0.05))
	var shown := _shown[i] if i < _shown.size() else 0.0
	var base := int(floor(shown))
	var frac := shown - base
	for k in range(-2, 3):
		var digit := wrapi(base + k, 0, maxi(options(i).size(), 1))
		var angle := (k - frac) * (PI / 5.0)
		if absf(angle) > PI * 0.48:
			continue
		var y := c.y + sin(angle) * DIGIT_RADIUS
		var squash := cos(angle)
		var col := Color(0.93, 0.90, 0.80, clampf(squash * squash, 0.0, 1.0))
		var text := str(digit)
		var opts := options(i)
		if digit < opts.size():
			text = String(opts[digit])
		ci.draw_set_transform(Vector2(c.x, y), 0.0, Vector2(1.0, squash))
		PuzzleArt.text_center(ci, _font_digits, text, Vector2.ZERO, 44, col)
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	# Mép bánh có khía nhô ra bên phải cửa sổ, khía trôi theo số.
	var edge := Rect2(win.end.x + 4, win.position.y + 6, 12, win.size.y - 12)
	ci.draw_rect(edge, Color(0.25, 0.17, 0.07))
	for k in 16:
		var a := (k / 16.0 + shown / 10.0) * TAU
		var y := edge.get_center().y + sin(a) * edge.size.y * 0.5
		if cos(a) > 0.0:
			ci.draw_line(Vector2(edge.position.x, y), Vector2(edge.end.x, y), Color(0.85, 0.66, 0.34, cos(a)), 2.0)
	# Vạch chỉ số giữa cửa sổ và kính mờ.
	ci.draw_line(Vector2(win.position.x - 6, c.y), Vector2(win.position.x, c.y), PuzzleArt.BRASS_DARK, 3.0)
	ci.draw_rect(Rect2(win.position, Vector2(win.size.x, win.size.y * 0.22)), Color(0, 0, 0, 0.35))
	ci.draw_rect(Rect2(Vector2(win.position.x, win.end.y - win.size.y * 0.22), Vector2(win.size.x, win.size.y * 0.22)),
			Color(0, 0, 0, 0.35))
	# Vòng đang chọn: mũi tên đồng phía dưới + ánh đèn hắt lên.
	if selected:
		var tip := Vector2(c.x, win.end.y + 14)
		ci.draw_colored_polygon(PackedVector2Array([tip, tip + Vector2(-10, 14), tip + Vector2(10, 14)]),
				Color(0.95, 0.82, 0.5, 0.9))
		ci.draw_rect(win.grow(5), Color(1.0, 0.8, 0.45, 0.55 + 0.2 * sin(_time * 4.0)), false, 2.0)
	elif i == _hover:
		ci.draw_rect(win.grow(5), Color(1.0, 0.85, 0.6, 0.25), false, 2.0)
