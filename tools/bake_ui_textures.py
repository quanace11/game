#!/usr/bin/env python3
"""Sinh texture cho giao diện giấy tờ và đồ vật cận cảnh (assets/ui/).

Chạy:  python3 -m pip install pillow && python3 tools/bake_ui_textures.py

Toàn bộ là hình vẽ thủ tục bằng Pillow, cố định hạt ngẫu nhiên nên chạy lại cho ra đúng ảnh cũ.
Các ảnh đều liền mạch (lát lặp được) để shader dịch UV tùy ý cho mỗi tờ giấy khác nhau:
- paper_fibers.png  thớ giấy: hạt mịn + sợi xơ ngắn (xám, 128 = trung tính)
- paper_stains.png  R: trường ố tần số thấp (shader lấy ngưỡng ra vết nước + viền khô),
                    G: nhiễu mịn cho viền vệt nước, B: đốm ố (foxing),
                    A: nhiễu tần số thấp (mép rách, nét mực đậm nhạt)
- tin_metal.png     tôn mạ kẽm cũ: hoa kẽm, xước, gỉ loang (RGB)
- wood_grain.png    vân gỗ dọc (xám, tô màu trong shader/modulate)
"""

import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "ui")


def seamless_noise(size, cells, seed):
    """Nhiễu giá trị liền mạch: lưới ngẫu nhiên cells x cells, phóng bicubic trên bản lát 3x3."""
    rng = random.Random(seed)
    small = Image.new("L", (cells, cells))
    small.putdata([rng.randint(0, 255) for _ in range(cells * cells)])
    tiled = Image.new("L", (cells * 3, cells * 3))
    for i in range(3):
        for j in range(3):
            tiled.paste(small, (i * cells, j * cells))
    big = tiled.resize((size * 3, size * 3), Image.BICUBIC)
    return big.crop((size, size, size * 2, size * 2))


def fbm(size, base_cells, octaves, seed, gain=0.5):
    # Chia biên độ trước khi cộng để tổng không vượt 255 (ImageChops.add cắt ngọn).
    amp_total = sum(gain ** o for o in range(octaves))
    acc = None
    for o in range(octaves):
        n = seamless_noise(size, base_cells * (2 ** o), seed + o * 17)
        k = gain ** o / amp_total
        n = n.point(lambda v, a=k: v * a)
        acc = n if acc is None else ImageChops.add(acc, n)
    return ImageOps.autocontrast(acc, cutoff=1)


def wrap_draw(size, draw_fn):
    """Vẽ lên tấm 3x3 rồi gập về giữa để nét chạm mép vẫn liền mạch."""
    big = Image.new("L", (size * 3, size * 3), 0)
    draw_fn(ImageDraw.Draw(big), size)
    out = Image.new("L", (size, size), 0)
    for i in range(3):
        for j in range(3):
            out = ImageChops.lighter(out, big.crop((i * size, j * size, (i + 1) * size, (j + 1) * size)))
    return out


def fibers(size, seed):
    rng = random.Random(seed)
    grain = Image.effect_noise((size, size), 40).filter(ImageFilter.GaussianBlur(0.6))
    soft = fbm(size, 16, 4, seed + 3).point(lambda v: 128 + (v - 128) * 0.35)

    def draw_strands(d, s, light):
        for _ in range(2600):
            x, y = rng.uniform(s, 2 * s), rng.uniform(s, 2 * s)
            ang = rng.uniform(0, math.pi * 2)
            length = rng.uniform(6, 34)
            pts = []
            for k in range(6):
                t = k / 5.0
                ang += rng.uniform(-0.35, 0.35)
                pts.append((x + math.cos(ang) * length * t, y + math.sin(ang) * length * t))
            d.line(pts, fill=rng.randint(40, 110) if light else rng.randint(30, 90), width=1)

    light = wrap_draw(size, lambda d, s: draw_strands(d, s, True)).filter(ImageFilter.GaussianBlur(0.5))
    dark = wrap_draw(size, lambda d, s: draw_strands(d, s, False)).filter(ImageFilter.GaussianBlur(0.5))
    img = ImageChops.add(ImageChops.blend(grain, soft, 0.25), light.point(lambda v: v * 0.45))
    img = ImageChops.subtract(img, dark.point(lambda v: v * 0.4))
    # Đưa về quanh 128 để shader dùng như độ lệch sáng/tối.
    return ImageOps.autocontrast(img, cutoff=0.5).point(lambda v: 70 + v * 0.45)


