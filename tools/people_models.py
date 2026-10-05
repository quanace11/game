#!/usr/bin/env python3
"""Người và hình nhân giấy cho chương 2, cùng đèn bão và cảnh đồng quê ngoài cửa xe.

- Hành khách xe 2006 (và thân xác An): thân người bo tròn, áo quần vải, nón lá / mũ cối / khăn.
- Hình nhân giấy (hàng mã) của những người chết trên chuyến xe 1999: áo giấy màu cứng gấp nếp
  có viền kim tuyến, tà áo dài phủ đùi, ống tay loe, bàn tay cắt giấy, mặt vẽ phẳng (mày cong,
  má hồng, môi đỏ), cổ và cổ tay lộ nan tre, cắm trên hai cọc tre.
- Đèn bão (đèn hurricane) có ống dẫn khí hai bên, bầu kính, lồng dây, quai xách.

Mesh sinh ra assets/models/bus/*.obj (dùng mesh_kit). Cấu trúc node giữ nguyên như bản cũ để
BusWreckDirector tìm được: <gốc>/Upper/Head (người ngồi), <gốc>/Head (người đứng), <gốc>/Held.
"""

import math
import random

import mesh_kit as mk
from mesh_kit import RX, RY, RZ, S, T
from level_blockout import basis_mul, basis_x, basis_y, basis_z, color, f, xform

import bus_models

MODELS = bus_models.MODELS


def _save(m):
    return bus_models.save(m)


def _mirror(m, name):
    return bus_models.mirror_x(m, name)


def _section_torso(m, slot, table, nu=16, nv=10, flat=False, superk=0.85, xf=None):
    """Thân hình ống, mặt cắt elip biến thiên theo bảng (y, nửa rộng, nửa sâu, lệch z)."""
    def at(y):
        for (y0, a0, b0, z0), (y1, a1, b1, z1) in zip(table[:-1], table[1:]):
            if y0 <= y <= y1:
                t = (y - y0) / (y1 - y0) if y1 > y0 else 0
                t = t * t * (3 - 2 * t)
                return a0 + (a1 - a0) * t, b0 + (b1 - b0) * t, z0 + (z1 - z0) * t
        return table[-1][1:]
    ys = (table[0][0], table[-1][0])

    def fn(u, v):
        y = ys[0] + (ys[1] - ys[0]) * v
        a, b, zo = at(y)
        th = 2 * math.pi * u
        c, s = math.cos(th), math.sin(th)
        x = a * math.copysign(abs(s) ** superk, s)
        z = zo - b * math.copysign(abs(c) ** superk, c)
        return (x, y, z)
    mk.grid(m, slot, fn, nu, nv, wrap_u=True, flat=flat, xf=xf)


def _limb(m, slot, pts, r0, r1, sides=10, xf=None):
    path = mk.round_path(pts, 0.04, 4) if len(pts) > 2 else pts
    mk.tube(m, slot, path, r0, sides=sides, radius_fn=lambda t: 1.0 + (r1 / r0 - 1.0) * t, xf=xf)


# ---------------------------------------------------------------------------
# Người (vải, da)
# ---------------------------------------------------------------------------

TORSO = [(0.0, 0.155, 0.105, 0.0), (0.12, 0.16, 0.11, -0.005), (0.28, 0.175, 0.12, -0.01),
         (0.42, 0.19, 0.105, 0.0), (0.5, 0.15, 0.085, 0.005), (0.54, 0.08, 0.06, 0.01), (0.57, 0.05, 0.045, 0.01)]


