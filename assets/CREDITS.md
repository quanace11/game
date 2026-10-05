# Nguồn asset CC0

Mọi texture và model dưới đây lấy từ [Poly Haven](https://polyhaven.com), giấy phép **CC0 1.0** (public domain, không bắt buộc ghi công; ghi lại để tiện tra cứu).

Tải lại: `python3 tools/fetch_cc0_assets.py` (texture) và `python3 tools/fetch_cc0_assets.py models` (model).

## Texture (`assets/textures/`)

| Bộ trong game | Asset Poly Haven | Kích thước thật | Tác giả |
|---|---|---|---|
| `bamboo_weave` | [bamboo_wall_02](https://polyhaven.com/a/bamboo_wall_02) 1k | 1.7 m | Amal Kumar |
| `brick_red` | [red_brick](https://polyhaven.com/a/red_brick) 1k | 1.4 m | Rob Tuytel |
| `concrete_damp` | [dirty_concrete](https://polyhaven.com/a/dirty_concrete) 1k | 3.0 m | Rob Tuytel |
| `earth` | [dirt_floor](https://polyhaven.com/a/dirt_floor) 1k | 2.07 m | eye-candy.xyz |
| `fabric` | [cotton_jersey](https://polyhaven.com/a/cotton_jersey) 1k | 0.264 m | Rico Cilliers, colormass |
| `grass` | [leafy_grass](https://polyhaven.com/a/leafy_grass) 1k | 2.0 m | Charlotte Baglioni |
| `lacquer_red` | [lacquered_cherry_wood](https://polyhaven.com/a/lacquered_cherry_wood) 1k | 1.0 m | Jenelle van Heerden, Rico Cilliers |
| `limewash_old` | [white_plaster_02](https://polyhaven.com/a/white_plaster_02) 2k | 2.0 m | Rob Tuytel |
| `oak_floor` | [laminate_floor_02](https://polyhaven.com/a/laminate_floor_02) 2k | 1.7 m | Charlotte Baglioni, Dario Barresi |
| `painted_wood` | [blue_painted_planks](https://polyhaven.com/a/blue_painted_planks) 1k | 1.0 m | Rob Tuytel |
| `plaster_white` | [painted_plaster_wall](https://polyhaven.com/a/painted_plaster_wall) 2k | 2.0 m | Amal Kumar |
| `roof_tile` | [clay_roof_tiles_02](https://polyhaven.com/a/clay_roof_tiles_02) 1k | 2.5 m | Amal Kumar |
| `rust_metal` | [rusty_metal_02](https://polyhaven.com/a/rusty_metal_02) 1k | 1.0 m | Rob Tuytel |
| `tile_terracotta` | [terracotta_floor_tiles](https://polyhaven.com/a/terracotta_floor_tiles) 2k | 2.08 m | Dimitrios Savva |
| `wood_dark` | [wood_table_001](https://polyhaven.com/a/wood_table_001) 1k | 1.5 m | Dimitrios Savva, Rico Cilliers |
| `wood_weathered` | [weathered_brown_planks](https://polyhaven.com/a/weathered_brown_planks) 1k | 1.8 m | Dimitrios Savva, Rico Cilliers |
| `curtain_damask` | [floral_jacquard](https://polyhaven.com/a/floral_jacquard) 1k (chuyển xám) | 0.384 m | Rico Cilliers, colormass |
| `moss` | [concrete_moss](https://polyhaven.com/a/concrete_moss) 1k | 3.0 m | Rob Tuytel |
| `paint_clean` | [blue_metal_plate](https://polyhaven.com/a/blue_metal_plate) 1k (chuyển xám) | 2.5 m | Rob Tuytel |
| `paint_flaking` | [rusty_metal_sheet](https://polyhaven.com/a/rusty_metal_sheet) 1k | 2.0 m | Amal Kumar |
| `paint_worn` | [green_metal_rust](https://polyhaven.com/a/green_metal_rust) 1k | 1.0 m | Rob Tuytel |
| `rubber_mat` | [rubber_tiles](https://polyhaven.com/a/rubber_tiles) 1k | 2.0 m | Amal Kumar |
| `rust_heavy` | [rust_coarse_01](https://polyhaven.com/a/rust_coarse_01) 1k | 2.2 m | Dimitrios Savva, Rico Cilliers |
| `vinyl` | [leather_red_03](https://polyhaven.com/a/leather_red_03) 1k (chuyển xám) | 0.3 m | Rob Tuytel |

Các bộ `rug_dream`, `newspaper`, `reed_mat` và toàn bộ `decals/` vẫn là ảnh tự sinh bằng `tools/bake_textures.gd` (hình vẽ riêng của game).

Ảnh trong `assets/textures/bus/` (nhiễu xác xe, kính bẩn, giấy hàng mã, mặt hình nhân, đồng hồ taplô, bùa, vé, hộp bánh, vòng số khóa...) tự vẽ bằng `tools/bake_bus_textures.py`. Mesh xe khách, hành khách, hình nhân và đồ vật câu đố trong `assets/models/bus/` sinh thủ tục bằng `tools/bus_models.py`, `tools/people_models.py`, `tools/prop_models.py` (chạy qua `tools/bus_blockout.py` / `tools/bus_puzzles_blockout.py`).

## Model (`assets/models/`)

| Model | Nguồn | Tác giả |
|---|---|---|
| `portable_cassette_player` | https://polyhaven.com/a/portable_cassette_player | Mateusz Sadek |
| `pot_enamel_01` | https://polyhaven.com/a/pot_enamel_01 | Kuutti Siitonen |
| `potted_plant_02` | https://polyhaven.com/a/potted_plant_02 | Rico Cilliers |
| `tea_set_01` | https://polyhaven.com/a/tea_set_01 | James Ray Cock, Jurita Burger, Rico Cilliers |
| `vintage_oil_lamp` | https://polyhaven.com/a/vintage_oil_lamp | Monsta3D |
| `wicker_basket_01` | https://polyhaven.com/a/wicker_basket_01 | Kuutti Siitonen |
| `wooden_bucket_01` | https://polyhaven.com/a/wooden_bucket_01 | James Ray Cock |
| `wooden_crate_01` | https://polyhaven.com/a/wooden_crate_01 | James Ray Cock |

## Phông chữ giấy tờ (`assets/fonts/`)

Tất cả theo giấy phép SIL Open Font License 1.1 (bản OFL.txt để kèm trong từng thư mục). Tệp woff2 tách theo bộ ký tự (vietnamese, latin, latin-ext) lấy từ gói @fontsource trên npm, bản gốc phát hành trên Google Fonts. Tải lại: `python3 tools/fetch_ui_fonts.py`.

| Thư mục | Phông | Dùng cho | Tác giả |
|---|---|---|---|
| `charm` | Charm 400/700 | chữ bút mực, bút lông (nhật ký, bùa, tên trên giấy điều) | The Charm Project Authors (Cadson Demak) |
| `mynerve` | Mynerve 400 | chữ bút bi (giấy ghi chú, sổ chi tiêu) | The Mynerve Project Authors (Carolina Short) |
| `grape-nuts` | Grape Nuts 400 | chữ bút chì | The Grape Nuts Project Authors |
| `mali` | Mali 400/500 | chữ học trò (vở ô li) | The Mali Project Authors (Cadson Demak) |
| `tinos` | Tinos 400/700 | chữ in trên giấy tờ, vé | The Tinos Project Authors |
| `xanh-mono` | Xanh Mono 400 | chữ đánh máy | The XanhMono Project Authors (Yellow Type Foundry) |
| `oswald` | Oswald 500/700 | chữ con dấu, biển số | The Oswald Project Authors |

## Ảnh giao diện giấy tờ (`assets/ui/`)

`paper_fibers.png`, `paper_stains.png`, `tin_metal.png`, `wood_grain.png` là nhiễu tự sinh bằng `tools/bake_ui_textures.py` (thớ giấy, vết ố, tôn hộp sắt, vân gỗ), dùng cho shader `shaders/ui/paper_sheet.gdshader` và các câu đố.
