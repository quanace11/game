## Bé gái trong cơn ác mộng: đứng quay lưng, khóc thút thít (âm thanh 3D),
## rồi quay ngoắt đầu lại ở cú jumpscare.
##
## Mặt trước (khuôn mặt đen kịt) hướng về -Z cục bộ. Đặt cô bé sao cho
## lưng (+Z) quay về phía người chơi.
class_name GhostGirl
extends Node3D

## Đổi góc quay đầu ở cú jumpscare (độ, quanh trục Y). 180 = quay hẳn ra sau.
@export var head_turn_degrees: float = 180.0
## Nghiêng đầu bất thường sau khi quay (độ, quanh trục Z).
@export var head_tilt_degrees: float = 24.0
@export var head_turn_duration: float = 0.16

@onready var _head: Node3D = %HeadPivot
@onready var _crying: AudioStreamPlayer3D = %Crying
@onready var talk_area: Interactable = %TalkArea
## Ánh sáng lạnh rọi vào mặt cô bé đúng lúc quay đầu, để khuôn mặt đen kịt đọc được.
@onready var _face_light: OmniLight3D = %FaceLight

var _turn_tween: Tween


func _exit_tree() -> void:
	if _turn_tween:
		_turn_tween.kill()


## Phát tiếng khóc. [param stream] null thì giữ stream đã gán trong scene.
func start_crying(stream: AudioStream = null) -> void:
	if stream:
		_crying.stream = stream
	if _crying.stream and not _crying.playing:
		_crying.play()


## Tắt tiếng khóc đột ngột (khoảng lặng trước jumpscare).
func stop_crying() -> void:
	_crying.stop()


func set_talkable(value: bool) -> void:
	if talk_area:
		talk_area.enabled = value


## Vị trí bờ vai để camera nhìn vào khi An đặt tay lên vai.
func get_shoulder_position() -> Vector3:
	return to_global(Vector3(0.1, 0.86, 0.0))


## Quay ngoắt đầu lại. Trả về tween để chờ [signal Tween.finished].
func snap_head() -> Tween:
	if _turn_tween:
		_turn_tween.kill()
	var start := _head.rotation
	_turn_tween = create_tween()
	# Hai cái giật nhẹ trước khi quay hẳn.
	_turn_tween.tween_property(_head, "rotation:y", start.y + deg_to_rad(8.0), 0.05)
	_turn_tween.tween_property(_head, "rotation:y", start.y - deg_to_rad(4.0), 0.05)
	_turn_tween.tween_property(_head, "rotation:y", start.y + deg_to_rad(head_turn_degrees),
			head_turn_duration).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_turn_tween.parallel().tween_property(_head, "rotation:z", deg_to_rad(head_tilt_degrees),
			head_turn_duration)
	_turn_tween.parallel().tween_property(_face_light, "light_energy", 1.4, head_turn_duration)
	return _turn_tween
