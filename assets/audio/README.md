# Âm thanh phân cảnh mở đầu

Thả file đúng tên vào thư mục này (đuôi `.ogg`, `.wav` hoặc `.mp3`), `OpeningSequenceManager` tự nạp, không cần sửa scene. Muốn dùng file ở chỗ khác thì gán vào ô tương ứng trong Inspector của node `OpeningSequence`.

| ID | Dùng ở đâu | Gợi ý |
|---|---|---|
| `sfx_crying` | Tiếng khóc thút thít của bé gái trong mơ (3D, phát từ vị trí cô bé) | Mono, loop được, 10-20 giây |
| `sfx_jumpscare` | Stinger lúc cô bé quay ngoắt đầu | Ngắn, chát chúa, 1-2 giây |
| `voice_parents` | Cuộc thì thầm của bố mẹ ngoài hành lang (qua bus `Muffled` có Low-Pass) | Mono, khớp 5 câu phụ đề |
| `sfx_breathing` | An thở dốc lúc bừng tỉnh (tùy chọn) | 4-6 giây |
| `sfx_footsteps` | Tiếng bước chân xa dần ngoài hành lang (tùy chọn) | 4 giây |

Thiếu file nào thì phân cảnh vẫn chạy bình thường, chỉ không có tiếng. Chú thích âm thanh như "(tiếng khóc thút thít)" luôn hiện trên phụ đề.

Độ "nghe qua vách" chỉnh ở `muffle_cutoff_hz` của `OpeningSequence` hoặc bus `Muffled` trong tab Audio.

## Âm thanh câu đố buổi sáng (`MorningBedroom`)

Phát qua `SfxPlayer` (lắng nghe `EventBus.sfx_requested` / `ui_sfx_requested`), cùng quy tắc: thả file đúng tên vào đây là có tiếng, thiếu thì im lặng.

| ID | Dùng ở đâu | Gợi ý |
|---|---|---|
| `sfx_pillow_lift` | Nhấc gối | Tiếng vải sột soạt, < 1 giây |
| `sfx_key_jingle` | Nhặt chìa khóa đồng | Leng keng kim loại nhỏ |
| `sfx_drawer_slide` | Kéo / đẩy hộc bàn | Tiếng gỗ trượt, ~0.5 giây |
| `sfx_drawer_locked` | Kéo hộc đang khóa, dùng sai vật trong giao diện ổ khóa | Cạch kẹt cứng |
| `sfx_key_insert` | Chìa tra vào ổ | Tiếng kim loại sượt ngắn |
| `sfx_lock_click` | Chìa vặn 90 độ, bật chốt | Tách chốt cơ |
| `sfx_page_flip` | Lật trang sổ chi tiêu | Tiếng giấy cũ |
| `sfx_paper` | Nhặt sổ, tiền, mảnh giấy | Sột soạt giấy |
| `sfx_keypad_beep` | Bấm phím két sắt | Bíp ngắn |
| `sfx_keypad_error` | Nhập sai mật mã | Bíp lỗi trầm |
| `sfx_safe_bolt` | Nhập đúng mật mã | Chốt sắt bật mở nặng nề |
| `sfx_safe_door` | Cánh cửa két mở hé | Bản lề sắt kẽo kẹt |
