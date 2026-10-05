#!/usr/bin/env python3
"""Mesh thủ tục cho đồ vật câu đố chương 2 (scenes/bus/BusPuzzles.tscn) và vài đồ trong xác xe.

Mỗi hàm build_* sinh một file assets/models/bus/<tên>.obj (qua bus_models.save) và ghi danh
sách khe vật liệu vào bus_models.MODELS. Gốc tọa độ mỗi mesh đặt sao cho khớp chỗ khối hộp
blockout cũ (ghi ở từng hàm), để scene chỉ cần thay mesh mà không xê dịch Area3D.

Chạy riêng:  python3 tools/prop_models.py   (bus_puzzles_blockout.py tự gọi build_all()).
"""

import math
import random

import bus_models
import mesh_kit as mk
from mesh_kit import RX, RY, RZ, T

MODELS = bus_models.MODELS


def _save(m):
    return bus_models.save(m)


def card(m, slot, w, h, xf=None, nu=1, nv=1, bend=None):
    """Tấm giấy/bìa phẳng nằm trong mặt XZ (mặt trên +Y), UV 0..1 phủ trọn ảnh, hai mặt.
    bend(x, z) -> độ võng theo Y để giấy cong nhẹ."""
    def fn(u, v):
        x, z = (u - 0.5) * w, (0.5 - v) * h
        return (x, bend(x, z) if bend else 0.0, z)
    mk.grid(m, slot, fn, nu, nv, uv_fn=lambda u, v, p: (u, v), xf=xf, flip=True, double=True)


def disk_planar(m, slot, r, y, segs=24, xf=None, down=False):
    """Mặt tròn phẳng, UV chiếu phẳng theo mét (tâm = 0): vật liệu dùng uv1_scale = 1/(2r), offset 0.5."""
    pts = [(r * math.cos(2 * math.pi * k / segs), y, -r * math.sin(2 * math.pi * k / segs)) for k in range(segs)]
    if down:
        pts.reverse()
    mk.polygon(m, slot, pts, (0, -1 if down else 1, 0), xf)


# ---------------------------------------------------------------------------
# XÁC XE
# ---------------------------------------------------------------------------

def build_talisman_wrap():
    """Bùa giấy vàng quấn quanh bầu kính đèn bão (khớp tools/people_models.build_storm_lamp):
    một vòng giấy quấn hơn một vòng, đuôi giấy rủ xuống, buộc dây đỏ."""
    m = mk.Mesh("pz_talisman_wrap")
    glass = [(0.04, 0.078), (0.052, 0.1), (0.058, 0.135), (0.054, 0.17), (0.04, 0.198)]

    def glass_r(y):
        for (r0, y0), (r1, y1) in zip(glass, glass[1:]):
            if y0 <= y <= y1:
                return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
        return glass[-1][0]

    y0, y1 = 0.092, 0.182
    turns = 1.25

    def band(u, v):
        a = 2 * math.pi * turns * u + 0.4
        y = y0 + (y1 - y0) * v + 0.004 * math.sin(a * 3)
        # lồng dây bảo vệ ở r~0.066: giấy nằm dưới lồng, quấn lớp sau phồng hơn lớp trước
        r = glass_r(y) + 0.003 + 0.0025 * u + 0.0012 * math.sin(a * 7 + v * 4)
        return (r * math.cos(a), y, -r * math.sin(a))

    circ = 2 * math.pi * 0.058 * turns
    mk.grid(m, "paper", band, 40, 4, uv_fn=lambda u, v, p: (v, u * circ / 0.27), double=True)
    # Đuôi giấy bong ra, rủ xuống, cong theo gió
    a_end = 2 * math.pi * turns + 0.4
    ex, ez = math.cos(a_end), -math.sin(a_end)
    tx, tz = -ez, ex     # tiếp tuyến vòng quấn

    def tail(u, v):
        s = v * 0.2
        w = (u - 0.5) * 0.04
        base_r = 0.066
        p = (ex * base_r + tx * (0.01 + s * 0.25), 0.15 - s * 0.95, ez * base_r + tz * (0.01 + s * 0.25))
        out = 0.02 * math.sin(v * 2.5) + 0.004 * math.sin(u * 6)
        return (p[0] + ex * out + 0.0, p[1] + w * 0.25, p[2] + ez * out + w * 0.97)

    mk.grid(m, "paper", tail, 2, 10, uv_fn=lambda u, v, p: (u, 0.62 * v + 0.3), double=True)
    # Dây đỏ buộc ngang giữa
    ring = [(math.cos(a) * 0.0655, 0.137, -math.sin(a) * 0.0655)
            for a in [2 * math.pi * k / 28 for k in range(28)]]
    mk.tube(m, "string", ring, 0.0016, sides=4, closed=True)
    _save(m)