def build_people():
    m = mk.Mesh("p_torso")
    _section_torso(m, "shirt", TORSO)
    # Cổ áo
    mk.tube(m, "shirt", mk.arc((0, 0.535, 0.01), 0.062, 0, 360, 18, "xz")[:-1], 0.008, closed=True)
    _save(m)

    m = mk.Mesh("p_legs_seated")
    mk.rbox(m, "pants", (0.34, 0.14, 0.27), 0.06, segs=3, xf=T(0, 0.565, 0.05))
    for sx in (-1, 1):
        _limb(m, "pants", [(sx * 0.09, 0.565, 0.06), (sx * 0.1, 0.56, -0.3)], 0.08, 0.062, 12)
        _limb(m, "pants", [(sx * 0.1, 0.54, -0.33), (sx * 0.1, 0.1, -0.38)], 0.058, 0.042, 12)
        mk.ellipsoid(m, "pants", (0.062, 0.06, 0.06), 12, 8, xf=T(sx * 0.1, 0.53, -0.32))
    _save(m)

    m = mk.Mesh("p_feet")
    for sx in (-1, 1):
        mk.rbox(m, "shoe", (0.1, 0.022, 0.25), 0.01, segs=2, xf=T(sx * 0.1, 0.011, -0.42))
        mk.ellipsoid(m, "skin", (0.045, 0.035, 0.11), 10, 6, xf=T(sx * 0.1, 0.045, -0.44))
        mk.tube(m, "skin", [(sx * 0.1, 0.05, -0.38), (sx * 0.1, 0.12, -0.38)], 0.038, sides=8)
        mk.rbox(m, "shoe", (0.1, 0.012, 0.025), 0.005, segs=1, xf=T(sx * 0.1, 0.07, -0.47))
    _save(m)

    m = mk.Mesh("p_arms_seated")
    for sx in (-1, 1):
        _limb(m, "shirt", [(sx * 0.19, 0.44, 0.0), (sx * 0.215, 0.2, -0.02)], 0.058, 0.048, 10)
        mk.ellipsoid(m, "shirt", (0.06, 0.06, 0.06), 10, 6, xf=T(sx * 0.19, 0.44, 0.0))
        _limb(m, "shirt", [(sx * 0.215, 0.2, -0.02), (sx * 0.16, 0.085, -0.27)], 0.048, 0.04, 10)
        _limb(m, "skin", [(sx * 0.16, 0.085, -0.27), (sx * 0.15, 0.075, -0.3)], 0.034, 0.032, 8)
        mk.rbox(m, "skin", (0.07, 0.03, 0.09), 0.014, segs=2, xf=T(sx * 0.14, 0.065, -0.35) * RY(sx * 10))
    _save(m)

    m = mk.Mesh("p_arm_down_R")
    _limb(m, "shirt", [(0.2, 0.44, 0.0), (0.22, 0.18, 0.0), (0.21, -0.06, -0.03)], 0.055, 0.04, 10)
    mk.ellipsoid(m, "shirt", (0.06, 0.06, 0.06), 10, 6, xf=T(0.2, 0.44, 0.0))
    mk.rbox(m, "skin", (0.035, 0.1, 0.07), 0.014, segs=2, xf=T(0.21, -0.12, -0.03))
    _save(m)
    _save(_mirror(m, "p_arm_down_L"))
    m = mk.Mesh("p_arm_up_R")
    _limb(m, "shirt", [(0.2, 0.44, 0.0), (0.27, 0.68, 0.0), (0.27, 0.98, 0.02)], 0.055, 0.04, 10)
    mk.ellipsoid(m, "shirt", (0.06, 0.06, 0.06), 10, 6, xf=T(0.2, 0.44, 0.0))
    mk.rbox(m, "skin", (0.04, 0.1, 0.075), 0.015, segs=2, xf=T(0.27, 1.05, 0.02))
    _save(m)
    _save(_mirror(m, "p_arm_up_L"))

    m = mk.Mesh("p_legs_stand")
    mk.rbox(m, "pants", (0.34, 0.2, 0.22), 0.07, segs=3, xf=T(0, 0.86, 0.0))
    for sx in (-1, 1):
        _limb(m, "pants", [(sx * 0.09, 0.86, 0.0), (sx * 0.095, 0.47, 0.01)], 0.082, 0.06, 12)
        _limb(m, "pants", [(sx * 0.095, 0.47, 0.01), (sx * 0.095, 0.08, 0.0)], 0.058, 0.044, 12)
        mk.rbox(m, "shoe", (0.1, 0.03, 0.26), 0.012, segs=2, xf=T(sx * 0.095, 0.015, -0.05))
        mk.ellipsoid(m, "shoe", (0.05, 0.035, 0.1), 10, 6, xf=T(sx * 0.095, 0.05, -0.07))
    _save(m)

    m = mk.Mesh("p_head")
    mk.ellipsoid(m, "skin", (0.082, 0.105, 0.098), 20, 12, xf=T(0, 0.0, 0.0))
    mk.ellipsoid(m, "skin", (0.066, 0.06, 0.07), 14, 8, xf=T(0, -0.06, -0.025))
    mk.ellipsoid(m, "skin", (0.014, 0.022, 0.016), 8, 6, xf=T(0, -0.02, -0.1))
    for sx in (-1, 1):
        mk.ellipsoid(m, "skin", (0.012, 0.028, 0.02), 8, 6, xf=T(sx * 0.082, -0.01, 0.005))
    mk.tube(m, "skin", [(0, -0.165, 0.012), (0, -0.06, 0.012)], 0.045, sides=12)
    _save(m)

    m = mk.Mesh("p_hair_short")
    mk.ellipsoid(m, "hair", (0.088, 0.112, 0.104), 20, 10, xf=T(0, 0.008, 0.008), v_range=(0.42, 1.0))
    mk.ellipsoid(m, "hair", (0.084, 0.06, 0.06), 14, 6, xf=T(0, -0.02, 0.05))
    _save(m)
    m = mk.Mesh("p_hair_bun")
    mk.ellipsoid(m, "hair", (0.088, 0.112, 0.104), 20, 10, xf=T(0, 0.008, 0.008), v_range=(0.42, 1.0))
    mk.ellipsoid(m, "hair", (0.084, 0.07, 0.07), 14, 6, xf=T(0, -0.02, 0.05))
    mk.ellipsoid(m, "hair", (0.05, 0.042, 0.04), 12, 8, xf=T(0, -0.04, 0.115))
    _save(m)

    # Nón lá: chóp nón có các vòng nan nổi, hai mặt
    m = mk.Mesh("hat_non_la")
    prof = []
    for k in range(13):
        t = k / 12
        r = 0.24 * (1 - t)
        y = 0.16 * t + 0.003 * math.sin(t * 12 * math.pi)
        prof.append((r, y))
    mk.lathe(m, "hat", prof, 28)
    inner = [(r * 0.985, y - 0.006) for r, y in reversed(prof)]
    mk.lathe(m, "hat", inner, 28)
    mk.tube(m, "hat", mk.arc((0, 0.0, 0), 0.24, 0, 360, 36, "xz")[:-1], 0.005, closed=True)
    _save(m)
    m = mk.Mesh("hat_mu_coi")
    mk.lathe(m, "hat", [(0.0, 0.17), (0.06, 0.165), (0.1, 0.14), (0.125, 0.09), (0.13, 0.04), (0.17, 0.012),
                        (0.175, 0.0), (0.16, -0.004), (0.12, 0.02), (0.11, 0.03)], 24)
    mk.lathe(m, "hat", [(0.0, 0.18), (0.012, 0.18), (0.012, 0.168), (0.0, 0.168)], 10)
    _save(m)
    m = mk.Mesh("hat_khan")
    mk.tube(m, "hat", mk.arc((0, 0.0, 0), 0.088, 0, 360, 24, "xz")[:-1], 0.03, closed=True, xf=T(0, 0.03, 0.005))
    mk.ellipsoid(m, "hat", (0.085, 0.06, 0.095), 14, 6, xf=T(0, 0.05, 0.005), v_range=(0.5, 1.0))
    _save(m)


