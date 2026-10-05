## Đạo diễn chương "Chuyến xe không về bến": từ lúc An bị nhốt trong xác xe đến khi
## giải hết chấp niệm của chuyến xe đêm 14/04/1999 và tỉnh lại trên xe thật năm 2006.
##
## Ba lớp xe (xem [BusLevel]): xe thật 2006 (Day), xác xe (Derelict), Đêm 1999 (Night).
## Đèn bão là cánh cửa giữa xác xe và Đêm 1999:
## - Ở xác xe bấm F thổi tắt đèn -> sang Đêm 1999. Ở Đêm 1999 bấm F quẹt diêm châm lại -> về xác xe.
## - Chỉ đèn bão và lọ diêm theo An qua lại; đồ khác đang cầm tan thành tro (vật quay về chỗ cũ).
## - Dời đồ ở Đêm 1999 thì ở xác xe nó vẫn nằm ở chỗ mới.
## Gợi ý kiểu Áo Cưới Giấy: ký hiệu nhắc nhau, sách dạy luật, Nokia gọi khi kẹt lâu,
## và phím H "Thắp hương hỏi" (lần 1 khoanh vùng, lần 2 cho đáp án).
##
## Đồ vật câu đố nằm trong scenes/bus/BusPuzzles.tscn (sinh bằng tools/bus_puzzles_blockout.py),
## director tìm theo tên node. Chạy thử từng đoạn: đổi [member debug_start] rồi F6 scene BusRide.
class_name BusWreckDirector
extends Node

enum DebugStart {
	OFF,        ## Chơi bình thường từ phân cảnh đi xe.
	DARK,       ## Vừa mất điện trong xác xe, bắt đầu tìm cách thắp sáng.
	LAMP_LIT,   ## Đèn bão đã thắp, cầm trên tay, chưa sang Đêm 1999.
	NIGHT,      ## Đang ở Đêm 1999, hộp bánh quy đã dời, cảnh xe 2006 đã xem.
	DRIVER,     ## Bà Năm, Hùng, chú Bảy đã được giải thoát, còn đánh thức bác Tư.
	FINALE,     ## Chạy luôn đoạn kết (bác Tư tỉnh, xuống bến, tỉnh dậy trên xe 2006).
}

const LAMP_ACTION := &"lamp"
const HINT_ACTION := &"hint"
## Đồ theo An qua lại giữa hai lớp.
const CROSS_LAYER_ITEMS: Array[StringName] = [&"matches", &"bus_ticket_1999"]
## Vật nhặt được -> node gốc (vật quay về chỗ cũ khi tan thành tro lúc đổi lớp).
const PICKUP_ORIGINS := {
	&"kerosene": "Wreck/Kerosene", &"cotton_thread": "Wreck/Thread",
	&"non_coi": "Night/NonCoi", &"goi_thuoc_bac": "Night/ThuocBac", &"dieu_cay": "Night/DieuCay",
	&"biscuit_tin": "Night/Tin", &"paper_clogs": "Night/GlowClogs", &"wind_oil": "Night/WindOil",
	&"pencil": "Night/BayPencil", &"cai_luong_tape": "Night/HungTape",
}
## Sổ phụ xe: ai ngồi ghế nào.
const SEAT_ANSWER := {"03": &"non_coi", "04": &"dieu_cay", "05": &"goi_thuoc_bac"}
const PASSENGER_ITEMS: Array[StringName] = [&"non_coi", &"goi_thuoc_bac", &"dieu_cay"]
## Khóa hộp tôn: số xe 385 (decal dán ngoài kính, nhìn từ trong thành "Ƨ8Ɛ").
const LOCK_CODE: Array[int] = [3, 8, 5]
## Bảng lộ trình: các lựa chọn hiển thị và thứ tự đúng theo băng (chùa -> chợ -> tàu -> đò).
const ROUTE_OPTIONS: Array[StringName] = [&"ROUTE_FERRY", &"ROUTE_MARKET", &"ROUTE_PAGODA", &"ROUTE_TRAIN"]
const ROUTE_ANSWER: Array[int] = [2, 1, 3, 0]
## Vé bù: hàng trên lỗ thứ 8 (ghế 08), hàng giữa bên phải (trẻ em),
## hàng dưới lỗ thứ 5 (Bến Đò, nơi bác Tư dừng đón bé gái; lỗ đầu là bến xe huyện).
const PUNCH_ANSWER: Array[int] = [7, 1, 4]
## Quy ước chuông của nhà xe: 1 hồi có khách xuống, 2 hồi cho xe chạy, 3 hồi dừng gấp.
const BELL_OPTIONS: Array[StringName] = [&"UI_BELL_1", &"UI_BELL_2", &"UI_BELL_3"]
const CLOG_SIZES: Array[StringName] = [&"UI_CLOG_SIZE_CHILD", &"UI_CLOG_SIZE_WOMAN", &"UI_CLOG_SIZE_MAN"]
const NAME_KEYS := {&"tu": &"NAME_TRAN_VAN_TU", &"nam": &"NAME_NAM_CHO_DOAI", &"hung": &"NAME_HUNG"}

@export var ride: BusRideDirector
@export var level: BusLevel
## Gốc scene BusPuzzles (hai nhóm Wreck và Night).
@export var puzzles: Node3D
## Bé gái ngồi ghế 08 ở cuối chương (dùng lại bóng người ngoài cửa kính).
@export var girl: Node3D
@export var debug_start: DebugStart = DebugStart.OFF
## Kẹt quá số giây này không có tiến triển thì chiếc Nokia đổ chuông.
@export var stuck_call_seconds: float = 150.0
## Scene chuyển sang sau màn kết chương (để trống = dừng ở màn chữ).
@export_file("*.tscn") var next_scene: String = ""

@export_group("Đèn bão cầm tay")
@export var held_lamp_offset: Vector3 = Vector3(0.3, -0.36, -0.72)
@export var held_lamp_scale: float = 0.75
@export var lamp_light_energy: float = 1.5
@export var lamp_light_range: float = 6.5
@export var flashlight_energy: float = 0.45

var _active := false
var _busy := false
var _player: PlayerController
var _layer: BusLevel.Layer = BusLevel.Layer.DERELICT
var _wreck: Node3D
var _night: Node3D
var _on: Dictionary[Node, bool] = {}
var _rng := RandomNumberGenerator.new()

# Tiến trình.
var _lamp_state := 0          # 0 quấn bùa, 1 đã gỡ bùa, 2 đã thắp (cầm trên tay)
var _visited_night := false
var _box_open := false
var _matches_taken := false
var _tin_moved := false
var _glimpse_done := false
var _clog_seen := false
var _names: Array[StringName] = []
var _clogs_burned := false
var _nam_shod := false         # bà Năm đã xỏ guốc mã, chờ chuông xin xuống bến
var _nam_freed := false
var _tape_fixed := false
var _hung_freed := false
var _seats_done: Dictionary[String, bool] = {}
var _counted := false
var _footprints_seen := false
var _bay_freed := false
var _tu_step := 0              # 0 đang ngủ, 1 đã xoa dầu gió, 2 đã bật cải lương
var _tick := 0
var _finished := false
## Đồ đang chờ người chơi chọn để trả cho hình nhân hành khách.
var _pending_choice: Array[StringName] = []

# Gợi ý.
var _hint_levels: Dictionary[String, int] = {}
var _called: Dictionary[String, bool] = {}
var _idle := 0.0

# Đèn cầm tay.
var _held_lamp: Node3D
var _held_flame: MeshInstance3D
var _held_light: OmniLight3D
var _held_lit := false
var _flame_time := 0.0
var _flashlight_on := false


func _ready() -> void:
	_rng.randomize()
	if puzzles:
		_wreck = puzzles.get_node_or_null(^"Wreck")
		_night = puzzles.get_node_or_null(^"Night")
		for group: Node in [_wreck, _night]:
			if group == null:
				continue
			for child in group.get_children():
				var target := child as Interactable
				if target:
					_on[target] = target.visible
					target.interacted.connect(_on_interacted.bind(target))
		puzzles.visible = false
	_set_all_enabled(false)
	EventBus.selector_submitted.connect(_on_selector_submitted)


func _exit_tree() -> void:
	if EventBus.selector_submitted.is_connected(_on_selector_submitted):
		EventBus.selector_submitted.disconnect(_on_selector_submitted)


