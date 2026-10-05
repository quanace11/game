#!/usr/bin/env python3
"""Sinh mesh chi tiết cho chiếc xe khách (vỏ xe, ghế, buồng lái, giá hành lý...) ra
assets/models/bus/*.obj. tools/bus_blockout.py gọi build_all() trước khi ghi scene.

Mẫu tham chiếu: xe khách liên tỉnh Việt Nam thập niên 1990 (kiểu Karosa / W50 đóng lại thùng):
ghế lưng cao bọc giả da có khăn trùm, tay vịn mạ crôm trên đầu ghế, cửa sổ kính lùa khung nhôm,
rèm vải, giá hành lý ống crôm, trần cong có gân, taplô tôn sơn với vô-lăng to gần nằm ngang.

Mỗi mesh có nhiều khe vật liệu (slot); bus_blockout.py gán vật liệu riêng cho từng lớp xe
(Day 2006 / Night 1999 / Derelict) nên cùng một hình học dùng được cho cả ba lớp.
"""

import math
import os
import random

import mesh_kit as mk
from mesh_kit import RX, RY, RZ, S, T

from bus_blockout import (BENCH_Z, DOOR_Z, H, HALF_W, ROWS, SEAT_W, SEAT_X, WIN_W, WIN_Y, Z_BACK, Z_FRONT)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "models", "bus")
RES = "res://assets/models/bus/"

WALL = 0.08
WALL_TOP = 1.86          # mép trên vách thẳng, từ đây trần cong vào
COVE_X = 0.70            # trần phẳng từ -COVE_X đến COVE_X
SILL_Y = 0.88            # gờ nhôm dưới cửa sổ: chia sơn vách dưới / trên
WINDSHIELD_Y = (1.02, 1.84)
WINDSHIELD_HALF = 1.15
REAR_WIN = (0.8, 1.1, 1.7)  # nửa rộng, mép dưới, mép trên
DRIVER_WIN_Z = (-4.85, -3.75)
DOOR_TOP = 1.80
RACK_Z = (-3.45, 4.05)
WINDOW_ZS = ROWS + [BENCH_Z]

MODELS = {}   # tên -> danh sách slot (thứ tự surface)


def roof_y(x):
    """Chiều cao trần tại hoành độ x."""
    ax = abs(x)
    if ax <= COVE_X:
        return H
    a = HALF_W - COVE_X
    b = H - WALL_TOP
    t = min((ax - COVE_X) / a, 1.0)
    return WALL_TOP + b * math.sqrt(max(0.0, 1.0 - t * t))


def roof_profile(n=14):
    """Biên dạng trần từ trái sang phải (pháp tuyến hướng xuống, vào lòng xe)."""
    pts = []
    a = HALF_W - COVE_X
    b = H - WALL_TOP
    for k in range(n + 1):
        ang = math.pi * k / (2 * n)            # 0 -> 90 độ
        pts.append((-(COVE_X + a * math.cos(ang)), WALL_TOP + b * math.sin(ang)))
    for k in range(1, 5):
        pts.append((-COVE_X + 2 * COVE_X * k / 4, H))
    for k in range(n - 1, -1, -1):
        ang = math.pi * k / (2 * n)
        pts.append((COVE_X + a * math.cos(ang), WALL_TOP + b * math.sin(ang)))
    return pts


def save(mesh):
    mesh.write_obj(os.path.join(OUT_DIR, mesh.name + ".obj"))
    MODELS[mesh.name] = list(mesh.slots)
    return mesh


def mirror_x(mesh, name):
    m = mk.Mesh(name)
    for slot in mesh.slots:
        v, n, uv, t = mesh.data[slot]
        m.add(slot, [(-p[0], p[1], p[2]) for p in v], [(-q[0], q[1], q[2]) for q in n], uv,
              [(a, c, b) for a, b, c in t])
    return m


# ---------------------------------------------------------------------------
# Vách có ô cửa
# ---------------------------------------------------------------------------

def _rect_x(mesh, slot, x, za, zb, ya, yb, facing):
    """Tấm phẳng vuông góc trục X. facing = -1: pháp tuyến -X."""
    if facing < 0:
        pts = [(x, ya, za), (x, ya, zb), (x, yb, zb), (x, yb, za)]
        uvs = [(za, ya), (zb, ya), (zb, yb), (za, yb)]
    else:
        pts = [(x, ya, zb), (x, ya, za), (x, yb, za), (x, yb, zb)]
        uvs = [(-zb, ya), (-za, ya), (-za, yb), (-zb, yb)]
    mesh.add(slot, pts, [(facing, 0, 0)] * 4, uvs, [(0, 1, 2), (0, 2, 3)])


def _rect_z(mesh, slot, z, xa, xb, ya, yb, facing):
    if facing > 0:
        pts = [(xa, ya, z), (xb, ya, z), (xb, yb, z), (xa, yb, z)]
        uvs = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
    else:
        pts = [(xb, ya, z), (xa, ya, z), (xa, yb, z), (xb, yb, z)]
        uvs = [(-xb, ya), (-xa, ya), (-xa, yb), (-xb, yb)]
    mesh.add(slot, pts, [(0, 0, facing)] * 4, uvs, [(0, 1, 2), (0, 2, 3)])


def _rect_y(mesh, slot, y, xa, xb, za, zb, facing):
    if facing > 0:
        pts = [(xa, y, zb), (xb, y, zb), (xb, y, za), (xa, y, za)]
    else:
        pts = [(xa, y, za), (xb, y, za), (xb, y, zb), (xa, y, zb)]
    uvs = [(p[0], p[2]) for p in pts]
    mesh.add(slot, pts, [(0, facing, 0)] * 4, uvs, [(0, 1, 2), (0, 2, 3)])


def _split_y(intervals, splits):
    out = []
    for a, b in intervals:
        cuts = [a] + [s for s in splits if a < s < b] + [b]
        out += list(zip(cuts[:-1], cuts[1:]))
    return out


def side_wall(mesh, side, openings, slot_fn, reveal_slot):
    """Vách bên (side = -1 trái / 1 phải). openings: [(z0, z1, y0, y1)]."""
    x_in = side * HALF_W
    x_out = side * (HALF_W + WALL)
    zs = sorted(set([Z_FRONT, Z_BACK] + [o[0] for o in openings] + [o[1] for o in openings]))
    for za, zb in zip(zs[:-1], zs[1:]):
        holes = sorted((o[2], o[3]) for o in openings if o[0] <= za + 1e-6 and o[1] >= zb - 1e-6)
        solid = []
        y = 0.0
        for h0, h1 in holes:
            if h0 > y:
                solid.append((y, h0))
            y = max(y, h1)
        if y < WALL_TOP:
            solid.append((y, WALL_TOP))
        for ya, yb in _split_y(solid, [SILL_Y]):
            _rect_x(mesh, slot_fn((ya + yb) / 2), x_in, za, zb, ya, yb, -side)
    # Thành ô cửa (độ dày vách)
    for z0, z1, y0, y1 in openings:
        xa, xb = min(x_in, x_out), max(x_in, x_out)
        if y0 > 0.001:
            _rect_y(mesh, reveal_slot, y0, xa, xb, z0, z1, 1)
        _rect_y(mesh, reveal_slot, y1, xa, xb, z0, z1, -1)
        for z, f in ((z0, 1), (z1, -1)):
            pts_x = (xa, xb)
            _rect_z(mesh, reveal_slot, z, pts_x[0], pts_x[1], y0, y1, f)


