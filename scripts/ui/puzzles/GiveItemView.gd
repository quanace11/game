## Trả đồ cho hình nhân hành khách: đôi tay giấy của hình nhân chìa ra, ngửa lòng bàn tay;
## những món An đang mang bày trên vạt áo phía dưới. Đặt món nào vào tay là trao món đó.
##
## - Chuột: kéo một món thả vào lòng bàn tay, hoặc bấm chọn món rồi bấm vào đôi tay.
## - Bàn phím: A/D chọn món, E đặt vào tay.
class_name GiveItemView
extends PuzzleView

const HANDS := Vector2(640, 352)
const ITEM_Y := 570.0
const ITEM_SPACING := 230.0

var _kinds: Array[int] = []
var _pos: Array[Vector2] = []
var _hover := -1
var _drag := -1
var _drag_offset := Vector2.ZERO
var _given := -1
var _give_t := 0.0
var _time := 0.0
var _seat := ""
var _scene: Control
var _tags: Array[Label] = []


func _setup() -> void:
	texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	_seat = String(puzzle_id).trim_prefix("give_")
	var table := {&"ITEM_NON_COI_NAME": Pictograms.Kind.HELMET, &"ITEM_THUOC_BAC_NAME": Pictograms.Kind.HERBS,
			&"ITEM_DIEU_CAY_NAME": Pictograms.Kind.PIPE}
	var opts := options(0)
	for i in opts.size():
		var kind := Pictograms.Kind.HERBS
		for key: StringName in table:
			if tr(key) == String(opts[i]):
				kind = table[key]
		_kinds.append(kind)
		_pos.append(_home(i))
	_scene = Control.new()
	_scene.size = size
	_scene.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_scene.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	add_child(_scene)
	_scene.draw.connect(_draw_scene)
	for i in opts.size():
		var tag := DocumentStyles.caption_tag(String(opts[i]), _home(i) + Vector2(0, 70))
		add_child(tag)
		_tags.append(tag)


func hint_text() -> String:
	return tr(&"UI_GIVE_HINT")


func _home(i: int) -> Vector2:
	var n := options(0).size()
	return Vector2(640 + (i - (n - 1) * 0.5) * ITEM_SPACING, ITEM_Y)


func _process(delta: float) -> void:
	_time += delta
	for i in _pos.size():
		if i == _drag or i == _given:
			continue
		var lift := Vector2(0, -18) if i == selection[0] else Vector2.ZERO
		_pos[i] = _pos[i].lerp(_home(i) + lift, minf(1.0, delta * 12.0))
	_scene.queue_redraw()


func handle_input(event: InputEvent) -> bool:
	if _busy:
		return true
	if event is InputEventMouseMotion:
		var p := stage_pos(event)
		if _drag >= 0:
			_pos[_drag] = p - _drag_offset
		else:
			_hover = _item_at(p)
		return true
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var p := stage_pos(event)
		if (event as InputEventMouseButton).pressed:
			var hit := _item_at(p)
			if hit >= 0:
				if selection[0] != hit:
					tick()
				selection[0] = hit
				_drag = hit
				_drag_offset = p - _pos[hit]
			elif p.distance_to(HANDS) < 150.0:
				_give()
		elif _drag >= 0:
			var i := _drag
			_drag = -1
			if _pos[i].distance_to(HANDS) < 160.0:
				selection[0] = i
				_give()
		return true
	if pressed(event, LEFT):
		selection[0] = wrapi(selection[0] - 1, 0, maxi(_pos.size(), 1))
		tick()
	elif pressed(event, RIGHT):
		selection[0] = wrapi(selection[0] + 1, 0, maxi(_pos.size(), 1))
		tick()
	elif pressed(event, CONFIRM):
		_give()
	else:
		return false
	return true


func _give() -> void:
	if _pos.is_empty():
		return
	_given = selection[0]
	submit_requested.emit()


