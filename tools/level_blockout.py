#!/usr/bin/env python3
"""Sinh hai bối cảnh chi tiết (CSG + mesh nguyên khối + texture PBR) cho game.

Chạy:  python3 tools/level_blockout.py
Kết quả: scenes/levels/DreamBedroom.tscn và scenes/levels/OldHouse.tscn

Texture lấy từ res://assets/textures/: phần lớn là texture CC0 thật của Poly Haven
(tools/fetch_cc0_assets.py, danh sách trong assets/textures/cc0_sets.json), phần còn lại
sinh bằng tools/bake_textures.gd. Model trang trí CC0 nằm trong res://assets/models/.

LƯU Ý: chạy lại script sẽ GHI ĐÈ hai file .tscn trên. Nếu đã chỉnh scene
bằng Godot editor thì đừng chạy lại, hoặc sửa số đo ở đây trước rồi mới chạy.

Quy ước: 1 đơn vị = 1 mét, trục +Y lên trên, mặt tiền nhà quay về +Z (hướng nam).
- Kết cấu và đồ đạc lớn là CSGCombiner3D có va chạm (người chơi không đi xuyên).
- Đồ trang trí nhỏ là MeshInstance3D không va chạm (nhẹ hơn CSG).
- Tên node (Wall_Living_Front, Bed_Her, Safe...) giữ cố định để khi xuất sang Blender
  và nhập lại, có thể gắn lại chức năng theo tên.
"""

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = "res://assets/textures/"
DECAL = "res://assets/textures/decals/"

# Bộ texture CC0 thật (tải bằng tools/fetch_cc0_assets.py): albedo + normal + ORM, kèm kích thước thật.
_CC0_PATH = os.path.join(ROOT, "assets", "textures", "cc0_sets.json")
CC0 = json.load(open(_CC0_PATH)) if os.path.exists(_CC0_PATH) else {}


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


def basis_z(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [c, -s, 0, s, c, 0, 0, 0, 1]


def basis_scale(sx, sy, sz):
    return [sx, 0, 0, 0, sy, 0, 0, 0, sz]


def basis_mul(*ms):
    r = ms[0]
    for b in ms[1:]:
        a = r
        r = []
        for i in range(3):
            for j in range(3):
                r.append(sum(a[i * 3 + k] * b[k * 3 + j] for k in range(3)))
    return r


# Hướng pháp tuyến cho tấm phẳng (QuadMesh nhìn về +Z cục bộ).
FACING = {
    "+z": basis_y(0), "-z": basis_y(180), "+x": basis_y(90), "-x": basis_y(-90),
    "+y": basis_x(-90), "-y": basis_x(90),
}
NORMAL = {"+z": (0, 0, 1), "-z": (0, 0, -1), "+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0)}


def xform(pos=(0, 0, 0), rot_y=0.0, basis=None):
    b = basis if basis is not None else basis_y(rot_y)
    return "Transform3D(%s, %s)" % (", ".join(f(v) for v in b), ", ".join(f(v) for v in pos))


def color(c):
    return "Color(%s, %s, %s, %s)" % (f(c[0]), f(c[1]), f(c[2]), f(c[3] if len(c) > 3 else 1))


def vec3(v):
    return "Vector3(%s, %s, %s)" % tuple(f(x) for x in v)


class Scene:
    def __init__(self, root_name, root_type="Node3D"):
        self.ext = []
        self.ext_ids = {}
        self.sub = []
        self.nodes = []
        self.materials = {}
        self.meshes = {}
        self.names = {}
        self.nodes.append('[node name="%s" type="%s"]\n' % (root_name, root_type))

    # ----- tài nguyên -----
    def ext_res(self, kind, path):
        if path in self.ext_ids:
            return self.ext_ids[path]
        rid = "%d_%s" % (len(self.ext) + 1, os.path.splitext(os.path.basename(path))[0].lower())
        self.ext.append('[ext_resource type="%s" path="%s" id="%s"]' % (kind, path, rid))
        self.ext_ids[path] = rid
        return rid

    def sub_res(self, kind, rid, props):
        lines = ['[sub_resource type="%s" id="%s"]' % (kind, rid)]
        lines += ["%s = %s" % (k, v) for k, v in props]
        self.sub.append("\n".join(lines) + "\n")
        return rid

    def mat(self, name, rgb, roughness=0.85, metallic=0.0, emission=None, energy=1.0, alpha=None,
            unshaded=False, cull=False, billboard=False):
        """Vật liệu màu trơn."""
        if name in self.materials:
            return self.materials[name]
        props = []
        if alpha is not None:
            props.append(("transparency", "1"))
        if cull or alpha is not None:
            props.append(("cull_mode", "2"))
        if unshaded:
            props.append(("shading_mode", "0"))
        if billboard:
            props.append(("billboard_mode", "3"))
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

    def pbr(self, name, tex, tint=(1, 1, 1), tile=1.0, rough=1.0, normal=1.0, metallic=0.0,
            triplanar=True, uv_scale=(1, 1)):
        """Vật liệu PBR dùng bộ texture <tex>_albedo/_normal/_rough.

        triplanar=True: chiếu theo tọa độ thế giới, mỗi ô texture rộng `tile` mét (hợp với CSG).
        """
        if name in self.materials:
            return self.materials[name]
        cc0 = CC0.get(tex)
        a = self.ext_res("Texture2D", TEX + tex + "_albedo.jpg")
        props = [
            ("albedo_color", color(tint)),
            ("albedo_texture", 'ExtResource("%s")' % a),
        ]
        if cc0:
            # Texture thật: trải theo kích thước ngoài đời, AO/roughness/metallic gói trong 1 ảnh ORM.
            tile = cc0["size_m"]
            normal = min(normal, 1.0)  # normal map chụp thật, không cần phóng đại như ảnh sinh thủ tục
            n = self.ext_res("Texture2D", TEX + tex + "_normal.jpg")
            orm = self.ext_res("Texture2D", TEX + tex + "_orm.jpg")
            props += [
                ("orm_texture", 'ExtResource("%s")' % orm),
                ("ao_enabled", "true"), ("ao_light_affect", "0.25"),
                ("metallic", f(1.0 if metallic else 0.0)),
                ("roughness", f(rough)),
            ]
            kind = "ORMMaterial3D"
        else:
            n = self.ext_res("Texture2D", TEX + tex + "_normal.png")
            r = self.ext_res("Texture2D", TEX + tex + "_rough.jpg")
            if metallic:
                props.append(("metallic", f(metallic)))
            props += [
                ("roughness", f(rough)),
                ("roughness_texture", 'ExtResource("%s")' % r),
            ]
            kind = "StandardMaterial3D"
        props += [
            ("normal_enabled", "true"),
            ("normal_scale", f(normal)),
            ("normal_texture", 'ExtResource("%s")' % n),
        ]
        if triplanar:
            k = 1.0 / tile
            props += [("uv1_scale", vec3((k, k, k))), ("uv1_triplanar", "true"),
                      ("uv1_world_triplanar", "true")]
        else:
            props.append(("uv1_scale", vec3((uv_scale[0], uv_scale[1], 1))))
        props.append(("texture_filter", "5"))
        rid = self.sub_res(kind, "Mat_" + name, props)
        self.materials[name] = rid
        return rid

    def decal_mat(self, name, png, tint=(1, 1, 1, 1), opaque=False, emission=None):
        """Vật liệu cho tấm dán (vết ố, ảnh, lịch...): ảnh RGBA trải hết tấm Quad."""
        if name in self.materials:
            return self.materials[name]
        t = self.ext_res("Texture2D", DECAL + png)
        props = []
        if not opaque:
            props += [("transparency", "1"), ("depth_draw_mode", "0")]
        props += [("albedo_color", color(tint)), ("albedo_texture", 'ExtResource("%s")' % t),
                  ("roughness", "0.95"), ("texture_filter", "5")]
        if emission:
            props += [("emission_enabled", "true"), ("emission", color(emission)),
                      ("emission_energy_multiplier", "1"), ("emission_operator", "1"),
                      ("emission_texture", 'ExtResource("%s")' % t)]
        rid = self.sub_res("StandardMaterial3D", "Mat_" + name, props)
        self.materials[name] = rid
        return rid

    def mesh_res(self, kind, dims):
        key = (kind, tuple(round(d, 4) for d in dims))
        if key in self.meshes:
            return self.meshes[key]
        rid = "Mesh_%d" % (len(self.meshes) + 1)
        if kind == "box":
            props = [("size", vec3(dims))]
        elif kind == "cyl":
            props = [("top_radius", f(dims[0])), ("bottom_radius", f(dims[1])), ("height", f(dims[2])),
                     ("radial_segments", str(int(dims[3]) if len(dims) > 3 else 20)), ("rings", "1")]
            if len(dims) > 4 and not dims[4]:
                props += [("cap_top", "false"), ("cap_bottom", "false")]
        elif kind == "sphere":
            props = [("radius", f(dims[0])), ("height", f(dims[1])), ("radial_segments", "20"), ("rings", "10")]
        elif kind == "torus":
            props = [("inner_radius", f(dims[0])), ("outer_radius", f(dims[1])), ("rings", "32"),
                     ("ring_segments", "8")]
        elif kind == "quad":
            props = [("size", "Vector2(%s, %s)" % (f(dims[0]), f(dims[1])))]
        elif kind == "prism":
            props = [("left_to_right", f(dims[3]) if len(dims) > 3 else "0.5"), ("size", vec3(dims[:3]))]
        else:
            raise ValueError(kind)
        cls = {"box": "BoxMesh", "cyl": "CylinderMesh", "sphere": "SphereMesh", "torus": "TorusMesh",
               "quad": "QuadMesh", "prism": "PrismMesh"}[kind]
        self.sub_res(cls, rid, props)
        self.meshes[key] = rid
        return rid

    # ----- node -----
    def uniq(self, parent, name):
        key = (parent, name)
        if key not in self.names:
            self.names[key] = 1
            return name
        self.names[key] += 1
        return "%s%d" % (name, self.names[key])

    def node(self, name, kind, parent=".", props=(), extra_header=""):
        name = self.uniq(parent, name)
        head = '[node name="%s" type="%s" parent="%s"%s]' % (name, kind, parent, extra_header)
        body = "".join("%s = %s\n" % (k, v) for k, v in props)
        self.nodes.append(head + "\n" + body)
        return name if parent == "." else parent + "/" + name

    def instance(self, name, rid, parent=".", props=()):
        head = '[node name="%s" parent="%s" instance=ExtResource("%s")]' % (name, parent, rid)
        body = "".join("%s = %s\n" % (k, v) for k, v in props)
        self.nodes.append(head + "\n" + body)

    def group(self, name, parent=".", pos=(0, 0, 0), rot_y=0.0, collision=True, basis=None):
        props = [("transform", xform(pos, rot_y, basis))]
        if collision:
            props.append(("use_collision", "true"))
        return self.node(name, "CSGCombiner3D", parent, props)

    def empty(self, name, parent=".", pos=(0, 0, 0), rot_y=0.0, basis=None, props=()):
        return self.node(name, "Node3D", parent, [("transform", xform(pos, rot_y, basis))] + list(props))

    def box(self, name, parent, center, size, mat, rot_y=0.0, subtract=False, basis=None):
        props = [("transform", xform(center, rot_y, basis))]
        if subtract:
            props.append(("operation", "2"))
        props.append(("size", vec3(size)))
        if mat:
            props.append(("material", 'SubResource("%s")' % mat))
        return self.node(name, "CSGBox3D", parent, props)

    def cyl(self, name, parent, center, radius, height, mat, sides=16, basis=None, subtract=False):
        props = [("transform", xform(center, basis=basis))]
        if subtract:
            props.append(("operation", "2"))
        props += [("radius", f(radius)), ("height", f(height)), ("sides", str(sides)),
                  ("material", 'SubResource("%s")' % mat)]
        return self.node(name, "CSGCylinder3D", parent, props)

    def sphere(self, name, parent, center, radius, mat):
        props = [("transform", xform(center)), ("radius", f(radius)),
                 ("material", 'SubResource("%s")' % mat)]
        return self.node(name, "CSGSphere3D", parent, props)

    def mesh(self, name, parent, kind, dims, pos, mat, rot_y=0.0, basis=None, shadow=True, extra=()):
        """Mesh trang trí không va chạm."""
        props = [("transform", xform(pos, rot_y, basis))]
        if not shadow:
            props.append(("cast_shadow", "0"))
        props.append(("mesh", 'SubResource("%s")' % self.mesh_res(kind, dims)))
        if mat:
            props.append(("material_override", 'SubResource("%s")' % mat))
        props += list(extra)
        return self.node(name, "MeshInstance3D", parent, props)

    def model(self, name, parent, asset, pos, rot_y=0.0, scale=1.0):
        """Model CC0 (glTF trong assets/models/<asset>/), chỉ để nhìn, không va chạm."""
        rid = self.ext_res("PackedScene", "res://assets/models/%s/%s.gltf" % (asset, asset))
        b = basis_mul(basis_y(rot_y), basis_scale(scale, scale, scale))
        self.nodes.append('[node name="%s" parent="%s" instance=ExtResource("%s")]\ntransform = %s\n'
                          % (self.uniq(parent, name), parent, rid, xform(pos, basis=b)))

    def decal(self, name, parent, pos, facing, size, mat, roll=0.0, offset=0.006):
        """Tấm dán phẳng sát bề mặt. `facing` là hướng pháp tuyến của bề mặt (vd '+z')."""
        n = NORMAL[facing]
        p = (pos[0] + n[0] * offset, pos[1] + n[1] * offset, pos[2] + n[2] * offset)
        b = basis_mul(FACING[facing], basis_z(roll))
        return self.mesh(name, parent, "quad", size, p, mat, basis=b, shadow=False)

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
        print("wrote", path, "(%d nodes)" % len(self.nodes))


# ---------------------------------------------------------------------------
# Đồ nội thất dựng sẵn. Hệ tọa độ cục bộ: mặt trước của đồ quay về +Z.
# ---------------------------------------------------------------------------

def legs(sc, g, w, d, h, m, t=0.05, inset=0.03, turned=False):
    for i, (sx, sz) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
        p = (sx * (w / 2 - t / 2 - inset), h / 2, sz * (d / 2 - t / 2 - inset))
        if turned:
            sc.cyl("Leg%d" % (i + 1), g, p, t / 2, h, m, sides=10)
        else:
            sc.box("Leg%d" % (i + 1), g, p, (t, h, t), m)


def bed(sc, name, parent, pos, rot, w, l, frame, linen, blanket, pillow, headboard_h=1.0, posts=False,
        old=False):
    g = sc.group(name, parent, pos, rot)
    if old:
        # Giường gỗ kiểu cũ: phản dày, chân tiện, chiếu trải thẳng lên ván.
        sc.box("Base", g, (0, 0.38, 0), (w, 0.08, l), frame)
        sc.box("RailL", g, (-w / 2 + 0.03, 0.3, 0), (0.06, 0.12, l), frame)
        sc.box("RailR", g, (w / 2 - 0.03, 0.3, 0), (0.06, 0.12, l), frame)
        legs(sc, g, w, l, 0.34, frame, t=0.09, inset=0, turned=True)
        sc.box("Mattress", g, (0, 0.43, 0), (w - 0.04, 0.02, l - 0.04), linen)
    else:
        sc.box("Base", g, (0, 0.27, 0), (w, 0.24, l), frame)
        legs(sc, g, w, l, 0.15, frame, t=0.08, inset=0)
        sc.box("Mattress", g, (0, 0.47, 0.02), (w - 0.08, 0.16, l - 0.1), linen)
    top = 0.44 if old else 0.55
    sc.box("Blanket", g, (0, top + 0.02, 0.35), (w - 0.06, 0.05, l * 0.55), blanket)
    sc.box("BlanketFold", g, (0, top + 0.05, 0.35 - l * 0.275 + 0.08), (w - 0.06, 0.06, 0.16), blanket)
    sc.box("Headboard", g, (0, headboard_h / 2, -l / 2 + 0.04), (w + 0.04, headboard_h, 0.08), frame)
    sc.box("Footboard", g, (0, 0.3 if not old else 0.32, l / 2 - 0.03), (w + 0.04, 0.6 if not old else 0.64, 0.06), frame)
    n = 2 if w > 1.3 else 1
    for i in range(n):
        x = 0 if n == 1 else (-1 + 2 * i) * w / 4
        sc.box("Pillow%d" % (i + 1), g, (x, top + 0.06, -l / 2 + 0.3), (w / n - 0.18, 0.11, 0.36), pillow)
    if posts:
        # Cọc màn (khung mắc màn) kiểu giường gỗ cũ.
        for i, (sx, sz) in enumerate([(-1, -1), (1, -1), (-1, 1), (1, 1)]):
            sc.box("NetPost%d" % (i + 1), g, (sx * (w / 2 + 0.02), 0.95, sz * (l / 2 - 0.03)),
                   (0.045, 1.9, 0.045), frame)
        sc.box("NetRailL", g, (-w / 2 - 0.02, 1.88, 0), (0.035, 0.035, l), frame)
        sc.box("NetRailR", g, (w / 2 + 0.02, 1.88, 0), (0.035, 0.035, l), frame)
        sc.box("NetRailHead", g, (0, 1.88, -l / 2 + 0.03), (w + 0.08, 0.035, 0.035), frame)
        sc.box("NetRailFoot", g, (0, 1.88, l / 2 - 0.03), (w + 0.08, 0.035, 0.035), frame)
    return g


def wardrobe(sc, name, parent, pos, rot, w, h, d, body, trim, doors=2, ajar=None, dark=None, handle=None,
             mirror=None):
    """Tủ quần áo có khoang rỗng bên trong; cánh `ajar` (chỉ số) hé mở `ajar_deg` độ."""
    g = sc.group(name, parent, pos, rot)
    sc.box("Body", g, (0, h / 2 + 0.05, 0), (w, h - 0.1, d), body)
    if dark:
        sc.box("Cavity", g, (0, h / 2 + 0.05, 0.03), (w - 0.05, h - 0.2, d - 0.02), dark, subtract=True)
    sc.box("Plinth", g, (0, 0.03, -0.02), (w - 0.06, 0.06, d - 0.06), trim)
    sc.box("Crown", g, (0, h - 0.02, 0.01), (w + 0.05, 0.05, d + 0.05), trim)
    dw = w / doors
    hm = handle or trim
    for i in range(doors):
        x0 = -w / 2 + dw * i
        left_hinge = i < doors / 2
        hinge_x = x0 if left_hinge else x0 + dw
        deg = 0
        if ajar is not None and ajar[0] == i:
            deg = -ajar[1] * (1 if left_hinge else -1)
        leaf = sc.group("Door%d" % (i + 1), g, (hinge_x, 0, d / 2), deg, collision=False) \
            if deg else sc.empty("Door%d" % (i + 1), g, (hinge_x, 0, d / 2))
        cx = dw / 2 - 0.004 if left_hinge else -dw / 2 + 0.004
        sgn = 1 if left_hinge else -1
        if deg:
            sc.box("Leaf", leaf, (cx, h / 2 + 0.05, 0.01), (dw - 0.008, h - 0.12, 0.02), body)
            sc.box("Panel", leaf, (cx, h / 2 + 0.05, 0.022), (dw - 0.12, h - 0.4, 0.008), trim)
            sc.box("Handle", leaf, (cx + sgn * (dw / 2 - 0.07), h * 0.52, 0.04), (0.02, 0.16, 0.025), hm)
        else:
            sc.mesh("Leaf", leaf, "box", (dw - 0.008, h - 0.12, 0.02), (cx, h / 2 + 0.05, 0.01), body)
            sc.mesh("Panel", leaf, "box", (dw - 0.12, h - 0.4, 0.008), (cx, h / 2 + 0.05, 0.022), trim)
            if mirror and i == doors // 2:
                sc.mesh("Mirror", leaf, "box", (dw - 0.2, h - 0.6, 0.006), (cx, h / 2 + 0.05, 0.03), mirror)
            sc.mesh("Handle", leaf, "box", (0.02, 0.16, 0.025), (cx + sgn * (dw / 2 - 0.07), h * 0.52, 0.04), hm)
    return g


def chest_of_drawers(sc, name, parent, pos, rot, w, h, d, body, front, drawers=4, knob=None):
    g = sc.group(name, parent, pos, rot)
    sc.box("Body", g, (0, h / 2 + 0.04, 0), (w, h - 0.08, d), body)
    sc.box("Top", g, (0, h + 0.01, 0.005), (w + 0.03, 0.025, d + 0.02), body)
    legs(sc, g, w, d, 0.08, body, t=0.05, inset=0.01)
    dh = (h - 0.14) / drawers
    for i in range(drawers):
        y = 0.1 + dh * (i + 0.5)
        sc.mesh("Drawer%d" % (i + 1), g, "box", (w - 0.06, dh - 0.025, 0.018), (0, y, d / 2 + 0.009), front)
        sc.mesh("Knob%d" % (i + 1), g, "cyl", (0.018, 0.018, 0.025, 10), (0, y, d / 2 + 0.03), knob or body,
                basis=basis_x(90))
    return g


def desk(sc, name, parent, pos, rot, w, d, wood, front, drawer_side=1, knob=None):
    g = sc.group(name, parent, pos, rot)
    sc.box("Top", g, (0, 0.735, 0), (w, 0.03, d), wood)
    x = drawer_side * (w / 2 - 0.22)
    sc.box("DrawerBlock", g, (x, 0.36, 0), (0.42, 0.72, d - 0.04), wood)
    for i in range(3):
        y = 0.13 + i * 0.22
        sc.mesh("Drawer%d" % (i + 1), g, "box", (0.38, 0.18, 0.015), (x, y, d / 2 - 0.012), front)
        sc.mesh("Pull%d" % (i + 1), g, "box", (0.08, 0.015, 0.02), (x, y + 0.04, d / 2 + 0.005), knob or wood)
    lx = -drawer_side * (w / 2 - 0.04)
    sc.box("LegFront", g, (lx, 0.36, d / 2 - 0.05), (0.05, 0.72, 0.05), wood)
    sc.box("LegBack", g, (lx, 0.36, -d / 2 + 0.05), (0.05, 0.72, 0.05), wood)
    sc.box("ModestyPanel", g, (0, 0.5, -d / 2 + 0.02), (w - 0.1, 0.4, 0.02), wood)
    return g


def chair(sc, name, parent, pos, rot, wood, seat_h=0.45, w=0.44, back=True, cushion=None, old=False):
    g = sc.group(name, parent, pos, rot)
    sc.box("Seat", g, (0, seat_h - 0.02, 0), (w, 0.04, w), wood)
    legs(sc, g, w, w, seat_h - 0.04, wood, t=0.04, inset=0.0)
    if old:
        # Ghế gỗ kiểu cũ: giằng chân và tựa song.
        sc.box("StretcherF", g, (0, 0.12, w / 2 - 0.02), (w - 0.04, 0.025, 0.02), wood)
        sc.box("StretcherL", g, (-w / 2 + 0.02, 0.15, 0), (0.02, 0.025, w - 0.04), wood)
        sc.box("StretcherR", g, (w / 2 - 0.02, 0.15, 0), (0.02, 0.025, w - 0.04), wood)
    if back:
        if old:
            for sx in (-1, 1):
                sc.box("BackPost", g, (sx * (w / 2 - 0.02), seat_h + 0.25, -w / 2 + 0.02), (0.04, 0.5, 0.04), wood)
            sc.box("BackTop", g, (0, seat_h + 0.47, -w / 2 + 0.02), (w, 0.07, 0.035), wood)
            for k in range(3):
                sc.box("Slat", g, (-0.1 + k * 0.1, seat_h + 0.22, -w / 2 + 0.02), (0.03, 0.4, 0.02), wood)
        else:
            sc.box("Back", g, (0, seat_h + 0.25, -w / 2 + 0.02), (w, 0.45, 0.03), wood)
    if cushion:
        sc.mesh("Cushion", g, "box", (w - 0.04, 0.05, w - 0.04), (0, seat_h + 0.025, 0.01), cushion)
    return g


def table(sc, name, parent, pos, rot, w, d, h, wood, t=0.05, apron=True, turned=False):
    g = sc.group(name, parent, pos, rot)
    sc.box("Top", g, (0, h - 0.02, 0), (w, 0.04, d), wood)
    if apron and h > 0.3:
        sc.box("ApronF", g, (0, h - 0.08, d / 2 - 0.06), (w - 0.14, 0.08, 0.02), wood)
        sc.box("ApronB", g, (0, h - 0.08, -d / 2 + 0.06), (w - 0.14, 0.08, 0.02), wood)
    legs(sc, g, w, d, h - 0.04, wood, t=t, turned=turned)
    return g


def bulb(sc, name, parent, pos, light_color, energy, rng, glass, cord, cord_len=0.5, shadow=True,
         shade=None, flicker=None, sway=None, socket=None):
    """Bóng đèn treo: điểm treo (có thể đung đưa) > OmniLight3D > dây + đui + bóng.

    flicker: dict tham số cho LightFlicker.gd; sway: dict tham số cho Sway.gd.
    """
    top = (pos[0], pos[1] + cord_len + 0.05, pos[2])
    pprops = []
    if sway is not None:
        pprops = [("script", 'ExtResource("%s")' % sc.ext_res("Script", "res://scripts/levels/Sway.gd"))]
        pprops += list(sway.items())
    pivot = sc.empty(name + "_Pivot", parent, top, props=pprops)
    lprops = [
        ("transform", xform((0, -(cord_len + 0.05), 0))),
        ("light_color", color(light_color)),
        ("light_energy", f(energy)),
        ("shadow_enabled", "true" if shadow else "false"),
        ("omni_range", f(rng)),
        ("omni_attenuation", "1.4"),
    ]
    if shadow:
        lprops.append(("shadow_blur", "1.5"))
    if flicker is not None:
        lprops.append(("script", 'ExtResource("%s")' % sc.ext_res("Script", "res://scripts/levels/LightFlicker.gd")))
        lprops.append(("emissive_mesh", 'NodePath("Fixture/Bulb")'))
        lprops += list(flicker.items())
    lp = sc.node(name, "OmniLight3D", pivot, lprops)
    g = sc.empty("Fixture", lp)
    sc.mesh("Cord", g, "cyl", (0.004, 0.004, cord_len, 6), (0, cord_len / 2 + 0.08, 0), cord, shadow=False)
    sc.mesh("Socket", g, "cyl", (0.018, 0.022, 0.06, 10), (0, 0.07, 0), socket or cord, shadow=False)
    sc.mesh("Bulb", g, "sphere", (0.035, 0.075), (0, 0.01, 0), glass, shadow=False)
    if shade:
        sc.mesh("Shade", g, "cyl", (0.03, 0.16, 0.1, 16, False), (0, 0.07, 0), shade, shadow=True)
    return lp


def player(sc, rid, pos, rot_y):
    sc.instance("Player", rid, props=[("transform", xform(pos, rot_y))])


def environment(sc, rid, top, horizon, ground_horizon, ground_bottom, ambient, ambient_energy,
                sky_energy=1.0, fog_color=None, fog_density=0.0, exposure=1.0, extra=()):
    sc.sub_res("ProceduralSkyMaterial", "SkyMat_" + rid, [
        ("sky_top_color", color(top)), ("sky_horizon_color", color(horizon)),
        ("ground_bottom_color", color(ground_bottom)), ("ground_horizon_color", color(ground_horizon)),
        ("sky_energy_multiplier", f(sky_energy)),
    ])
    sc.sub_res("Sky", "Sky_" + rid, [("sky_material", 'SubResource("SkyMat_%s")' % rid)])
    props = [
        ("background_mode", "2"), ("sky", 'SubResource("Sky_%s")' % rid),
        ("ambient_light_source", "3"), ("ambient_light_color", color(ambient)),
        ("ambient_light_sky_contribution", "0.3"), ("ambient_light_energy", f(ambient_energy)),
        ("tonemap_mode", "3"), ("tonemap_exposure", f(exposure)),
        ("ssao_enabled", "true"), ("ssao_radius", "1.2"), ("ssao_intensity", "2.5"),
        ("glow_enabled", "true"), ("glow_intensity", "0.6"), ("glow_bloom", "0.05"),
    ]
    if fog_color:
        props += [("fog_enabled", "true"), ("fog_light_color", color(fog_color)), ("fog_density", f(fog_density))]
    props += list(extra)
    sc.sub_res("Environment", "Env_" + rid, props)
    sc.node("WorldEnvironment", "WorldEnvironment", ".", [("environment", 'SubResource("Env_%s")' % rid)])


def sun(sc, name, direction, light_color, energy, extra=()):
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
    ] + list(extra))


