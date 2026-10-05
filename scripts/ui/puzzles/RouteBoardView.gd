## Bảng lộ trình trên kính lái: tấm gỗ sơn xanh có bốn cặp móc (Bến 1-4), bốn tấm biển tôn
## rơi dưới sàn. Người chơi nhặt biển treo lên móc.
##
## - Chuột: kéo một tấm biển (dưới sàn hoặc đang treo) thả vào móc; thả vào móc đã có biển thì
##   đổi chỗ hai tấm; thả ra ngoài thì biển rơi về sàn.
## - Bàn phím: A/D chọn cặp móc, W/S đổi tấm biển treo ở móc đó, E xong.
## Còn móc trống thì chưa xác nhận được. Sai: các biển lắc lư va vào nhau. Đúng: biển đứng yên.
class_name RouteBoardView
extends PuzzleView

const SLOT_X: Array[float] = [262.0, 514.0, 766.0, 1018.0]
const HOOK_Y := 214.0
const BOARD := Rect2(118, 96, 1044, 236)
const FLOOR_Y := 540.0
const SNAP := 130.0

var _plaques: Array[PaperSheet] = []
var _floor_spots: Array[Vector2] = []
var _floor_rot: Array[float] = []
var _swing: Array[float] = []
var _cursor := 0
var _drag := -1
var _drag_offset := Vector2.ZERO
var _time := 0.0
var _board: Control


func _setup() -> void:
	texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	_board = Control.new()
	_board.size = size
	_board.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_board.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	add_child(_board)
	_board.draw.connect(_draw_board)
	var opts := options(0)
	for i in selection.size():
		selection[i] = -1
	var rng := RandomNumberGenerator.new()
	rng.seed = 21
	for i in opts.size():
		var name := DocumentStyles.stop_name(String(opts[i]))
		var plaque := DocumentStyles.make_plaque(name, _kind_for(String(opts[i]), i), i + 7)
		plaque.pivot_offset = Vector2(plaque.size.x * 0.5, PaperSheet.MARGIN + 22.0)
		add_child(plaque)
		_plaques.append(plaque)
		_floor_spots.append(Vector2(250 + i * 262 + rng.randf_range(-30, 30), FLOOR_Y + rng.randf_range(-20, 40)))
		_floor_rot.append(rng.randf_range(-16, 16))
		_swing.append(0.0)
		_set_pose(i, _floor_spots[i], _floor_rot[i])


func hint_text() -> String:
	return tr(&"UI_ROUTE_HINT")


## Hình trên biển theo tên bến (khớp bản dịch ROUTE_*), không khớp thì đoán theo thứ tự.
func _kind_for(option: String, index: int) -> int:
	var table := {&"ROUTE_PAGODA": Pictograms.Kind.BELL, &"ROUTE_MARKET": Pictograms.Kind.POLE,
			&"ROUTE_TRAIN": Pictograms.Kind.TRAIN, &"ROUTE_FERRY": Pictograms.Kind.BOAT}
	for key: StringName in table:
		if tr(key) == option:
			return table[key]
	return DocumentStyles.STOP_KINDS[index % 4]


func _slot_of(plaque: int) -> int:
	return selection.find(plaque)


func _hang_point(slot: int) -> Vector2:
	return Vector2(SLOT_X[slot], HOOK_Y)


## Đặt tấm biển [param i] sao cho điểm treo (giữa hai lỗ) nằm tại [param p].
func _set_pose(i: int, p: Vector2, degrees: float) -> void:
	var plaque := _plaques[i]
	plaque.position = p - plaque.pivot_offset
	plaque.rotation_degrees = degrees


func _move_to_place(i: int) -> void:
	var plaque := _plaques[i]
	var slot := _slot_of(i)
	var target := _hang_point(slot) if slot >= 0 else _floor_spots[i]
	var rot := 0.0 if slot >= 0 else _floor_rot[i]
	var t := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	t.tween_property(plaque, "position", target - plaque.pivot_offset, 0.28)
	t.tween_property(plaque, "rotation_degrees", rot, 0.28)
	if slot >= 0:
		_swing[i] = 9.0
		EventBus.ui_sfx_requested.emit(&"sfx_plaque_hang")


