## Bấm một vé trắng bằng kìm bấm vé của chú Bảy.
##
## Vé in sẵn ba hàng lỗ (ghế 1-9, người lớn / trẻ em, bến lên). Kìm bấm là thật: lỗ đã bấm
## không lấp lại được; bấm hỏng thì lấy vé trắng khác trong xấp.
## - Chuột: rê kìm tới lỗ, bấm chuột trái để bấm. Bấm vào xấp vé trắng để lấy vé mới.
## - Bàn phím: W/S chọn hàng, A/D chọn lỗ, Space bấm, R lấy vé mới, E đưa vé.
## Sai: vé bị vò lại vứt đi, vé trắng mới được rút ra. Đúng: vé được đưa đi.
class_name TicketPunchView
extends PuzzleView

const TICKET_SIZE := Vector2(380, 540)
const TICKET_CENTER := Vector2(560, 362)
const STACK_CENTER := Vector2(1010, 470)
const COUNTS: Array[int] = [9, 2, 5]

var _ticket: PaperSheet
var _stack: PaperSheet
var _tool: Control
var _row := 0
var _hole := 0
var _target := Vector2.ZERO
var _tool_pos := Vector2(900, 360)
var _clamp := 0.0
var _hover_stack := false
var _mouse_mode := false


func _setup() -> void:
	for i in selection.size():
		selection[i] = -1
	var look := {"paper_color": Color(0.86, 0.88, 0.80), "age": 0.4, "grain": 0.5, "foxing": 0.2, "tear": 0.6,
			"perforate": Vector4(1, 0, 0, 0), "light_pos": Vector2(0.45, 0.3)}
	var stack_draw := func(ci: CanvasItem) -> void:
		DocumentStyles.draw_punch_layout(ci, Vector2(190, 270), -1)
	_stack = PaperSheet.new(Vector2(190, 270), look, stack_draw)
	_stack.place(STACK_CENTER, 6.0)
	add_child(_stack)
	_new_ticket(false)
	_tool = Control.new()
	_tool.size = size
	_tool.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_tool)
	_tool.draw.connect(_draw_tool)
	_update_target()
	_tool_pos = _target + Vector2(60, 40)


func hint_text() -> String:
	return tr(&"UI_PUNCH_HINT")


func _new_ticket(animate: bool) -> void:
	for i in selection.size():
		selection[i] = -1
	var look := {"paper_color": Color(0.87, 0.89, 0.81), "age": 0.3, "grain": 0.5, "foxing": 0.1, "tear": 0.6,
			"perforate": Vector4(1, 0, 0, 0), "light_pos": Vector2(0.4, 0.3), "stain_shift": Vector2(randf(), randf())}
	var ink := func(ci: CanvasItem) -> void:
		DocumentStyles.draw_punch_layout(ci, TICKET_SIZE, _row if not _mouse_mode else -1)
	var holes := func(ci: CanvasItem) -> void:
		var r := DocumentStyles.hole_radius(TICKET_SIZE)
		for row in selection.size():
			if selection[row] >= 0:
				DocumentStyles.draw_hole(ci, DocumentStyles.punch_hole_pos(TICKET_SIZE, row, selection[row], COUNTS[row]), r)
	_ticket = PaperSheet.new(TICKET_SIZE, look, ink, holes)
	add_child(_ticket)
	if _tool:
		move_child(_tool, -1)
	if animate:
		_ticket.place(STACK_CENTER, 6.0)
		_ticket.scale = Vector2.ONE * 0.5
		var t := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		t.tween_property(_ticket, "position", TICKET_CENTER - _ticket.size * 0.5, 0.4)
		t.tween_property(_ticket, "rotation_degrees", -2.0, 0.4)
		t.tween_property(_ticket, "scale", Vector2.ONE, 0.4)
		EventBus.ui_sfx_requested.emit(&"sfx_paper")
	else:
		_ticket.place(TICKET_CENTER, -2.0)


## Vứt vé đang cầm (vò lại, ném sang trái).
func _discard(crumple: bool) -> void:
	var old := _ticket
	var t := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	t.tween_property(old, "position", old.position + Vector2(-520, 160), 0.45)
	t.tween_property(old, "rotation_degrees", -40.0 if crumple else -10.0, 0.45)
	if crumple:
		t.tween_property(old, "scale", Vector2(0.45, 0.35), 0.3)
		old.set_param(&"crumple", 2.5)
		old.set_param(&"folds", Vector2(2, 3))
		old.set_param(&"fold_strength", 1.6)
	t.chain().tween_callback(old.queue_free)


