## Dây chuông báo bến: sợi thừng chạy dọc trần xe tới quả chuông đồng ở đầu xe, đầu dây có
## con lăn gỗ để nắm. Giật bao nhiêu hồi thì buông tay; dừng tay một lúc là tín hiệu gửi đi.
##
## - Chuột: nắm con lăn kéo xuống rồi thả (mỗi lần kéo hết tầm là một hồi), hoặc bấm vào con lăn.
## - Bàn phím: S / Xuống / Space giật một hồi; E buông tay ngay.
## Kết quả là chỉ số lựa chọn (số hồi - 1), tối đa bằng số lựa chọn (3 hồi).
class_name BellRopeView
extends PuzzleView

const PULLEY := Vector2(760, 92)
const HANDLE_REST := Vector2(760, 430)
const PULL_DEPTH := 120.0
const SETTLE_TIME := 1.7

var _pulls := 0
var _pull := 0.0          # 0 nghỉ .. 1 kéo hết tầm
var _dragging := false
var _drag_start := 0.0
var _bell_swing := 0.0
var _time := 0.0
var _idle := 0.0
var _scene: Control


func _setup() -> void:
	texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	_scene = Control.new()
	_scene.size = size
	_scene.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_scene.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	add_child(_scene)
	_scene.draw.connect(_draw_scene)


func hint_text() -> String:
	return tr(&"UI_BELL_HINT")


func _max_pulls() -> int:
	return maxi(options(0).size(), 1)


func _process(delta: float) -> void:
	_time += delta
	_bell_swing *= exp(-3.0 * delta)
	if not _dragging and _pull > 0.0:
		_pull = maxf(0.0, _pull - delta * 4.0)
	# Giật xong, dừng tay một lúc: tín hiệu chuông coi như đã gửi.
	if _pulls > 0 and not _busy and not _dragging:
		_idle += delta
		if _idle >= (0.8 if _pulls >= _max_pulls() else SETTLE_TIME):
			_release()
	_scene.queue_redraw()


func handle_input(event: InputEvent) -> bool:
	if _busy:
		return true
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var p := stage_pos(event)
		if (event as InputEventMouseButton).pressed:
			if p.distance_to(_handle_pos()) < 70.0:
				_dragging = true
				_drag_start = p.y
				_idle = 0.0
		elif _dragging:
			_dragging = false
			if _pull < 0.15:
				_ring()
		return true
	if event is InputEventMouseMotion:
		if _dragging:
			var p := stage_pos(event)
			_pull = clampf((p.y - _drag_start) / PULL_DEPTH, 0.0, 1.0)
			_idle = 0.0
			if _pull >= 0.98:
				_ring()
				_drag_start = p.y + 9999.0
		return true
	if pressed(event, DOWN) or (event is InputEventKey and (event as InputEventKey).pressed
			and not (event as InputEventKey).echo and (event as InputEventKey).physical_keycode == KEY_SPACE):
		_ring()
		return true
	if pressed(event, [&"interact"]) or (event is InputEventKey and (event as InputEventKey).pressed
			and (event as InputEventKey).physical_keycode in [KEY_ENTER, KEY_KP_ENTER]):
		if _pulls > 0:
			_release()
		return true
	return false


## Một lần giật: dây căng, con lăn xuống hết tầm, quả chuông lắc.
func _ring() -> void:
	if _pulls >= _max_pulls():
		return
	_pulls += 1
	_idle = 0.0
	_pull = 1.0
	_bell_swing = 1.0
	selection[0] = _pulls - 1
	EventBus.ui_sfx_requested.emit(&"sfx_rope_pull")


func _release() -> void:
	if _busy or _pulls == 0:
		return
	_busy = true
	submit_requested.emit()


func play_right() -> float:
	return 0.35


func _handle_pos() -> Vector2:
	var sway := sin(_time * 1.3) * 6.0 * (1.0 - _pull)
	return HANDLE_REST + Vector2(sway, PULL_DEPTH * _pull)


