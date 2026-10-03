#!/usr/bin/env python3
"""Tải texture PBR CC0 thật từ Poly Haven (polyhaven.com, giấy phép CC0) vào assets/textures/.

Chạy:  python3 -m pip install pillow && python3 tools/fetch_cc0_assets.py
       python3 tools/fetch_cc0_assets.py models     (tải model glTF vào assets/models/)
Sau đó chạy lại tools/level_blockout.py để sinh scene dùng bộ texture mới.

Mỗi bộ texture <name> được ghi thành:
  <name>_albedo.jpg   màu (Diffuse)
  <name>_normal.jpg   normal map chuẩn OpenGL (nor_gl), đúng quy ước của Godot
  <name>_orm.jpg      R = AO, G = roughness, B = metallic (bản "arm" của Poly Haven) -> ORMMaterial3D
Kích thước thật của texture (mét) ghi vào assets/textures/cc0_sets.json để level_blockout.py
trải texture đúng tỉ lệ ngoài đời. Bộ nào không có ở đây (rug_dream, newspaper, reed_mat,
decal) vẫn là ảnh sinh bằng tools/bake_textures.gd vì đó là hình vẽ riêng của game.
"""

import io
import json
import os
import sys
import urllib.request

from PIL import Image, ImageEnhance, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures")
API = "https://api.polyhaven.com"
UA = {"User-Agent": "NoAmDuong-asset-fetch/1.0"}
JPG_QUALITY = 86

# tên bộ trong game: (asset Poly Haven, độ phân giải, xử lý thêm)
# "gray": khử màu albedo để tint trong level_blockout.py quyết định màu (vải nhiều màu dùng chung 1 bộ).
# "sat": giữ lại bấy nhiêu phần độ bão hòa màu (0..1).
# "mean": kéo độ sáng trung bình của albedo về giá trị này (0..255).
SETS = {
    "plaster_white": ("plastered_wall", "2k", {"mean": 226, "sat": 0.3}),  # tường sơn trắng sạch cho giấc mơ
    "oak_floor": ("laminate_floor_02", "2k", {}),
    "limewash_old": ("white_plaster_02", "2k", {"size_m": 2.0, "mean": 175}),  # 1 m lặp lộ trên tường 3 m
    "tile_terracotta": ("terracotta_floor_tiles", "2k", {"mean": 80}),
    "brick_red": ("red_brick", "1k", {"mean": 90}),
    "roof_tile": ("clay_roof_tiles_02", "1k", {}),
    "concrete_damp": ("dirty_concrete", "1k", {}),
    "earth": ("dirt_floor", "1k", {"mean": 100}),
    "grass": ("leafy_grass", "1k", {"mean": 95}),
    "wood_dark": ("wood_table_001", "1k", {}),
    "lacquer_red": ("lacquered_cherry_wood", "1k", {}),
    "wood_weathered": ("weathered_brown_planks", "1k", {}),
    "painted_wood": ("blue_painted_planks", "1k", {}),
    "rust_metal": ("rusty_metal_02", "1k", {"mean": 70}),
    "fabric": ("cotton_jersey", "1k", {"gray": True, "mean": 204}),
    "bamboo_weave": ("bamboo_wall_02", "1k", {}),
}

# Model CC0 (glTF 1k) cho đồ trang trí nhỏ, lưu ở assets/models/<asset>/.
MODELS = [
    "tea_set_01",               # bộ ấm chén trên bàn tiếp khách
    "portable_cassette_player", # đài cát-xét trên tủ chè
    "vintage_oil_lamp",         # đèn dầu
    "pot_enamel_01",            # nồi men trong bếp
    "wooden_bucket_01",         # xô gỗ cạnh chum nước
    "wicker_basket_01",         # rổ mây
    "wooden_crate_01",          # thùng gỗ dưới hầm
    "potted_plant_02",          # chậu cây phòng ngủ trong mơ
]

MAPS = {"albedo": "Diffuse", "normal": "nor_gl", "orm": "arm"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def save_jpg(data, path, gray=False, mean=None, sat=None):
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if gray:
        im = ImageOps.grayscale(im).convert("RGB")
    if sat is not None:
        im = ImageEnhance.Color(im).enhance(sat)
    if mean:
        g = ImageOps.grayscale(im)
        cur = sum(i * c for i, c in enumerate(g.histogram())) / (g.width * g.height)
        k = mean / max(cur, 1.0)
        im = im.point(lambda v: min(255, int(v * k)))
    im.save(path, "JPEG", quality=JPG_QUALITY, optimize=True, progressive=False)


def fetch_model(asset):
    files = json.loads(get("%s/files/%s" % (API, asset)))
    g = files["gltf"]["1k"]["gltf"]
    dst = os.path.join(ROOT, "assets", "models", asset)
    os.makedirs(os.path.join(dst, "textures"), exist_ok=True)
    with open(os.path.join(dst, asset + ".gltf"), "wb") as fh:
        fh.write(get(g["url"]))
    for rel, inc in g["include"].items():
        path = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(get(inc["url"]))
    info = json.loads(get("%s/info/%s" % (API, asset)))
    print("ok model", asset)
    return {"source": "https://polyhaven.com/a/" + asset, "authors": sorted(info.get("authors", {}).keys()),
            "license": "CC0 1.0"}


def main():
    only = set(sys.argv[1:])
    if only == {"models"}:
        credits = {m: fetch_model(m) for m in MODELS}
        with open(os.path.join(ROOT, "assets", "models", "credits.json"), "w") as fh:
            json.dump(credits, fh, indent=2, ensure_ascii=False, sort_keys=True)
            fh.write("\n")
        return
    meta_path = os.path.join(OUT, "cc0_sets.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    for name, (asset, res, opts) in SETS.items():
        if only and name not in only:
            continue
        files = json.loads(get("%s/files/%s" % (API, asset)))
        info = json.loads(get("%s/info/%s" % (API, asset)))
        for suffix, key in MAPS.items():
            url = files[key][res]["jpg"]["url"]
            albedo = suffix == "albedo"
            save_jpg(get(url), os.path.join(OUT, "%s_%s.jpg" % (name, suffix)),
                     gray=albedo and opts.get("gray", False), mean=opts.get("mean") if albedo else None,
                     sat=opts.get("sat") if albedo else None)
        # Ảnh sinh thủ tục cũ cùng tên không còn dùng.
        for old in ("_normal.png", "_rough.jpg"):
            for p in (os.path.join(OUT, name + old), os.path.join(OUT, name + old + ".import")):
                if os.path.exists(p):
                    os.remove(p)
        dims = info.get("dimensions") or [1000, 1000]
        meta[name] = {
            "source": "https://polyhaven.com/a/" + asset,
            "asset": asset,
            "authors": sorted(info.get("authors", {}).keys()),
            "license": "CC0 1.0",
            "resolution": res,
            "size_m": opts.get("size_m", round(max(dims) / 1000.0, 3)),
        }
        print("ok", name, "<-", asset, res, meta[name]["size_m"], "m")
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


if __name__ == "__main__":
    main()