def build_shell():
    """Vỏ trong của xe: vách, vách đầu (khung kính lái), vách sau, trần cong có gân."""
    m = mk.Mesh("bus_shell")
    low = lambda y: "wall_low" if y < SILL_Y else "wall_up"
    win = [(z - WIN_W / 2, z + WIN_W / 2, WIN_Y[0], WIN_Y[1]) for z in WINDOW_ZS]
    side_wall(m, -1, win + [(DRIVER_WIN_Z[0], DRIVER_WIN_Z[1], 0.95, 1.75)], low, "reveal")
    side_wall(m, 1, win + [(DOOR_Z[0], DOOR_Z[1], 0.0, DOOR_TOP)], low, "reveal")
    # Vách đầu: dưới kính lái, hai cột kính, phần vòm trên.
    _rect_z(m, "wall_low", Z_FRONT, -HALF_W, HALF_W, 0.0, WINDSHIELD_Y[0], 1)
    for sx in (-1, 1):
        xa, xb = sorted((sx * WINDSHIELD_HALF, sx * HALF_W))
        _rect_z(m, "wall_up", Z_FRONT, xa, xb, WINDSHIELD_Y[0], WALL_TOP, 1)
    xs = [-HALF_W + 2 * HALF_W * k / 24 for k in range(25)]
    for xa, xb in zip(xs[:-1], xs[1:]):
        y0 = WINDSHIELD_Y[1] if max(abs(xa), abs(xb)) <= WINDSHIELD_HALF + 1e-6 else WALL_TOP
        if abs(xa) > WINDSHIELD_HALF - 1e-6 or abs(xb) > WINDSHIELD_HALF + 1e-6:
            y0 = WALL_TOP
        pts = [(xa, y0, Z_FRONT), (xb, y0, Z_FRONT), (xb, roof_y(xb), Z_FRONT), (xa, roof_y(xa), Z_FRONT)]
        m.add("wall_up", pts, [(0, 0, 1)] * 4, [(p[0], p[1]) for p in pts], [(0, 1, 2), (0, 2, 3)])
    # Phần vách dưới mép kính (giữa 1.84 và 1.86) ở hai cột đã phủ; dải giữa kính lái và vòm:
    # Vách sau với ô kính sau.
    rw, ry0, ry1 = REAR_WIN
    _rect_z(m, "wall_low", Z_BACK, -HALF_W, HALF_W, 0.0, SILL_Y, -1)
    _rect_z(m, "wall_up", Z_BACK, -HALF_W, HALF_W, SILL_Y, ry0, -1)
    for sx in (-1, 1):
        xa, xb = sorted((sx * rw, sx * HALF_W))
        _rect_z(m, "wall_up", Z_BACK, xa, xb, ry0, ry1, -1)
    for xa, xb in zip(xs[:-1], xs[1:]):
        pts = [(xb, ry1, Z_BACK), (xa, ry1, Z_BACK), (xa, roof_y(xa), Z_BACK), (xb, roof_y(xb), Z_BACK)]
        m.add("wall_up", pts, [(0, 0, -1)] * 4, [(-p[0], p[1]) for p in pts], [(0, 1, 2), (0, 2, 3)])
    # Trần cong
    prof = roof_profile()
    mk.extrude(m, "ceiling", prof, Z_FRONT, Z_BACK, smooth=True)
    # Gân trần: dải cong nhô xuống ở mỗi cột cửa sổ.
    rib_zs = [z + 0.4 for z in ROWS[:-1]] + [ROWS[0] - 0.4, ROWS[0] - 1.2, Z_FRONT + 0.05, Z_BACK - 0.05]
    for zc in rib_zs:
        _arch_band(m, "rib", prof, zc - 0.03, zc + 0.03, 0.014)
    # Nẹp dọc chạy suốt chiều dài ở chỗ trần bắt đầu cong và chỗ trần phẳng.
    for sx in (-1, 1):
        for (x, y) in ((sx * (HALF_W - 0.004), WALL_TOP - 0.01), (sx * COVE_X, H - 0.004)):
            mk.rbox(m, "rib", (0.03, 0.022, Z_BACK - Z_FRONT), 0.008, segs=1,
                    xf=T(x - sx * 0.008, y, (Z_FRONT + Z_BACK) / 2))
    return save(m)


def _arch_band(m, slot, prof, z0, z1, depth):
    """Dải gân bám theo biên dạng trần, lồi vào trong một đoạn depth."""
    n = len(prof)
    nrm = []
    for i in range(n):
        a = prof[max(i - 1, 0)]
        b = prof[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy) or 1.0
        nrm.append((dy / l, -dx / l))
    inner = [(p[0] + q[0] * depth, p[1] + q[1] * depth) for p, q in zip(prof, nrm)]
    mk.extrude(m, slot, inner, z0, z1, smooth=True)
    # Hai mặt bên của gân
    for z, f in ((z0, -1), (z1, 1)):
        verts, ns, uvs, tris = [], [], [], []
        for i in range(n):
            verts += [(prof[i][0], prof[i][1], z), (inner[i][0], inner[i][1], z)]
            ns += [(0, 0, f)] * 2
            uvs += [(prof[i][0], prof[i][1]), (inner[i][0], inner[i][1])]
        for i in range(n - 1):
            a = i * 2
            if f > 0:
                tris += [(a, a + 2, a + 3), (a, a + 3, a + 1)]
            else:
                tris += [(a, a + 3, a + 2), (a, a + 1, a + 3)]
        m.add(slot, verts, ns, uvs, tris)


def build_floor():
    """Sàn, thảm cao su lối đi, hốc bánh sau, bậc cửa."""
    m = mk.Mesh("bus_floor")
    _rect_y(m, "floor", 0.0, -HALF_W, HALF_W, Z_FRONT, Z_BACK, 1)
    # Thảm cao su lối đi, viền nẹp nhôm
    mk.rbox(m, "runner", (0.58, 0.008, 7.5), 0.003, segs=1, xf=T(0, 0.004, 0.25))
    for sx in (-1, 1):
        mk.rbox(m, "trim", (0.025, 0.01, 7.5), 0.004, segs=1, xf=T(sx * 0.3, 0.005, 0.25))
    # Hốc bánh sau (nổi dưới hàng ghế 7-8), bọc tôn chống trượt
    for sx in (-1, 1):
        mk.rbox(m, "arch", (0.36, 0.3, 1.1), 0.12, segs=4, mid=2, xf=T(sx * (HALF_W - 0.17), 0.13, 2.3))
    # Bậc lên xuống ở cửa: mặt cao su, mũi bậc nẹp nhôm
    dz = (DOOR_Z[0] + DOOR_Z[1]) / 2
    mk.box(m, "step", (0.6, 0.2, 0.9), xf=T(0.95, 0.1, dz))
    mk.rbox(m, "trim", (0.03, 0.035, 0.9), 0.008, segs=1, xf=T(0.655, 0.19, dz))
    # Nẹp chân vách (len tường) dọc hai bên
    for sx in (-1, 1):
        mk.rbox(m, "trim", (0.02, 0.08, Z_BACK - Z_FRONT), 0.006, segs=1,
                xf=T(sx * (HALF_W - 0.01), 0.04, (Z_FRONT + Z_BACK) / 2))
    return save(m)


# ---------------------------------------------------------------------------
# Khung cửa sổ nhôm, kính, rèm
# ---------------------------------------------------------------------------

def _frame_ring(m, slot, cx, cy, w, h, t, depth, xf):
    """Khung chữ nhật (mặt phẳng XY cục bộ, nhô về +Z)."""
    for (x, y, sw, sh) in ((cx, cy - h / 2 + t / 2, w, t), (cx, cy + h / 2 - t / 2, w, t),
                           (cx - w / 2 + t / 2, cy, t, h - 2 * t), (cx + w / 2 - t / 2, cy, t, h - 2 * t)):
        mk.box(m, slot, (sw, sh, depth), xf=xf * T(x, y, 0))