def _place(sc, name, parent, model, mats, pos=(0, 0, 0), basis=None, rot_y=0.0, shadow=1):
    slots = MODELS[model]
    rid = sc.ext_res("ArrayMesh", bus_models.RES + model + ".obj")
    props = [("transform", xform(pos, rot_y, basis))]
    if shadow != 1:
        props.append(("cast_shadow", str(shadow)))
    props.append(("mesh", 'ExtResource("%s")' % rid))
    for i, s in enumerate(slots):
        props.append(("surface_material_override/%d" % i, 'SubResource("%s")' % mats[s]))
    return sc.node(name, "MeshInstance3D", parent, props)


def place_hat(sc, name, parent, kind, mat, pos, basis=None):
    return _place(sc, name, parent, "hat_" + kind, {"hat": mat}, pos, basis)


def _hair_for(hat):
    return "p_hair_bun" if hat == "khan" else "p_hair_short"


def seated_person(sc, name, parent, pos, shirt, pants, skin, hair, hat=None, hat_mat=None, lean=0.0,
                  head_tilt=0.0, rot_y=0.0):
    """Người ngồi, mặt quay -Z. Node: <name>/Upper (nghiêng người) /Head (gục đầu)."""
    shoe = sc.mat("Sandal", (0.12, 0.1, 0.09), 0.6)
    g = sc.empty(name, parent, pos, rot_y)
    _place(sc, "Legs", g, "p_legs_seated", {"pants": pants})
    _place(sc, "Feet", g, "p_feet", {"skin": skin, "shoe": shoe})
    body = sc.empty("Upper", g, (0, 0.58, 0.06), basis=basis_x(lean))
    _place(sc, "Torso", body, "p_torso", {"shirt": shirt})
    _place(sc, "Arms", body, "p_arms_seated", {"shirt": shirt, "skin": skin})
    head = sc.empty("Head", body, (0, 0.72, 0), basis=basis_z(head_tilt))
    _place(sc, "Face", head, "p_head", {"skin": skin})
    _place(sc, "Hair", head, _hair_for(hat), {"hair": hair})
    if hat in ("non_la", "mu_coi", "khan"):
        y = {"non_la": 0.075, "mu_coi": 0.02, "khan": 0.035}[hat]
        _place(sc, {"non_la": "NonLa", "mu_coi": "MuCoi", "khan": "Khan"}[hat], head, "hat_" + hat, {"hat": hat_mat},
               (0, y, 0.005))
    return g


def standing_person(sc, name, parent, pos, rot_y, shirt, pants, skin, hair, arm_up=True, bag=None):
    """Người đứng, mặt quay -Z. Node: <name>/Head."""
    g = sc.empty(name, parent, pos, rot_y)
    shoe = sc.mat("Sandal", (0.12, 0.1, 0.09), 0.6)
    _place(sc, "Legs", g, "p_legs_stand", {"pants": pants, "shoe": shoe})
    _place(sc, "Torso", g, "p_torso", {"shirt": shirt}, (0, 0.86, 0))
    _place(sc, "ArmL", g, "p_arm_down_L", {"shirt": shirt, "skin": skin}, (0, 0.86, 0))
    _place(sc, "ArmR", g, "p_arm_up_R" if arm_up else "p_arm_down_R", {"shirt": shirt, "skin": skin}, (0, 0.86, 0))
    head = sc.empty("Head", g, (0, 1.6, 0))
    _place(sc, "Face", head, "p_head", {"skin": skin})
    _place(sc, "Hair", head, "p_hair_short", {"hair": hair})
    if bag:
        sc.mesh("Bag", g, "box", (0.24, 0.2, 0.08), (-0.24, 0.9, -0.08), bag)
        sc.mesh("Strap", g, "box", (0.03, 0.75, 0.02), (0.02, 1.2, -0.12), bag, basis=basis_z(35))
    return g


# ---------------------------------------------------------------------------
# Hình nhân giấy
# ---------------------------------------------------------------------------

EF_TORSO = [(-0.02, 0.17, 0.12, 0.0), (0.1, 0.165, 0.115, 0.0), (0.3, 0.18, 0.12, -0.005), (0.43, 0.2, 0.11, 0.0),
            (0.5, 0.15, 0.09, 0.005), (0.55, 0.075, 0.06, 0.01)]


