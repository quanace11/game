## Gối nằm của An. Bấm [E] Nhấc gối: gối được nhấc lên, dịch sang một bên
## bằng Tween, để lộ vật giấu bên dưới ([member revealed], ví dụ chìa khóa đồng).
##
## Vật bên dưới bị tắt tương tác cho tới khi gối đã nhấc xong, nên tâm ngắm
## không thể "nhìn xuyên" gối để nhặt trước.
class_name PillowInteraction
extends Interactable

## Vật lộ ra dưới gối.
@export var revealed: Interactable
## Gối được nhấc cao bao nhiêu mét trước khi dịch sang bên.
@export var lift_height: float = 0.14
## Độ dời cuối cùng (trong không gian của node cha), ví dụ trượt về phía cuối giường.
@export var slide_offset: Vector3 = Vector3(0.05, 0.03, 0.45)
@export var slide_yaw_degrees: float = 18.0
@export var lift_duration: float = 0.3
@export var slide_duration: float = 0.5
@export var lift_sfx: StringName = &"sfx_pillow_lift"

var is_lifted := false
var _tween: Tween


func _ready() -> void:
	super()
	if prompt_text_key.is_empty():
		prompt_text_key = "PROMPT_PILLOW_LIFT"
	if revealed:
		revealed.enabled = false


func _exit_tree() -> void:
	if _tween:
		_tween.kill()


func interact(actor: Node) -> bool:
	if not enabled or is_lifted:
		return false
	is_lifted = true
	enabled = false
	interacted.emit(actor)
	EventBus.interaction_requested.emit(self, actor)
	EventBus.sfx_requested.emit(lift_sfx, global_position)

	var up := Vector3.UP * lift_height
	var start := position
	var end := start + slide_offset
	_tween = create_tween().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_tween.tween_property(self, "position", start + up, lift_duration)
	_tween.tween_property(self, "position", end + up, slide_duration)
	_tween.parallel().tween_property(self, "rotation:y",
			rotation.y + deg_to_rad(slide_yaw_degrees), slide_duration)
	_tween.tween_property(self, "position", end, 0.18).set_ease(Tween.EASE_IN)
	_tween.tween_callback(_reveal)
	return true


func _reveal() -> void:
	if is_instance_valid(revealed):
		revealed.enabled = true
