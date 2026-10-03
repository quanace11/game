## Đạo diễn phân cảnh mở đầu: Cơn ác mộng ngoài sân -> Choàng tỉnh và nghe lén.
##
## Chỉ điều phối timeline: nạp level, điều khiển camera/âm thanh, rồi phát
## sự kiện qua EventBus. Phụ đề, fade, mờ, mí mắt, vignette do CinematicOverlay
## lắng nghe và vẽ; rung camera do CameraShake trong Player xử lý.
##
## Chạy thử từng giai đoạn: đổi [member start_state] trong Inspector rồi F6.
class_name OpeningSequenceManager
extends Node3D

enum State { STATE_NIGHTMARE, STATE_AWAKENING, STATE_FINISHED }

const SKIP_ACTIONS: Array[StringName] = [&"interact", &"ui_accept"]
const STANDING_HEAD := Vector3(0.0, 1.6, 0.0)
const COLD_TINT := Color(0.04, 0.08, 0.16)

## Phát khi An bấm [E] Hỏi thăm (nội bộ, để timeline chờ).
signal _girl_approached

@export var start_state: State = State.STATE_NIGHTMARE
@export var nightmare_scene: PackedScene
@export var bedroom_scene: PackedScene
## Scene chuyển tới khi phân cảnh xong. Để trống thì thả An đi lại tự do trong phòng.
@export_file("*.tscn") var next_scene_path: String

@export_group("Cơn ác mộng")
## An bước chậm trong mơ.
@export var nightmare_walk_speed: float = 1.3
## Bán kính (m) hiện lời nhắc [E] Hỏi thăm.
@export var talk_radius: float = 1.5
## Chiều cao mắt khi ngồi xổm cạnh cô bé.
@export var crouch_head_height: float = 0.95
## Khoảng cách An dừng lại để đặt tay lên vai cô bé.
@export var hand_reach: float = 0.75
## Giây chờ sau khi mở mắt trong mơ rồi mới hiện độc thoại đầu tiên.
@export var notice_delay: float = 2.5
## Khoảng lặng (giây) sau khi tiếng khóc tắt, trước khi cô bé quay đầu.
@export var silence_before_scare: float = 1.6
## Thời gian giữ màn hình đen sau jumpscare.
@export var blackout_seconds: float = 1.0

@export_group("Choàng tỉnh")
## Vị trí thân An trên giường (tọa độ thế giới của DreamBedroom).
@export var bed_position: Vector3 = Vector3(-0.45, 0.6, -1.75)
@export var bed_yaw_degrees: float = 180.0
## Vị trí Head lúc nằm (đầu trên gối) và lúc ngồi dậy, tương đối với thân.
@export var lying_head: Vector3 = Vector3(0.0, 0.2, 0.4)
@export var sitting_head: Vector3 = Vector3(0.0, 0.8, 0.0)
## Chỗ An đứng khi được thả tự do (nếu không có next_scene_path).
@export var free_position: Vector3 = Vector3(1.4, 0.05, -0.4)

@export_group("Phụ đề")
@export var seconds_per_char: float = 0.055
@export var min_line_seconds: float = 2.5
@export var line_gap: float = 0.35
## Cho bấm E / Enter để qua câu sớm.
@export var allow_skip: bool = true

@export_group("Âm thanh (để trống = tự tìm res://assets/audio/<id>.ogg|wav|mp3)")
@export var sfx_crying: AudioStream
@export var sfx_jumpscare: AudioStream
@export var voice_parents: AudioStream
@export var sfx_breathing: AudioStream
@export var sfx_footsteps: AudioStream
## Bus có AudioEffectLowPassFilter để tiếng nghe như vọng qua vách.
@export var muffle_bus: StringName = &"Muffled"
@export var muffle_cutoff_hz: float = 650.0

@onready var _level_root: Node3D = $LevelRoot
@onready var _night_mode: BedroomNightMode = $BedroomNightMode
@onready var _stinger: AudioStreamPlayer = $Stinger
@onready var _breathing: AudioStreamPlayer = $Breathing
@onready var _parents_voice: AudioStreamPlayer3D = $ParentsVoice
@onready var _footsteps: AudioStreamPlayer3D = $Footsteps

var state: State = State.STATE_NIGHTMARE
var _level: Node3D
var _player: PlayerController
var _girl: GhostGirl
var _awaiting_talk := false
var _skippable := false
var _skip_requested := false


func _ready() -> void:
	_stinger.stream = AudioSlots.resolve("sfx_jumpscare", sfx_jumpscare)
	_breathing.stream = AudioSlots.resolve("sfx_breathing", sfx_breathing)
	_parents_voice.stream = AudioSlots.resolve("voice_parents", voice_parents)
	_footsteps.stream = AudioSlots.resolve("sfx_footsteps", sfx_footsteps)
	_configure_muffle()
	_run()