def _side_xf(side, z):
    """Khung tọa độ cục bộ cho chi tiết trên vách: X cục bộ chạy dọc thân xe, +Z cục bộ hướng vào lòng xe."""
    # side = 1 (vách phải): mặt trong nhìn về -X.
    return T(side * HALF_W, 0, z) * RY(-90 if side > 0 else 90)


def build_window_frames():
    """Khung nhôm cửa sổ, gờ bệ cửa, ray kính lùa, đố giữa (hai bên + cửa lái + kính lái + kính sau)."""
    m = mk.Mesh("bus_window_frames")
    for side in (-1, 1):
        zs = list(WINDOW_ZS)
        for z in zs:
            xf = _side_xf(side, z)
            hgt = WIN_Y[1] - WIN_Y[0]
            _frame_ring(m, "alu", 0, (WIN_Y[0] + WIN_Y[1]) / 2, WIN_W + 0.05, hgt + 0.05, 0.035, 0.025,
                        xf * T(0, 0, 0.005))
            # Đố giữa và ray dưới / trên của hai cánh kính lùa (lùi vào trong lòng vách)
            mk.rbox(m, "alu", (0.03, hgt, 0.03), 0.006, segs=1, xf=xf * T(0, (WIN_Y[0] + WIN_Y[1]) / 2, -0.04))
            for y in (WIN_Y[0] + 0.012, WIN_Y[1] - 0.012):
                mk.rbox(m, "alu", (WIN_W, 0.024, 0.06), 0.006, segs=1, xf=xf * T(0, y, -0.04))
            # Chốt kính
            mk.rbox(m, "rubber", (0.035, 0.05, 0.02), 0.006, segs=1,
                    xf=xf * T(0.03 * side, (WIN_Y[0] + WIN_Y[1]) / 2, -0.02))
        # Gờ bệ cửa sổ nhôm chạy suốt thân xe (trừ chỗ cửa lên xuống)
        z0 = Z_FRONT + 0.1 if side < 0 else DOOR_Z[1] + 0.02
        L = Z_BACK - 0.05 - z0
        mk.rbox(m, "alu", (0.05, 0.035, L), 0.01, segs=1, xf=T(side * (HALF_W - 0.025), SILL_Y + 0.02, z0 + L / 2))
        # Nẹp nhôm dưới mép trần
        mk.rbox(m, "alu", (0.02, 0.03, Z_BACK - Z_FRONT), 0.006, segs=1,
                xf=T(side * (HALF_W - 0.01), WIN_Y[1] + 0.07, (Z_FRONT + Z_BACK) / 2))
    # Cửa sổ bác tài (vách trái, phía trước)
    zc = (DRIVER_WIN_Z[0] + DRIVER_WIN_Z[1]) / 2
    w = DRIVER_WIN_Z[1] - DRIVER_WIN_Z[0]
    _frame_ring(m, "alu", 0, 1.35, w + 0.05, 0.85, 0.035, 0.025, _side_xf(-1, zc) * T(0, 0, 0.005))
    mk.rbox(m, "alu", (0.03, 0.8, 0.03), 0.006, segs=1, xf=_side_xf(-1, zc) * T(0.05, 1.35, -0.04))
    # Kính lái: viền cao su đen + trụ giữa
    _frame_ring(m, "rubber", 0, sum(WINDSHIELD_Y) / 2, 2 * WINDSHIELD_HALF + 0.04,
                WINDSHIELD_Y[1] - WINDSHIELD_Y[0] + 0.04, 0.04, 0.03, T(0, 0, Z_FRONT + 0.012))
    mk.rbox(m, "rubber", (0.06, WINDSHIELD_Y[1] - WINDSHIELD_Y[0], 0.05), 0.012, segs=1,
            xf=T(0, sum(WINDSHIELD_Y) / 2, Z_FRONT - 0.01))
    # Kính sau
    rw, ry0, ry1 = REAR_WIN
    _frame_ring(m, "rubber", 0, (ry0 + ry1) / 2, 2 * rw + 0.04, ry1 - ry0 + 0.04, 0.035, 0.03,
                T(0, 0, Z_BACK - 0.012) * RY(180))
    return save(m)


def _pane(m, glass_slot, frame_slot, z0, z1, y0, y1, xf, frame=True, broken=None, rng=None):
    """Một tấm kính lùa (mặt phẳng XY cục bộ, x dọc thân xe) có khung nhôm mảnh."""
    zc = (z0 + z1) / 2
    w = z1 - z0
    h = y1 - y0
    if broken:
        # Kính vỡ: chỉ còn mảnh răng cưa bám mép dưới và một góc trên.
        pts = [(z0, y0)]
        n = 7
        for k in range(n + 1):
            x = z0 + w * k / n
            y = y0 + rng.uniform(0.05, 0.28) * (0.4 if k in (0, n) else 1.0)
            pts.append((x, y))
        pts.append((z1, y0))
        poly = [(p[0], p[1], 0.0) for p in pts]
        mk.polygon(m, glass_slot, list(reversed(poly)), (0, 0, 1), xf)
        mk.polygon(m, glass_slot, poly, (0, 0, -1), xf)
        corner = [(z1, y1, 0), (z1 - rng.uniform(0.12, 0.25), y1, 0), (z1, y1 - rng.uniform(0.15, 0.3), 0)]
        mk.polygon(m, glass_slot, corner, (0, 0, 1), xf)
        mk.polygon(m, glass_slot, list(reversed(corner)), (0, 0, -1), xf)
    else:
        pts = [(z0, y0, 0), (z1, y0, 0), (z1, y1, 0), (z0, y1, 0)]
        uvs = [(z0, y0), (z1, y0), (z1, y1), (z0, y1)]
        m.add(glass_slot, pts, [(0, 0, 1)] * 4, uvs, [(0, 1, 2), (0, 2, 3)], xf)
        m.add(glass_slot, pts, [(0, 0, 1)] * 4, uvs, [(0, 1, 2), (0, 2, 3)], xf, flip=True)
    if frame:
        _frame_ring(m, frame_slot, zc, (y0 + y1) / 2, w, h, 0.018, 0.012, xf)


