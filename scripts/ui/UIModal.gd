## Tiện ích dùng chung cho các giao diện "modal" (soi ổ khóa, sổ chi tiêu, két sắt).
##
## Mở: khóa điều khiển của An (di chuyển, xoay nhìn, tâm ngắm, Hotbar) và đặt
## chế độ chuột. Đóng: luôn khóa chuột lại (MOUSE_MODE_CAPTURED) để An nhìn
## quanh được ngay, kể cả khi trước đó người chơi đã bấm Esc nhả chuột.
class_name UIModal
extends RefCounted


## [param show_cursor] = true để hiện con trỏ (MOUSE_MODE_VISIBLE) cho giao diện
## dùng chuột; false thì giữ chuột bị khóa và ẩn.
static func open(show_cursor: bool) -> void:
	EventBus.player_controls_locked.emit(true)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if show_cursor else Input.MOUSE_MODE_CAPTURED


static func close() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	EventBus.player_controls_locked.emit(false)