def _paper_panel(m, slot, trim, corners_fn, nu, nv, trim_edges=(), trim_w=0.03):
    """Tấm giấy cứng (hai mặt, gấp nếp phẳng). corners_fn(u, v) -> điểm."""
    mk.grid(m, slot, corners_fn, nu, nv, double=True, flat=True)
    for e in trim_edges:
        if e == "bottom":
            fn = lambda u, v: _offset(corners_fn(u, 0.0), corners_fn(u, min(1.0, trim_w)), v)
        elif e == "left":
            fn = lambda u, v: _offset(corners_fn(0.0, u), corners_fn(min(1.0, trim_w), u), v)
        else:
            fn = lambda u, v: _offset(corners_fn(1.0, u), corners_fn(1.0 - min(1.0, trim_w), u), v)
        mk.grid(m, trim, lambda u, v, fn=fn: _lift(fn(u, v)), nu, 1, double=True, flat=True,
                uv_fn=lambda u, v, p: (u * 4.0, v))


def _offset(a, b, t):
    return mk.lerp(a, b, t)


def _lift(p):
    return (p[0], p[1] + 0.003, p[2])


def build_effigies():
    # Áo giấy (thân + vạt + tà trước phủ đùi + tà sau) cho hình nhân ngồi; gốc ở eo (node Upper).
    for variant in ("ao_dai", "shirt"):
        m = mk.Mesh("e_torso_" + variant)
        _section_torso(m, "paper", EF_TORSO, nu=10, nv=6, flat=True, superk=0.7)
        # Viền cổ áo kim tuyến + nẹp áo chéo (áo dài cài khuy bên phải)
        mk.tube(m, "trim", mk.arc((0, 0.535, 0.012), 0.07, 0, 360, 10, "xz")[:-1], 0.014, sides=4, closed=True)
        if variant == "ao_dai":
            mk.tube(m, "trim", [(0.0, 0.52, -0.075), (0.08, 0.46, -0.1), (0.15, 0.38, -0.08), (0.165, 0.1, -0.11)],
                    0.008, sides=4)
            # Tà trước phủ lên đùi, tà sau buông sau lưng ghế: giấy cứng gấp góc.
            front = lambda u, v: ((u - 0.5) * 0.3 * (1 + 0.15 * v), 0.0 - 0.02 * v + 0.012 * math.sin(u * math.pi),
                                  -0.11 - v * 0.36)
            _paper_panel(m, "paper", "trim", front, 4, 3, trim_edges=("bottom", "left", "right"), trim_w=0.12)
            # Vạt hông xòe
            hem = lambda u, v: (0.19 * math.sin(2 * math.pi * u) * (1 + 0.15 * v), -0.02 - v * 0.08,
                                -0.13 * math.cos(2 * math.pi * u) * (1 + 0.2 * v))
            mk.grid(m, "paper", hem, 10, 1, double=True, flat=True)
        else:
            mk.tube(m, "trim", [(0.0, 0.52, -0.08), (0.0, 0.02, -0.125)], 0.006, sides=4)
            for k in range(5):
                mk.ellipsoid(m, "trim", (0.012, 0.012, 0.006), 6, 4, xf=T(0.0, 0.45 - k * 0.09, -0.128))
        # Hai cọc tre đỡ hình nhân lộ ra dưới vạt áo sau
        for sx in (-1, 1):
            mk.tube(m, "bamboo", [(sx * 0.07, 0.25, 0.09), (sx * 0.08, -0.58, 0.16)], 0.011, sides=6)
        _save(m)

    # Ống tay áo loe (giấy cứng), cổ tay nan tre, bàn tay cắt giấy dẹt
    m = mk.Mesh("e_arms_seated")
    for sx in (-1, 1):
        sh = (sx * 0.19, 0.45, 0.0)
        el = (sx * 0.23, 0.2, -0.04)
        wr = (sx * 0.17, 0.1, -0.24)
        mk.tube(m, "paper", [sh, el], 0.06, sides=6, caps=True)
        mk.tube(m, "paper", [el, wr], 0.055, sides=6, caps=False, radius_fn=lambda t: 1.0 + 0.6 * t)
        mk.tube(m, "trim", [mk.lerp(el, wr, 0.9), wr], 0.087, sides=6, caps=False)
        mk.tube(m, "bamboo", [mk.lerp(el, wr, 0.6), (sx * 0.15, 0.075, -0.31)], 0.008, sides=5)
        # Bàn tay: tấm giấy dẹt hình xẻng, ngón vẽ bằng mực
        hand = mk.Mesh("tmp")
        pts = [(-0.03, 0.0, 0.0), (0.03, 0.0, 0.0), (0.035, 0.0, -0.07), (0.015, 0.0, -0.095), (-0.015, 0.0, -0.095),
               (-0.035, 0.0, -0.07)]
        mk.polygon(hand, "hand", pts, (0, 1, 0))
        mk.polygon(hand, "hand", list(reversed(pts)), (0, -1, 0))
        m.merge(hand, T(sx * 0.15, 0.072, -0.3) * RY(sx * 8) * RZ(sx * 12))
    _save(m)

    m = mk.Mesh("e_legs_seated")
    mk.rbox(m, "pants", (0.34, 0.12, 0.26), 0.02, segs=1, xf=T(0, 0.565, 0.05))
    for sx in (-1, 1):
        mk.tube(m, "pants", [(sx * 0.09, 0.565, 0.06), (sx * 0.1, 0.56, -0.33)], 0.075, sides=6)
        mk.tube(m, "pants", [(sx * 0.1, 0.56, -0.33), (sx * 0.1, 0.11, -0.38)], 0.068, sides=6,
                radius_fn=lambda t: 1.0 + 0.25 * t)
        mk.tube(m, "bamboo", [(sx * 0.1, 0.12, -0.38), (sx * 0.1, 0.05, -0.39)], 0.012, sides=5)
    _save(m)
    m = mk.Mesh("e_feet_shoes")
    for sx in (-1, 1):
        mk.rbox(m, "shoe", (0.1, 0.05, 0.22), 0.02, segs=1, xf=T(sx * 0.1, 0.025, -0.43))
        mk.rbox(m, "trim", (0.104, 0.012, 0.16), 0.004, segs=1, xf=T(sx * 0.1, 0.052, -0.41))
    _save(m)
    m = mk.Mesh("e_feet_bare")
    for sx in (-1, 1):
        pts = [(-0.04, 0.0, 0.0), (0.04, 0.0, 0.0), (0.045, 0.0, -0.17), (0.0, 0.0, -0.2), (-0.045, 0.0, -0.17)]
        mk.polygon(m, "hand", pts, (0, 1, 0), T(sx * 0.1, 0.012, -0.36))
        mk.polygon(m, "hand", list(reversed(pts)), (0, -1, 0), T(sx * 0.1, 0.012, -0.36))
    _save(m)

    # Đầu: nửa trước dán mặt vẽ, nửa sau tóc sơn đen; cổ là nan tre bọc giấy viền.
    m = mk.Mesh("e_head")
    rx, ry, rz = 0.095, 0.118, 0.1

    def head(u, v):
        th = 2 * math.pi * u
        ph = math.pi * (v - 0.5)
        # Mặt hơi phẳng (mặt nạ giấy bồi) và cằm thon
        x = rx * math.cos(ph) * math.sin(th) * (0.92 if ph < 0 else 1.0)
        y = ry * math.sin(ph)
        z = rz * math.cos(ph) * math.cos(th)
        if z < 0:
            z *= 0.82
        return (x, y, z)

    def face_uv(u, v, p):
        return (0.5 - p[0] / (2 * rx), 0.5 + p[1] / (2 * ry))
    mk.grid(m, "face", head, 16, 14, u_range=(0.25, 0.75), uv_fn=face_uv)
    mk.grid(m, "hair", head, 16, 14, u_range=(0.75, 1.25))
    mk.tube(m, "bamboo", [(0, -0.2, 0.01), (0, -0.09, 0.01)], 0.016, sides=6)
    mk.lathe(m, "trim", [(0.035, -0.2), (0.055, -0.175), (0.05, -0.16), (0.03, -0.15)], 10, smooth=False)
    # Tai giấy dẹt
    for sx in (-1, 1):
        mk.ellipsoid(m, "face_plain", (0.008, 0.03, 0.022), 6, 4, xf=T(sx * 0.093, -0.005, 0.01))
    _save(m)
    m = mk.Mesh("e_hair_bun")
    mk.ellipsoid(m, "hair", (0.052, 0.045, 0.045), 10, 6, xf=T(0, -0.02, 0.11))
    mk.lathe(m, "trim", [(0.012, -0.008), (0.012, 0.008)], 8, xf=T(0, -0.02, 0.16) * RX(90))
    _save(m)
    m = mk.Mesh("e_hair_khan")
    # Khăn vấn / khăn đóng: vành vải xếp nếp quấn quanh đầu
    mk.tube(m, "hat", mk.arc((0, 0.0, 0), 0.098, 0, 360, 14, "xz")[:-1], 0.036, sides=6, closed=True,
            xf=T(0, 0.05, 0.005) * RX(-6))
    mk.tube(m, "hat", mk.arc((0, 0.0, 0), 0.09, 0, 360, 14, "xz")[:-1], 0.03, sides=6, closed=True,
            xf=T(0, 0.095, 0.005) * RX(-6))
    _save(m)

    # Hình nhân đứng (chú Bảy): áo dài tới gối, quần, hai tay (một giơ lên nắm dây chuông)
    m = mk.Mesh("e_body_stand")
    _section_torso(m, "paper", EF_TORSO, nu=10, nv=6, flat=True, superk=0.7, xf=T(0, 0.86, 0))
    mk.tube(m, "trim", mk.arc((0, 0.86 + 0.535, 0.012), 0.07, 0, 360, 10, "xz")[:-1], 0.014, sides=4, closed=True)
    skirt = lambda u, v: (0.19 * math.sin(2 * math.pi * u) * (1 + 0.35 * v), 0.86 - v * 0.42,
                          -0.13 * math.cos(2 * math.pi * u) * (1 + 0.3 * v))
    mk.grid(m, "paper", skirt, 10, 3, double=True, flat=True)
    hemb = lambda u, v: (0.19 * math.sin(2 * math.pi * u) * (1.35 - 0.04 * v), 0.44 + v * 0.05,
                         -0.13 * math.cos(2 * math.pi * u) * (1.3 - 0.04 * v))
    mk.grid(m, "trim", hemb, 10, 1, double=True, flat=True, uv_fn=lambda u, v, p: (u * 8, v))
    for sx in (-1, 1):
        mk.tube(m, "pants", [(sx * 0.09, 0.8, 0.0), (sx * 0.095, 0.08, 0.0)], 0.075, sides=6,
                radius_fn=lambda t: 1.0 - 0.15 * t)
        mk.rbox(m, "shoe", (0.1, 0.05, 0.24), 0.02, segs=1, xf=T(sx * 0.095, 0.025, -0.05))
    # Tay trái buông cầm xấp vé, tay phải giơ cao
    sh = (-0.2, 1.31, 0.0)
    mk.tube(m, "paper", [sh, (-0.24, 1.07, 0.02)], 0.06, sides=6)
    mk.tube(m, "paper", [(-0.24, 1.07, 0.02), (-0.25, 0.86, -0.04)], 0.055, sides=6, caps=False,
            radius_fn=lambda t: 1.0 + 0.6 * t)
    mk.tube(m, "trim", [(-0.25, 0.885, -0.035), (-0.25, 0.86, -0.04)], 0.087, sides=6, caps=False)
    mk.tube(m, "bamboo", [(-0.25, 0.9, -0.04), (-0.25, 0.8, -0.05)], 0.008, sides=5)
    sh = (0.2, 1.31, 0.0)
    mk.tube(m, "paper", [sh, (0.26, 1.55, 0.0)], 0.06, sides=6)
    mk.tube(m, "paper", [(0.26, 1.55, 0.0), (0.26, 1.8, 0.02)], 0.055, sides=6, caps=False,
            radius_fn=lambda t: 1.0 + 0.6 * t)
    mk.tube(m, "trim", [(0.26, 1.775, 0.018), (0.26, 1.8, 0.02)], 0.087, sides=6, caps=False)
    mk.tube(m, "bamboo", [(0.26, 1.76, 0.02), (0.26, 1.9, 0.02)], 0.008, sides=5)
    for (p, ang) in (((0.26, 1.9, 0.02), 0), ((-0.25, 0.8, -0.05), 180)):
        hand = mk.Mesh("tmp")
        pts = [(-0.03, 0.0, 0.0), (0.03, 0.0, 0.0), (0.035, -0.07, 0.0), (0.015, -0.095, 0.0), (-0.015, -0.095, 0.0),
               (-0.035, -0.07, 0.0)]
        mk.polygon(hand, "hand", pts, (0, 0, -1))
        mk.polygon(hand, "hand", list(reversed(pts)), (0, 0, 1))
        m.merge(hand, T(*p) * RZ(ang))
    _save(m)


