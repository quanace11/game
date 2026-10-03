## Đạo diễn phân cảnh xe khách về Thôn Đoài.
##
## Timeline: màn chữ mở chương trên nền đen ở bến xe -> An lên xe, tìm ghế trống
## và ngồi xuống -> xe lăn bánh, phụ xe và bà cụ bắt chuyện -> An buồn ngủ, mí mắt
## sụp dần rồi thiếp đi -> tỉnh dậy trên chính chiếc xe ấy nhưng vắng tanh, mục
## nát, đỗ im trong sương. An đi lại tự do, tìm thấy vé xe năm 1999; cửa xe kẹt
## cứng và có thứ gì đó đứng ngoài ô kính cửa.
##
## Director chỉ điều phối: phát lời thoại, fade, hiệu ứng qua EventBus (CinematicOverlay
## vẽ), đổi trạng thái nhìn của xe qua [BusLevel], bật/tắt các Interactable.
## Chạy thử từng đoạn: đổi [member start_state] trong Inspector rồi F6.
class_name BusRideDirector
extends Node3D

enum State {
	INTRO,     ## Nền đen, màn chữ mở chương, tiếng bến xe.
	BOARDING,  ## An đứng trong xe, tìm ghế trống.
	RIDING,    ## Xe chạy, hội thoại với phụ xe và bà cụ.
	DROWSY,    ## Mí mắt nặng dần, chớp mắt chậm.
	ASLEEP,    ## Màn hình đen, tiếng thì thầm.
	DERELICT,  ## Tỉnh dậy trên xe hoang, đi lại tìm hiểu.
	TRAPPED,   ## Đã thử cửa xe và thấy bóng người ngoài cửa kính.
}

const SKIP_ACTIONS: Array[StringName] = [&"interact", &"ui_accept"]
const STANDING_HEAD_Y := 1.6

@export var level: BusLevel
@export var start_state: State = State.INTRO

@export_group("Tương tác")
## Ghế trống của An (bên phải, sát cửa sổ).
@export var seat: Interactable
## Cửa lên xuống của xe (chỉ dùng ở trạng thái hoang tàn).
@export var bus_door: Interactable
## Các vật chỉ xuất hiện và tương tác được khi xe đã hoang tàn.
@export var derelict_interactables: Array[Interactable] = []
## Bóng người hiện ngoài ô kính cửa xe trong khoảnh khắc mất điện (GhostGirl hoặc node chứa nó).
@export var apparition: Node3D
@export var ticket_item_id: StringName = &"bus_ticket_1999"

@export_group("Chỗ ngồi")
## Vị trí thân An khi ngồi (tọa độ thế giới) và hướng nhìn.
@export var seat_position: Vector3 = Vector3(1.03, 0.0, -0.36)
@export var seat_yaw_degrees: float = 0.0
@export var seated_head_height: float = 1.2
## Chỗ An đứng dậy ra lối đi khi tỉnh trên xe hoang.
@export var stand_position: Vector3 = Vector3(0.2, 0.05, -0.45)
@export var stand_yaw_degrees: float = 90.0

@export_group("Xe chạy")
## Biên độ nghiêng (radian) và nhún (mét) của đầu An khi xe chạy.
@export var sway_roll: float = 0.012
@export var sway_bob: float = 0.006
## Khoảng giây giữa hai lần xe xóc ổ gà.
@export var bump_interval: Vector2 = Vector2(2.5, 6.0)

@export_group("Phụ đề")
@export var seconds_per_char: float = 0.055
@export var min_line_seconds: float = 2.5
@export var line_gap: float = 0.35
## Cho bấm E / Enter để qua câu sớm.
@export var allow_skip: bool = true

@export_group("Âm thanh (để trống = tự tìm res://assets/audio/<id>.ogg|wav|mp3)")
@export var station_stream: AudioStream
@export var engine_stream: AudioStream
@export var derelict_stream: AudioStream
@export var stinger_stream: AudioStream

@onready var _station: AudioStreamPlayer = $StationAmbience
@onready var _engine: AudioStreamPlayer = $Engine
@onready var _derelict_amb: AudioStreamPlayer = $DerelictAmbience
@onready var _stinger: AudioStreamPlayer = $Stinger