## BusRideDirector hỏi có nhảy thẳng vào đoạn chạy thử không.
func skips_ride() -> bool:
	return debug_start != DebugStart.OFF


func is_active() -> bool:
	return _active


## Bắt đầu chương: gọi sau khi An thấy bóng người ngoài cửa kính.
func begin() -> void:
	if _active:
		return
	_player = level.get_node_or_null(^"Player") as PlayerController if level else null
	if _player == null or puzzles == null:
		push_error("BusWreckDirector: thiếu level/Player hoặc puzzles.")
		return
	_active = true
	puzzles.visible = true
	_build_held_lamp()
	_apply_layer(BusLevel.Layer.DERELICT)
	if debug_start != DebugStart.OFF:
		_apply_debug()
		return
	_play_darkness()


# --- 1. MẤT ĐIỆN, TÌM CÁCH THẮP SÁNG ---------------------------------------------

func _play_darkness() -> void:
	_busy = true
	level.set_power(false)
	var tube := level.get_node_or_null(^"Derelict/TubeLight")
	if tube:
		tube.process_mode = Node.PROCESS_MODE_DISABLED
	await _wait(1.2)
	await _say_monologue(&"BUS2_MONO_DARK")
	_set_flashlight(true)
	EventBus.ui_sfx_requested.emit(&"sfx_flashlight_click")
	await _wait(0.6)
	_busy = false
	EventBus.objective_updated.emit(tr(&"OBJ_FIND_LIGHT"), true)
	_caption(&"BUS2_TIP_HINT", 5.0)


func on_bus_door() -> void:
	if not _active or _busy or _layer != BusLevel.Layer.DERELICT:
		return
	_pull_back_to_seat()


## Cứ ra đến cửa là bị kéo về cạnh ghế 07.
func _pull_back_to_seat() -> void:
	_busy = true
	EventBus.player_controls_locked.emit(true)
	EventBus.camera_shake_requested.emit(0.02, 0.6)
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 0.25)
	await _wait(0.6)
	_player.global_position = ride.stand_position
	_player.rotation.y = deg_to_rad(ride.stand_yaw_degrees)
	_player.velocity = Vector3.ZERO
	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 0.8)
	EventBus.player_controls_locked.emit(false)
	await _say_monologue(&"BUS2_MONO_PULLED_BACK")
	_busy = false


func _on_lamp() -> void:
	var lamp := _area("Wreck/Lamp")
	if _lamp_state == 0:
		_lamp_state = 1
		var talisman := lamp.get_node_or_null(^"Talisman") as Node3D
		if talisman:
			talisman.visible = false
		lamp.prompt_text_key = "PROMPT_LAMP_FIX"
		EventBus.sfx_requested.emit(&"sfx_paper", lamp.global_position)
		_read(&"OBJ_TALISMAN_NAME", [&"DOC_TALISMAN"])
		_progress()
		return
	var missing: PackedStringArray = []
	if not Inventory.has_item(&"kerosene"):
		missing.append(tr(&"BUS2_NEED_OIL"))
	if not Inventory.has_item(&"cotton_thread"):
		missing.append(tr(&"BUS2_NEED_WICK"))
	if not Inventory.has_item(&"matches"):
		missing.append(tr(&"BUS2_NEED_FIRE"))
	if not missing.is_empty():
		_monologue_text(tr(&"BUS2_MONO_LAMP_NEED").format({"list": ", ".join(missing)}))
		return
	_light_lamp()


func _light_lamp() -> void:
	_busy = true
	_remove_item(&"kerosene")
	_remove_item(&"cotton_thread")
	_set_on(_area("Wreck/Lamp"), false)
	_lamp_state = 2
	_progress()
	await _say_monologue(&"BUS2_MONO_LAMP_ASSEMBLE")
	EventBus.ui_sfx_requested.emit(&"sfx_match_strike")
	_set_flashlight(false)
	_set_held_lamp(true, true)
	EventBus.screen_fade_requested.emit(Color(1.0, 0.6, 0.25), 0.5, 0.08)
	await _wait(0.12)
	EventBus.screen_fade_requested.emit(Color(1.0, 0.6, 0.25), 0.0, 0.8)
	await _say_monologue(&"BUS2_MONO_LAMP_LIT")
	await _wait(0.6)
	EventBus.subtitle_requested.emit(tr(&"SPEAKER_UNKNOWN"), tr(&"BUS2_WHISPER_BLOW"), 3.0)
	await _wait(3.2)
	EventBus.objective_updated.emit(tr(&"OBJ_BLOW_LAMP"), true)
	_caption(&"BUS2_TIP_LAMP", 6.0)
	_busy = false


func _on_tin_box() -> void:
	if not _box_open:
		var rows: Array = []
		for i in 3:
			rows.append({"label": tr(&"UI_DIAL").format({"n": i + 1}),
					"options": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]})
		EventBus.selector_requested.emit(&"tin_box", tr(&"UI_TIN_BOX_TITLE"), rows, LOCK_CODE.duplicate(), false)
		return
	_learn_name(&"tu")
	if not _matches_taken:
		_take_matches()


func _open_tin_box() -> void:
	_box_open = true
	_progress()
	var box := _area("Wreck/TinBox")
	var lid := box.get_node_or_null(^"Lid") as Node3D
	if lid:
		create_tween().tween_property(lid, "rotation:x", deg_to_rad(-105.0), 0.6).set_trans(Tween.TRANS_BACK)
	var contents := box.get_node_or_null(^"Contents") as Node3D
	if contents:
		contents.visible = true
	EventBus.sfx_requested.emit(&"sfx_tin_lid", box.global_position)
	var docs: Array[String] = ["DOC_DRIVER_LICENSE", "DOC_CONDUCTOR_LEDGER"]
	box.pages = docs
	box.prompt_text_key = "PROMPT_TIN_BOX_READ"
	await _wait(0.7)
	_take_matches()
	_learn_name(&"tu")
	_read(&"OBJ_DRIVER_TIN_BOX_NAME", [&"DOC_DRIVER_LICENSE", &"DOC_CONDUCTOR_LEDGER"])
	await EventBus.document_closed
	_monologue(&"BUS2_MONO_LEDGER_HAND")


func _take_matches() -> void:
	if _give(&"matches", &"ITEM_MATCHES_NAME", &"ITEM_MATCHES_DESC"):
		_matches_taken = true
		var jar := _area("Wreck/TinBox").get_node_or_null(^"Contents/MatchJar") as Node3D
		if jar:
			jar.visible = false
		_monologue(&"BUS2_MONO_MATCHES")


# --- 2. ĐÊM 1999: THỔI TẮT / THẮP LẠI ĐÈN ------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	if not _active or _busy or _finished or _player == null or _player.controls_locked:
		return
	if event.is_action_pressed(LAMP_ACTION):
		get_viewport().set_input_as_handled()
		if _lamp_state < 2:
			return
		if _layer == BusLevel.Layer.DERELICT:
			_blow_out()
		elif _layer == BusLevel.Layer.NIGHT:
			_relight()
	elif event.is_action_pressed(HINT_ACTION):
		get_viewport().set_input_as_handled()
		_show_incense_hint()


func _blow_out() -> void:
	_busy = true
	EventBus.player_controls_locked.emit(true)
	EventBus.ui_sfx_requested.emit(&"sfx_lamp_blow")
	if _held_flame:
		create_tween().tween_property(_held_flame, "scale", Vector3(0.2, 0.05, 0.2), 0.35)
	EventBus.screen_effect_requested.emit(&"vignette", 0.95, 0.4)
	EventBus.screen_effect_requested.emit(&"blur", 2.5, 0.4)
	EventBus.screen_fade_requested.emit(Color(0.01, 0.05, 0.04), 1.0, 0.45)
	await _wait(0.7)
	var vanished := _apply_layer(BusLevel.Layer.NIGHT)
	EventBus.screen_fade_requested.emit(Color(0.01, 0.05, 0.04), 0.0, 1.1)
	EventBus.screen_effect_requested.emit(&"blur", 0.0, 1.5)
	EventBus.screen_effect_requested.emit(&"vignette", 0.45, 1.5)
	EventBus.ui_sfx_requested.emit(&"sfx_heartbeat")
	EventBus.player_controls_locked.emit(false)
	if not _visited_night:
		_visited_night = true
		_progress()
		await _wait(1.0)
		await _say_monologue(&"BUS2_MONO_NIGHT_1")
		await _say_monologue(&"BUS2_MONO_NIGHT_2")
		_update_free_objective(true)
	elif vanished:
		_monologue(&"BUS2_MONO_ASH_HANDS")
	_busy = false