def effigy_materials(sc, key, cloth, pants, face="man", shoe=(0.08, 0.07, 0.07)):
    """Bộ vật liệu một hình nhân: giấy in hoa văn tô màu, viền kim tuyến, mặt vẽ, tóc sơn, nan tre."""
    from bus_blockout import texmat
    paper_n = "paper_crease_normal.png"
    mats = {
        "paper": texmat(sc, "Ef%sCloth" % key, "paper_print.png", tuple(cloth) + (1,), rough=0.9, uv=(5, 5),
                        normal_png=paper_n, normal=0.8, cull=False),
        "pants": texmat(sc, "Ef%sPants" % key, "paper_crease_albedo.png", tuple(pants) + (1,), rough=0.95, uv=(4, 4),
                        normal_png=paper_n, normal=0.8, cull=False),
        "trim": texmat(sc, "EfGoldTrim", "gold_trim.png", rough=0.4, metallic=0.5, uv=(1, 1), cull=False,
                       emission=(0.25, 0.18, 0.05), energy=0.6),
        "face": texmat(sc, "EfFace_" + face, "effigy_face_%s.png" % face, rough=0.75, emission=(0.12, 0.12, 0.11),
                       energy=0.8),
        "face_plain": texmat(sc, "EfFacePlain", "paper_crease_albedo.png", (0.95, 0.92, 0.86, 1), rough=0.9),
        "hand": texmat(sc, "EfHand", "paper_crease_albedo.png", (0.96, 0.92, 0.86, 1), rough=0.9, cull=False,
                       emission=(0.1, 0.1, 0.09), energy=0.6),
        "hair": texmat(sc, "EfHair", "paper_crease_albedo.png", (0.07, 0.065, 0.075, 1), rough=0.45,
                       normal_png=paper_n, normal=0.6),
        "hat": texmat(sc, "Ef%sHat" % key, "paper_crease_albedo.png", (0.1, 0.1, 0.16, 1), rough=0.6,
                      normal_png=paper_n),
        "bamboo": sc.pbr("EfBamboo", "bamboo_weave", (0.95, 0.85, 0.6), triplanar=True),
        "shoe": texmat(sc, "EfShoe", "paper_crease_albedo.png", tuple(shoe) + (1,), rough=0.5),
    }
    return mats


