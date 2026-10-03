## Gắn vào nhân vật An (làm node con Area3D, kèm CollisionShape3D là vùng tầm với).
##
## Theo dõi các Interactable trong vùng, chọn vật gần nhất và gọi
## [method Interactable.interact] khi người chơi bấm action "interact" (phím E).
## UI lời nhắc lắng nghe [signal EventBus.interaction_prompt_changed].
class_name PlayerInteractor
extends Area3D

const INTERACT_ACTION := &"interact"

## Node đại diện người chơi, truyền vào Interactable làm actor.
## Mặc định là node cha (nhân vật An).
@export var actor: Node

var _candidates: Array[Interactable] = []
var _focused: Interactable


func _ready() -> void:
	if actor == null:
		actor = get_parent()
	# Chỉ quét vật tương tác, không để thứ khác phát hiện vùng này.
	monitoring = true
	monitorable = false
	collision_layer = 0
	collision_mask = 0
	set_collision_mask_value(Interactable.INTERACTABLE_LAYER, true)
	area_entered.connect(_on_area_entered)
	area_exited.connect(_on_area_exited)


func _physics_process(_delta: float) -> void:
	_set_focused(_find_nearest())


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(INTERACT_ACTION):
		if try_interact():
			get_viewport().set_input_as_handled()


## Tương tác với vật đang được chọn. Trả về true nếu thành công.
func try_interact() -> bool:
	var target := _find_nearest()
	if target == null:
		return false
	var ok := target.interact(actor)
	_set_focused(_find_nearest())
	return ok


func get_focused() -> Interactable:
	return _focused


func _find_nearest() -> Interactable:
	var nearest: Interactable = null
	var best := INF
	for candidate in _candidates:
		if not is_instance_valid(candidate) or not candidate.enabled:
			continue
		var dist := global_position.distance_squared_to(candidate.global_position)
		if dist < best:
			best = dist
			nearest = candidate
	return nearest


func _set_focused(target: Interactable) -> void:
	if target == _focused:
		return
	_focused = target
	var text := target.get_prompt_text() if target else ""
	EventBus.interaction_prompt_changed.emit(text)


func _on_area_entered(area: Area3D) -> void:
	if area is Interactable and area not in _candidates:
		_candidates.append(area)


func _on_area_exited(area: Area3D) -> void:
	_candidates.erase(area)