def build_glass(variant, rng_seed=5):
    """Kính toàn xe cho một lớp. variant: day (vài ô mở), night (đóng kín), wreck (vỡ, bẩn)."""
    rng = random.Random(rng_seed)
    m = mk.Mesh("bus_glass_" + variant)
    broken = {("R", 1), ("L", 4), ("R", 7), ("L", 8)} if variant == "wreck" else set()
    opened = {("L", 0), ("R", 2), ("L", 3), ("R", 5), ("L", 6)} if variant == "day" else set()
    for side in (-1, 1):
        sname = "L" if side < 0 else "R"
        for i, z in enumerate(WINDOW_ZS):
            xf = _side_xf(side, z)
            y0, y1 = WIN_Y[0] + 0.02, WIN_Y[1] - 0.02
            half = WIN_W / 2
            is_broken = (sname, i) in broken
            # Cánh trước nằm ray ngoài, cánh sau ray trong. Cửa mở: cánh sau lùa chồng lên cánh trước.
            front = (-half + 0.005, 0.015) if side > 0 else (-0.015, half - 0.005)
            back = (-0.015, half - 0.005) if side > 0 else (-half + 0.005, 0.015)
            _pane(m, "glass", "alu", front[0], front[1], y0, y1, xf * T(0, 0, -0.055), broken=is_broken and True,
                  rng=rng)
            if (sname, i) in opened:
                shift = (front[0] - back[0]) * 0.85
                _pane(m, "glass", "alu", back[0] + shift, back[1] + shift, y0, y1, xf * T(0, 0, -0.03))
            elif is_broken:
                _pane(m, "glass", "alu", back[0], back[1], y0, y1, xf * T(0, 0, -0.03), broken=True, rng=rng)
            else:
                _pane(m, "glass", "alu", back[0], back[1], y0, y1, xf * T(0, 0, -0.03))
    # Kính lái (hai nửa), kính cửa lái, kính cánh cửa, kính sau
    for sx in (-1, 1):
        xa, xb = (0.02, WINDSHIELD_HALF) if sx > 0 else (-WINDSHIELD_HALF, -0.02)
        pts = [(xa, WINDSHIELD_Y[0], Z_FRONT - 0.02), (xb, WINDSHIELD_Y[0], Z_FRONT - 0.02),
               (xb, WINDSHIELD_Y[1], Z_FRONT - 0.02), (xa, WINDSHIELD_Y[1], Z_FRONT - 0.02)]
        uvs = [(p[0], p[1]) for p in pts]
        m.add("glass_front", pts, [(0, 0, 1)] * 4, uvs, [(0, 1, 2), (0, 2, 3)])
        m.add("glass_front", pts, [(0, 0, 1)] * 4, uvs, [(0, 1, 2), (0, 2, 3)], flip=True)
    zc = (DRIVER_WIN_Z[0] + DRIVER_WIN_Z[1]) / 2
    w = DRIVER_WIN_Z[1] - DRIVER_WIN_Z[0]
    _pane(m, "glass", "alu", -w / 2 + 0.01, 0.06, 0.97, 1.73, _side_xf(-1, zc) * T(0, 0, -0.05))
    _pane(m, "glass", "alu", 0.04, w / 2 - 0.01, 0.97, 1.73, _side_xf(-1, zc) * T(0, 0, -0.03))
    # Ô kính trên hai cánh cửa gấp
    leaf = (DOOR_Z[1] - DOOR_Z[0]) / 2
    for k in range(2):
        zc = DOOR_Z[0] + leaf * (k + 0.5)
        _pane(m, "glass", "alu", -leaf / 2 + 0.04, leaf / 2 - 0.04, 1.22, DOOR_TOP - 0.055,
              T(HALF_W + 0.02, 0, zc) * RY(-90), frame=False)
    rw, ry0, ry1 = REAR_WIN
    pts = [(rw, ry0, Z_BACK + 0.02), (-rw, ry0, Z_BACK + 0.02), (-rw, ry1, Z_BACK + 0.02), (rw, ry1, Z_BACK + 0.02)]
    uvs = [(p[0], p[1]) for p in pts]
    m.add("glass", pts, [(0, 0, -1)] * 4, uvs, [(0, 1, 2), (0, 2, 3)])
    m.add("glass", pts, [(0, 0, -1)] * 4, uvs, [(0, 1, 2), (0, 2, 3)], flip=True)
    return save(m)


def build_curtains(variant, seed=9):
    """Rèm vải trên thanh treo mỗi ô cửa. day: vén gọn hai bên; night: kéo che một nửa; wreck: rách tả tơi."""
    rng = random.Random(seed)
    m = mk.Mesh("bus_curtains_" + variant)
    for side in (-1, 1):
        for i, z in enumerate(WINDOW_ZS):
            xf = _side_xf(side, z)
            top = WIN_Y[1] + 0.035
            # Thanh treo rèm
            mk.tube(m, "rod", [(-WIN_W / 2 - 0.02, top + 0.01, 0.045), (WIN_W / 2 + 0.02, top + 0.01, 0.045)],
                    0.006, sides=6, xf=xf)
            if variant == "day":
                pieces = [(-WIN_W / 2 + 0.02, 0.13, 0.62), (WIN_W / 2 - 0.15, 0.13, 0.62)]
            elif variant == "night":
                pieces = [(-WIN_W / 2 + 0.02, 0.36 if i % 3 else 0.2, 0.7), (WIN_W / 2 - 0.15, 0.13, 0.66)]
            else:
                if i % 3 == 1:
                    continue
                pieces = [(-WIN_W / 2 + 0.02 + rng.uniform(0, 0.25), rng.uniform(0.1, 0.22), rng.uniform(0.35, 0.8))]
            for (x0, w, h) in pieces:
                _curtain(m, x0, w, h, top, rng, torn=(variant == "wreck"), tied=(variant == "day"), xf=xf)
    return save(m)


def _curtain(m, x0, w, h, top, rng, torn=False, tied=False, xf=None):
    folds = max(3, int(w / 0.035))
    amp = 0.012 + (0.02 if tied else 0.0)
    jag = [rng.uniform(-0.25, 0.0) for _ in range(folds * 2 + 1)] if torn else None

    def fn(u, v):
        x = x0 + u * w
        # Nếp gấp: sóng sin dọc chiều ngang; dải buộc ở giữa thắt rèm lại (rèm ban ngày).
        pinch = 1.0
        if tied:
            pinch = 0.55 + 0.45 * abs(v - 0.45) / 0.55
            x = x0 + w / 2 + (u - 0.5) * w * pinch
        zf = 0.03 + amp * math.sin(u * folds * 2 * math.pi) * (0.6 + 0.4 * v)
        y = top - v * h
        if jag:
            k = u * (len(jag) - 1)
            i = int(k)
            t = k - i
            j = jag[i] * (1 - t) + jag[min(i + 1, len(jag) - 1)] * t
            y = top - v * h * (1.0 + j)
        return (x, y, zf + v * 0.01)

    def uvf(u, v, p):
        return (u * w * 1.6, v * h)
    mk.grid(m, "cloth", fn, folds * 2, 6, uv_fn=uvf, double=True, xf=xf)
    if tied:
        # Dải vải buộc rèm
        mk.rbox(m, "cloth", (w * 0.62, 0.035, 0.05), 0.015, segs=1,
                xf=(xf * T(x0 + w / 2, top - 0.45 * h, 0.035)) if xf else T(x0 + w / 2, top - 0.45 * h, 0.035))


# ---------------------------------------------------------------------------
# Ghế
# ---------------------------------------------------------------------------

BACK_TILT = 10.0
BACK_H = 0.68
BACK_T = 0.075
BACK_Y0 = 0.50
BACK_Z = 0.20           # tâm lưng ghế so với tâm hàng (về phía sau, +Z)
CUSHION_Y = 0.465


def _back_xf():
    pivot = (0.0, BACK_Y0, BACK_Z - 0.03)
    return T(*pivot) * RX(BACK_TILT) * T(-pivot[0], -pivot[1], -pivot[2])


def _cushion(m, slot, cx, w, d, xf=None):
    hx, hz = w / 2, d / 2

    def deform(p, n):
        if p[1] > 0:
            k = (1 - (p[0] / hx) ** 2) * (1 - (p[2] / hz) ** 2)
            p = (p[0], p[1] + 0.014 * max(k, 0), p[2])
        # Mép trước cuộn tròn xuống
        if p[2] < -hz + 0.05:
            p = (p[0], p[1] - 0.008, p[2])
        return p, n
    mk.rbox(m, slot, (w, 0.11, d), 0.04, segs=3, mid=6, deform=deform,
            xf=(xf or mk.I) * T(cx, CUSHION_Y, -0.01))


