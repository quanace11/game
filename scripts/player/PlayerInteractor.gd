## Tâm ngắm tương tác: RayCast3D gắn dưới Camera3D của An, bắn thẳng về phía
## trước [member reach] mét.
##
## Khi rọi trúng một Interactable, phát [signal EventBus.interaction_focus_changed]
## để HUD làm sáng tâm ngắm và hiện tên vật. Bấm action "interact" (E) để tương tác.
## Tường và đồ vật thường (layer 1) chặn tia, nên không tương tác xuyên tường.
class_name PlayerInteractor
extends RayCast3D

const INTERACT_ACTION := &"interact"

## Tầm với của tia (mét).
@export var reach: float = 2.0
## Node đại diện người chơi, truyền vào Interactable làm actor và được loại khỏi tia.
@export var actor: Node

var _focused: Interactable
var _locked := false


func _ready() -> void:
	target_position = Vector3(0.0, 0.0, -reach)
	collide_with_areas = true
	collide_with_bodies = true
	collision_mask = 0
	set_collision_mask_value(1, true)
	set_collision_mask_value(Interactable.INTERACTABLE_LAYER, true)
	if actor == null:
		actor = owner
	if actor is CollisionObject3D:
		add_exception(actor)
	EventBus.player_controls_locked.connect(_on_controls_locked)


func _physics_process(_delta: float) -> void:
	if not _locked:
		_set_focused(_find_target())


func _unhandled_input(event: InputEvent) -> void:
	if not _locked and event.is_action_pressed(INTERACT_ACTION):
		if try_interact():
			get_viewport().set_input_as_handled()


## Tương tác với vật đang được rọi. Trả về true nếu thành công.
func try_interact() -> bool:
	var target := _find_target()
	if target == null:
		return false
	var ok := target.interact(actor)
	_set_focused(null if _locked else _find_target())
	return ok


func get_focused() -> Interactable:
	return _focused


func _find_target() -> Interactable:
	force_raycast_update()
	if not is_colliding():
		return null
	var target := get_collider() as Interactable
	if target == null or not target.enabled or target.is_queued_for_deletion():
		return null
	return target


func _set_focused(target: Interactable) -> void:
	if target == _focused:
		return
	_focused = target
	EventBus.interaction_focus_changed.emit(target)


func _on_controls_locked(locked: bool) -> void:
	_locked = locked
	if locked:
		_set_focused(null)