def seated_effigy(sc, name, parent, pos, mats, style="ao_dai", hair=None, feet="shoes", lean=0.0, head_tilt=0.0,
                  rot_y=0.0):
    """Hình nhân giấy ngồi. Node như người thật: <name>/Upper/Head."""
    g = sc.empty(name, parent, pos, rot_y)
    _place(sc, "Legs", g, "e_legs_seated", mats)
    _place(sc, "Feet", g, "e_feet_" + feet, mats)
    body = sc.empty("Upper", g, (0, 0.58, 0.06), basis=basis_x(lean))
    _place(sc, "Torso", body, "e_torso_" + style, mats)
    _place(sc, "Arms", body, "e_arms_seated", mats)
    head = sc.empty("Head", body, (0, 0.74, 0), basis=basis_z(head_tilt))
    _place(sc, "Face", head, "e_head", mats)
    if hair:
        _place(sc, "Hair", head, "e_hair_" + hair, mats)
    return g


def standing_effigy(sc, name, parent, pos, rot_y, mats, hair=None):
    """Hình nhân giấy đứng. Node: <name>/Head."""
    g = sc.empty(name, parent, pos, rot_y)
    _place(sc, "Body", g, "e_body_stand", mats)
    head = sc.empty("Head", g, (0, 1.62, 0))
    _place(sc, "Face", head, "e_head", mats)
    if hair:
        _place(sc, "Hair", head, "e_hair_" + hair, mats)
    return g