func _relight() -> void:
	_busy = true
	EventBus.player_controls_locked.emit(true)
	EventBus.ui_sfx_requested.emit(&"sfx_match_strike")
	await _wait(0.35)
	if _tin_moved and not _glimpse_done:
		await _play_glimpse()
		EventBus.player_controls_locked.emit(false)
		_busy = false
		return
	EventBus.screen_fade_requested.emit(Color(1.0, 0.62, 0.3), 0.85, 0.12)
	await _wait(0.2)
	var vanished := _apply_layer(BusLevel.Layer.DERELICT)
	EventBus.screen_effect_requested.emit(&"blur", 1.5, 0.0)
	EventBus.screen_effect_requested.emit(&"blur", 0.0, 1.2)
	EventBus.screen_fade_requested.emit(Color(1.0, 0.62, 0.3), 0.0, 0.9)
	EventBus.player_controls_locked.emit(false)
	if vanished:
		_monologue(&"BUS2_MONO_ASH_HANDS")
	_busy = false


## Đổi lớp xe. Trả về true nếu có đồ trên tay tan thành tro.
func _apply_layer(to: BusLevel.Layer) -> bool:
	var vanished := false
	if _active and to != _layer:
		vanished = _vanish_layer_items()
	_layer = to
	level.set_layer(to)
	if _wreck:
		_wreck.visible = to == BusLevel.Layer.DERELICT
	if _night:
		_night.visible = to == BusLevel.Layer.NIGHT
	if ride:
		ride.set_derelict_interactables(to == BusLevel.Layer.DERELICT)
		ride.set_derelict_ambience(to == BusLevel.Layer.DERELICT)
	_refresh_enabled()
	if _lamp_state >= 2:
		_set_held_lamp(true, to == BusLevel.Layer.DERELICT)
	return vanished


func _vanish_layer_items() -> bool:
	var vanished := false
	for i in Inventory.SLOT_COUNT:
		var item := Inventory.get_item(i)
		if item == null or item.id in CROSS_LAYER_ITEMS:
			continue
		Inventory.remove_item(i)
		vanished = true
		if PICKUP_ORIGINS.has(item.id):
			_set_on(_area(PICKUP_ORIGINS[item.id]), true)
	return vanished


# --- 2b. CẢNH XE 2006 (MỘT LẦN) ------------------------------------------------------

func _play_glimpse() -> void:
	_glimpse_done = true
	EventBus.screen_fade_requested.emit(Color(1.0, 0.85, 0.6), 1.0, 0.25)
	if _held_flame:
		create_tween().tween_property(_held_flame, "scale", Vector3(2.2, 2.6, 2.2), 0.3)
	await _wait(0.4)
	var saved := _player.global_transform
	var saved_pitch := _player.head.rotation.x
	_vanish_layer_items()
	level.set_layer(BusLevel.Layer.DAY)
	level.set_moving(false, true)
	level.set_glimpse(true)
	puzzles.visible = false
	_set_all_enabled(false)
	ride.set_derelict_interactables(false)
	ride.set_derelict_ambience(false)
	_player.global_position = Vector3(0.05, 0.05, 1.0)
	_player.rotation.y = 0.0
	_player.head.rotation.x = deg_to_rad(-16.0)
	_player.movement_locked = true
	var driver_head := level.get_node_or_null(^"Day/Passengers/Driver/Upper/Head") as Node3D
	var engine := _make_player(&"amb_bus_engine", -10.0, 0.32)
	EventBus.screen_effect_requested.emit(&"blur", 1.4, 0.0)
	EventBus.screen_effect_requested.emit(&"vignette", 0.7, 0.0)
	EventBus.screen_fade_requested.emit(Color(1.0, 0.85, 0.6), 0.25, 1.4)
	EventBus.player_controls_locked.emit(false)
	_caption(&"BUS2_CAPTION_GLIMPSE", 4.0)
	if driver_head:
		create_tween().tween_property(driver_head, "rotation:x", deg_to_rad(28.0), 6.0)
	await _wait(1.5)
	for key: StringName in [&"BUS2_MONO_GLIMPSE_1", &"BUS2_MONO_GLIMPSE_2", &"BUS2_MONO_GLIMPSE_3",
			&"BUS2_MONO_GLIMPSE_4"]:
		await _say_monologue(key)
	EventBus.player_controls_locked.emit(true)
	EventBus.screen_fade_requested.emit(Color(1.0, 0.62, 0.3), 1.0, 0.5)
	await _wait(0.6)
	if engine:
		engine.queue_free()
	if driver_head:
		driver_head.rotation.x = 0.0
	level.set_glimpse(false)
	level.set_old_woman_gone(false)
	puzzles.visible = true
	_player.global_transform = saved
	_player.head.rotation.x = saved_pitch
	_player.movement_locked = false
	if _held_flame:
		_held_flame.scale = Vector3.ONE
	_apply_layer(BusLevel.Layer.DERELICT)
	EventBus.screen_effect_requested.emit(&"blur", 0.0, 1.5)
	EventBus.screen_effect_requested.emit(&"vignette", 0.35, 1.5)
	EventBus.screen_fade_requested.emit(Color(1.0, 0.62, 0.3), 0.0, 1.2)
	await _wait(1.0)
	await _say_monologue(&"BUS2_MONO_GLIMPSE_AFTER")
	_progress()


# --- 2.1 HỘP BÁNH QUY / 3. BÀ NĂM VÀ ĐÔI GUỐC MÃ -------------------------------------

func _on_rack() -> void:
	if _tin_moved:
		_monologue(&"BUS2_MONO_RACK_DONE")
		return
	if not Inventory.has_item(&"biscuit_tin"):
		_monologue(&"BUS2_MONO_RACK")
		return
	_remove_item(&"biscuit_tin")
	_tin_moved = true
	var rack := _area("Night/Rack")
	var placed := rack.get_node_or_null(^"Placed") as Node3D
	if placed:
		placed.visible = true
	EventBus.sfx_requested.emit(&"sfx_tin_lid", rack.global_position)
	_set_on(_area("Night/Tin"), false)
	_set_on(_area("Wreck/TinRusted"), false)
	_set_on(_area("Wreck/TinDry"), true)
	_monologue(&"BUS2_MONO_TIN_PLACED")
	_progress()


func _on_tin_dry() -> void:
	if not _clogs_burned and not Inventory.has_item(&"paper_kit"):
		_give(&"paper_kit", &"ITEM_PAPER_KIT_NAME", &"ITEM_PAPER_KIT_DESC")
	_progress()


func _on_basin() -> void:
	if _clogs_burned:
		_monologue(&"BUS2_MONO_BASIN_DONE")
		return
	if not Inventory.has_item(&"paper_kit"):
		_monologue(&"BUS2_MONO_BASIN")
		return
	if not Inventory.has_item(&"matches"):
		_monologue(&"BUS2_MONO_BASIN_NO_FIRE")
		return
	if _names.is_empty():
		_monologue(&"BUS2_MONO_NEED_NAME")
		return
	var sizes: Array[String] = []
	for key in CLOG_SIZES:
		sizes.append(tr(key))
	var names: Array[String] = []
	for id in _names:
		names.append(tr(NAME_KEYS[id]))
	var nam_index := _names.find(&"nam")
	var rows: Array = [
		{"label": tr(&"UI_CLOG_SIZE"), "options": sizes},
		{"label": tr(&"UI_CLOG_NAME"), "options": names},
	]
	EventBus.selector_requested.emit(&"burn_clogs", tr(&"UI_BURN_TITLE"), rows, [1, nam_index], true)


func _burn_clogs(correct: bool) -> void:
	_busy = true
	_remove_item(&"paper_kit")
	var basin := _area("Wreck/Basin")
	var fire := basin.get_node_or_null(^"Fire") as Node3D
	EventBus.sfx_requested.emit(&"sfx_paper_burn", basin.global_position)
	if fire:
		fire.visible = true
	await _say_monologue(&"BUS2_MONO_BURNING")
	await _wait(1.5)
	if fire:
		fire.visible = false
	if correct:
		_clogs_burned = true
		_set_on(_area("Night/GlowClogs"), true)
		await _say_monologue(&"BUS2_MONO_BURN_OK")
		_progress()
	else:
		await _say_monologue(&"BUS2_MONO_BURN_WRONG")
	_busy = false


