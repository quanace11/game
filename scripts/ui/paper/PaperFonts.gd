## Font cho giấy tờ trong game: chữ viết tay, chữ in, chữ máy chữ, chữ dấu mộc.
##
## Mỗi font tải về từ @fontsource (tools/fetch_ui_fonts.py) bị tách thành ba tệp
## vietnamese / latin / latin-ext. Ở đây ghép lại bằng [member Font.fallbacks] nên
## chữ Việt đủ dấu (ặ ữ ỡ ỷ ỵ...) vẫn hiện đúng một kiểu chữ.
class_name PaperFonts
extends RefCounted

## Bút máy nghiêng, nét thanh đậm: nhật ký, chữ thầy cúng, khói hương.
const PEN := "charm"
## Bút bi người lớn: sổ phụ xe, chú Bảy, bà Năm, mẩu giấy ghi vội.
const BALLPOINT := "mynerve"
## Bút chì run, chữ viết vội.
const PENCIL := "grape-nuts"
## Chữ học trò tròn trịa: vở của Hùng.
const SCHOOL := "mali"
## Chữ in giấy tờ nhà nước.
const PRINT := "tinos"
## Chữ máy chữ điền vào mẫu.
const TYPEWRITER := "xanh-mono"
## Chữ đứng đậm cho dấu mộc, nhãn dán.
const STAMP := "oswald"

const DIR := "res://assets/fonts/"

static var _cache: Dictionary = {}


## Font [param family] (một trong các hằng ở trên) độ đậm [param weight].
## Không có độ đậm đó thì lấy 400 (hoặc độ đậm đầu tiên có sẵn).
static func get_font(family: String, weight: int = 400) -> Font:
	var key := "%s-%d" % [family, weight]
	if _cache.has(key):
		return _cache[key]
	# Tệp vietnamese làm font chính: chữ dựng sẵn (ố, ữ, ỵ...) lấy thẳng từ đây. Nếu để latin
	# làm chính, HarfBuzz tách "ố" thành "ô" + dấu sắc rồi dấu rơi sang font khác, lệch chỗ.
	var base := _load(family, "vietnamese", weight)
	if base == null:
		for w: int in [400, 500, 700]:
			base = _load(family, "vietnamese", w)
			if base:
				weight = w
				break
	if base == null:
		push_warning("PaperFonts: thiếu font " + family)
		return ThemeDB.fallback_font
	var font := FontVariation.new()
	font.base_font = base
	var fallbacks: Array[Font] = []
	for subset: String in ["latin", "latin-ext"]:
		var f := _load(family, subset, weight)
		if f:
			fallbacks.append(f)
	font.fallbacks = fallbacks
	_cache[key] = font
	return font


static func _load(family: String, subset: String, weight: int) -> FontFile:
	var path := "%s%s/%s-%s-%d.woff2" % [DIR, family, family, subset, weight]
	if not ResourceLoader.exists(path):
		return null
	return load(path) as FontFile