var state: State = State.INTRO
var _player: PlayerController
var _skippable := false
var _skip_requested := false
var _riding := false
var _sway_time := 0.0
var _bump_timer := 0.0
var _rng := RandomNumberGenerator.new()
var _door_tried := false
var _ticket_pending := false
var _audio_tweens: Array[Tween] = []
var _motion_tween: Tween


func _ready() -> void:
	_rng.randomize()
	_station.stream = AudioSlots.resolve("amb_bus_station", station_stream)
	_engine.stream = AudioSlots.resolve("amb_bus_engine", engine_stream)
	_derelict_amb.stream = AudioSlots.resolve("amb_bus_derelict", derelict_stream)
	_stinger.stream = AudioSlots.resolve("sfx_jumpscare", stinger_stream)
	if level == null:
		push_error("BusRideDirector: chưa gán node level.")
		return
	_player = level.get_node_or_null(^"Player") as PlayerController
	if _player == null:
		push_error("BusRideDirector: level thiếu node Player.")
		return
	_set_derelict_interactables(false)
	if apparition:
		apparition.visible = false
		# Bóng ma chỉ để nhìn: tắt vùng [E] Hỏi thăm của GhostGirl.
		for node: Node in [apparition] + apparition.get_children():
			if node is GhostGirl:
				(node as GhostGirl).set_talkable(false)
	if bus_door:
		bus_door.interacted.connect(_on_bus_door_interacted)
	EventBus.item_picked_up.connect(_on_item_picked_up)
	EventBus.document_closed.connect(_on_document_closed)
	_run()


func _exit_tree() -> void:
	_riding = false
	if bus_door and bus_door.interacted.is_connected(_on_bus_door_interacted):
		bus_door.interacted.disconnect(_on_bus_door_interacted)
	if EventBus.item_picked_up.is_connected(_on_item_picked_up):
		EventBus.item_picked_up.disconnect(_on_item_picked_up)
	if EventBus.document_closed.is_connected(_on_document_closed):
		EventBus.document_closed.disconnect(_on_document_closed)
	for t in _audio_tweens:
		if t:
			t.kill()
	if _motion_tween:
		_motion_tween.kill()


func _unhandled_input(event: InputEvent) -> void:
	if not _skippable:
		return
	for action in SKIP_ACTIONS:
		if event.is_action_pressed(action):
			_skip_requested = true
			get_viewport().set_input_as_handled()
			return


func _process(delta: float) -> void:
	if not _riding or _player == null:
		return
	# Xe lắc lư: nghiêng nhẹ hai bên, nhún theo mặt đường, thỉnh thoảng xóc ổ gà.
	_sway_time += delta
	var roll := sin(_sway_time * 1.7) * sway_roll + sin(_sway_time * 0.63) * sway_roll * 0.6
	var bob := sin(_sway_time * 9.0) * sway_bob * 0.5 + sin(_sway_time * 3.1) * sway_bob * 0.5
	_player.head.rotation.z = roll
	_player.head.position.y = seated_head_height + bob
	_bump_timer -= delta
	if _bump_timer <= 0.0:
		_bump_timer = _rng.randf_range(bump_interval.x, bump_interval.y)
		EventBus.camera_shake_requested.emit(_rng.randf_range(0.006, 0.014), 0.3)


func _run() -> void:
	if _player == null:
		return
	if start_state <= State.BOARDING:
		await _play_intro()
		if not is_inside_tree():
			return
		if seat:
			await seat.interacted
		else:
			push_warning("BusRideDirector: chưa gán ghế, An ngồi xuống ngay.")
		if not is_inside_tree():
			return
		await _sit_down()
	else:
		_place_seated()
	if start_state <= State.DROWSY:
		if start_state <= State.RIDING:
			await _play_ride()
		if not is_inside_tree():
			return
		await _play_drowsy()
	if not is_inside_tree():
		return
	await _play_wake()


# --- 1. BẾN XE VÀ LÊN XE ---------------------------------------------------------