def stains(size, seed):
    rng = random.Random(seed)
    # R: trường nhiễu tần số thấp thô; shader lấy ngưỡng theo độ ố mong muốn, phần biên
    #    ngưỡng thành viền vệt nước khô.
    blot = fbm(size, 4, 6, seed + 1, gain=0.55)
    # G: nhiễu mịn làm viền vệt nước lúc đậm lúc nhạt.
    wobble = fbm(size, 32, 3, seed + 9)

    # B: đốm ố (foxing): chấm nâu nhỏ có quầng.
    def draw_spots(d, s):
        for _ in range(220):
            x, y = rng.uniform(s, 2 * s), rng.uniform(s, 2 * s)
            r = rng.choice([1, 1, 2, 2, 3, 4, 6, 9])
            d.ellipse((x - r, y - r, x + r, y + r), fill=rng.randint(120, 255))
    spots = wrap_draw(size, draw_spots).filter(ImageFilter.GaussianBlur(1.4))
    # A: nhiễu nhiều tầng cho mép rách và độ đậm nhạt của mực.
    low = fbm(size, 8, 6, seed + 5, gain=0.6)
    return Image.merge("RGBA", (blot, wobble, spots, low))


def tin_metal(size, seed):
    rng = random.Random(seed)
    # Hoa kẽm: các mảng đa giác sáng tối khác nhau.
    spangle = Image.new("L", (size * 3, size * 3), 128)
    d = ImageDraw.Draw(spangle)
    for _ in range(900):
        cx, cy = rng.uniform(size, 2 * size), rng.uniform(size, 2 * size)
        r = rng.uniform(10, 34)
        pts = [(cx + math.cos(a) * r * rng.uniform(0.6, 1.2), cy + math.sin(a) * r * rng.uniform(0.6, 1.2))
               for a in sorted(rng.uniform(0, math.pi * 2) for _ in range(7))]
        d.polygon(pts, fill=rng.randint(116, 142))
    sp = spangle.crop((size, size, 2 * size, 2 * size)).filter(ImageFilter.GaussianBlur(1.6))
    base = ImageChops.blend(sp, fbm(size, 8, 4, seed + 2), 0.35)

    def draw_scratches(dd, s):
        for _ in range(160):
            x, y = rng.uniform(s, 2 * s), rng.uniform(s, 2 * s)
            ang = rng.gauss(0.3, 0.5)
            ln = rng.uniform(8, 90)
            dd.line((x, y, x + math.cos(ang) * ln, y + math.sin(ang) * ln), fill=rng.randint(90, 220), width=1)
    scratches = wrap_draw(size, draw_scratches)
    rust_mask = fbm(size, 6, 5, seed + 4).point(lambda v: max(0, min(255, (v - 160) * 3)))
    pits = fbm(size, 48, 2, seed + 6)
    rust_mask = ImageChops.multiply(rust_mask, pits.point(lambda v: min(255, 60 + v)))
    rust_mask = rust_mask.filter(ImageFilter.GaussianBlur(1.2))

    metal = Image.merge("RGB", (base.point(lambda v: int(v * 0.78 + 30)),
                                base.point(lambda v: int(v * 0.80 + 32)),
                                base.point(lambda v: int(v * 0.84 + 36))))
    metal = ImageChops.add(metal, Image.merge("RGB", (scratches,) * 3).point(lambda v: v * 0.18))
    rust_col = Image.merge("RGB", (pits.point(lambda v: int(60 + v * 0.38)),
                                   pits.point(lambda v: int(30 + v * 0.2)),
                                   pits.point(lambda v: int(16 + v * 0.08))))
    return Image.composite(rust_col, metal, rust_mask)


def wood_grain(size, seed):
    rng = random.Random(seed)
    # Vân gỗ: nhiễu kéo dài theo trục dọc + đường vân sin méo.
    stretched = seamless_noise(size, 24, seed).resize((size, size))
    lines = Image.new("L", (size, size))
    px = lines.load()
    warp = fbm(size, 4, 3, seed + 3).load()
    phase = rng.uniform(0, 6.28)
    for y in range(size):
        for x in range(size):
            w = warp[x, y] / 255.0
            v = math.sin((x / size) * math.pi * 2 * 9 + w * 11.0 + phase)
            px[x, y] = int(128 + 70 * (v ** 5))
    fine = Image.effect_noise((size, size), 30).resize((size // 8, size)).resize((size, size), Image.BICUBIC)
    img = ImageChops.blend(lines, fine, 0.35)
    img = ImageChops.blend(img, stretched, 0.2)
    return ImageOps.autocontrast(img, cutoff=1)


def main():
    os.makedirs(OUT, exist_ok=True)
    fibers(1024, 11).save(os.path.join(OUT, "paper_fibers.png"))
    stains(1024, 23).save(os.path.join(OUT, "paper_stains.png"))
    tin_metal(512, 37).save(os.path.join(OUT, "tin_metal.png"))
    wood_grain(512, 41).save(os.path.join(OUT, "wood_grain.png"))
    print("xong:", OUT)


if __name__ == "__main__":
    main()
