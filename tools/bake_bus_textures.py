#!/usr/bin/env python3
"""Sinh các texture vẽ riêng cho chương 2 (xe khách + hình nhân giấy) vào assets/textures/bus/.

Chạy:  python3 -m pip install pillow && python3 tools/bake_bus_textures.py
(tools/bus_blockout.py và tools/bus_puzzles_blockout.py tự gọi lại script này.)

Toàn bộ là hình vẽ thủ tục bằng Pillow, cố định hạt ngẫu nhiên nên chạy lại cho ra đúng ảnh cũ:
- wreck_noise.png    ba kênh nhiễu liền mạch (gỉ, rêu, vệt nước) cho shader xác xe
- glass_grime.png    màng bụi bẩn + vệt chảy trên kính xe bỏ hoang (RGBA)
- glass_rain.png     giọt mưa đọng, vệt nước trên kính đêm mưa (RGBA)
- paper_crease_*.png nếp nhăn giấy bản (albedo xám + normal map) cho hình nhân
- paper_print.png    hoa văn in trên giấy áo hình nhân (xám, tô màu bằng albedo_color)
- gold_trim.png      dải giấy kim tuyến viền cổ áo, gấu áo
- effigy_face_*.png  mặt hình nhân vẽ bằng bút lông: tóc, mày, mắt, má hồng, môi đỏ
- gauge_face.png     mặt đồng hồ taplô
- moss_patch.png     mảng rêu (RGBA) dán lên sàn và chân vách xác xe
- seat_cloth.png     khăn trùm lưng ghế: vải trắng, viền xanh
"""

import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "textures", "bus")
TEX = os.path.join(ROOT, "assets", "textures")


def seamless_noise(size, cells, seed, mode="L"):
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


def fbm(size, base_cells, octaves, seed):
    """Nhiễu nhiều quãng (cộng có trọng số, chuẩn hóa trước khi cộng để không bị cắt trần 255)."""
    amps = [0.5 ** o for o in range(octaves)]
    total = sum(amps)
    acc = Image.new("L", (size, size), 0)
    for o, amp in enumerate(amps):
        n = seamless_noise(size, base_cells * (2 ** o), seed + o * 17)
        acc = ImageChops.add(acc, n.point(lambda v, a=amp / total: v * a))
    return ImageOps.autocontrast(acc, cutoff=1)


def height_to_normal(h, strength=2.0):
    """Ảnh độ cao (L) -> normal map OpenGL (RGB)."""
    w, hgt = h.size
    px = h.load()
    out = Image.new("RGB", (w, hgt))
    po = out.load()
    for y in range(hgt):
        for x in range(w):
            l = px[(x - 1) % w, y]
            r = px[(x + 1) % w, y]
            u = px[x, (y - 1) % hgt]
            d = px[x, (y + 1) % hgt]
            dx = (r - l) / 255.0 * strength
            dy = (d - u) / 255.0 * strength
            nx, ny, nz = -dx, dy, 1.0
            k = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
            po[x, y] = (int((nx * k * 0.5 + 0.5) * 255), int((ny * k * 0.5 + 0.5) * 255), int((nz * k * 0.5 + 0.5) * 255))
    return out


