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

## Âm thanh chương "Chuyến xe không về bến" (`BusRide`, `BusWreckDirector`)

Cùng quy tắc: thả file đúng tên vào đây là có tiếng, thiếu thì im lặng (phụ đề chú thích vẫn hiện).

| ID | Dùng ở đâu |
|---|---|
| `sfx_flashlight_click` | Bật đèn pin khi xác xe mất điện |
| `sfx_lamp_blow` | Thổi tắt đèn bão, sang Đêm 1999 |
| `sfx_match_strike` | Quẹt diêm châm đèn, về xác xe |
| `sfx_heartbeat` | Vào Đêm 1999, mỗi nhịp thời gian nhích lên hoặc lùi lại |
| `sfx_dial_tick` | Xoay vòng số / đổi lựa chọn trong giao diện chọn đáp án |
| `sfx_tin_lid` | Mở hộp tôn, đặt hộp bánh quy lên giá |
| `sfx_paper_burn` | Hóa vàng trong chậu sắt, hình nhân cháy thành tàn lửa |
| `sfx_paper_creak` | Hình nhân giấy quay đầu |
| `sfx_drop` | Hình nhân buông đồ xuống sàn (trả sai đồ) |
| `sfx_tape_hiss`, `sfx_temple_bell`, `sfx_market`, `sfx_train_horn`, `sfx_ferry_water` | Bốn đoạn âm thanh trong băng cát-sét của Hùng |
| `sfx_brake_screech` | Tiếng phanh rít (cuối băng, bác Tư đạp phanh) |
| `sfx_ticket_punch` | Kìm bấm vé |
| `sfx_cloth`, `sfx_pour_tea` | Xoa dầu gió, rót chè |
| `sfx_bus_bell` | Giật dây chuông báo bến |
| `sfx_bus_horn` | Ba tiếng còi xe 2006 khi qua cầu |
| `sfx_footsteps` | An bước xuống bậc xe |
| `sfx_nokia_ring` | Chiếc Nokia đổ chuông khi kẹt lâu |
| `sfx_incense` | Thắp hương hỏi (phím H) |
| `amb_bus_engine` | Dùng lại: tiếng động cơ kéo dãn chậm trong cảnh xe 2006 đông cứng |