def dust(sc, name, parent, center, extents, amount=60, col=(1, 0.95, 0.85, 0.35), size=0.012):
    """Bụi lơ lửng (bắt sáng ở luồng nắng / dưới bóng đèn)."""
    m = sc.mat("DustMote%d" % len(sc.materials), col[:3], 1.0, alpha=col[3] * 0.7, unshaded=True, billboard=True)
    # Hạt tròn nhỏ thay vì tấm vuông: ở gần không còn lộ thành ô vuông trắng.
    q = sc.mesh_res("sphere", (size * 0.3, size * 0.6))
    sc.node(name, "CPUParticles3D", parent, [
        ("transform", xform(center)),
        ("amount", str(amount)), ("lifetime", "12.0"), ("preprocess", "12.0"),
        ("mesh", 'SubResource("%s")' % q), ("material_override", 'SubResource("%s")' % m),
        ("cast_shadow", "0"),
        ("emission_shape", "3"), ("emission_box_extents", vec3(extents)),
        ("direction", "Vector3(0, 1, 0)"), ("spread", "180.0"), ("gravity", "Vector3(0, -0.004, 0)"),
        ("initial_velocity_min", "0.005"), ("initial_velocity_max", "0.03"),
        ("particle_flag_align_y", "false"),
    ])


def window_bars(sc, parent, name, center, width, height, along_x, mat, n=6):
    g = sc.group(name, parent, collision=False)
    for i in range(n):
        o = -width / 2 + width * (i + 1) / (n + 1)
        p = (center[0] + (o if along_x else 0), center[1], center[2] + (0 if along_x else o))
        sc.cyl("Bar%d" % (i + 1), g, p, 0.009, height, mat, sides=8)


def window_frame(sc, parent, name, center, width, height, depth, along_x, mat, sill=None, mullion=True,
                 glass=None):
    """Khung cửa sổ gỗ ôm sát lỗ khoét trên tường."""
    g = sc.empty(name, parent, center, 0 if along_x else 90)
    t = 0.06
    sc.mesh("Top", g, "box", (width + 2 * t, t, depth), (0, height / 2 + t / 2, 0), mat)
    sc.mesh("Bottom", g, "box", (width + 2 * t, t, depth), (0, -height / 2 - t / 2, 0), mat)
    sc.mesh("Left", g, "box", (t, height, depth), (-width / 2 - t / 2, 0, 0), mat)
    sc.mesh("Right", g, "box", (t, height, depth), (width / 2 + t / 2, 0, 0), mat)
    if mullion:
        sc.mesh("Mullion", g, "box", (0.04, height, 0.05), (0, 0, 0), mat)
        sc.mesh("Transom", g, "box", (width, 0.04, 0.05), (0, height * 0.18, 0), mat)
    if glass:
        sc.mesh("Glass", g, "box", (width, height, 0.008), (0, 0, 0), glass, shadow=False)
    if sill:
        sc.mesh("Sill", g, "box", (width + 0.25, 0.035, depth + 0.12), (0, -height / 2 - t - 0.017, 0), sill)
    return g


# ---------------------------------------------------------------------------
# 1. Phòng ngủ trong mơ: sáng sủa, hiện đại, gọn gàng. Kinh dị chỉ thoáng qua:
#    đồng hồ đứng ở 12 giờ (giờ Ngọ), bình cúc trắng, dấu chân ướt trẻ con từ
#    cửa sổ tới tủ, cánh tủ hé mở để lộ khoang tối, bóng người nhỏ trong tranh.
# ---------------------------------------------------------------------------