def build_lamp_hook():
    """Móc sắt bắt vào vách sau + đoạn dây thép treo quai đèn. Gốc = điểm quai đèn (đỉnh quai)."""
    m = mk.Mesh("pz_lamp_hook")
    mk.box(m, "iron", (0.05, 0.07, 0.008), T(0, 0.2, 0.09))
    for sy in (-1, 1):
        mk.lathe(m, "iron", [(0.0, 0.0), (0.006, 0.0), (0.006, 0.004), (0.0, 0.005)], 8,
                 T(0, 0.2 + sy * 0.022, 0.086) * RX(-90))
    mk.tube(m, "iron", mk.round_path([(0, 0.2, 0.086), (0, 0.2, 0.03), (0, 0.17, 0.0), (0, 0.13, 0.0)], 0.015, 4),
            0.004, sides=6)
    mk.tube(m, "iron", mk.arc((0, 0.12, 0), 0.012, -90, 250, 12, "yz"), 0.0025, sides=5)
    mk.tube(m, "wire", [(0, 0.11, 0), (0.002, 0.06, 0.001), (0, 0.0, 0)], 0.0012, sides=4)
    _save(m)


def build_kerosene_bottle():
    """Chai thủy tinh cũ đựng dầu hỏa, nút giấy cuộn + dây, nhãn giấy. Nằm dọc trục Y, đáy ở y=0,
    tâm thân ở (0, 0.09, 0); khi đặt nằm nghiêng thì xoay quanh Z."""
    m = mk.Mesh("pz_kerosene")
    body = [(0.0, 0.0), (0.03, 0.0), (0.037, 0.004), (0.038, 0.012), (0.038, 0.11), (0.034, 0.13), (0.022, 0.15),
            (0.0135, 0.165), (0.013, 0.19), (0.0155, 0.193), (0.0155, 0.2), (0.0115, 0.202), (0.0115, 0.19),
            (0.0, 0.19)]
    mk.lathe(m, "glass", body, 24)
    oil = [(0.0, 0.004), (0.034, 0.004), (0.035, 0.012), (0.035, 0.085), (0.0, 0.085)]
    mk.lathe(m, "oil", oil, 20)
    # Nút giấy cuộn + dây buộc cổ chai
    mk.lathe(m, "cork", [(0.0, 0.185), (0.011, 0.185), (0.0118, 0.205), (0.013, 0.214), (0.008, 0.222),
                         (0.0, 0.223)], 10)
    mk.tube(m, "cork", mk.arc((0, 0.188, 0), 0.0145, 0, 360, 14, "xz")[:-1], 0.0012, sides=4, closed=True)
    # Nhãn giấy dán thân, mép bong
    def label(u, v):
        a = math.radians(-60 + 120 * u)
        r = 0.0385 + (0.004 * (1 - v) if u > 0.85 else 0.0)
        return (r * math.cos(a), 0.035 + 0.06 * v, -r * math.sin(a))
    mk.grid(m, "label", label, 8, 1, uv_fn=lambda u, v, p: (u, v), double=True)
    _save(m)


def build_spool():
    """Ống chỉ gỗ quấn chỉ bông trắng, đầu chỉ tuột ra. Trục X, tâm ở gốc (khớp khối cũ 0.05 x r0.025)."""
    m = mk.Mesh("pz_spool")
    wood = [(0.0, -0.028), (0.026, -0.028), (0.027, -0.025), (0.026, -0.022), (0.012, -0.02), (0.012, 0.02),
            (0.026, 0.022), (0.027, 0.025), (0.026, 0.028), (0.0, 0.028)]
    mk.lathe(m, "wood", wood, 20, RZ(90))
    cot = [(0.0119, -0.0205), (0.0205, -0.0205), (0.022, -0.015), (0.0225, 0.0), (0.022, 0.015), (0.0205, 0.0205),
           (0.0119, 0.0205)]
    mk.lathe(m, "cotton", cot, 24, RZ(90))
    # Sợi chỉ tuột
    path = [(0.008, 0.022, 0.006), (0.015, 0.02, -0.02), (0.03, 0.006, -0.05), (0.06, -0.012, -0.07),
            (0.085, -0.02, -0.06), (0.1, -0.022, -0.075)]
    mk.tube(m, "cotton", path, 0.0011, sides=4)
    _save(m)


