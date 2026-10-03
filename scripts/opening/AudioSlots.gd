## Tìm file âm thanh theo ID trong res://assets/audio/.
##
## Thả file đúng tên (ví dụ sfx_crying.ogg) vào thư mục là phân cảnh tự dùng,
## không cần sửa code hay scene. Thiếu file thì trả về null và phân cảnh vẫn
## chạy bình thường (chỉ không có tiếng).
class_name AudioSlots
extends RefCounted

const AUDIO_DIR := "res://assets/audio/"
const EXTENSIONS: Array[String] = ["ogg", "wav", "mp3"]


## [param override] khác null thì dùng luôn (gán từ Inspector).
static func resolve(id: String, override: AudioStream = null) -> AudioStream:
	if override:
		return override
	for ext in EXTENSIONS:
		var path := "%s%s.%s" % [AUDIO_DIR, id, ext]
		if ResourceLoader.exists(path):
			return load(path) as AudioStream
	return null