func _physics_process(_delta: float) -> void:
	if not _awaiting_talk or _girl == null or _player == null:
		return
	var offset := _girl.global_position - _player.global_position
	offset.y = 0.0
	_girl.set_talkable(offset.length() <= talk_radius)


func _unhandled_input(event: InputEvent) -> void:
	if not _skippable:
		return
	for action in SKIP_ACTIONS:
		if event.is_action_pressed(action):
			_skip_requested = true
			get_viewport().set_input_as_handled()
			return


func _run() -> void:
	if start_state == State.STATE_NIGHTMARE:
		await _play_nightmare()
	if not is_inside_tree():
		return
	await _play_awakening()
	if is_inside_tree():
		await _finish()


# --- GIAI ĐOẠN 1: CƠN ÁC MỘNG -------------------------------------------------

func _play_nightmare() -> void:
	_set_state(State.STATE_NIGHTMARE)
	if not _load_level(nightmare_scene):
		return
	_girl = _level.get_node_or_null(^"GhostGirl") as GhostGirl
	if _girl == null:
		push_error("OpeningSequenceManager: NightmareYard thiếu node GhostGirl.")
		return
	_player.walk_speed = nightmare_walk_speed
	_girl.start_crying(AudioSlots.resolve("sfx_crying", sfx_crying))
	_girl.talk_area.interacted.connect(_on_girl_interacted, CONNECT_ONE_SHOT)

	# Không gian hư ảo: mờ nhòe tan dần, viền lạnh nhẹ suốt giấc mơ.
	EventBus.screen_effect_requested.emit(&"blur", 3.0, 0.0)
	EventBus.screen_effect_requested.emit(&"blur", 0.6, 4.0)
	EventBus.screen_effect_requested.emit(&"vignette", 0.35, 0.0)
	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 3.0)
	EventBus.subtitle_requested.emit("", tr(&"CAPTION_CRYING"), 3.0)

	# Bước 1: An nhận ra bóng lưng quen thuộc.
	await _wait(notice_delay)
	_monologue(&"OPENING_MONO_GIRL_NOTICE")

	# Bước 2: chờ An lại gần (<= talk_radius) và bấm [E] Hỏi thăm.
	_awaiting_talk = true
	await _girl_approached
	_awaiting_talk = false
	if not is_inside_tree():
		return
	EventBus.player_controls_locked.emit(true)
	EventBus.subtitles_cleared.emit()
	await _crouch_beside_girl()
	await _say(&"SPEAKER_AN", &"OPENING_AN_ASK_GIRL")

	# Bước 3: người con bé lạnh ngắt.
	EventBus.camera_shake_requested.emit(0.012, 1.4)
	EventBus.screen_effect_requested.emit(&"vignette", 0.75, 1.5)
	await _say_monologue(&"OPENING_MONO_COLD")

	# Bước 4: tiếng khóc tắt phụt, khoảng lặng, rồi cô bé quay ngoắt đầu lại.
	_girl.stop_crying()
	EventBus.subtitles_cleared.emit()
	await _wait(silence_before_scare)
	if _stinger.stream:
		_stinger.play()
	EventBus.camera_shake_requested.emit(0.04, 0.6)
	await _girl.snap_head().finished
	await _wait(0.35)
	EventBus.screen_fade_requested.emit(Color.WHITE, 1.0, 0.04)
	await _wait(0.12)
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 0.0)
	EventBus.screen_effect_requested.emit(&"vignette", 0.0, 0.0)
	EventBus.screen_effect_requested.emit(&"blur", 0.0, 0.0)
	MemoryManager.unlock_memory(&"memory_nightmare_girl")
	_unload_level()
	await _wait(blackout_seconds)


## Ngồi xổm xuống cạnh cô bé, xoay người nhìn vào bờ vai.
func _crouch_beside_girl() -> void:
	_player.set_physics_process(false)
	var girl_pos := _girl.global_position
	var away := _player.global_position - girl_pos
	away.y = 0.0
	away = away.normalized() if away.length() > 0.01 else Vector3.BACK
	var stand_pos := girl_pos + away * hand_reach
	stand_pos.y = _player.global_position.y

	var shoulder := _girl.get_shoulder_position()
	var to_shoulder := shoulder - stand_pos
	var target_yaw := atan2(-to_shoulder.x, -to_shoulder.z)
	var eye_y := stand_pos.y + crouch_head_height
	var flat := Vector2(to_shoulder.x, to_shoulder.z).length()
	var target_pitch := atan2(shoulder.y - eye_y, flat)

	var start_yaw := _player.rotation.y
	var tween := create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(_player, "global_position", stand_pos, 1.4)
	tween.tween_method(func(t: float) -> void: _player.rotation.y = lerp_angle(start_yaw, target_yaw, t),
			0.0, 1.0, 1.0)
	tween.tween_property(_player.head, "position:y", crouch_head_height, 1.4)
	tween.tween_property(_player.head, "rotation:x", target_pitch, 1.2)
	await tween.finished


