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
