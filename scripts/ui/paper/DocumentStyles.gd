## Dựng "vật thật" cho từng tài liệu trong DocumentViewer: trang nhật ký, mẩu giấy ghi địa chỉ,
## vé xe, lá bùa, giấy phép, sổ phụ xe, vở học trò, vành nón, biển bến, cuống vé, nhãn dán...
##
## Chọn kiểu theo khóa dịch của trang ([constant STYLE_BY_KEY]). DocumentViewer chỉ nhận chữ đã
## dịch, nên [method key_for_text] dò ngược chữ -> khóa (theo ngôn ngữ hiện tại). Trang không
## có trong bảng thì đoán: dòng đầu viết hoa = giấy in, còn lại = giấy viết tay.
##
## Lời dẫn của người kể (cả đoạn nằm trong ngoặc đơn, ví dụ "(Kẹp trong túi nilông nên còn khô.)")
## không viết lên giấy mà hiện thành chú thích dưới vật ([code]captions[/code]).
class_name DocumentStyles
extends RefCounted

const STYLE_BY_KEY := {
	&"DOC_DIARY_PAGE_1": &"diary", &"DOC_DIARY_PAGE_2": &"diary", &"DOC_DIARY_PAGE_3": &"diary",
	&"DOC_ADDRESS_NOTE": &"note",
	&"DOC_BUS_TICKET": &"ticket",
	&"DOC_TALISMAN": &"talisman",
	&"DOC_DRIVER_LICENSE": &"license",
	&"DOC_PERMIT": &"permit",
	&"DOC_CONDUCTOR_LEDGER": &"ledger",
	&"DOC_PATTERN_BOOK_1": &"pattern_book", &"DOC_PATTERN_BOOK_2": &"pattern_book",
	&"DOC_PATTERN_BOOK_3": &"paper_stack",
	&"DOC_HUNG_NOTEBOOK": &"school_notebook",
	&"DOC_NAM_HAT": &"hat",
	&"DOC_FALLEN_PLAQUES": &"plaques",
	&"DOC_TICKET_STUBS_1": &"stubs", &"DOC_TICKET_STUBS_2": &"stubs",
	&"DOC_BELL_RULES": &"sticker",
}
## Các kiểu hợp lệ cho [signal EventBus.styled_document_requested].
const STYLES: Array[StringName] = [&"diary", &"note", &"ticket", &"talisman", &"license", &"permit",
		&"ledger", &"pattern_book", &"paper_stack", &"school_notebook", &"hat", &"plaques", &"stubs",
		&"sticker", &"incense", &"form", &"handwritten"]

const CENTER := Vector2(640, 345)

const INK_BLUE_BLACK := Color(0.09, 0.11, 0.27)
const INK_BALLPOINT := Color(0.10, 0.18, 0.50)
const INK_PURPLE := Color(0.34, 0.15, 0.50)
const INK_PENCIL := Color(0.20, 0.20, 0.22, 0.9)
const INK_PRINT := Color(0.10, 0.09, 0.08)
const INK_PRINT_RED := Color(0.60, 0.11, 0.10)
const INK_STAMP := Color(0.78, 0.10, 0.13, 0.82)
const INK_BRUSH := Color(0.06, 0.045, 0.04)
const INK_CINNABAR := Color(0.80, 0.12, 0.08)
const RULE_BLUE := Color(0.30, 0.42, 0.72, 0.38)
const RULE_RED := Color(0.78, 0.22, 0.22, 0.55)
const GRID_PURPLE := Color(0.50, 0.36, 0.66, 0.30)

## Hình biển bến theo thứ tự liệt kê trong các trang (chùa, chợ, tàu, đò).
const STOP_KINDS: Array[int] = [Pictograms.Kind.BELL, Pictograms.Kind.POLE, Pictograms.Kind.TRAIN, Pictograms.Kind.BOAT]

static var _reverse: Dictionary = {}
static var _reverse_locale := ""


# --- Chọn kiểu --------------------------------------------------------------------------

## Khóa dịch có bản dịch đúng bằng [param text] (theo ngôn ngữ hiện tại), không thấy thì &"".
static func key_for_text(text: String) -> StringName:
	var locale := TranslationServer.get_locale()
	if locale != _reverse_locale or _reverse.is_empty():
		_reverse.clear()
		_reverse_locale = locale
		for key: StringName in STYLE_BY_KEY:
			_reverse[TranslationServer.translate(key)] = key
	return _reverse.get(text, &"")


## Kiểu giấy cho một trang. [param title]: tên vật (để nhận ra lá "Thắp hương hỏi").
static func style_for(text: String, title: String) -> StringName:
	if title == TranslationServer.translate(&"UI_INCENSE_TITLE"):
		return &"incense"
	var key := key_for_text(text)
	if key != &"":
		return STYLE_BY_KEY[key]
	var first := text.strip_edges().split("\n")[0]
	if first.length() > 3 and first == first.to_upper() and first != first.to_lower():
		return &"form"
	return &"handwritten"


## Dựng một trang. Trả về {"items": Array[Control] đã đặt chỗ trên sân khấu 1280x720,
## "captions": PackedStringArray lời dẫn}.
static func build(style: StringName, text: String, title: String) -> Dictionary:
	match style:
		&"diary": return _diary(text)
		&"note": return _note(text)
		&"ticket": return _ticket(text)
		&"talisman": return _talisman(text)
		&"license": return _form(text, true, false)
		&"permit": return _form(text, false, true)
		&"form": return _form(text, false, false)
		&"ledger": return _ledger(text)
		&"pattern_book": return _pattern_book(text)
		&"paper_stack": return _paper_stack(text)
		&"school_notebook": return _school_notebook(text)
		&"hat": return _hat(text)
		&"plaques": return _plaques(text)
		&"stubs": return _stubs(text)
		&"sticker": return _sticker(text)
		&"incense": return _incense(text)
	return _handwritten(text)


# --- Tiện ích phân tích chữ ----------------------------------------------------------

## Tách đoạn lời dẫn (cả đoạn nằm trong ngoặc đơn) ra khỏi phần chữ trên giấy.
static func split_narration(text: String) -> Dictionary:
	var body := PackedStringArray()
	var captions := PackedStringArray()
	for para in text.split("\n"):
		var t := para.strip_edges()
		if t.begins_with("(") and t.ends_with(")"):
			captions.append(t.substr(1, t.length() - 2))
		else:
			body.append(para)
	return {"body": "\n".join(body).strip_edges(), "captions": captions}


## Phần nằm giữa cặp ngoặc kép đầu-cuối của [param s], không có thì "".
static func quoted(s: String) -> String:
	var a := s.find("\"")
	var b := s.rfind("\"")
	if a >= 0 and b > a:
		return s.substr(a + 1, b - a - 1)
	for pair: Array in [["“", "”"], ["«", "»"]]:
		a = s.find(pair[0])
		b = s.rfind(pair[1])
		if a >= 0 and b > a:
			return s.substr(a + 1, b - a - 1)
	return ""


## Dòng "Nhãn: giá trị" -> [nhãn, giá trị]; không có dấu hai chấm thì [] .
static func field(line: String) -> PackedStringArray:
	var i := line.find(":")
	if i <= 0 or i > 28:
		return PackedStringArray()
	return PackedStringArray([line.substr(0, i).strip_edges(), line.substr(i + 1).strip_edges()])


static func _result(items: Array, captions: PackedStringArray) -> Dictionary:
	return {"items": items, "captions": captions}


static func _font(family: String, weight: int = 400) -> Font:
	return PaperFonts.get_font(family, weight)


static func _writer(family: String, font_size: int, color: Color, hand: bool, weight: int = 400) -> InkWriter:
	var w := InkWriter.new(_font(family, weight), font_size, color)
	if hand:
		w.jitter = 1.0
		w.pressure = 0.5
		w.slope = -0.006
		w.wander = 6.0
	return w


# --- Hình vẽ chung -------------------------------------------------------------------------

## Dòng kẻ ngang của giấy sổ, bắt đầu từ [param top], cách nhau [param step].
static func _rules(ci: CanvasItem, size: Vector2, top: float, step: float, color: Color) -> void:
	var y := top
	while y < size.y - 12.0:
		ci.draw_line(Vector2(0, y), Vector2(size.x, y), color, 1.2)
		y += step