func _on_girl_interacted(_actor: Node) -> void:
	_girl_approached.emit()


# --- GIAI ĐOẠN 2: CHOÀNG TỈNH VÀ NGHE LÉN --------------------------------------

func _play_awakening() -> void:
	_set_state(State.STATE_AWAKENING)
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 0.0)
	EventBus.screen_effect_requested.emit(&"eyes_open", 0.0, 0.0)
	EventBus.screen_effect_requested.emit(&"blur", 4.0, 0.0)
	if not _load_level(bedroom_scene):
		return
	_night_mode.apply(_level)
	_put_player_in_bed()

	# An bừng tỉnh: thở dốc, mí mắt hé mở chập chờn, mờ nhòe tan dần.
	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 0.6)
	EventBus.subtitle_requested.emit("", tr(&"CAPTION_BREATHING"), 3.0)
	if _breathing.stream:
		_breathing.volume_db = 0.0
		_breathing.play()
	EventBus.camera_shake_requested.emit(0.006, 3.5)
	await _open_eyes()

	# Ngồi dậy (chưa bước xuống giường).
	var sit := create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	sit.tween_property(_player.head, "position", sitting_head, 2.2)
	sit.tween_property(_player.head, "rotation:x", deg_to_rad(-6.0), 2.2)
	await sit.finished
	await _say_monologue(&"OPENING_MONO_WAKE")
	_fade_out_breathing()
	await _wait(1.2)

	# Nghe lén: cho xoay nhìn nhưng vẫn ngồi trên giường.
	EventBus.objective_updated.emit(tr(&"OBJ_LISTEN_PARENTS"), false)
	EventBus.player_controls_locked.emit(false)
	EventBus.subtitle_requested.emit("", tr(&"CAPTION_WHISPER"), 3.0)
	await _wait(2.5)
	if _parents_voice.stream:
		_parents_voice.play()
	# Khi đã có file voice_parents thì không cho bỏ qua để phụ đề khớp tiếng.
	var skippable := _parents_voice.stream == null
	await _say(&"SPEAKER_MOTHER", &"OPENING_MOTHER_01", skippable)
	await _say(&"SPEAKER_MOTHER", &"OPENING_MOTHER_02", skippable)
	await _say(&"SPEAKER_FATHER", &"OPENING_FATHER_01", skippable)
	await _say(&"SPEAKER_FATHER", &"OPENING_FATHER_02", skippable)
	await _say(&"SPEAKER_FATHER", &"OPENING_FATHER_03", skippable)
	while _parents_voice.playing and is_inside_tree():
		await get_tree().process_frame

	# Tiếng bước chân nhỏ dần rồi tắt hẳn.
	await _footsteps_fade_away()
	await _wait(1.2)

	# The Call to Adventure.
	await _say_monologue(&"OPENING_MONO_CALL_01")
	await _say_monologue(&"OPENING_MONO_CALL_02")
	EventBus.objective_updated.emit(tr(&"OBJ_FIND_NOTEBOOK"), true)
	MemoryManager.unlock_memory(&"memory_parents_secret")


func _put_player_in_bed() -> void:
	EventBus.player_controls_locked.emit(true)
	_player.set_physics_process(false)
	_player.movement_locked = true
	_player.velocity = Vector3.ZERO
	_player.global_position = bed_position
	_player.rotation = Vector3(0.0, deg_to_rad(bed_yaw_degrees), 0.0)
	_player.head.position = lying_head
	_player.head.rotation = Vector3(deg_to_rad(75.0), 0.0, 0.0)


func _open_eyes() -> void:
	EventBus.screen_effect_requested.emit(&"blur", 0.0, 5.0)
	var steps: Array[Vector2] = [  # (độ mở, thời gian)
		Vector2(0.3, 0.9), Vector2(0.05, 0.3), Vector2(0.65, 1.1),
		Vector2(0.4, 0.35), Vector2(1.0, 1.4),
	]
	for step in steps:
		EventBus.screen_effect_requested.emit(&"eyes_open", step.x, step.y)
		await _wait(step.y + 0.1)


func _fade_out_breathing() -> void:
	if not _breathing.playing:
		return
	var tween := create_tween()
	tween.tween_property(_breathing, "volume_db", -40.0, 2.5)
	tween.tween_callback(_breathing.stop)