def build_tin_box():
    """Hộp tôn đựng giấy tờ của bác Tư. Thân rỗng 0.22 x 0.07 x 0.14, tâm ở gốc (khớp khối cũ).
    Mặt trước (+Z, quay về phía người đứng sau ghế lái): tai khóa + khóa số ba vòng (slot 'dial', trục X tại
    x = -0.03 / 0 / 0.03). Bản lề ở mép -Z (phía kính lái) để nắp lật lên khi BusWreckDirector xoay rotation.x âm."""
    m = mk.Mesh("pz_tin_box")
    w, h, d, t = 0.22, 0.07, 0.14, 0.004
    mk.box(m, "tin", (w, t, d), T(0, -h / 2 + t / 2, 0))
    for sx in (-1, 1):
        mk.box(m, "tin", (t, h, d), T(sx * (w / 2 - t / 2), 0, 0))
    for sz in (-1, 1):
        mk.box(m, "tin", (w - 2 * t, h, t), T(0, 0, sz * (d / 2 - t / 2)))
    # Gân dập quanh thân + mép cuộn
    for y in (-0.018, 0.012):
        mk.rbox(m, "tin", (w + 0.004, 0.006, d + 0.004), 0.002, 1, xf=T(0, y, 0), faces=None)
    # Bản lề phía kính lái
    mk.tube(m, "tin", [(-w / 2 + 0.01, h / 2, -d / 2 - 0.002), (w / 2 - 0.01, h / 2, -d / 2 - 0.002)], 0.004, sides=8)
    # Thân khóa ba vòng
    mk.rbox(m, "brass", (0.11, 0.03, 0.016), 0.004, 1, xf=T(0, 0.0, d / 2 + 0.008))
    for k in range(3):
        x = -0.03 + 0.03 * k
        dial = [(0.0, -0.0055), (0.0105, -0.0055), (0.0125, -0.004), (0.0125, 0.004), (0.0105, 0.0055),
                (0.0, 0.0055)]
        mk.lathe(m, "dial", dial, 20, T(x, 0.0, d / 2 + 0.019) * RZ(90))
    # Tai khóa (móc chữ U từ nắp xuống)
    mk.tube(m, "brass", [(-0.05, 0.036, d / 2 + 0.006), (-0.05, 0.01, d / 2 + 0.012),
                         (-0.05, 0.004, d / 2 + 0.014)], 0.0035, sides=6)
    _save(m)
    # Nắp: gốc ở bản lề (node Lid đặt tại (0, h/2, -d/2)), nắp vươn về +Z.
    m = mk.Mesh("pz_tin_lid")
    mk.rbox(m, "tin", (w + 0.006, 0.008, d + 0.006), 0.003, 1, xf=T(0, 0.004, d / 2))
    mk.rbox(m, "tin", (w - 0.03, 0.004, d - 0.03), 0.006, 2, xf=T(0, 0.009, d / 2))
    for sx in (-1, 1):
        mk.box(m, "tin", (0.004, 0.014, d + 0.006), T(sx * (w / 2 + 0.003), -0.004, d / 2))
    mk.box(m, "tin", (w + 0.006, 0.014, 0.004), T(0, -0.004, d + 0.003))
    _save(m)


def build_match_jar():
    """Lọ thủy tinh nhỏ đựng diêm, nắp thiếc. Đáy y = -0.03 (khớp trụ cũ cao 0.06 tâm ở gốc)."""
    m = mk.Mesh("pz_match_jar")
    mk.lathe(m, "glass", [(0.0, -0.03), (0.02, -0.03), (0.022, -0.026), (0.022, 0.018), (0.018, 0.022),
                          (0.018, 0.026), (0.0, 0.026)], 18)
    mk.lathe(m, "lid", [(0.0, 0.024), (0.0195, 0.024), (0.0195, 0.034), (0.0, 0.035)], 18)
    rng = random.Random(7)
    for k in range(14):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.0, 0.014)
        x, z = r * math.cos(a), r * math.sin(a)
        tilt = rng.uniform(-8, 8)
        mk.box(m, "stick", (0.0024, 0.045, 0.0024), T(x, -0.006, z) * RZ(tilt))
        mk.ellipsoid(m, "head", (0.0022, 0.0035, 0.0022), 6, 4, xf=T(x, -0.006, z) * RZ(tilt) * T(0, 0.024, 0))
    _save(m)