def _backrest(m, cx, w, xf, pleats=4, slot="vinyl", shell="shell"):
    """Lưng ghế: thân bọc giả da, mặt sau ốp nhựa, mặt trước may chần dọc (pleat)."""
    hy = BACK_H / 2
    yc = BACK_Y0 + hy
    mk.rbox(m, slot, (w, BACK_H, BACK_T), 0.035, segs=3, mid=2,
            slot_fn=lambda n: shell if n[2] > 0.5 else slot,
            xf=xf * T(cx, yc, BACK_Z))
    # Mặt trước phồng, chần thành các múi dọc
    pw, ph = w - 0.05, BACK_H - 0.09
    z_front = BACK_Z - BACK_T / 2 + 0.002

    def fn(u, v):
        bulge = 0.022 * math.sin(math.pi * u) ** 0.6 * math.sin(math.pi * v) ** 0.5
        chan = 0.006 * (1 - abs(math.cos(math.pi * u * pleats)))
        x = cx - pw / 2 + u * pw
        y = BACK_Y0 + 0.04 + v * ph
        # Phần đỡ lưng dưới phồng hơn
        lumbar = 0.012 * math.exp(-((v - 0.3) / 0.18) ** 2) * math.sin(math.pi * u)
        return (x, y, z_front - bulge - chan - lumbar)
    mk.grid(m, slot, fn, pleats * 6, 14, flip=True, xf=xf)


def _cloth_cover(m, cx, w, xf, slot="cloth", drop=0.17, seed=0):
    """Khăn trùm đầu lưng ghế: vắt qua đỉnh, buông xuống trước và sau."""
    rng = random.Random(seed)
    top = BACK_Y0 + BACK_H
    rz = BACK_T / 2 + 0.028
    cw = w - 0.06
    waves = [rng.uniform(-0.01, 0.01) for _ in range(6)]

    def fn(u, v):
        x = cx - cw / 2 + u * cw
        # v: 0 = mép trước dưới, 0.5 = đỉnh, 1 = mép sau dưới. Đoạn đỉnh là nửa vòng tròn.
        L = drop
        arc_len = math.pi * rz
        s = v * (2 * L + arc_len)
        hem = 0.01 * math.sin(u * 9.0 + v * 3) + waves[int(u * 5.99)] * 0.5
        if s < L:
            y = top - 0.035 - (L - s) + hem * (1 - s / L)
            z = BACK_Z - rz
        elif s < L + arc_len:
            a = (s - L) / rz
            y = top - 0.035 + math.sin(a) * rz * 0.9
            z = BACK_Z - rz * math.cos(a)
        else:
            s2 = s - L - arc_len
            y = top - 0.035 - s2 + hem * (s2 / L)
            z = BACK_Z + rz
        # Vải xòe nhẹ ra hai bên ở mép
        z += (0.006 if z > BACK_Z else -0.006) * (abs(u - 0.5) * 2) ** 2
        return (x, y, z)

    def uvf(u, v, p):
        return (u, v)
    mk.grid(m, slot, fn, 12, 24, uv_fn=uvf, xf=xf, double=True)


def _seat_frame(m, w, slot="frame", wall_side=1):
    """Khung ghế đôi bên phải (lối đi ở -X cục bộ). Chân chữ A phía lối đi, giá bắt vách phía cửa sổ."""
    hx = w / 2
    mk.rbox(m, slot, (w - 0.02, 0.035, 0.40), 0.01, segs=1, xf=T(0, 0.392, -0.01))
    ax = -wall_side * (hx - 0.03)
    leg = mk.round_path([(ax, 0.01, -0.17), (ax, 0.385, -0.04), (ax, 0.01, 0.15)], 0.05, 5)
    mk.tube(m, slot, leg, 0.015, sides=10)
    for z in (-0.17, 0.15):
        mk.rbox(m, slot, (0.05, 0.012, 0.07), 0.004, segs=1, xf=T(ax, 0.006, z))
    # Thanh gác chân cho người ngồi sau
    mk.tube(m, slot, [(ax, 0.12, 0.13), (wall_side * (hx - 0.02), 0.12, 0.13)], 0.011, sides=8)
    # Giá bắt vách
    mk.rbox(m, slot, (0.04, 0.12, 0.3), 0.008, segs=1, xf=T(wall_side * (hx - 0.01), 0.33, 0.0))
    # Ống khung lưng hai bên (lộ ra dưới lưng ghế)
    for x in (-hx + 0.04, hx - 0.04):
        mk.tube(m, slot, [(x, 0.39, BACK_Z - 0.04), (x, 0.56, BACK_Z - 0.01)], 0.012, sides=8)


def build_seat_pair():
    """Ghế đôi bên phải; bản bên trái là ảnh gương. Bốn mesh tách rời để lớp xác xe bẻ gãy lưng, rách nệm."""
    w = SEAT_X[1] - SEAT_X[0] + SEAT_W   # 0.84
    hx = w / 2
    centers = (-hx / 2, hx / 2)
    bxf = _back_xf()
    out = {}
    frame = mk.Mesh("seat_frame_R")
    _seat_frame(frame, w)
    cush = mk.Mesh("seat_cushion_R")
    for c in centers:
        _cushion(cush, "vinyl", c, w / 2 - 0.012, 0.42)
    back = mk.Mesh("seat_back_R")
    for c in centers:
        _backrest(back, c, w / 2 - 0.012, bxf)
    # Tay nắm mạ crôm chạy ngang đỉnh lưng ghế + gạt tàn trên lưng ghế phía lối đi
    top = BACK_Y0 + BACK_H
    bar = mk.round_path([(-hx + 0.02, top - 0.04, BACK_Z), (-hx + 0.02, top + 0.06, BACK_Z),
                         (hx - 0.02, top + 0.06, BACK_Z), (hx - 0.02, top - 0.04, BACK_Z)], 0.04, 5)
    mk.tube(back, "chrome", bar, 0.012, sides=10, xf=bxf)
    mk.rbox(back, "chrome", (0.13, 0.05, 0.025), 0.008, segs=1,
            xf=bxf * T(centers[0], 0.86, BACK_Z + BACK_T / 2 + 0.012))
    cloth = mk.Mesh("seat_cloth_R")
    for k, c in enumerate(centers):
        _cloth_cover(cloth, c, w / 2 - 0.012, bxf, seed=k)
    for mesh in (frame, cush, back, cloth):
        save(mesh)
        save(mirror_x(mesh, mesh.name[:-2] + "_L"))
    return out


def build_bench():
    """Băng ghế cuối xe 5 chỗ, lưng tựa vách sau."""
    w = 2 * HALF_W
    n = 5
    sw = (w - 0.04) / n
    bxf = _back_xf()
    base = mk.Mesh("bench_base")
    mk.rbox(base, "shell", (w, 0.39, 0.38), 0.02, segs=1, xf=T(0, 0.195, 0.0))
    mk.rbox(base, "frame", (w, 0.035, 0.42), 0.01, segs=1, xf=T(0, 0.392, -0.01))
    save(base)
    cush = mk.Mesh("bench_cushion")
    back = mk.Mesh("bench_back")
    cloth = mk.Mesh("bench_cloth")
    for k in range(n):
        c = -w / 2 + 0.02 + sw * (k + 0.5)
        _cushion(cush, "vinyl", c, sw - 0.01, 0.42)
        _backrest(back, c, sw - 0.01, bxf)
        _cloth_cover(cloth, c, sw - 0.01, bxf, seed=10 + k)
    for mesh in (cush, back, cloth):
        save(mesh)


def build_driver_seat():
    """Ghế lái đơn, rộng hơn, đặt trên bệ tôn. Gốc tọa độ ở tâm sàn dưới ghế."""
    w = 0.5
    bxf = _back_xf()
    m = mk.Mesh("driver_seat")
    mk.rbox(m, "frame", (0.42, 0.36, 0.42), 0.02, segs=1, xf=T(0, 0.18, 0.0))
    _cushion(m, "vinyl", 0.0, w, 0.46)
    _backrest(m, 0.0, w, bxf, pleats=5)
    # Tựa đầu riêng
    mk.rbox(m, "vinyl", (0.28, 0.16, 0.08), 0.035, segs=3, xf=bxf * T(0, BACK_Y0 + BACK_H + 0.1, BACK_Z))
    for x in (-0.08, 0.08):
        mk.tube(m, "chrome", [(x, BACK_Y0 + BACK_H - 0.02, BACK_Z), (x, BACK_Y0 + BACK_H + 0.04, BACK_Z)], 0.008,
                sides=6, xf=bxf)
    save(m)