func _on_nam() -> void:
	if _nam_shod:
		_monologue(&"BUS2_MONO_NAM_WAITING")
		return
	if not Inventory.has_item(&"paper_clogs"):
		_monologue(&"BUS2_MONO_NAM_BAREFOOT")
		return
	_remove_item(&"paper_clogs")
	_shoe_nam()


## Bà Năm xỏ guốc mã, nhưng còn một nút nữa: bà lỡ bến vì chú Bảy quên giật chuông.
func _shoe_nam() -> void:
	_busy = true
	_nam_shod = true
	_progress()
	var effigy := _night.get_node_or_null(^"BaNam") as Node3D
	_add_glow_clogs(effigy)
	_caption(&"BUS2_CAPTION_NAM_MOVES", 3.0)
	_look_at_player(effigy, 2.5)
	await _wait(2.6)
	await _say(&"SPEAKER_NAM", &"BUS2_NAM_MISSED_STOP")
	_busy = false


## Một hồi chuông xin xuống bến: bà Năm đứng dậy xuống xe, để lại lọ dầu gió cho bác Tư.
func _free_nam() -> void:
	_busy = true
	_nam_freed = true
	_progress()
	_set_on(_area("Night/Nam"), false)
	_set_on(_area("Night/Hat"), false)
	var effigy := _night.get_node_or_null(^"BaNam") as Node3D
	_caption(&"BUS2_CAPTION_NAM_GETS_OFF", 3.0)
	_look_at_player(effigy, 2.5)
	await _wait(2.6)
	await _say(&"SPEAKER_NAM", &"BUS2_NAM_THANKS")
	await _burn_effigy(effigy)
	_set_on(_area("Night/WindOil"), true)
	_monologue(&"BUS2_MONO_WIND_OIL")
	_update_free_objective(false)
	_busy = false


## Đôi guốc giấy hiện dưới chân bà Năm.
func _add_glow_clogs(effigy: Node3D) -> void:
	if effigy == null:
		return
	var source := _area("Night/GlowClogs")
	for child in source.get_children():
		if child is MeshInstance3D:
			var copy := child.duplicate() as MeshInstance3D
			effigy.add_child(copy)
			copy.position = Vector3(copy.position.x, 0.035, -0.4)


# --- 4. HÙNG VÀ CHIẾC ĐÀI ĂN BĂNG ---------------------------------------------------

func _on_deck() -> void:
	if _tape_fixed:
		_play_tape(false)
		return
	var has_pencil := Inventory.has_item(&"pencil")
	var has_tape := Inventory.has_item(&"sticky_tape")
	if not (has_pencil and has_tape):
		var key := &"BUS2_MONO_DECK_JAMMED"
		if has_pencil:
			key = &"BUS2_MONO_DECK_NEED_TAPE"
		elif has_tape:
			key = &"BUS2_MONO_DECK_NEED_PENCIL"
		_monologue(key)
		return
	_remove_item(&"pencil")
	_remove_item(&"sticky_tape")
	_tape_fixed = true
	_progress()
	var tangle := _area("Night/Deck").get_node_or_null(^"Tangle") as Node3D
	if tangle:
		tangle.visible = false
	_play_tape(true)


func _play_tape(first_time: bool) -> void:
	_busy = true
	var deck := _area("Night/Deck")
	if first_time:
		await _say_monologue(&"BUS2_MONO_TAPE_FIX")
		_caption(&"BUS2_CAPTION_PLAY", 2.5)
		await _wait(2.6)
	var at := deck.global_position
	for pair: Array in [[&"sfx_tape_hiss", &"BUS2_CAPTION_HISS"], [&"sfx_temple_bell", &"BUS2_CAPTION_BELL"],
			[&"sfx_market", &"BUS2_CAPTION_MARKET"], [&"sfx_train_horn", &"BUS2_CAPTION_TRAIN"],
			[&"sfx_ferry_water", &"BUS2_CAPTION_FERRY"], [&"sfx_tape_hiss", &"BUS2_CAPTION_TAPE_END"]]:
		EventBus.sfx_requested.emit(pair[0], at)
		_caption(pair[1], 2.6)
		await _wait(2.9)
	if first_time:
		await _say_monologue(&"BUS2_MONO_TAPE_ORDER")
	_busy = false


func _on_board() -> void:
	if not _tape_fixed:
		_monologue(&"BUS2_MONO_BOARD")
		return
	var options: Array[String] = []
	for key in ROUTE_OPTIONS:
		options.append(tr(key))
	var rows: Array = []
	for i in 4:
		rows.append({"label": tr(&"UI_ROUTE_SLOT").format({"n": i + 1}), "options": options})
	EventBus.selector_requested.emit(&"route", tr(&"UI_ROUTE_TITLE"), rows, ROUTE_ANSWER.duplicate(), false)


func _free_hung() -> void:
	_busy = true
	_hung_freed = true
	_progress()
	_set_on(_area("Night/Board"), false)
	_set_on(_area("Night/Plaques"), false)
	_set_on(_area("Night/Deck"), false)
	_set_on(_area("Night/Schoolbag"), false)
	var plaques := _night.get_node_or_null(^"BoardPlaques") as Node3D
	if plaques:
		plaques.visible = true
	var at := _area("Night/Deck").global_position
	EventBus.sfx_requested.emit(&"sfx_tape_hiss", at)
	_caption(&"BUS2_CAPTION_TAPE_CONTINUES", 2.5)
	await _wait(2.6)
	await _say(&"SPEAKER_HUNG", &"BUS2_HUNG_MESSAGE")
	_caption(&"BUS2_CAPTION_YAWN", 2.5)
	await _wait(2.6)
	await _say(&"SPEAKER_TU", &"BUS2_TU_YAWN")
	EventBus.sfx_requested.emit(&"sfx_brake_screech", at)
	_caption(&"BUS2_CAPTION_SCREAM", 2.5)
	EventBus.camera_shake_requested.emit(0.02, 0.6)
	await _wait(2.8)
	var effigy := _night.get_node_or_null(^"Hung") as Node3D
	EventBus.sfx_requested.emit(&"sfx_tape_eject", at)
	_caption(&"BUS2_CAPTION_EJECT", 2.5)
	_look_at_player(effigy, 2.0)
	await _wait(2.6)
	await _say(&"SPEAKER_HUNG", &"BUS2_HUNG_RETURN")
	await _burn_effigy(effigy)
	_set_on(_area("Night/HungTape"), true)
	_monologue(&"BUS2_MONO_TAPE_LEFT")
	await _wait(3.0)
	await _say_monologue(&"BUS2_MONO_THREE_STEPS")
	_update_free_objective(false)
	_busy = false


# --- 5. CHÚ BẢY ĐẾM KHÁCH -------------------------------------------------------------

func _on_passenger(num: String) -> void:
	if _seats_done.get(num, false):
		_monologue(&"BUS2_MONO_PASSENGER_SETTLED")
		return
	var held: Array[StringName] = []
	for id in PASSENGER_ITEMS:
		if Inventory.has_item(id):
			held.append(id)
	if held.is_empty():
		_monologue_text(tr(&"BUS2_MONO_PASSENGER").format({"n": num}))
		return
	if held.size() == 1:
		_give_passenger(num, held[0])
		return
	var names: Array[String] = []
	for id in held:
		names.append(_item_name(id))
	_pending_choice = held
	EventBus.selector_requested.emit(StringName("give_" + num), tr(&"UI_GIVE_TITLE").format({"n": num}),
			[{"label": tr(&"UI_GIVE_ITEM"), "options": names}], [], false)


func _give_passenger(num: String, id: StringName) -> void:
	_remove_item(id)
	var effigy := _night.get_node_or_null(NodePath("Passenger" + num)) as Node3D
	if SEAT_ANSWER[num] == id:
		_seats_done[num] = true
		var held := effigy.get_node_or_null(NodePath("Held/" + String(id))) as Node3D if effigy else null
		if held:
			held.visible = true
		EventBus.sfx_requested.emit(&"sfx_paper", effigy.global_position if effigy else Vector3.ZERO)
		_progress()
		if _seats_done.size() >= SEAT_ANSWER.size():
			_play_bay_count()
		else:
			_monologue(&"BUS2_MONO_PASSENGER_OK")
		return
	# Đặt sai: hình nhân buông đồ xuống sàn rồi quay đầu nhìn An.
	_set_on(_area(PICKUP_ORIGINS[id]), true)
	EventBus.sfx_requested.emit(&"sfx_drop", effigy.global_position if effigy else Vector3.ZERO)
	_look_at_player(effigy, 3.0)
	_monologue(&"BUS2_MONO_PASSENGER_WRONG")