def build_dream_bedroom():
    sc = Scene("DreamBedroom")
    p_rid = sc.ext_res("PackedScene", "res://scenes/player/Player.tscn")
    i_rid = sc.ext_res("Script", "res://scripts/interaction/Interactable.gd")

    wall = sc.pbr("WallPlaster", "plaster_white", (1, 1, 1), tile=1.5, normal=0.6)
    floor = sc.pbr("FloorOak", "oak_floor", (1, 1, 1), tile=1.6, normal=0.8)
    ceil = sc.pbr("Ceiling", "plaster_white", (1.03, 1.03, 1.03), tile=1.5, normal=0.3)
    trim = sc.mat("Trim", (0.95, 0.94, 0.92), 0.45)
    grass = sc.pbr("Grass", "grass", (1, 1, 1), tile=2.0)
    linen = sc.pbr("Linen", "fabric", (0.97, 0.96, 0.94), tile=0.35, normal=0.5)
    duvet = sc.pbr("Duvet", "fabric", (0.86, 0.89, 0.92), tile=0.4, normal=0.7)
    throw = sc.pbr("Throw", "fabric", (0.55, 0.62, 0.7), tile=0.15, normal=1.2)
    head = sc.pbr("Upholstery", "fabric", (0.68, 0.66, 0.62), tile=0.12, normal=1.5)
    sage = sc.pbr("Sage", "fabric", (0.62, 0.68, 0.6), tile=0.15, normal=1.4)
    wood_light = sc.pbr("WoodLight", "oak_floor", (1.08, 1.06, 1.02), tile=2.4, normal=0.4)
    wood_front = sc.mat("WoodFront", (0.93, 0.9, 0.84), 0.5)
    # Két sắt sơn tĩnh điện đen (giấc mơ sạch sẽ, không gỉ sét).
    metal_dark = sc.mat("SafeSteel", (0.07, 0.075, 0.08), 0.38, metallic=0.6)
    brass = sc.mat("Brass", (0.85, 0.68, 0.38), 0.28, metallic=0.95)
    curtain = sc.mat("Curtain", (0.99, 0.97, 0.93), 0.95, alpha=0.55)
    drape = sc.pbr("Drape", "fabric", (0.86, 0.8, 0.7), tile=0.25, normal=1.0)
    rug = sc.pbr("Rug", "rug_dream", (1, 1, 1), triplanar=False)
    lampshade = sc.mat("LampShade", (1, 0.96, 0.88), 0.9, emission=(1, 0.86, 0.62), energy=0.5)
    glass = sc.mat("BulbWarm", (1, 0.92, 0.75), 0.2, emission=(1, 0.88, 0.65), energy=2.5)
    window_glass = sc.mat("WindowGlass", (0.85, 0.92, 0.95), 0.03, alpha=0.12, metallic=0.2)
    leaf = sc.mat("Leaf", (0.2, 0.42, 0.18), 0.6, cull=True)
    stem = sc.mat("Stem", (0.3, 0.38, 0.18), 0.8)
    pot = sc.mat("Pot", (0.88, 0.85, 0.8), 0.45)
    terracotta = sc.mat("PotTerracotta", (0.66, 0.38, 0.26), 0.85)
    mirror = sc.mat("Mirror", (0.85, 0.88, 0.9), 0.02, metallic=1.0)
    dark = sc.mat("WardrobeDark", (0.015, 0.012, 0.01), 1.0)
    book_cols = [sc.mat("Book%d" % i, c, 0.8) for i, c in enumerate(
        [(0.62, 0.2, 0.18), (0.2, 0.32, 0.45), (0.85, 0.8, 0.68), (0.3, 0.42, 0.3), (0.15, 0.15, 0.17)])]
    paper = sc.mat("Paper", (0.96, 0.95, 0.92), 0.9)
    water = sc.mat("GlassWater", (0.8, 0.9, 0.95), 0.05, alpha=0.3)
    white_flower = sc.mat("Chrysanthemum", (0.96, 0.95, 0.9), 0.9)
    flower_core = sc.mat("FlowerCore", (0.85, 0.75, 0.3), 0.9)
    tree_bark = sc.pbr("Bark", "wood_weathered", (0.7, 0.62, 0.55), tile=0.6)
    foliage = sc.mat("Foliage", (0.22, 0.4, 0.17), 0.9)
    hedge = sc.mat("Hedge", (0.18, 0.34, 0.14), 0.95)
    fence_white = sc.mat("FenceWhite", (0.92, 0.92, 0.9), 0.6)
    ceramic = sc.mat("Ceramic", (0.95, 0.94, 0.92), 0.2)
    clock_m = sc.decal_mat("ClockFace", "clock_face.png", opaque=False)
    painting = sc.decal_mat("Painting", "painting.png", opaque=True)
    drawing = sc.decal_mat("ChildDrawing", "child_drawing.png", opaque=True)
    footprint = sc.decal_mat("Footprint", "footprint.png")
    photo = sc.decal_mat("PhotoSmall", "family_photo.png", tint=(1.1, 1.08, 1.05, 1), opaque=True)

    environment(sc, "day", (0.32, 0.52, 0.85), (0.78, 0.86, 0.95), (0.6, 0.65, 0.6), (0.2, 0.25, 0.2),
                (0.95, 0.96, 1.0), 0.75, sky_energy=1.1, exposure=1.2, extra=[
                    ("sdfgi_enabled", "true"), ("sdfgi_use_occlusion", "true"), ("sdfgi_energy", "1.2"),
                    ("ssil_enabled", "true"),
                    ("volumetric_fog_enabled", "true"), ("volumetric_fog_density", "0.012"),
                    ("volumetric_fog_albedo", color((1, 0.98, 0.95))), ("volumetric_fog_anisotropy", "0.6"),
                    ("adjustment_enabled", "true"), ("adjustment_contrast", "1.04"),
                    ("adjustment_saturation", "1.05"),
                ])
    sun(sc, "Sun", (-0.35, -0.6, -0.72), (1, 0.95, 0.86), 2.2, extra=[("light_volumetric_fog_energy", "1.5")])

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
        sc.box("Window_Front%d" % (i + 1), s, (x, 1.45, hz + T / 2), (1.5, 1.7, T + 0.2), wall, subtract=True)

    deco = sc.empty("Decor")
    # Phào chỉ chân tường và trần.
    for nme, c, sz in (("Back", (0, 0.06, -hz + 0.01), (W, 0.12, 0.02)),
                       ("Front", (0, 0.06, hz - 0.01), (W, 0.12, 0.02)),
                       ("West", (-hx + 0.01, 0.06, 0), (0.02, 0.12, D)),
                       ("East", (hx - 0.01, 0.06, 0), (0.02, 0.12, D))):
        sc.mesh("Skirting_" + nme, deco, "box", sz, c, trim)
        cc = (c[0], H - 0.05, c[2])
        csz = (sz[0] + (0.06 if sz[0] < 0.1 else 0), 0.1, sz[2] + (0.06 if sz[2] < 0.1 else 0))
        sc.mesh("Cornice_" + nme, deco, "box", csz, cc, trim)
    sc.mesh("Rug", deco, "quad", (3.0, 2.6), (0, 0.004, -1.0), rug, basis=FACING["+y"], shadow=False)

    # Tranh lớn trên đầu giường (có một bóng người rất nhỏ đứng bên bờ sông).
    sc.mesh("ArtFrame", deco, "box", (1.24, 0.84, 0.04), (0, 1.98, -hz + 0.02), wood_light)
    sc.decal("ArtCanvas", deco, (0, 1.98, -hz + 0.04), "+z", (1.12, 0.72), painting, offset=0.002)
    # Đồng hồ treo trên cửa, dừng ở 12 giờ.
    sc.mesh("Clock_Body", deco, "cyl", (0.17, 0.17, 0.04, 32), (hx - 0.02, 2.55, 1.4), trim,
            basis=basis_z(90))
    sc.decal("Clock_Face", deco, (hx - 0.04, 2.55, 1.4), "-x", (0.32, 0.32), clock_m, offset=0.003)

    for i, x in enumerate((-1.3, 1.3)):
        window_frame(sc, deco, "WindowFrame%d" % (i + 1), (x, 1.45, hz + 0.1), 1.5, 1.7, 0.2, True, trim,
                     sill=trim, glass=window_glass)
        sc.mesh("CurtainRod%d" % (i + 1), deco, "cyl", (0.014, 0.014, 2.5, 10), (x, 2.55, hz - 0.12), brass,
                basis=basis_z(90))
        for sx in (-1, 1):
            sc.mesh("RodFinial%d" % (i + 1), deco, "sphere", (0.03, 0.06), (x + sx * 1.26, 2.55, hz - 0.12), brass)
            # Rèm dày hai bên: nhiều nếp xếp.
            for k in range(5):
                px = x + sx * (0.82 + k * 0.08)
                pz = hz - 0.12 + (0.025 if k % 2 else -0.02)
                sc.mesh("Drape%d" % (i + 1), deco, "box", (0.09, 2.45, 0.03), (px, 1.3, pz), drape)
        # Rèm voan mỏng che nửa dưới cửa sổ, ánh nắng lọt qua.
        for k in range(10):
            px = x - 0.7 + k * 0.155
            pz = hz - 0.08 + (0.015 if k % 2 else -0.012)
            sc.mesh("Sheer%d" % (i + 1), deco, "box", (0.16, 2.4, 0.006), (px, 1.32, pz), curtain, shadow=False)

    # Cửa ra vào (đóng) trên tường đông, có khuôn.
    door = sc.empty("Door", deco, (hx - 0.02, 0, 1.4), -90)
    sc.mesh("Frame_L", door, "box", (0.07, 2.18, 0.04), (-0.5, 1.09, 0.0), trim)
    sc.mesh("Frame_R", door, "box", (0.07, 2.18, 0.04), (0.5, 1.09, 0.0), trim)
    sc.mesh("Frame_T", door, "box", (1.07, 0.07, 0.04), (0, 2.16, 0.0), trim)
    sc.mesh("Leaf", door, "box", (0.92, 2.1, 0.04), (0, 1.05, -0.01), wood_front)
    for k, y in enumerate((0.55, 1.55)):
        sc.mesh("Panel%d" % (k + 1), door, "box", (0.66, 0.75, 0.012), (0, y, 0.014), trim)
    sc.mesh("Handle", door, "box", (0.14, 0.022, 0.05), (0.33, 1.0, 0.045), brass)
    sc.mesh("Rose", door, "cyl", (0.03, 0.03, 0.02, 12), (0.38, 1.0, 0.025), brass, basis=basis_x(90))
    sc.mesh("Switch", deco, "box", (0.012, 0.12, 0.08), (hx - 0.006, 1.2, 0.75), trim)

    # Giường king: đầu giường bọc nệm cao, chần nút.
    bed(sc, "Bed_King", ".", (0, 0, -1.4), 0, 1.9, 2.1, wood_light, linen, duvet, linen, headboard_h=1.3)
    sc.box("HeadboardPanel", "Bed_King", (0, 0.9, -0.99), (1.96, 0.82, 0.08), head)
    for r in range(3):
        for cidx in range(7):
            sc.mesh("Tuft", "Bed_King", "sphere", (0.012, 0.012), (-0.81 + cidx * 0.27, 0.65 + r * 0.25, -0.948),
                    brass, shadow=False)
    sc.mesh("Throw", "Bed_King", "box", (1.96, 0.035, 0.5), (0, 0.63, 0.62), throw)
    sc.mesh("ThrowDrop", "Bed_King", "box", (1.96, 0.3, 0.03), (0, 0.48, 0.865), throw)
    for k, x in enumerate((-0.42, 0.42)):
        sc.mesh("Cushion", "Bed_King", "box", (0.42, 0.3, 0.1), (x, 0.74, -0.68), sage,
                basis=basis_x(-15))
    bench = sc.group("Bench_Foot", ".", (0, 0, 0.0))
    sc.box("BenchTop", bench, (0, 0.42, 0), (1.4, 0.07, 0.42), head)
    legs(sc, bench, 1.4, 0.42, 0.39, wood_light, t=0.04)
    sc.mesh("Book", bench, "box", (0.17, 0.035, 0.24), (0.4, 0.475, 0.02), book_cols[1], rot_y=12)
    for i, x in enumerate((-1.35, 1.35)):
        n = "Nightstand%d" % (i + 1)
        chest_of_drawers(sc, n, ".", (x, 0, -2.22), 0, 0.5, 0.55, 0.4, wood_light, wood_front, drawers=2,
                         knob=brass)
        lamp = sc.node("Lamp", "OmniLight3D", n, [
            ("transform", xform((-0.08 * (1 if i else -1), 0.9, -0.05))), ("light_color", color((1, 0.84, 0.62))),
            ("light_energy", "0.4"), ("omni_range", "2.5"), ("shadow_enabled", "false")])
        sc.mesh("Base", lamp, "cyl", (0.04, 0.07, 0.3, 16), (0, -0.18, 0), ceramic)
        sc.mesh("Shade", lamp, "cyl", (0.1, 0.15, 0.2, 24, False), (0, 0.02, 0), lampshade)
        sc.mesh("Bulb", lamp, "sphere", (0.03, 0.06), (0, 0, 0), glass, shadow=False)
    # Đồ trên tab đầu giường.
    sc.mesh("Clock_Alarm", "Nightstand2", "box", (0.12, 0.08, 0.05), (0.12, 0.6, 0.08), trim, rot_y=-20)
    sc.decal("Clock_AlarmFace", "Nightstand2", (0.12 + 0.025 * math.sin(math.radians(-20)), 0.6,
             0.08 + 0.025 * math.cos(math.radians(-20))), "+z", (0.06, 0.06), clock_m, roll=0, offset=0.001)
    sc.mesh("WaterGlass", "Nightstand1", "cyl", (0.033, 0.03, 0.11, 16), (0.13, 0.62, 0.06), water, shadow=False)
    for k in range(3):
        sc.mesh("Book%d" % (k + 1), "Nightstand1", "box", (0.15, 0.03, 0.22),
                (0.0 - 0.1, 0.58 + k * 0.032, 0.05), book_cols[k], rot_y=(k * 9 - 6))
    sc.mesh("PhotoFrame", "Nightstand2", "box", (0.12, 0.16, 0.015), (-0.13, 0.66, -0.05), wood_light)
    sc.decal("Photo", "Nightstand2", (-0.13, 0.66, -0.0425), "+z", (0.1, 0.13), photo, offset=0.002)

    # Tủ quần áo 3 cánh: cánh giữa hé mở, bên trong tối đen.
    wardrobe(sc, "Wardrobe", ".", (-hx + 0.31, 0, 0.7), 90, 2.2, 2.3, 0.6, wood_light, wood_front, doors=3,
             ajar=(2, 9), dark=dark, handle=brass, mirror=mirror)

    # Két sắt cạnh tủ quần áo (vật tương tác).
    safe = sc.node("Safe", "Area3D", ".", [
        ("transform", xform((-hx + 0.27, 0, -1.05), 90)),
        ("script", 'ExtResource("%s")' % i_rid),
        ("item_id", '&"dream_safe"'),
        ("display_name_key", '"OBJ_SAFE_NAME"'),
    ])
    sg = sc.group("Body", safe)
    sc.box("Box", sg, (0, 0.3, 0), (0.48, 0.6, 0.46), metal_dark)
    sc.box("DoorPanel", sg, (0, 0.3, 0.235), (0.4, 0.5, 0.012), metal_dark)
    sc.cyl("Dial", sg, (0.08, 0.38, 0.25), 0.045, 0.025, brass, basis=basis_x(90))
    sc.box("Handle", sg, (-0.1, 0.3, 0.25), (0.02, 0.12, 0.03), brass)
    for k, y in enumerate((0.12, 0.48)):
        sc.box("Hinge%d" % (k + 1), sg, (-0.205, y, 0.245), (0.02, 0.06, 0.02), brass)
    sc.box("Keypad", sg, (0.08, 0.2, 0.245), (0.09, 0.1, 0.012), sc.mat("KeypadBlack", (0.03, 0.03, 0.03), 0.3))
    sc.sub_res("BoxShape3D", "Shape_safe", [("size", "Vector3(0.6, 0.7, 0.6)")])
    sc.node("CollisionShape3D", "CollisionShape3D", safe, [
        ("transform", xform((0, 0.35, 0))), ("shape", 'SubResource("Shape_safe")')])

    # Bàn trang điểm + gương ở tường đông.
    desk(sc, "Vanity", ".", (hx - 0.27, 0, -1.1), -90, 1.1, 0.5, wood_light, wood_front, knob=brass)
    sc.mesh("MirrorFrame", deco, "box", (0.03, 0.9, 0.7), (hx - 0.02, 1.48, -1.1), wood_light)
    sc.mesh("Mirror", deco, "box", (0.01, 0.8, 0.6), (hx - 0.04, 1.48, -1.1), mirror)
    chair(sc, "Vanity_Stool", ".", (hx - 0.85, 0, -1.1), 90, wood_light, back=False, cushion=head)
    vt = sc.empty("Vanity_Items", deco, (hx - 0.3, 0.75, -1.1), -90)
    sc.mesh("Vase", vt, "cyl", (0.04, 0.06, 0.2, 16), (-0.35, 0.1, 0.0), ceramic)
    # Bình cúc trắng (loài hoa của tang lễ), thoạt nhìn chỉ là hoa trang trí.
    for k in range(7):
        a = k * 2.4
        r = 0.03 + 0.03 * (k % 3)
        hy = 0.32 + 0.05 * ((k * 7) % 3)
        px, pz = -0.35 + r * math.cos(a), r * math.sin(a)
        sc.mesh("FlowerStem", vt, "cyl", (0.003, 0.003, hy - 0.1, 4), (px * 0.9 - 0.035, (hy + 0.1) / 2, pz * 0.9),
                stem, shadow=False)
        sc.mesh("Flower", vt, "sphere", (0.035, 0.05), (px, hy, pz), white_flower)
        sc.mesh("FlowerCore", vt, "sphere", (0.012, 0.02), (px, hy + 0.02, pz), flower_core, shadow=False)
    for k, (x, c) in enumerate(((0.1, (0.7, 0.4, 0.5)), (0.18, (0.6, 0.75, 0.8)))):
        sc.mesh("Perfume%d" % (k + 1), vt, "cyl", (0.025, 0.03, 0.09, 12), (x, 0.045, 0.08),
                sc.mat("Perfume%d" % k, c, 0.05, alpha=0.6))
    sc.mesh("JewelryBox", vt, "box", (0.18, 0.07, 0.12), (0.3, 0.035, -0.06), sage)
    sc.mesh("Hairbrush", vt, "box", (0.05, 0.025, 0.2), (0.05, 0.013, -0.1), wood_front, rot_y=30)
    # Tranh sáp màu trẻ con dán cạnh gương: người thứ tư bị tô đen.
    sc.decal("ChildDrawing", deco, (hx, 1.55, -0.42), "-x", (0.3, 0.3), drawing, roll=4)

    # Ghế bành + đèn cây + bàn trà cạnh cửa sổ.
    ag = sc.group("Armchair", ".", (-1.7, 0, 1.85), 150)
    sc.box("Seat", ag, (0, 0.3, 0.03), (0.78, 0.2, 0.72), sage)
    sc.box("Back", ag, (0, 0.68, -0.31), (0.78, 0.66, 0.16), sage)
    sc.box("ArmL", ag, (-0.34, 0.5, 0.03), (0.12, 0.26, 0.72), sage)
    sc.box("ArmR", ag, (0.34, 0.5, 0.03), (0.12, 0.26, 0.72), sage)
    legs(sc, ag, 0.72, 0.66, 0.2, wood_light, t=0.04, turned=True)
    sc.mesh("SeatCushion", ag, "box", (0.56, 0.08, 0.6), (0, 0.44, 0.06), sage)
    sc.mesh("Pillow", ag, "box", (0.4, 0.3, 0.1), (0.05, 0.62, -0.18), linen, basis=basis_mul(basis_y(10), basis_x(-15)))
    st = table(sc, "SideTable", ".", (-2.35, 0, 1.15), 0, 0.45, 0.45, 0.55, wood_light, t=0.035, apron=False)
    sc.mesh("TeaCup", st, "cyl", (0.04, 0.03, 0.06, 16), (0.06, 0.58, 0.05), ceramic)
    sc.mesh("Saucer", st, "cyl", (0.07, 0.07, 0.008, 16), (0.06, 0.554, 0.05), ceramic)
    sc.mesh("Book", st, "box", (0.16, 0.03, 0.22), (-0.08, 0.565, -0.04), book_cols[0], rot_y=-14)
    fl = sc.empty("FloorLamp", ".", (-2.4, 0, 2.2))
    sc.mesh("Base", fl, "cyl", (0.14, 0.15, 0.03, 20), (0, 0.015, 0), brass)
    sc.mesh("Pole", fl, "cyl", (0.012, 0.012, 1.5, 8), (0, 0.76, 0), brass)
    sc.mesh("Shade", fl, "cyl", (0.14, 0.2, 0.26, 24, False), (0, 1.55, 0), lampshade)

    # Cây cảnh trong chậu: thân + lá to.
    pg = sc.group("Plant", ".", (2.35, 0, 0.3))
    # Khối va chạm cho chậu, phần nhìn là model CC0 (Poly Haven potted_plant_02).
    sc.cyl("PotCollision", pg, (0, 0.2, 0), 0.22, 0.4, sc.mat("Invisible", (0, 0, 0), alpha=0.0))
    sc.model("PlantModel", ".", "potted_plant_02", (2.35, 0, 0.3), 30, 1.2)

    # Dấu chân ướt trẻ con: từ cửa sổ trái đi về phía tủ quần áo hé mở.
    for k in range(7):
        t = k / 6.0
        x = -1.3 + (-1.9 + 1.3) * t + (0.07 if k % 2 else -0.07)
        z = 2.2 + (0.95 - 2.2) * t
        ang = math.degrees(math.atan2(-1.9 + 1.3, 0.95 - 2.2))
        sc.decal("Footprint", deco, (x, 0.0, z), "+y", (0.11, 0.2), footprint, roll=ang + 180, offset=0.003)

    # Đèn trần áp sát.
    lamp = sc.node("CeilingLight", "OmniLight3D", ".", [
        ("transform", xform((0, H - 0.15, -0.2))), ("light_color", color((1, 0.93, 0.82))),
        ("light_energy", "0.25"), ("omni_range", "6.0"), ("shadow_enabled", "false")])
    sc.mesh("Dome", lamp, "sphere", (0.22, 0.14), (0, 0.08, 0), lampshade, shadow=False)
    sc.mesh("Rim", lamp, "cyl", (0.23, 0.23, 0.02, 32), (0, 0.13, 0), brass, shadow=False)
    # Đèn phụ giả ánh sáng hắt từ cửa sổ (cho renderer Compatibility không có GI).
    sc.node("WindowBounce", "OmniLight3D", ".", [
        ("transform", xform((0, 1.4, 1.6))), ("light_color", color((1, 0.97, 0.92))),
        ("light_energy", "0.6"), ("omni_range", "5.5"), ("shadow_enabled", "false"),
        ("light_specular", "0.1")])
    # Phản chiếu cho gương, kim loại, kính.
    sc.node("ReflectionProbe", "ReflectionProbe", ".", [
        ("transform", xform((0, 1.5, 0))), ("size", vec3((W, H, D))), ("box_projection", "true"),
        ("enable_shadows", "true"), ("update_mode", "1")])
    dust(sc, "SunDust", ".", (-0.4, 1.4, 0.8), (1.6, 1.0, 1.4), amount=90)

    # Khung cảnh ngoài cửa sổ: sân cỏ, hàng rào trắng, bụi cây, một cây lớn.
    out = sc.empty("Outside")
    for k in range(14):
        x = -7 + k
        sc.mesh("FencePicket", out, "box", (0.08, 0.9, 0.03), (x, 0.45, 7.5), fence_white)
    sc.mesh("FenceRail", out, "box", (14, 0.06, 0.03), (-0.5, 0.65, 7.48), fence_white)
    sc.mesh("FenceRail", out, "box", (14, 0.06, 0.03), (-0.5, 0.25, 7.48), fence_white)
    for k in range(8):
        sc.mesh("Hedge", out, "sphere", (0.7, 1.0), (-5.5 + k * 1.5, 0.45, 6.6 + 0.2 * (k % 2)), hedge,
                basis=basis_scale(1.2, 1.0, 0.9))
    sc.mesh("TreeTrunk", out, "cyl", (0.16, 0.25, 3.6, 12), (3.5, 1.8, 9.0), tree_bark)
    for k, (dx, dy, dz, r) in enumerate([(0, 4.0, 0, 1.8), (1.1, 3.5, 0.4, 1.3), (-1.0, 3.6, -0.3, 1.4),
                                         (0.2, 4.9, 0.2, 1.2)]):
        sc.mesh("TreeCanopy", out, "sphere", (r, r * 1.8), (3.5 + dx, dy, 9.0 + dz), foliage)

    player(sc, p_rid, (0.6, 0.05, 1.4), 15)
    sc.save("scenes/levels/DreamBedroom.tscn")