# ---------------------------------------------------------------------------
# Giá hành lý, tay vịn trần, cột cửa, đèn trần
# ---------------------------------------------------------------------------

def build_racks():
    m = mk.Mesh("bus_racks")
    z0, z1 = RACK_Z
    for side in (-1, 1):
        for x in (0.86, 0.95, 1.04, 1.13):
            mk.tube(m, "chrome", [(side * x, 1.83, z0), (side * x, 1.83, z1)], 0.009, sides=8)
        mk.tube(m, "chrome", [(side * 0.83, 1.885, z0), (side * 0.83, 1.885, z1)], 0.011, sides=10)
        nb = 6
        for k in range(nb):
            z = z0 + 0.05 + (z1 - z0 - 0.1) * k / (nb - 1)
            path = mk.round_path([(side * (HALF_W - 0.005), 1.75, z), (side * 1.14, 1.83, z), (side * 0.83, 1.83, z),
                                  (side * 0.83, 1.885, z)], 0.03, 4)
            mk.tube(m, "chrome", path, 0.012, sides=8)
            mk.rbox(m, "chrome", (0.012, 0.07, 0.05), 0.004, segs=1, xf=T(side * (HALF_W - 0.006), 1.75, z))
        # Tay vịn dọc trần + quai treo
        mk.tube(m, "chrome", [(side * 0.42, 1.97, -3.55), (side * 0.42, 1.97, 4.0)], 0.016, sides=12)
        for k in range(6):
            z = -3.4 + k * 1.45
            mk.tube(m, "chrome", [(side * 0.42, 1.97, z), (side * 0.42, H, z)], 0.009, sides=8)
            mk.lathe(m, "chrome", [(0.0, H - 0.012), (0.028, H - 0.012), (0.03, H - 0.004), (0.0, H)], 12,
                     xf=T(side * 0.42, 0, z))
        for z in (-3.55, 4.0):
            mk.lathe(m, "chrome", [(0.0, -0.02), (0.019, -0.018), (0.02, 0.0), (0.019, 0.018), (0.0, 0.02)], 12,
                     xf=T(side * 0.42, 1.97, z) * RX(90))
    # Cột vịn ở cửa lên xuống, có đế và chụp
    mk.tube(m, "chrome", [(0.55, 0.0, -3.62), (0.55, H, -3.62)], 0.018, sides=12)
    for y in (0.0, H - 0.02):
        mk.lathe(m, "chrome", [(0.0, 0.0), (0.04, 0.0), (0.04, 0.008), (0.022, 0.02), (0.0, 0.02)], 14,
                 xf=T(0.55, y, -3.62))
    return save(m)


def build_ceiling_lights():
    """Ba hộp đèn tuýp giữa trần (mặt khuếch tán là slot riêng để bật sáng)."""
    m = mk.Mesh("bus_ceiling_lights")
    for z in (-2.5, 0.5, 3.0):
        mk.rbox(m, "housing", (0.17, 0.045, 1.26), 0.012, segs=1, xf=T(0, H - 0.022, z))
        mk.rbox(m, "diffuser", (0.13, 0.012, 1.2), 0.005, segs=1, xf=T(0, H - 0.046, z))
    # Loa và cửa gió nhỏ dọc trần
    for z in (-1.0, 1.9):
        mk.lathe(m, "housing", [(0.0, -0.012), (0.07, -0.012), (0.075, 0.0), (0.0, 0.0)], 18, xf=T(0, H - 0.0, z))
        mk.lathe(m, "grille", [(0.0, -0.013), (0.06, -0.013)], 18, xf=T(0, H, z))
    return save(m)


# ---------------------------------------------------------------------------
# Buồng lái
# ---------------------------------------------------------------------------

def build_dashboard():
    """Taplô tôn sơn: mặt đứng hướng vào khoang, mặt trên phẳng (đồ câu đố đặt lên), cụm đồng hồ trước ghế lái."""
    m = mk.Mesh("dashboard")
    zf = Z_FRONT
    top = 1.10
    # Biên dạng mặt cắt (y, z) đùn dọc trục X: chân taplô -> mặt đứng -> mép cuộn -> mặt trên
    prof_yz = [(0.0, -4.36), (0.86, -4.36), (0.96, -4.38), (1.05, -4.40), (1.095, -4.43), (top, -4.47),
               (top, -4.80), (top, zf)]
    # extrude chạy dọc Z; xoay để chạy dọc X: dùng biên dạng (z, y) trong mặt phẳng rồi xoay 90 độ quanh Y.
    # RY(90) đưa trục Z cục bộ thành +X và trục X cục bộ thành -Z, nên biên dạng dùng (-z, y).
    prof = [(-z, y) for y, z in reversed(prof_yz)]
    mk.extrude(m, "dash", prof, -HALF_W, HALF_W, xf=RY(90), smooth=True)
    # Hai đầu hồi taplô
    for x, f in ((-HALF_W + 0.001, -1), (HALF_W - 0.001, 1)):
        pts = [(x, y, z) for y, z in prof_yz] + [(x, 0.0, zf)]
        mk.polygon(m, "dash", pts if f > 0 else list(reversed(pts)), (f, 0, 0))
    # Mép nhôm trên mép cuộn
    mk.tube(m, "chrome", [(-HALF_W + 0.02, 1.07, -4.415), (HALF_W - 0.02, 1.07, -4.415)], 0.006, sides=6)
    # Hộp đồng hồ (che nắng) trước ghế lái
    hx = -0.7
    hood = mk.round_path([(hx - 0.32, top, -4.5), (hx - 0.3, top + 0.13, -4.56), (hx + 0.3, top + 0.13, -4.56),
                          (hx + 0.32, top, -4.5)], 0.06, 6)
    mk.tube(m, "dash", hood, 0.03, sides=10)
    mk.rbox(m, "dash", (0.6, 0.12, 0.2), 0.03, segs=1, xf=T(hx, top + 0.06, -4.62))
    mk.rbox(m, "panel", (0.56, 0.11, 0.01), 0.004, segs=1, xf=T(hx, top + 0.055, -4.515) * RX(-12))
    for k, (dx, r) in enumerate(((-0.17, 0.05), (0.0, 0.055), (0.17, 0.05))):
        g = T(hx + dx, top + 0.058, -4.508) * RX(-12)
        mk.lathe(m, "chrome", [(r + 0.006, -0.004), (r + 0.008, 0.004), (r, 0.008)], 20, xf=g * RX(-90))
        _dial(m, "gauge", r, g * RX(-90) * T(0, -0.001, 0))
    # Công tắc, núm vặn dọc mặt đứng
    for k in range(6):
        mk.rbox(m, "panel", (0.022, 0.035, 0.02), 0.004, segs=1, xf=T(-0.25 + k * 0.05, 0.97, -4.385) * RX(-20))
    for k in range(3):
        mk.lathe(m, "chrome", [(0.0, 0.0), (0.016, 0.0), (0.016, 0.018), (0.0, 0.02)], 12,
                 xf=T(0.25 + k * 0.08, 0.9, -4.36) * RX(90))
    # Hộc để đồ có nắp phía bên phụ
    mk.rbox(m, "panel", (0.42, 0.18, 0.012), 0.006, segs=1, xf=T(0.75, 0.82, -4.358))
    mk.rbox(m, "chrome", (0.08, 0.015, 0.02), 0.005, segs=1, xf=T(0.75, 0.88, -4.35))
    return save(m)


