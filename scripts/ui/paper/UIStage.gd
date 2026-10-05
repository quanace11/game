## Sân khấu 1280x720 cho giao diện cận cảnh: luôn nằm giữa màn hình, phóng to/thu nhỏ
## giữ nguyên tỉ lệ theo cửa sổ (dự án không bật stretch). Con của nó dựng theo tọa độ 1280x720.
class_name UIStage
extends Control

const DESIGN := Vector2(1280, 720)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size = DESIGN
	get_viewport().size_changed.connect(_fit)
	_fit()


func _fit() -> void:
	var view := get_viewport().get_visible_rect().size
	var k := minf(view.x / DESIGN.x, view.y / DESIGN.y)
	scale = Vector2.ONE * k
	position = (view - DESIGN * k) * 0.5


## Đổi tọa độ màn hình (sự kiện chuột) sang tọa độ sân khấu.
func to_stage(screen_pos: Vector2) -> Vector2:
	return (screen_pos - position) / scale.x