func _play_intro() -> void:
	_set_state(State.INTRO)
	level.set_derelict(false)
	level.set_moving(false, true)
	EventBus.player_controls_locked.emit(true)
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 0.0)
	_play(_station, -4.0)

	EventBus.title_card_requested.emit(tr(&"BUS_CHAPTER_TITLE"), tr(&"BUS_TITLE_PLACE"), 5.5)
	await _wait(6.0, allow_skip)
	EventBus.subtitle_requested.emit("", tr(&"BUS_CAPTION_STATION"), 3.0)
	await _wait(2.4)
	await _say(&"SPEAKER_CONDUCTOR", &"BUS_CONDUCTOR_CALL")

	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 2.0)
	await _say_monologue(&"BUS_MONO_INTRO")
	if not is_inside_tree():
		return
	EventBus.objective_updated.emit(tr(&"OBJ_FIND_SEAT"), true)
	EventBus.player_controls_locked.emit(false)
	_set_state(State.BOARDING)


## An ngồi xuống ghế: khóa di chuyển, chỉ còn xoay nhìn.
func _sit_down() -> void:
	EventBus.player_controls_locked.emit(true)
	if seat:
		seat.enabled = false
	_player.set_physics_process(false)
	_player.velocity = Vector3.ZERO
	var start_yaw := _player.rotation.y
	var target_yaw := deg_to_rad(seat_yaw_degrees)
	if _motion_tween:
		_motion_tween.kill()
	_motion_tween = create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_motion_tween.tween_property(_player, "global_position", seat_position, 1.4)
	_motion_tween.tween_method(func(t: float) -> void: _player.rotation.y = lerp_angle(start_yaw, target_yaw, t),
			0.0, 1.0, 1.2)
	_motion_tween.tween_property(_player.head, "position:y", seated_head_height, 1.4)
	_motion_tween.tween_property(_player.head, "rotation:x", deg_to_rad(-4.0), 1.2)
	await _motion_tween.finished
	if not is_inside_tree():
		return
	_player.movement_locked = true
	_set_hotbar_visible(false)
	EventBus.player_controls_locked.emit(false)
	EventBus.objective_updated.emit(tr(&"OBJ_BUS_RIDE"), false)


## Đặt An ngồi sẵn trên ghế (khi chạy thử từ giữa phân cảnh).
func _place_seated() -> void:
	if seat:
		seat.enabled = false
	_player.set_physics_process(false)
	_player.global_position = seat_position
	_player.rotation = Vector3(0.0, deg_to_rad(seat_yaw_degrees), 0.0)
	_player.head.position.y = seated_head_height
	_player.movement_locked = true
	_set_hotbar_visible(false)


# --- 2. XE LĂN BÁNH --------------------------------------------------------------

func _play_ride() -> void:
	_set_state(State.RIDING)
	_fade_audio(_station, -40.0, 4.0, true)
	_play(_engine, -6.0)
	level.set_moving(true)
	_riding = true
	EventBus.camera_shake_requested.emit(0.012, 0.7)
	EventBus.subtitle_requested.emit("", tr(&"BUS_CAPTION_ENGINE"), 3.0)
	await _wait(3.5)

	await _say(&"SPEAKER_CONDUCTOR", &"BUS_CONDUCTOR_ASK")
	await _say(&"SPEAKER_AN", &"BUS_AN_ANSWER")
	await _wait(0.8)
	await _say(&"SPEAKER_CONDUCTOR", &"BUS_CONDUCTOR_PAUSE")
	await _say(&"SPEAKER_CONDUCTOR", &"BUS_CONDUCTOR_LAST")
	await _wait(3.0)

	await _say(&"SPEAKER_OLD_WOMAN", &"BUS_OLD_WOMAN_ASK")
	await _say(&"SPEAKER_AN", &"BUS_AN_OLD_HOUSE")
	await _wait(1.0)
	await _say(&"SPEAKER_OLD_WOMAN", &"BUS_OLD_WOMAN_RIVER")
	await _say_monologue(&"BUS_MONO_RIVER")
	await _say(&"SPEAKER_OLD_WOMAN", &"BUS_OLD_WOMAN_SLEEP")
	await _wait(2.0)


# --- 3. BUỒN NGỦ VÀ THIẾP ĐI -----------------------------------------------------