def _dial(m, slot, r, xf):
    """Mặt đồng hồ tròn (hướng -Y cục bộ) có UV phẳng 0..1 để dán ảnh mặt số."""
    def fn(u, v):
        a = 2 * math.pi * u
        return (r * v * math.cos(a), 0.0, -r * v * math.sin(a))

    def uvf(u, v, p):
        a = 2 * math.pi * u
        return (0.5 + 0.5 * v * math.cos(a), 0.5 + 0.5 * v * math.sin(a))
    mk.grid(m, slot, fn, 20, 2, uv_fn=uvf, xf=xf, normal_fn=lambda u, v, p: (0.0, -1.0, 0.0))


def build_steering():
    """Vô-lăng xe khách: vành to, ba nan, trụ lái chéo xuống sàn. Gốc ở tâm vành."""
    m = mk.Mesh("steering_wheel")
    R = 0.22
    rim = mk.arc((0, 0, 0), R, 0, 360, 40, "xz")[:-1]
    mk.tube(m, "grip", rim, 0.017, sides=10, closed=True)
    for a in (90, 210, 330):
        r = math.radians(a)
        mk.tube(m, "spoke", [(math.cos(r) * 0.04, -0.01, math.sin(r) * 0.04),
                             (math.cos(r) * (R - 0.01), 0.0, math.sin(r) * (R - 0.01))], 0.011, sides=8)
    mk.lathe(m, "spoke", [(0.0, -0.035), (0.05, -0.03), (0.055, -0.005), (0.04, 0.012), (0.0, 0.016)], 18)
    mk.lathe(m, "chrome", [(0.0, 0.016), (0.025, 0.016), (0.0, 0.019)], 14)
    mk.tube(m, "column", [(0, -0.04, 0), (0, -0.62, 0)], 0.032, sides=12)
    mk.lathe(m, "column", [(0.0, -0.66), (0.07, -0.66), (0.06, -0.6), (0.033, -0.56)], 14)
    return save(m)


def build_cab_misc():
    """Nắp máy cạnh ghế lái, cần số, vách ngăn sau ghế lái, gương chiếu hậu, tấm che nắng, cánh cửa gấp."""
    m = mk.Mesh("cab_misc")
    # Nắp máy: khối bo tròn bọc giả da, viền tôn
    mk.rbox(m, "vinyl", (0.7, 0.58, 0.8), 0.09, segs=4, mid=2, xf=T(-0.05, 0.29, -4.05))
    mk.rbox(m, "frame", (0.72, 0.06, 0.82), 0.015, segs=1, xf=T(-0.05, 0.03, -4.05))
    # Cần số dài có quả nắm
    mk.tube(m, "chrome", mk.round_path([(-0.2, 0.0, -4.15), (-0.2, 0.55, -4.2), (-0.21, 0.92, -4.3)], 0.1, 6), 0.011)
    mk.lathe(m, "knob", [(0.0, -0.035), (0.03, -0.025), (0.036, 0.0), (0.03, 0.025), (0.0, 0.035)], 14,
             xf=T(-0.21, 0.95, -4.31))
    mk.lathe(m, "rubber", [(0.06, 0.0), (0.05, 0.05), (0.02, 0.1)], 14, xf=T(-0.2, 0.0, -4.15))
    # Vách ngăn sau ghế lái: tấm tôn + tay vịn crôm
    mk.rbox(m, "panel_paint", (0.95, 1.0, 0.035), 0.01, segs=1, xf=T(-0.72, 0.5, -3.62))
    mk.tube(m, "chrome", mk.round_path([(-1.2, 1.0, -3.62), (-1.2, 1.12, -3.62), (-0.25, 1.12, -3.62),
                                        (-0.25, 0.0, -3.62)], 0.05, 5), 0.017)
    # Gương chiếu hậu trong xe (rộng, cong)
    mk.rbox(m, "frame", (0.42, 0.11, 0.03), 0.02, segs=3, xf=T(0, 1.95, Z_FRONT + 0.16))
    mk.rbox(m, "mirror", (0.39, 0.085, 0.01), 0.012, segs=1, xf=T(0, 1.95, Z_FRONT + 0.177))
    mk.tube(m, "frame", [(0, 1.98, Z_FRONT + 0.15), (0, 2.08, Z_FRONT + 0.06)], 0.008, sides=6)
    # Tấm che nắng hai bên
    for x in (-0.6, 0.6):
        mk.rbox(m, "visor", (0.5, 0.2, 0.018), 0.012, segs=1,
                xf=T(x, 1.92, Z_FRONT + 0.12) * RX(-55) * T(0, -0.1, 0))
        mk.tube(m, "chrome", [(x - 0.26, 1.95, Z_FRONT + 0.08), (x + 0.26, 1.95, Z_FRONT + 0.08)], 0.006, sides=6)
    # Hai cánh cửa gấp: khung sơn, ô kính trên (kính nằm trong mesh kính từng lớp), tấm dưới
    dz0, dz1 = DOOR_Z
    leaf = (dz1 - dz0) / 2
    for k in range(2):
        zc = dz0 + leaf * (k + 0.5)
        xf = T(HALF_W + 0.02, 0, zc)
        mk.rbox(m, "door", (0.03, 0.95, leaf - 0.01), 0.008, segs=1, xf=xf * T(0, 0.2 + 0.475, 0))
        for (y, hh) in ((1.2, 0.04), (DOOR_TOP - 0.03, 0.05)):
            mk.rbox(m, "door", (0.035, hh, leaf - 0.01), 0.008, segs=1, xf=xf * T(0, y, 0))
        for dzz in (-leaf / 2 + 0.025, leaf / 2 - 0.025):
            mk.rbox(m, "door", (0.035, DOOR_TOP - 1.17, 0.045), 0.008, segs=1, xf=xf * T(0, (1.2 + DOOR_TOP) / 2, dzz))
        mk.rbox(m, "rubber", (0.04, DOOR_TOP - 0.2, 0.02), 0.008, segs=1,
                xf=xf * T(0, (0.2 + DOOR_TOP) / 2, (leaf / 2 - 0.005) * (1 if k == 0 else -1)))
        # Tay nắm dọc mạ crôm phía trong cánh
        mk.tube(m, "chrome", mk.round_path([(-0.02, 0.75, 0.0), (-0.06, 0.75, 0.0), (-0.06, 1.15, 0.0),
                                            (-0.02, 1.15, 0.0)], 0.02, 4), 0.01, xf=xf * T(0, 0, leaf * 0.25))
    return save(m)


def build_route_board():
    """Bảng lộ trình gỗ có khung, bốn móc treo (đặt ở BOARD_POS, mặt hướng +X)."""
    m = mk.Mesh("route_board")
    mk.rbox(m, "board", (0.02, 0.5, 0.36), 0.004, segs=1)
    _frame_ring(m, "frame", 0, 0, 0.38, 0.52, 0.02, 0.03, RY(90))
    return save(m)