# ---------------------------------------------------------------------------
# 2. Nhà cũ Bắc Bộ thập niên 198x: nhà cấp 4 ba gian, mái ngói, bếp sau,
#    hầm ngay dưới phòng của cô ấy (phòng ngủ phía đông). Ban đêm, điện yếu.
# ---------------------------------------------------------------------------

def build_old_house():
    sc = Scene("OldHouse")
    p_rid = sc.ext_res("PackedScene", "res://scenes/player/Player.tscn")

    lime = sc.pbr("WallLimewash", "limewash_old", (1.0, 0.9, 0.7), tile=3.0, normal=1.0)  # vôi ve vàng
    lime_kitchen = sc.pbr("WallKitchen", "limewash_old", (0.72, 0.67, 0.6), tile=2.4, normal=1.2)
    tiles = sc.pbr("FloorBrickTile", "tile_terracotta", (1, 1, 1), tile=1.2, normal=1.0)
    ceil = sc.pbr("CeilingCot", "bamboo_weave", (0.9, 0.85, 0.78), tile=1.6, normal=1.0)
    earth = sc.pbr("Ground", "earth", (0.75, 0.72, 0.68), tile=2.5)
    yard = sc.pbr("YardBrick", "brick_red", (0.62, 0.58, 0.55), tile=1.3, normal=1.2)
    fence = sc.pbr("FenceBrick", "brick_red", (0.75, 0.72, 0.68), tile=1.0, normal=1.3)
    roof = sc.pbr("RoofTile", "roof_tile", (0.9, 0.85, 0.82), tile=1.2, normal=1.5)
    concrete = sc.pbr("CellarConcrete", "concrete_damp", (0.8, 0.78, 0.74), tile=1.5, normal=1.2)
    cellar_wall = sc.pbr("CellarWall", "concrete_damp", (0.9, 0.84, 0.74), tile=1.2, normal=1.5)
    cellar_floor = sc.pbr("CellarFloor", "earth", (0.85, 0.8, 0.72), tile=1.6, normal=1.5)
    kitchen_floor = sc.pbr("KitchenFloor", "concrete_damp", (0.6, 0.55, 0.5), tile=1.4, normal=1.0)
    wood = sc.pbr("WoodDark", "wood_dark", (1, 1, 1), tile=1.0, normal=0.8)
    wood_mid = sc.pbr("WoodMid", "wood_dark", (1.35, 1.25, 1.1), tile=1.0, normal=0.8)
    wood_old = sc.pbr("WoodOld", "wood_weathered", (1, 1, 1), tile=1.0, normal=1.2)
    painted = sc.pbr("PaintedWood", "painted_wood", (1, 1, 1), tile=1.4, normal=1.0)
    lacquer = sc.pbr("AltarRed", "lacquer_red", (1, 1, 1), tile=0.8, normal=0.6)
    iron = sc.pbr("Iron", "rust_metal", (1, 1, 1), tile=0.6, metallic=0.5)
    linen = sc.pbr("LinenOld", "fabric", (0.82, 0.78, 0.68), tile=0.4, normal=0.8)
    blanket = sc.pbr("BlanketFloral", "fabric", (0.55, 0.2, 0.18), tile=0.25, normal=1.2)
    blanket2 = sc.pbr("BlanketGreen", "fabric", (0.3, 0.38, 0.3), tile=0.25, normal=1.2)
    red_cloth = sc.pbr("RedCloth", "fabric", (0.6, 0.06, 0.05), tile=0.2, normal=1.0)
    white_cloth = sc.pbr("WhiteCloth", "fabric", (0.86, 0.84, 0.78), tile=0.25, normal=1.0)
    reed = sc.pbr("ReedMat", "reed_mat", (1, 1, 1), tile=1.0, normal=1.0)
    newspaper = sc.pbr("Newspaper", "newspaper", (0.95, 0.92, 0.85), triplanar=False)
    net = sc.mat("MosquitoNet", (0.9, 0.9, 0.86), 1.0, alpha=0.22)
    glass_dark = sc.mat("CabinetGlass", (0.1, 0.12, 0.12), 0.05, metallic=0.3, alpha=0.55)
    tv_body = sc.pbr("TVBody", "wood_dark", (1.2, 1.1, 1.0), tile=0.5, normal=0.3)
    tv_screen = sc.mat("TVScreen", (0.25, 0.3, 0.32), 0.1, emission=(0.45, 0.55, 0.6), energy=0.6)
    plastic_grey = sc.mat("PlasticGrey", (0.35, 0.34, 0.32), 0.5)
    gold = sc.mat("AltarGold", (0.72, 0.53, 0.22), 0.35, metallic=0.85)
    ceramic = sc.mat("Ceramic", (0.86, 0.84, 0.76), 0.3)
    porcelain_blue = sc.mat("PorcelainBlue", (0.7, 0.76, 0.82), 0.25)
    jar = sc.mat("JarGlaze", (0.28, 0.16, 0.09), 0.3)
    jar_clay = sc.pbr("JarClay", "earth", (1.2, 0.9, 0.7), tile=0.6, normal=0.8)
    brick_counter = sc.pbr("BrickCounter", "brick_red", (0.85, 0.8, 0.75), tile=0.9, normal=1.2)
    straw = sc.pbr("Straw", "reed_mat", (0.75, 0.65, 0.45), tile=0.3, normal=2.0)
    aluminium = sc.mat("Aluminium", (0.62, 0.62, 0.64), 0.45, metallic=0.85)
    wax = sc.mat("CandleWax", (0.88, 0.82, 0.68), 0.6)
    flame = sc.mat("CandleFlame", (1, 0.7, 0.3), 0.5, emission=(1, 0.55, 0.2), energy=4.0, unshaded=True)
    incense = sc.mat("Incense", (0.55, 0.12, 0.08), 0.8)
    ash = sc.mat("Ash", (0.45, 0.44, 0.42), 1.0)
    ember = sc.mat("Ember", (1, 0.3, 0.1), 1.0, emission=(1, 0.25, 0.05), energy=3.0)
    rice = sc.mat("Rice", (0.93, 0.92, 0.86), 0.9)
    fruit_o = sc.mat("FruitRotting", (0.55, 0.33, 0.1), 0.6)
    banana = sc.mat("BananaOld", (0.45, 0.35, 0.12), 0.7)
    rope = sc.mat("Rope", (0.55, 0.45, 0.28), 1.0)
    leaf_green = sc.mat("BananaLeaf", (0.16, 0.28, 0.1), 0.7, cull=True)
    leaf_dry = sc.mat("BananaLeafDry", (0.36, 0.3, 0.16), 0.9, cull=True)
    trunk = sc.mat("BananaTrunk", (0.32, 0.36, 0.2), 0.8)
    soot = sc.mat("Soot", (0.05, 0.045, 0.04), 1.0)
    cord = sc.mat("Cord", (0.05, 0.05, 0.05), 0.7)
    insul = sc.mat("PorcelainKnob", (0.9, 0.88, 0.82), 0.3)
    bulb_glass = sc.mat("BulbYellow", (1, 0.85, 0.55), 0.2, emission=(1, 0.72, 0.38), energy=4.0)
    bulb_red = sc.mat("BulbRed", (1, 0.3, 0.2), 0.2, emission=(1, 0.15, 0.08), energy=4.0)
    bike_paint = sc.mat("BikePaint", (0.08, 0.1, 0.09), 0.4, metallic=0.4)
    tyre = sc.mat("Tyre", (0.03, 0.03, 0.03), 0.9)
    chrome = sc.mat("Chrome", (0.7, 0.7, 0.7), 0.25, metallic=1.0)
    hat = sc.mat("ConicalHat", (0.62, 0.56, 0.4), 0.9, cull=True)
    green_thermos = sc.mat("Thermos", (0.25, 0.45, 0.4), 0.35)
    moonglow = sc.mat("Moon", (0.9, 0.92, 1.0), 1.0, emission=(0.85, 0.9, 1.0), energy=2.0, unshaded=True)
    d_damp = sc.decal_mat("D_Damp", "stain_damp.png")
    d_mold = sc.decal_mat("D_Mold", "mold.png")
    d_crack = sc.decal_mat("D_Crack", "crack.png")
    d_soot = sc.decal_mat("D_Soot", "soot.png")
    d_hand = sc.decal_mat("D_Hand", "handprint.png")
    d_scratch = sc.decal_mat("D_Scratch", "scratches.png")
    d_web = sc.decal_mat("D_Cobweb", "cobweb.png", tint=(1, 1, 1, 0.8))
    d_joss = sc.decal_mat("D_Joss", "joss_paper.png", opaque=True)
    d_talisman = sc.decal_mat("D_Talisman", "talisman.png", opaque=True)
    d_portrait = sc.decal_mat("D_Portrait", "portrait.png", opaque=True)
    d_family = sc.decal_mat("D_Family", "family_photo.png", opaque=True)
    d_calendar = sc.decal_mat("D_Calendar", "calendar.png", opaque=True)
    d_clock = sc.decal_mat("D_Clock", "clock_face.png")

    environment(sc, "night", (0.01, 0.015, 0.04), (0.08, 0.09, 0.13), (0.04, 0.04, 0.05), (0.01, 0.01, 0.01),
                (0.42, 0.48, 0.68), 0.22, sky_energy=0.6, fog_color=(0.07, 0.08, 0.11), fog_density=0.03,
                exposure=1.15, extra=[
                    ("fog_sky_affect", "0.6"),
                    # Ánh đèn sợi đốt hắt lên tường/trần (SSIL) cho có chiều sâu, vẫn giữ góc tối.
                    # Không bật SDFGI: với nền đất dày và đêm tối, SDFGI làm tắt hẳn ánh sáng môi trường.
                    ("ssil_enabled", "true"), ("ssil_intensity", "1.0"),
                    ("volumetric_fog_enabled", "true"), ("volumetric_fog_density", "0.035"),
                    ("volumetric_fog_albedo", color((0.75, 0.78, 0.85))),
                    ("volumetric_fog_emission", color((0.01, 0.012, 0.02))),
                    ("volumetric_fog_anisotropy", "0.4"), ("volumetric_fog_length", "40.0"),
                    ("adjustment_enabled", "true"), ("adjustment_contrast", "1.1"),
                    ("adjustment_saturation", "0.78"),
                ])
    sun(sc, "Moon", (0.35, -0.55, -0.55), (0.55, 0.62, 0.85), 1.0, extra=[("light_volumetric_fog_energy", "2.0")])
    sc.mesh("MoonDisc", ".", "sphere", (2.0, 4.0), (-28, 34, 40), moonglow, shadow=False)

    H, T = 3.2, 0.2           # cao trần nhà chính, độ dày tường
    HK = 2.8                   # cao trần bếp
    s = sc.group("Structure")
    # Nền đất dày 3 m để khoét hầm bên dưới.
    sc.box("Ground", s, (0, -1.5, 0), (30, 3, 30), earth)
    sc.box("Yard", s, (0, 0.01, 6.0), (16, 0.02, 6.0), yard)
    # Hiên nhà: bậc thềm lát gạch cao hơn sân.
    sc.box("Porch", s, (0, 0.03, 3.55), (12.4, 0.06, 1.3), tiles)
    # Tường rào bao quanh khu đất (16 x 18 m).
    sf = sc.group("Structure_Fence")
    sc.box("Fence_South", sf, (0, 0.8, 9.1), (16.4, 1.6, 0.2), fence)
    sc.box("Fence_North", sf, (0, 0.8, -9.1), (16.4, 1.6, 0.2), fence)
    sc.box("Fence_West", sf, (-8.1, 0.8, 0), (0.2, 1.6, 18.0), fence)
    sc.box("Fence_East", sf, (8.1, 0.8, 0), (0.2, 1.6, 18.0), fence)
    for k, x in enumerate((-8.1, 8.1)):
        for j in range(5):
            sc.box("Fence_Pillar", sf, (x, 0.85, -8.0 + j * 4.0), (0.32, 1.7, 0.32), fence)
    # Nhà chính: trong lòng x -6.0..6.0, z -2.75..2.75.
    sc.box("Floor_Main", s, (0, 0.01, 0), (12.0, 0.02, 5.5), tiles)
    sc.box("Floor_Kitchen", s, (0, 0.01, -4.975), (4.5, 0.02, 4.05), kitchen_floor)
    # Tường nhà chính, tường bếp tách thành khối riêng (đèn mỗi phòng chỉ phải chiếu khối gần nó).
    sw = sc.group("Structure_Walls")
    sk = sc.group("Structure_Kitchen")
    sc.box("Wall_Front", sw, (0, H / 2, 2.85), (12.4, H, T), lime)
    sc.box("Wall_Back", sw, (0, H / 2, -2.85), (12.4, H, T), lime)
    sc.box("Wall_West", sw, (-6.1, H / 2, 0), (T, H, 5.9), lime)
    sc.box("Wall_East", sw, (6.1, H / 2, 0), (T, H, 5.9), lime)
    sc.box("Wall_Partition_West", sw, (-2.5, H / 2, 0), (T, H, 5.5), lime)
    sc.box("Wall_Partition_East", sw, (2.5, H / 2, 0), (T, H, 5.5), lime)
    sc.box("Ceiling_Main", sw, (0, H + 0.075, 0), (12.4, 0.15, 5.9), ceil)
    # Bếp sau: trong lòng x -2.25..2.25, z -7.0..-2.95.
    sc.box("Wall_Kitchen_West", sk, (-2.35, HK / 2, -5.025), (T, HK, 4.15), lime_kitchen)
    sc.box("Wall_Kitchen_East", sk, (2.35, HK / 2, -5.025), (T, HK, 4.15), lime_kitchen)
    sc.box("Wall_Kitchen_Back", sk, (0, HK / 2, -7.1), (4.9, HK, T), lime_kitchen)
    sc.box("Ceiling_Kitchen", sk, (0, HK + 0.075, -5.025), (4.9, 0.15, 4.15), ceil)

    # Khoét cửa đi, cửa sổ, hầm.
    sub = lambda n, c, sz, grp=sw: sc.box(n, grp, c, sz, lime, subtract=True)
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
    sub("Window_Kitchen_East", (2.35, 1.6, -5.0), (0.4, 1.0, 1.0), sk)
    # Hầm: dưới phòng ngủ đông, trong lòng x 2.6..6.0, z -2.75..2.75, cao 2.1 m.
    sc.box("Cellar_Space", s, (4.3, -1.25, 0), (3.4, 2.1, 5.5), cellar_wall, subtract=True)
    sc.box("Cellar_FloorFill", s, (4.3, -2.29, 0), (3.4, 0.02, 5.5), cellar_floor)
    # Miệng hầm 0.9 x 2.55 m trên sàn phòng cô ấy.
    sc.box("Cellar_Hatch", s, (4.85, -0.1, 0.825), (0.9, 0.3, 2.55), wood_old, subtract=True)

    # Chân tường quét hắc ín đen (thói quen chống ẩm của nhà cũ) và nẹp trần cót.
    deco = sc.empty("Decor")
    plinth = sc.mat("WallPlinthTar", (0.09, 0.08, 0.07), 0.6)
    for nme, c, sz in [
        ("Front_W", (-4.25, 0.13, 2.745), (3.5, 0.26, 0.01)), ("Front_L", (-1.7, 0.13, 2.745), (1.4, 0.26, 0.01)),
        ("Front_R", (1.7, 0.13, 2.745), (1.4, 0.26, 0.01)), ("Front_E", (4.25, 0.13, 2.745), (3.5, 0.26, 0.01)),
        ("Back_W", (-4.3, 0.13, -2.745), (3.4, 0.26, 0.01)), ("Back_L", (-0.5, 0.13, -2.745), (3.8, 0.26, 0.01)),
        ("Back_E", (4.3, 0.13, -2.745), (3.4, 0.26, 0.01)),
        ("West", (-5.995, 0.13, 0), (0.01, 0.26, 5.5)), ("East", (5.995, 0.13, 0), (0.01, 0.26, 5.5)),
        ("PartW_L", (-2.395, 0.13, 0.9), (0.01, 0.26, 3.7)), ("PartW_B", (-2.605, 0.13, 0.9), (0.01, 0.26, 3.7)),
        ("PartE_L", (2.395, 0.13, 0.9), (0.01, 0.26, 3.7)), ("PartE_H", (2.605, 0.13, 0.9), (0.01, 0.26, 3.7)),
        ("PartW_L2", (-2.395, 0.13, -2.3), (0.01, 0.26, 0.9)), ("PartW_B2", (-2.605, 0.13, -2.3), (0.01, 0.26, 0.9)),
        ("PartE_L2", (2.395, 0.13, -2.3), (0.01, 0.26, 0.9)), ("PartE_H2", (2.605, 0.13, -2.3), (0.01, 0.26, 0.9)),
    ]:
        sc.mesh("Plinth_" + nme, deco, "box", sz, c, plinth, shadow=False)
    batten = wood_old
    for k in range(9):
        x = -6.0 + 1.5 * k
        sc.mesh("CeilingBatten", deco, "box", (0.05, 0.03, 5.5), (x, H - 0.015, 0), batten, shadow=False)
    for z in (-1.4, 0.0, 1.4):
        sc.mesh("CeilingBatten", deco, "box", (12.0, 0.03, 0.05), (0, H - 0.015, z), batten, shadow=False)
    # Xà gỗ lộ ra ở trần bếp (bếp không làm trần cót, chỉ có xà và mái ám khói).
    for k in range(4):
        sc.mesh("KitchenRafter", deco, "box", (0.1, 0.12, 4.15), (-1.7 + k * 1.15, HK - 0.06, -5.025), wood)

    # Mái ngói hai mái + hiên trước (cột gỗ, xà).
    rf = sc.group("Roof", collision=False)
    a = math.degrees(math.atan2(1.6, 2.95))
    L = math.hypot(2.95, 1.6) + 0.6
    off = 0.3
    for nme, sgn in (("Roof_Front", 1), ("Roof_Back", -1)):
        cz = sgn * (2.95 / 2 + off * math.cos(math.radians(a)))
        cy = H + 0.15 + 0.8 - off * math.sin(math.radians(a)) + 0.06
        sc.box(nme, rf, (0, cy, cz), (13.0, 0.12, L), roof, basis=basis_x(sgn * a))
    sc.box("Roof_Ridge", rf, (0, H + 1.85, 0), (13.2, 0.18, 0.3), roof)
    for sx in (-1, 1):
        sc.mesh("Roof_Gable", rf, "prism", (5.9, 1.7, 0.2), (sx * 6.1, H + 0.85, 0), lime, rot_y=90)
    sc.box("Roof_Porch", rf, (0, 3.2, 3.75), (13.0, 0.08, 1.7), roof, basis=basis_x(12))
    ka = math.degrees(math.atan2(0.35, 4.4))
    sc.box("Roof_Kitchen", rf, (0, HK + 0.3, -5.1), (5.4, 0.1, 4.6), roof, basis=basis_x(-ka))
    porch = sc.group("Porch_Columns")
    for k, x in enumerate((-5.9, -2.5, 2.5, 5.9)):
        sc.cyl("Column%d" % (k + 1), porch, (x, 1.5, 4.05), 0.1, 3.0, wood, sides=12)
        sc.cyl("ColumnBase%d" % (k + 1), porch, (x, 0.17, 4.05), 0.16, 0.12, sc.mat("Stone", (0.4, 0.39, 0.36), 0.9),
               sides=12)
    sc.box("Porch_Beam", porch, (0, 3.02, 4.05), (12.2, 0.14, 0.12), wood)

    # Song sắt cửa sổ + khung + cánh cửa chớp sơn xanh mở ra ngoài.
    window_bars(sc, ".", "Bars_Bedroom1_Front", (-4.3, 1.55, 2.85), 1.2, 1.3, True, iron)
    window_bars(sc, ".", "Bars_Bedroom2_Front", (4.0, 1.55, 2.85), 1.2, 1.3, True, iron)
    window_bars(sc, ".", "Bars_Living_FrontL", (-1.75, 1.55, 2.85), 0.9, 1.3, True, iron, n=4)
    window_bars(sc, ".", "Bars_Living_FrontR", (1.75, 1.55, 2.85), 0.9, 1.3, True, iron, n=4)
    window_bars(sc, ".", "Bars_Bedroom1_West", (-6.1, 1.55, 1.5), 1.1, 1.3, False, iron)
    window_bars(sc, ".", "Bars_Bedroom2_East", (6.1, 1.55, 1.2), 1.1, 1.3, False, iron)
    window_bars(sc, ".", "Bars_Kitchen_East", (2.35, 1.6, -5.0), 1.0, 1.0, False, iron, n=5)
    wins = [("Bedroom1_Front", (-4.3, 1.55, 2.85), 1.2, 1.3, "+z"), ("Bedroom2_Front", (4.0, 1.55, 2.85), 1.2, 1.3, "+z"),
            ("Living_FrontL", (-1.75, 1.55, 2.85), 0.9, 1.3, "+z"), ("Living_FrontR", (1.75, 1.55, 2.85), 0.9, 1.3, "+z"),
            ("Bedroom1_West", (-6.1, 1.55, 1.5), 1.1, 1.3, "-x"), ("Bedroom2_East", (6.1, 1.55, 1.2), 1.1, 1.3, "+x"),
            ("Kitchen_East", (2.35, 1.6, -5.0), 1.0, 1.0, "+x")]
    for nme, c, w, h, face in wins:
        along_x = face in ("+z", "-z")
        window_frame(sc, deco, "WindowFrame_" + nme, c, w, h, 0.2, along_x, painted, mullion=False,
                     sill=None)
        # Hai cánh chớp mở hé ra ngoài tường (góc khác nhau cho tự nhiên).
        n = NORMAL[face]
        for k, side in enumerate((-1, 1)):
            ang = side * (100 + 25 * k) * (1 if face in ("+z", "+x") else -1)
            hinge = (c[0] + (side * w / 2 if along_x else 0) + n[0] * 0.12,
                     c[1], c[2] + (0 if along_x else -side * w / 2) + n[2] * 0.12)
            base = 0 if along_x else 90
            leaf = sc.empty("Shutter_%s%d" % (nme, k + 1), deco, hinge, base + ang)
            sc.mesh("Leaf", leaf, "box", (w / 2 - 0.01, h, 0.03), (-side * (w / 4), 0, 0), painted)
            for j in range(7):
                sc.mesh("Louver", leaf, "box", (w / 2 - 0.08, 0.04, 0.045), (-side * (w / 4), -h / 2 + 0.15 + j * 0.16, 0.01),
                        painted, basis=basis_x(-30))

    # Khuôn cửa đi.
    for nme, c, w, h, along_x in [("Main", (0, 1.2, 2.85), 2.0, 2.4, True), ("Bedroom1", (-2.5, 1.05, -1.4), 0.9, 2.1, False),
                                  ("Bedroom2", (2.5, 1.05, -1.4), 0.9, 2.1, False), ("Kitchen", (1.6, 1.05, -2.85), 0.9, 2.1, True)]:
        g = sc.empty("DoorFrame_" + nme, deco, c, 0 if along_x else 90)
        sc.mesh("Left", g, "box", (0.08, h, 0.24), (-w / 2 + 0.04, 0, 0), wood)
        sc.mesh("Right", g, "box", (0.08, h, 0.24), (w / 2 - 0.04, 0, 0), wood)
        sc.mesh("Top", g, "box", (w, 0.08, 0.24), (0, h / 2 - 0.04, 0), wood)
        sc.mesh("Sill", g, "box", (w, 0.04, 0.24), (0, -h / 2 + 0.02, 0), wood)

    # Cánh cửa gỗ (mở) để có cảm giác nhà thật; không chặn lối đi.
    dg = sc.group("Doors", collision=False)
    sc.box("Door_Main_LeafL", dg, (-1.05, 1.2, 2.3), (0.05, 2.38, 0.98), painted, rot_y=0)
    sc.box("Door_Main_LeafR", dg, (1.05, 1.2, 2.3), (0.05, 2.38, 0.98), painted, rot_y=0)
    sc.box("Door_Bedroom1_Leaf", dg, (-2.95, 1.04, -0.92), (0.88, 2.08, 0.04), painted)
    # Cửa phòng cô ấy chỉ mở hé một nửa.
    sc.box("Door_Bedroom2_Leaf", dg, (2.96, 1.04, -1.2), (0.88, 2.08, 0.04), painted, rot_y=35)
    sc.box("Door_Kitchen_Leaf", dg, (1.12, 1.04, -3.4), (0.04, 2.08, 0.88), painted)
    for nme, p in (("Main_BoltL", (-1.0, 1.2, 1.82)), ("Main_BoltR", (1.0, 1.2, 1.82))):
        sc.mesh(nme, deco, "box", (0.03, 0.03, 0.18), p, iron)

    # ---------------- Phòng khách (gian giữa) ----------------
    ag = sc.group("Altar", ".", (0, 0, -2.42))
    sc.box("Top", ag, (0, 1.1, 0), (1.6, 0.06, 0.6), lacquer)
    sc.box("Apron", ag, (0, 0.98, 0.28), (1.5, 0.18, 0.03), gold)
    legs(sc, ag, 1.6, 0.6, 1.07, lacquer, t=0.07)
    sc.box("Shelf", ag, (0, 0.25, 0), (1.45, 0.04, 0.5), lacquer)
    # Bậc cấp nhỏ trên bàn thờ để đặt ảnh thờ cao hơn bát hương.
    sc.box("Step", ag, (0, 1.2, -0.17), (1.2, 0.14, 0.24), lacquer)
    al = sc.empty("Altar_Items", ".", (0, 1.13, -2.42))
    # Bát hương sứ men lam, chân hương cháy dở.
    sc.mesh("IncenseBowl", al, "cyl", (0.1, 0.075, 0.13, 20), (0, 0.065, 0.06), porcelain_blue)
    sc.mesh("IncenseAsh", al, "cyl", (0.092, 0.092, 0.01, 20), (0, 0.125, 0.06), ash, shadow=False)
    for k in range(9):
        a = k * 0.7
        r = 0.02 + 0.05 * ((k * 3) % 5) / 5.0
        h = 0.08 + 0.06 * ((k * 5) % 4) / 4.0
        p = (r * math.cos(a), 0.13 + h / 2, 0.06 + r * math.sin(a))
        sc.mesh("IncenseStick", al, "cyl", (0.0025, 0.0025, h, 4), p, incense, basis=basis_z((k % 3 - 1) * 4),
                shadow=False)
    for k in range(3):
        sc.mesh("IncenseFresh", al, "cyl", (0.003, 0.003, 0.24, 4), (-0.02 + k * 0.02, 0.25, 0.06), incense,
                basis=basis_z((k - 1) * 3), shadow=False)
        sc.mesh("IncenseEmber", al, "sphere", (0.004, 0.008), (-0.02 + k * 0.02 - (k - 1) * 0.006, 0.37, 0.06),
                ember, shadow=False)
    # Ảnh thờ (khuôn mặt nhòe) trong khung gỗ thếp vàng.
    sc.mesh("PortraitFrame", al, "box", (0.3, 0.4, 0.03), (0, 0.35, -0.2), gold, basis=basis_x(-8))
    sc.decal("Portrait", al, (0, 0.35, -0.18), "+z", (0.26, 0.36), d_portrait, offset=0.002)
    sc.mesh("PortraitStand", al, "box", (0.12, 0.12, 0.03), (0, 0.13, -0.24), lacquer)
    # Ảnh thứ hai bị úp mặt xuống.
    sc.mesh("PortraitFaceDown", al, "box", (0.24, 0.025, 0.32), (0.42, 0.02, -0.1), gold, rot_y=8)
    for sx in (-1, 1):
        x = sx * 0.62
        sc.mesh("Vase", al, "cyl", (0.04, 0.065, 0.28, 16), (x, 0.14, 0.0), porcelain_blue)
        sc.mesh("VaseNeck", al, "cyl", (0.05, 0.03, 0.05, 16), (x, 0.3, 0.0), porcelain_blue)
        # Hoa héo rũ.
        for k in range(4):
            sc.mesh("WiltedStem", al, "cyl", (0.003, 0.003, 0.25, 4), (x + (k - 1.5) * 0.02, 0.42, 0.0),
                    banana, basis=basis_z((k - 1.5) * 18), shadow=False)
            sc.mesh("WiltedHead", al, "sphere", (0.025, 0.04), (x + (k - 1.5) * 0.07, 0.52 - abs(k - 1.5) * 0.04, 0.0),
                    fruit_o)
        # Cây nến sáp và ngọn lửa nhỏ.
        cx = sx * 0.38
        sc.mesh("CandleStand", al, "cyl", (0.03, 0.05, 0.12, 12), (cx, 0.06, 0.05), gold)
        sc.mesh("Candle", al, "cyl", (0.018, 0.018, 0.12 if sx < 0 else 0.05, 12),
                (cx, 0.18 if sx < 0 else 0.145, 0.05), wax)
        if sx < 0:
            sc.mesh("Flame", al, "sphere", (0.008, 0.026), (cx, 0.255, 0.05), flame, shadow=False)
    cl = sc.node("CandleLight", "OmniLight3D", al, [
        ("transform", xform((-0.38, 0.3, 0.1))), ("light_color", color((1, 0.6, 0.3))),
        ("light_energy", "0.6"), ("omni_range", "2.2"), ("shadow_enabled", "true"),
        ("script", 'ExtResource("%s")' % sc.ext_res("Script", "res://scripts/levels/LightFlicker.gd")),
        ("hum", "0.18"), ("calm_range", "Vector2(6, 14)"), ("dip", "0.3"),
        ("emissive_mesh", 'NodePath("../Flame")')])
    del cl
    # Mâm ngũ quả đã để lâu ngày, bát cơm cúng cắm đũa dựng đứng.
    sc.mesh("FruitPlate", al, "cyl", (0.16, 0.12, 0.03, 20), (0.0, 0.015, 0.2), gold)
    for k, (dx, dz) in enumerate([(-0.06, 0.18), (0.05, 0.17), (0.0, 0.24), (-0.03, 0.21)]):
        sc.mesh("Fruit", al, "sphere", (0.04, 0.07), (dx, 0.06, dz), fruit_o)
    sc.mesh("Bananas", al, "cyl", (0.02, 0.025, 0.2, 8), (0.05, 0.07, 0.22), banana, basis=basis_mul(basis_y(30), basis_z(80)))
    sc.mesh("RiceBowl", al, "cyl", (0.06, 0.035, 0.05, 16), (-0.22, 0.025, 0.2), ceramic)
    sc.mesh("Rice", al, "sphere", (0.055, 0.04), (-0.22, 0.05, 0.2), rice)
    for k in range(2):
        sc.mesh("Chopstick", al, "cyl", (0.003, 0.004, 0.24, 4), (-0.22 + (k - 0.5) * 0.012, 0.16, 0.2), wood_mid,
                shadow=False)
    for k in range(3):
        sc.mesh("TeaCup", al, "cyl", (0.025, 0.02, 0.03, 12), (0.18 + k * 0.06, 0.015, 0.22), ceramic)
    # Hoành phi, câu đối sơn son thếp vàng.
    sc.mesh("Altar_Panel", deco, "box", (1.5, 0.6, 0.05), (0, 2.45, -2.72), lacquer)
    sc.mesh("Altar_PanelBorder", deco, "box", (1.42, 0.52, 0.01), (0, 2.45, -2.69), gold)
    sc.mesh("Altar_Calligraphy", deco, "box", (1.3, 0.4, 0.012), (0, 2.45, -2.685), lacquer)
    for k in range(4):
        sc.mesh("Altar_Character", deco, "box", (0.18, 0.22, 0.004), (-0.48 + k * 0.32, 2.45, -2.678), gold)
    for sx in (-1, 1):
        sc.mesh("Altar_Couplet", deco, "box", (0.22, 1.5, 0.04), (sx * 1.0, 1.75, -2.73), lacquer)
        for k in range(6):
            sc.mesh("Couplet_Character", deco, "box", (0.12, 0.12, 0.004), (sx * 1.0, 1.15 + k * 0.22, -2.708), gold)
    # Giấy tiền vàng mã vương dưới chân bàn thờ.
    for k in range(9):
        x = -0.6 + (k * 0.37) % 1.3
        z = -2.0 + ((k * 0.53) % 0.8)
        sc.decal("JossPaper", deco, (x, 0.02, z), "+y", (0.12, 0.12), d_joss, roll=k * 37, offset=0.002 + k * 0.0003)
    sc.mesh("JossStack", deco, "box", (0.2, 0.06, 0.14), (0.4, 0.29, -2.42), sc.mat("JossStack", (0.8, 0.62, 0.2), 0.9))
    bulb(sc, "Light_AltarRed", ".", (0.45, 1.5, -2.6), (1, 0.22, 0.1), 0.5, 2.8, bulb_red, cord,
         cord_len=0.02, shadow=False, flicker={"hum": "0.05", "calm_range": "Vector2(9, 20)", "dip": "0.2"})
    bulb(sc, "Light_AltarRed2", ".", (-0.45, 1.5, -2.6), (1, 0.22, 0.1), 0.35, 2.4, bulb_red, cord,
         cord_len=0.02, shadow=False)

    # Lịch bloc, ảnh gia đình (một người bị cào mặt), đồng hồ chết ở 12 giờ, nón lá treo tường.
    sc.mesh("Calendar_Board", deco, "box", (0.01, 0.6, 0.4), (-2.395, 1.75, 1.6), wood_mid)
    sc.decal("Calendar", deco, (-2.39, 1.72, 1.6), "+x", (0.32, 0.38), d_calendar, offset=0.002)
    sc.mesh("FamilyPhoto_Frame", deco, "box", (0.02, 0.5, 0.65), (2.39, 1.85, 0.9), wood)
    sc.decal("FamilyPhoto", deco, (2.378, 1.85, 0.9), "-x", (0.58, 0.44), d_family, offset=0.003)
    sc.mesh("Clock_Case", deco, "box", (0.36, 0.5, 0.1), (0, 2.75, 2.7), wood)
    sc.mesh("Clock_Pendulum", deco, "box", (0.012, 0.18, 0.005), (0, 2.6, 2.65), gold)
    sc.decal("Clock_Face", deco, (0, 2.82, 2.65), "-z", (0.26, 0.26), d_clock, offset=0.003)
    sc.mesh("ConicalHat", deco, "cyl", (0.0, 0.22, 0.15, 24, False), (2.32, 1.6, -0.5), hat,
            basis=basis_mul(basis_z(90), basis_y(0)))
    # Dây điện đi nổi trên tường, puly sứ, công tắc.
    for nme, p0, p1 in [("Wire_LivingBack", (-2.4, 2.9, -2.73), (2.4, 2.9, -2.73)),
                        ("Wire_LivingWest", (-2.38, 2.9, -2.75), (-2.38, 2.9, 2.75)),
                        ("Wire_Drop", (-2.38, 1.3, -1.95), (-2.38, 2.9, -1.95))]:
        mid = tuple((a + b) / 2 for a, b in zip(p0, p1))
        ln = math.dist(p0, p1)
        if abs(p0[1] - p1[1]) > 0.01:
            b = basis_y(0)
        elif abs(p0[0] - p1[0]) > 0.01:
            b = basis_z(90)
        else:
            b = basis_x(90)
        sc.mesh(nme, deco, "cyl", (0.004, 0.004, ln, 4), mid, cord, basis=b, shadow=False)
    for k in range(6):
        sc.mesh("WireKnob", deco, "cyl", (0.012, 0.015, 0.025, 8), (-2.0 + k * 0.8, 2.9, -2.735), insul,
                basis=basis_x(90), shadow=False)
    sc.mesh("Switch", deco, "box", (0.03, 0.12, 0.08), (-2.385, 1.3, -1.95), sc.mat("Bakelite", (0.25, 0.2, 0.15), 0.3))

    # Tủ chè + TV đen trắng dọc tường ngăn phía tây (quay vào phòng khách).
    tg = sc.group("TuChe", ".", (-2.12, 0, 0.9), 90)
    sc.box("Body", tg, (0, 0.45, 0), (1.8, 0.7, 0.48), wood)
    legs(sc, tg, 1.8, 0.48, 0.1, wood, t=0.05, turned=True)
    sc.box("Cavity", tg, (0, 0.47, 0.05), (1.7, 0.58, 0.4), soot, subtract=True)
    for i in range(3):
        sc.mesh("GlassDoor%d" % (i + 1), tg, "box", (0.52, 0.52, 0.01), (-0.6 + i * 0.6, 0.47, 0.245), glass_dark)
        sc.mesh("DoorRail%d" % (i + 1), tg, "box", (0.56, 0.04, 0.02), (-0.6 + i * 0.6, 0.74, 0.245), wood)
    for k in range(5):
        sc.mesh("Cup", tg, "cyl", (0.03, 0.022, 0.05, 12), (-0.7 + k * 0.12, 0.215, 0.05), ceramic)
    sc.mesh("Teapot", tg, "sphere", (0.07, 0.11), (0.3, 0.24, 0.0), porcelain_blue)
    sc.mesh("Bottle", tg, "cyl", (0.03, 0.04, 0.24, 12), (0.65, 0.3, 0.0), sc.mat("BottleGreen", (0.15, 0.3, 0.2), 0.05, alpha=0.7))
    sc.box("Top", tg, (0, 0.82, 0), (1.86, 0.04, 0.52), wood)
    sc.model("CassettePlayer", tg, "portable_cassette_player", (0.68, 0.9, 0.08), -12)
    sc.mesh("Doily", tg, "box", (0.7, 0.004, 0.42), (0, 0.842, 0), white_cloth, shadow=False)
    tv = sc.group("TV_CRT", ".", (-2.12, 0.84, 0.9), 90)
    sc.box("Body", tv, (0, 0.24, -0.03), (0.58, 0.46, 0.44), tv_body)
    sc.box("Back", tv, (0, 0.24, -0.3), (0.42, 0.34, 0.16), plastic_grey)
    sc.box("ScreenBezel", tv, (-0.06, 0.25, 0.192), (0.42, 0.34, 0.01), plastic_grey)
    sc.mesh("Screen", tv, "box", (0.36, 0.28, 0.01), (-0.06, 0.25, 0.2), tv_screen)
    for k in range(3):
        sc.mesh("Knob", tv, "cyl", (0.018, 0.018, 0.02, 10), (0.22, 0.36 - k * 0.09, 0.2), plastic_grey,
                basis=basis_x(90))
    sc.mesh("AntennaBase", tv, "sphere", (0.04, 0.05), (0, 0.48, -0.05), plastic_grey)
    for sgn in (-1, 1):
        sc.mesh("Antenna", tv, "cyl", (0.003, 0.004, 0.5, 4), (sgn * 0.12, 0.69, -0.05), chrome,
                basis=basis_z(-sgn * 28))
    # Màn hình nhiễu trắng còn sáng: rọi một quầng xanh xám lên phòng.
    sc.node("TVGlow", "OmniLight3D", ".", [
        ("transform", xform((-1.75, 1.1, 0.83))), ("light_color", color((0.6, 0.72, 0.85))),
        ("light_energy", "0.35"), ("omni_range", "3.0"), ("shadow_enabled", "false"),
        ("script", 'ExtResource("%s")' % sc.ext_res("Script", "res://scripts/levels/LightFlicker.gd")),
        ("hum", "0.35"), ("calm_range", "Vector2(2, 5)"), ("dip", "0.2"),
        ("emissive_mesh", 'NodePath("../TV_CRT/Screen")')])

    # Bộ bàn ghế gỗ tiếp khách, ấm chén, phích nước.
    table(sc, "Salon_Table", ".", (0.2, 0, 0.9), 0, 1.1, 0.6, 0.48, wood, turned=True)
    sc.model("TeaSet", "Salon_Table", "tea_set_01", (-0.12, 0.48, 0), 90, 0.6)
    sc.mesh("Thermos", "Salon_Table", "cyl", (0.055, 0.06, 0.32, 16), (0.32, 0.62, 0.1), green_thermos)
    sc.mesh("ThermosCap", "Salon_Table", "cyl", (0.035, 0.045, 0.05, 12), (0.32, 0.8, 0.1), aluminium)
    sc.mesh("Ashtray", "Salon_Table", "cyl", (0.06, 0.05, 0.02, 12), (0.3, 0.47, -0.15), glass_dark)
    bg = sc.group("Salon_Bench", ".", (1.45, 0, 0.9), -90)
    sc.box("Seat", bg, (0, 0.44, 0), (1.7, 0.05, 0.55), wood)
    sc.box("Back", bg, (0, 0.8, -0.25), (1.7, 0.6, 0.04), wood)
    sc.box("ArmL", bg, (-0.83, 0.62, 0), (0.05, 0.3, 0.55), wood)
    sc.box("ArmR", bg, (0.83, 0.62, 0), (0.05, 0.3, 0.55), wood)
    legs(sc, bg, 1.7, 0.55, 0.42, wood, t=0.06, turned=True)
    sc.mesh("BenchMat", bg, "box", (1.6, 0.01, 0.5), (0, 0.47, 0.01), reed)
    chair(sc, "Salon_ChairS", ".", (0.2, 0, 1.75), 180, wood, old=True)
    # Một chiếc ghế bị xoay quay vào bàn thờ như có ai vừa ngồi.
    chair(sc, "Salon_ChairN", ".", (0.25, 0, 0.05), 160, wood, old=True)
    # Quạt trần.
    fan = sc.group("CeilingFan", ".", (0.2, 0, 0.9), 17, collision=False)
    sc.box("Rod", fan, (0, 2.95, 0), (0.03, 0.5, 0.03), iron)
    sc.cyl("Motor", fan, (0, 2.68, 0), 0.12, 0.12, plastic_grey)
    for i in range(3):
        sc.box("Blade%d" % (i + 1), fan, (0, 2.66, 0), (0.12, 0.01, 1.3), wood_old, rot_y=i * 60)
    # Xe đạp cũ dựng ngoài hiên.
    bk = sc.empty("Bicycle", ".", (-3.6, 0.06, 3.55), 0)
    for k, x in enumerate((-0.52, 0.52)):
        sc.mesh("Wheel", bk, "torus", (0.3, 0.335), (x, 0.335, 0), tyre, basis=basis_x(90))
        sc.mesh("Rim", bk, "torus", (0.29, 0.3), (x, 0.335, 0), chrome, basis=basis_x(90))
        sc.mesh("Hub", bk, "cyl", (0.025, 0.025, 0.1, 8), (x, 0.335, 0), chrome, basis=basis_x(90))
        for j in range(6):
            sc.mesh("Spoke", bk, "cyl", (0.002, 0.002, 0.58, 3), (x, 0.335, 0), chrome,
                    basis=basis_mul(basis_z(j * 30)), shadow=False)
    for nme, p0, p1 in [("Down", (-0.05, 0.38, 0), (0.42, 0.78, 0)), ("Top", (0.0, 0.8, 0), (0.42, 0.82, 0)),
                        ("Seat", (-0.05, 0.38, 0), (-0.05, 0.86, 0)), ("ChainStay", (-0.05, 0.38, 0), (-0.52, 0.335, 0)),
                        ("SeatStay", (-0.05, 0.8, 0), (-0.52, 0.335, 0)), ("Fork", (0.42, 0.82, 0), (0.52, 0.335, 0)),
                        ("Stem", (0.42, 0.82, 0), (0.4, 1.0, 0))]:
        mid = tuple((a + b) / 2 for a, b in zip(p0, p1))
        ln = math.dist(p0, p1)
        ang = math.degrees(math.atan2(p1[0] - p0[0], p1[1] - p0[1]))
        sc.mesh("Frame_" + nme, bk, "cyl", (0.016, 0.016, ln, 8), mid, bike_paint, basis=basis_z(-ang))
    sc.mesh("Handlebar", bk, "cyl", (0.012, 0.012, 0.55, 8), (0.4, 1.0, 0), chrome, basis=basis_x(90))
    sc.mesh("Saddle", bk, "box", (0.25, 0.05, 0.14), (-0.07, 0.89, 0), tyre)
    sc.mesh("Rack", bk, "box", (0.35, 0.02, 0.14), (-0.42, 0.72, 0), chrome)
    bulb(sc, "Light_Living", ".", (0.0, 2.45, -0.9), (1, 0.66, 0.34), 0.85, 6.5, bulb_glass, cord, cord_len=0.65,
         flicker={"hum": "0.06", "calm_range": "Vector2(6, 15)"}, sway={"amplitude_deg": "Vector2(3, 2)", "speed": "0.3"})
    # Vết ố, mốc, nứt trong phòng khách.
    sc.decal("Mold", deco, (-1.2, 0.5, -2.75), "+z", (1.6, 1.0), d_mold)
    sc.decal("Mold", deco, (2.4, 0.45, 2.0), "-x", (1.2, 0.9), d_mold)
    sc.decal("Damp", deco, (1.6, 2.6, -2.75), "+z", (1.4, 1.2), d_damp)
    sc.decal("Damp", deco, (-0.8, H, 0.5), "-y", (1.6, 1.6), d_damp, offset=0.035)
    sc.decal("Crack", deco, (-2.4, 2.4, -0.4), "+x", (0.9, 0.9), d_crack, roll=20)
    sc.decal("Cobweb", deco, (2.39, H - 0.02, -2.74), "-x", (0.7, 0.7), d_web, roll=0)
    sc.decal("Cobweb", deco, (-2.39, H - 0.02, 2.74), "+x", (0.6, 0.6), d_web, roll=-90)

    # ---------------- Phòng ngủ tây (bố mẹ) ----------------
    bed(sc, "Bed_Parents", ".", (-5.0, 0, -1.0), 90, 1.6, 2.0, wood, reed, blanket2, linen,
        headboard_h=0.95, posts=True, old=True)
    # Màn đã vén cuộn lên thanh.
    sc.mesh("NetRolled", "Bed_Parents", "cyl", (0.06, 0.06, 2.0, 10), (-0.82, 1.8, 0), net, basis=basis_x(90),
            shadow=False)
    wardrobe(sc, "Wardrobe_Parents", ".", (-3.4, 0, -2.44), 0, 1.2, 1.9, 0.58, wood, wood_mid, mirror=None)
    desk(sc, "Desk_Parents", ".", (-4.3, 0, 2.43), 180, 1.1, 0.55, wood_mid, wood)
    sc.mesh("Radio", "Desk_Parents", "box", (0.32, 0.18, 0.12), (0.1, 0.84, 0.05), tv_body)
    sc.mesh("RadioGrille", "Desk_Parents", "box", (0.16, 0.12, 0.005), (0.04, 0.84, -0.012), soot)
    sc.mesh("Lamp", "Desk_Parents", "cyl", (0.06, 0.09, 0.05, 12), (-0.35, 0.775, 0), iron)
    sc.mesh("Notebook", "Desk_Parents", "box", (0.18, 0.015, 0.25), (-0.1, 0.758, 0.05), linen, rot_y=8)
    chair(sc, "Chair_Parents", ".", (-4.3, 0, 1.85), 0, wood_mid, old=True)
    chest_of_drawers(sc, "Drawers_Parents", ".", (-2.85, 0, 1.4), -90, 0.9, 0.95, 0.45, wood, wood_mid)
    cp = sc.group("Chest_Parents", ".", (-5.6, 0, 2.2), 90)
    sc.box("Body", cp, (0, 0.24, 0), (0.9, 0.48, 0.5), wood_old)
    sc.box("Lid", cp, (0, 0.5, 0), (0.92, 0.05, 0.52), wood_old)
    for x in (-0.3, 0.3):
        sc.box("Band", cp, (x, 0.26, 0), (0.04, 0.5, 0.52), iron)
    sc.mesh("Lock", cp, "box", (0.06, 0.08, 0.02), (0, 0.4, 0.26), iron)
    sc.mesh("Hanger_Shirt", deco, "box", (0.5, 0.65, 0.02), (-5.99, 1.6, -2.3), white_cloth, rot_y=90)
    sc.mesh("Hanger_Nail", deco, "cyl", (0.005, 0.005, 0.04, 4), (-5.98, 1.95, -2.3), iron, basis=basis_z(90))
    bulb(sc, "Light_Bedroom1", ".", (-4.3, 2.55, 0.0), (1, 0.66, 0.34), 0.55, 5.5, bulb_glass, cord, cord_len=0.6)
    sc.decal("Mold", deco, (-6.0, 0.5, 0.0), "+x", (2.0, 1.0), d_mold)
    sc.decal("Damp", deco, (-4.5, 2.8, -2.75), "+z", (1.2, 1.0), d_damp)
    sc.decal("Cobweb", deco, (-5.99, H - 0.02, -2.74), "+x", (0.6, 0.6), d_web)

    # ---------------- Phòng ngủ đông (phòng của cô ấy, có hầm bên dưới) ----------------
    bed(sc, "Bed_Her", ".", (5.0, 0, -2.05), -90, 1.4, 2.0, wood, reed, blanket, linen,
        headboard_h=0.95, posts=True, old=True)
    # Màn buông kín giường, phía trong như có dáng người nằm dưới chăn.
    for nme, c, sz in [("NetSideL", (-0.72, 1.12, 0), (0.01, 1.52, 2.0)), ("NetSideR", (0.72, 1.12, 0), (0.01, 1.52, 2.0)),
                       ("NetFoot", (0, 1.12, 0.98), (1.44, 1.52, 0.01)), ("NetHead", (0, 1.12, -0.98), (1.44, 1.52, 0.01)),
                       ("NetTop", (0, 1.88, 0), (1.44, 0.01, 2.0))]:
        sc.mesh(nme, "Bed_Her", "box", sz, c, net, shadow=False)
    sc.mesh("BlanketLump", "Bed_Her", "sphere", (0.22, 0.32), (0.05, 0.52, 0.15), blanket,
            basis=basis_scale(1.1, 0.7, 3.0))
    chest_of_drawers(sc, "Nightstand_Her", ".", (5.75, 0, -1.1), -90, 0.45, 0.55, 0.4, wood, wood_mid, drawers=2)
    sc.model("OilLamp", "Nightstand_Her", "vintage_oil_lamp", (0, 0.55, 0), 0, 0.45)
    wardrobe(sc, "Wardrobe_Her", ".", (3.4, 0, -2.44), 0, 1.2, 1.9, 0.58, wood, wood_mid, ajar=(1, 25), dark=soot)
    desk(sc, "Desk_Her", ".", (2.88, 0, 1.15), 90, 1.1, 0.55, wood_mid, wood, drawer_side=-1)
    for k in range(4):
        sc.mesh("Book", "Desk_Her", "box", (0.15, 0.025, 0.21), (0.25, 0.76 + k * 0.026, -0.05), linen if k % 2 else blanket2,
                rot_y=k * 7)
    sc.mesh("Mirror_Stand", "Desk_Her", "box", (0.22, 0.3, 0.02), (-0.2, 0.9, -0.15), wood)
    chair(sc, "Chair_Her", ".", (3.45, 0, 1.15), -90, wood_mid, old=True)
    chest_of_drawers(sc, "Drawers_Her", ".", (3.2, 0, 2.5), 180, 0.9, 0.85, 0.45, wood, wood_mid)
    # Gương treo tường bị phủ vải trắng (tục che gương khi nhà có tang).
    sc.mesh("Mirror_Her", deco, "box", (0.02, 0.6, 0.4), (2.61, 1.6, 0.0), sc.mat("MirrorOld", (0.55, 0.57, 0.55), 0.1, metallic=0.9))
    sc.mesh("Mirror_Cloth", deco, "box", (0.012, 0.75, 0.5), (2.63, 1.52, 0.02), white_cloth, basis=basis_x(4))
    # Báo cũ dán tường cạnh bàn học.
    for k, (z, y) in enumerate([(1.4, 1.6), (0.9, 1.75), (1.85, 1.95)]):
        sc.mesh("Newspaper", deco, "quad", (0.42, 0.56), (2.607, y, z), newspaper, basis=basis_mul(FACING["+x"], basis_z(k * 4 - 3)),
                shadow=False)
    # Đôi guốc mộc lệch nhau trước cửa phòng.
    for k, (x, z, r) in enumerate([(2.95, -1.15, 10), (3.05, -0.85, 55)]):
        sc.mesh("WoodenClog", deco, "box", (0.1, 0.03, 0.24), (x, 0.03, z), wood_old, rot_y=r)
        sc.mesh("ClogStrap", deco, "box", (0.11, 0.025, 0.04), (x, 0.06, z), red_cloth, rot_y=r)
    # Dấu tay kéo dài và vết cào cạnh miệng hầm.
    sc.decal("HandPrint", deco, (6.0, 0.62, 2.2), "-x", (0.35, 0.5), d_hand, roll=-8)
    sc.decal("HandPrint", deco, (6.0, 0.4, 2.48), "-x", (0.3, 0.45), d_hand, roll=12)
    sc.decal("Scratches", deco, (5.3, -0.1, 1.6), "-x", (0.3, 0.2), d_scratch, roll=90)
    sc.decal("Mold", deco, (6.0, 0.5, -0.5), "-x", (2.4, 1.1), d_mold)
    sc.decal("Damp", deco, (4.4, H, 0.4), "-y", (2.0, 2.0), d_damp, offset=0.035)
    sc.decal("Crack", deco, (5.0, 2.3, 2.75), "-z", (1.0, 1.0), d_crack, roll=-30)
    sc.decal("Cobweb", deco, (5.99, H - 0.02, 2.74), "-x", (0.8, 0.8), d_web, roll=90)
    sc.decal("Cobweb", deco, (2.61, H - 0.02, -2.74), "+x", (0.5, 0.5), d_web)
    # Viền gỗ quanh miệng hầm.
    hatch = sc.empty("Cellar_HatchFrame", deco, (4.85, 0.02, 0.825))
    for nme, c, sz in [("N", (0, 0, -1.3), (1.04, 0.04, 0.07)), ("S", (0, 0, 1.3), (1.04, 0.04, 0.07)),
                       ("W", (-0.485, 0, 0), (0.07, 0.04, 2.6)), ("E", (0.485, 0, 0), (0.07, 0.04, 2.6))]:
        sc.mesh(nme, hatch, "box", sz, c, wood_old)
    # Nắp hầm dựng nghiêng vào tường.
    sc.mesh("Cellar_HatchLid", deco, "box", (0.9, 1.3, 0.05), (5.85, 0.66, 0.2), wood_old,
            basis=basis_mul(basis_y(90), basis_x(-12)))
    bulb(sc, "Light_Bedroom2", ".", (4.2, 2.55, -0.6), (1, 0.6, 0.3), 0.8, 5.5, bulb_glass, cord, cord_len=0.6,
         flicker={"hum": "0.1", "calm_range": "Vector2(3, 8)", "dip": "0.0"})

    # Cầu thang xuống hầm: bậc chỉ để nhìn, va chạm là một mặt dốc (CharacterBody3D không tự bước bậc).
    st = sc.group("Cellar_Stairs", ".", collision=False)
    # Mặt dốc đi từ mặt sàn gạch (y = 0.02) xuống sàn hầm (y = -2.3).
    n, top_z, bot_z, depth = 12, -0.45, 2.1, 2.32
    rise, run = depth / n, (bot_z - top_z) / n
    for k in range(n - 1):
        z0 = bot_z - (k + 1) * run
        top = -2.3 + (k + 1) * rise
        sc.box("Step%02d" % (k + 1), st, (4.85, top - 0.025, z0 + run / 2), (0.86, 0.05, run + 0.02), wood_old)
    for sx in (-1, 1):
        ln = math.hypot(bot_z - top_z, depth)
        ang = math.degrees(math.atan2(depth, bot_z - top_z))
        sc.box("Stringer", st, (4.85 + sx * 0.44, -depth / 2 - 0.1, (top_z + bot_z) / 2), (0.05, 0.25, ln), wood_old,
               basis=basis_x(ang))
    ramp_len = math.hypot(bot_z - top_z, depth)
    ang = math.degrees(math.atan2(depth, bot_z - top_z))
    b = basis_x(ang)
    mid = (4.85, 0.02 - depth / 2, (top_z + bot_z) / 2)
    nrm = (0, math.cos(math.radians(ang)), math.sin(math.radians(ang)))
    c = (mid[0], mid[1] - 0.05 * nrm[1], mid[2] - 0.05 * nrm[2])
    sc.sub_res("BoxShape3D", "Shape_cellar_ramp", [("size", "Vector3(0.9, 0.1, %s)" % f(ramp_len))])
    rb = sc.node("Cellar_StairsRamp", "StaticBody3D", ".", [("transform", xform(c, basis=b))])
    sc.node("CollisionShape3D", "CollisionShape3D", rb, [("shape", 'SubResource("Shape_cellar_ramp")')])
    for k in range(3):
        sc.decal("JossPaper", deco, (4.75 + k * 0.08, -2.3 + (k + 3) * rise + 0.002, bot_z - (k + 3) * run - run / 2),
                 "+y", (0.1, 0.1), d_joss, roll=k * 50)

    # ---------------- Hầm ----------------
    cg = sc.group("Cellar_Shelves", ".", (2.85, -2.3, -1.2), 90)
    for i in range(3):
        sc.box("Board%d" % (i + 1), cg, (0, 0.3 + i * 0.55, 0), (1.8, 0.03, 0.4), wood_old)
    for i, x in enumerate((-0.88, 0.88)):
        sc.box("Upright%d" % (i + 1), cg, (x, 0.85, 0), (0.04, 1.7, 0.4), wood_old)
    sack = sc.pbr("Sack", "fabric", (0.62, 0.52, 0.36), tile=0.12, normal=2.0)
    for i, (x, y) in enumerate([(-0.5, 0.42), (0.3, 0.42), (-0.2, 0.97), (0.55, 1.52)]):
        sc.box("Box%d" % (i + 1), cg, (x, y, 0), (0.35, 0.22, 0.3), wood_old)
    for k in range(5):
        sc.mesh("PickleJar", cg, "cyl", (0.06, 0.08, 0.2, 14), (-0.75 + k * 0.14, 1.42, 0.05), jar)
    for k in range(4):
        sc.mesh("Bottle", cg, "cyl", (0.018, 0.035, 0.25, 10), (0.2 + k * 0.08, 0.97, 0.08),
                sc.mat("BottleDusty", (0.25, 0.28, 0.2), 0.6, alpha=0.8))
    chest = sc.group("Cellar_Chest", ".", (3.3, -2.3, 0.9), 90)
    sc.box("Body", chest, (0, 0.28, 0), (1.0, 0.56, 0.55), iron)
    sc.box("Lid", chest, (0, 0.585, 0), (1.02, 0.05, 0.57), iron)
    for x in (-0.35, 0.0, 0.35):
        sc.box("Band", chest, (x, 0.3, 0), (0.05, 0.6, 0.58), iron)
    sc.mesh("Padlock", chest, "box", (0.07, 0.09, 0.03), (0, 0.45, 0.3), sc.mat("Brass", (0.6, 0.48, 0.25), 0.4, metallic=0.9))
    for i, (x, z) in enumerate([(3.2, 1.9), (3.6, 2.35), (3.1, 2.4)]):
        cr = sc.group("Cellar_Crate%d" % (i + 1), ".", (x, -2.3, z), 12 * i)
        sc.box("Box", cr, (0, 0.22, 0), (0.45, 0.44, 0.45), wood_old)
        for y in (0.08, 0.36):
            sc.mesh("Slat", cr, "box", (0.47, 0.06, 0.47), (0, y, 0), wood_old)
    sc.model("Cellar_OldCrate", ".", "wooden_crate_01", (5.45, -2.3, 1.9), 75)
    sg = sc.group("Cellar_Sacks", ".", (5.6, -2.3, 0.2))
    for k, (dz, dy) in enumerate([(-0.25, 0.18), (0.25, 0.18), (0.0, 0.48)]):
        sc.box("Sack%d" % (k + 1), sg, (0, dy, dz), (0.5, 0.32, 0.6), sack, rot_y=k * 23)
        sc.mesh("SackTop", sg, "sphere", (0.2, 0.18), (0, dy + 0.17, dz), sack, basis=basis_scale(1.2, 1, 1.5))
    # Chum sành lớn bịt vải đỏ, dán bùa vàng, trước chum là bát cơm cắm đũa và nến tàn.
    cj = sc.group("Cellar_Jar", ".", (4.3, -2.3, -2.25))
    sc.cyl("Body", cj, (0, 0.38, 0), 0.32, 0.6, jar_clay, sides=24)
    sc.sphere("Belly", cj, (0, 0.45, 0), 0.36, jar_clay)
    sc.cyl("Neck", cj, (0, 0.78, 0), 0.2, 0.14, jar_clay, sides=24)
    sc.mesh("Cloth", cj, "sphere", (0.24, 0.16), (0, 0.86, 0), red_cloth)
    sc.mesh("Rope", cj, "torus", (0.19, 0.215), (0, 0.8, 0), rope)
    for k in range(4):
        a = math.radians(-55 + k * 35)
        sc.mesh("Talisman", cj, "quad", (0.1, 0.3), (0.37 * math.sin(a), 0.48, 0.37 * math.cos(a)), d_talisman,
                basis=basis_mul(basis_y(math.degrees(a)), basis_x(-5)), shadow=False)
    off = sc.empty("Cellar_Offering", ".", (4.3, -2.28, -1.62), 180)
    sc.mesh("RiceBowl", off, "cyl", (0.06, 0.035, 0.05, 16), (0, 0.025, 0), ceramic)
    sc.mesh("Rice", off, "sphere", (0.055, 0.04), (0, 0.05, 0), rice)
    for k in range(2):
        sc.mesh("Chopstick", off, "cyl", (0.003, 0.004, 0.24, 4), ((k - 0.5) * 0.012, 0.16, 0), wood_mid, shadow=False)
    for k, (dx, h) in enumerate([(-0.15, 0.04), (0.15, 0.07)]):
        sc.mesh("CandleStub", off, "cyl", (0.02, 0.022, h, 10), (dx, h / 2, 0.05), wax)
    sc.mesh("CandleFlame", off, "sphere", (0.008, 0.024), (0.15, 0.085, 0.05), flame, shadow=False)
    sc.node("CandleLight", "OmniLight3D", off, [
        ("transform", xform((0.15, 0.2, 0.15))), ("light_color", color((1, 0.55, 0.25))),
        ("light_energy", "0.5"), ("omni_range", "2.4"), ("shadow_enabled", "true"),
        ("script", 'ExtResource("%s")' % sc.ext_res("Script", "res://scripts/levels/LightFlicker.gd")),
        ("hum", "0.25"), ("calm_range", "Vector2(3, 7)"), ("dip", "0.15"),
        ("emissive_mesh", 'NodePath("../CandleFlame")')])
    # Một chiếc dép trẻ con lẻ loi dưới chân cầu thang.
    sc.mesh("ChildSandal", ".", "box", (0.07, 0.02, 0.15), (4.45, -2.28, 2.45), red_cloth, rot_y=35)
    for k, x in enumerate((3.55, 3.75, 4.85, 5.05)):
        sc.decal("Talisman", deco, (x, -1.05 - 0.05 * (k % 2), -2.75), "+z", (0.1, 0.3), d_talisman, roll=(k - 1.5) * 4)
    sc.decal("Scratches", deco, (6.0, -1.4, 1.0), "-x", (0.5, 0.6), d_scratch, roll=5)
    sc.decal("Scratches", deco, (6.0, -1.7, 1.5), "-x", (0.4, 0.5), d_scratch, roll=-10)
    sc.decal("Mold", deco, (4.3, -1.8, -2.75), "+z", (3.0, 1.0), d_mold)
    sc.decal("Mold", deco, (6.0, -1.8, -1.0), "-x", (2.5, 1.0), d_mold)
    sc.decal("Cobweb", deco, (2.61, -0.22, -2.74), "+x", (0.9, 0.9), d_web)
    sc.decal("Cobweb", deco, (5.99, -0.22, -2.74), "-x", (0.8, 0.8), d_web, roll=0)
    bulb(sc, "Light_Cellar", ".", (4.3, -0.65, -0.8), (1, 0.6, 0.28), 1.4, 6.0, bulb_glass, cord, cord_len=0.35,
         flicker={"hum": "0.12", "calm_range": "Vector2(2, 6)", "burst_count": "Vector2i(3, 9)", "dip": "0.0"},
         sway={"amplitude_deg": "Vector2(4, 3)", "speed": "0.22"})
    dust(sc, "CellarDust", ".", (4.3, -1.3, 0.0), (1.5, 0.9, 2.5), amount=70, col=(0.9, 0.85, 0.75, 0.3))
    dust(sc, "LivingDust", ".", (0.0, 1.6, 0.0), (2.2, 1.2, 2.5), amount=60, col=(1, 0.9, 0.7, 0.25))

    # ---------------- Bếp ----------------
    kc = sc.group("Kitchen_Hearth", ".", (-1.0, 0, -6.7))
    sc.box("Counter", kc, (0, 0.4, 0), (2.2, 0.8, 0.6), brick_counter)
    sc.box("CounterTop", kc, (0, 0.81, 0), (2.25, 0.03, 0.64), concrete)
    # Hốc đun củi khoét vào bệ.
    sc.box("FirePit", kc, (-0.55, 0.42, 0.15), (0.5, 0.35, 0.4), soot, subtract=True)
    sc.mesh("Ash", kc, "box", (0.45, 0.02, 0.35), (-0.55, 0.26, 0.15), ash)
    sc.mesh("Ember", kc, "sphere", (0.05, 0.04), (-0.55, 0.28, 0.12), ember, shadow=False)
    sc.mesh("Stove", kc, "cyl", (0.14, 0.16, 0.18, 16), (-0.5, 0.92, 0), iron)
    sc.mesh("Pot", kc, "cyl", (0.17, 0.14, 0.18, 20), (-0.5, 1.1, 0), soot)
    sc.mesh("PotLid", kc, "cyl", (0.02, 0.17, 0.04, 20), (-0.5, 1.21, 0), aluminium)
    sc.mesh("Kettle", kc, "sphere", (0.11, 0.18), (0.05, 0.92, 0.0), aluminium)
    sc.mesh("KettleSpout", kc, "cyl", (0.01, 0.02, 0.12, 6), (0.16, 0.95, 0), aluminium, basis=basis_z(-60))
    sc.mesh("CuttingBoard", kc, "cyl", (0.17, 0.17, 0.05, 20), (0.6, 0.85, 0.05), wood_old)
    sc.mesh("Cleaver", kc, "box", (0.2, 0.004, 0.09), (0.6, 0.878, 0.05), iron, rot_y=25)
    # Kiềng ba chân bên cạnh, bó củi, đống rơm.
    for k in range(3):
        a = math.radians(k * 120)
        sc.mesh("TrivetLeg", ".", "cyl", (0.012, 0.012, 0.25, 6), (0.6 + 0.12 * math.cos(a), 0.125, -6.3 + 0.12 * math.sin(a)),
                iron)
    sc.mesh("TrivetRing", ".", "torus", (0.12, 0.14), (0.6, 0.25, -6.3), iron)
    for k in range(7):
        sc.mesh("Firewood", ".", "cyl", (0.035, 0.04, 0.8, 7), (-2.0 + (k % 4) * 0.08, 0.04 + (k // 4) * 0.07, -5.9 + (k % 3) * 0.05),
                wood_old, basis=basis_x(90))
    for k, (dx, dz, r) in enumerate([(0, 0, 0.35), (0.25, 0.2, 0.25), (-0.15, 0.3, 0.28), (0.1, -0.3, 0.22)]):
        sc.mesh("StrawPile", ".", "sphere", (r, r * 1.2), (-1.85 + dx, r * 0.3, -5.25 + dz), straw,
                basis=basis_mul(basis_y(k * 40), basis_scale(1.0, 0.55, 1.3)))
    sc.decal("SootMark", deco, (-1.5, 1.7, -7.0), "+z", (1.6, 2.0), d_soot)
    sc.decal("SootMark", deco, (-0.6, HK - 0.2, -6.4), "-y", (2.0, 1.5), d_soot, offset=0.02)
    wc = sc.group("Kitchen_WallCabinet", ".", (-1.0, 1.65, -6.82))
    sc.box("Body", wc, (0, 0.3, 0), (2.0, 0.6, 0.35), wood_mid)
    sc.mesh("DoorGap", wc, "box", (0.01, 0.55, 0.01), (0, 0.3, 0.176), wood)
    cb = sc.group("Kitchen_DishCabinet", ".", (-2.0, 0, -4.2), 90)
    sc.box("Body", cb, (0, 0.8, 0), (0.9, 1.4, 0.45), wood_mid)
    legs(sc, cb, 0.9, 0.45, 0.1, wood_mid, t=0.05)
    sc.mesh("MeshDoorTop", cb, "box", (0.8, 0.55, 0.01), (0, 1.15, 0.228), glass_dark)
    sc.mesh("DoorBottom", cb, "box", (0.8, 0.55, 0.01), (0, 0.5, 0.228), wood)
    for k in range(4):
        sc.mesh("Bowl", cb, "cyl", (0.06, 0.035, 0.05, 12), (-0.3 + k * 0.2, 1.0, 0.0), porcelain_blue)
    for i, z in enumerate((-6.55, -5.85)):
        wj = sc.group("Kitchen_WaterJar%d" % (i + 1), ".", (1.8, 0, z))
        sc.cyl("Jar", wj, (0, 0.3, 0), 0.28, 0.5, jar_clay, sides=20)
        sc.sphere("Belly", wj, (0, 0.38, 0), 0.32, jar_clay)
        sc.cyl("Rim", wj, (0, 0.66, 0), 0.24, 0.06, jar_clay, sides=20)
        sc.mesh("Water", wj, "cyl", (0.21, 0.21, 0.01, 20), (0, 0.6, 0), sc.mat("DarkWater", (0.02, 0.03, 0.03), 0.02))
        sc.mesh("Lid", wj, "cyl", (0.26, 0.26, 0.02, 20), (0.1 if i else -0.1, 0.7, 0.0), wood_old,
                basis=basis_z(6 if i else -4))
    sc.mesh("CoconutLadle", ".", "sphere", (0.07, 0.07), (1.4, 0.035, -6.2), wood_old)
    sc.model("WaterBucket", ".", "wooden_bucket_01", (1.25, 0, -6.7), 25)
    sc.model("WickerBasket", ".", "wicker_basket_01", (-1.6, 0, -5.7), 15)
    table(sc, "Kitchen_LowTable", ".", (0.4, 0, -4.6), 0, 0.8, 0.8, 0.32, wood_old, t=0.04, apron=False)
    for k in range(3):
        sc.mesh("Bowl", "Kitchen_LowTable", "cyl", (0.06, 0.035, 0.05, 12), (-0.15 + k * 0.15, 0.345, 0.1), ceramic)
    sc.mesh("Chopsticks", "Kitchen_LowTable", "box", (0.24, 0.008, 0.02), (0.05, 0.325, -0.15), wood_mid, rot_y=10)
    sc.model("EnamelPot", "Kitchen_LowTable", "pot_enamel_01", (-0.22, 0.32, -0.15), 30)
    for i, (x, z) in enumerate([(0.4, -5.25), (0.4, -3.95), (-0.25, -4.6), (1.05, -4.6)]):
        table(sc, "Kitchen_Stool%d" % (i + 1), ".", (x, 0, z), i * 11, 0.28, 0.28, 0.24, wood_old, t=0.03, apron=False)
    shelf = sc.group("Kitchen_Shelf", ".", (2.1, 1.5, -3.6), -90, collision=False)
    sc.box("Board", shelf, (0, 0, 0), (0.9, 0.03, 0.25), wood_old)
    for i in range(3):
        sc.cyl("Bowl%d" % (i + 1), shelf, (-0.3 + i * 0.3, 0.05, 0), 0.07, 0.06, ceramic)
    # Rổ rá tre treo tường.
    for k, (z, r) in enumerate([(-6.2, 0.2), (-5.7, 0.15)]):
        sc.mesh("BambooBasket", deco, "cyl", (r, r * 0.7, 0.08, 20), (-2.2, 1.8, z), reed, basis=basis_z(90))
    sc.decal("Mold", deco, (2.25, 0.5, -4.0), "-x", (2.0, 1.0), d_mold)
    sc.decal("Cobweb", deco, (-2.24, HK - 0.14, -6.99), "+x", (0.8, 0.8), d_web)
    bulb(sc, "Light_Kitchen", ".", (0.0, 2.25, -5.0), (1, 0.62, 0.3), 0.95, 6.0, bulb_glass, cord, cord_len=0.4,
         flicker={"hum": "0.08", "calm_range": "Vector2(5, 12)"})

    # ---------------- Sân ----------------
    # Bụi chuối góc vườn (thứ cây dân gian gắn với chuyện ma), lá rách, có tàu lá khô rũ xuống.
    for k, (x, z, h) in enumerate([(6.6, 7.6, 2.6), (7.2, 7.0, 3.1), (6.9, 8.3, 2.2), (-7.0, -7.6, 2.8)]):
        g = sc.empty("BananaTree%d" % (k + 1), ".", (x, 0, z), k * 47)
        sc.mesh("Trunk", g, "cyl", (0.1, 0.16, h, 10), (0, h / 2, 0), trunk)
        for j in range(6):
            a = j * 60 + k * 13
            dry = j in (1, 4)
            tilt = 60 if not dry else 150
            lb = basis_mul(basis_y(a), basis_x(tilt - 90))
            d = (lb[2], lb[5], lb[8])
            sc.mesh("Leaf", g, "box", (0.45, 0.01, 1.7), (d[0] * 0.85, h + d[1] * 0.85, d[2] * 0.85),
                    leaf_dry if dry else leaf_green, basis=lb)
    # Dây phơi và một chiếc áo trắng đung đưa.
    sc.mesh("ClothesLinePostW", ".", "cyl", (0.04, 0.04, 2.0, 6), (-6.0, 1.0, 5.5), wood_old)
    sc.mesh("ClothesLinePostE", ".", "cyl", (0.04, 0.04, 2.0, 6), (-2.5, 1.0, 5.8), wood_old)
    sc.mesh("ClothesLine", ".", "cyl", (0.004, 0.004, 3.51, 4), (-4.25, 1.95, 5.65), cord,
            basis=basis_mul(basis_y(-4.9), basis_z(90)))
    shirt = sc.empty("HangingShirt", ".", (-4.6, 1.95, 5.62), props=[
        ("script", 'ExtResource("%s")' % sc.ext_res("Script", "res://scripts/levels/Sway.gd")),
        ("amplitude_deg", "Vector2(10, 3)"), ("speed", "0.25")])
    sc.mesh("Body", shirt, "box", (0.46, 0.62, 0.02), (0, -0.36, 0), white_cloth)
    for sx in (-1, 1):
        sc.mesh("Sleeve", shirt, "box", (0.32, 0.12, 0.02), (sx * 0.32, -0.12, 0), white_cloth, basis=basis_z(sx * 35))
    sc.mesh("WaterJar_Yard", ".", "sphere", (0.45, 0.8), (5.0, 0.45, 3.8), jar_clay)
    sc.mesh("Broom", ".", "cyl", (0.015, 0.015, 1.3, 6), (2.3, 0.65, 3.0), wood_old, basis=basis_x(-15))
    sc.mesh("BroomHead", ".", "cyl", (0.03, 0.15, 0.4, 10), (2.3, 0.1, 3.18), straw, basis=basis_x(-15))
    sc.decal("YardMoss", deco, (3.5, 0.025, 7.0), "+y", (3.0, 3.0), d_mold, roll=30, offset=0.002)
    sc.decal("YardMoss", deco, (-5.0, 0.025, 8.0), "+y", (3.0, 2.0), d_mold, roll=-10, offset=0.002)

    # Đèn hiên ngoài sân.
    bulb(sc, "Light_Porch", ".", (2.6, 2.75, 3.4), (1, 0.66, 0.34), 0.5, 6.0, bulb_glass, cord, cord_len=0.15,
         sway={"amplitude_deg": "Vector2(5, 4)", "speed": "0.4"})

    player(sc, p_rid, (0, 0.05, 6.5), 0)
    sc.save("scenes/levels/OldHouse.tscn")


if __name__ == "__main__":
    build_dream_bedroom()
    build_old_house()