func _play_bay_count() -> void:
	_busy = true
	var bay := _night.get_node_or_null(^"Bay") as Node3D
	await _wait(0.8)
	_caption(&"BUS2_CAPTION_BAY_COUNTS", 2.5)
	await _wait(2.6)
	await _say(&"SPEAKER_BAY", &"BUS2_BAY_COUNT")
	await _say(&"SPEAKER_BAY", &"BUS2_BAY_EXTRA")
	var seat08 := _area("Night/Seat08")
	if bay and seat08:
		_turn_head_towards(bay.get_node_or_null(^"Head") as Node3D, seat08.global_position, 0.8)
	_counted = true
	_progress()
	await _say_monologue(&"BUS2_MONO_SEAT08_HINT")
	_busy = false


func _on_bay() -> void:
	if not _counted:
		_say(&"SPEAKER_BAY", &"BUS2_BAY_BLOCK")
	else:
		_say(&"SPEAKER_BAY", &"BUS2_BAY_TICKET")


func _on_satchel() -> void:
	if not _counted:
		_monologue(&"BUS2_MONO_SATCHEL")
		return
	var rows: Array = [
		{"label": tr(&"UI_PUNCH_TOP"), "options": _hole_rows(9)},
		{"label": tr(&"UI_PUNCH_BOTTOM"), "options": ["●   ○", "○   ●"]},
		{"label": tr(&"UI_PUNCH_STOP"), "options": _hole_rows(5)},
	]
	EventBus.selector_requested.emit(&"punch", tr(&"UI_PUNCH_TITLE"), rows, PUNCH_ANSWER.duplicate(), false)


## Các lựa chọn một hàng lỗ bấm: lỗ thứ i được bấm (●), còn lại để trống (○).
func _hole_rows(count: int) -> Array[String]:
	var options: Array[String] = []
	for i in count:
		var holes := PackedStringArray()
		for j in count:
			holes.append("●" if j == i else "○")
		options.append(" ".join(holes))
	return options


func _free_bay() -> void:
	_busy = true
	_bay_freed = true
	_progress()
	for path in ["Night/BayBody", "Night/Satchel", "Night/Stubs"]:
		_set_on(_area(path), false)
	var bay := _night.get_node_or_null(^"Bay") as Node3D
	EventBus.sfx_requested.emit(&"sfx_ticket_punch", bay.global_position if bay else Vector3.ZERO)
	_caption(&"BUS2_CAPTION_PUNCH", 2.5)
	await _wait(2.6)
	await _say(&"SPEAKER_BAY", &"BUS2_BAY_RELEASE")
	await _say(&"SPEAKER_BAY", &"BUS2_BAY_PENCIL")
	_turn_head_towards(bay.get_node_or_null(^"Head") as Node3D if bay else null,
			_area("Night/Seat08").global_position, 0.6)
	await _say(&"SPEAKER_BAY", &"BUS2_BAY_NOT_OURS")
	await _burn_effigy(bay)
	_set_on(_area("Night/BayPencil"), true)
	_monologue(&"BUS2_MONO_PENCIL_LEFT")
	_update_free_objective(false)
	_busy = false


# --- 6. ĐÁNH THỨC BÁC TƯ -----------------------------------------------------------

func _on_tu() -> void:
	if _tu_step >= 1:
		_monologue(&"BUS2_MONO_TU_STIRRING")
		return
	if not Inventory.has_item(&"wind_oil"):
		_monologue(&"BUS2_MONO_TU_ASLEEP")
		return
	_remove_item(&"wind_oil")
	_tu_step = 1
	_progress()
	EventBus.sfx_requested.emit(&"sfx_cloth", _area("Night/TuBody").global_position)
	_caption(&"BUS2_CAPTION_WIND_OIL", 3.0)
	_nudge_time(1)


## Đài cát-sét trên taplô: lắp cuộn băng Hùng trả lại để cải lương cất lên.
func _on_dash_deck() -> void:
	if _tu_step >= 2:
		_monologue(&"BUS2_MONO_OPERA_DONE")
		return
	if not Inventory.has_item(&"cai_luong_tape"):
		_monologue(&"BUS2_MONO_DASH_EMPTY")
		return
	if _tu_step < 1:
		_wrong_order()
		return
	_remove_item(&"cai_luong_tape")
	_tu_step = 2
	_progress()
	var deck := _area("Night/DashDeck")
	EventBus.sfx_requested.emit(&"sfx_cai_luong", deck.global_position if deck else Vector3.ZERO)
	_caption(&"BUS2_CAPTION_OPERA", 3.5)
	_nudge_time(1)


func _on_bell_rope() -> void:
	if not _bay_freed:
		_monologue(&"BUS2_MONO_ROPE_HELD")
		return
	var options: Array[String] = []
	for key in BELL_OPTIONS:
		options.append(tr(key))
	EventBus.selector_requested.emit(&"bell", tr(&"UI_BELL_TITLE"),
			[{"label": tr(&"UI_BELL_COUNT"), "options": options}], [], false)


## Giật [param count] hồi chuông theo quy ước của nhà xe.
func _ring_bell(count: int) -> void:
	if count == 3 and _tu_step >= 2:
		_play_finale()
		return
	_busy = true
	var at := _area("Night/BellRope").global_position
	for i in count:
		EventBus.sfx_requested.emit(&"sfx_bus_bell", at)
		_caption(&"BUS2_CAPTION_BELL_RING", 1.0)
		await _wait(1.1)
	_busy = false
	match count:
		1:
			if _nam_shod and not _nam_freed:
				_free_nam()
			else:
				_monologue(&"BUS2_MONO_BELL_NOBODY")
		2:
			_monologue(&"BUS2_MONO_BELL_TWO")
		_:
			_wrong_order()


## Sai thứ tự đánh thức bác Tư: thời gian giật lùi một giây, các hình nhân quay đầu nhìn An.
func _wrong_order() -> void:
	_caption(&"BUS2_CAPTION_WRONG_BELL", 3.0)
	_nudge_time(-1)
	for path in ["Passenger03", "Passenger04", "Passenger05", "Tu"]:
		_look_at_player(_night.get_node_or_null(NodePath(path)) as Node3D, 3.0)
	_monologue(&"BUS2_MONO_WRONG_ORDER")


## Thời gian ở Đêm 1999 nhích lên (hoặc lùi lại) một giây.
func _nudge_time(step: int) -> void:
	_tick = clampi(_tick + step, -3, 6)
	level.set_night_time(_tick)
	EventBus.ui_sfx_requested.emit(&"sfx_heartbeat")
	EventBus.camera_shake_requested.emit(0.01, 0.5)
	var head := _night.get_node_or_null(^"Tu/Upper") as Node3D
	if head:
		create_tween().tween_property(head, "rotation:x", deg_to_rad(10.0 - 6.0 * maxi(_tu_step, 0)), 0.8)


# --- 7. XUỐNG BẾN ------------------------------------------------------------------

func _play_finale() -> void:
	_busy = true
	_finished = true
	_set_all_enabled(false)
	EventBus.player_controls_locked.emit(true)
	var rope_at := _area("Night/BellRope").global_position
	for i in 3:
		EventBus.sfx_requested.emit(&"sfx_bus_bell", rope_at)
		_caption(&"BUS2_CAPTION_BELL_RING", 1.4)
		_nudge_time(1)
		await _wait(1.5)
	var tu := _night.get_node_or_null(^"Tu") as Node3D
	var upper := tu.get_node_or_null(^"Upper") as Node3D if tu else null
	if upper:
		create_tween().tween_property(upper, "rotation:x", deg_to_rad(-6.0), 0.3)
	EventBus.sfx_requested.emit(&"sfx_brake_screech", tu.global_position if tu else Vector3.ZERO)
	_caption(&"BUS2_CAPTION_BRAKE", 2.5)
	EventBus.camera_shake_requested.emit(0.05, 1.2)
	await _wait(1.4)
	level.show_stop_sign(true)
	await _wait(1.2)
	await _say(&"SPEAKER_TU", &"BUS2_TU_CONFESS")
	await _say(&"SPEAKER_TU", &"BUS2_TU_THANKS")
	EventBus.objective_updated.emit(tr(&"OBJ_FREE_PASSENGERS").format({"n": 4}), false)
	for path in ["Tu", "Passenger03", "Passenger04", "Passenger05"]:
		var effigy := _night.get_node_or_null(NodePath(path)) as Node3D
		if effigy and effigy.visible:
			_burn_effigy(effigy)
	await _wait(3.0)
	await _play_step_off()
	await _play_wake_on_real_bus()