func _process(_delta: float) -> void:
	_update_target()
	_tool_pos = _tool_pos.lerp(_target, 0.35)
	_tool.queue_redraw()


func _update_target() -> void:
	if _ticket == null:
		return
	var local := DocumentStyles.punch_hole_pos(TICKET_SIZE, _row, _hole, COUNTS[_row])
	_target = _ticket.paper_to_parent(local)


func handle_input(event: InputEvent) -> bool:
	if _busy:
		return true
	if event is InputEventMouseMotion:
		var p := stage_pos(event)
		_hover_stack = _on_stack(p)
		var hit := _hole_at(p)
		if hit.x >= 0:
			_mouse_mode = true
			if hit.x != _row or hit.y != _hole:
				_row = hit.x
				_hole = hit.y
				_ticket.redraw()
		return true
	if event is InputEventMouseButton and (event as InputEventMouseButton).pressed \
			and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var p := stage_pos(event)
		if _on_stack(p):
			_take_new()
		elif _hole_at(p).x >= 0:
			_punch()
		return true
	if event is InputEventKey and (event as InputEventKey).pressed and not (event as InputEventKey).echo:
		var key := (event as InputEventKey).physical_keycode
		if key == KEY_SPACE:
			_punch()
			return true
		if key == KEY_R:
			_take_new()
			return true
	_mouse_mode = false
	if pressed(event, UP):
		_row = wrapi(_row - 1, 0, COUNTS.size())
		_hole = mini(_hole, COUNTS[_row] - 1)
	elif pressed(event, DOWN):
		_row = wrapi(_row + 1, 0, COUNTS.size())
		_hole = mini(_hole, COUNTS[_row] - 1)
	elif pressed(event, LEFT):
		_hole = wrapi(_hole - 1, 0, COUNTS[_row])
	elif pressed(event, RIGHT):
		_hole = wrapi(_hole + 1, 0, COUNTS[_row])
	elif pressed(event, [&"interact"]) or (event is InputEventKey and (event as InputEventKey).pressed
			and (event as InputEventKey).physical_keycode in [KEY_ENTER, KEY_KP_ENTER]):
		_try_submit()
	else:
		return false
	_ticket.redraw()
	return true


func _punch() -> void:
	if selection[_row] >= 0:
		status_requested.emit(tr(&"UI_PUNCH_ROW_DONE"))
		shake(_ticket, create_tween(), 3.0, 2, 0.15)
		return
	selection[_row] = _hole
	EventBus.ui_sfx_requested.emit(&"sfx_ticket_punch")
	var t := create_tween()
	t.tween_property(self, "_clamp", 1.0, 0.07)
	t.tween_callback(_ticket.redraw)
	t.tween_callback(_drop_chad.bind(_target))
	t.tween_property(self, "_clamp", 0.0, 0.18)


## Mẩu giấy tròn bị kìm đục ra rơi xuống.
func _drop_chad(at: Vector2) -> void:
	var chad := Control.new()
	chad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chad.position = at
	chad.draw.connect(func() -> void:
		chad.draw_circle(Vector2.ZERO, 6.0, Color(0.84, 0.86, 0.78))
		chad.draw_arc(Vector2.ZERO, 6.0, 0, TAU, 12, Color(0.6, 0.15, 0.12, 0.6), 1.0))
	add_child(chad)
	var t := create_tween().set_parallel()
	t.tween_property(chad, "position", at + Vector2(randf_range(-30, 30), 260), 0.7).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
	t.tween_property(chad, "scale", Vector2(1.0, 0.3), 0.7)
	t.tween_property(chad, "modulate:a", 0.0, 0.7)
	t.chain().tween_callback(chad.queue_free)


func _take_new() -> void:
	_discard(false)
	_new_ticket(true)
	tick()


func _try_submit() -> void:
	if selection.has(-1):
		status_requested.emit(tr(&"UI_PUNCH_INCOMPLETE"))
		return
	submit_requested.emit()


