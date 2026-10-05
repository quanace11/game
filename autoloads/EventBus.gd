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

## Như [signal document_requested] nhưng chỉ định luôn kiểu giấy [param style]
## (xem DocumentStyles.STYLES, ví dụ &"note", &"form", &"talisman"); &"" = tự chọn theo nội dung.
signal styled_document_requested(title: String, pages: Array[String], style: StringName)

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

## Hiện màn chữ mở đầu chương ở giữa màn hình (thường trên nền đen).
## [param title] và [param subtitle] đã dịch bằng tr(); [param subtitle] rỗng thì chỉ hiện tiêu đề.
signal title_card_requested(title: String, subtitle: String, duration: float)

## Rung camera người chơi. [param strength] tính bằng mét lệch tối đa.
signal camera_shake_requested(strength: float, duration: float)

## Phân cảnh mở đầu chuyển trạng thái. [param state] là OpeningSequenceManager.State.
signal opening_state_changed(state: int)

## Phân cảnh mở đầu kết thúc, gameplay tự do bắt đầu.
signal opening_sequence_finished

# --- Câu đố / đồ vật cơ khí ---

## Phát hiệu ứng âm thanh 3D [param sound_id] tại [param at] (tọa độ thế giới).
## SfxPlayer tìm file res://assets/audio/<sound_id>.ogg|wav|mp3, thiếu file thì im lặng.
signal sfx_requested(sound_id: StringName, at: Vector3)

## Phát âm thanh giao diện (không định vị), ví dụ tiếng bấm phím két sắt.
signal ui_sfx_requested(sound_id: StringName)

## Một cờ trạng thái cốt truyện trong GameManager thay đổi.
signal story_flag_changed(flag: StringName, value: bool)

## Mở giao diện soi ổ khóa [param lock_id]. [param key_item_id] là ID vật phẩm mở được khóa này.
signal lock_inspect_requested(lock_id: StringName, key_item_id: StringName)

## Ổ khóa [param lock_id] vừa được mở bằng chìa (sau hoạt ảnh tra chìa và vặn).
signal lock_opened(lock_id: StringName)

## Mở giao diện đọc sổ đặc biệt (ví dụ sổ chi tiêu bị xé trang).
signal book_requested(book_id: StringName)

## Người chơi vừa gập sổ [param book_id].
signal book_closed(book_id: StringName)

## DocumentViewer vừa đóng.
signal document_closed

## Mở bàn phím két sắt [param safe_id]; [param code] là mật mã đúng.
signal keypad_requested(safe_id: StringName, code: String)

## Nhập đúng mật mã két sắt [param safe_id].
signal safe_unlocked(safe_id: StringName)

## Phân cảnh buổi sáng chuyển trạng thái. [param state] là MorningBedroomDirector.State.
signal morning_state_changed(state: int)

## Phân cảnh xe khách chuyển trạng thái. [param state] là BusRideDirector.State.
signal bus_state_changed(state: int)

## Mở giao diện chọn đáp án nhiều hàng (khóa số, xếp biển, bấm vé...).
## [param rows]: mỗi phần tử là {"label": String, "options": Array[String]} đã dịch.
## [param answer]: chỉ số lựa chọn đúng từng hàng, rỗng = không kiểm tra, trả lựa chọn về luôn.
## [param close_on_wrong]: true = chọn sai cũng đóng (ví dụ đốt mã sai là mất giấy).
signal selector_requested(puzzle_id: StringName, title: String, rows: Array, answer: Array, close_on_wrong: bool)

## Người chơi xác nhận ở giao diện chọn đáp án. [param selection] là chỉ số đã chọn từng hàng.
signal selector_submitted(puzzle_id: StringName, selection: Array, correct: bool)

@warning_ignore_restore("unused_signal")