func _play_step_off() -> void:
	_caption(&"BUS2_CAPTION_STEP_OFF", 2.5)
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 0.8)
	await _wait(1.2)
	_player.set_physics_process(false)
	_player.velocity = Vector3.ZERO
	_player.global_position = Vector3(1.95, -0.95, 0.4)
	_player.rotation.y = deg_to_rad(90.0)
	_player.head.rotation.x = deg_to_rad(20.0)
	if girl:
		# Bé gái ngồi ghế 08, quay mặt ra cửa sổ nhìn An.
		girl.global_position = Vector3(1.0, 0.4, 0.32)
		girl.rotation = Vector3(0.0, deg_to_rad(-90.0), 0.0)
		girl.visible = true
	EventBus.ui_sfx_requested.emit(&"sfx_footsteps")
	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 1.5)
	await _wait(1.6)
	await _say_monologue(&"BUS2_MONO_LOOK_BACK")
	await _wait(1.2)
	# Đèn bão vụt tắt.
	EventBus.ui_sfx_requested.emit(&"sfx_jumpscare")
	_set_held_lamp(true, false)
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 0.05)
	await _wait(0.8)
	if girl:
		girl.visible = false


func _play_wake_on_real_bus() -> void:
	puzzles.visible = false
	_set_held_lamp(false, false)
	_remove_item(&"matches")
	level.set_layer(BusLevel.Layer.DAY)
	level.set_glimpse(true, false)
	level.set_moving(true, true)
	ride.set_derelict_interactables(false)
	ride.set_derelict_ambience(false)
	ride.place_seated()
	var engine := _make_player(&"amb_bus_engine", -8.0, 1.0)
	await _wait(1.0)
	for i in 3:
		EventBus.ui_sfx_requested.emit(&"sfx_bus_horn")
		await _wait(0.9)
	_caption(&"BUS2_CAPTION_HORN", 3.0)
	await _wait(3.2)
	level.set_moving(false)
	EventBus.screen_effect_requested.emit(&"eyes_open", 0.0, 0.0)
	EventBus.screen_effect_requested.emit(&"blur", 3.0, 0.0)
	EventBus.screen_fade_requested.emit(Color.BLACK, 0.0, 0.6)
	for step: Vector2 in [Vector2(0.4, 1.0), Vector2(0.15, 0.4), Vector2(1.0, 1.2)]:
		EventBus.screen_effect_requested.emit(&"eyes_open", step.x, step.y)
		await _wait(step.y + 0.1)
	EventBus.screen_effect_requested.emit(&"blur", 0.0, 2.0)
	EventBus.screen_effect_requested.emit(&"vignette", 0.2, 2.0)
	EventBus.player_controls_locked.emit(false)
	await _say(&"SPEAKER_CONDUCTOR", &"BUS2_CONDUCTOR_LAST_STOP")
	await _say_monologue(&"BUS2_MONO_WAKE_DAY")
	await _say_monologue(&"BUS2_MONO_ASH")
	_give(&"child_sandal", &"ITEM_CHILD_SANDAL_NAME", &"ITEM_CHILD_SANDAL_DESC")
	await _say_monologue(&"BUS2_MONO_SANDAL")
	GameManager.set_flag(&"bus_chapter_done")
	EventBus.objective_updated.emit(tr(&"OBJ_WALK_TO_HOUSE"), true)
	await _wait(4.0)
	if engine:
		engine.queue_free()
	EventBus.screen_fade_requested.emit(Color.BLACK, 1.0, 2.0)
	await _wait(2.2)
	EventBus.title_card_requested.emit(tr(&"BUS2_END_TITLE"), tr(&"BUS2_END_SUBTITLE"), 6.0)
	await _wait(6.5)
	if not next_scene.is_empty() and is_inside_tree():
		get_tree().change_scene_to_file(next_scene)


# --- Tương tác --------------------------------------------------------------------

func _on_interacted(_actor: Node, target: Interactable) -> void:
	if not _active or _busy:
		return
	_progress()
	match String(target.name):
		"Lamp":
			_on_lamp()
		"Kerosene", "Thread", "NonCoi", "ThuocBac", "DieuCay", "GlowClogs", "WindOil", "BayPencil", "HungTape":
			_pickup(target)
		"Tin":
			if _pickup(target):
				_monologue(&"BUS2_MONO_TIN_TAKEN")
		"TinBox":
			_on_tin_box()
		"NumberDecal":
			_monologue(&"BUS2_MONO_DECAL")
		"TinRusted":
			_monologue(&"BUS2_MONO_TIN_RUSTED")
		"TinDry":
			_on_tin_dry()
		"Clog":
			_clog_seen = true
			_monologue(&"BUS2_MONO_CLOG")
		"Basin":
			_on_basin()
		"Notebook":
			_learn_name(&"hung")
		"DeckRusted":
			_monologue(&"BUS2_MONO_DECK_RUSTED")
		"Hat":
			var first := not &"nam" in _names
			_learn_name(&"nam")
			if first:
				await EventBus.document_closed
				_monologue(&"BUS2_MONO_HAT_NAME")
		"Nam":
			_on_nam()
		"Rack":
			_on_rack()
		"Deck":
			_on_deck()
		"Schoolbag":
			_monologue(&"BUS2_MONO_SCHOOLBAG")
		"Basket":
			if not _tape_fixed and not Inventory.has_item(&"sticky_tape"):
				if _give(&"sticky_tape", &"ITEM_STICKY_TAPE_NAME", &"ITEM_STICKY_TAPE_DESC"):
					_monologue(&"BUS2_MONO_TAPE_FOUND")
			else:
				_monologue(&"BUS2_MONO_BASKET")
		"Footprints":
			_footprints_seen = true
			_monologue(&"BUS2_MONO_FOOTPRINTS")
		"DoorLever":
			_footprints_seen = true
			_monologue(&"BUS2_MONO_DOOR_LEVER")
		"Board":
			_on_board()
		"Seat03", "Seat04", "Seat05":
			_on_passenger(String(target.name).trim_prefix("Seat"))
		"BayBody":
			_on_bay()
		"Satchel":
			_on_satchel()
		"BellRope":
			_on_bell_rope()
		"TuBody":
			_on_tu()
		"DashDeck":
			_on_dash_deck()
		"Seat08":
			_monologue(&"BUS2_MONO_SEAT08_COUNTED" if _counted else &"BUS2_MONO_SEAT08")


func _on_selector_submitted(puzzle_id: StringName, selection: Array, correct: bool) -> void:
	if not _active:
		return
	match String(puzzle_id):
		"tin_box":
			if correct:
				_open_tin_box()
		"burn_clogs":
			_burn_clogs(correct)
		"route":
			if correct:
				_free_hung()
		"punch":
			if correct:
				_free_bay()
		"bell":
			if not selection.is_empty():
				_ring_bell(int(selection[0]) + 1)
		_:
			if String(puzzle_id).begins_with("give_") and not selection.is_empty():
				var index := int(selection[0])
				if index >= 0 and index < _pending_choice.size():
					_give_passenger(String(puzzle_id).trim_prefix("give_"), _pending_choice[index])


## Nhặt vật: vào Hotbar, vật ẩn đi (để có thể hiện lại khi tan thành tro lúc đổi lớp).
func _pickup(target: Interactable) -> bool:
	if Inventory.is_full():
		EventBus.inventory_full.emit()
		_monologue(&"BUS2_MONO_HANDS_FULL")
		return false
	Inventory.add_item(target.to_item_data())
	EventBus.sfx_requested.emit(&"sfx_paper", target.global_position)
	_set_on(target, false)
	return true


