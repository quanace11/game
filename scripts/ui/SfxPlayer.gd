## Phát hiệu ứng âm thanh theo yêu cầu từ EventBus.
##
## - [signal EventBus.sfx_requested]: âm thanh 3D tại một vị trí trong thế giới.
## - [signal EventBus.ui_sfx_requested]: âm thanh giao diện, không định vị.
## File được tìm theo ID trong res://assets/audio/ (xem [AudioSlots]); thiếu file
## thì bỏ qua, game vẫn chạy bình thường. Mỗi lần phát tạo một player tạm và tự
## giải phóng khi phát xong.
class_name SfxPlayer
extends Node3D

@export var bus: StringName = &"SFX"
@export var unit_size: float = 3.0

var _cache: Dictionary[StringName, AudioStream] = {}


func _ready() -> void:
	if AudioServer.get_bus_index(bus) == -1:
		bus = &"Master"
	EventBus.sfx_requested.connect(_on_sfx_requested)
	EventBus.ui_sfx_requested.connect(_on_ui_sfx_requested)


func _exit_tree() -> void:
	if EventBus.sfx_requested.is_connected(_on_sfx_requested):
		EventBus.sfx_requested.disconnect(_on_sfx_requested)
	if EventBus.ui_sfx_requested.is_connected(_on_ui_sfx_requested):
		EventBus.ui_sfx_requested.disconnect(_on_ui_sfx_requested)


func _on_sfx_requested(sound_id: StringName, at: Vector3) -> void:
	var stream := _resolve(sound_id)
	if stream == null:
		return
	var player := AudioStreamPlayer3D.new()
	player.stream = stream
	player.bus = bus
	player.unit_size = unit_size
	add_child(player)
	player.global_position = at
	player.finished.connect(player.queue_free)
	player.play()


func _on_ui_sfx_requested(sound_id: StringName) -> void:
	var stream := _resolve(sound_id)
	if stream == null:
		return
	var player := AudioStreamPlayer.new()
	player.stream = stream
	player.bus = bus
	add_child(player)
	player.finished.connect(player.queue_free)
	player.play()


func _resolve(sound_id: StringName) -> AudioStream:
	if not _cache.has(sound_id):
		_cache[sound_id] = AudioSlots.resolve(String(sound_id))
	return _cache[sound_id]