# ---------------------------------------------------------------------------
# Đèn bão
# ---------------------------------------------------------------------------

def build_storm_lamp():
    """Đèn bão kiểu hurricane: bình dầu có gân, hai ống dẫn khí hai bên, bầu kính, nắp, quai."""
    m = mk.Mesh("storm_lamp")
    mk.lathe(m, "metal", [(0.0, 0.0), (0.07, 0.0), (0.078, 0.008), (0.08, 0.022), (0.074, 0.03), (0.08, 0.038),
                          (0.076, 0.05), (0.05, 0.058), (0.046, 0.066), (0.0, 0.066)], 24)
    # Vòng đế bầu kính + núm vặn bấc
    mk.lathe(m, "metal", [(0.0, 0.066), (0.052, 0.066), (0.055, 0.074), (0.046, 0.078), (0.0, 0.078)], 20)
    mk.tube(m, "metal", [(0.0, 0.06, -0.05), (0.0, 0.06, -0.085)], 0.004, sides=6)
    mk.lathe(m, "metal", [(0.0, 0.0), (0.013, 0.0), (0.013, 0.006), (0.0, 0.006)], 10,
             xf=T(0, 0.06, -0.088) * RX(90))
    # Bầu kính
    glass = [(0.04, 0.078), (0.052, 0.1), (0.058, 0.135), (0.054, 0.17), (0.04, 0.198), (0.032, 0.205)]
    mk.lathe(m, "glass", glass, 24)
    # Lồng dây bảo vệ quanh bầu kính
    for k in range(4):
        a = math.radians(45 + 90 * k)
        mk.tube(m, "metal", [(math.cos(a) * 0.06, 0.078, math.sin(a) * 0.06),
                             (math.cos(a) * 0.066, 0.14, math.sin(a) * 0.066),
                             (math.cos(a) * 0.045, 0.2, math.sin(a) * 0.045)], 0.0025, sides=4, caps=False)
    mk.tube(m, "metal", mk.arc((0, 0.14, 0), 0.066, 0, 360, 24, "xz")[:-1], 0.0025, sides=4, closed=True)
    # Nắp chụp + chóp thông hơi
    mk.lathe(m, "metal", [(0.0, 0.2), (0.07, 0.205), (0.072, 0.212), (0.05, 0.235), (0.03, 0.245), (0.026, 0.262),
                          (0.034, 0.27), (0.0, 0.275)], 24)
    # Hai ống dẫn khí đặc trưng của đèn bão: từ hông bình dầu lên nắp
    for sx in (-1, 1):
        path = mk.round_path([(sx * 0.078, 0.03, 0.0), (sx * 0.1, 0.04, 0.0), (sx * 0.1, 0.2, 0.0),
                              (sx * 0.06, 0.225, 0.0)], 0.02, 5)
        mk.tube(m, "metal", path, 0.0085, sides=8)
    # Quai xách dây thép
    bail = mk.arc((0, 0.24, 0), 0.105, 0, 180, 18, "xy")
    mk.tube(m, "metal", bail, 0.0028, sides=5)
    _save(m)


def storm_lamp(sc, name, parent, pos, metal, glass_mat, flame=None, rot_y=0.0):
    g = sc.empty(name, parent, pos, rot_y)
    rid = sc.ext_res("ArrayMesh", bus_models.RES + "storm_lamp.obj")
    sc.node("Lamp", "MeshInstance3D", g, [
        ("mesh", 'ExtResource("%s")' % rid),
        ("surface_material_override/0", 'SubResource("%s")' % metal),
        ("surface_material_override/1", 'SubResource("%s")' % glass_mat),
    ])
    if flame:
        sc.mesh("Wick", g, "cyl", (0.006, 0.008, 0.012, 6), (0, 0.084, 0), sc.mat("Wick", (0.1, 0.08, 0.06), 1.0))
        sc.mesh("Flame", g, "sphere", (0.011, 0.042), (0, 0.11, 0), flame, shadow=False)
    return g


# ---------------------------------------------------------------------------
# Cảnh quê ngoài cửa sổ xe ban ngày (trôi theo +Z bằng ScrollingScenery.gd)
# ---------------------------------------------------------------------------