func _process(delta: float) -> void:
	_time += delta
	for i in _plaques.size():
		if _swing[i] > 0.05 and _slot_of(i) >= 0 and i != _drag:
			_swing[i] *= exp(-2.2 * delta)
			_plaques[i].rotation_degrees = _swing[i] * sin(_time * 7.0 + i)
	_board.queue_redraw()


func handle_input(event: InputEvent) -> bool:
	if _busy:
		return true
	if event is InputEventMouseMotion:
		if _drag >= 0:
			var p := stage_pos(event)
			_plaques[_drag].position = p - _drag_offset
			var slot := _nearest_slot(p - _drag_offset + _plaques[_drag].pivot_offset)
			if slot >= 0:
				_cursor = slot
		return true
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var p := stage_pos(event)
		if (event as InputEventMouseButton).pressed:
			var hit := _plaque_at(p)
			if hit >= 0:
				_drag = hit
				_drag_offset = p - _plaques[hit].position
				move_child(_plaques[hit], -1)
				var t := create_tween()
				t.tween_property(_plaques[hit], "rotation_degrees", -4.0, 0.12)
				EventBus.ui_sfx_requested.emit(&"sfx_plaque_pick")
		elif _drag >= 0:
			var i := _drag
			_drag = -1
			var hang := _plaques[i].position + _plaques[i].pivot_offset
			_drop(i, _nearest_slot(hang))
		return true
	if pressed(event, LEFT):
		_cursor = wrapi(_cursor - 1, 0, SLOT_X.size())
	elif pressed(event, RIGHT):
		_cursor = wrapi(_cursor + 1, 0, SLOT_X.size())
	elif pressed(event, UP):
		_cycle(1)
	elif pressed(event, DOWN):
		_cycle(-1)
	elif pressed(event, CONFIRM):
		_try_submit()
	else:
		return false
	return true


func _try_submit() -> void:
	if selection.has(-1):
		status_requested.emit(tr(&"UI_ROUTE_EMPTY"))
		for i in _plaques.size():
			if _slot_of(i) < 0:
				shake(_plaques[i], create_tween(), 5.0, 2, 0.2)
		return
	submit_requested.emit()


## Treo biển [param i] vào móc [param slot] (-1 = thả xuống sàn), đổi chỗ nếu móc đã có biển.
func _drop(i: int, slot: int) -> void:
	var old := _slot_of(i)
	if slot < 0:
		if old >= 0:
			selection[old] = -1
		EventBus.ui_sfx_requested.emit(&"sfx_plaque_drop")
	else:
		var occupant := selection[slot]
		if old >= 0:
			selection[old] = occupant
		elif occupant >= 0:
			selection[slot] = -1
		selection[slot] = i
		_cursor = slot
		if occupant >= 0 and occupant != i:
			_move_to_place(occupant)
	_move_to_place(i)


## Bàn phím: đổi biển ở móc đang chọn sang tấm kế tiếp (lấy từ sàn hoặc đổi với móc khác).
func _cycle(step: int) -> void:
	var count := _plaques.size()
	var current := selection[_cursor]
	var next := wrapi(current + 1 + step, 0, count + 1) - 1
	if next < 0:
		selection[_cursor] = -1
		_move_to_place(current)
		tick()
		return
	_drop(next, _cursor)
	if current >= 0 and _slot_of(current) < 0:
		_move_to_place(current)
	tick()


func _nearest_slot(p: Vector2) -> int:
	var best := -1
	var best_d := SNAP
	for s in SLOT_X.size():
		var d := p.distance_to(_hang_point(s))
		if d < best_d:
			best_d = d
			best = s
	return best


func _plaque_at(p: Vector2) -> int:
	for k in range(get_child_count() - 1, -1, -1):
		var node := get_child(k)
		var i := _plaques.find(node)
		if i < 0:
			continue
		var local := _plaques[i].parent_to_paper(p)
		if Rect2(Vector2.ZERO, _plaques[i].paper_size).grow(6).has_point(local):
			return i
	return -1


func play_wrong(_closing: bool) -> float:
	for i in _plaques.size():
		_swing[i] = 16.0 + i * 3.0
	EventBus.ui_sfx_requested.emit(&"sfx_plaque_rattle")
	return 1.0


func play_right() -> float:
	for i in _plaques.size():
		_swing[i] = 2.0
	return 0.8