func play_right() -> float:
	var i := _given if _given >= 0 else selection[0]
	_given = i
	var t := create_tween().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	t.tween_method(func(v: Vector2) -> void: _pos[i] = v, _pos[i], HANDS + Vector2(0, -6), 0.45)
	t.parallel().tween_property(_tags[i], "modulate:a", 0.0, 0.3)
	t.tween_property(self, "_give_t", 1.0, 0.35)
	EventBus.ui_sfx_requested.emit(&"sfx_paper")
	return 0.95


func _item_at(p: Vector2) -> int:
	for i in _pos.size():
		if p.distance_to(_pos[i]) < 80.0:
			return i
	return -1


# --- Vẽ ------------------------------------------------------------------------------

func _draw_scene() -> void:
	var ci := _scene
	var breathe := sin(_time * 1.1) * 2.0
	# Thân áo giấy xanh của hình nhân, vai xuôi, phần đầu chìm vào bóng tối phía trên.
	var robe := Pictograms.smooth(PackedVector2Array([Vector2(520, 60), Vector2(760, 60), Vector2(880, 120),
			Vector2(915, 280), Vector2(365, 280), Vector2(400, 120)]), 6, true)
	PuzzleArt.tex_poly(ci, robe, PuzzleArt.FIBER_TEX, Color(0.16, 0.30, 0.42), 1.0 / 260.0)
	PuzzleArt.grad_poly(ci, robe, Color(0, 0, 0, 0.85), Color(0, 0, 0, 0.2))
	for k in 4:
		var y := 140.0 + k * 40.0
		ci.draw_line(Vector2(410 - k * 6, y), Vector2(870 + k * 6, y), Color(0.85, 0.66, 0.25, 0.14), 1.5)
	Pictograms.stroke(ci, PackedVector2Array([Vector2(585, 62), Vector2(640, 150), Vector2(695, 62)]), 14.0,
			Color(0.66, 0.50, 0.2), false, 0.15)
	var paper := Color(0.90, 0.88, 0.82)
	var ink := Color(0.08, 0.06, 0.05, 0.9)
	# Hai ống tay áo đỏ chìa về phía An, thu nhỏ dần tới cổ tay, mép viền vàng.
	for side: float in [-1.0, 1.0]:
		var shoulder := Vector2(640 + side * 225, 130)
		var cuff := Vector2(640 + side * 64, 300 + breathe)
		var sleeve := Pictograms.smooth(PackedVector2Array([shoulder + Vector2(-side * 40, -60),
				shoulder + Vector2(side * 45, 10), cuff + Vector2(side * 48, 8), cuff + Vector2(-side * 40, 6),
				shoulder + Vector2(-side * 90, 40)]), 5, true)
		PuzzleArt.tex_poly(ci, sleeve, PuzzleArt.FIBER_TEX, Color(0.55, 0.12, 0.1), 1.0 / 240.0)
		PuzzleArt.grad_poly(ci, sleeve, Color(0, 0, 0, 0.6), Color(0, 0, 0, 0.05))
	# Đôi bàn tay giấy ngửa lên, chụm lại thành lòng chén, ngón tay chĩa về phía An.
	for side: float in [-1.0, 1.0]:
		var palm_c := Vector2(640 + side * 46, 352 + breathe)
		var palm := PackedVector2Array()
		for k in 18:
			var a := TAU * k / 18.0
			palm.append(palm_c + Vector2(cos(a) * 44, sin(a) * 50).rotated(side * 0.18))
		# Bốn ngón tay xòe nhẹ, cong xuống; ngón cái nằm phía ngoài.
		var fingers: Array[PackedVector2Array] = []
		for f in 4:
			var base := palm_c + Vector2(side * (-26 + f * 17), 36 - absf(f - 1.5) * 4)
			var length := [36.0, 44.0, 42.0, 32.0][f] as float
			var dir := Vector2(side * (-0.12 + f * 0.1), 1.0).normalized()
			fingers.append(PackedVector2Array([base, base + dir * length * 0.55 + Vector2(side * 2, 0), base + dir * length]))
		var thumb_base := palm_c + Vector2(side * 38, -6)
		fingers.append(PackedVector2Array([thumb_base, thumb_base + Vector2(side * 22, 14), thumb_base + Vector2(side * 30, 34)]))
		# Viền mực trước, giấy đè lên sau để thành nét bao.
		ci.draw_colored_polygon(_grow(palm, palm_c, 2.6), ink)
		for fp in fingers:
			Pictograms.stroke(ci, Pictograms.smooth(fp, 4), 17.0, ink, false, 0.0)
		for fp in fingers:
			Pictograms.stroke(ci, Pictograms.smooth(fp, 4), 12.5, paper, false, 0.0)
			ci.draw_circle(fp[2], 4.0, Color(0.78, 0.18, 0.18, 0.85))
		ci.draw_colored_polygon(palm, paper)
		# Chỉ tay vẽ bút lông, bóng lòng bàn tay.
		PuzzleArt.grad_poly(ci, palm, Color(0, 0, 0, 0.0), Color(0, 0, 0, 0.12))
		Pictograms.stroke(ci, PackedVector2Array([palm_c + Vector2(-side * 28, -8), palm_c + Vector2(side * 4, 6),
				palm_c + Vector2(side * 26, 0)]), 1.6, Color(ink, 0.5), true, 0.3)
		Pictograms.stroke(ci, PackedVector2Array([palm_c + Vector2(-side * 20, 14), palm_c + Vector2(side * 18, 20)]),
				1.4, Color(ink, 0.4), true, 0.3)
		# Cổ tay áo viền kim tuyến đè lên cổ tay.
		var cuff := Vector2(640 + side * 64, 300 + breathe)
		Pictograms.stroke(ci, PackedVector2Array([cuff + Vector2(-side * 44, 4), cuff + Vector2(0, 12), cuff + Vector2(side * 50, 6)]),
				12.0, Color(0.86, 0.68, 0.28), false, 0.2)
	# Bóng lòng bàn tay chờ đồ.
	if _given < 0:
		var glow := 0.18 + 0.1 * sin(_time * 3.0)
		ci.draw_arc(HANDS + Vector2(0, 10), 120, 0, TAU, 48, Color(1, 0.85, 0.55, glow), 2.0, true)
	# Biển số ghế dán trên vách.
	var plate := Rect2(1040, 70, 120, 80)
	ci.draw_rect(plate.grow(3), Color(0.1, 0.08, 0.06))
	ci.draw_rect(plate, Color(0.86, 0.84, 0.76))
	PuzzleArt.text_center(ci, PaperFonts.get_font(PaperFonts.STAMP, 700), _seat, plate.get_center(), 46, Color(0.62, 0.12, 0.1))
	# Vạt áo của An phía dưới, bày các món đồ.
	var cloth := PackedVector2Array([Vector2(180, 500), Vector2(1100, 500), Vector2(1180, 700), Vector2(100, 700)])
	PuzzleArt.tex_poly(ci, cloth, PuzzleArt.FIBER_TEX, Color(0.16, 0.15, 0.13), 1.0 / 300.0)
	PuzzleArt.grad_poly(ci, cloth, Color(0, 0, 0, 0.4), Color(0, 0, 0, 0.7))
	var fills := {Pictograms.Kind.HELMET: Color(0.33, 0.40, 0.24), Pictograms.Kind.HERBS: Color(0.80, 0.72, 0.55),
			Pictograms.Kind.PIPE: Color(0.62, 0.48, 0.26)}
	for i in _pos.size():
		var p := _pos[i]
		var lifted := i == selection[0] and _given < 0
		var scale_k := 1.25 if i != _given else lerpf(1.25, 0.9, _give_t)
		PuzzleArt.soft_shadow(ci, p + Vector2(10, 46), Vector2(70, 18), 0.6 if not lifted else 0.35)
		if lifted or i == _hover:
			ci.draw_circle(p, 74, Color(1, 0.85, 0.55, 0.10 if not lifted else 0.16))
		Pictograms.draw(ci, _kinds[i], p, scale_k, Color(0.1, 0.08, 0.06), 3.0, fills.get(_kinds[i], Color(0.6, 0.5, 0.4)))


func _grow(pts: PackedVector2Array, c: Vector2, d: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	for p in pts:
		out.append(p + (p - c).normalized() * d)
	return out