def save(im, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    im.save(path, optimize=True)
    return path


# ---------------------------------------------------------------------------

def wreck_noise():
    r = fbm(256, 4, 4, 11)
    g = fbm(256, 8, 4, 41)
    # Kênh B: vệt chảy dọc (kéo giãn theo trục dọc ảnh) cho vệt nước loang dưới mép ngập.
    b = fbm(256, 16, 3, 77).resize((256, 32), Image.BICUBIC).resize((256, 256), Image.BICUBIC)
    save(Image.merge("RGB", (r, g, b)), "wreck_noise.png")


def glass_grime():
    size = 512
    rng = random.Random(7)
    base = fbm(size, 4, 5, 101)
    alpha = base.point(lambda v: int(40 + v * 0.55))
    # Vệt chảy từ trên xuống
    streak = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(streak)
    for _ in range(160):
        x = rng.uniform(0, size)
        y0 = rng.uniform(-50, size * 0.7)
        ln = rng.uniform(40, 260)
        w = rng.uniform(1, 4)
        d.line([(x, y0), (x + rng.uniform(-6, 6), y0 + ln)], fill=rng.randint(40, 120), width=int(w))
    streak = streak.filter(ImageFilter.GaussianBlur(1.5))
    # Mảng bám dày ở mép dưới
    grad = Image.linear_gradient("L").resize((size, size))
    grad = grad.point(lambda v: max(0, v - 150) * 2)
    alpha = ImageChops.add(alpha, streak)
    alpha = ImageChops.add(alpha, grad)
    spots = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(spots)
    for _ in range(90):
        x, y, r = rng.uniform(0, size), rng.uniform(0, size), rng.uniform(2, 14)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rng.randint(60, 160))
    alpha = ImageChops.add(alpha, spots.filter(ImageFilter.GaussianBlur(3)))
    col = Image.merge("RGB", (base.point(lambda v: 70 + v // 5), base.point(lambda v: 64 + v // 5),
                              base.point(lambda v: 50 + v // 6)))
    col.putalpha(alpha)
    save(col, "glass_grime.png")


def glass_rain():
    size = 512
    rng = random.Random(1404)
    a = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(a)
    # Vệt nước chảy
    for _ in range(70):
        x = rng.uniform(0, size)
        y = rng.uniform(-40, size)
        pts = [(x, y)]
        for k in range(rng.randint(6, 18)):
            x += rng.uniform(-2.5, 2.5)
            y += rng.uniform(8, 18)
            pts.append((x, y))
        d.line(pts, fill=rng.randint(60, 120), width=rng.choice((1, 2, 2, 3)))
        r = rng.uniform(2.5, 5)
        d.ellipse([x - r, y - r, x + r, y + r * 1.3], fill=150)
    # Giọt đọng
    for _ in range(900):
        x, y = rng.uniform(0, size), rng.uniform(0, size)
        r = rng.choice((0.8, 1.2, 1.5, 2, 2.5, 3.5))
        d.ellipse([x - r, y - r, x + r, y + r * 1.15], fill=rng.randint(90, 180))
    a = a.filter(ImageFilter.GaussianBlur(0.7))
    col = Image.new("RGB", (size, size), (200, 214, 222))
    col.putalpha(a)
    save(col, "glass_rain.png")


def paper_crease():
    """Giấy bản nhàu: các nếp gấp thẳng ngẫu nhiên + sợi giấy."""
    size = 512
    rng = random.Random(99)
    h = Image.new("L", (size, size), 128)
    for _ in range(26):
        # Mỗi nếp là một nửa mặt phẳng nâng / hạ nhẹ -> cạnh gấp sắc
        layer = Image.new("L", (size, size), 0)
        d = ImageDraw.Draw(layer)
        ang = rng.uniform(0, math.pi)
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        dx, dy = math.cos(ang) * size * 2, math.sin(ang) * size * 2
        nx, ny = -dy, dx
        poly = [(cx - dx, cy - dy), (cx + dx, cy + dy), (cx + dx + nx, cy + dy + ny), (cx - dx + nx, cy - dy + ny)]
        d.polygon(poly, fill=rng.randint(6, 16))
        layer = layer.filter(ImageFilter.GaussianBlur(rng.uniform(4, 14)))
        h = ImageChops.add(h, layer) if rng.random() < 0.5 else ImageChops.subtract(h, layer)
    fibers = fbm(size, 32, 3, 5).point(lambda v: (v - 128) // 10 + 128)
    h = Image.blend(h, fibers, 0.3)
    h = ImageOps.autocontrast(h, cutoff=0.5)
    save(height_to_normal(h, 3.0), "paper_crease_normal.png")
    alb = h.point(lambda v: 200 + v // 5)
    save(alb.convert("RGB"), "paper_crease_albedo.png")


def paper_print():
    """Hoa văn in kiểu giấy áo hàng mã: hoa thị + chữ thọ tròn, xếp so le, mực nhạt."""
    size = 512
    rng = random.Random(3)
    im = Image.new("L", (size * 2, size * 2), 238)
    d = ImageDraw.Draw(im)
    step = 128
    for j in range(0, size * 2 + step, step):
        for i in range(0, size * 2 + step, step):
            ox = i + (step // 2 if (j // step) % 2 else 0)
            oy = j
            if (i // step + j // step) % 2 == 0:
                # Chữ thọ cách điệu: vòng tròn + chữ thập + móc
                r = 34
                d.ellipse([ox - r, oy - r, ox + r, oy + r], outline=120, width=7)
                d.line([ox - 22, oy, ox + 22, oy], fill=120, width=6)
                d.line([ox, oy - 22, ox, oy + 22], fill=120, width=6)
                d.line([ox - 22, oy - 12, ox - 22, oy + 12], fill=120, width=6)
                d.line([ox + 22, oy - 12, ox + 22, oy + 12], fill=120, width=6)
            else:
                # Hoa năm cánh
                for k in range(5):
                    a = 2 * math.pi * k / 5 + 0.3
                    px, py = ox + math.cos(a) * 18, oy + math.sin(a) * 18
                    d.ellipse([px - 13, py - 13, px + 13, py + 13], fill=150)
                d.ellipse([ox - 8, oy - 8, ox + 8, oy + 8], fill=200)
    im = im.resize((size, size), Image.LANCZOS)
    # Mực in không đều
    blot = fbm(size, 8, 3, 21).point(lambda v: 255 - v // 4)
    im = ImageChops.lighter(im, ImageChops.invert(blot).point(lambda v: v // 2))
    save(im.convert("RGB"), "paper_print.png")


def gold_trim():
    """Dải kim tuyến: nền vàng, hình răng cưa + chấm tròn, ánh kim loang."""
    w, h = 512, 128
    im = Image.new("RGB", (w * 2, h * 2), (196, 150, 52))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w * 2, 18], fill=(150, 30, 26))
    d.rectangle([0, h * 2 - 18, w * 2, h * 2], fill=(150, 30, 26))
    for i in range(0, w * 2, 64):
        d.polygon([(i, 40), (i + 32, 128), (i + 64, 40)], fill=(232, 196, 92))
        d.polygon([(i, 216), (i + 32, 128), (i + 64, 216)], fill=(170, 120, 40))
        d.ellipse([i + 24, 120, i + 40, 136], fill=(150, 30, 26))
    im = im.resize((w, h), Image.LANCZOS)
    sheen = fbm(w, 8, 2, 8).resize((w, h))
    im = Image.blend(im, Image.merge("RGB", (sheen, sheen, sheen.point(lambda v: v // 2))), 0.18)
    save(im, "gold_trim.png")


def _face(name, skin, kind, seed):
    """Mặt hình nhân vẽ phẳng. Ảnh vuông: trục u ngang mặt, v dọc (trên = đỉnh đầu)."""
    S = 1024
    rng = random.Random(seed)
    im = Image.new("RGB", (S, S), skin)
    d = ImageDraw.Draw(im)
    cx = S // 2
    ink = (18, 16, 20)
    # Tóc sơn đen: đường chân tóc cong (cao ở giữa trán, thấp dần xuống thái dương).
    top = {"woman": 250, "old_woman": 250, "boy": 300, "man": 270, "old_man": 250}[kind]
    hair = []
    for i in range(0, S + 1, 16):
        t = (i - cx) / cx
        y = top + 260 * t * t
        if kind in ("woman", "old_woman"):
            y += 40 * math.exp(-(t * 12) ** 2) * -1  # ngôi rẽ giữa
        if kind == "boy":
            y += 18 * math.sin(i / 22.0)  # mái lởm chởm
        hair.append((i, y))
    d.polygon([(0, 0), (S, 0)] + hair[::-1], fill=ink)
    if kind == "old_woman":
        # Vài sợi tóc bạc vẽ bằng nét trắng mảnh
        for _ in range(26):
            x = rng.uniform(80, S - 80)
            d.line([(x, 20), (x + rng.uniform(-40, 40), 260)], fill=(150, 150, 150), width=3)
    # Má hồng: đốm tròn đỏ đậm, nhòe
    cheeks = Image.new("L", (S, S), 0)
    dc = ImageDraw.Draw(cheeks)
    for sx in (-1, 1):
        x = cx + sx * 200
        dc.ellipse([x - 92, 600 - 80, x + 92, 600 + 80], fill=210)
    cheeks = cheeks.filter(ImageFilter.GaussianBlur(26))
    red = Image.new("RGB", (S, S), (214, 52, 66))
    im = Image.composite(red, im, cheeks)
    d = ImageDraw.Draw(im)
    # Lông mày cong mảnh (nét bút lông), mắt hạnh nhân, con ngươi đen nhìn thẳng
    for sx in (-1, 1):
        ex = cx + sx * 160
        brow_y = 380 if kind != "old_woman" else 392
        d.arc([ex - 120, brow_y - 30, ex + 120, brow_y + 90], 200, 340, fill=ink, width=14)
        ey = 470
        d.chord([ex - 92, ey - 44, ex + 92, ey + 44], 180, 360, fill=(250, 248, 240))
        d.chord([ex - 92, ey - 30, ex + 92, ey + 30], 0, 180, fill=(250, 248, 240))
        d.arc([ex - 92, ey - 44, ex + 92, ey + 44], 180, 360, fill=ink, width=12)
        d.arc([ex - 92, ey - 30, ex + 92, ey + 30], 0, 180, fill=ink, width=6)
        d.ellipse([ex - 30, ey - 34, ex + 30, ey + 26], fill=ink)
        d.ellipse([ex - 10, ey - 22, ex + 4, ey - 8], fill=(240, 240, 235))
        if kind in ("old_man", "old_woman"):
            d.arc([ex - 80, ey + 16, ex + 80, ey + 80], 20, 160, fill=(120, 80, 70), width=5)
    # Mũi: hai nét nhỏ
    d.arc([cx - 40, 520, cx + 40, 600], 30, 150, fill=(150, 70, 60), width=7)
    # Môi đỏ nhỏ, khóe miệng nhếch lên (cười mỉm hơi rợn)
    lip = (196, 22, 30)
    d.chord([cx - 60, 650, cx + 60, 712], 0, 180, fill=lip)
    d.chord([cx - 48, 664, cx + 48, 700], 180, 360, fill=lip)
    d.arc([cx - 130, 600, cx + 130, 700], 35, 145, fill=(90, 20, 24), width=6)
    if kind in ("old_man", "man") and seed % 2:
        d.arc([cx - 110, 610, cx + 110, 680], 200, 340, fill=ink, width=10)  # ria mép
    # Vân giấy
    paper = Image.open(os.path.join(OUT, "paper_crease_albedo.png")).convert("L").resize((S, S))
    im = ImageChops.multiply(im, Image.merge("RGB", (paper, paper, paper)).point(lambda v: min(255, v + 30)))
    im = im.resize((512, 512), Image.LANCZOS)
    save(im, "effigy_face_%s.png" % name)


def faces():
    _face("man", (236, 228, 212), "man", 3)
    _face("old_man", (232, 224, 206), "old_man", 5)
    _face("woman", (240, 232, 222), "woman", 2)
    _face("old_woman", (234, 224, 210), "old_woman", 8)
    _face("boy", (240, 234, 220), "boy", 4)


def gauge_face():
    S = 512
    im = Image.new("RGB", (S, S), (16, 16, 18))
    d = ImageDraw.Draw(im)
    c = S // 2
    d.ellipse([16, 16, S - 16, S - 16], fill=(232, 228, 210))
    d.ellipse([32, 32, S - 32, S - 32], fill=(24, 24, 26))
    for k in range(41):
        a = math.radians(225 - 270 * k / 40)
        r0 = 210 if k % 5 == 0 else 225
        d.line([(c + math.cos(a) * r0, c - math.sin(a) * r0), (c + math.cos(a) * 236, c - math.sin(a) * 236)],
               fill=(235, 232, 220), width=8 if k % 5 == 0 else 4)
    for k in range(9):
        a = math.radians(225 - 270 * k / 8)
        x, y = c + math.cos(a) * 170, c - math.sin(a) * 170
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(235, 232, 220))
    a = math.radians(160)
    d.line([(c, c), (c + math.cos(a) * 200, c - math.sin(a) * 200)], fill=(230, 60, 30), width=10)
    d.ellipse([c - 24, c - 24, c + 24, c + 24], fill=(60, 60, 60))
    save(im, "gauge_face.png")


def moss_patch():
    size = 512
    moss = Image.open(os.path.join(TEX, "moss_albedo.jpg")).convert("RGB").resize((size, size))
    mask = fbm(size, 4, 5, 202)
    # Mảng loang, tâm đậm, rìa vụn
    rad = Image.radial_gradient("L").resize((size, size))
    m = ImageChops.subtract(mask, rad.point(lambda v: v * 1.5))
    m = m.point(lambda v: 0 if v < 20 else min(255, (v - 20) * 5))
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    moss = ImageChops.multiply(moss, Image.new("RGB", (size, size), (190, 215, 150)))
    moss.putalpha(m)
    save(moss, "moss_patch.png")


def seat_cloth():
    w, h = 512, 256
    im = Image.new("RGB", (w, h), (236, 232, 222))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 22], fill=(40, 70, 130))
    d.rectangle([0, 30, w, 36], fill=(40, 70, 130))
    d.rectangle([0, h - 36, w, h - 30], fill=(40, 70, 130))
    d.rectangle([0, h - 22, w, h], fill=(40, 70, 130))
    # Hoa văn thêu ở giữa (họa tiết hình thoi)
    for i in range(40, w, 96):
        d.polygon([(i, 128), (i + 24, 100), (i + 48, 128), (i + 24, 156)], outline=(160, 40, 40), width=4)
    weave = fbm(256, 64, 2, 9).resize((w, h)).point(lambda v: 225 + v // 9)
    im = ImageChops.multiply(im, Image.merge("RGB", (weave, weave, weave)))
    save(im, "seat_cloth.png")


# ---------------------------------------------------------------------------
# Đồ vật câu đố (tools/prop_models.py, tools/bus_puzzles_blockout.py)
# ---------------------------------------------------------------------------

def _font(size):
    """Chỉ dùng cho chữ số; không có DejaVu thì dùng phông mặc định của Pillow."""
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def _paper_base(w, h, rgb, seed, stain=0.5):
    """Giấy cũ: màu nền + loang ẩm + sợi giấy."""
    im = Image.new("RGB", (w, h), rgb)
    blot = fbm(max(w, h), 6, 4, seed).resize((w, h))
    dark = Image.new("RGB", (w, h), tuple(int(c * 0.72) for c in rgb))
    im = Image.composite(dark, im, blot.point(lambda v: int(max(0, v - 150) * 2.2 * stain)))
    fib = seamless_noise(max(w, h), 64, seed + 5).resize((w, h))
    im = Image.blend(im, Image.merge("RGB", (fib, fib, fib)), 0.06)
    return im


def prop_talisman():
    """Lá bùa giấy vàng quấn đèn: viền son, chữ triện vẽ tay, vệt nước loang và mép rách."""
    w, h = 128, 384
    rng = random.Random(91)
    im = _paper_base(w, h, (222, 178, 62), 91, stain=0.8)
    d = ImageDraw.Draw(im)
    red = (168, 22, 18)
    d.rectangle([7, 7, w - 8, h - 8], outline=red, width=4)
    d.rectangle([14, 14, w - 15, h - 15], outline=red, width=1)
    # Ấn son trên đầu bùa
    d.rectangle([40, 24, 88, 72], outline=red, width=5)
    d.line([52, 36, 76, 60], fill=red, width=4)
    d.line([76, 36, 52, 60], fill=red, width=4)
    # Nét bùa: các nét ngang có đuôi + đường xoắn chạy dọc
    y = 92
    while y < h - 70:
        x0 = rng.randint(28, 44)
        d.line([x0, y, x0 + rng.randint(36, 60), y + rng.randint(-4, 4)], fill=red, width=rng.choice((4, 5, 6)))
        if rng.random() < 0.6:
            xc = rng.randint(40, 88)
            d.line([xc, y - 6, xc + rng.randint(-8, 8), y + 18], fill=red, width=4)
        y += rng.randint(16, 26)
    pts = [(64 + 22 * math.sin(t * 0.35), 300 + t * 1.1) for t in range(0, 60)]
    d.line(pts, fill=red, width=5)
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    # Mép rách: alpha răng cưa ở hai đầu
    a = Image.new("L", (w, h), 255)
    da = ImageDraw.Draw(a)
    for x in range(0, w, 4):
        da.rectangle([x, 0, x + 3, rng.randint(0, 9)], fill=0)
        da.rectangle([x, h - rng.randint(1, 14), x + 3, h], fill=0)
    im.putalpha(a)
    save(im, "prop_talisman.png")


def prop_biscuit_tin():
    """Hộp bánh quy thiếc: nắp đỏ in vòng vàng + hoa mai; thân đỏ có hai sọc vàng."""
    S = 256
    im = Image.new("RGB", (S, S), (150, 24, 20))
    d = ImageDraw.Draw(im)
    gold = (214, 168, 70)
    c = S // 2
    for r, wdt in ((120, 6), (104, 3), (52, 3)):
        d.ellipse([c - r, c - r, c + r, c + r], outline=gold, width=wdt)
    for k in range(5):
        a = 2 * math.pi * k / 5 - math.pi / 2
        px, py = c + math.cos(a) * 24, c + math.sin(a) * 24
        d.ellipse([px - 17, py - 17, px + 17, py + 17], fill=(236, 200, 96))
    d.ellipse([c - 9, c - 9, c + 9, c + 9], fill=(150, 24, 20))
    for k in range(16):
        a = 2 * math.pi * k / 16
        px, py = c + math.cos(a) * 78, c + math.sin(a) * 78
        d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=gold)
    save(im, "prop_biscuit_lid.png")
    w, h = 512, 96
    im = Image.new("RGB", (w, h), (150, 24, 20))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 8, w, 16], fill=gold)
    d.rectangle([0, h - 16, w, h - 8], fill=gold)
    for i in range(0, w, 64):
        d.ellipse([i + 20, 36, i + 44, 60], outline=gold, width=3)
        d.line([i + 32, 30, i + 32, 66], fill=gold, width=2)
    save(im, "prop_biscuit_side.png")


def prop_ticket():
    """Cuống vé xe khách giấy pơ-luya hồng: dòng kẻ in, số seri, dấu tròn đỏ, mép xé răng cưa."""
    w, h = 128, 224
    rng = random.Random(1999)
    im = _paper_base(w, h, (226, 186, 182), 12, stain=0.4)
    d = ImageDraw.Draw(im)
    ink = (60, 58, 92)
    d.rectangle([6, 6, w - 7, h - 7], outline=ink, width=2)
    d.rectangle([14, 16, w - 15, 44], fill=ink)
    for k in range(6):
        y = 64 + k * 22
        d.line([16, y, w - 18, y], fill=ink, width=1)
        d.line([16, y - 8, 16 + rng.randint(20, 40), y - 8], fill=ink, width=3)
    d.text((22, 188), "0%d%d%d" % (rng.randint(1, 9), rng.randint(0, 9), rng.randint(0, 9)), fill=(150, 30, 30),
           font=_font(22))
    d.ellipse([60, 112, 112, 164], outline=(190, 40, 40), width=3)
    d.ellipse([70, 122, 102, 154], outline=(190, 40, 40), width=1)
    a = Image.new("L", (w, h), 255)
    da = ImageDraw.Draw(a)
    for x in range(0, w, 8):
        da.polygon([(x, 0), (x + 8, 0), (x + 4, 6)], fill=0)
    im.putalpha(a)
    save(im, "prop_ticket.png")


def prop_dial():
    """Vòng số khóa ba vòng: dải 0-9 quấn quanh trụ, chữ trắng trên nền đồng xỉn."""
    w, h = 320, 40
    im = Image.new("RGB", (w, h), (70, 58, 40))
    d = ImageDraw.Draw(im)
    fnt = _font(26)
    for k in range(10):
        x = k * 32
        d.line([x, 0, x, h], fill=(40, 32, 22), width=3)
        d.text((x + 9, 5), str(k), fill=(230, 220, 190), font=fnt)
    save(im, "prop_dial.png")


def prop_thermos():
    """Thân phích nước sắt tráng men xanh, dải hoa mẫu đơn hồng quanh giữa thân."""
    w, h = 512, 256
    rng = random.Random(5)
    im = Image.new("RGB", (w, h), (46, 104, 78))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 70, w, 186], fill=(236, 226, 196))
    for i in range(0, w, 128):
        cx, cy = i + 64, 128
        for k in range(7):
            a = 2 * math.pi * k / 7
            px, py = cx + math.cos(a) * 18, cy + math.sin(a) * 18
            d.ellipse([px - 16, py - 16, px + 16, py + 16], fill=(214, 92, 120))
        d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(240, 196, 80))
        for s in (-1, 1):
            d.ellipse([cx + s * 44 - 14, cy - 8 + rng.randint(-6, 6), cx + s * 44 + 14, cy + 8], fill=(60, 120, 60))
    d.rectangle([0, 64, w, 70], fill=(200, 160, 60))
    d.rectangle([0, 186, w, 192], fill=(200, 160, 60))
    save(im, "prop_thermos.png")


def prop_grille():
    """Mặt loa đài cát-sét: lưới lỗ tròn trên nền nhựa đen (ô lặp liền mạch)."""
    S = 128
    im = Image.new("RGB", (S, S), (34, 34, 36))
    d = ImageDraw.Draw(im)
    for j in range(8):
        for i in range(8):
            x = i * 16 + (8 if j % 2 else 0)
            y = j * 16 + 8
            for ox in (0, -S):
                d.ellipse([x + ox - 4, y - 4, x + ox + 4, y + 4], fill=(8, 8, 9))
    save(im, "prop_grille.png")


def prop_label():
    """Nhãn giấy dán chai dầu hỏa: giấy ngả vàng, khung mực xanh, vệt dầu thấm."""
    w, h = 256, 128
    im = _paper_base(w, h, (214, 196, 150), 33, stain=1.0)
    d = ImageDraw.Draw(im)
    ink = (40, 60, 110)
    d.rectangle([10, 10, w - 11, h - 11], outline=ink, width=3)
    d.ellipse([30, 34, 90, 94], outline=ink, width=3)
    d.polygon([(60, 44), (74, 78), (46, 78)], fill=(170, 50, 30))
    for k in range(3):
        d.line([110, 44 + k * 18, 220 - k * 20, 44 + k * 18], fill=ink, width=5)
    save(im, "prop_label.png")


def prop_permit():
    """Giấy phép lưu hành xe khách: giấy xanh nhạt in khung, dấu đỏ, mực nhòe vì ngấm nước."""
    w, h = 256, 180
    rng = random.Random(85)
    im = _paper_base(w, h, (206, 214, 196), 85, stain=1.4)
    d = ImageDraw.Draw(im)
    ink = (50, 62, 88)
    d.rectangle([8, 8, w - 9, h - 9], outline=ink, width=3)
    d.rectangle([20, 18, w - 21, 38], fill=ink)
    for k in range(6):
        y = 56 + k * 18
        d.line([20, y, 20 + rng.randint(40, 70), y], fill=ink, width=4)
        d.line([100, y + 4, w - 24, y + 4], fill=ink, width=1)
    d.text((176, 140), "..85", fill=(40, 40, 60), font=_font(22))
    d.ellipse([28, 120, 84, 176], outline=(186, 40, 40), width=4)
    im = im.filter(ImageFilter.GaussianBlur(0.9))
    # Mực nhòe: vùng loang lớn mờ hẳn
    blot = fbm(w, 4, 3, 86).resize((w, h)).point(lambda v: max(0, v - 140) * 2)
    im = Image.composite(Image.new("RGB", (w, h), (188, 190, 170)), im, blot.filter(ImageFilter.GaussianBlur(3)))
    save(im, "prop_permit.png")


def props():
    prop_talisman()
    prop_biscuit_tin()
    prop_ticket()
    prop_dial()
    prop_thermos()
    prop_grille()
    prop_label()
    prop_permit()


def main():
    wreck_noise()
    glass_grime()
    glass_rain()
    paper_crease()
    paper_print()
    gold_trim()
    faces()
    gauge_face()
    moss_patch()
    seat_cloth()
    props()
    print("baked bus textures ->", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
