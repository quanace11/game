#!/usr/bin/env python3
"""Sinh scene blockout (greybox) cho các bối cảnh bằng CSG.

Chạy:  python3 tools/level_blockout.py
Kết quả: scenes/levels/DreamBedroom.tscn và scenes/levels/OldHouse.tscn

LƯU Ý: chạy lại script sẽ GHI ĐÈ hai file .tscn trên. Nếu đã chỉnh scene
bằng Godot editor thì đừng chạy lại, hoặc sửa số đo ở đây trước rồi mới chạy.

Quy ước: 1 đơn vị = 1 mét, trục +Y lên trên, mặt tiền nhà quay về +Z (hướng nam).
Tên node (Wall_Living_Front, Bed_Her...) giữ cố định để khi xuất sang Blender
và nhập lại, có thể gắn lại chức năng theo tên.
"""

import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def f(v):
    s = "%.4f" % v
    s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def basis_y(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [c, 0, s, 0, 1, 0, -s, 0, c]


def basis_x(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [1, 0, 0, 0, c, -s, 0, s, c]


def basis_mul(a, b):
    r = []
    for i in range(3):
        for j in range(3):
            r.append(sum(a[i * 3 + k] * b[k * 3 + j] for k in range(3)))
    return r


def xform(pos=(0, 0, 0), rot_y=0.0, basis=None):
    b = basis if basis is not None else basis_y(rot_y)
    return "Transform3D(%s, %s)" % (", ".join(f(v) for v in b), ", ".join(f(v) for v in pos))


def color(c):
    return "Color(%s, %s, %s, %s)" % (f(c[0]), f(c[1]), f(c[2]), f(c[3] if len(c) > 3 else 1))


class Scene:
    def __init__(self, root_name, root_type="Node3D"):
        self.ext = []
        self.sub = []
        self.nodes = []
        self.materials = {}
        self.nodes.append('[node name="%s" type="%s"]\n' % (root_name, root_type))

    def ext_res(self, kind, path):
        rid = "%d_%s" % (len(self.ext) + 1, os.path.splitext(os.path.basename(path))[0].lower())
        self.ext.append('[ext_resource type="%s" path="%s" id="%s"]' % (kind, path, rid))
        return rid

    def sub_res(self, kind, rid, props):
        lines = ['[sub_resource type="%s" id="%s"]' % (kind, rid)]
        lines += ["%s = %s" % (k, v) for k, v in props]
        self.sub.append("\n".join(lines) + "\n")
        return rid

    def mat(self, name, rgb, roughness=0.85, metallic=0.0, emission=None, energy=1.0, alpha=None):
        if name in self.materials:
            return self.materials[name]
        props = []
        if alpha is not None:
            props.append(("transparency", "1"))
            props.append(("cull_mode", "2"))
        props.append(("albedo_color", color(tuple(rgb) + ((alpha,) if alpha is not None else ()))))
        if metallic:
            props.append(("metallic", f(metallic)))
        props.append(("roughness", f(roughness)))
        if emission:
            props += [("emission_enabled", "true"), ("emission", color(emission)),
                      ("emission_energy_multiplier", f(energy))]
        rid = self.sub_res("StandardMaterial3D", "Mat_" + name, props)
        self.materials[name] = rid
        return rid

    def node(self, name, kind, parent=".", props=(), extra_header=""):
        head = '[node name="%s" type="%s" parent="%s"%s]' % (name, kind, parent, extra_header)
        body = "".join("%s = %s\n" % (k, v) for k, v in props)
        self.nodes.append(head + "\n" + body)
        return name if parent == "." else parent + "/" + name

    def instance(self, name, rid, parent=".", props=()):
        head = '[node name="%s" parent="%s" instance=ExtResource("%s")]' % (name, parent, rid)
        body = "".join("%s = %s\n" % (k, v) for k, v in props)
        self.nodes.append(head + "\n" + body)

    def group(self, name, parent=".", pos=(0, 0, 0), rot_y=0.0, collision=True):
        props = [("transform", xform(pos, rot_y))]
        if collision:
            props.append(("use_collision", "true"))
        return self.node(name, "CSGCombiner3D", parent, props)

    def box(self, name, parent, center, size, mat, rot_y=0.0, subtract=False, basis=None):
        props = [("transform", xform(center, rot_y, basis))]
        if subtract:
            props.append(("operation", "2"))
        props.append(("size", "Vector3(%s, %s, %s)" % tuple(f(v) for v in size)))
        if mat:
            props.append(("material", 'SubResource("%s")' % mat))
        return self.node(name, "CSGBox3D", parent, props)

    def cyl(self, name, parent, center, radius, height, mat, sides=16):
        props = [("transform", xform(center)), ("radius", f(radius)), ("height", f(height)),
                 ("sides", str(sides)), ("material", 'SubResource("%s")' % mat)]
        return self.node(name, "CSGCylinder3D", parent, props)

    def sphere(self, name, parent, center, radius, mat):
        props = [("transform", xform(center)), ("radius", f(radius)),
                 ("material", 'SubResource("%s")' % mat)]
        return self.node(name, "CSGSphere3D", parent, props)

    def save(self, path):
        steps = len(self.ext) + len(self.sub) + 1
        out = ["[gd_scene load_steps=%d format=3]\n" % steps]
        if self.ext:
            out.append("\n".join(self.ext) + "\n")
        out += self.sub
        out += self.nodes
        full = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as fh:
            fh.write("\n".join(out))
        print("wrote", path)


# ---------------------------------------------------------------------------
# Đồ nội thất dựng sẵn. Hệ tọa độ cục bộ: mặt trước của đồ quay về +Z.
# ---------------------------------------------------------------------------

def legs(sc, g, w, d, h, m, t=0.05, inset=0.03):
    for i, (sx, sz) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        sc.box("Leg%d" % (i + 1), g, (sx * (w / 2 - t / 2 - inset), h / 2, sz * (d / 2 - t / 2 - inset)),
               (t, h, t), m)


def bed(sc, name, parent, pos, rot, w, l, frame, linen, blanket, pillow, headboard_h=1.0, posts=False):
    g = sc.group(name, parent, pos, rot)
    sc.box("Base", g, (0, 0.27, 0), (w, 0.24, l), frame)
    legs(sc, g, w, l, 0.15, frame, t=0.08, inset=0)
    sc.box("Mattress", g, (0, 0.47, 0.02), (w - 0.08, 0.16, l - 0.1), linen)
    sc.box("Blanket", g, (0, 0.56, 0.3), (w - 0.04, 0.04, l * 0.62), blanket)
    sc.box("Headboard", g, (0, headboard_h / 2, -l / 2 + 0.04), (w + 0.04, headboard_h, 0.08), frame)
    sc.box("Footboard", g, (0, 0.3, l / 2 - 0.03), (w + 0.04, 0.6, 0.06), frame)
    n = 2 if w > 1.3 else 1
    for i in range(n):
        x = 0 if n == 1 else (-1 + 2 * i) * w / 4
        sc.box("Pillow%d" % (i + 1), g, (x, 0.6, -l / 2 + 0.32), (w / n - 0.15, 0.12, 0.38), pillow)
    if posts:
        # Cọc màn (khung mắc màn) kiểu giường gỗ cũ.
        for i, (sx, sz) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
            sc.box("NetPost%d" % (i + 1), g, (sx * (w / 2 + 0.02), 0.95, sz * (l / 2 - 0.03)),
                   (0.04, 1.9, 0.04), frame)
        sc.box("NetRailL", g, (-w / 2 - 0.02, 1.88, 0), (0.03, 0.03, l), frame)
        sc.box("NetRailR", g, (w / 2 + 0.02, 1.88, 0), (0.03, 0.03, l), frame)
    return g


def wardrobe(sc, name, parent, pos, rot, w, h, d, body, trim, doors=2):
    g = sc.group(name, parent, pos, rot)
    sc.box("Body", g, (0, h / 2 + 0.05, 0), (w, h - 0.1, d), body)
    sc.box("Plinth", g, (0, 0.025, -0.02), (w - 0.06, 0.05, d - 0.06), trim)
    sc.box("Crown", g, (0, h - 0.02, 0.01), (w + 0.04, 0.04, d + 0.04), trim)
    for i in range(1, doors):
        sc.box("DoorGap%d" % i, g, (-w / 2 + w * i / doors, h / 2 + 0.05, d / 2 + 0.003), (0.012, h - 0.2, 0.01), trim)
    for i in range(doors):
        x = -w / 2 + w * (i + 1) / doors - 0.06 if i < doors / 2 else -w / 2 + w * i / doors + 0.06
        sc.box("Handle%d" % (i + 1), g, (x, h * 0.55, d / 2 + 0.02), (0.02, 0.16, 0.03), trim)
    return g


def chest_of_drawers(sc, name, parent, pos, rot, w, h, d, body, front, drawers=4):
    g = sc.group(name, parent, pos, rot)
    sc.box("Body", g, (0, h / 2 + 0.04, 0), (w, h - 0.08, d), body)
    legs(sc, g, w, d, 0.08, body, t=0.05, inset=0.01)
    dh = (h - 0.14) / drawers
    for i in range(drawers):
        y = 0.1 + dh * (i + 0.5)
        sc.box("Drawer%d" % (i + 1), g, (0, y, d / 2 + 0.008), (w - 0.06, dh - 0.03, 0.016), front)
        sc.box("Knob%d" % (i + 1), g, (0, y, d / 2 + 0.03), (0.06, 0.025, 0.025), body)
    return g


def desk(sc, name, parent, pos, rot, w, d, wood, front, drawer_side=1):
    g = sc.group(name, parent, pos, rot)
    sc.box("Top", g, (0, 0.735, 0), (w, 0.03, d), wood)
    x = drawer_side * (w / 2 - 0.22)
    sc.box("DrawerBlock", g, (x, 0.36, 0), (0.42, 0.72, d - 0.04), wood)
    for i in range(3):
        y = 0.13 + i * 0.22
        sc.box("Drawer%d" % (i + 1), g, (x, y, d / 2 - 0.01), (0.38, 0.18, 0.015), front)
    lx = -drawer_side * (w / 2 - 0.04)
    sc.box("LegFront", g, (lx, 0.36, d / 2 - 0.05), (0.05, 0.72, 0.05), wood)
    sc.box("LegBack", g, (lx, 0.36, -d / 2 + 0.05), (0.05, 0.72, 0.05), wood)
    sc.box("ModestyPanel", g, (0, 0.5, -d / 2 + 0.02), (w - 0.1, 0.4, 0.02), wood)
    return g


def chair(sc, name, parent, pos, rot, wood, seat_h=0.45, w=0.44, back=True):
    g = sc.group(name, parent, pos, rot)
    sc.box("Seat", g, (0, seat_h - 0.02, 0), (w, 0.04, w), wood)
    legs(sc, g, w, w, seat_h - 0.04, wood, t=0.04, inset=0.0)
    if back:
        sc.box("Back", g, (0, seat_h + 0.25, -w / 2 + 0.02), (w, 0.45, 0.03), wood)
    return g


def table(sc, name, parent, pos, rot, w, d, h, wood, t=0.05):
    g = sc.group(name, parent, pos, rot)
    sc.box("Top", g, (0, h - 0.02, 0), (w, 0.04, d), wood)
    legs(sc, g, w, d, h - 0.04, wood, t=t)
    return g


def bulb(sc, name, parent, pos, light_color, energy, rng, glass, cord, cord_len=0.5, shadow=True,
         shade=None):
    """Bóng đèn treo: dây + bóng phát sáng + OmniLight3D."""
    lp = sc.node(name, "OmniLight3D", parent, [
        ("transform", xform(pos)),
        ("light_color", color(light_color)),
        ("light_energy", f(energy)),
        ("shadow_enabled", "true" if shadow else "false"),
        ("omni_range", f(rng)),
        ("omni_attenuation", "1.2"),
    ])
    g = sc.group("Fixture", lp, collision=False)
    sc.box("Cord", g, (0, cord_len / 2 + 0.05, 0), (0.012, cord_len, 0.012), cord)
    sc.sphere("Bulb", g, (0, 0, 0), 0.05, glass)
    if shade:
        sc.cyl("Shade", g, (0, 0.08, 0), 0.16, 0.06, shade)
    return lp


def player(sc, rid, pos, rot_y):
    sc.instance("Player", rid, props=[("transform", xform(pos, rot_y))])


def environment(sc, rid, top, horizon, ground_horizon, ground_bottom, ambient, ambient_energy,
                sky_energy=1.0, fog_color=None, fog_density=0.0, exposure=1.0):
    sc.sub_res("ProceduralSkyMaterial", "SkyMat_" + rid, [
        ("sky_top_color", color(top)), ("sky_horizon_color", color(horizon)),
        ("ground_bottom_color", color(ground_bottom)), ("ground_horizon_color", color(ground_horizon)),
        ("sky_energy_multiplier", f(sky_energy)),
    ])
    sc.sub_res("Sky", "Sky_" + rid, [("sky_material", 'SubResource("SkyMat_%s")' % rid)])
    props = [
        ("background_mode", "2"), ("sky", 'SubResource("Sky_%s")' % rid),
        ("ambient_light_source", "3"), ("ambient_light_color", color(ambient)),
        ("ambient_light_sky_contribution", "0.5"), ("ambient_light_energy", f(ambient_energy)),
        ("tonemap_mode", "3"), ("tonemap_exposure", f(exposure)),
        ("ssao_enabled", "true"), ("glow_enabled", "true"), ("glow_intensity", "0.5"),
    ]
    if fog_color:
        props += [("fog_enabled", "true"), ("fog_light_color", color(fog_color)), ("fog_density", f(fog_density))]
    sc.sub_res("Environment", "Env_" + rid, props)
    sc.node("WorldEnvironment", "WorldEnvironment", ".", [("environment", 'SubResource("Env_%s")' % rid)])


def sun(sc, name, direction, light_color, energy):
    d = direction
    n = math.sqrt(sum(c * c for c in d))
    d = [c / n for c in d]
    z = [-c for c in d]
    up = [0, 1, 0]
    x = [up[1] * z[2] - up[2] * z[1], up[2] * z[0] - up[0] * z[2], up[0] * z[1] - up[1] * z[0]]
    n = math.sqrt(sum(c * c for c in x))
    x = [c / n for c in x]
    y = [z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]]
    b = [x[0], y[0], z[0], x[1], y[1], z[1], x[2], y[2], z[2]]
    sc.node(name, "DirectionalLight3D", ".", [
        ("transform", xform((0, 8, 0), basis=b)),
        ("light_color", color(light_color)), ("light_energy", f(energy)),
        ("shadow_enabled", "true"), ("directional_shadow_max_distance", "40.0"),
    ])


def window_bars(sc, parent, name, center, width, height, along_x, mat, n=6):
    g = sc.group(name, parent, collision=False)
    for i in range(n):
        o = -width / 2 + width * (i + 1) / (n + 1)
        p = (center[0] + (o if along_x else 0), center[1], center[2] + (0 if along_x else o))
        sc.box("Bar%d" % (i + 1), g, p, (0.02, height, 0.02), mat)


# ---------------------------------------------------------------------------
# 1. Phòng ngủ trong mơ: sáng sủa, hiện đại, gọn gàng.
# ---------------------------------------------------------------------------

def build_dream_bedroom():
    sc = Scene("DreamBedroom")
    p_rid = sc.ext_res("PackedScene", "res://scenes/player/Player.tscn")
    i_rid = sc.ext_res("Script", "res://scripts/interaction/Interactable.gd")

    wall = sc.mat("Wall", (0.93, 0.91, 0.87), 0.9)
    floor = sc.mat("FloorOak", (0.74, 0.58, 0.4), 0.6)
    ceil = sc.mat("Ceiling", (0.97, 0.96, 0.94), 0.95)
    trim = sc.mat("Trim", (0.98, 0.98, 0.97), 0.7)
    grass = sc.mat("Grass", (0.33, 0.5, 0.25), 1.0)
    linen = sc.mat("Linen", (0.96, 0.96, 0.95), 0.9)
    duvet = sc.mat("Duvet", (0.82, 0.86, 0.9), 0.9)
    head = sc.mat("Upholstery", (0.52, 0.56, 0.6), 0.95)
    wood_light = sc.mat("WoodLight", (0.86, 0.8, 0.7), 0.6)
    wood_front = sc.mat("WoodFront", (0.9, 0.86, 0.78), 0.55)
    metal_dark = sc.mat("SafeSteel", (0.14, 0.15, 0.17), 0.35, metallic=0.8)
    brass = sc.mat("Brass", (0.85, 0.7, 0.4), 0.3, metallic=0.9)
    curtain = sc.mat("Curtain", (0.97, 0.95, 0.9), 0.95, alpha=0.75)
    rug = sc.mat("Rug", (0.78, 0.72, 0.64), 1.0)
    lampshade = sc.mat("LampShade", (1, 0.95, 0.85), 0.9, emission=(1, 0.85, 0.6), energy=0.6)
    glass = sc.mat("BulbWarm", (1, 0.9, 0.7), 0.2, emission=(1, 0.85, 0.6), energy=2.0)
    plant = sc.mat("Plant", (0.25, 0.45, 0.2), 0.9)
    pot = sc.mat("Pot", (0.85, 0.82, 0.78), 0.6)
    mirror = sc.mat("Mirror", (0.8, 0.85, 0.9), 0.05, metallic=1.0)
    art = sc.mat("Artwork", (0.55, 0.68, 0.75), 0.8)

    environment(sc, "day", (0.32, 0.52, 0.85), (0.75, 0.85, 0.95), (0.6, 0.65, 0.6), (0.2, 0.25, 0.2),
                (0.95, 0.95, 1.0), 1.0, sky_energy=1.2)
    sun(sc, "Sun", (-0.35, -0.75, -0.55), (1, 0.96, 0.88), 2.2)

    # Kích thước trong lòng phòng: 5.5 x 5.0 m, cao 3.0 m.
    W, D, H, T = 5.5, 5.0, 3.0, 0.2
    hx, hz = W / 2, D / 2
    s = sc.group("Structure")
    sc.box("Ground", s, (0, -0.51, 0), (40, 1, 40), grass)
    sc.box("Floor", s, (0, -0.05, 0), (W + 2 * T, 0.1, D + 2 * T), floor)
    sc.box("Wall_Back", s, (0, H / 2, -hz - T / 2), (W + 2 * T, H, T), wall)
    sc.box("Wall_Front", s, (0, H / 2, hz + T / 2), (W + 2 * T, H, T), wall)
    sc.box("Wall_West", s, (-hx - T / 2, H / 2, 0), (T, H, D), wall)
    sc.box("Wall_East", s, (hx + T / 2, H / 2, 0), (T, H, D), wall)
    sc.box("Ceiling", s, (0, H + 0.075, 0), (W + 2 * T, 0.15, D + 2 * T), ceil)
    # Hai cửa sổ lớn ở tường trước.
    for i, x in enumerate((-1.3, 1.3)):
        sc.box("Window_Front%d" % (i + 1), s, (x, 1.45, hz + T / 2), (1.5, 1.7, T + 0.2), trim, subtract=True)

    deco = sc.group("Decor", collision=False)
    sc.box("Skirting_Back", deco, (0, 0.05, -hz + 0.005), (W, 0.1, 0.01), trim)
    sc.box("Skirting_West", deco, (-hx + 0.005, 0.05, 0), (0.01, 0.1, D), trim)
    sc.box("Rug", deco, (0, 0.005, -1.1), (2.9, 0.01, 2.6), rug)
    sc.box("ArtFrame", deco, (0, 1.95, -hz + 0.02), (1.1, 0.7, 0.03), trim)
    sc.box("ArtCanvas", deco, (0, 1.95, -hz + 0.04), (1.0, 0.6, 0.01), art)
    for i, x in enumerate((-1.3, 1.3)):
        sc.box("CurtainRod%d" % (i + 1), deco, (x, 2.5, hz - 0.08), (2.3, 0.025, 0.025), brass)
        sc.box("Curtain%dL" % (i + 1), deco, (x - 0.95, 1.3, hz - 0.1), (0.4, 2.4, 0.04), curtain)
        sc.box("Curtain%dR" % (i + 1), deco, (x + 0.95, 1.3, hz - 0.1), (0.4, 2.4, 0.04), curtain)
        sc.box("Sill%d" % (i + 1), deco, (x, 0.59, hz - 0.03), (1.6, 0.03, 0.12), trim)
    # Cửa ra vào (đóng) trên tường đông.
    sc.box("Door_Frame", deco, (hx - 0.01, 1.07, 1.4), (0.03, 2.14, 1.0), trim)
    sc.box("Door_Leaf", deco, (hx - 0.03, 1.03, 1.4), (0.03, 2.04, 0.9), wood_front)
    sc.box("Door_Handle", deco, (hx - 0.07, 1.0, 1.05), (0.05, 0.03, 0.14), brass)

    bed(sc, "Bed_King", ".", (0, 0, -1.4), 0, 1.9, 2.1, wood_light, linen, duvet, linen, headboard_h=1.25)
    sc.box("HeadboardPanel", "Bed_King", (0, 0.85, -0.99), (1.8, 0.7, 0.04), head)
    sc.box("BenchTop", sc.group("Bench_Foot", ".", (0, 0, 0.0)), (0, 0.42, 0), (1.4, 0.06, 0.42), head)
    legs(sc, "Bench_Foot", 1.4, 0.42, 0.39, wood_light, t=0.04)
    for i, x in enumerate((-1.35, 1.35)):
        n = "Nightstand%d" % (i + 1)
        chest_of_drawers(sc, n, ".", (x, 0, -2.22), 0, 0.5, 0.55, 0.4, wood_light, wood_front, drawers=2)
        lamp = sc.node("Lamp", "OmniLight3D", n, [
            ("transform", xform((0, 0.95, 0))), ("light_color", color((1, 0.85, 0.65))),
            ("light_energy", "0.35"), ("omni_range", "2.5")])
        lg = sc.group("Fixture", lamp, collision=False)
        sc.cyl("Base", lg, (0, -0.3, 0), 0.06, 0.18, brass)
        sc.cyl("Shade", lg, (0, -0.05, 0), 0.14, 0.2, lampshade)

    wardrobe(sc, "Wardrobe", ".", (-hx + 0.31, 0, 0.7), 90, 2.2, 2.3, 0.6, wood_light, wood_front, doors=3)

    # Két sắt cạnh tủ quần áo (vật tương tác).
    safe = sc.node("Safe", "Area3D", ".", [
        ("transform", xform((-hx + 0.27, 0, -1.05), 90)),
        ("script", 'ExtResource("%s")' % i_rid),
        ("item_id", '&"dream_safe"'),
        ("display_name_key", '"OBJ_SAFE_NAME"'),
    ])
    sg = sc.group("Body", safe)
    sc.box("Box", sg, (0, 0.3, 0), (0.48, 0.6, 0.46), metal_dark)
    sc.box("DoorPanel", sg, (0, 0.3, 0.235), (0.4, 0.5, 0.01), metal_dark)
    sc.cyl("Dial", sg, (0.08, 0.36, 0.25), 0.04, 0.02, brass)
    sc.box("Handle", sg, (-0.1, 0.3, 0.25), (0.02, 0.12, 0.03), brass)
    sc.sub_res("BoxShape3D", "Shape_safe", [("size", "Vector3(0.6, 0.7, 0.6)")])
    sc.node("CollisionShape3D", "CollisionShape3D", safe, [
        ("transform", xform((0, 0.35, 0))), ("shape", 'SubResource("Shape_safe")')])

    # Bàn trang điểm + gương ở tường đông.
    desk(sc, "Vanity", ".", (hx - 0.27, 0, -1.1), -90, 1.1, 0.5, wood_light, wood_front)
    sc.box("Mirror", deco, (hx - 0.02, 1.45, -1.1), (0.02, 0.8, 0.6), mirror)
    chair(sc, "Vanity_Stool", ".", (hx - 0.85, 0, -1.1), 90, head, back=False)

    # Ghế bành cạnh cửa sổ và chậu cây.
    ag = sc.group("Armchair", ".", (-1.7, 0, 1.85), 150)
    sc.box("Seat", ag, (0, 0.3, 0.03), (0.75, 0.2, 0.7), head)
    sc.box("Back", ag, (0, 0.65, -0.3), (0.75, 0.6, 0.15), head)
    sc.box("ArmL", ag, (-0.33, 0.48, 0.03), (0.12, 0.25, 0.7), head)
    sc.box("ArmR", ag, (0.33, 0.48, 0.03), (0.12, 0.25, 0.7), head)
    legs(sc, ag, 0.7, 0.65, 0.2, wood_light, t=0.04)
    pg = sc.group("Plant", ".", (2.35, 0, 0.3))
    sc.cyl("Pot", pg, (0, 0.2, 0), 0.18, 0.4, pot)
    sc.sphere("Leaves", pg, (0, 0.75, 0), 0.35, plant)

    bulb(sc, "CeilingLight", ".", (0, H - 0.1, 0), (1, 0.92, 0.8), 0.3, 6, glass, trim, cord_len=0.05,
         shadow=False)

    player(sc, p_rid, (0.6, 0.05, 1.4), 15)
    sc.save("scenes/levels/DreamBedroom.tscn")


# ---------------------------------------------------------------------------
# 2. Nhà cũ Bắc Bộ thập niên 198x: nhà cấp 4 ba gian, mái ngói, bếp sau,
#    hầm ngay dưới phòng của cô ấy (phòng ngủ phía đông).
# ---------------------------------------------------------------------------

def build_old_house():
    sc = Scene("OldHouse")
    p_rid = sc.ext_res("PackedScene", "res://scenes/player/Player.tscn")

    lime = sc.mat("WallLimewash", (0.8, 0.74, 0.56), 0.95)
    lime_dirty = sc.mat("WallKitchen", (0.5, 0.45, 0.36), 1.0)
    brick_floor = sc.mat("FloorBrickTile", (0.46, 0.33, 0.26), 0.9)
    ceil = sc.mat("CeilingPlaster", (0.72, 0.68, 0.56), 0.95)
    earth = sc.mat("Ground", (0.22, 0.2, 0.16), 1.0)
    yard = sc.mat("YardBrick", (0.4, 0.3, 0.24), 1.0)
    fence = sc.mat("FenceBrick", (0.5, 0.45, 0.38), 1.0)
    roof = sc.mat("RoofTile", (0.45, 0.2, 0.13), 0.9)
    concrete = sc.mat("CellarConcrete", (0.3, 0.3, 0.28), 1.0)
    wood = sc.mat("WoodDark", (0.3, 0.17, 0.09), 0.7)
    wood_mid = sc.mat("WoodMid", (0.42, 0.26, 0.14), 0.7)
    wood_old = sc.mat("WoodOld", (0.35, 0.28, 0.2), 0.95)
    glass_dark = sc.mat("CabinetGlass", (0.15, 0.17, 0.18), 0.1, metallic=0.3)
    linen = sc.mat("LinenOld", (0.82, 0.78, 0.68), 0.95)
    blanket = sc.mat("BlanketFloral", (0.45, 0.22, 0.2), 0.95)
    mat_floor = sc.mat("ReedMat", (0.75, 0.65, 0.42), 1.0)
    iron = sc.mat("Iron", (0.12, 0.12, 0.12), 0.6, metallic=0.6)
    tv_body = sc.mat("TVBody", (0.35, 0.3, 0.26), 0.6)
    tv_screen = sc.mat("TVScreen", (0.06, 0.08, 0.08), 0.15)
    red = sc.mat("AltarRed", (0.4, 0.1, 0.07), 0.6)
    gold = sc.mat("AltarGold", (0.75, 0.58, 0.25), 0.35, metallic=0.8)
    ceramic = sc.mat("Ceramic", (0.85, 0.82, 0.74), 0.3)
    jar = sc.mat("JarClay", (0.36, 0.24, 0.16), 0.8)
    brick_counter = sc.mat("BrickCounter", (0.5, 0.26, 0.18), 1.0)
    soot = sc.mat("Soot", (0.1, 0.09, 0.08), 1.0)
    paper = sc.mat("CalendarPaper", (0.9, 0.86, 0.75), 0.9)
    photo = sc.mat("PhotoBW", (0.35, 0.35, 0.33), 0.8)
    sack = sc.mat("Sack", (0.6, 0.52, 0.38), 1.0)
    bulb_glass = sc.mat("BulbYellow", (1, 0.85, 0.55), 0.2, emission=(1, 0.75, 0.4), energy=3.0)
    bulb_red = sc.mat("BulbRed", (1, 0.3, 0.2), 0.2, emission=(1, 0.2, 0.1), energy=3.0)
    cord = sc.mat("Cord", (0.08, 0.08, 0.08), 0.8)

    environment(sc, "night", (0.02, 0.03, 0.08), (0.1, 0.1, 0.16), (0.06, 0.06, 0.07), (0.02, 0.02, 0.02),
                (0.45, 0.5, 0.7), 0.12, sky_energy=0.6, fog_color=(0.06, 0.07, 0.1), fog_density=0.01)
    sun(sc, "Moon", (0.3, -0.6, -0.5), (0.6, 0.66, 0.85), 0.25)

    H, T = 3.2, 0.2           # cao trần nhà chính, độ dày tường
    HK = 2.8                   # cao trần bếp
    s = sc.group("Structure")
    # Nền đất dày 3 m để khoét hầm bên dưới.
    sc.box("Ground", s, (0, -1.5, 0), (30, 3, 30), earth)
    sc.box("Yard", s, (0, 0.01, 6.0), (16, 0.02, 6.0), yard)
    # Tường rào bao quanh khu đất (16 x 18 m).
    sc.box("Fence_South", s, (0, 0.8, 9.1), (16.4, 1.6, 0.2), fence)
    sc.box("Fence_North", s, (0, 0.8, -9.1), (16.4, 1.6, 0.2), fence)
    sc.box("Fence_West", s, (-8.1, 0.8, 0), (0.2, 1.6, 18.0), fence)
    sc.box("Fence_East", s, (8.1, 0.8, 0), (0.2, 1.6, 18.0), fence)
    # Nhà chính: trong lòng x -6.0..6.0, z -2.75..2.75.
    sc.box("Floor_Main", s, (0, 0.01, 0), (12.0, 0.02, 5.5), brick_floor)
    sc.box("Wall_Front", s, (0, H / 2, 2.85), (12.4, H, T), lime)
    sc.box("Wall_Back", s, (0, H / 2, -2.85), (12.4, H, T), lime)
    sc.box("Wall_West", s, (-6.1, H / 2, 0), (T, H, 5.9), lime)
    sc.box("Wall_East", s, (6.1, H / 2, 0), (T, H, 5.9), lime)
    sc.box("Wall_Partition_West", s, (-2.5, H / 2, 0), (T, H, 5.5), lime)
    sc.box("Wall_Partition_East", s, (2.5, H / 2, 0), (T, H, 5.5), lime)
    sc.box("Ceiling_Main", s, (0, H + 0.075, 0), (12.4, 0.15, 5.9), ceil)
    # Bếp sau: trong lòng x -2.25..2.25, z -7.0..-2.95.
    sc.box("Floor_Kitchen", s, (0, 0.01, -4.975), (4.5, 0.02, 4.05), concrete)
    sc.box("Wall_Kitchen_West", s, (-2.35, HK / 2, -5.025), (T, HK, 4.15), lime_dirty)
    sc.box("Wall_Kitchen_East", s, (2.35, HK / 2, -5.025), (T, HK, 4.15), lime_dirty)
    sc.box("Wall_Kitchen_Back", s, (0, HK / 2, -7.1), (4.9, HK, T), lime_dirty)
    sc.box("Ceiling_Kitchen", s, (0, HK + 0.075, -5.025), (4.9, 0.15, 4.15), ceil)

    # Khoét cửa đi, cửa sổ, hầm.
    sub = lambda n, c, sz: sc.box(n, s, c, sz, wood, subtract=True)
    sub("Door_Main", (0, 1.2, 2.85), (2.0, 2.4, 0.4))
    sub("Door_Bedroom1", (-2.5, 1.05, -1.4), (0.4, 2.1, 0.9))
    sub("Door_Bedroom2", (2.5, 1.05, -1.4), (0.4, 2.1, 0.9))
    sub("Door_Kitchen", (1.6, 1.05, -2.85), (0.9, 2.1, 0.4))
    sub("Window_Bedroom1_Front", (-4.3, 1.55, 2.85), (1.2, 1.3, 0.4))
    sub("Window_Bedroom2_Front", (4.0, 1.55, 2.85), (1.2, 1.3, 0.4))
    sub("Window_Living_FrontL", (-1.75, 1.55, 2.85), (0.9, 1.3, 0.4))
    sub("Window_Living_FrontR", (1.75, 1.55, 2.85), (0.9, 1.3, 0.4))
    sub("Window_Bedroom1_West", (-6.1, 1.55, 1.5), (0.4, 1.3, 1.1))
    sub("Window_Bedroom2_East", (6.1, 1.55, 1.2), (0.4, 1.3, 1.1))
    sub("Window_Kitchen_East", (2.35, 1.6, -5.0), (0.4, 1.0, 1.0))
    # Hầm: dưới phòng ngủ đông, trong lòng x 2.6..6.0, z -2.75..2.75, cao 2.1 m.
    sc.box("Cellar_Space", s, (4.3, -1.25, 0), (3.4, 2.1, 5.5), concrete, subtract=True)
    # Miệng hầm 0.9 x 2.55 m trên sàn phòng cô ấy.
    sc.box("Cellar_Hatch", s, (4.85, -0.1, 0.825), (0.9, 0.3, 2.55), concrete, subtract=True)

    # Mái ngói hai mái (chỉ để nhìn từ sân, không va chạm).
    rf = sc.group("Roof", collision=False)
    a = math.degrees(math.atan2(1.6, 2.95))
    L = math.hypot(2.95, 1.6) + 0.6
    off = 0.3
    for nme, sgn in (("Roof_Front", 1), ("Roof_Back", -1)):
        cz = sgn * (2.95 / 2 + off * math.cos(math.radians(a)))
        cy = H + 0.15 + 0.8 - off * math.sin(math.radians(a)) + 0.06
        sc.box(nme, rf, (0, cy, cz), (13.0, 0.12, L), roof, basis=basis_x(sgn * a))
    ka = math.degrees(math.atan2(0.35, 4.4))
    sc.box("Roof_Kitchen", rf, (0, HK + 0.3, -5.1), (5.4, 0.1, 4.6), roof, basis=basis_x(-ka))

    # Song sắt cửa sổ.
    window_bars(sc, ".", "Bars_Bedroom1_Front", (-4.3, 1.55, 2.85), 1.2, 1.3, True, iron)
    window_bars(sc, ".", "Bars_Bedroom2_Front", (4.0, 1.55, 2.85), 1.2, 1.3, True, iron)
    window_bars(sc, ".", "Bars_Living_FrontL", (-1.75, 1.55, 2.85), 0.9, 1.3, True, iron, n=4)
    window_bars(sc, ".", "Bars_Living_FrontR", (1.75, 1.55, 2.85), 0.9, 1.3, True, iron, n=4)
    window_bars(sc, ".", "Bars_Bedroom1_West", (-6.1, 1.55, 1.5), 1.1, 1.3, False, iron)
    window_bars(sc, ".", "Bars_Bedroom2_East", (6.1, 1.55, 1.2), 1.1, 1.3, False, iron)
    window_bars(sc, ".", "Bars_Kitchen_East", (2.35, 1.6, -5.0), 1.0, 1.0, False, iron, n=5)

    # Cánh cửa gỗ (mở hé) để có cảm giác nhà thật; không chặn lối đi.
    dg = sc.group("Doors", collision=False)
    sc.box("Door_Main_LeafL", dg, (-1.05, 1.2, 2.3), (0.05, 2.38, 0.98), wood, rot_y=0)
    sc.box("Door_Main_LeafR", dg, (1.05, 1.2, 2.3), (0.05, 2.38, 0.98), wood, rot_y=0)
    sc.box("Door_Bedroom1_Leaf", dg, (-2.95, 1.04, -0.92), (0.88, 2.08, 0.04), wood_mid)
    sc.box("Door_Bedroom2_Leaf", dg, (2.95, 1.04, -0.92), (0.88, 2.08, 0.04), wood_mid)
    sc.box("Door_Kitchen_Leaf", dg, (1.12, 1.04, -3.4), (0.04, 2.08, 0.88), wood_mid)

    # ---------------- Phòng khách (gian giữa) ----------------
    ag = sc.group("Altar", ".", (0, 0, -2.42))
    sc.box("Top", ag, (0, 1.1, 0), (1.6, 0.06, 0.6), red)
    sc.box("Apron", ag, (0, 0.98, 0.28), (1.5, 0.18, 0.03), gold)
    legs(sc, ag, 1.6, 0.6, 1.07, red, t=0.07)
    sc.box("Shelf", ag, (0, 0.25, 0), (1.45, 0.04, 0.5), red)
    sc.cyl("IncenseBowl", ag, (0, 1.2, 0.05), 0.09, 0.12, ceramic)
    sc.cyl("VaseL", ag, (-0.55, 1.28, 0), 0.06, 0.3, ceramic)
    sc.cyl("VaseR", ag, (0.55, 1.28, 0), 0.06, 0.3, ceramic)
    sc.box("PhotoFrameL", ag, (-0.25, 1.3, -0.15), (0.24, 0.32, 0.03), gold)
    sc.box("PhotoFrameR", ag, (0.25, 1.3, -0.15), (0.24, 0.32, 0.03), gold)
    sc.box("FruitPlate", ag, (0, 1.15, 0.2), (0.3, 0.04, 0.2), gold)
    deco = sc.group("Decor", collision=False)
    sc.box("Altar_Panel", deco, (0, 2.2, -2.74), (1.4, 0.9, 0.02), red)
    sc.box("Altar_Calligraphy", deco, (0, 2.2, -2.72), (1.1, 0.5, 0.01), gold)
    sc.box("Calendar", deco, (-2.39, 1.7, 1.6), (0.01, 0.5, 0.35), paper)
    sc.box("FamilyPhoto", deco, (2.39, 1.8, 0.9), (0.01, 0.45, 0.6), photo)
    sc.box("Clock", deco, (0, 2.6, 2.74), (0.35, 0.35, 0.03), wood)
    bulb(sc, "Light_AltarRed", ".", (0, 1.45, -2.55), (1, 0.25, 0.12), 0.4, 2.5, bulb_red, cord,
         cord_len=0.02, shadow=False)

    # Tủ chè + TV đen trắng dọc tường ngăn phía tây (quay vào phòng khách).
    tg = sc.group("TuChe", ".", (-2.12, 0, 0.9), 90)
    sc.box("Body", tg, (0, 0.45, 0), (1.8, 0.7, 0.48), wood)
    legs(sc, tg, 1.8, 0.48, 0.1, wood, t=0.05)
    for i in range(3):
        sc.box("GlassDoor%d" % (i + 1), tg, (-0.6 + i * 0.6, 0.45, 0.245), (0.5, 0.5, 0.01), glass_dark)
    sc.box("Top", tg, (0, 0.82, 0), (1.86, 0.04, 0.52), wood)
    tv = sc.group("TV_CRT", ".", (-2.12, 0.84, 0.9), 90)
    sc.box("Body", tv, (0, 0.23, -0.03), (0.56, 0.46, 0.44), tv_body)
    sc.box("Screen", tv, (-0.06, 0.24, 0.195), (0.36, 0.3, 0.01), tv_screen)
    sc.box("Knobs", tv, (0.2, 0.24, 0.195), (0.08, 0.3, 0.01), glass_dark)
    sc.box("AntennaL", tv, (-0.12, 0.62, -0.05), (0.01, 0.35, 0.01), iron, basis=[0.94, 0.34, 0, -0.34, 0.94, 0, 0, 0, 1])
    sc.box("AntennaR", tv, (0.12, 0.62, -0.05), (0.01, 0.35, 0.01), iron, basis=[0.94, -0.34, 0, 0.34, 0.94, 0, 0, 0, 1])

    # Bộ bàn ghế gỗ tiếp khách.
    table(sc, "Salon_Table", ".", (0.2, 0, 0.9), 0, 1.1, 0.6, 0.48, wood)
    sc.cyl("Teapot", "Salon_Table", (0, 0.53, 0), 0.07, 0.1, ceramic)
    bg = sc.group("Salon_Bench", ".", (1.45, 0, 0.9), -90)
    sc.box("Seat", bg, (0, 0.44, 0), (1.7, 0.05, 0.55), wood)
    sc.box("Back", bg, (0, 0.8, -0.25), (1.7, 0.6, 0.04), wood)
    sc.box("ArmL", bg, (-0.83, 0.62, 0), (0.05, 0.3, 0.55), wood)
    sc.box("ArmR", bg, (0.83, 0.62, 0), (0.05, 0.3, 0.55), wood)
    legs(sc, bg, 1.7, 0.55, 0.42, wood, t=0.05)
    chair(sc, "Salon_ChairS", ".", (0.2, 0, 1.75), 180, wood)
    chair(sc, "Salon_ChairN", ".", (0.2, 0, 0.05), 0, wood)
    # Quạt trần.
    fan = sc.group("CeilingFan", ".", (0.2, 0, 0.9), 0, collision=False)
    sc.box("Rod", fan, (0, 2.95, 0), (0.03, 0.5, 0.03), iron)
    sc.cyl("Motor", fan, (0, 2.68, 0), 0.12, 0.1, wood_old)
    for i in range(3):
        sc.box("Blade%d" % (i + 1), fan, (0, 2.66, 0), (0.12, 0.01, 1.3), wood_old, rot_y=i * 60)
    bulb(sc, "Light_Living", ".", (0.0, 2.55, -1.2), (1, 0.7, 0.38), 1.3, 7.0, bulb_glass, cord, cord_len=0.6)

    # ---------------- Phòng ngủ tây (bố mẹ) ----------------
    bed(sc, "Bed_Parents", ".", (-5.0, 0, -1.0), 90, 1.6, 2.0, wood, mat_floor, blanket, linen,
        headboard_h=0.9, posts=True)
    wardrobe(sc, "Wardrobe_Parents", ".", (-3.4, 0, -2.44), 0, 1.2, 1.9, 0.58, wood, wood_mid)
    desk(sc, "Desk_Parents", ".", (-4.3, 0, 2.43), 180, 1.1, 0.55, wood_mid, wood)
    chair(sc, "Chair_Parents", ".", (-4.3, 0, 1.85), 0, wood_mid)
    chest_of_drawers(sc, "Drawers_Parents", ".", (-2.85, 0, 1.4), -90, 0.9, 0.95, 0.45, wood, wood_mid)
    sc.box("Chest_Lid", sc.group("Chest_Parents", ".", (-5.6, 0, 2.2), 90), (0, 0.25, 0), (0.9, 0.5, 0.5), wood_old)
    bulb(sc, "Light_Bedroom1", ".", (-4.3, 2.6, 0.0), (1, 0.7, 0.38), 0.9, 6.0, bulb_glass, cord, cord_len=0.55)

    # ---------------- Phòng ngủ đông (phòng của cô ấy, có hầm bên dưới) ----------------
    bed(sc, "Bed_Her", ".", (5.0, 0, -2.05), -90, 1.4, 2.0, wood, linen, blanket, linen,
        headboard_h=0.9, posts=True)
    chest_of_drawers(sc, "Nightstand_Her", ".", (5.75, 0, -1.1), -90, 0.45, 0.55, 0.4, wood, wood_mid, drawers=2)
    wardrobe(sc, "Wardrobe_Her", ".", (3.4, 0, -2.44), 0, 1.2, 1.9, 0.58, wood, wood_mid)
    desk(sc, "Desk_Her", ".", (2.88, 0, 1.15), 90, 1.1, 0.55, wood_mid, wood, drawer_side=-1)
    chair(sc, "Chair_Her", ".", (3.45, 0, 1.15), -90, wood_mid)
    chest_of_drawers(sc, "Drawers_Her", ".", (3.2, 0, 2.5), 180, 0.9, 0.85, 0.45, wood, wood_mid)
    sc.box("Mirror_Her", deco, (2.61, 1.6, 0.0), (0.02, 0.6, 0.4), ceramic)
    bulb(sc, "Light_Bedroom2", ".", (4.2, 2.6, -0.6), (1, 0.7, 0.38), 0.9, 6.0, bulb_glass, cord, cord_len=0.55)

    # Cầu thang xuống hầm: bậc chỉ để nhìn, va chạm là một mặt dốc (CharacterBody3D không tự bước bậc).
    st = sc.group("Cellar_Stairs", ".", collision=False)
    # Mặt dốc đi từ mặt sàn gạch (y = 0.02) xuống sàn hầm (y = -2.3).
    n, top_z, bot_z, depth = 12, -0.45, 2.1, 2.32
    rise, run = depth / n, (bot_z - top_z) / n
    for k in range(n - 1):
        z0 = bot_z - (k + 1) * run
        top = -2.3 + (k + 1) * rise
        sc.box("Step%02d" % (k + 1), st, (4.85, (top - 2.3) / 2, z0 + run / 2), (0.9, top + 2.3, run), wood_old)
    ramp_len = math.hypot(bot_z - top_z, depth)
    ang = math.degrees(math.atan2(depth, bot_z - top_z))
    b = basis_x(ang)
    mid = (4.85, 0.02 - depth / 2, (top_z + bot_z) / 2)
    nrm = (0, math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    c = (mid[0], mid[1] - 0.05 * nrm[1], mid[2] - 0.05 * nrm[2])
    sc.sub_res("BoxShape3D", "Shape_cellar_ramp", [("size", "Vector3(0.9, 0.1, %s)" % f(ramp_len))])
    rb = sc.node("Cellar_StairsRamp", "StaticBody3D", ".", [("transform", xform(c, basis=b))])
    sc.node("CollisionShape3D", "CollisionShape3D", rb, [("shape", 'SubResource("Shape_cellar_ramp")')])

    # ---------------- Hầm ----------------
    cg = sc.group("Cellar_Shelves", ".", (2.85, -2.3, -1.2), 90)
    for i in range(3):
        sc.box("Board%d" % (i + 1), cg, (0, 0.3 + i * 0.55, 0), (1.8, 0.03, 0.4), wood_old)
    for i, x in enumerate((-0.88, 0.88)):
        sc.box("Upright%d" % (i + 1), cg, (x, 0.85, 0), (0.04, 1.7, 0.4), wood_old)
    for i, (x, y) in enumerate([(-0.5, 0.42), (0.3, 0.42), (-0.2, 0.97), (0.55, 1.52)]):
        sc.box("Box%d" % (i + 1), cg, (x, y, 0), (0.35, 0.22, 0.3), sack)
    chest = sc.group("Cellar_Chest", ".", (5.4, -2.3, -2.2), -90)
    sc.box("Body", chest, (0, 0.28, 0), (1.0, 0.56, 0.55), wood_old)
    sc.box("Band", chest, (0, 0.28, 0.28), (1.02, 0.06, 0.01), iron)
    for i, (x, z) in enumerate([(3.2, 1.9), (3.6, 2.3), (3.1, 2.4)]):
        sc.box("Crate%d" % (i + 1), sc.group("Cellar_Crate%d" % (i + 1), ".", (x, -2.3, z), 12 * i),
               (0, 0.22, 0), (0.45, 0.44, 0.45), wood_old)
    sc.box("Sacks", sc.group("Cellar_Sacks", ".", (5.6, -2.3, 0.2)), (0, 0.2, 0), (0.6, 0.4, 0.9), sack)
    bulb(sc, "Light_Cellar", ".", (4.3, -0.55, -0.8), (1, 0.65, 0.32), 0.6, 5.0, bulb_glass, cord, cord_len=0.25)

    # ---------------- Bếp ----------------
    kc = sc.group("Kitchen_Hearth", ".", (-1.0, 0, -6.7))
    sc.box("Counter", kc, (0, 0.4, 0), (2.2, 0.8, 0.6), brick_counter)
    sc.box("CounterTop", kc, (0, 0.81, 0), (2.25, 0.03, 0.64), concrete)
    sc.cyl("Stove", kc, (-0.5, 0.92, 0), 0.16, 0.2, iron)
    sc.cyl("Pot", kc, (-0.5, 1.1, 0), 0.15, 0.16, soot)
    sc.box("CuttingBoard", kc, (0.5, 0.84, 0.05), (0.45, 0.03, 0.3), wood_old)
    sc.box("SootMark", deco, (-1.5, 1.6, -6.99), (0.7, 1.4, 0.01), soot)
    wc = sc.group("Kitchen_WallCabinet", ".", (-1.0, 1.65, -6.82))
    sc.box("Body", wc, (0, 0.3, 0), (2.0, 0.6, 0.35), wood_mid)
    sc.box("DoorGap", wc, (0, 0.3, 0.176), (0.01, 0.55, 0.01), wood)
    cb = sc.group("Kitchen_DishCabinet", ".", (-2.0, 0, -4.2), 90)
    sc.box("Body", cb, (0, 0.8, 0), (0.9, 1.4, 0.45), wood_mid)
    legs(sc, cb, 0.9, 0.45, 0.1, wood_mid, t=0.05)
    sc.box("MeshDoorTop", cb, (0, 1.15, 0.228), (0.8, 0.55, 0.01), glass_dark)
    sc.box("DoorBottom", cb, (0, 0.5, 0.228), (0.8, 0.55, 0.01), wood)
    for i, z in enumerate((-6.55, -5.85)):
        sc.cyl("Jar", sc.group("Kitchen_WaterJar%d" % (i + 1), ".", (1.8, 0, z)), (0, 0.32, 0), 0.3, 0.64, jar)
    table(sc, "Kitchen_LowTable", ".", (0.4, 0, -4.6), 0, 0.8, 0.8, 0.32, wood_old, t=0.04)
    for i, (x, z) in enumerate([(0.4, -5.25), (0.4, -3.95), (-0.25, -4.6), (1.05, -4.6)]):
        table(sc, "Kitchen_Stool%d" % (i + 1), ".", (x, 0, z), 0, 0.28, 0.28, 0.24, wood_old, t=0.03)
    shelf = sc.group("Kitchen_Shelf", ".", (2.1, 1.5, -3.6), -90, collision=False)
    sc.box("Board", shelf, (0, 0, 0), (0.9, 0.03, 0.25), wood_old)
    for i in range(3):
        sc.cyl("Bowl%d" % (i + 1), shelf, (-0.3 + i * 0.3, 0.05, 0), 0.07, 0.06, ceramic)
    bulb(sc, "Light_Kitchen", ".", (0.0, 2.35, -5.0), (1, 0.68, 0.35), 0.8, 6.0, bulb_glass, cord, cord_len=0.4)

    # Đèn hiên ngoài sân.
    bulb(sc, "Light_Porch", ".", (2.6, 2.7, 3.2), (1, 0.7, 0.38), 0.6, 6.0, bulb_glass, cord, cord_len=0.2)

    player(sc, p_rid, (0, 0.05, 6.5), 0)
    sc.save("scenes/levels/OldHouse.tscn")


if __name__ == "__main__":
    build_dream_bedroom()
    build_old_house()