def build_book():
    """Sổ bìa cứng (sổ nhật trình / vở học trò), nằm trong mặt XZ, gáy ở -X, tâm ở gốc. 0.09 x 0.012 x 0.12."""
    m = mk.Mesh("pz_book")
    w, h, d = 0.09, 0.012, 0.12
    mk.box(m, "pages", (w - 0.006, h - 0.003, d - 0.006), T(0.002, 0, 0))
    for sy in (-1, 1):
        mk.box(m, "cover", (w, 0.0015, d), T(0, sy * (h / 2 - 0.00075), 0))
    mk.tube(m, "cover", [(-w / 2, 0, d / 2), (-w / 2, 0, -d / 2)], h / 2, sides=8, caps=False)
    _save(m)


def build_open_notebook():
    """Vở học trò mở, trang cong lên, ló khỏi miệng cặp. Gáy theo trục Z tại gốc."""
    m = mk.Mesh("pz_open_notebook")
    for side in (-1, 1):
        def page(u, v, side=side, lift=0.0):
            x = side * 0.085 * u
            y = 0.012 * math.sin(u * math.pi * 0.9) + 0.004 + lift
            return (x, y, (v - 0.5) * 0.2)
        mk.grid(m, "pages", page, 6, 1, uv_fn=lambda u, v, p, s=side: (0.5 + s * 0.5 * u, v), double=True)
        mk.box(m, "cover", (0.088, 0.002, 0.205), T(side * 0.044, 0.0, 0))
    _save(m)


def build_paper_sheet():
    """Tờ giấy nhàu (giấy phép, giấy tờ) 1 x 1, scale khi đặt. UV 0..1."""
    m = mk.Mesh("pz_paper_sheet")
    card(m, "paper", 1.0, 1.0, nu=6, nv=4,
         bend=lambda x, z: 0.02 * math.sin(x * 9.0) * math.cos(z * 5.0) + 0.03 * max(0.0, x - 0.3))
    _save(m)


def build_biscuit_tin():
    """Hộp bánh quy thiếc tròn r 0.1, cao 0.09, đáy ở y = 0; nắp riêng (pz_biscuit_lid), gốc ở mép dưới nắp."""
    m = mk.Mesh("pz_biscuit_can")
    mk.lathe(m, "side", [(0.0985, 0.004), (0.1, 0.008), (0.1, 0.075)], 32)
    mk.lathe(m, "rim", [(0.0, 0.0), (0.094, 0.0), (0.099, 0.002), (0.0985, 0.004)], 32)
    mk.lathe(m, "rim", [(0.1, 0.075), (0.097, 0.078), (0.097, 0.086), (0.093, 0.087), (0.093, 0.01),
                        (0.0, 0.01)], 32)
    _save(m)
    m = mk.Mesh("pz_biscuit_lid")
    mk.lathe(m, "rim", [(0.0985, 0.0), (0.1035, 0.0), (0.104, 0.004), (0.104, 0.017), (0.1, 0.02),
                        (0.096, 0.02)], 32)
    disk_planar(m, "top", 0.096, 0.02, 32)
    _save(m)


def build_clog():
    """Guốc mộc Việt: đế gỗ một khối, gót cao, mũi vát, quai vải/da bản rộng. Mũi guốc hướng -Z.
    Tâm ở gốc, đáy ở y = -0.0125 (khớp khối cũ 0.08 x 0.025 x 0.2)."""
    m = mk.Mesh("pz_clog")
    side = [(-0.1, -0.0125), (0.1, -0.0125), (0.1, 0.03), (0.07, 0.03), (0.06, 0.005), (-0.07, 0.0),
            (-0.095, 0.006), (-0.1, 0.003)]
    # đùn theo X (bề ngang 0.08): biên dạng (z, y) -> xoay để trục đùn là X
    prof = [(z, y) for z, y in side]
    mk.extrude(m, "wood", prof, -0.04, 0.04, xf=RY(-90), closed=True, caps=True)
    # Quai: dải cong ôm mu bàn chân
    def strap(u, v):
        a = math.pi * u
        return (-0.045 * math.cos(a), 0.003 + 0.04 * math.sin(a), -0.045 + (v - 0.5) * 0.035)
    mk.grid(m, "strap", strap, 10, 1, double=True)
    for sx in (-1, 1):
        mk.box(m, "nail", (0.006, 0.006, 0.006), T(sx * 0.044, 0.003, -0.05))
    _save(m)


