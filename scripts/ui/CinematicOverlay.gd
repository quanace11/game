## Lớp trình bày cho phân cảnh kịch bản: fade/chớp màn hình, hiệu ứng mờ/mí mắt/
## vignette, phụ đề hội thoại, monologue nội tâm và mục tiêu.
##
## Chỉ lắng nghe EventBus, không chứa logic cốt truyện.
class_name CinematicOverlay
extends CanvasLayer

const SPEAKER_COLOR := "#d9b38c"
const NEUTRAL := {&"blur": 0.0, &"eyes_open": 1.0, &"vignette": 0.0}

## Bắt đầu với màn hình đen (để phân cảnh fade-in).
@export var start_black: bool = true

@onready var _fx: ColorRect = %ScreenFX
@onready var _fade: ColorRect = %Fade
@onready var _subtitle: RichTextLabel = %Subtitle
@onready var _monologue: Label = %Monologue
@onready var _objective_box: Control = %ObjectiveBox
@onready var _objective_header: Label = %ObjectiveHeader
@onready var _objective_text: Label = %ObjectiveText
@onready var _title_card: Control = %TitleCard
@onready var _title_label: Label = %TitleLabel
@onready var _title_sub: Label = %TitleSub

var _fx_material: ShaderMaterial
var _fade_tween: Tween
var _fx_tweens: Dictionary[StringName, Tween] = {}
var _subtitle_tween: Tween
var _monologue_tween: Tween
var _objective_tween: Tween
var _title_tween: Tween


func _ready() -> void:
	_fx_material = _fx.material as ShaderMaterial
	if _fx_material:
		for key: StringName in NEUTRAL:
			_fx_material.set_shader_parameter(String(key), NEUTRAL[key])
	_fade.color = Color(0, 0, 0, 1.0 if start_black else 0.0)
	_subtitle.modulate.a = 0.0
	_monologue.modulate.a = 0.0
	_objective_box.modulate.a = 0.0
	_title_card.modulate.a = 0.0
	_update_fx_visibility()
	EventBus.subtitle_requested.connect(_on_subtitle_requested)
	EventBus.inner_monologue_requested.connect(_on_monologue_requested)
	EventBus.subtitles_cleared.connect(_on_subtitles_cleared)
	EventBus.objective_updated.connect(_on_objective_updated)
	EventBus.screen_fade_requested.connect(_on_fade_requested)
	EventBus.screen_effect_requested.connect(_on_effect_requested)
	EventBus.title_card_requested.connect(_on_title_card_requested)


func _exit_tree() -> void:
	var links := {
		EventBus.subtitle_requested: _on_subtitle_requested,
		EventBus.inner_monologue_requested: _on_monologue_requested,
		EventBus.subtitles_cleared: _on_subtitles_cleared,
		EventBus.objective_updated: _on_objective_updated,
		EventBus.screen_fade_requested: _on_fade_requested,
		EventBus.screen_effect_requested: _on_effect_requested,
		EventBus.title_card_requested: _on_title_card_requested,
	}
	for sig: Signal in links:
		if sig.is_connected(links[sig]):
			sig.disconnect(links[sig])


func _on_subtitle_requested(speaker: String, text: String, duration: float) -> void:
	var body := _escape(text)
	if speaker.is_empty():
		_subtitle.text = "[i][color=#a9b3bf]%s[/color][/i]" % body
	else:
		_subtitle.text = "[color=%s]%s:[/color] %s" % [SPEAKER_COLOR, _escape(speaker), body]
	_subtitle_tween = _show_timed(_subtitle, _subtitle_tween, duration)


func _on_title_card_requested(title: String, subtitle: String, duration: float) -> void:
	_title_label.text = title
	_title_sub.text = subtitle
	_title_sub.visible = not subtitle.is_empty()
	if _title_tween:
		_title_tween.kill()
	_title_tween = create_tween()
	_title_tween.tween_property(_title_card, "modulate:a", 1.0, 1.2)
	_title_tween.tween_interval(maxf(duration - 2.4, 0.2))
	_title_tween.tween_property(_title_card, "modulate:a", 0.0, 1.2)


func _on_monologue_requested(text: String, duration: float) -> void:
	_monologue.text = text
	_monologue_tween = _show_timed(_monologue, _monologue_tween, duration)


func _on_subtitles_cleared() -> void:
	for t: Tween in [_subtitle_tween, _monologue_tween]:
		if t:
			t.kill()
	_subtitle.modulate.a = 0.0
	_monologue.modulate.a = 0.0


func _on_objective_updated(text: String, is_new: bool) -> void:
	_objective_header.text = tr(&"UI_OBJECTIVE_NEW") if is_new else tr(&"UI_OBJECTIVE")
	_objective_text.text = text
	if _objective_tween:
		_objective_tween.kill()
	_objective_tween = create_tween()
	_objective_box.modulate = Color(1.0, 0.85, 0.6, 0.0) if is_new else Color(1, 1, 1, 0)
	_objective_tween.tween_property(_objective_box, "modulate:a", 1.0, 0.6)
	if is_new:
		_objective_tween.tween_property(_objective_box, "modulate", Color.WHITE, 2.0)


func _on_fade_requested(color: Color, alpha: float, duration: float) -> void:
	if _fade_tween:
		_fade_tween.kill()
	var from := _fade.color
	_fade.color = Color(color.r, color.g, color.b, from.a)
	if duration <= 0.0:
		_fade.color.a = alpha
		return
	_fade_tween = create_tween()
	_fade_tween.tween_property(_fade, "color:a", alpha, duration)


func _on_effect_requested(effect: StringName, value: float, duration: float) -> void:
	if not NEUTRAL.has(effect) or _fx_material == null:
		push_warning("CinematicOverlay: unknown screen effect '%s'" % effect)
		return
	var old: Tween = _fx_tweens.get(effect)
	if old:
		old.kill()
	_fx.visible = true
	var param := String(effect)
	if duration <= 0.0:
		_fx_material.set_shader_parameter(param, value)
		_update_fx_visibility()
		return
	var from: float = _fx_material.get_shader_parameter(param)
	var tween := create_tween()
	tween.tween_method(func(v: float) -> void: _fx_material.set_shader_parameter(param, v),
			from, value, duration)
	tween.finished.connect(_update_fx_visibility)
	_fx_tweens[effect] = tween


## Tắt ColorRect hiệu ứng khi mọi tham số về trung tính, để khỏi đọc màn hình mỗi khung hình.
func _update_fx_visibility() -> void:
	if _fx_material == null:
		_fx.visible = false
		return
	for key: StringName in NEUTRAL:
		if not is_equal_approx(_fx_material.get_shader_parameter(String(key)), NEUTRAL[key]):
			_fx.visible = true
			return
	_fx.visible = false


func _show_timed(label: CanvasItem, previous: Tween, duration: float) -> Tween:
	if previous:
		previous.kill()
	var tween := create_tween()
	tween.tween_property(label, "modulate:a", 1.0, 0.25)
	tween.tween_interval(maxf(duration - 0.5, 0.1))
	tween.tween_property(label, "modulate:a", 0.0, 0.25)
	return tween


func _escape(text: String) -> String:
	return text.replace("[", "[lb]")
