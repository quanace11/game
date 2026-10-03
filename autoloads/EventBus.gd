## EventBus: kênh signal trung tâm (Autoload "EventBus").
##
## Các hệ thống phát và lắng nghe signal qua đây thay vì tham chiếu trực tiếp
## lẫn nhau, giúp scene tách rời (decoupled).
##
## Phát:     EventBus.memory_unlocked.emit(&"memory_nightmare_01")
## Lắng nghe: EventBus.memory_unlocked.connect(_on_memory_unlocked)
##
## Không đặt class_name cho file này: tên Autoload "EventBus" đã là tên toàn cục,
## đặt thêm class_name trùng tên sẽ gây lỗi.
extends Node

# Signal chỉ được khai báo ở đây và emit từ nơi khác, nên tắt cảnh báo
# "signal được khai báo nhưng không dùng trong class".
@warning_ignore_start("unused_signal")

## Người chơi (hoặc actor khác) yêu cầu tương tác với một đối tượng.
## [param interactable]: node bị tương tác (cửa, vết đinh, đồ vật...).
## [param actor]: node thực hiện tương tác, thường là Player.
signal interaction_requested(interactable: Node, actor: Node)

## Một mảnh ký ức / sự kiện cốt truyện được mở khóa.
## [param memory_id]: ID duy nhất, ví dụ &"memory_prologue_nightmare".
signal memory_unlocked(memory_id: StringName)

## Mức độ lời nguyền thay đổi.
## [param new_level]: mức mới.
## [param old_level]: mức trước khi đổi, để UI/hiệu ứng biết tăng hay giảm.
signal curse_level_changed(new_level: int, old_level: int)

@warning_ignore_restore("unused_signal")