func _draw_scene() -> void:
	var ci := _scene
	# Trần xe: dải tôn sơn kem có đinh tán, đã ố.
	var ceiling := PackedVector2Array([Vector2(0, 0), Vector2(1280, 0), Vector2(1280, 120), Vector2(0, 150)])
	PuzzleArt.tex_poly(ci, ceiling, PuzzleArt.TIN_TEX, Color(0.42, 0.40, 0.33), 1.0 / 500.0)
	PuzzleArt.grad_poly(ci, ceiling, Color(0, 0, 0, 0.6), Color(0, 0, 0, 0.1))
	for k in 16:
		var x := 40.0 + k * 80.0
		ci.draw_circle(Vector2(x, 128 - x * 0.023), 3, Color(0.15, 0.13, 0.1))
	# Quả chuông đồng gắn trên vách đầu xe (bên trái), lắc khi giật.
	var bell_pivot := Vector2(250, 120)
	var angle := sin(_time * 16.0) * 0.35 * _bell_swing
	ci.draw_rect(Rect2(bell_pivot + Vector2(-34, -40), Vector2(68, 20)), Color(0.18, 0.15, 0.12))
	ci.draw_set_transform(bell_pivot, angle)
	var dome := PackedVector2Array()
	for i in 21:
		var t := float(i) / 20.0
		var a := PI + t * PI
		dome.append(Vector2(cos(a) * 62, sin(a) * 66 + 70))
	dome.append(Vector2(70, 92))
	dome.append(Vector2(-70, 92))
	PuzzleArt.grad_poly(ci, dome, PuzzleArt.BRASS_LIGHT, PuzzleArt.BRASS_DARK)
	ci.draw_arc(Vector2(-14, 40), 34, PI * 1.1, PI * 1.45, 10, Color(1, 0.95, 0.75, 0.6), 5.0, true)
	ci.draw_line(Vector2(-70, 92), Vector2(70, 92), PuzzleArt.BRASS_DARK, 4.0)
	ci.draw_circle(Vector2(sin(_time * 22.0) * 14.0 * _bell_swing, 98), 9, Color(0.25, 0.2, 0.12))
	# Cần gạt búa chuông, nối với dây.
	ci.draw_line(Vector2(0, -8), Vector2(80, 16), Color(0.3, 0.28, 0.25), 6.0)
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	var lever_end := bell_pivot + Vector2(80, 16).rotated(angle)
	# Dây thừng: từ cần chuông chạy dọc trần qua ròng rọc rồi buông xuống.
	var handle := _handle_pos()
	var sag := 18.0 * (1.0 - _pull)
	var top_run := Pictograms.smooth(PackedVector2Array([lever_end, (lever_end + PULLEY) * 0.5 + Vector2(0, sag), PULLEY]), 10)
	_rope(ci, top_run)
	_rope(ci, PackedVector2Array([PULLEY + Vector2(14, 0), PULLEY + Vector2(14, 60), handle + Vector2(0, -36)]))
	ci.draw_circle(PULLEY, 20, Color(0.2, 0.18, 0.16))
	ci.draw_circle(PULLEY, 14, Color(0.42, 0.38, 0.32))
	ci.draw_circle(PULLEY, 4, Color(0.15, 0.13, 0.1))
	# Con lăn gỗ ở đầu dây, mòn bóng vì tay nắm.
	var grip := Rect2(handle + Vector2(-22, -40), Vector2(44, 96))
	PuzzleArt.soft_shadow(ci, handle + Vector2(18, 30), Vector2(40, 70), 0.4)
	var grip_pts := PuzzleArt.rounded_rect(grip, 20)
	PuzzleArt.tex_poly(ci, grip_pts, PuzzleArt.WOOD_TEX, Color(0.55, 0.36, 0.2), 1.0 / 160.0)
	PuzzleArt.grad_poly(ci, grip_pts, Color(1, 0.9, 0.7, 0.18), Color(0, 0, 0, 0.45))
	ci.draw_line(grip.position + Vector2(10, 14), grip.position + Vector2(10, 80), Color(1, 0.9, 0.7, 0.3), 3.0)
	if not _dragging and _pulls == 0:
		ci.draw_arc(handle + Vector2(0, 8), 64, 0, TAU, 40, Color(1, 0.85, 0.5, 0.25 + 0.15 * sin(_time * 3.0)), 2.0, true)
	# Đếm số hồi đã giật bằng những vạch nhỏ cạnh con lăn (như người ta đếm nhẩm).
	for i in _pulls:
		ci.draw_line(Vector2(860 + i * 18, 470), Vector2(856 + i * 18, 510), Color(0.95, 0.9, 0.78, 0.8), 3.0)


func _rope(ci: CanvasItem, pts: PackedVector2Array) -> void:
	var curve := Pictograms.smooth(pts, 10) if pts.size() > 2 else pts
	ci.draw_polyline(curve, Color(0.22, 0.17, 0.11), 9.0, true)
	ci.draw_polyline(curve, Color(0.55, 0.45, 0.30), 6.0, true)
	# Thớ thừng xoắn.
	for i in range(0, curve.size() - 1):
		var a := curve[i]
		var b := curve[i + 1]
		var d := (b - a)
		if d.length() < 0.01:
			continue
		var n := Vector2(-d.y, d.x).normalized() * 3.0
		ci.draw_line(a - n, (a + b) * 0.5 + n, Color(0.3, 0.22, 0.13, 0.7), 1.5)