func _play_drowsy() -> void:
	_set_state(State.DROWSY)
	_riding = true
	level.set_moving(true, true)
	if not _engine.playing:
		_play(_engine, -6.0)
	await _say_monologue(&"BUS_MONO_DROWSY")

	# Ba lần chớp mắt, mỗi lần nhắm lâu hơn, nhìn mờ hơn.
	for i in 3:
		if not is_inside_tree():
			return
		var close_time := 0.7 + i * 0.5
		EventBus.screen_effect_requested.emit(&"blur", 1.0 + i * 1.0, close_time)
		EventBus.screen_effect_requested.emit(&"vignette", 0.25 + i * 0.15, close_time)
		EventBus.screen_effect_requested.emit(&"eyes_open", 0.08, close_time)
		await _wait(close_time + 0.25 + i * 0.5)
		EventBus.screen_effect_requested.emit(&"eyes_open", 1.0 - i * 0.2, 0.5)
		if i == 1:
			_monologue(&"BUS_MONO_FIGHT")
		await _wait(2.6 - i * 0.6)

	# Mí mắt sụp hẳn.
	_set_state(State.ASLEEP)
	EventBus.player_controls_locked.emit(true)
	EventBus.subtitles_cleared.emit()
	EventBus.screen_effect_requested.emit(&"eyes_open", 0.0, 2.5)
	EventBus.screen_effect_requested.emit(&"blur", 4.0, 2.5)
	_fade_audio(_engine, -40.0, 5.0, true)
	await _wait(2.4)
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 0.6)
	await _wait(2.8)
	_riding = false
	EventBus.subtitle_requested.emit(tr(&"SPEAKER_UNKNOWN"), tr(&"BUS_WHISPER_ARRIVED"), 2.8)
	await _wait(3.6)


# --- 4. TỈNH DẬY TRÊN XE HOANG ---------------------------------------------------

func _play_wake() -> void:
	_set_state(State.DERELICT)
	_riding = false
	EventBus.player_controls_locked.emit(true)
	EventBus.subtitles_cleared.emit()
	_engine.stop()
	_station.stop()
	level.set_derelict(true)
	level.set_moving(false, true)
	_set_derelict_interactables(true)
	_player.head.rotation.z = 0.0
	_player.head.position.y = seated_head_height
	_play(_derelict_amb, -8.0)

	EventBus.screen_effect_requested.emit(&"eyes_open", 0.0, 0.0)
	EventBus.screen_effect_requested.emit(&"blur", 4.0, 0.0)
	EventBus.screen_effect_requested.emit(&"vignette", 0.55, 0.0)
	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 0.8)
	# Mí mắt hé mở chập chờn, mờ nhòe tan dần.
	for step: Vector2 in [Vector2(0.35, 1.3), Vector2(0.12, 0.5), Vector2(0.7, 1.6), Vector2(1.0, 1.2)]:
		EventBus.screen_effect_requested.emit(&"eyes_open", step.x, step.y)
		await _wait(step.y + 0.1)
	EventBus.screen_effect_requested.emit(&"blur", 0.3, 3.5)
	EventBus.screen_effect_requested.emit(&"vignette", 0.35, 4.0)
	EventBus.subtitle_requested.emit("", tr(&"BUS_CAPTION_SILENCE"), 3.5)
	EventBus.camera_shake_requested.emit(0.004, 3.0)
	await _wait(2.0)
	# Cho nhìn quanh trước khi đứng dậy.
	EventBus.player_controls_locked.emit(false)
	await _say_monologue(&"BUS_MONO_WAKE")
	await _say_monologue(&"BUS_MONO_DERELICT")
	if not is_inside_tree():
		return
	await _stand_up()
	if not is_inside_tree():
		return
	EventBus.screen_effect_requested.emit(&"blur", 0.0, 2.0)
	EventBus.objective_updated.emit(tr(&"OBJ_SEARCH_BUS"), true)