func _footsteps_fade_away() -> void:
	EventBus.subtitle_requested.emit("", tr(&"CAPTION_FOOTSTEPS"), 3.5)
	var start := _footsteps.position
	if _footsteps.stream:
		_footsteps.volume_db = 0.0
		_footsteps.play()
	var tween := create_tween().set_parallel()
	tween.tween_property(_footsteps, "position", start + Vector3(3.5, 0.0, -4.0), 4.0)
	tween.tween_property(_footsteps, "volume_db", -40.0, 4.0).set_ease(Tween.EASE_IN)
	await tween.finished
	_footsteps.stop()
	_footsteps.position = start


# --- KẾT THÚC ---------------------------------------------------------------------

func _finish() -> void:
	_set_state(State.STATE_FINISHED)
	EventBus.opening_sequence_finished.emit()
	await _wait(3.0)
	if not is_inside_tree():
		return
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 1.5)
	await _wait(1.6)
	if not next_scene_path.is_empty():
		get_tree().change_scene_to_file(next_scene_path)
		return
	if _player:
		var hud := _player.get_node_or_null(^"HUD") as HUD
		if hud:
			hud.set_hotbar_visible(true)
		_player.global_position = free_position
		_player.head.position = STANDING_HEAD
		_player.head.rotation = Vector3.ZERO
		_player.movement_locked = false
		_player.set_physics_process(true)
	EventBus.player_controls_locked.emit(false)
	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 1.5)


# --- Tiện ích ----------------------------------------------------------------------

func _set_state(new_state: State) -> void:
	state = new_state
	EventBus.opening_state_changed.emit(new_state)


func _load_level(scene: PackedScene) -> bool:
	_unload_level()
	if scene == null:
		push_error("OpeningSequenceManager: chưa gán scene cho giai đoạn %s." % State.keys()[state])
		return false
	_level = scene.instantiate() as Node3D
	_level_root.add_child(_level)
	_player = _level.get_node_or_null(^"Player") as PlayerController
	if _player == null:
		push_error("OpeningSequenceManager: level %s thiếu node Player." % _level.name)
		return false
	# An chưa có đồ gì trong phân cảnh mở đầu: ẩn Hotbar cho khung hình sạch.
	var hud := _player.get_node_or_null(^"HUD") as HUD
	if hud:
		hud.set_hotbar_visible(false)
	return true


func _unload_level() -> void:
	_awaiting_talk = false
	_girl = null
	_player = null
	if is_instance_valid(_level):
		_level.queue_free()
	_level = null


func _line_duration(text: String) -> float:
	return maxf(min_line_seconds, text.length() * seconds_per_char)


## Câu thoại có người nói, hiện dạng phụ đề.
func _say(speaker_key: StringName, text_key: StringName, skippable: bool = true) -> void:
	var text := tr(text_key)
	var duration := _line_duration(text)
	EventBus.subtitle_requested.emit(tr(speaker_key), text, duration)
	await _wait(duration + line_gap, skippable and allow_skip)


## Độc thoại nội tâm, hiện ở góc dưới màn hình. Không chờ.
func _monologue(text_key: StringName) -> float:
	var text := tr(text_key)
	var duration := _line_duration(text)
	EventBus.inner_monologue_requested.emit(text, duration)
	return duration


## Độc thoại nội tâm và chờ đọc xong (hoặc người chơi bấm qua).
func _say_monologue(text_key: StringName) -> void:
	var duration := _monologue(text_key)
	await _wait(duration + line_gap, allow_skip)


## Chờ [param seconds] giây. [param skippable] = true thì E/Enter kết thúc sớm.
func _wait(seconds: float, skippable: bool = false) -> void:
	_skip_requested = false
	_skippable = skippable
	var left := seconds
	while left > 0.0 and is_inside_tree():
		await get_tree().process_frame
		left -= get_process_delta_time()
		if _skip_requested:
			EventBus.subtitles_cleared.emit()
			break
	_skippable = false
	_skip_requested = false


func _configure_muffle() -> void:
	for player: AudioStreamPlayer3D in [_parents_voice, _footsteps]:
		player.attenuation_filter_cutoff_hz = muffle_cutoff_hz
	var idx := AudioServer.get_bus_index(muffle_bus)
	if idx == -1:
		push_warning("OpeningSequenceManager: không có bus '%s', dùng Master." % muffle_bus)
		_parents_voice.bus = &"Master"
		_footsteps.bus = &"Master"
		return
	for i in AudioServer.get_bus_effect_count(idx):
		var low_pass := AudioServer.get_bus_effect(idx, i) as AudioEffectLowPassFilter
		if low_pass:
			low_pass.cutoff_hz = muffle_cutoff_hz
