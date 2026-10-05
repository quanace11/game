## Một tờ giấy vật lý trên giao diện (giấy sổ, vé, bùa, giấy phép...).
##
## Gồm ba lớp, cùng hệ tọa độ "px giấy" (0,0 = góc trên trái tờ giấy):
## - [member ink]: Control trong SubViewport nền trong suốt; mọi thứ vẽ ở đây (chữ, dòng kẻ,
##   dấu mộc, hình vẽ) được shader paper_sheet thấm vào giấy như mực thật.
## - Giấy: ColorRect chạy shader paper_sheet (màu giấy, thớ, ố, vết nước, nếp gấp, mép rách, bóng đổ).
## - [member overlay]: vẽ đè lên trên giấy, không bị thấm (lỗ bấm vé, ghim, băng dính...).
## Kích thước Control = paper_size + 2 * MARGIN (lề chứa bóng đổ); xoay quanh tâm.
class_name PaperSheet
extends Control

const MARGIN := 48.0
## Lớp mực vẽ ở độ phân giải gấp đôi để chữ vẫn sắc khi phóng to.
const INK_SCALE := 2.0
const SHADER := preload("res://shaders/ui/paper_sheet.gdshader")
const FIBER_TEX := preload("res://assets/ui/paper_fibers.png")
const STAIN_TEX := preload("res://assets/ui/paper_stains.png")

## Vài kiểu giấy hay dùng. Khóa trùng tên uniform trong shader paper_sheet.
const LOOK_NOTEBOOK := {
	"paper_color": Color(0.90, 0.86, 0.75), "age": 0.55, "grain": 0.5, "foxing": 0.25, "tear": 1.5,
}
const LOOK_FORM := {
	"paper_color": Color(0.87, 0.85, 0.78), "age": 0.45, "grain": 0.45, "foxing": 0.2, "tear": 1.0,
}

var paper_size := Vector2(400, 500)
var ink: Control
var overlay: Control
var paper: ColorRect

var _viewport: SubViewport
var _material: ShaderMaterial


## [param look]: tham số shader (paper_color, age, stain, folds, perforate, sheen...).
## [param draw_ink] / [param draw_overlay]: Callable(ci: CanvasItem) vẽ trong hệ px giấy.
func _init(p_size: Vector2 = Vector2(400, 500), look: Dictionary = {}, draw_ink := Callable(),
		draw_overlay := Callable()) -> void:
	paper_size = p_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size = paper_size + Vector2.ONE * MARGIN * 2.0
	custom_minimum_size = size
	pivot_offset = size * 0.5

	_viewport = SubViewport.new()
	_viewport.transparent_bg = true
	_viewport.disable_3d = true
	_viewport.size = Vector2i((paper_size * INK_SCALE).ceil())
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_viewport)
	ink = Control.new()
	ink.size = paper_size
	ink.scale = Vector2.ONE * INK_SCALE
	_viewport.add_child(ink)
	if draw_ink.is_valid():
		ink.draw.connect(draw_ink.bind(ink))

	_material = ShaderMaterial.new()
	_material.shader = SHADER
	_material.set_shader_parameter(&"ink_tex", _viewport.get_texture())
	_material.set_shader_parameter(&"fiber_tex", FIBER_TEX)
	_material.set_shader_parameter(&"stain_tex", STAIN_TEX)
	_material.set_shader_parameter(&"paper_size", paper_size)
	_material.set_shader_parameter(&"margin", MARGIN)
	paper = ColorRect.new()
	paper.mouse_filter = Control.MOUSE_FILTER_IGNORE
	paper.size = size
	paper.material = _material
	add_child(paper)
	set_look(look)

	overlay = Control.new()
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	overlay.position = Vector2.ONE * MARGIN
	overlay.size = paper_size
	add_child(overlay)
	if draw_overlay.is_valid():
		overlay.draw.connect(draw_overlay.bind(overlay))


func set_look(look: Dictionary) -> void:
	for key: String in look:
		_material.set_shader_parameter(StringName(key), look[key])


func set_param(key: StringName, value: Variant) -> void:
	_material.set_shader_parameter(key, value)


## Vẽ lại lớp mực và lớp đè (khi nội dung đổi, ví dụ vừa bấm lỗ vé).
func redraw() -> void:
	ink.queue_redraw()
	overlay.queue_redraw()


## Tâm tờ giấy trong hệ tọa độ của Control cha.
func get_paper_center() -> Vector2:
	return position + size * 0.5


## Đặt tâm tờ giấy tại [param p] (tọa độ Control cha).
func place(p: Vector2, degrees: float = 0.0) -> void:
	position = p - size * 0.5
	rotation_degrees = degrees


## Đổi tọa độ px giấy sang tọa độ Control cha (tính cả góc xoay).
func paper_to_parent(p: Vector2) -> Vector2:
	return get_transform() * (p + Vector2.ONE * MARGIN)


## Đổi tọa độ Control cha sang px giấy.
func parent_to_paper(p: Vector2) -> Vector2:
	return get_transform().affine_inverse() * p - Vector2.ONE * MARGIN
