# Xuất level sang Blender (.glb)

| File | Nguồn |
|---|---|
| `OldHouse.glb` | `scenes/levels/OldHouse.tscn` |
| `DreamBedroom.glb` | `scenes/levels/DreamBedroom.tscn` |

Texture đã nhúng sẵn trong file. 1 unit = 1 m, gốc toạ độ trùng gốc của scene trong Godot. Mỗi file có đúng một Empty gốc
(`OldHouse` / `DreamBedroom`).

## Trong file có gì / không có gì

- **Có:** toàn bộ phần nhìn thấy (tường, sàn, mái, đồ đạc, decal vết ố/nấm mốc, bóng đèn).
  CSG đã được nướng thành mesh thường. Texture triplanar đã được đổi thành UV thật nên
  trong Blender trông giống trong game.
- **Không có (Claude gắn lại khi nhận file về):** đèn, sương/bầu trời, Player, collision,
  bụi/khói particle, script nhấp nháy đèn và đung đưa (`Light_*_Pivot`, `HangingShirt`),
  logic Interactable.
- Gương trong tủ DreamBedroom hiện màu đen trong Blender là bình thường (phản chiếu do Godot tạo).

## Luật khi sửa trong Blender

1. **Giữ tên object.** Claude dựa vào tên để gắn lại đèn, script và Interactable. Đặc biệt:
   `Safe` (két sắt), `Cellar_HatchLid` (nắp hầm), `Altar_Items`, `Cellar_Offering`,
   `HangingShirt`, các Empty `Light_*_Pivot` và bóng đèn bên trong. Object mới thì đặt tên
   có nghĩa bằng tiếng Anh, ví dụ `Wall_Kitchen_North`, `Jar_Pickle_02`.
2. **Không di chuyển, xoay hay scale Empty gốc.** Giữ 1 unit = 1 m (Scene Properties >
   Units: Metric, Unit Scale 1.0). Nếu có scale object thì `Ctrl+A > Scale` trước khi xuất.
3. **Đồ tương tác để thành object riêng**, không join vào tường hay bàn (két sắt, nắp hầm,
   chum, giấy tờ, kẹp tóc…).
4. **Collision (tuỳ chọn):** thêm hậu tố vào tên object để Godot tự tạo va chạm:
   - `-col`: vừa hiện mesh vừa có va chạm (ví dụ `Wall_Back-col`).
   - `-colonly`: khối vô hình chỉ để va chạm (hộp đơn giản bao quanh đồ phức tạp).
   Nếu không đánh dấu, Claude sẽ tự thêm collision.
5. **Vật liệu:** giữ tên vật liệu (`Mat_FenceBrick`, `Mat_AltarRed`…), dùng Principled BSDF + Image Texture. Node procedural (Noise, Voronoi…)
   không xuất được sang glTF, cần bake ra ảnh trước.
6. **Không cần đèn và camera** trong file, có cũng sẽ bị bỏ.

## Xuất lại từ Blender

`File > Export > glTF 2.0`, rồi:

- **Format:** glTF Binary (`.glb`)
- **Include:** bỏ chọn Cameras và Punctual Lights
- **Transform:** để nguyên `+Y Up` (đã bật sẵn)
- **Data > Mesh:** bật Apply Modifiers, UVs, Normals
- **Data > Material:** Export, Images: Automatic

Giữ nguyên tên file (`OldHouse.glb`, `DreamBedroom.glb`) rồi gửi lại trong thread (hoặc
push đè vào thư mục `exports/`). Claude sẽ đưa vào `assets/models/`, dựng lại `.tscn`,
gắn collision, Interactable, đèn, script rồi chụp ảnh để đối chiếu.

## Tạo lại file từ scene

```
godot --headless --path . --import
godot --headless --path . -s tools/export_glb.gd
python3 tools/glb_dedupe.py exports/*.glb
```

Bước cuối gộp các ảnh texture trùng nhau mà exporter của Godot ghi lặp (giảm khoảng 35% dung lượng).
Thư mục này có `.gdignore` nên Godot không import các file ở đây vào project.