def build_basin():
    """Chậu sắt tráng men cũ: miệng r 0.2, đáy r 0.14, sâu 0.12, vành cuộn. Đáy ở y = 0."""
    m = mk.Mesh("pz_basin")
    prof = [(0.0, 0.0), (0.13, 0.0), (0.14, 0.006), (0.195, 0.115), (0.204, 0.12), (0.21, 0.126), (0.205, 0.131),
            (0.198, 0.126), (0.19, 0.117), (0.135, 0.01), (0.0, 0.01)]
    mk.lathe(m, "iron", prof, 36)
    rng = random.Random(4)
    ash = []
    for k in range(37):
        a = 2 * math.pi * k / 36
        ash.append(a)
    def ashf(u, v):
        a = 2 * math.pi * u
        r = 0.15 * v
        y = 0.013 + 0.012 * (1 - v) * (0.6 + 0.4 * math.sin(a * 3 + 1)) + 0.012 * v * v
        return (r * math.cos(a), y, -r * math.sin(a))
    mk.grid(m, "ash", ashf, 18, 4, wrap_u=True, flip=True)
    for k in range(6):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.03, 0.12)
        mk.box(m, "ash", (0.04, 0.003, 0.03), T(r * math.cos(a), 0.03, r * math.sin(a)) * RY(rng.uniform(0, 180))
               * RX(rng.uniform(-12, 12)))
    _save(m)


def build_boombox():
    """Đài cát-sét hai loa (kiểu đài Nhật thập niên 80-90): thân 0.32 x 0.12 x 0.09, tâm ở gốc, mặt loa
    quay -Z, quai xách trên nóc."""
    m = mk.Mesh("pz_boombox")
    w, h, d = 0.32, 0.12, 0.09
    mk.rbox(m, "body", (w, h, d), 0.012, 2)
    for sx in (-1, 1):
        mk.lathe(m, "body", [(0.0, 0.0), (0.043, 0.0), (0.045, 0.003), (0.041, 0.004)], 24,
                 T(sx * 0.095, -0.005, -d / 2) * RX(-90))
        disk_planar(m, "grille", 0.04, 0.0035, 24, T(sx * 0.095, -0.005, -d / 2) * RX(-90))
        mk.lathe(m, "chrome", [(0.0, 0.0), (0.009, 0.0), (0.008, 0.006), (0.0, 0.007)], 12,
                 T(sx * 0.095, -0.005, -d / 2 - 0.004) * RX(-90))
    # Cửa băng giữa: khung + kính
    mk.rbox(m, "chrome", (0.1, 0.06, 0.006), 0.003, 1, xf=T(0, 0.005, -d / 2 - 0.001))
    mk.box(m, "window", (0.084, 0.044, 0.004), T(0, 0.005, -d / 2 - 0.004))
    mk.box(m, "tape", (0.06, 0.03, 0.002), T(0, 0.005, -d / 2 - 0.0005))
    # Phím bấm trên nóc
    for k in range(6):
        mk.rbox(m, "chrome", (0.016, 0.008, 0.024), 0.002, 1, xf=T(-0.045 + k * 0.018, h / 2 + 0.003, -0.02))
    # Núm vặn hai bên
    for k, x in enumerate((-0.13, 0.13)):
        mk.lathe(m, "chrome", [(0.0, 0.0), (0.009, 0.0), (0.009, 0.01), (0.0, 0.011)], 12,
                 T(x, h / 2, 0.015))
    # Quai xách chrome
    path = mk.round_path([(-0.12, h / 2, 0.0), (-0.11, h / 2 + 0.05, 0.0), (0.11, h / 2 + 0.05, 0.0),
                          (0.12, h / 2, 0.0)], 0.025, 4)
    mk.tube(m, "chrome", path, 0.006, sides=8)
    # Ăng-ten gập
    mk.tube(m, "chrome", [(0.14, h / 2 - 0.01, 0.03), (-0.1, h / 2 + 0.006, 0.035)], 0.0022, sides=5)
    _save(m)


def build_schoolbag():
    """Cặp sách vải bạt có nắp, quai đeo, khóa cài. 0.3 x 0.24 x 0.1, tâm ở gốc, mặt nắp quay -Z."""
    m = mk.Mesh("pz_schoolbag")
    w, h, d = 0.3, 0.24, 0.1

    def puff(p, n):
        k = 1.0 + 0.12 * (1 - (2 * p[0] / w) ** 2) * (1 - (2 * p[1] / h) ** 2)
        return (p[0], p[1], p[2] * k), n
    mk.rbox(m, "canvas", (w, h, d), 0.025, 2, deform=puff)
    def flap(u, v):
        x = (u - 0.5) * (w + 0.01)
        y = h / 2 + 0.005 - v * h * 0.62
        z = -d / 2 - 0.012 - 0.008 * math.sin(math.pi * u) - 0.01 * math.sin(v * math.pi * 0.5)
        if v < 0.15:
            z = -d / 2 + (z + d / 2) * v / 0.15
            y = h / 2 + 0.005 + 0.004 * (1 - v / 0.15)
        return (x, y, z)
    mk.grid(m, "leather", flap, 6, 6, double=True)
    for sx in (-1, 1):
        mk.box(m, "leather", (0.025, 0.12, 0.004), T(sx * 0.07, h / 2 - h * 0.62 + 0.03, -d / 2 - 0.03))
        mk.box(m, "metal", (0.03, 0.02, 0.006), T(sx * 0.07, h / 2 - h * 0.62 - 0.005, -d / 2 - 0.03))
    path = mk.round_path([(-0.06, h / 2, 0.0), (-0.05, h / 2 + 0.05, 0.0), (0.05, h / 2 + 0.05, 0.0),
                          (0.06, h / 2, 0.0)], 0.02, 3)
    mk.tube(m, "leather", path, 0.008, sides=6)
    _save(m)