func play_wrong(_closing: bool) -> float:
	var t := create_tween()
	t.tween_interval(0.35)
	t.tween_callback(func() -> void:
		_discard(true)
		EventBus.ui_sfx_requested.emit(&"sfx_paper_crumple"))
	t.tween_interval(0.35)
	t.tween_callback(_new_ticket.bind(true))
	return 1.2


func play_right() -> float:
	var t := create_tween().set_parallel().set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	t.tween_property(_ticket, "position", _ticket.position + Vector2(0, -620), 0.6).set_delay(0.2)
	t.tween_property(_ticket, "rotation_degrees", 6.0, 0.6).set_delay(0.2)
	return 0.9


func _hole_at(p: Vector2) -> Vector2i:
	var local := _ticket.parent_to_paper(p)
	var r := DocumentStyles.hole_radius(TICKET_SIZE) * 2.2
	for row in COUNTS.size():
		for i in COUNTS[row]:
			if local.distance_to(DocumentStyles.punch_hole_pos(TICKET_SIZE, row, i, COUNTS[row])) < r:
				return Vector2i(row, i)
	return Vector2i(-1, -1)


func _on_stack(p: Vector2) -> bool:
	return Rect2(Vector2.ZERO, _stack.paper_size).has_point(_stack.parent_to_paper(p))


# --- Kìm bấm vé ------------------------------------------------------------------------

func _draw_tool() -> void:
	var ci := _tool
	# Xấp vé trắng: viền sáng khi rê chuột tới.
	if _hover_stack:
		ci.draw_set_transform_matrix(_stack.get_transform())
		ci.draw_rect(Rect2(Vector2.ONE * PaperSheet.MARGIN, _stack.paper_size).grow(4), Color(1, 0.85, 0.5, 0.6), false, 2.0)
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	var tip := _tool_pos
	var gap := 22.0 * (1.0 - _clamp)
	var steel := Color(0.58, 0.6, 0.62)
	var steel_dark := Color(0.2, 0.21, 0.22)
	# Bóng kìm đổ xuống vé.
	var sh := Vector2(14, 18)
	ci.draw_colored_polygon(_arm(tip + sh, gap, 1.0), Color(0, 0, 0, 0.35))
	ci.draw_colored_polygon(_arm(tip + sh, gap, -1.0), Color(0, 0, 0, 0.35))
	# Hai cán kìm từ dưới phải lên tới mỏ kìm.
	for side: float in [1.0, -1.0]:
		var arm := _arm(tip, gap, side)
		PuzzleArt.grad_poly(ci, arm, steel.lightened(0.15), steel_dark)
		var grip := PackedVector2Array([arm[2], arm[3], arm[3] + Vector2(70, 70), arm[2] + Vector2(70, 70)])
		ci.draw_colored_polygon(grip, Color(0.45, 0.12, 0.1))
	# Mỏ kìm: đầu đục tròn phía trên, đế đỡ phía dưới vé.
	ci.draw_circle(tip + Vector2(0, -gap * 0.5 - 6), 15, steel_dark)
	ci.draw_circle(tip + Vector2(0, -gap * 0.5 - 7), 12, steel)
	ci.draw_circle(tip + Vector2(-3, -gap * 0.5 - 10), 4, Color(1, 1, 1, 0.5))
	ci.draw_arc(tip, DocumentStyles.hole_radius(TICKET_SIZE) + 3, 0, TAU, 24, Color(1, 0.85, 0.5, 0.7 * (1.0 - _clamp)), 2.0, true)
	ci.draw_circle(tip + Vector2(34, 18), 6, steel_dark)


## Một cán kìm: từ mỏ ([param tip]) chéo xuống phải; [param side] = 1 cán trên, -1 cán dưới.
func _arm(tip: Vector2, gap: float, side: float) -> PackedVector2Array:
	var head := tip + Vector2(0, -gap * 0.5 * side)
	var dir := Vector2(1.0, 0.55 + 0.08 * side).normalized()
	var normal := Vector2(-dir.y, dir.x)
	var root := head + Vector2(30, 6 * side)
	var end := root + dir * 230.0 + normal * side * 26.0
	return PackedVector2Array([head + normal * 9.0, head - normal * 9.0, end - normal * 11.0, end + normal * 11.0])