# --- Vẽ ------------------------------------------------------------------------------

func _draw_board() -> void:
	var ci := _board
	# Sàn xe dưới chân: thảm cao su sẫm có gân.
	var floor_rect := Rect2(60, 420, 1160, 260)
	ci.draw_rect(floor_rect, Color(0.07, 0.065, 0.06))
	for k in 30:
		var x := floor_rect.position.x + k * 40.0
		ci.draw_line(Vector2(x, floor_rect.position.y), Vector2(x, floor_rect.end.y), Color(0.12, 0.11, 0.1), 3.0)
	PuzzleArt.grad_poly(ci, PackedVector2Array([floor_rect.position, Vector2(floor_rect.end.x, floor_rect.position.y),
			floor_rect.end, Vector2(floor_rect.position.x, floor_rect.end.y)]), Color(0, 0, 0, 0.8), Color(0, 0, 0, 0.1))
	# Tấm bảng gỗ sơn xanh, sơn tróc lộ vân gỗ.
	PuzzleArt.soft_shadow(ci, BOARD.get_center() + Vector2(10, 22), BOARD.size * 0.55, 0.7)
	var board := PuzzleArt.rounded_rect(BOARD, 6)
	PuzzleArt.tex_poly(ci, board, PuzzleArt.WOOD_TEX, Color(0.47, 0.34, 0.22), Vector2(1.0 / 900.0, 1.0 / 260.0).x)
	var paint := PuzzleArt.rounded_rect(BOARD.grow(-10), 4)
	PuzzleArt.tex_poly(ci, paint, PuzzleArt.WOOD_TEX, Color(0.20, 0.34, 0.27), 1.0 / 700.0, Vector2(0.2, 0.0))
	PuzzleArt.tex_poly(ci, paint, PuzzleArt.FIBER_TEX, Color(0.1, 0.12, 0.08, 0.35), 1.0 / 300.0)
	PuzzleArt.bevel(ci, board, Color(1, 0.9, 0.7, 0.35), Color(0, 0, 0, 0.8), 3.0)
	var font := PaperFonts.get_font(PaperFonts.STAMP, 500)
	PuzzleArt.text_center(ci, font, tr(&"PAPER_ROUTE_BOARD"), Vector2(640, 128), 26, Color(0.92, 0.88, 0.74, 0.92))
	# Đường tuyến sơn trắng nối bốn bến, mũi tên chỉ chiều xe chạy.
	ci.draw_line(Vector2(SLOT_X[0] - 90, 162), Vector2(SLOT_X[3] + 80, 162), Color(0.9, 0.86, 0.72, 0.7), 3.0)
	var tip := Vector2(SLOT_X[3] + 96, 162)
	ci.draw_colored_polygon(PackedVector2Array([tip, tip + Vector2(-16, -8), tip + Vector2(-16, 8)]), Color(0.9, 0.86, 0.72, 0.8))
	for s in SLOT_X.size():
		var c := Vector2(SLOT_X[s], 162)
		var lit := s == _cursor
		ci.draw_circle(c, 17, Color(0.9, 0.86, 0.72) if not lit else Color(1.0, 0.86, 0.5))
		ci.draw_circle(c, 13, Color(0.2, 0.32, 0.25))
		PuzzleArt.text_center(ci, font, str(s + 1), c, 20, Color(0.95, 0.9, 0.78))
		for side: float in [-76.0, 76.0]:
			var h := Vector2(SLOT_X[s] + side, HOOK_Y - 16)
			ci.draw_circle(h + Vector2(1, 2), 5, Color(0, 0, 0, 0.5))
			ci.draw_circle(h, 4.5, Color(0.55, 0.52, 0.48))
			ci.draw_arc(h + Vector2(0, 11), 8, -PI * 0.5, PI * 0.9, 12, Color(0.62, 0.6, 0.55), 3.0, true)
		if lit:
			var glow := Rect2(SLOT_X[s] - 112, HOOK_Y - 34, 224, 170)
			ci.draw_rect(glow, Color(1.0, 0.8, 0.45, 0.10 + 0.05 * sin(_time * 4.0)))
			ci.draw_rect(glow, Color(1.0, 0.82, 0.5, 0.45), false, 1.5)