# ---------------------------------------------------------------------------
# ĐÊM 1999
# ---------------------------------------------------------------------------

def build_herb_pack():
    """Gói thuốc bắc: giấy dó gói vuông, gấp mép, buộc dây đỏ chữ thập. 0.2 x 0.1 x 0.14, tâm ở gốc."""
    m = mk.Mesh("pz_herb_pack")
    w, h, d = 0.2, 0.1, 0.14

    def bulge(p, n):
        k = 1.0 + 0.1 * (1 - (2 * p[0] / w) ** 2) * (1 - (2 * p[2] / d) ** 2)
        return (p[0], p[1] * k, p[2]), n
    mk.rbox(m, "paper", (w, h, d), 0.012, 2, deform=bulge)
    # Mép giấy gấp chéo trên nóc
    mk.polygon(m, "paper", [(-w / 2 + 0.01, h / 2 + 0.006, -d / 2 + 0.01), (w / 2 - 0.01, h / 2 + 0.006, -d / 2 + 0.01),
                            (0.02, h / 2 + 0.008, 0.02)], (0, 1, 0))
    for path in ([(-w / 2 - 0.002, 0, 0), (-w / 2 - 0.002, h / 2 + 0.006, 0), (w / 2 + 0.002, h / 2 + 0.006, 0),
                  (w / 2 + 0.002, -h / 2 - 0.002, 0), (-w / 2 - 0.002, -h / 2 - 0.002, 0), (-w / 2 - 0.002, 0, 0)],
                 [(0, 0, -d / 2 - 0.002), (0, h / 2 + 0.011, -d / 2 - 0.002), (0, h / 2 + 0.011, d / 2 + 0.002),
                  (0, -h / 2 - 0.002, d / 2 + 0.002), (0, -h / 2 - 0.002, -d / 2 - 0.002), (0, 0, -d / 2 - 0.002)]):
        mk.tube(m, "string", path, 0.0022, sides=4)
    # Nút buộc + hai đầu dây
    mk.ellipsoid(m, "string", (0.008, 0.006, 0.008), 6, 4, xf=T(0, h / 2 + 0.012, 0))
    mk.tube(m, "string", [(0, h / 2 + 0.013, 0), (0.02, h / 2 + 0.016, -0.02), (0.035, h / 2 + 0.01, -0.03)],
            0.0018, sides=4)
    _save(m)


def build_dieu_cay():
    """Điếu cày: ống tre dài 0.55 có đốt, nõ điếu cắm xiên, dọc trục Y, tâm ở gốc."""
    m = mk.Mesh("pz_dieu_cay")
    L, r = 0.55, 0.026
    mk.tube(m, "bamboo", [(0, -L / 2, 0), (0, L / 2, 0)], r, sides=14, caps=True)
    for y in (-0.16, 0.06, 0.22):
        mk.tube(m, "node", mk.arc((0, y, 0), r + 0.001, 0, 360, 16, "xz")[:-1], 0.0035, sides=5, closed=True)
    # Miệng hút bọc đồng, nõ điếu
    mk.lathe(m, "metal", [(0.0, 0.0), (r + 0.002, 0.0), (r + 0.002, 0.03), (r - 0.004, 0.032), (0.0, 0.032)], 14,
             T(0, L / 2 - 0.02, 0))
    mk.tube(m, "bamboo", [(0, -0.12, -r + 0.004), (0, -0.09, -r - 0.04)], 0.007, sides=8)
    mk.lathe(m, "metal", [(0.0, -0.01), (0.008, -0.01), (0.012, 0.012), (0.009, 0.014), (0.0, 0.004)], 10,
             T(0, -0.085, -r - 0.045) * RX(-38))
    _save(m)


