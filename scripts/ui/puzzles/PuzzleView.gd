## Lớp gốc cho một "đồ vật cận cảnh" trong SelectorPuzzleUI: hộp tôn khóa số, bảng lộ trình,
## vé bấm lỗ, giấy cắt guốc, dây chuông, tay hình nhân...
##
## View dựng trên sân khấu 1280x720 ([UIStage]), tự vẽ và tự xử lý phím/chuột, giữ lựa chọn
## hiện tại dưới dạng chỉ số từng hàng (cùng định dạng [signal EventBus.selector_submitted]).
## Khi người chơi xác nhận, view phát [signal submit_requested]; SelectorPuzzleUI so đáp án rồi
## gọi [method play_right] / [method play_wrong] để view diễn phản hồi vật lý.
class_name PuzzleView
extends Control

## Người chơi xác nhận (bấm E, giật xong dây chuông, đưa đồ vào tay...).
signal submit_requested
## Muốn hiện một dòng trạng thái ngắn (ví dụ "Còn bến trống.").
signal status_requested(text: String)

const TICK_SFX := &"sfx_dial_tick"

var puzzle_id: StringName
var title := ""
var rows: Array = []
var selection: Array[int] = []
var stage: UIStage
var _busy := false


func _init() -> void:
	size = UIStage.DESIGN
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Gọi một lần sau khi view được thêm vào sân khấu.
func setup(p_id: StringName, p_title: String, p_rows: Array, p_stage: UIStage) -> void:
	puzzle_id = p_id
	title = p_title
	rows = p_rows
	stage = p_stage
	selection.clear()
	for row in rows:
		selection.append(0)
	_setup()


## Ghi đè: dựng hình, đặt lựa chọn ban đầu.
func _setup() -> void:
	pass


## Ghi đè: xử lý phím/chuột. Trả về true nếu đã dùng sự kiện.
func handle_input(_event: InputEvent) -> bool:
	return false


## Dòng chỉ dẫn điều khiển hiện ở góc dưới.
func hint_text() -> String:
	return tr(&"UI_SELECTOR_HINT")


func get_selection() -> Array[int]:
	return selection.duplicate()


## Ghi đè: phản hồi khi đúng. Trả về số giây diễn trước khi đóng.
func play_right() -> float:
	return 0.7


## Ghi đè: phản hồi khi sai. [param closing] = true nếu sai là đóng luôn (đốt mã sai...).
## Trả về số giây diễn.
func play_wrong(_closing: bool) -> float:
	return 0.9


func set_busy(busy: bool) -> void:
	_busy = busy


func options(row: int) -> Array:
	if row < 0 or row >= rows.size():
		return []
	return rows[row].get("options", [])


## Vị trí chuột của [param event] trên sân khấu.
func stage_pos(event: InputEvent) -> Vector2:
	if event is InputEventMouse:
		return stage.to_stage((event as InputEventMouse).position)
	return Vector2(-1, -1)


func tick() -> void:
	EventBus.ui_sfx_requested.emit(TICK_SFX)


static func pressed(event: InputEvent, actions: Array) -> bool:
	for a: StringName in actions:
		if event.is_action_pressed(a, true):
			return true
	return false


const LEFT := [&"move_left", &"ui_left"]
const RIGHT := [&"move_right", &"ui_right"]
const UP := [&"move_forward", &"ui_up"]
const DOWN := [&"move_back", &"ui_down"]
const CONFIRM := [&"interact", &"ui_accept"]


## Rung một Control quanh vị trí gốc (khóa không mở, biển lắc...).
static func shake(node: CanvasItem, tween: Tween, strength: float, times: int, duration: float) -> void:
	var base: Vector2 = node.position
	var step := duration / (times * 2.0)
	for i in times:
		var k := 1.0 - float(i) / times
		tween.tween_property(node, "position", base + Vector2(strength * k, -strength * 0.3 * k), step)
		tween.tween_property(node, "position", base - Vector2(strength * k, -strength * 0.2 * k), step)
	tween.tween_property(node, "position", base, step)
