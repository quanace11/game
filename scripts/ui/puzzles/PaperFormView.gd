## Câu đố chưa có đồ vật riêng: một mảnh giấy ghi các hàng lựa chọn bằng bút chì,
## mỗi hàng có hai mũi tên vẽ tay để đổi. W/S chọn hàng, A/D (hoặc bấm mũi tên) đổi, E xác nhận.
class_name PaperFormView
extends PuzzleView

const ROW_H := 64.0

var _row := 0
var _sheet: PaperSheet
var _size := Vector2(560, 300)


func _setup() -> void:
	_size = Vector2(600, 150 + rows.size() * ROW_H)
	var look := {"paper_color": Color(0.88, 0.85, 0.75), "age": 0.5, "tear": 2.0, "folds": Vector2(0, 1),
			"fold_strength": 0.5, "stain_shift": Vector2(0.4, 0.6)}
	_sheet = PaperSheet.new(_size, look, _draw_ink)
	_sheet.place(Vector2(640, 350), -1.0)
	add_child(_sheet)


func _draw_ink(ci: CanvasItem) -> void:
	var head := InkWriter.new(PaperFonts.get_font(PaperFonts.BALLPOINT), 26, DocumentStyles.INK_BALLPOINT)
	head.jitter = 1.0
	head.align = HORIZONTAL_ALIGNMENT_CENTER
	head.write(ci, title, Vector2(30, 24), _size.x - 60)
	var label := InkWriter.new(PaperFonts.get_font(PaperFonts.PENCIL), 26, DocumentStyles.INK_PENCIL)
	label.jitter = 1.0
	var value := InkWriter.new(PaperFonts.get_font(PaperFonts.BALLPOINT), 30, DocumentStyles.INK_BALLPOINT)
	value.jitter = 1.0
	value.align = HORIZONTAL_ALIGNMENT_CENTER
	for i in rows.size():
		var y := 120.0 + i * ROW_H
		if i == _row:
			ci.draw_rect(Rect2(20, y - 34, _size.x - 40, ROW_H - 8), Color(0.95, 0.8, 0.3, 0.22))
		label.write_line(ci, String(rows[i].get("label", "")), Vector2(40, y))
		var opts := options(i)
		var text := String(opts[selection[i]]) if not opts.is_empty() else ""
		value.write_line(ci, text, Vector2(_size.x * 0.62, y))
		for side: float in [-1.0, 1.0]:
			var x := _size.x * 0.62 + side * 150.0
			Pictograms.stroke(ci, PackedVector2Array([Vector2(x - side * 10, y - 18), Vector2(x + side * 6, y - 9),
					Vector2(x - side * 10, y)]), 3.0, DocumentStyles.INK_PENCIL, true, 0.2)


func handle_input(event: InputEvent) -> bool:
	if _busy:
		return true
	if event is InputEventMouseButton and (event as InputEventMouseButton).pressed \
			and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var p := _sheet.parent_to_paper(stage_pos(event))
		for i in rows.size():
			var y := 120.0 + i * ROW_H
			if p.y > y - 40 and p.y < y + 16:
				_row = i
				if p.x > _size.x * 0.62 + 100:
					_cycle(1)
				elif p.x > _size.x * 0.62 - 190 and p.x < _size.x * 0.62 - 100:
					_cycle(-1)
				_sheet.redraw()
		return true
	if pressed(event, UP):
		_row = wrapi(_row - 1, 0, rows.size())
	elif pressed(event, DOWN):
		_row = wrapi(_row + 1, 0, rows.size())
	elif pressed(event, LEFT):
		_cycle(-1)
	elif pressed(event, RIGHT):
		_cycle(1)
	elif pressed(event, CONFIRM):
		submit_requested.emit()
	else:
		return false
	_sheet.redraw()
	return true


func _cycle(step: int) -> void:
	var count := options(_row).size()
	if count > 0:
		selection[_row] = wrapi(selection[_row] + step, 0, count)
		tick()


func play_wrong(_closing: bool) -> float:
	shake(_sheet, create_tween(), 8.0, 3, 0.35)
	return 0.8
