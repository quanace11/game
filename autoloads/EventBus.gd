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

## Lời nhắc tương tác thay đổi (đã dịch). Chuỗi rỗng nghĩa là ẩn lời nhắc.
signal interaction_prompt_changed(text: String)

## Yêu cầu UI hiển thị monologue nội tâm ngắn.
## [param text]: câu đã dịch bằng tr().
## [param duration]: số giây hiển thị.
signal inner_monologue_requested(text: String, duration: float)

## Yêu cầu bật hiệu ứng ký ức (sương mờ/vignette) trong [param duration] giây.
signal memory_effect_requested(memory_id: StringName, duration: float)

@warning_ignore_restore("unused_signal")
