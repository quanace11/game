#!/usr/bin/env python3
"""Bộ dựng mesh thủ tục nhỏ: sinh hình khối có bo cạnh, ống uốn, khối tiện, mặt tham số...
rồi ghi ra file .obj (Godot nhập thành ArrayMesh, mỗi `usemtl` là một surface riêng).

Dùng cho tools/bus_models.py và tools/bus_puzzles_blockout.py. Không cần thư viện ngoài.

Quy ước:
- 1 đơn vị = 1 mét, +Y lên trên. UV tính bằng mét (u, v theo kích thước thật) để vật liệu
  chỉ cần uv1_scale = 1 / kích thước ảnh texture là trải đúng tỉ lệ ngoài đời.
- Mỗi Mesh có nhiều "khe vật liệu" (slot). Thứ tự slot = thứ tự surface trong Godot,
  scene gán vật liệu bằng surface_material_override/<thứ tự>.
"""

import math
import os

# ---------------------------------------------------------------------------
# Toán vector nhỏ gọn
# ---------------------------------------------------------------------------


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(a):
    return math.sqrt(dot(a, a))


def norm(a):
    l = length(a)
    return (a[0] / l, a[1] / l, a[2] / l) if l > 1e-12 else (0.0, 1.0, 0.0)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class Xf:
    """Phép biến đổi affine: ma trận 3x3 (theo hàng) + tịnh tiến."""

    def __init__(self, m=None, t=(0.0, 0.0, 0.0)):
        self.m = m or [1, 0, 0, 0, 1, 0, 0, 0, 1]
        self.t = t

    def __mul__(self, o):
        a, b = self.m, o.m
        m = [sum(a[i * 3 + k] * b[k * 3 + j] for k in range(3)) for i in range(3) for j in range(3)]
        return Xf(m, add(self.apply_dir(o.t), self.t))

    def apply(self, p):
        return add(self.apply_dir(p), self.t)

    def apply_dir(self, p):
        m = self.m
        return (m[0] * p[0] + m[1] * p[1] + m[2] * p[2], m[3] * p[0] + m[4] * p[1] + m[5] * p[2],
                m[6] * p[0] + m[7] * p[1] + m[8] * p[2])

    def apply_normal(self, n):
        # Dùng ma trận nghịch đảo chuyển vị để pháp tuyến đúng cả khi co giãn không đều.
        m = self.m
        c = [m[4] * m[8] - m[5] * m[7], m[5] * m[6] - m[3] * m[8], m[3] * m[7] - m[4] * m[6],
             m[2] * m[7] - m[1] * m[8], m[0] * m[8] - m[2] * m[6], m[1] * m[6] - m[0] * m[7],
             m[1] * m[5] - m[2] * m[4], m[2] * m[3] - m[0] * m[5], m[0] * m[4] - m[1] * m[3]]
        # c là ma trận phụ hợp chuyển vị (cofactor) -> tỉ lệ với nghịch đảo chuyển vị.
        return norm((c[0] * n[0] + c[1] * n[1] + c[2] * n[2], c[3] * n[0] + c[4] * n[1] + c[5] * n[2],
                     c[6] * n[0] + c[7] * n[1] + c[8] * n[2]))


def T(x, y, z):
    return Xf(t=(x, y, z))