## Chữ chạy theo cung tròn (dấu mộc, vành nón). [param mirrored] = lật gương từng chữ.
static func arc_text(ci: CanvasItem, text: String, center: Vector2, radius: float, mid_angle: float,
		font: Font, font_size: int, color: Color, mirrored := false, clockwise := true) -> void:
	var widths: Array[float] = []
	var total := 0.0
	for ch in text:
		var cw := font.get_string_size(ch, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
		widths.append(cw)
		total += cw
	var dir := 1.0 if clockwise else -1.0
	var angle := mid_angle - dir * total * 0.5 / radius
	for i in text.length():
		var half := widths[i] * 0.5 / radius
		angle += dir * half
		var p := center + Vector2(cos(angle), sin(angle)) * radius
		var rot := angle + dir * PI * 0.5
		var xf := Transform2D(rot, p)
		if mirrored:
			xf = xf * Transform2D(0.0, Vector2(-1, 1), 0.0, Vector2.ZERO)
		ci.draw_set_transform_matrix(xf)
		ci.draw_string(font, Vector2(-widths[i] * 0.5, font_size * 0.35), text[i], HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
		angle += dir * half
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


## Dấu mộc tròn: hai vòng tròn, chữ chạy vòng trên, ngôi sao giữa.
static func round_stamp(ci: CanvasItem, center: Vector2, radius: float, text: String, color: Color,
		angle := 0.0) -> void:
	ci.draw_set_transform(center, angle)
	ci.draw_arc(Vector2.ZERO, radius, 0, TAU, 64, color, 2.6, true)
	ci.draw_arc(Vector2.ZERO, radius * 0.66, 0, TAU, 48, color, 1.6, true)
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)
	var font := _font(PaperFonts.STAMP, 500)
	arc_text(ci, text, center, radius * 0.82, angle - PI * 0.5, font, int(radius * 0.24), color)
	var star := PackedVector2Array()
	for i in 10:
		var a := -PI * 0.5 + angle + TAU * i / 10.0
		var r := radius * (0.3 if i % 2 == 0 else 0.12)
		star.append(center + Vector2(cos(a), sin(a)) * r)
	ci.draw_colored_polygon(star, color)


## Dấu chữ nhật hai viền (VÉ TRẺ EM, ĐÃ SOÁT...).
static func box_stamp(ci: CanvasItem, center: Vector2, text: String, font_size: int, color: Color, angle: float) -> void:
	var font := _font(PaperFonts.STAMP, 700)
	var ts := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size)
	var half := Vector2(ts.x * 0.5 + 10, font_size * 0.75)
	ci.draw_set_transform(center, angle)
	ci.draw_rect(Rect2(-half, half * 2.0), color, false, 2.4)
	ci.draw_rect(Rect2(-half + Vector2(3, 3), half * 2.0 - Vector2(6, 6)), color, false, 1.0)
	ci.draw_string(font, Vector2(-ts.x * 0.5, font_size * 0.36), text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


## Vệt mực nhòe nước che mất chữ.
static func smudge(ci: CanvasItem, rect: Rect2, color: Color, seed_value: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	for i in 7:
		var c := Color(color, color.a * 0.16)
		var r := Vector2(rect.size.x * rng.randf_range(0.25, 0.55), rect.size.y * rng.randf_range(0.35, 0.7))
		var p := rect.position + Vector2(rng.randf() * rect.size.x, rng.randf() * rect.size.y)
		var pts := PackedVector2Array()
		for k in 16:
			var a := TAU * k / 16.0
			pts.append(p + Vector2(cos(a) * r.x, sin(a) * r.y) * rng.randf_range(0.8, 1.15))
		ci.draw_colored_polygon(pts, c)
	for i in 3:
		var y := rect.position.y + rect.size.y * (0.3 + i * 0.22)
		Pictograms.stroke(ci, PackedVector2Array([Vector2(rect.position.x, y), Vector2(rect.end.x, y + rng.randf_range(-3, 3))]),
				rect.size.y * 0.22, Color(color, color.a * 0.35), true, 0.4, seed_value + i)


## Vòng hoen gỉ quanh lỗ ghim.
static func rust_ring(ci: CanvasItem, center: Vector2, radius: float) -> void:
	for i in 6:
		ci.draw_circle(center, radius * (1.0 - i * 0.14), Color(0.45, 0.24, 0.08, 0.07))




# --- Các kiểu giấy ------------------------------------------------------------------------

static func _diary(text: String) -> Dictionary:
	var parts := split_narration(text)
	var body: String = parts["body"]
	var size := Vector2(520, 640)
	var look := PaperSheet.LOOK_NOTEBOOK.duplicate()
	look.merge({"paper_color": Color(0.91, 0.87, 0.76), "age": 0.6, "stain": 0.12, "stain_shift": Vector2(0.31, 0.62),
			"tear": 2.0, "light_pos": Vector2(0.3, 0.2)}, true)
	var draw_ink := func(ci: CanvasItem) -> void:
		_rules(ci, size, 96.0, 34.0, RULE_BLUE)
		ci.draw_line(Vector2(72, 0), Vector2(72, size.y), RULE_RED, 1.4)
		ci.draw_line(Vector2(76, 0), Vector2(76, size.y), Color(RULE_RED, 0.3), 1.0)
		var w := _writer(PaperFonts.PEN, 25, INK_BLUE_BLACK, true)
		w.line_height = 34.0
		# Chân chữ đặt lên dòng kẻ: dòng đầu ở y = 96 + 34.
		w.write(ci, body, Vector2(90, 96.0 + 34.0 - 25.0 - 4.0), size.x - 120.0)
	var sheet := PaperSheet.new(size, look, draw_ink)
	sheet.place(CENTER, -1.4)
	return _result([sheet], parts["captions"])


static func _note(text: String) -> Dictionary:
	var parts := split_narration(text)
	var body: String = parts["body"]
	var w := _writer(PaperFonts.BALLPOINT, 30, INK_BALLPOINT, true)
	w.line_height = 40.0
	var size := Vector2(470, maxf(220.0, w.measure(body, 400.0) + 110.0))
	var look := PaperSheet.LOOK_NOTEBOOK.duplicate()
	look.merge({"paper_color": Color(0.92, 0.89, 0.80), "tear": 5.0, "tear_freq": 1.6, "folds": Vector2(1, 1),
			"fold_strength": 0.9, "stain_shift": Vector2(0.7, 0.2), "age": 0.5}, true)
	var draw_ink := func(ci: CanvasItem) -> void:
		_rules(ci, size, 58.0, 40.0, Color(RULE_BLUE, 0.25))
		w.write(ci, body, Vector2(36, 58.0 + 40.0 - 30.0 - 6.0), size.x - 70.0)
	var sheet := PaperSheet.new(size, look, draw_ink)
	sheet.place(CENTER, 2.5)
	return _result([sheet], parts["captions"])


static func _handwritten(text: String) -> Dictionary:
	return _note(text)


## Vé xe khách: mặt trước in đỏ, chữ điền tay bằng bút bi; mặt sau (nếu lời dẫn có câu trong
## ngoặc kép) là dòng bút chì.
static func _ticket(text: String) -> Dictionary:
	var parts := split_narration(text)
	var lines: PackedStringArray = String(parts["body"]).split("\n", false)
	var heading := lines[0] if not lines.is_empty() else ""
	var fields: Array = []
	for i in range(1, lines.size()):
		var f := field(lines[i])
		if not f.is_empty():
			fields.append(f)
	var size := Vector2(330, 470)
	var look := {"paper_color": Color(0.86, 0.88, 0.80), "age": 0.55, "grain": 0.55, "foxing": 0.35, "tear": 0.8,
			"perforate": Vector4(1, 0, 0, 0), "folds": Vector2(0, 1), "fold_strength": 0.5, "stain": 0.1,
			"stain_shift": Vector2(0.13, 0.47), "light_pos": Vector2(0.4, 0.3)}
	var draw_front := func(ci: CanvasItem) -> void:
		var red := INK_PRINT_RED
		ci.draw_rect(Rect2(14, 14, size.x - 28, size.y - 28), red, false, 2.0)
		ci.draw_rect(Rect2(19, 19, size.x - 38, size.y - 38), Color(red, 0.6), false, 1.0)
		var coop := InkWriter.new(_font(PaperFonts.PRINT, 700), 12, red)
		coop.align = HORIZONTAL_ALIGNMENT_CENTER
		coop.write_line(ci, TranslationServer.translate(&"PAPER_BUS_COOP"), Vector2(size.x * 0.5, 46))
		var head := InkWriter.new(_font(PaperFonts.PRINT, 700), 30, red)
		head.align = HORIZONTAL_ALIGNMENT_CENTER
		head.write_line(ci, heading, Vector2(size.x * 0.5, 92))
		var serial := InkWriter.new(_font(PaperFonts.TYPEWRITER), 17, Color(0.15, 0.12, 0.35))
		serial.align = HORIZONTAL_ALIGNMENT_CENTER
		serial.write_line(ci, "Nº 004751", Vector2(size.x * 0.5, 118))
		var label := InkWriter.new(_font(PaperFonts.PRINT), 17, red)
		var hand := _writer(PaperFonts.BALLPOINT, 25, INK_BALLPOINT, true)
		var y := 170.0
		for f: PackedStringArray in fields:
			label.write_line(ci, f[0] + ":", Vector2(34, y))
			var lx := 40.0 + label.line_width(f[0] + ":")
			var x := lx
			while x < size.x - 36:
				ci.draw_circle(Vector2(x, y + 3), 0.9, Color(red, 0.7))
				x += 5.0
			hand.size = 25 if lx + hand.line_width(f[1]) < size.x - 30 else 20
			hand.write_line(ci, f[1], Vector2(lx + 6, y - 3))
			y += 52.0
		var foot := InkWriter.new(_font(PaperFonts.PRINT), 12, Color(red, 0.9))
		foot.align = HORIZONTAL_ALIGNMENT_CENTER
		foot.write_line(ci, TranslationServer.translate(&"PAPER_TICKET_COPY"), Vector2(size.x * 0.5, size.y - 34))
		round_stamp(ci, Vector2(size.x - 92, size.y - 104), 46, TranslationServer.translate(&"PAPER_BUS_COOP"), INK_STAMP, 0.3)
	var front := PaperSheet.new(size, look, draw_front)
	var items: Array = [front]
	var back_text := ""
	for cap in parts["captions"]:
		back_text = quoted(cap)
		if not back_text.is_empty():
			break
	if back_text.is_empty():
		front.place(CENTER, -2.0)
		return _result(items, parts["captions"])
	front.place(CENTER + Vector2(-140, 0), -3.0)
	var bsize := Vector2(330, 200)
	var blook := look.duplicate()
	blook.merge({"perforate": Vector4(0, 0, 1, 0), "folds": Vector2(1, 0), "stain_shift": Vector2(0.6, 0.1),
			"ink_grain": 0.75, "foxing": 0.45}, true)
	var draw_back := func(ci: CanvasItem) -> void:
		var pencil := _writer(PaperFonts.PENCIL, 38, INK_PENCIL, true)
		pencil.jitter = 1.8
		pencil.slope = -0.05
		pencil.line_height = 46.0
		var h := pencil.measure(back_text, bsize.x - 60)
		pencil.write(ci, back_text, Vector2(32, (bsize.y - h) * 0.5 - 8), bsize.x - 60)
	var back := PaperSheet.new(bsize, blook, draw_back)
	back.place(CENTER + Vector2(200, 90), 5.0)
	items.append(back)
	return _result(items, parts["captions"])


## Lá bùa giấy vàng: mặt trước nét son đỏ, mặt sau chữ thầy cúng bút lông (nét son thấm ngược qua).
static func _talisman(text: String) -> Dictionary:
	var parts := split_narration(text)
	var body: String = parts["body"]
	var size := Vector2(270, 640)
	var look := {"paper_color": Color(0.84, 0.70, 0.38), "age_color": Color(0.55, 0.40, 0.2), "age": 0.5,
			"age_width": 50.0, "grain": 0.75, "foxing": 0.45, "tear": 3.0, "crumple": 0.45, "stain": 0.08,
			"stain_shift": Vector2(0.42, 0.18), "ink_grain": 0.45, "light_pos": Vector2(0.5, 0.25)}
	var front_look := look.duplicate()
	front_look.merge({"stain_shift": Vector2(0.1, 0.8), "crumple": 0.55}, true)
	var draw_front := func(ci: CanvasItem) -> void:
		Pictograms.talisman_glyph(ci, Rect2(30, 30, size.x - 60, size.y - 60), INK_CINNABAR, 4242)
	var front := PaperSheet.new(size, front_look, draw_front)
	front.place(CENTER + Vector2(-170, -10), -7.0)
	front.modulate = Color(0.78, 0.74, 0.7)
	var draw_back := func(ci: CanvasItem) -> void:
		ci.draw_set_transform_matrix(Transform2D(0.0, Vector2(-1, 1), 0.0, Vector2(size.x, 0)))
		Pictograms.talisman_glyph(ci, Rect2(30, 30, size.x - 60, size.y - 60), Color(INK_CINNABAR, 0.16), 4242)
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)
		var brush := _writer(PaperFonts.PEN, 27, INK_BRUSH, true, 700)
		brush.align = HORIZONTAL_ALIGNMENT_CENTER
		brush.line_height = 40.0
		brush.paragraph_gap = 0.5
		var h := brush.measure(body, size.x - 50)
		brush.write(ci, body, Vector2(25, (size.y - h) * 0.5 - 20), size.x - 50)
	var back := PaperSheet.new(size, look, draw_back)
	back.place(CENTER + Vector2(120, 0), 2.5)
	return _result([front, back], parts["captions"])


## Giấy tờ in: quốc hiệu, tên giấy, các dòng "nhãn: giá trị" (giá trị đánh máy).
## [param photo]: có ô ảnh và dấu (bằng lái, bọc túi nilông). [param pinned]: ghim trên taplô, ngấm nước.
static func _form(text: String, photo: bool, pinned: bool) -> Dictionary:
	var parts := split_narration(text)
	var lines: PackedStringArray = String(parts["body"]).split("\n", false)
	var heading := lines[0] if not lines.is_empty() else ""
	var fields: Array = []
	for i in range(1, lines.size()):
		var f := field(lines[i])
		fields.append(f if not f.is_empty() else PackedStringArray(["", lines[i]]))
	var size := Vector2(580, 360) if photo else Vector2(500, 620)
	var look := PaperSheet.LOOK_FORM.duplicate()
	if photo:
		look.merge({"paper_color": Color(0.90, 0.80, 0.80), "sheen": 0.55, "age": 0.35, "corner_round": 10.0,
				"tear": 0.0, "stain_shift": Vector2(0.55, 0.35)}, true)
	if pinned:
		look.merge({"stain": 0.62, "stain_bias_y": 0.5, "ink_wash": 0.85, "age": 0.8, "foxing": 0.6,
				"crumple": 0.5, "tear": 4.0, "stain_shift": Vector2(0.2, 0.05), "folds": Vector2(1, 0)}, true)
	var head_size := 13 if photo else 15
	var draw_ink := func(ci: CanvasItem) -> void:
		var cx := size.x * 0.5
		var state := InkWriter.new(_font(PaperFonts.PRINT, 700), head_size, INK_PRINT)
		state.align = HORIZONTAL_ALIGNMENT_CENTER
		state.write_line(ci, TranslationServer.translate(&"PAPER_STATE_HEADER"), Vector2(cx, 40))
		var mt := TranslationServer.translate(&"PAPER_STATE_MOTTO")
		var my := 60.0 if photo else 64.0
		state.write_line(ci, mt, Vector2(cx, my))
		var mw := state.line_width(mt)
		ci.draw_line(Vector2(cx - mw * 0.5, my + 6), Vector2(cx + mw * 0.5, my + 6), INK_PRINT, 1.0)
		var head := InkWriter.new(_font(PaperFonts.PRINT, 700), 26 if photo else 24, INK_PRINT_RED if photo else INK_PRINT)
		head.align = HORIZONTAL_ALIGNMENT_CENTER
		var head_y := 104.0 if photo else 128.0
		if head.line_width(heading) > size.x - 60:
			head.size = 20
		head.write_line(ci, heading, Vector2(cx, head_y))
		var x0 := 200.0 if photo else 50.0
		var y := head_y + (54.0 if photo else 70.0)
		var label := InkWriter.new(_font(PaperFonts.PRINT), 18, INK_PRINT)
		var typed := InkWriter.new(_font(PaperFonts.TYPEWRITER), 21, Color(0.08, 0.07, 0.12, 0.92))
		typed.jitter = 0.25
		typed.pressure = 0.6
		var n := 0
		for f: PackedStringArray in fields:
			n += 1
			var lx := x0
			if not f[0].is_empty():
				label.write_line(ci, f[0] + ":", Vector2(x0, y))
				lx = x0 + label.line_width(f[0] + ":") + 12.0
			var value := f[1]
			var paren := value.find("(")
			var close := value.find(")", paren) if paren >= 0 else -1
			if close > paren:
				# "(nhòe nước) . . . 8 5": chỗ trong ngoặc là chữ đã mất, vẽ vệt nhòe thay chữ.
				var lost_w := maxf(70.0, typed.line_width(value.substr(paren, close - paren + 1)) * 0.8)
				smudge(ci, Rect2(lx, y - 22, lost_w, 28), Color(0.15, 0.13, 0.3, 1.0), n * 17)
				var rest := value.substr(close + 1).strip_edges()
				if not rest.is_empty():
					typed.write_line(ci, rest, Vector2(lx + lost_w + 8.0, y))
			else:
				typed.write_line(ci, value, Vector2(lx, y))
			y += 44.0 if photo else 52.0
		if photo:
			var ph := Rect2(36, 120, 130, 170)
			ci.draw_rect(ph, Color(0.62, 0.6, 0.58, 0.55))
			ci.draw_circle(ph.position + Vector2(65, 66), 30, Color(0.25, 0.22, 0.2, 0.55))
			var shoulders := PackedVector2Array([ph.position + Vector2(14, 170), ph.position + Vector2(24, 116),
					ph.position + Vector2(65, 100), ph.position + Vector2(106, 116), ph.position + Vector2(116, 170)])
			ci.draw_colored_polygon(Pictograms.smooth(shoulders, 6), Color(0.2, 0.18, 0.17, 0.6))
			ci.draw_rect(ph, INK_PRINT, false, 1.0)
			round_stamp(ci, ph.end - Vector2(6, 22), 46, TranslationServer.translate(&"PAPER_TRANSPORT_STAMP"), INK_STAMP, -0.5)
		else:
			round_stamp(ci, Vector2(size.x - 120, size.y - 120), 58, TranslationServer.translate(&"PAPER_TRANSPORT_STAMP"),
					Color(INK_STAMP, 0.65), 0.2)
		if pinned:
			rust_ring(ci, Vector2(size.x * 0.5, 22), 26.0)
	var draw_over := func(ci: CanvasItem) -> void:
		if pinned:
			# Đinh ghim gỉ cắm qua mép trên.
			var p := Vector2(size.x * 0.5, 22)
			ci.draw_circle(p + Vector2(2, 3), 9, Color(0, 0, 0, 0.35))
			ci.draw_circle(p, 8, Color(0.36, 0.22, 0.12))
			ci.draw_circle(p - Vector2(2, 2), 4, Color(0.62, 0.42, 0.25))
		if photo:
			# Túi nilông bọc ngoài: mép túi trong mờ và một nếp nhăn sáng.
			ci.draw_rect(Rect2(Vector2(-12, -12), size + Vector2(24, 24)), Color(1, 1, 1, 0.07))
			ci.draw_rect(Rect2(Vector2(-12, -12), size + Vector2(24, 24)), Color(1, 1, 1, 0.22), false, 2.0)
			ci.draw_line(Vector2(-6, size.y * 0.7), Vector2(size.x * 0.3, size.y + 8), Color(1, 1, 1, 0.16), 3.0)
	var sheet := PaperSheet.new(size, look, draw_ink, draw_over)
	sheet.place(CENTER, 1.6 if photo else -1.2)
	return _result([sheet], parts["captions"])


## Sổ phụ xe: giấy kẻ dòng có cột, chữ bút bi; phần dưới ngấm nước, chỉ còn một câu đọc được.
static func _ledger(text: String) -> Dictionary:
	var parts := split_narration(text)
	var lines: PackedStringArray = String(parts["body"]).split("\n")
	var survive := ""
	for cap in parts["captions"]:
		survive = quoted(cap)
	var size := Vector2(540, 660)
	var look := {"paper_color": Color(0.88, 0.86, 0.78), "age": 0.6, "grain": 0.5, "foxing": 0.3, "tear": 1.5,
			"stain": 0.42, "stain_bias_y": 1.1, "ink_wash": 0.35, "stain_shift": Vector2(0.66, 0.4),
			"light_pos": Vector2(0.4, 0.2)}
	var draw_ink := func(ci: CanvasItem) -> void:
		_rules(ci, size, 92.0, 36.0, RULE_BLUE)
		ci.draw_line(Vector2(60, 50), Vector2(60, size.y), RULE_RED, 1.2)
		ci.draw_line(Vector2(size.x - 90, 50), Vector2(size.x - 90, size.y), RULE_RED, 1.2)
		ci.draw_line(Vector2(0, 56), Vector2(size.x, 56), Color(RULE_RED, 0.8), 1.6)
		var head := lines[0] if not lines.is_empty() else ""
		var hw := _writer(PaperFonts.BALLPOINT, 27, INK_BALLPOINT, true)
		hw.write_line(ci, head, Vector2(72, 44))
		ci.draw_line(Vector2(72, 50), Vector2(72 + hw.line_width(head), 48), Color(INK_BALLPOINT, 0.8), 1.4)
		var w := _writer(PaperFonts.BALLPOINT, 24, INK_BALLPOINT, true)
		w.line_height = 36.0
		var rest := "\n".join(lines.slice(1)).strip_edges()
		var y := w.write(ci, rest, Vector2(72, 92.0 + 36.0 - 24.0 - 5.0), size.x - 180.0)
		# Mấy dòng nhòe nước không đọc được, rồi câu còn sót lại.
		var rng := RandomNumberGenerator.new()
		rng.seed = 77
		y += 36.0
		for i in 3:
			var x := 72.0
			while x < size.x - 120:
				var len := rng.randf_range(26, 70)
				Pictograms.stroke(ci, PackedVector2Array([Vector2(x, y - 6), Vector2(x + len * 0.5, y - 9 + rng.randf() * 4),
						Vector2(x + len, y - 6)]), rng.randf_range(7, 11), Color(INK_BALLPOINT, 0.2), true, 0.5, i * 31 + int(x))
				x += len + rng.randf_range(10, 18)
			y += 36.0
		if not survive.is_empty():
			w.write(ci, survive, Vector2(150, y - 24.0 - 5.0), size.x - 220.0)
	var sheet := PaperSheet.new(size, look, draw_ink)
	sheet.place(CENTER, -1.0)
	return _result([sheet], parts["captions"])


## Hình đôi guốc (nhìn từ trên) có quai mang hoa văn, dùng cho sách mẫu và câu đố cắt guốc.
## [param pair] = false thì chỉ vẽ một chiếc.
static func clog_outline(ci: CanvasItem, c: Vector2, s: float, color: Color, motif: int, width := 2.0,
		fill := Color(0, 0, 0, 0), pair := true) -> void:
	var centers := [c] if not pair else [c + Vector2(-27, -4) * s, c + Vector2(27, 4) * s]
	for k in centers.size():
		var cc: Vector2 = centers[k]
		var flip := -1.0 if (pair and k == 0) else 1.0
		var curve := clog_points(cc, s, flip)
		if fill.a > 0.0:
			ci.draw_colored_polygon(curve, fill)
		var closed := curve.duplicate()
		closed.append(curve[0])
		ci.draw_polyline(closed, color, width, true)
		# Quai guốc: dải cong vắt ngang mũi guốc, hai đầu đóng đinh.
		var band := PackedVector2Array()
		for i in 9:
			var t := float(i) / 8.0
			band.append(cc + Vector2(lerpf(-29, 29, t), -34 - sin(t * PI) * 5.0) * s)
		for i in 9:
			var t := 1.0 - float(i) / 8.0
			band.append(cc + Vector2(lerpf(-29, 29, t), -14 - sin(t * PI) * 5.0) * s)
		ci.draw_colored_polygon(band, Color(color, 0.14 if fill.a <= 0.0 else 0.0))
		var band_line := band.duplicate()
		band_line.append(band[0])
		ci.draw_polyline(band_line, color, width * 0.8, true)
		for x: float in [-25.0, 25.0]:
			ci.draw_circle(cc + Vector2(x, -24) * s, maxf(1.2, 2.0 * s), color)
		if motif >= 0:
			Pictograms.draw(ci, motif, cc + Vector2(0, -26) * s, s * 0.17, color, maxf(1.0, width * 0.6))


## Đường viền đế guốc quanh tâm [param c], cỡ [param s] (1 = dài 126px);
## [param flip] = -1 cho chiếc trái.
static func clog_points(c: Vector2, s: float, flip := 1.0) -> PackedVector2Array:
	var sole := [Vector2(0, -62), Vector2(19, -56), Vector2(25, -36), Vector2(23, -8), Vector2(16, 18),
			Vector2(19, 44), Vector2(14, 60), Vector2(0, 64), Vector2(-14, 60), Vector2(-19, 44),
			Vector2(-17, 18), Vector2(-23, -8), Vector2(-25, -36), Vector2(-19, -56)]
	var pts := PackedVector2Array()
	for p: Vector2 in sole:
		pts.append(c + Vector2(p.x * flip + 3.0 * flip * (p.y + 64) / 128.0, p.y) * s)
	return Pictograms.smooth(pts, 6, true)


static func _pattern_book(text: String) -> Dictionary:
	var parts := split_narration(text)
	var lines: PackedStringArray = String(parts["body"]).split("\n")
	var subtitle := ""
	for cap in parts["captions"]:
		subtitle = cap
	var size := Vector2(540, 650)
	var look := {"paper_color": Color(0.86, 0.80, 0.66), "age": 0.7, "grain": 0.9, "foxing": 0.45, "tear": 2.5,
			"stain": 0.08, "stain_shift": Vector2(0.27, 0.73), "ink_grain": 0.3, "crumple": 0.25}
	var motifs := [Pictograms.Kind.FISH, Pictograms.Kind.PLUM, Pictograms.Kind.THO]
	var draw_ink := func(ci: CanvasItem) -> void:
		# Gáy sách khâu chỉ bên trái.
		for i in 12:
			var sy := 40.0 + i * 50.0
			ci.draw_line(Vector2(18, sy), Vector2(18, sy + 26), Color(0.3, 0.2, 0.15, 0.6), 2.0)
			ci.draw_circle(Vector2(18, sy), 2.2, Color(0.2, 0.12, 0.1, 0.6))
		var w := _writer(PaperFonts.BALLPOINT, 24, INK_PURPLE, true)
		w.line_height = 33.0
		var y := 36.0
		var motif := 0
		var first := true
		for line in lines:
			var t := line.strip_edges()
			if t.is_empty():
				y += 14.0
				continue
			if first and t == t.to_upper():
				var head := _writer(PaperFonts.BALLPOINT, 31, INK_PURPLE, true)
				head.align = HORIZONTAL_ALIGNMENT_CENTER
				y = head.write(ci, t, Vector2(40, y), size.x - 80.0) + 2.0
				if not subtitle.is_empty():
					var sub := _writer(PaperFonts.BALLPOINT, 20, INK_PURPLE, true)
					sub.align = HORIZONTAL_ALIGNMENT_CENTER
					y = sub.write(ci, "(" + subtitle + ")", Vector2(40, y), size.x - 80.0) + 10.0
			elif t.begins_with("-") and motif < 3:
				var row_y := y
				y = w.write(ci, t, Vector2(60, y + 18.0), size.x - 210.0)
				var k := 0.42 + motif * 0.1
				clog_outline(ci, Vector2(size.x - 92, row_y + 22 + 64.0 * k), k, Color(INK_PURPLE, 0.9), motifs[motif], 1.6)
				y = maxf(y, row_y + 128.0 * k + 34.0)
				motif += 1
			else:
				y = w.write(ci, t, Vector2(60, y), size.x - 110.0) + 6.0
			first = false
	var sheet := PaperSheet.new(size, look, draw_ink)
	sheet.place(CENTER, 1.2)
	# Dòng phụ đề "(hàng mã bà Năm, chợ Đoài)" đã viết lên giấy, không cần chú thích nữa.
	return _result([sheet], PackedStringArray())


## Xấp giấy điều, giấy vàng và chiếc kéo nhỏ kẹp trong sách mẫu.
static func _paper_stack(text: String) -> Dictionary:
	var parts := split_narration(text)
	var items: Array = []
	var colors := [Color(0.72, 0.12, 0.10), Color(0.90, 0.72, 0.22), Color(0.78, 0.16, 0.12), Color(0.93, 0.78, 0.30)]
	for i in colors.size():
		var look := {"paper_color": colors[i], "age_color": Color(0.5, 0.3, 0.15), "age": 0.4, "grain": 0.9,
				"foxing": 0.15, "tear": 1.2, "shadow_alpha": 0.45, "stain_shift": Vector2(i * 0.21, i * 0.37),
				"light_pos": Vector2(0.3, 0.2)}
		var gold: bool = colors[i].g > 0.5
		var draw_ink := func(ci: CanvasItem) -> void:
			if gold:
				# Giấy vàng có ô in kim nhũ.
				for gx in 6:
					for gy in 5:
						ci.draw_rect(Rect2(30 + gx * 56, 24 + gy * 54, 34, 34), Color(0.75, 0.52, 0.12, 0.45), false, 1.5)
		var sheet := PaperSheet.new(Vector2(380, 300), look, draw_ink)
		sheet.place(CENTER + Vector2(-60 + i * 30, -30 + i * 14), -8.0 + i * 5.0)
		items.append(sheet)
	var scissors := Control.new()
	scissors.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scissors.size = Vector2(260, 140)
	scissors.position = CENTER + Vector2(30, 40)
	scissors.rotation_degrees = -24.0
	scissors.draw.connect(func() -> void:
		var steel := Color(0.62, 0.64, 0.66)
		var dark := Color(0.12, 0.1, 0.09)
		scissors.draw_colored_polygon(PackedVector2Array([Vector2(90, 70), Vector2(252, 58), Vector2(96, 84)]), Color(0, 0, 0, 0.35))
		scissors.draw_colored_polygon(PackedVector2Array([Vector2(86, 56), Vector2(244, 42), Vector2(92, 70)]), steel)
		scissors.draw_colored_polygon(PackedVector2Array([Vector2(86, 72), Vector2(240, 80), Vector2(92, 60)]), steel.darkened(0.25))
		scissors.draw_circle(Vector2(92, 64), 5, dark)
		for p: Vector2 in [Vector2(46, 40), Vector2(46, 92)]:
			scissors.draw_arc(p, 24, 0, TAU, 32, dark, 9.0, true)
			scissors.draw_arc(p, 24, 3.6, 4.6, 12, Color(0.4, 0.36, 0.34), 3.0, true)
		scissors.draw_line(Vector2(64, 50), Vector2(90, 60), dark, 9.0)
		scissors.draw_line(Vector2(64, 80), Vector2(90, 68), dark, 9.0))
	items.append(scissors)
	var captions: PackedStringArray = parts["captions"]
	if captions.is_empty():
		captions.append(String(parts["body"]))
	return _result(items, captions)


## Vở ô li của Hùng: lưới ô li tím, mực tím, bốn hình vẽ rải khắp trang, ghi chú bên lề.
static func _school_notebook(text: String) -> Dictionary:
	var captions := PackedStringArray()
	var drawings: Array[String] = []
	var margin_note := ""
	for para in text.split("\n"):
		var t := para.strip_edges()
		if t.is_empty():
			continue
		if t.begins_with("-"):
			drawings.append(t)
		elif not drawings.is_empty() and not quoted(t).is_empty():
			margin_note = quoted(t)
		else:
			captions.append(t)
	var size := Vector2(560, 660)
	var look := {"paper_color": Color(0.93, 0.92, 0.87), "age": 0.4, "grain": 0.35, "foxing": 0.15, "tear": 1.0,
			"stain": 0.2, "stain_bias_y": -0.4, "stain_shift": Vector2(0.81, 0.33), "light_pos": Vector2(0.45, 0.3)}
	var spots := [Vector2(400, 130), Vector2(200, 290), Vector2(410, 390), Vector2(200, 120)]
	var draw_ink := func(ci: CanvasItem) -> void:
		# Vở 4 ô li: ô lớn 32px, mỗi ô chia 4 dòng li.
		var y := 40.0
		var row := 0
		while y < size.y:
			ci.draw_line(Vector2(0, y), Vector2(size.x, y), Color(GRID_PURPLE, 0.55 if row % 4 == 0 else 0.25), 1.0)
			y += 8.0
			row += 1
		var x := 86.0
		while x < size.x:
			ci.draw_line(Vector2(x, 0), Vector2(x, size.y), Color(GRID_PURPLE, 0.45), 1.0)
			x += 32.0
		ci.draw_line(Vector2(80, 0), Vector2(80, size.y), RULE_RED, 1.6)
		for i in mini(drawings.size(), 4):
			Pictograms.draw(ci, STOP_KINDS[i], spots[i], 1.15, Color(INK_PURPLE, 0.92), 2.6)
			var note := quoted(drawings[i])
			if not note.is_empty():
				var nw := _writer(PaperFonts.SCHOOL, 18, INK_PURPLE, true)
				nw.align = HORIZONTAL_ALIGNMENT_CENTER
				nw.line_height = 26.0
				nw.write(ci, note, spots[i] + Vector2(-120, 52), 240.0)
		if not margin_note.is_empty():
			var mw := _writer(PaperFonts.SCHOOL, 19, INK_PURPLE, true)
			mw.line_height = 32.0
			mw.slope = -0.025
			ci.draw_line(Vector2(100, size.y - 158), Vector2(size.x - 40, size.y - 166), Color(INK_PURPLE, 0.5), 1.4)
			mw.write(ci, margin_note, Vector2(108, size.y - 148), size.x - 150.0)
	var sheet := PaperSheet.new(size, look, draw_ink)
	sheet.place(CENTER, -1.8)
	return _result([sheet], captions)


## Mặt trong vành nón lá: lá cọ phơi, vòng nan tre, dòng mực tím viết ngược như soi gương.
static func _hat(text: String) -> Dictionary:
	var lines: PackedStringArray = text.strip_edges().split("\n", false)
	var mirrored_text := lines[lines.size() - 1].strip_edges() if not lines.is_empty() else ""
	var captions := PackedStringArray()
	for i in lines.size() - 1:
		captions.append(lines[i].strip_edges())
	var hat := Control.new()
	hat.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hat.size = Vector2(600, 600)
	hat.position = CENTER - hat.size * 0.5
	hat.draw.connect(func() -> void:
		var c := Vector2(300, 300)
		var r := 286.0
		hat.draw_circle(c + Vector2(10, 18), r + 4, Color(0, 0, 0, 0.5))
		# Lá nón xếp tỏa tia từ đỉnh, mỗi lá ngả màu hơi khác.
		var rng := RandomNumberGenerator.new()
		rng.seed = 5
		var leaves := 120
		for i in leaves:
			var a0 := TAU * i / leaves
			var a1 := TAU * (i + 1) / leaves
			var shade := rng.randf_range(0.93, 1.0)
			var col := Color(0.86 * shade, 0.82 * shade, 0.64 * shade * rng.randf_range(0.96, 1.04))
			hat.draw_colored_polygon(PackedVector2Array([c, c + Vector2(cos(a0), sin(a0)) * r,
					c + Vector2(cos(a1), sin(a1)) * r]), col)
		# Gân lá: các tia mảnh sáng tối xen kẽ.
		for i in 360:
			var a := TAU * i / 360.0 + rng.randf_range(-0.004, 0.004)
			var light := i % 3 == 0
			hat.draw_line(c + Vector2(cos(a), sin(a)) * 18.0, c + Vector2(cos(a), sin(a)) * r,
					Color(1, 1, 0.95, 0.10) if light else Color(0.35, 0.3, 0.15, 0.10), 1.0, true)
		# Lòng nón sâu dần vào đỉnh: tối dần về tâm.
		for k in 30:
			var t := float(k) / 30.0
			hat.draw_circle(c, r * (1.0 - t * 0.97), Color(0.10, 0.07, 0.03, 0.03 + t * 0.012))
		# Vết ố nước mưa loang trên lá.
		for i in 5:
			var p := c + Vector2(rng.randf_range(-170, 170), rng.randf_range(-170, 170))
			for k in 6:
				hat.draw_circle(p, rng.randf_range(20, 46) * (1.0 - k * 0.12), Color(0.45, 0.33, 0.12, 0.035))
		# Vòng nan tre lộ qua lớp lá và mũi chỉ khâu.
		for k in range(2, 17):
			var rr := r * k / 16.0
			hat.draw_arc(c, rr, 0, TAU, 128, Color(0.30, 0.24, 0.10, 0.16), 3.0, true)
			var stitches := int(rr / 7.0)
			for j in stitches:
				var a := TAU * (j + 0.5 * (k % 2)) / stitches
				var d := Vector2(cos(a), sin(a))
				hat.draw_line(c + d * (rr - 3.5), c + d * (rr + 3.5), Color(0.95, 0.93, 0.86, 0.5), 1.2, true)
		hat.draw_arc(c, r - 4, 0, TAU, 160, Color(0.40, 0.30, 0.14), 9.0, true)
		hat.draw_arc(c, r - 9, 0, TAU, 160, Color(0.22, 0.16, 0.08, 0.6), 2.0, true)
		hat.draw_arc(c, r, 0, TAU, 160, Color(0.12, 0.09, 0.05), 2.0, true)
		# Dòng mực tím viết dọc vành (phía trên), chữ lật như soi gương.
		arc_text(hat, mirrored_text, c, r * 0.83, -PI * 0.5, _font(PaperFonts.BALLPOINT), 38,
				Color(0.38, 0.14, 0.52, 0.88), true, true))
	return _result([hat], captions)



static func stop_name(option: String) -> String:
	var p := option.find("(")
	var name := option.substr(0, p).strip_edges() if p > 0 else option.strip_edges()
	var colon := name.find(":")
	return name.substr(0, colon).strip_edges() if colon > 0 else name


static func _plaques(text: String) -> Dictionary:
	var captions := PackedStringArray()
	var names: Array[String] = []
	for para in text.split("\n"):
		var t := para.strip_edges()
		if t.begins_with("-"):
			names.append(stop_name(t.trim_prefix("-").strip_edges()))
		elif not t.is_empty():
			captions.append(t)
	var items: Array = []
	var spots := [Vector2(-250, -90), Vector2(80, -140), Vector2(-110, 110), Vector2(250, 70)]
	var angles := [-14.0, 9.0, 4.0, -21.0]
	for i in mini(names.size(), 4):
		var plaque := make_plaque(names[i], STOP_KINDS[i], i + 3)
		plaque.scale = Vector2.ONE * 1.25
		plaque.place(CENTER + spots[i], angles[i])
		items.append(plaque)
	return _result(items, captions)



## Một tấm biển bến tôn sơn (dùng cho trang biển rơi và câu đố bảng lộ trình).
## [param hung] = đang treo: vẽ thêm khoen móc qua hai lỗ.
static func make_plaque(name: String, kind: int, seed_value: int, hung := false) -> PaperSheet:
	var size := Vector2(200, 128)
	var look := {"paper_color": Color(0.88, 0.85, 0.76), "age_color": Color(0.42, 0.2, 0.08), "age": 0.85,
			"age_width": 26.0, "grain": 0.25, "foxing": 0.9, "tear": 0.6, "corner_round": 9.0,
			"stain": 0.18, "stain_shift": Vector2(seed_value * 0.17, seed_value * 0.29), "ink_grain": 0.35,
			"sheen": 0.15, "shadow_alpha": 0.7, "shadow_offset": Vector2(4, 8), "shadow_blur": 12.0}
	var draw_ink := func(ci: CanvasItem) -> void:
		ci.draw_rect(Rect2(8, 8, size.x - 16, size.y - 16), Color(0.66, 0.12, 0.1, 0.95), false, 5.0)
		Pictograms.draw(ci, kind, Vector2(56, 66), 0.6, Color(0.55, 0.1, 0.08), 3.2, Color(0.55, 0.1, 0.08, 0.18))
		var w := InkWriter.new(_font(PaperFonts.PRINT, 700), 21, Color(0.14, 0.12, 0.1))
		w.line_height = 24.0
		w.align = HORIZONTAL_ALIGNMENT_CENTER
		var h := w.measure(name, 96.0)
		w.write(ci, name, Vector2(96, 70 - h * 0.5 - 4), 96.0)
	var draw_over := func(ci: CanvasItem) -> void:
		for x: float in [24.0, size.x - 24.0]:
			ci.draw_circle(Vector2(x, 22), 5.0, Color(0.06, 0.05, 0.04))
			ci.draw_arc(Vector2(x, 22), 5.5, 0, TAU, 16, Color(0.5, 0.42, 0.32), 1.2, true)
			if hung:
				ci.draw_arc(Vector2(x, 14), 9.0, PI * 0.1, PI * 0.9, 12, Color(0.55, 0.5, 0.45), 3.0, true)
				ci.draw_line(Vector2(x, 5), Vector2(x, -18), Color(0.55, 0.5, 0.45), 3.0)
	return PaperSheet.new(size, look, draw_ink, draw_over)


## Một cuống vé đã soát: ba hàng lỗ in sẵn, lỗ đã bấm, số ghế viết tay ở góc, dấu đóng nếu có.
static func make_ticket_stub(rows: Array, seat: String, stamp: String, seed_value: int) -> PaperSheet:
	var size := Vector2(220, 300)
	var look := {"paper_color": Color(0.86, 0.88, 0.80), "age": 0.6, "grain": 0.5, "foxing": 0.5, "tear": 0.6,
			"perforate": Vector4(0, 1, 0, 0), "stain_shift": Vector2(seed_value * 0.13, seed_value * 0.31),
			"stain": 0.08, "light_pos": Vector2(0.4, 0.3), "shadow_alpha": 0.5}
	var draw_ink := func(ci: CanvasItem) -> void:
		draw_punch_layout(ci, size, -1)
		if not seat.is_empty():
			var w := _writer(PaperFonts.BALLPOINT, 34, INK_BALLPOINT, true)
			w.write_line(ci, seat, Vector2(size.x - 64, 70))
		if not stamp.is_empty():
			box_stamp(ci, Vector2(size.x * 0.5, size.y - 40), stamp, 15, INK_STAMP, -0.12)
	var draw_over := func(ci: CanvasItem) -> void:
		for r in rows.size():
			var holes: Array = rows[r]
			for i in holes.size():
				if holes[i]:
					draw_hole(ci, punch_hole_pos(size, r, i, holes.size()))
	return PaperSheet.new(size, look, draw_ink, draw_over)


## Bố cục in sẵn của vé bấm lỗ (dùng chung cho cuống vé và câu đố bấm vé):
## tên vé, ba hàng lỗ (ghế 1-9, người lớn / trẻ em, bến lên).
## [param highlight_row] >= 0 thì tô nhạt hàng đó (con trỏ bàn phím).
static func draw_punch_layout(ci: CanvasItem, size: Vector2, highlight_row: int) -> void:
	var red := INK_PRINT_RED
	ci.draw_rect(Rect2(10, 10, size.x - 20, size.y - 20), Color(red, 0.85), false, 1.6)
	var head := InkWriter.new(_font(PaperFonts.PRINT, 700), int(size.x / 14.0), red)
	head.align = HORIZONTAL_ALIGNMENT_CENTER
	head.write_line(ci, TranslationServer.translate(&"DOC_BUS_TICKET").split("\n")[0], Vector2(size.x * 0.5, size.y * 0.11))
	var label := InkWriter.new(_font(PaperFonts.PRINT), int(size.x / 19.0), red)
	var tag_w := InkWriter.new(_font(PaperFonts.PRINT), int(size.x / 22.0), red)
	tag_w.align = HORIZONTAL_ALIGNMENT_CENTER
	var counts := [9, 2, 5]
	var row_labels := [&"PAPER_PUNCH_SEAT", &"PAPER_PUNCH_FARE", &"PAPER_PUNCH_STOP"]
	var r_hole := hole_radius(size)
	for r in 3:
		var first := punch_hole_pos(size, r, 0, counts[r])
		if highlight_row == r:
			ci.draw_rect(Rect2(14, first.y - r_hole * 4.2, size.x - 28, r_hole * 7.6), Color(0.95, 0.8, 0.3, 0.25))
		label.write_line(ci, TranslationServer.translate(row_labels[r]), Vector2(18, first.y - r_hole * 2.2))
		for i in counts[r]:
			var p := punch_hole_pos(size, r, i, counts[r])
			ci.draw_arc(p, r_hole, 0, TAU, 20, Color(red, 0.9), 1.3, true)
			var tag := ""
			if r == 0:
				tag = str(i + 1)
			elif r == 1:
				tag = TranslationServer.translate(&"PAPER_PUNCH_ADULT" if i == 0 else &"PAPER_PUNCH_CHILD")
			if not tag.is_empty():
				tag_w.write_line(ci, tag, p + Vector2(0, r_hole * 3.0))


static func hole_radius(size: Vector2) -> float:
	return size.x * 0.03


## Tâm lỗ thứ [param i] (trong [param count] lỗ) của hàng [param row] trên vé cỡ [param size].
static func punch_hole_pos(size: Vector2, row: int, i: int, count: int) -> Vector2:
	var y := size.y * (0.33 + row * 0.22)
	var left := size.x * 0.11
	var right := size.x * 0.89
	if count == 2:
		left = size.x * 0.28
		right = size.x * 0.72
	return Vector2(left + (right - left) * (float(i) / maxf(count - 1, 1)), y)


## Lỗ bấm xuyên giấy: thấy nền tối phía dưới, mép giấy hơi xơ.
static func draw_hole(ci: CanvasItem, p: Vector2, r := 6.4) -> void:
	ci.draw_circle(p, r, Color(0.04, 0.03, 0.03))
	ci.draw_circle(p + Vector2(r * 0.2, r * 0.25), r * 0.7, Color(0.0, 0.0, 0.0))
	ci.draw_arc(p, r, 0, TAU, 20, Color(0.95, 0.93, 0.85, 0.55), 1.0, true)


## Hàng lỗ dạng chữ "○ ○ ● ○" -> mảng bool; không phải hàng lỗ thì [].
static func parse_holes(line: String) -> Array:
	var t := line.strip_edges()
	if t.is_empty():
		return []
	var out: Array = []
	for ch in t:
		if ch == "●":
			out.append(true)
		elif ch == "○":
			out.append(false)
		elif ch != " ":
			return []
	return out


static func _stubs(text: String) -> Dictionary:
	var paras: PackedStringArray = text.split("\n")
	var captions := PackedStringArray()
	var stubs: Array = []
	var note := ""
	var i := 0
	while i < paras.size():
		var t := paras[i].strip_edges()
		if t.is_empty():
			i += 1
			continue
		if i + 1 < paras.size() and not parse_holes(paras[i + 1]).is_empty():
			var rows: Array = []
			var j := i + 1
			while j < paras.size() and not parse_holes(paras[j]).is_empty():
				rows.append(parse_holes(paras[j]))
				j += 1
			stubs.append({"header": t, "rows": rows})
			i = j
			continue
		if t.ends_with(":") and i + 1 < paras.size() and not quoted(paras[i + 1]).is_empty():
			note = quoted(paras[i + 1])
			captions.append(t.trim_suffix(":"))
			i += 2
			continue
		captions.append(t)
		i += 1
	var items: Array = []
	var count := stubs.size() + (1 if not note.is_empty() else 0)
	var spacing := 260.0
	var x := CENTER.x - spacing * (count - 1) * 0.5
	var n := 0
	# Cụm chữ in hoa dài trong lời tả (VÉ TRẺ EM - NỬA GIÁ) là dấu đóng trên cuống.
	var caps := RegEx.create_from_string("\\p{Lu}[\\p{Lu}\\s\\-]{5,}\\p{Lu}")
	for stub: Dictionary in stubs:
		var header: String = stub["header"]
		var seat := quoted(header)
		var stamp := ""
		var m := caps.search(header)
		if m:
			stamp = m.get_string().strip_edges()
		var sheet := make_ticket_stub(stub["rows"], seat, stamp, n + 2)
		sheet.place(Vector2(x, CENTER.y - 20 + (n % 2) * 16.0), -4.0 + n * 3.5)
		items.append(sheet)
		# Chú thích nhỏ dưới cuống: phần lời tả còn lại (khách lên ở đâu...).
		var rest := header.substr(header.rfind("\"") + 1)
		if not stamp.is_empty():
			rest = rest.replace(stamp, "")
		var kept := PackedStringArray()
		for part in rest.split(",", false):
			var p := part.strip_edges()
			if not p.is_empty() and not p.begins_with("đóng dấu") and not p.begins_with("stamped"):
				kept.append(p)
		if not kept.is_empty():
			items.append(caption_tag(", ".join(kept), Vector2(x, CENTER.y + 168)))
		x += spacing
		n += 1
	if not note.is_empty():
		var bsize := Vector2(240, 300)
		var look := {"paper_color": Color(0.84, 0.86, 0.78), "age": 0.7, "foxing": 0.5, "tear": 0.6,
				"perforate": Vector4(0, 1, 0, 0), "stain_shift": Vector2(0.71, 0.13), "light_pos": Vector2(0.4, 0.3)}
		var draw_ink := func(ci: CanvasItem) -> void:
			var w := _writer(PaperFonts.BALLPOINT, 25, INK_BALLPOINT, true)
			w.line_height = 34.0
			var h := w.measure(note, bsize.x - 40)
			w.write(ci, note, Vector2(22, (bsize.y - h) * 0.5 - 10), bsize.x - 40)
		var back := PaperSheet.new(bsize, look, draw_ink)
		back.place(Vector2(x, CENTER.y - 10), 3.0)
		items.append(back)
	return _result(items, captions)


## Nhãn chú thích nhỏ đặt dưới một vật (chữ giao diện, không phải chữ trên giấy).
static func caption_tag(text: String, center: Vector2) -> Label:
	var tag := Label.new()
	tag.text = text
	tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tag.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tag.size = Vector2(240, 40)
	tag.position = center - Vector2(120, 0)
	tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tag.add_theme_font_size_override(&"font_size", 15)
	tag.add_theme_color_override(&"font_color", Color(0.80, 0.76, 0.68))
	tag.add_theme_color_override(&"font_shadow_color", Color(0, 0, 0, 0.8))
	return tag


## Nhãn dán quy ước chuông: decal nhựa trắng viền đỏ, bong một góc.
static func _sticker(text: String) -> Dictionary:
	var parts := split_narration(text)
	var lines: PackedStringArray = String(parts["body"]).split("\n")
	var size := Vector2(470, 330)
	var look := {"paper_color": Color(0.93, 0.92, 0.88), "age": 0.55, "age_width": 40.0, "grain": 0.2,
			"foxing": 0.35, "tear": 0.0, "corner_round": 14.0, "sheen": 0.35, "stain": 0.15,
			"stain_shift": Vector2(0.5, 0.9), "light_pos": Vector2(0.3, 0.3), "ink_grain": 0.15}
	var draw_ink := func(ci: CanvasItem) -> void:
		ci.draw_rect(Rect2(12, 12, size.x - 24, size.y - 24), INK_PRINT_RED, false, 6.0)
		ci.draw_rect(Rect2(12, 12, size.x - 24, 62), INK_PRINT_RED)
		var head := InkWriter.new(_font(PaperFonts.STAMP, 700), 32, Color(0.97, 0.94, 0.88))
		head.align = HORIZONTAL_ALIGNMENT_CENTER
		head.write_line(ci, lines[0] if not lines.is_empty() else "", Vector2(size.x * 0.5, 56))
		var y := 118.0
		var body := InkWriter.new(_font(PaperFonts.PRINT), 21, INK_PRINT)
		var bold := InkWriter.new(_font(PaperFonts.PRINT, 700), 21, INK_PRINT_RED)
		var plain := InkWriter.new(_font(PaperFonts.PRINT, 700), 19, INK_PRINT)
		plain.align = HORIZONTAL_ALIGNMENT_CENTER
		for i in range(1, lines.size()):
			var t := lines[i].strip_edges()
			if t.is_empty():
				y += 10.0
				continue
			var f := field(t)
			if f.is_empty():
				plain.write_line(ci, t, Vector2(size.x * 0.5, y + 6))
				y += 38.0
				continue
			bold.write_line(ci, f[0] + ":", Vector2(40, y))
			body.write_line(ci, f[1], Vector2(40 + bold.line_width(f[0] + ":") + 10.0, y))
			y += 36.0
	var draw_over := func(ci: CanvasItem) -> void:
		# Góc dưới phải bong lên, lộ mặt keo xám phía sau.
		var corner := size
		ci.draw_colored_polygon(PackedVector2Array([corner - Vector2(54, 0), corner, corner - Vector2(0, 46)]),
				Color(0.05, 0.05, 0.05, 0.92))
		ci.draw_colored_polygon(PackedVector2Array([corner - Vector2(54, 0), corner - Vector2(0, 46), corner - Vector2(40, 40)]),
				Color(0.72, 0.7, 0.66))
		ci.draw_line(corner - Vector2(54, 0), corner - Vector2(0, 46), Color(0.4, 0.38, 0.35), 1.0)
	var sheet := PaperSheet.new(size, look, draw_ink, draw_over)
	sheet.place(CENTER, -2.2)
	return _result([sheet], parts["captions"])


## Lá "Thắp hương hỏi": giấy bản mỏng, chữ nâu khói, khói hương lượn quanh, n nén hương trên đầu.
static func _incense(text: String) -> Dictionary:
	var parts := split_narration(text)
	var body: String = parts["body"]
	var sticks := 1
	var digits := RegEx.create_from_string("\\d+")
	for cap in parts["captions"]:
		var m := digits.search(cap)
		if m:
			sticks = clampi(int(m.get_string()), 1, 3)
	var w := _writer(PaperFonts.PEN, 28, Color(0.22, 0.15, 0.10), true)
	w.align = HORIZONTAL_ALIGNMENT_CENTER
	w.line_height = 40.0
	w.jitter = 0.6
	var size := Vector2(620, maxf(300.0, w.measure(body, 520.0) + 170.0))
	var look := {"paper_color": Color(0.86, 0.82, 0.71), "age_color": Color(0.5, 0.36, 0.2), "age": 0.65,
			"grain": 0.9, "foxing": 0.2, "tear": 3.5, "tear_freq": 1.4, "smoke": 1.0, "stain_shift": Vector2(0.15, 0.55),
			"light_pos": Vector2(0.5, 0.0), "light_falloff": 0.3}
	var draw_ink := func(ci: CanvasItem) -> void:
		var cx := size.x * 0.5
		for i in sticks:
			var sx := cx + (i - (sticks - 1) * 0.5) * 26.0
			ci.draw_line(Vector2(sx, 34), Vector2(sx, 96), Color(0.62, 0.16, 0.1), 4.0)
			ci.draw_line(Vector2(sx, 22), Vector2(sx, 36), Color(0.25, 0.2, 0.18), 3.0)
			ci.draw_circle(Vector2(sx, 21), 3.4, Color(1.0, 0.45, 0.12))
		w.write(ci, body, Vector2(50, 120), size.x - 100.0)
	var sheet := PaperSheet.new(size, look, draw_ink)
	sheet.place(CENTER, -0.8)
	return _result([sheet], PackedStringArray())