def build_scenery_models():
    m = mk.Mesh("tree_crown")
    rng = random.Random(8)
    for k in range(7):
        r = rng.uniform(0.9, 1.4)
        mk.ellipsoid(m, "leaf", (r, r * 0.8, r), 14, 8,
                     xf=T(rng.uniform(-0.9, 0.9), rng.uniform(-0.3, 0.6), rng.uniform(-0.9, 0.9)),
                     deform=lambda p: (p[0] * (1 + 0.08 * math.sin(p[1] * 9)), p[1], p[2] * (1 + 0.08 * math.cos(p[0] * 9))))
    _save(m)
    m = mk.Mesh("bamboo_clump")
    for k in range(9):
        a = 2 * math.pi * k / 9
        base = (math.cos(a) * 0.3, 0.0, math.sin(a) * 0.3)
        lean = (math.cos(a) * 1.6, 6.0, math.sin(a) * 1.6)
        pts = [mk.lerp(base, lean, t) for t in (0, 0.3, 0.6, 1.0)]
        pts = [(p[0] * (1 + 0.2 * t * t), p[1], p[2] * (1 + 0.2 * t * t)) for t, p in zip((0, 0.3, 0.6, 1.0), pts)]
        mk.tube(m, "cane", pts, 0.05, sides=6, radius_fn=lambda t: 1.0 - 0.6 * t)
        for j in range(4):
            c = mk.lerp(base, lean, 0.55 + j * 0.13)
            mk.ellipsoid(m, "leaf", (0.7, 0.35, 0.7), 10, 6, xf=T(c[0] * 1.15, c[1], c[2] * 1.15))
    _save(m)


def build_day_scenery(sc, out, scroll_script, ground_mat, road_mat):
    rng = random.Random(2006)
    trunk = sc.pbr("TrunkDay", "wood_dark", (0.45, 0.38, 0.3))
    foliage = sc.pbr("FoliageDay", "grass", (0.38, 0.55, 0.22))
    foliage_far = sc.mat("TreeLineFar", (0.3, 0.42, 0.28), 1.0)
    bamboo = sc.mat("Bamboo", (0.48, 0.55, 0.25), 0.7)
    pole = sc.pbr("ConcretePole", "concrete_damp", (0.8, 0.78, 0.74))
    straw = sc.pbr("Haystack", "bamboo_weave", (1.0, 0.9, 0.55))
    wall_house = sc.pbr("HouseWall", "limewash_old", (1.0, 0.92, 0.7))
    roof = sc.pbr("HouseRoof", "roof_tile", (1, 1, 1))
    sc_node = sc.node("Scenery", "Node3D", out, [
        ("script", 'ExtResource("%s")' % scroll_script),
        ("scrolling_materials", 'Array[BaseMaterial3D]([SubResource("%s"), SubResource("%s")])'
         % (ground_mat, road_mat)),
    ])
    # Lũy tre làng xa xa: dải cây liền dọc hai bên đường, đủ xa để không cần trôi.
    for side in (-1, 1):
        for k, (x, h) in enumerate([(32, 6.0), (55, 9.0)]):
            sc.mesh("TreeLine", out, "box", (6.0, h, 200.0), (side * x + rng.uniform(-2, 2), -0.95 + h / 2, 0),
                    foliage if k == 0 else foliage_far, shadow=False)
            for b in range(14):
                z = -95 + b * 14 + rng.uniform(-4, 4)
                _place(sc, "TreeTop", out, "tree_crown", {"leaf": foliage if k == 0 else foliage_far},
                       (side * x, -0.95 + h + 0.3, z), basis_mul(basis_y(b * 40), [2.4, 0, 0, 0, 2.0, 0, 0, 0, 2.4]),
                       shadow=0)
        for x in (8.0, 14.0, 21.0):
            sc.mesh("Dike", out, "box", (0.5, 0.18, 200.0), (side * x, -0.88, 0), road_mat, shadow=False)
    span = 120.0
    for k in range(26):
        side = 1 if k % 2 == 0 else -1
        z = -span / 2 + k * span / 26 + rng.uniform(-1.5, 1.5)
        x = side * rng.uniform(5.0, 16.0)
        kind = rng.choice(["tree", "tree", "bamboo", "bamboo", "hay", "house"])
        g = sc.empty("Prop%d" % k, sc_node, (x, -0.95, z), rng.uniform(0, 360))
        if kind == "tree":
            sc.mesh("Trunk", g, "cyl", (0.12, 0.2, 2.8, 8), (0, 1.4, 0), trunk)
            _place(sc, "Crown", g, "tree_crown", {"leaf": foliage}, (0, 3.4, 0))
        elif kind == "bamboo":
            _place(sc, "Clump", g, "bamboo_clump", {"cane": bamboo, "leaf": foliage})
        elif kind == "hay":
            sc.mesh("Hay", g, "cyl", (0.3, 1.1, 1.8, 12), (0, 0.9, 0), straw)
        else:
            sc.mesh("Walls", g, "box", (4.0, 2.4, 3.0), (0, 1.2, 0), wall_house)
            sc.mesh("Roof", g, "prism", (4.6, 1.3, 3.4), (0, 3.05, 0), roof, basis=basis_y(90))
    for k in range(6):
        g = sc.empty("Pole%d" % k, sc_node, (3.6, -0.95, -span / 2 + k * span / 6))
        sc.mesh("Post", g, "box", (0.2, 7.0, 0.2), (0, 3.5, 0), pole)
        sc.mesh("Arm", g, "box", (1.4, 0.1, 0.1), (0, 6.6, 0), pole)


def build_all():
    build_people()
    build_effigies()
    build_storm_lamp()
    build_scenery_models()