def RX(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return Xf([1, 0, 0, 0, c, -s, 0, s, c])


def RY(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return Xf([c, 0, s, 0, 1, 0, -s, 0, c])


def RZ(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return Xf([c, -s, 0, s, c, 0, 0, 0, 1])


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return Xf([x, 0, 0, 0, y, 0, 0, 0, z])


I = Xf()


# ---------------------------------------------------------------------------
# Mesh nhiều khe vật liệu
# ---------------------------------------------------------------------------

class Mesh:
    def __init__(self, name):
        self.name = name
        self.slots = []        # thứ tự surface
        self.data = {}         # slot -> [verts, normals, uvs, tris]

    def _slot(self, slot):
        if slot not in self.data:
            self.slots.append(slot)
            self.data[slot] = [[], [], [], []]
        return self.data[slot]

    def add(self, slot, verts, normals, uvs, tris, xf=None, flip=False):
        """Thêm một mảnh lưới. tris: bộ ba chỉ số (ngược chiều kim đồng hồ khi nhìn từ phía pháp tuyến)."""
        d = self._slot(slot)
        base = len(d[0])
        for p, n in zip(verts, normals):
            if xf is not None:
                p = xf.apply(p)
                n = xf.apply_normal(n)
            d[0].append(p)
            d[1].append(mul(n, -1) if flip else n)
        d[2].extend(uvs)
        for a, b, c in tris:
            d[3].append((base + a, base + c, base + b) if flip else (base + a, base + b, base + c))
        return self

    def merge(self, other, xf=None, slot_map=None):
        for slot in other.slots:
            v, n, uv, t = other.data[slot]
            self.add((slot_map or {}).get(slot, slot), v, n, uv, t, xf)
        return self

    def triangle_count(self):
        return sum(len(self.data[s][3]) for s in self.slots)

    def write_obj(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out = ["# Sinh tự động bởi tools/mesh_kit.py - đừng sửa tay", "o %s" % self.name]
        vo = 1
        body = []
        for slot in self.slots:
            v, n, uv, t = self.data[slot]
            for p in v:
                out.append("v %.4f %.4f %.4f" % p)
            for q in uv:
                out.append("vt %.4f %.4f" % q)
            for q in n:
                out.append("vn %.3f %.3f %.3f" % q)
            body.append("usemtl %s" % slot)
            for a, b, c in t:
                a, b, c = a + vo, b + vo, c + vo
                body.append("f %d/%d/%d %d/%d/%d %d/%d/%d" % (a, a, a, b, b, b, c, c, c))
            vo += len(v)
        with open(path, "w") as fh:
            fh.write("\n".join(out + body) + "\n")


# ---------------------------------------------------------------------------
# Lưới tham số: hàm f(u, v) -> điểm. Pháp tuyến tính từ lưới (trơn).
# ---------------------------------------------------------------------------

def grid(mesh, slot, fn, nu, nv, u_range=(0.0, 1.0), v_range=(0.0, 1.0), uv_fn=None, xf=None, flip=False,
         wrap_u=False, double=False, normal_fn=None, flat=False):
    """Mặt lưới (nu x nv ô). uv_fn(u, v, p) -> (s, t) theo mét; mặc định tự đo chiều dài cung."""
    us = [u_range[0] + (u_range[1] - u_range[0]) * i / nu for i in range(nu + 1)]
    vs = [v_range[0] + (v_range[1] - v_range[0]) * j / nv for j in range(nv + 1)]
    pts = [[fn(u, v) for u in us] for v in vs]
    # Pháp tuyến: sai phân trung tâm trên lưới.
    norms = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            if normal_fn:
                row.append(normal_fn(us[i], vs[j], pts[j][i]))
                continue
            if wrap_u:
                il, ir = (i - 1) % nu, (i + 1) % nu
            else:
                il, ir = max(i - 1, 0), min(i + 1, nu)
            jd, ju = max(j - 1, 0), min(j + 1, nv)
            du = sub(pts[j][ir], pts[j][il])
            dv = sub(pts[ju][i], pts[jd][i])
            n = cross(du, dv)
            if length(n) < 1e-10:
                # Điểm suy biến (đỉnh nón, cực cầu): mượn hàng bên cạnh.
                jj = 1 if j == 0 else nv - 1
                du = sub(pts[jj][ir], pts[jj][il])
                dv = sub(pts[min(jj + 1, nv)][i], pts[max(jj - 1, 0)][i])
                n = cross(du, dv)
            row.append(norm(n))
        norms.append(row)
    if uv_fn is None:
        # Độ dài cung dọc u (hàng giữa) và dọc v (cột giữa) để UV theo mét.
        mid_v = nv // 2
        su = [0.0]
        for i in range(1, nu + 1):
            su.append(su[-1] + length(sub(pts[mid_v][i], pts[mid_v][i - 1])))
        mid_u = nu // 2
        sv = [0.0]
        for j in range(1, nv + 1):
            sv.append(sv[-1] + length(sub(pts[j][mid_u], pts[j - 1][mid_u])))
        uv_fn2 = lambda i, j: (su[i], sv[j])
    else:
        uv_fn2 = lambda i, j: uv_fn(us[i], vs[j], pts[j][i])
    verts, ns, uvs, tris = [], [], [], []
    for j in range(nv + 1):
        for i in range(nu + 1):
            verts.append(pts[j][i])
            ns.append(norms[j][i])
            uvs.append(uv_fn2(i, j))
    w = nu + 1
    if flat:
        # Mặt phẳng từng ô (giấy cứng gấp nếp): tách đỉnh, pháp tuyến theo mặt.
        fv, fn_, fuv, ft = [], [], [], []
        for j in range(nv):
            for i in range(nu):
                a = j * w + i
                for tri in ((a, a + 1, a + w + 1), (a, a + w + 1, a + w)):
                    p0, p1, p2 = verts[tri[0]], verts[tri[1]], verts[tri[2]]
                    n = norm(cross(sub(p1, p0), sub(p2, p0)))
                    base = len(fv)
                    for q in tri:
                        fv.append(verts[q])
                        fn_.append(n)
                        fuv.append(uvs[q])
                    ft.append((base, base + 1, base + 2))
        verts, ns, uvs, tris = fv, fn_, fuv, ft
    else:
        for j in range(nv):
            for i in range(nu):
                a = j * w + i
                tris.append((a, a + 1, a + w + 1))
                tris.append((a, a + w + 1, a + w))
    mesh.add(slot, verts, ns, uvs, tris, xf, flip)
    if double:
        mesh.add(slot, verts, ns, uvs, tris, xf, not flip)
    return mesh


# ---------------------------------------------------------------------------
# Hộp: cạnh vuông (pháp tuyến phẳng) hoặc bo tròn (trơn), có thể biến dạng.
# ---------------------------------------------------------------------------

_FACES = [  # pháp tuyến, trục u, trục v
    ((1, 0, 0), (0, 0, -1), (0, 1, 0)), ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    ((0, 1, 0), (1, 0, 0), (0, 0, -1)), ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
]


def box(mesh, slot, size, xf=None, slot_fn=None, faces=None):
    """Hộp cạnh vuông, tâm ở gốc. slot_fn(normal) -> slot để mỗi mặt một vật liệu. faces: bỏ bớt mặt."""
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    h = (hx, hy, hz)
    for k, (n, u, v) in enumerate(_FACES):
        if faces is not None and k not in faces:
            continue
        c = (n[0] * hx, n[1] * hy, n[2] * hz)
        su = abs(dot(u, h))
        sv = abs(dot(v, h))
        pts = [add(c, add(mul(u, a * su), mul(v, b * sv))) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        uvs = [((a + 1) * su, (b + 1) * sv) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        s = slot_fn(n) if slot_fn else slot
        mesh.add(s, pts, [n] * 4, uvs, [(0, 1, 2), (0, 2, 3)], xf)
    return mesh


def rbox(mesh, slot, size, radius, segs=3, mid=1, xf=None, deform=None, slot_fn=None, faces=None):
    """Hộp bo tròn mọi cạnh (bán kính `radius`). deform(p, n) -> (p, n) để uốn/phồng trước khi đặt vào xf.

    UV mỗi mặt chiếu phẳng theo mét. slot_fn(normal_gốc) -> slot cho phép chia vật liệu theo mặt.
    """
    h = (size[0] / 2, size[1] / 2, size[2] / 2)
    r = min(radius, h[0] - 1e-4, h[1] - 1e-4, h[2] - 1e-4)
    r = max(r, 1e-4)
    inner = (h[0] - r, h[1] - r, h[2] - r)

    def coords(hh, rr, n_mid):
        c = [-hh + rr * (1 - math.cos(math.pi / 2 * k / segs)) for k in range(segs)]
        c += [-(hh - rr) + 2 * (hh - rr) * k / n_mid for k in range(n_mid + 1)]
        c += [hh - rr * (1 - math.cos(math.pi / 2 * k / segs)) for k in range(segs - 1, -1, -1)]
        return c

    for k, (n, u, v) in enumerate(_FACES):
        if faces is not None and k not in faces:
            continue
        au = [abs(x) for x in u].index(1)
        av = [abs(x) for x in v].index(1)
        an = [abs(x) for x in n].index(1)
        cu = coords(h[au], r, mid)
        cv = coords(h[av], r, mid)
        verts, ns, uvs, tris = [], [], [], []
        for b in cv:
            for a in cu:
                p = [0.0, 0.0, 0.0]
                p[an] = n[an] * h[an]
                p[au] = a * u[au]
                p[av] = b * v[av]
                q = tuple(clamp(p[i], -inner[i], inner[i]) for i in range(3))
                d = norm(sub(tuple(p), q))
                pos = add(q, mul(d, r))
                nn = d
                if deform:
                    pos, nn = deform(pos, nn)
                verts.append(pos)
                ns.append(nn)
                uvs.append((a * u[au] * (1 if u[au] > 0 else -1) + h[au], b + h[av]))
        w = len(cu)
        for j in range(len(cv) - 1):
            for i in range(w - 1):
                a = j * w + i
                tris.append((a, a + 1, a + w + 1))
                tris.append((a, a + w + 1, a + w))
        s = slot_fn(n) if slot_fn else slot
        mesh.add(s, verts, ns, uvs, tris, xf)
    return mesh


# ---------------------------------------------------------------------------
# Ống uốn theo đường gấp khúc (tay vịn, khung ghế, vô-lăng...)
# ---------------------------------------------------------------------------

def round_path(points, radius, segs=6):
    """Bo tròn các góc của đường gấp khúc bằng cung tròn bán kính `radius`."""
    if len(points) < 3:
        return list(points)
    out = [points[0]]
    for i in range(1, len(points) - 1):
        p0, p1, p2 = points[i - 1], points[i], points[i + 1]
        d0 = norm(sub(p0, p1))
        d1 = norm(sub(p2, p1))
        ang = math.acos(clamp(dot(d0, d1), -1, 1))
        if ang > math.pi - 1e-3:
            out.append(p1)
            continue
        cut = min(radius / math.tan(ang / 2), length(sub(p0, p1)) * 0.49, length(sub(p2, p1)) * 0.49)
        a = add(p1, mul(d0, cut))
        b = add(p1, mul(d1, cut))
        for k in range(segs + 1):
            t = k / segs
            # Bezier bậc hai qua đỉnh góc: đủ tròn cho ống nhỏ.
            q = add(add(mul(a, (1 - t) ** 2), mul(p1, 2 * t * (1 - t))), mul(b, t * t))
            out.append(q)
    out.append(points[-1])
    return out


def tube(mesh, slot, path, radius, sides=10, closed=False, caps=True, xf=None, radius_fn=None):
    """Ống tròn chạy theo `path`. radius_fn(t) với t = 0..1 dọc đường để vuốt thon."""
    n = len(path)
    # Tiếp tuyến
    tang = []
    for i in range(n):
        if closed:
            d = sub(path[(i + 1) % n], path[(i - 1) % n])
        else:
            d = sub(path[min(i + 1, n - 1)], path[max(i - 1, 0)])
        tang.append(norm(d))
    # Khung vận chuyển song song
    ref = (0, 1, 0) if abs(tang[0][1]) < 0.9 else (1, 0, 0)
    nrm = norm(cross(cross(tang[0], ref), tang[0]))
    frames = []
    for i in range(n):
        if i > 0:
            nrm = norm(sub(nrm, mul(tang[i], dot(nrm, tang[i]))))
        frames.append((nrm, norm(cross(tang[i], nrm))))
    lens = [0.0]
    for i in range(1, n):
        lens.append(lens[-1] + length(sub(path[i], path[i - 1])))
    total = lens[-1] + (length(sub(path[0], path[-1])) if closed else 0.0)
    rings = n + (1 if closed else 0)
    verts, ns, uvs, tris = [], [], [], []
    for i in range(rings):
        ii = i % n
        p = path[ii]
        a, b = frames[ii]
        t = (lens[ii] if i < n else total) / max(total, 1e-9)
        r = radius * (radius_fn(t) if radius_fn else 1.0)
        for k in range(sides + 1):
            ang = 2 * math.pi * k / sides
            d = add(mul(a, math.cos(ang)), mul(b, math.sin(ang)))
            verts.append(add(p, mul(d, r)))
            ns.append(d)
            uvs.append((lens[ii] if i < n else total, 2 * math.pi * radius * k / sides))
    w = sides + 1
    for i in range(rings - 1):
        for k in range(sides):
            a = i * w + k
            tris.append((a, a + 1, a + w + 1))
            tris.append((a, a + w + 1, a + w))
    mesh.add(slot, verts, ns, uvs, tris, xf)
    if caps and not closed:
        for end, sign in ((0, -1), (n - 1, 1)):
            p = path[end]
            a, b = frames[end]
            t = 0.0 if end == 0 else 1.0
            r = radius * (radius_fn(t) if radius_fn else 1.0)
            nn = mul(tang[end], sign)
            cv = [p] + [add(p, mul(add(mul(a, math.cos(2 * math.pi * k / sides)),
                                       mul(b, math.sin(2 * math.pi * k / sides))), r)) for k in range(sides)]
            cuv = [(0.0, 0.0)] + [(r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides))
                                  for k in range(sides)]
            ct = []
            for k in range(sides):
                k2 = (k + 1) % sides
                ct.append((0, k + 1, k2 + 1) if sign > 0 else (0, k2 + 1, k + 1))
            mesh.add(slot, cv, [nn] * len(cv), cuv, ct, xf)
    return mesh


def arc(center, radius, a0, a1, segs, plane="xy"):
    """Danh sách điểm trên cung tròn (độ)."""
    out = []
    for k in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * k / segs)
        c, s = math.cos(a) * radius, math.sin(a) * radius
        if plane == "xy":
            out.append((center[0] + c, center[1] + s, center[2]))
        elif plane == "xz":
            out.append((center[0] + c, center[1], center[2] + s))
        else:
            out.append((center[0], center[1] + c, center[2] + s))
    return out


# ---------------------------------------------------------------------------
# Khối tiện (xoay quanh trục Y) và đùn biên dạng 2D
# ---------------------------------------------------------------------------

def lathe(mesh, slot, profile, segs=24, xf=None, a0=0.0, a1=360.0, smooth=True):
    """profile: danh sách (bán kính, y) từ dưới lên. Mặt quay ra ngoài."""
    closed = abs(a1 - a0) >= 359.9
    n = len(profile)
    # Pháp tuyến 2D của biên dạng (trơn)
    pn = []
    for i in range(n):
        r0, y0 = profile[max(i - 1, 0)]
        r1, y1 = profile[min(i + 1, n - 1)]
        dr, dy = r1 - r0, y1 - y0
        l = math.hypot(dr, dy) or 1.0
        pn.append((dy / l, -dr / l))
    lens = [0.0]
    for i in range(1, n):
        lens.append(lens[-1] + math.hypot(profile[i][0] - profile[i - 1][0], profile[i][1] - profile[i - 1][1]))
    rmax = max(p[0] for p in profile) or 0.01
    verts, ns, uvs, tris = [], [], [], []
    for k in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * k / segs)
        c, s = math.cos(a), math.sin(a)
        for i, (r, y) in enumerate(profile):
            verts.append((r * c, y, -r * s))
            ns.append(norm((pn[i][0] * c, pn[i][1], -pn[i][0] * s)))
            uvs.append((rmax * math.radians(a1 - a0) * k / segs, lens[i]))
    for k in range(segs):
        for i in range(n - 1):
            a = k * n + i
            b = a + n
            tris.append((a, b, b + 1))
            tris.append((a, b + 1, a + 1))
    mesh.add(slot, verts, ns, uvs, tris, xf)
    return mesh


def extrude(mesh, slot, profile, z0, z1, xf=None, closed=False, smooth=False, caps=False, uv_offset=0.0):
    """Đùn biên dạng 2D (x, y) dọc trục Z từ z0 đến z1. Biên dạng chạy ngược chiều kim đồng hồ
    (nhìn từ +Z) thì mặt quay ra ngoài."""
    n = len(profile)
    segs = n if closed else n - 1
    verts, ns, uvs, tris = [], [], [], []
    acc = uv_offset
    if smooth:
        en = []
        for i in range(segs):
            a, b = profile[i], profile[(i + 1) % n]
            dx, dy = b[0] - a[0], b[1] - a[1]
            l = math.hypot(dx, dy) or 1.0
            en.append((dy / l, -dx / l))
        vn = []
        for i in range(n):
            e = []
            if closed or i > 0:
                e.append(en[(i - 1) % segs])
            if closed or i < n - 1:
                e.append(en[i % segs])
            sx = sum(q[0] for q in e)
            sy = sum(q[1] for q in e)
            l = math.hypot(sx, sy) or 1.0
            vn.append((sx / l, sy / l))
        lens = [acc]
        for i in range(1, n + (1 if closed else 0)):
            a, b = profile[i - 1], profile[i % n]
            lens.append(lens[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        cnt = n + (1 if closed else 0)
        for i in range(cnt):
            x, y = profile[i % n]
            nn = (vn[i % n][0], vn[i % n][1], 0.0)
            verts += [(x, y, z0), (x, y, z1)]
            ns += [nn, nn]
            uvs += [(z0, lens[i]), (z1, lens[i])]
        for i in range(cnt - 1):
            a = i * 2
            tris.append((a, a + 2, a + 3) if z1 > z0 else (a, a + 3, a + 2))
            tris.append((a, a + 3, a + 1) if z1 > z0 else (a, a + 1, a + 3))
    else:
        for i in range(segs):
            a, b = profile[i], profile[(i + 1) % n]
            dx, dy = b[0] - a[0], b[1] - a[1]
            l = math.hypot(dx, dy) or 1.0
            nn = (dy / l, -dx / l, 0.0)
            base = len(verts)
            verts += [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)]
            ns += [nn] * 4
            uvs += [(z0, acc), (z0, acc + l), (z1, acc + l), (z1, acc)]
            acc += l
            if z1 > z0:
                tris += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
            else:
                tris += [(base, base + 2, base + 1), (base, base + 3, base + 2)]
    mesh.add(slot, verts, ns, uvs, tris, xf)
    if caps:
        polygon(mesh, slot, [(x, y, z1) for x, y in profile], (0, 0, 1 if z1 > z0 else -1), xf)
        polygon(mesh, slot, [(x, y, z0) for x, y in reversed(profile)], (0, 0, -1 if z1 > z0 else 1), xf)
    return mesh


def polygon(mesh, slot, pts, normal, xf=None):
    """Đa giác phẳng (lõm cũng được) - tam giác hóa kiểu cắt tai. pts ngược chiều kim đồng hồ quanh normal."""
    n = norm(normal)
    a = norm(cross(n, (0, 1, 0) if abs(n[1]) < 0.9 else (1, 0, 0)))
    b = cross(n, a)
    p2 = [(dot(p, a), dot(p, b)) for p in pts]
    idx = list(range(len(pts)))
    tris = []

    def area2(i, j, k):
        return (p2[j][0] - p2[i][0]) * (p2[k][1] - p2[i][1]) - (p2[k][0] - p2[i][0]) * (p2[j][1] - p2[i][1])

    # Đảm bảo chiều dương
    s = sum(p2[i][0] * p2[(i + 1) % len(p2)][1] - p2[(i + 1) % len(p2)][0] * p2[i][1] for i in range(len(p2)))
    if s < 0:
        idx.reverse()
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        m = len(idx)
        for e in range(m):
            i, j, k = idx[(e - 1) % m], idx[e], idx[(e + 1) % m]
            if area2(i, j, k) <= 1e-12:
                continue
            ok = True
            for q in idx:
                if q in (i, j, k):
                    continue
                if (area2(i, j, q) >= 0 and area2(j, k, q) >= 0 and area2(k, i, q) >= 0):
                    ok = False
                    break
            if ok:
                tris.append((i, j, k))
                idx.pop(e)
                break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    uvs = [(q[0], q[1]) for q in p2]
    mesh.add(slot, list(pts), [n] * len(pts), uvs, tris, xf)
    return mesh


def quad(mesh, slot, p0, p1, p2, p3, xf=None, uv_scale=1.0):
    """Tứ giác phẳng p0..p3 ngược chiều kim đồng hồ."""
    n = norm(cross(sub(p1, p0), sub(p3, p0)))
    w = length(sub(p1, p0))
    h = length(sub(p3, p0))
    uvs = [(0, 0), (w * uv_scale, 0), (w * uv_scale, h * uv_scale), (0, h * uv_scale)]
    mesh.add(slot, [p0, p1, p2, p3], [n] * 4, uvs, [(0, 1, 2), (0, 2, 3)], xf)
    return mesh


def ellipsoid(mesh, slot, radii, nu=20, nv=12, xf=None, deform=None, uv_fn=None, v_range=(0.0, 1.0)):
    """Elipxoit (u quanh trục Y, v từ đáy lên đỉnh)."""
    rx, ry, rz = radii

    def fn(u, v):
        th = 2 * math.pi * u
        ph = math.pi * (v - 0.5)
        p = (rx * math.cos(ph) * math.sin(th), ry * math.sin(ph), rz * math.cos(ph) * math.cos(th))
        if deform:
            p = deform(p)
        return p

    return grid(mesh, slot, fn, nu, nv, (0.0, 1.0), v_range, uv_fn=uv_fn, xf=xf, wrap_u=True)