def build_plaque():
    """Biển bến gỗ sơn trắng chữ đỏ (chữ là Label3D): 0.24 x 0.075 x 0.012, mặt chữ quay +Z, tâm ở gốc.
    Viền gỗ + lỗ treo hai đầu."""
    m = mk.Mesh("pz_plaque")
    mk.rbox(m, "wood", (0.24, 0.075, 0.012), 0.004, 1)
    mk.box(m, "paint", (0.22, 0.058, 0.002), T(0, 0, 0.0061))
    for sx in (-1, 1):
        mk.tube(m, "metal", mk.arc((sx * 0.105, 0.025, 0.0065), 0.0045, 0, 360, 10, "xy")[:-1], 0.0012, sides=4,
                closed=True)
    _save(m)


def build_satchel():
    """Túi da đeo chéo của phụ xe: thân phồng, nắp gập, khóa cài đồng. 0.22 x 0.18 x 0.08, tâm ở gốc,
    nắp quay -Z."""
    m = mk.Mesh("pz_satchel")
    w, h, d = 0.22, 0.18, 0.08

    def puff(p, n):
        k = 1.0 + 0.15 * (1 - (2 * p[0] / w) ** 2) * (1 - (2 * p[1] / h) ** 2)
        return (p[0], p[1], p[2] * k), n
    mk.rbox(m, "leather", (w, h, d), 0.02, 2, deform=puff)

    def flap(u, v):
        x = (u - 0.5) * (w + 0.012)
        x *= 1.0 - 0.15 * v * v
        y = h / 2 + 0.004 - v * h * 0.7
        z = -d / 2 - 0.014 - 0.008 * math.sin(math.pi * u)
        if v < 0.12:
            z = -d / 2 + (z + d / 2) * v / 0.12
        return (x, y, z)
    mk.grid(m, "leather", flap, 6, 6, double=True)
    mk.box(m, "leather", (0.02, 0.05, 0.004), T(0, h / 2 - h * 0.7 + 0.01, -d / 2 - 0.02))
    mk.rbox(m, "metal", (0.03, 0.022, 0.006), 0.003, 1, xf=T(0, h / 2 - h * 0.7 - 0.004, -d / 2 - 0.022))
    _save(m)


def build_strap():
    """Quai da đeo chéo (dải dẹt dài 0.6 theo trục Y), tâm ở gốc."""
    m = mk.Mesh("pz_strap")
    mk.rbox(m, "leather", (0.03, 0.6, 0.006), 0.002, 1)
    _save(m)


def build_ticket_stack():
    """Xấp cuống vé xòe nhẹ, kẹp dây chun. Tâm ở gốc, giấy nằm trong mặt XZ (0.06 x 0.1)."""
    m = mk.Mesh("pz_tickets")
    rng = random.Random(21)
    for k in range(7):
        card(m, "ticket", 0.06, 0.1, T(rng.uniform(-0.003, 0.003), 0.0016 * k, rng.uniform(-0.004, 0.004))
             * RY(k * 4 - 10 + rng.uniform(-2, 2)), nu=2, nv=3,
             bend=lambda x, z: 0.004 * (z / 0.05) ** 2)
    mk.tube(m, "band", [(-0.031, 0.013, -0.02), (-0.031, -0.002, -0.02), (0.031, -0.002, -0.02),
                        (0.031, 0.013, -0.02), (-0.031, 0.013, -0.02)], 0.0015, sides=4)
    _save(m)


def build_bell_rope():
    """Dây chuông bện thô buông từ trần, đầu dây có nút + tua. Dọc trục Y dài 0.4, tâm ở gốc."""
    m = mk.Mesh("pz_bell_rope")
    path = [(0.003 * math.sin(t * 7), 0.2 - 0.4 * t, 0.003 * math.cos(t * 5)) for t in [k / 16 for k in range(17)]]
    for k in range(3):
        a = 2 * math.pi * k / 3
        strand = [(p[0] + 0.0025 * math.cos(a + i * 0.9), p[1], p[2] + 0.0025 * math.sin(a + i * 0.9))
                  for i, p in enumerate(path)]
        mk.tube(m, "rope", strand, 0.0028, sides=5)
    mk.ellipsoid(m, "rope", (0.012, 0.014, 0.012), 8, 6, xf=T(0, -0.2, 0))
    rng = random.Random(3)
    for k in range(7):
        a = 2 * math.pi * k / 7
        mk.tube(m, "rope", [(0.006 * math.cos(a), -0.205, 0.006 * math.sin(a)),
                            (0.012 * math.cos(a), -0.25 - rng.uniform(0, 0.02), 0.012 * math.sin(a))], 0.0016,
                sides=3)
    _save(m)