func _give(id: StringName, name_key: StringName, desc_key: StringName) -> bool:
	if Inventory.has_item(id):
		return true
	if Inventory.is_full():
		EventBus.inventory_full.emit()
		_monologue(&"BUS2_MONO_HANDS_FULL")
		return false
	var item := ItemData.new()
	item.id = id
	item.name_key = name_key
	item.description_key = desc_key
	Inventory.add_item(item)
	return true


func _remove_item(id: StringName) -> void:
	for i in Inventory.SLOT_COUNT:
		var item := Inventory.get_item(i)
		if item and item.id == id:
			Inventory.remove_item(i)
			return


func _item_name(id: StringName) -> String:
	for i in Inventory.SLOT_COUNT:
		var item := Inventory.get_item(i)
		if item and item.id == id:
			return item.get_display_name()
	return String(id)


func _learn_name(id: StringName) -> void:
	if not id in _names:
		_names.append(id)
		_progress()


func _area(path: String) -> Interactable:
	return puzzles.get_node_or_null(NodePath(path)) as Interactable


func _set_on(target: Interactable, on: bool) -> void:
	if target == null:
		return
	_on[target] = on
	target.visible = on
	_refresh_enabled()


func _refresh_enabled() -> void:
	for target: Interactable in _on.keys():
		if not is_instance_valid(target):
			continue
		var group := target.get_parent()
		var in_layer := (group == _wreck and _layer == BusLevel.Layer.DERELICT) \
				or (group == _night and _layer == BusLevel.Layer.NIGHT)
		target.enabled = _active and not _finished and in_layer and _on[target]


func _set_all_enabled(value: bool) -> void:
	for target: Interactable in _on.keys():
		if is_instance_valid(target):
			target.enabled = value


func _update_free_objective(is_new: bool) -> void:
	var count := int(_nam_freed) + int(_hung_freed) + int(_bay_freed)
	if count >= 3:
		EventBus.objective_updated.emit(tr(&"OBJ_WAKE_DRIVER"), true)
		return
	EventBus.objective_updated.emit(tr(&"OBJ_FREE_PASSENGERS").format({"n": count}), is_new)


# --- Gợi ý: Thắp hương hỏi (H) và Nokia gọi đến --------------------------------------

func _current_puzzle() -> String:
	if _lamp_state == 0:
		return "lamp"
	if _lamp_state == 1:
		if not Inventory.has_item(&"kerosene"):
			return "oil"
		if not Inventory.has_item(&"cotton_thread"):
			return "wick"
		if not Inventory.has_item(&"matches"):
			return "box"
		return "light"
	if not _visited_night:
		return "blow"
	if not _tin_moved:
		return "tin"
	if not _bay_freed:
		if not _counted:
			return "seats"
		return "punch" if _footprints_seen else "footprints"
	if not _nam_freed:
		if _nam_shod:
			return "nam_bell"
		if _clogs_burned:
			return "give_clogs"
		if not &"nam" in _names:
			return "name"
		return "burn"
	if not _hung_freed:
		return "route" if _tape_fixed else "tape"
	return "wake"


func _show_incense_hint() -> void:
	var id := _current_puzzle()
	var level_index := mini(_hint_levels.get(id, 0) + 1, 2)
	_hint_levels[id] = level_index
	EventBus.ui_sfx_requested.emit(&"sfx_incense")
	var body := tr(&"UI_INCENSE_LEVEL").format({"n": level_index}) + "\n\n" \
			+ tr(StringName("HINT_%s_%d" % [id.to_upper(), level_index]))
	var pages: Array[String] = [body]
	EventBus.document_requested.emit(tr(&"UI_INCENSE_TITLE"), pages)


func _process(delta: float) -> void:
	_animate_held_lamp(delta)
	if _flashlight_on and _player:
		var dip := 0.0 if _rng.randf() > 0.02 else _rng.randf_range(0.3, 0.9)
		_player.flashlight.light_energy = flashlight_energy * (1.0 - dip) * (0.9 + 0.1 * sin(_flame_time * 7.0))
	if not _active or _busy or _finished or _player == null or _player.controls_locked:
		return
	_idle += delta
	if _idle >= stuck_call_seconds:
		_idle = 0.0
		_nokia_call()


func _progress() -> void:
	_idle = 0.0


func _nokia_call() -> void:
	var id := _current_puzzle()
	var call := _nokia_line(id)
	if call.is_empty() or _called.get(id, false):
		return
	_called[id] = true
	_busy = true
	EventBus.ui_sfx_requested.emit(&"sfx_nokia_ring")
	_caption(&"BUS2_CAPTION_NOKIA", 3.0)
	await _wait(3.2)
	await _say(call[0], call[1])
	_caption(&"BUS2_CAPTION_NOKIA_END", 2.0)
	_busy = false


func _nokia_line(id: String) -> Array:
	match id:
		"oil", "wick", "box", "light", "lamp":
			return [&"SPEAKER_TU", &"NOKIA_BOX"]
		"blow":
			return [&"SPEAKER_UNKNOWN", &"BUS2_WHISPER_BLOW"]
		"tin":
			return [&"SPEAKER_NAM", &"NOKIA_TIN"]
		"name", "burn", "give_clogs":
			return [&"SPEAKER_NAM", &"NOKIA_CLOGS"]
		"tape", "route":
			return [&"SPEAKER_HUNG", &"NOKIA_TAPE"]
		"seats":
			return [&"SPEAKER_BAY", &"NOKIA_SEATS"]
		"footprints", "punch":
			return [&"SPEAKER_BAY", &"NOKIA_PUNCH"]
		"nam_bell":
			return [&"SPEAKER_NAM", &"NOKIA_NAM_BELL"]
		"wake":
			return [&"SPEAKER_TU", &"NOKIA_WAKE"]
	return []


# --- Hình nhân giấy -------------------------------------------------------------------

func _look_at_player(effigy: Node3D, hold: float) -> void:
	if effigy == null or not effigy.visible:
		return
	var head := effigy.get_node_or_null(^"Upper/Head") as Node3D
	if head == null:
		head = effigy.get_node_or_null(^"Head") as Node3D
	if head == null:
		return
	_turn_head_towards(head, _player.camera.global_position, 0.6)
	var tween := create_tween()
	tween.tween_interval(hold)
	tween.tween_property(head, "rotation:y", 0.0, 0.8)


func _turn_head_towards(head: Node3D, target: Vector3, duration: float) -> void:
	if head == null:
		return
	var to := target - head.global_position
	var world_yaw := atan2(-to.x, -to.z)
	var parent := head.get_parent_node_3d()
	var parent_yaw := parent.global_rotation.y if parent else 0.0
	var yaw := clampf(wrapf(world_yaw - parent_yaw, -PI, PI), deg_to_rad(-110.0), deg_to_rad(110.0))
	EventBus.sfx_requested.emit(&"sfx_paper_creak", head.global_position)
	create_tween().tween_property(head, "rotation:y", yaw, duration).set_trans(Tween.TRANS_SINE)


## Hình nhân cháy thành tàn lửa bay lên rồi biến mất.
func _burn_effigy(effigy: Node3D) -> void:
	if effigy == null or not effigy.visible:
		return
	var center := effigy.global_position + Vector3(0.0, 0.8, 0.0)
	EventBus.sfx_requested.emit(&"sfx_paper_burn", center)
	var light := OmniLight3D.new()
	light.light_color = Color(1.0, 0.55, 0.2)
	light.light_energy = 0.0
	light.omni_range = 2.5
	_night.add_child(light)
	light.global_position = center
	var embers := _make_embers()
	_night.add_child(embers)
	embers.global_position = center
	embers.emitting = true
	var tween := create_tween().set_parallel()
	tween.tween_property(light, "light_energy", 2.5, 0.4)
	tween.tween_property(effigy, "scale", Vector3(1.0, 0.02, 1.0), 2.0).set_delay(0.3).set_ease(Tween.EASE_IN)
	tween.chain().tween_property(light, "light_energy", 0.0, 1.0)
	await tween.finished
	effigy.visible = false
	light.queue_free()
	get_tree().create_timer(3.0).timeout.connect(embers.queue_free)


