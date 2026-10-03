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

## Tâm ngắm chuyển sang vật khác. [param interactable] là null khi không rọi trúng gì.
## HUD dùng [method Interactable.get_display_name] và [method Interactable.get_prompt_text].
signal interaction_focus_changed(interactable: Node)

## Một vật vừa được nhặt vào ô [param slot_index] của Hotbar.
signal item_picked_up(item: ItemData, slot_index: int)

## Người chơi cố nhặt đồ nhưng Hotbar đã đầy.
signal inventory_full

## Mở trình đọc tài liệu. [param title] và [param pages] đã được dịch bằng tr().
signal document_requested(title: String, pages: Array[String])

## Khóa/mở khóa điều khiển của An (di chuyển, xoay nhìn, tương tác) khi UI mở.
signal player_controls_locked(locked: bool)

## Yêu cầu UI hiển thị monologue nội tâm ngắn.
## [param text]: câu đã dịch bằng tr().
## [param duration]: số giây hiển thị.
signal inner_monologue_requested(text: String, duration: float)

## Yêu cầu bật hiệu ứng ký ức (sương mờ/vignette) trong [param duration] giây.
signal memory_effect_requested(memory_id: StringName, duration: float)

# --- Cinematic / phân cảnh kịch bản ---

## Hiện một câu thoại có người nói (phụ đề). [param speaker] và [param text] đã dịch bằng tr().
## [param speaker] rỗng nghĩa là chú thích âm thanh, ví dụ "(tiếng khóc thút thít)".
signal subtitle_requested(speaker: String, text: String, duration: float)

## Xóa ngay phụ đề và monologue đang hiện (khi người chơi bấm bỏ qua).
signal subtitles_cleared

## Cập nhật mục tiêu. [param text] đã dịch. [param is_new] = true để UI nhấn mạnh "Mục tiêu mới".
signal objective_updated(text: String, is_new: bool)

## Phủ màn hình bằng màu [param color], tween độ mờ tới [param alpha] trong [param duration] giây.
## Dùng cho fade-in/out, chớp trắng, sập tối.
signal screen_fade_requested(color: Color, alpha: float, duration: float)

## Tween một hiệu ứng màn hình tới [param value] trong [param duration] giây.
## [param effect]: &"blur" (0-6), &"eyes_open" (0 nhắm - 1 mở), &"vignette" (0-1, sắc lạnh).
signal screen_effect_requested(effect: StringName, value: float, duration: float)

## Rung camera người chơi. [param strength] tính bằng mét lệch tối đa.
signal camera_shake_requested(strength: float, duration: float)

## Phân cảnh mở đầu chuyển trạng thái. [param state] là OpeningSequenceManager.State.
signal opening_state_changed(state: int)

## Phân cảnh mở đầu kết thúc, gameplay tự do bắt đầu.
signal opening_sequence_finished

@warning_ignore_restore("unused_signal")