func _stand_up() -> void:
	EventBus.player_controls_locked.emit(true)
	var start_yaw := _player.rotation.y
	var target_yaw := deg_to_rad(stand_yaw_degrees)
	if _motion_tween:
		_motion_tween.kill()
	_motion_tween = create_tween().set_parallel().set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_motion_tween.tween_property(_player, "global_position", stand_position, 1.6)
	_motion_tween.tween_method(func(t: float) -> void: _player.rotation.y = lerp_angle(start_yaw, target_yaw, t),
			0.0, 1.0, 1.4)
	_motion_tween.tween_property(_player.head, "position:y", STANDING_HEAD_Y, 1.6)
	_motion_tween.tween_property(_player.head, "rotation:x", 0.0, 1.2)
	await _motion_tween.finished
	if not is_inside_tree():
		return
	_player.movement_locked = false
	_player.set_physics_process(true)
	_set_hotbar_visible(true)
	EventBus.player_controls_locked.emit(false)


# --- 5. CỬA XE KẸT VÀ BÓNG NGƯỜI NGOÀI CỬA KÍNH -----------------------------------

func _on_bus_door_interacted(_actor: Node) -> void:
	if state < State.DERELICT:
		return
	EventBus.camera_shake_requested.emit(0.015, 0.4)
	if _door_tried:
		_monologue(&"BUS_MONO_DOOR_JAMMED")
		return
	_door_tried = true
	_play_apparition()


func _play_apparition() -> void:
	_monologue(&"BUS_MONO_DOOR_JAMMED")
	await _wait(2.2)
	if not is_inside_tree():
		return
	# Mất điện, bóng người hiện ngoài ô kính cửa trong một nhịp đèn, rồi biến mất.
	level.set_power(false)
	EventBus.subtitles_cleared.emit()
	await _wait(1.1)
	if apparition:
		apparition.visible = true
	level.set_power(true)
	if _stinger.stream:
		_stinger.play()
	EventBus.camera_shake_requested.emit(0.03, 0.5)
	EventBus.screen_effect_requested.emit(&"vignette", 0.8, 0.15)
	await _wait(0.45)
	level.set_power(false)
	if apparition:
		apparition.visible = false
	await _wait(0.9)
	level.set_power(true)
	EventBus.screen_effect_requested.emit(&"vignette", 0.35, 2.0)
	await _say_monologue(&"BUS_MONO_WHO")
	if not is_inside_tree():
		return
	_set_state(State.TRAPPED)
	EventBus.objective_updated.emit(tr(&"OBJ_ESCAPE_BUS"), true)
	GameManager.set_flag(&"bus_trapped")


func _on_item_picked_up(item: ItemData, _slot: int) -> void:
	if item != null and item.id == ticket_item_id:
		_ticket_pending = true


func _on_document_closed() -> void:
	if not _ticket_pending:
		return
	_ticket_pending = false
	_monologue(&"BUS_MONO_TICKET")


# --- Tiện ích ----------------------------------------------------------------------

func _set_state(new_state: State) -> void:
	state = new_state
	EventBus.bus_state_changed.emit(new_state)


func _set_derelict_interactables(on: bool) -> void:
	for node in derelict_interactables:
		if node == null:
			continue
		node.visible = on
		node.enabled = on
	if bus_door:
		bus_door.enabled = on


## Ẩn Hotbar khi An ngồi trên xe (phụ đề hội thoại nằm đúng chỗ Hotbar).
func _set_hotbar_visible(value: bool) -> void:
	var hud := _player.get_node_or_null(^"HUD") as HUD if _player else null
	if hud:
		hud.set_hotbar_visible(value)


func _line_duration(text: String) -> float:
	return maxf(min_line_seconds, text.length() * seconds_per_char)


## Câu thoại có người nói, hiện dạng phụ đề.
func _say(speaker_key: StringName, text_key: StringName) -> void:
	var text := tr(text_key)
	var duration := _line_duration(text)
	EventBus.subtitle_requested.emit(tr(speaker_key), text, duration)
	await _wait(duration + line_gap, allow_skip)


## Độc thoại nội tâm, không chờ. Trả về thời lượng hiển thị.
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


func _play(player: AudioStreamPlayer, volume_db: float) -> void:
	if player.stream == null:
		return
	player.volume_db = volume_db
	player.play()


func _fade_audio(player: AudioStreamPlayer, to_db: float, duration: float, stop_after: bool) -> void:
	if not player.playing:
		return
	var tween := create_tween()
	tween.tween_property(player, "volume_db", to_db, duration)
	if stop_after:
		tween.tween_callback(player.stop)
	_audio_tweens.append(tween)