def build_thermos():
    """Phích nước thân sắt tráng men in hoa, nắp cốc nhựa, quai xách. Cao 0.28, r 0.045, dọc trục Y,
    tâm ở gốc (khớp trụ cũ)."""
    m = mk.Mesh("pz_thermos")
    r, H = 0.045, 0.28
    mk.lathe(m, "body", [(r, -H / 2 + 0.02), (r, H / 2 - 0.06)], 28)
    mk.lathe(m, "metal", [(0.0, -H / 2), (r - 0.004, -H / 2), (r + 0.002, -H / 2 + 0.006), (r + 0.002, -H / 2 + 0.02),
                          (r, -H / 2 + 0.022)], 28)
    mk.lathe(m, "metal", [(r, H / 2 - 0.062), (r + 0.002, H / 2 - 0.06), (r + 0.002, H / 2 - 0.05),
                          (0.03, H / 2 - 0.035), (0.028, H / 2 - 0.03)], 28)
    # Nắp cốc nhựa
    mk.lathe(m, "cap", [(0.0, H / 2 - 0.035), (0.034, H / 2 - 0.035), (0.036, H / 2 + 0.01), (0.033, H / 2 + 0.012),
                        (0.0, H / 2 + 0.012)], 24)
    for sy in (-1, 1):
        mk.tube(m, "metal", mk.arc((0, H / 2 - 0.05 if sy > 0 else -H / 2 + 0.03, 0), r + 0.003, 0, 360, 24,
                                   "xz")[:-1], 0.0025, sides=4, closed=True)
    path = mk.round_path([(r + 0.003, -H / 2 + 0.03, 0), (r + 0.02, -H / 2 + 0.05, 0), (r + 0.02, H / 2 - 0.07, 0),
                          (r + 0.003, H / 2 - 0.05, 0)], 0.02, 3)
    mk.tube(m, "metal", path, 0.004, sides=6)
    _save(m)


def build_sandal():
    """Dép nhựa trẻ con: đế hình bàn chân + quai chéo. Dài 0.15, mũi hướng -Z, đáy ở y = -0.01."""
    m = mk.Mesh("pz_sandal")
    outline = []
    for k in range(24):
        a = 2 * math.pi * k / 24
        x = 0.032 * math.cos(a)
        z = 0.075 * math.sin(a)
        if z < 0:
            x *= 1.12        # nửa trước rộng hơn
        x += 0.006 * math.sin(a) * (1 if z < 0 else 0)
        outline.append((x, z))
    prof = [(x, -z) for x, z in reversed(outline)]
    mk.extrude(m, "plastic", prof, -0.01, 0.002, xf=RX(-90), closed=True, caps=True)
    for sx in (-1, 1):
        mk.tube(m, "strap", [(sx * 0.034, 0.0, -0.01), (sx * 0.02, 0.022, -0.03), (0.0, 0.026, -0.04),
                             (-sx * 0.02, 0.022, -0.05), (-sx * 0.036, 0.0, -0.058)], 0.0055, sides=6)
    _save(m)


def build_vial():
    """Lọ dầu gió thủy tinh xanh nắp vàng, cao 0.06, tâm ở gốc."""
    m = mk.Mesh("pz_vial")
    mk.lathe(m, "glass", [(0.0, -0.03), (0.016, -0.03), (0.019, -0.026), (0.019, 0.016), (0.012, 0.024),
                          (0.008, 0.026), (0.008, 0.03), (0.0, 0.03)], 16)
    mk.lathe(m, "oil", [(0.0, -0.027), (0.017, -0.027), (0.017, 0.012), (0.0, 0.012)], 14)
    mk.lathe(m, "cap", [(0.0, 0.028), (0.0105, 0.028), (0.0105, 0.044), (0.0, 0.045)], 14)
    _save(m)


def build_all():
    build_talisman_wrap()
    build_lamp_hook()
    build_kerosene_bottle()
    build_spool()
    build_tin_box()
    build_match_jar()
    build_book()
    build_open_notebook()
    build_paper_sheet()
    build_biscuit_tin()
    build_clog()
    build_basin()
    build_boombox()
    build_schoolbag()
    build_herb_pack()
    build_dieu_cay()
    build_plaque()
    build_satchel()
    build_strap()
    build_ticket_stack()
    build_bell_rope()
    build_thermos()
    build_sandal()
    build_vial()


if __name__ == "__main__":
    build_all()
    print("prop models:", len([k for k in MODELS if k.startswith("pz_")]))