def build_luggage():
    """Hành lý trên giá: bao tải căng, va-li, thùng giấy buộc dây, giỏ."""
    sack = mk.Mesh("luggage_sack")

    def sag(p, n):
        x, y, z = p
        # Bao mềm: phình giữa, xẹp mép, đáy phẳng
        k = 1.0 + 0.12 * math.cos(x / 0.2 * math.pi / 2) * math.cos(z / 0.25 * math.pi / 2)
        y = y * (k if y > 0 else 0.6)
        return (x * (1.0 + 0.05 * (y / 0.1)), y, z), n
    mk.rbox(sack, "sack", (0.4, 0.18, 0.5), 0.07, segs=4, mid=4, deform=sag)
    # Dây buộc miệng bao
    mk.tube(sack, "rope", mk.arc((0, 0.0, 0.0), 0.205, 0, 360, 24, "xy")[:-1], 0.006, closed=True,
            xf=T(0, 0.0, 0.18) * S(1, 0.5, 1))
    save(sack)
    box = mk.Mesh("luggage_box")
    mk.rbox(box, "carton", (0.36, 0.2, 0.42), 0.012, segs=1)
    for z in (-0.1, 0.1):
        mk.tube(box, "rope", [(-0.19, 0.105, z), (0.19, 0.105, z)], 0.005, sides=6)
        mk.tube(box, "rope", [(-0.185, 0.105, z), (-0.185, -0.1, z)], 0.005, sides=6)
        mk.tube(box, "rope", [(0.185, 0.105, z), (0.185, -0.1, z)], 0.005, sides=6)
    save(box)
    case = mk.Mesh("luggage_case")
    mk.rbox(case, "case", (0.42, 0.16, 0.56), 0.035, segs=3)
    for z in (-0.2, 0.2):
        mk.rbox(case, "metal", (0.43, 0.165, 0.015), 0.006, segs=1, xf=T(0, 0, z))
    # Quai xách trên nắp
    mk.tube(case, "metal", mk.round_path([(-0.08, 0.08, 0.0), (-0.08, 0.12, 0.0), (0.08, 0.12, 0.0),
                                          (0.08, 0.08, 0.0)], 0.02, 4), 0.01)
    save(case)


def build_altar():
    """Bàn thờ nhỏ trên taplô: tượng Phật ngồi trên đài sen, bát hương, lọ hoa. Gốc ở mặt đế."""
    m = mk.Mesh("dash_altar")
    mk.rbox(m, "wood", (0.28, 0.03, 0.12), 0.006, segs=1, xf=T(0.06, 0.015, 0))
    # Đài sen
    mk.lathe(m, "gold", [(0.0, 0.03), (0.045, 0.03), (0.055, 0.045), (0.05, 0.055), (0.035, 0.06), (0.0, 0.06)], 16)
    # Thân Phật ngồi: khối tiện thon + đầu tròn + búi tóc
    body = [(0.0, 0.06), (0.05, 0.06), (0.052, 0.075), (0.042, 0.1), (0.032, 0.125), (0.026, 0.14), (0.016, 0.148),
            (0.0, 0.15)]
    mk.lathe(m, "gold", body, 16)
    mk.ellipsoid(m, "gold", (0.021, 0.024, 0.021), 14, 8, xf=T(0, 0.168, 0))
    mk.ellipsoid(m, "gold", (0.009, 0.012, 0.009), 8, 6, xf=T(0, 0.193, 0))
    # Hào quang sau lưng
    mk.tube(m, "gold", mk.arc((0, 0.16, 0.025), 0.04, -30, 210, 16, "xy"), 0.004, sides=5)
    # Bát hương sứ + chân nhang
    mk.lathe(m, "ceramic", [(0.0, 0.03), (0.022, 0.03), (0.03, 0.045), (0.032, 0.07), (0.028, 0.07), (0.026, 0.05),
                            (0.0, 0.05)], 16, xf=T(0.11, 0, 0))
    rng = random.Random(4)
    for k in range(4):
        x, z = 0.11 + rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012)
        mk.tube(m, "incense", [(x, 0.05, z), (x + rng.uniform(-0.01, 0.01), 0.13, z + rng.uniform(-0.01, 0.01))],
                0.0018, sides=4, caps=False)
    # Lọ hoa nhựa
    mk.lathe(m, "ceramic", [(0.0, 0.03), (0.016, 0.03), (0.022, 0.06), (0.012, 0.1), (0.016, 0.11), (0.0, 0.11)], 14,
             xf=T(0.17, 0, 0))
    for k in range(5):
        a = k * 72
        ex = 0.17 + math.cos(math.radians(a)) * 0.025
        ez = math.sin(math.radians(a)) * 0.025
        mk.tube(m, "leaf", [(0.17, 0.1, 0), (ex, 0.16 + (k % 2) * 0.02, ez)], 0.0025, sides=4)
        _flower(m, "flower", (ex, 0.165 + (k % 2) * 0.02, ez), 0.018)
    return save(m)


def _flower(m, slot, c, r):
    """Bông hoa nhựa 5 cánh dẹt."""
    for k in range(5):
        a = 2 * math.pi * k / 5
        mk.ellipsoid(m, slot, (r * 0.55, r * 0.18, r * 0.3), 8, 4,
                     xf=T(c[0] + math.cos(a) * r * 0.5, c[1], c[2] + math.sin(a) * r * 0.5) * RY(-math.degrees(a)))
    mk.ellipsoid(m, slot, (r * 0.25, r * 0.2, r * 0.25), 6, 4, xf=T(*c))


def build_garland():
    """Dây hoa nhựa vắt ngang mép trên kính lái + tua rua đỏ treo ở gương."""
    m = mk.Mesh("garland")
    pts = []
    for k in range(41):
        t = k / 40
        x = -1.05 + 2.1 * t
        pts.append((x, 1.86 - 0.07 * math.sin(t * math.pi * 2) ** 2, Z_FRONT + 0.06))
    mk.tube(m, "leaf", pts, 0.004, sides=5)
    for k in range(0, 41, 2):
        p = pts[k]
        _flower(m, "flower" if k % 4 else "flower2", (p[0], p[1] - 0.01, p[2] + 0.01), 0.03)
        if k % 4 == 2:
            mk.ellipsoid(m, "leaf", (0.03, 0.006, 0.014), 6, 4, xf=T(p[0] + 0.03, p[1], p[2] + 0.01) * RZ(-30))
    # Tua rua: nút thắt + chùm sợi đỏ, treo dưới gương
    top = (0.12, 1.9, Z_FRONT + 0.17)
    mk.tube(m, "tassel", [top, (0.12, 1.72, Z_FRONT + 0.17)], 0.003, sides=4)
    mk.rbox(m, "tassel", (0.06, 0.06, 0.015), 0.012, segs=1, xf=T(0.12, 1.69, Z_FRONT + 0.17) * RZ(45))
    for k in range(10):
        dx = (k - 4.5) * 0.004
        mk.tube(m, "tassel", [(0.12 + dx * 0.4, 1.65, Z_FRONT + 0.17), (0.12 + dx, 1.52, Z_FRONT + 0.17 + dx * 0.3)],
                0.002, sides=3)
    mk.lathe(m, "gold", [(0.0, 0.0), (0.012, 0.004), (0.012, 0.03), (0.0, 0.034)], 8, xf=T(0.12, 1.62, Z_FRONT + 0.17))
    return save(m)


def build_headlights():
    """Đèn pha tròn có chóa (nhìn từ ngoài, gốc ở tâm mặt kính, mặt kính hướng -Z)."""
    m = mk.Mesh("headlight")
    mk.lathe(m, "chrome", [(0.0, -0.06), (0.1, -0.05), (0.115, 0.0), (0.105, 0.012)], 20, xf=RX(-90))
    mk.lathe(m, "lens", [(0.0, 0.018), (0.1, 0.008)], 20, xf=RX(-90))
    return save(m)


def build_all():
    MODELS.clear()
    build_shell()
    build_floor()
    build_window_frames()
    for v in ("day", "night", "wreck"):
        build_glass(v)
        build_curtains(v)
    build_seat_pair()
    build_bench()
    build_driver_seat()
    build_racks()
    build_ceiling_lights()
    build_dashboard()
    build_steering()
    build_cab_misc()
    build_route_board()
    build_luggage()
    build_altar()
    build_garland()
    build_headlights()
    return MODELS


if __name__ == "__main__":
    for k, v in build_all().items():
        print(k, v)