func _make_embers() -> CPUParticles3D:
	var particles := CPUParticles3D.new()
	particles.amount = 60
	particles.lifetime = 2.5
	particles.one_shot = true
	particles.explosiveness = 0.3
	particles.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	particles.emission_box_extents = Vector3(0.25, 0.5, 0.2)
	particles.direction = Vector3.UP
	particles.spread = 25.0
	particles.gravity = Vector3(0.0, 0.5, 0.0)
	particles.initial_velocity_min = 0.2
	particles.initial_velocity_max = 0.6
	particles.scale_amount_min = 0.5
	particles.scale_amount_max = 1.2
	var quad := QuadMesh.new()
	quad.size = Vector2(0.025, 0.025)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mat.albedo_color = Color(1.0, 0.55, 0.15)
	quad.material = mat
	particles.mesh = quad
	return particles


# --- Đèn bão cầm tay ------------------------------------------------------------------

func _build_held_lamp() -> void:
	if _held_lamp or _player == null:
		return
	_held_lamp = Node3D.new()
	_held_lamp.name = "HeldLamp"
	_player.camera.add_child(_held_lamp)
	_held_lamp.position = held_lamp_offset
	_held_lamp.scale = Vector3.ONE * held_lamp_scale
	var metal := StandardMaterial3D.new()
	metal.albedo_color = Color(0.32, 0.22, 0.15)
	metal.metallic = 0.5
	metal.roughness = 0.8
	var glass := StandardMaterial3D.new()
	glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	glass.albedo_color = Color(0.9, 0.8, 0.6, 0.3)
	glass.roughness = 0.1
	_add_cyl(_held_lamp, 0.07, 0.08, 0.05, Vector3(0, 0.025, 0), metal)
	_add_cyl(_held_lamp, 0.045, 0.055, 0.13, Vector3(0, 0.135, 0), glass)
	_add_cyl(_held_lamp, 0.025, 0.065, 0.04, Vector3(0, 0.22, 0), metal)
	var handle := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 0.075
	torus.outer_radius = 0.085
	handle.mesh = torus
	handle.material_override = metal
	handle.position = Vector3(0, 0.27, 0)
	handle.rotation_degrees = Vector3(90, 0, 0)
	_held_lamp.add_child(handle)
	var flame_mat := StandardMaterial3D.new()
	flame_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	flame_mat.albedo_color = Color(1.0, 0.75, 0.35)
	_held_flame = MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.012
	sphere.height = 0.045
	_held_flame.mesh = sphere
	_held_flame.material_override = flame_mat
	_held_flame.position = Vector3(0, 0.11, 0)
	_held_flame.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_held_lamp.add_child(_held_flame)
	_held_light = OmniLight3D.new()
	_held_light.light_color = Color(1.0, 0.68, 0.38)
	_held_light.omni_range = lamp_light_range
	_held_light.shadow_enabled = true
	_held_light.position = Vector3(0, 0.16, 0.05)
	_held_lamp.add_child(_held_light)
	for node in _held_lamp.get_children():
		if node is GeometryInstance3D:
			(node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_held_lamp.visible = false


func _add_cyl(parent: Node3D, top: float, bottom: float, height: float, pos: Vector3, mat: Material) -> void:
	var mesh := CylinderMesh.new()
	mesh.top_radius = top
	mesh.bottom_radius = bottom
	mesh.height = height
	mesh.radial_segments = 14
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = mat
	node.position = pos
	parent.add_child(node)


func _set_held_lamp(visible_value: bool, lit: bool) -> void:
	if _held_lamp == null:
		return
	_held_lamp.visible = visible_value
	_held_lit = lit
	_held_flame.visible = lit
	_held_flame.scale = Vector3.ONE
	_held_light.visible = lit


func _animate_held_lamp(delta: float) -> void:
	_flame_time += delta
	if _held_light == null or not _held_lit:
		return
	var flicker := 0.88 + 0.08 * sin(_flame_time * 9.0) + 0.04 * sin(_flame_time * 23.0)
	_held_light.light_energy = lamp_light_energy * flicker
	# Đèn đung đưa nhẹ theo bước chân.
	var sway := 0.0
	if _player and _player.velocity.length() > 0.2:
		sway = sin(_flame_time * 7.0) * 0.012
	_held_lamp.position = held_lamp_offset + Vector3(sway * 0.5, absf(sway), 0.0)


func _set_flashlight(on: bool) -> void:
	_flashlight_on = on
	if _player and _player.flashlight:
		_player.flashlight.visible = on
		_player.flashlight.light_energy = flashlight_energy


# --- Chạy thử từ giữa chương ------------------------------------------------------------

func _apply_debug() -> void:
	level.set_power(false)
	if debug_start == DebugStart.DARK:
		_play_darkness()
		return
	_lamp_state = 2
	var lamp := _area("Wreck/Lamp")
	_set_on(lamp, false)
	_box_open = true
	_matches_taken = true
	_give(&"matches", &"ITEM_MATCHES_NAME", &"ITEM_MATCHES_DESC")
	_set_held_lamp(true, true)
	_learn_name(&"tu")
	if debug_start == DebugStart.LAMP_LIT:
		EventBus.objective_updated.emit(tr(&"OBJ_BLOW_LAMP"), true)
		return
	_visited_night = true
	_tin_moved = true
	_glimpse_done = true
	var placed := _area("Night/Rack").get_node_or_null(^"Placed") as Node3D
	if placed:
		placed.visible = true
	_set_on(_area("Night/Tin"), false)
	_set_on(_area("Wreck/TinRusted"), false)
	_set_on(_area("Wreck/TinDry"), true)
	if debug_start != DebugStart.NIGHT:
		_learn_name(&"nam")
		_learn_name(&"hung")
		_clogs_burned = true
		_nam_shod = true
		_nam_freed = true
		_footprints_seen = true
		_tape_fixed = true
		_hung_freed = true
		_counted = true
		_bay_freed = true
		for num in SEAT_ANSWER.keys():
			_seats_done[num] = true
			var held := _night.get_node_or_null(NodePath("Passenger%s/Held/%s" % [num, SEAT_ANSWER[num]])) as Node3D
			if held:
				held.visible = true
		for path in ["BaNam", "Hung", "Bay"]:
			(_night.get_node(NodePath(path)) as Node3D).visible = false
		for path in ["Night/Nam", "Night/Hat", "Night/Deck", "Night/Schoolbag", "Night/Board", "Night/Plaques",
				"Night/BayBody", "Night/Satchel", "Night/Stubs", "Night/NonCoi", "Night/ThuocBac",
				"Night/DieuCay"]:
			_set_on(_area(path), false)
		var plaques := _night.get_node_or_null(^"BoardPlaques") as Node3D
		if plaques:
			plaques.visible = true
		_set_on(_area("Night/WindOil"), true)
		_set_on(_area("Night/HungTape"), true)
	_apply_layer(BusLevel.Layer.NIGHT)
	_update_free_objective(true)
	if debug_start == DebugStart.FINALE:
		_tu_step = 2
		_play_finale()


# --- Tiện ích ----------------------------------------------------------------------------

func _read(title_key: StringName, page_keys: Array[StringName]) -> void:
	var pages: Array[String] = []
	for key in page_keys:
		pages.append(tr(key))
	EventBus.document_requested.emit(tr(title_key), pages)


func _caption(key: StringName, duration: float) -> void:
	EventBus.subtitle_requested.emit("", tr(key), duration)


func _monologue(key: StringName) -> float:
	return _monologue_text(tr(key))


func _monologue_text(text: String) -> float:
	var duration := maxf(2.5, text.length() * 0.055)
	EventBus.inner_monologue_requested.emit(text, duration)
	return duration


func _say_monologue(key: StringName) -> void:
	var duration := _monologue(key)
	await _wait(duration + 0.35)


func _say(speaker_key: StringName, text_key: StringName) -> void:
	var text := tr(text_key)
	var duration := maxf(2.5, text.length() * 0.055)
	EventBus.subtitle_requested.emit(tr(speaker_key), text, duration)
	await _wait(duration + 0.35)


func _wait(seconds: float) -> void:
	if not is_inside_tree():
		return
	await get_tree().create_timer(seconds).timeout


func _make_player(id: StringName, volume_db: float, pitch: float) -> AudioStreamPlayer:
	var stream := AudioSlots.resolve(String(id))
	if stream == null:
		return null
	var player := AudioStreamPlayer.new()
	player.stream = stream
	player.volume_db = volume_db
	player.pitch_scale = pitch
	player.bus = &"SFX" if AudioServer.get_bus_index(&"SFX") != -1 else &"Master"
	add_child(player)
	player.play()
	return player
