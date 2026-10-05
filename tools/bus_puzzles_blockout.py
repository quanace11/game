#!/usr/bin/env python3
"""Sinh đồ vật câu đố chương 2 "Chuyến xe không về bến": scenes/bus/BusPuzzles.tscn

Chạy:  python3 tools/bus_puzzles_blockout.py

Scene này được instance vào scenes/bus/BusRide.tscn, chồng đúng tọa độ lên
scenes/levels/Bus.tscn. Hai nhóm, BusWreckDirector bật/tắt theo lớp xe:
- Wreck: đồ trong xác xe (đèn bão quấn bùa, hộp tôn bác Tư, chậu sắt hóa vàng...).
- Night: Đêm 1999, hình nhân giấy của những người trên chuyến xe và đồ của họ.

Mỗi vật tương tác là Area3D gắn Interactable.gd; BusWreckDirector tìm theo tên node.
Hình dạng đồ vật là mesh thủ tục ở tools/prop_models.py (hình nhân: tools/people_models.py).

Thêm một vật tương tác mới:
    a = p.area("TenNode", nhom, vi_tri, kich_thuoc_hop_va_cham, "item_id", "KHOA_TEN", "KHOA_GOI_Y")
    p.prop("Model", a, "pz_<mesh>", {"slot": vat_lieu, ...}, (x, y, z))   # hoặc sc.mesh(...) khối đơn giản
    p.glint(a, (0, 0.25, 0))   # (tùy chọn) vũng sáng nhỏ để vật bắt sáng trong bóng tối
LƯU Ý: chạy lại script sẽ GHI ĐÈ scenes/bus/BusPuzzles.tscn.
"""

import random

import bus_models
import people_models
import prop_models
from level_blockout import CC0, Scene, basis_mul, basis_scale, basis_x, basis_y, basis_z, color, f, vec3, xform
from bus_blockout import (BOARD_POS, LAMP_POS, NAM_SEAT, HUNG_SEAT, NUMBERED_SEATS, RACK_Y, ROWS, SEAT_Y, Z_FRONT, place,
                          seat_xz, storm_lamp)
from people_models import effigy_materials, seated_effigy, standing_effigy

BASIN_POS = (0.0, 0.0, 3.85)
TIN_FLOOR = (-0.38, 0.07, -0.98)        # hộp bánh quy dưới chân bà Năm
TIN_RACK = (-1.0, RACK_Y + 0.07, ROWS[3])  # trên giá hành lý, ngay trên ghế bà
BAY_POS = (0.85, 0.2, -4.05)            # chú Bảy đứng trên bậc cửa
TU_POS = (-0.7, 0.05, -4.0)

# Màu ánh sáng "bắt sáng" của từng lớp: xác xe ánh trăng xám lạnh lọt qua kính vỡ, Đêm 1999 ánh đèn dầu.
GLINT_WRECK = (0.85, 0.88, 1.0)
GLINT_NIGHT = (1.0, 0.78, 0.5)
GLINT_NIGHT_ENERGY = 0.18


class Puzzles:
    def __init__(self):
        self.sc = Scene("BusPuzzles")
        self.ia = self.sc.ext_res("Script", "res://scripts/interaction/Interactable.gd")
        self.shapes = {}

    def shape(self, size):
        key = tuple(round(s, 3) for s in size)
        if key not in self.shapes:
            rid = "Shape_%d" % (len(self.shapes) + 1)
            self.sc.sub_res("BoxShape3D", rid, [("size", vec3(size))])
            self.shapes[key] = rid
        return self.shapes[key]

    def area(self, name, parent, pos, size, item_id, name_key, prompt_key="PROMPT_LOOK_CLOSER", rot_y=0.0,
             extra=(), visible=True):
        props = [("transform", xform(pos, rot_y))]
        if not visible:
            props.append(("visible", "false"))
        props += [("script", 'ExtResource("%s")' % self.ia), ("item_id", '&"%s"' % item_id),
                  ("display_name_key", '"%s"' % name_key)]
        if prompt_key:
            props.append(("prompt_text_key", '"%s"' % prompt_key))
        props += list(extra)
        path = self.sc.node(name, "Area3D", parent, props)
        self.sc.node("CollisionShape3D", "CollisionShape3D", path, [("shape", 'SubResource("%s")' % self.shape(size))])
        return path

    def prop(self, name, parent, model, mats, pos=(0, 0, 0), basis=None, rot_y=0.0, shadow=1):
        """Đặt mesh tools/prop_models.py; mats: slot -> vật liệu (thiếu slot thì báo lỗi)."""
        return place(self.sc, name, parent, model, mats, pos, basis, rot_y, shadow)

    def glint(self, parent, pos, energy=0.45, rng=0.75, col=GLINT_WRECK):
        """Vũng sáng nhỏ không đổ bóng: đủ để vật nổi khỏi bóng tối, không thành đèn đánh dấu."""
        return self.sc.node("Glint", "OmniLight3D", parent, [
            ("transform", xform(pos)), ("light_color", color(col)), ("light_energy", f(energy)),
            ("light_specular", "0.8"), ("omni_range", f(rng)), ("omni_attenuation", "1.6")])

    def mat(self, name, rgb=(1, 1, 1), rough=0.7, metal=0.0, tex=None, png=None, uv=None, uv_off=None, alpha=None,
            scissor=False, cull=True, glint=0.0, rim=0.0, normal_png=None, normal=1.0):
        """Vật liệu đồ vật.
        tex: bộ CC0 (assets/textures/<tex>_*.jpg), UV mesh tính bằng mét nên mặc định uv = 1/kích thước thật.
        png: ảnh vẽ (đường dẫn dưới assets/textures/). glint: tự phát sáng rất nhẹ theo màu albedo
        (giấy, kính, kim loại bóng vẫn đọc được trong bóng tối). rim: viền sáng ở mép khi có đèn chiếu."""
        sc = self.sc
        if name in sc.materials:
            return sc.materials[name]
        props = []
        kind = "StandardMaterial3D"
        if alpha is not None or scissor:
            props.append(("transparency", "2" if scissor else "1"))
            if scissor:
                props.append(("alpha_scissor_threshold", "0.4"))
        if not cull:
            props.append(("cull_mode", "2"))
        props.append(("albedo_color", color(tuple(rgb) + ((alpha,) if alpha is not None else ()))))
        tex_rid = None
        if tex:
            kind = "ORMMaterial3D"
            tex_rid = sc.ext_res("Texture2D", "res://assets/textures/%s_albedo.jpg" % tex)
            n = sc.ext_res("Texture2D", "res://assets/textures/%s_normal.jpg" % tex)
            o = sc.ext_res("Texture2D", "res://assets/textures/%s_orm.jpg" % tex)
            props += [("albedo_texture", 'ExtResource("%s")' % tex_rid), ("orm_texture", 'ExtResource("%s")' % o),
                      ("ao_enabled", "true"), ("ao_light_affect", "0.2")]
            if uv is None:
                k = 1.0 / CC0[tex]["size_m"]
                uv = (k, k)
            props += [("metallic", f(metal)), ("roughness", f(rough)),
                      ("normal_enabled", "true"), ("normal_scale", f(normal)), ("normal_texture", 'ExtResource("%s")' % n)]
        else:
            if png:
                tex_rid = sc.ext_res("Texture2D", "res://assets/textures/" + png)
                props.append(("albedo_texture", 'ExtResource("%s")' % tex_rid))
            if metal:
                props.append(("metallic", f(metal)))
            props.append(("roughness", f(rough)))
            if normal_png:
                n = sc.ext_res("Texture2D", "res://assets/textures/" + normal_png)
                props += [("normal_enabled", "true"), ("normal_scale", f(normal)),
                          ("normal_texture", 'ExtResource("%s")' % n)]
        if rim:
            props += [("rim_enabled", "true"), ("rim", f(rim)), ("rim_tint", "0.6")]
        if glint:
            props += [("emission_enabled", "true"), ("emission", color(rgb)), ("emission_energy_multiplier", f(glint))]
            if tex_rid:
                props += [("emission_operator", "1"), ("emission_texture", 'ExtResource("%s")' % tex_rid)]
        if uv:
            props.append(("uv1_scale", vec3((uv[0], uv[1], 1))))
        if uv_off:
            props.append(("uv1_offset", vec3((uv_off[0], uv_off[1], 0))))
        props.append(("texture_filter", "5"))
        rid = sc.sub_res(kind, "Mat_" + name, props)
        sc.materials[name] = rid
        return rid


def pages(*keys):
    return ("pages", 'Array[String]([%s])' % ", ".join('"%s"' % k for k in keys))


def desc(key):
    return ("description_key", '"%s"' % key)


def build_models():
    """Sinh lại mọi mesh .obj mà scene này dùng (xe, người/hình nhân, đồ vật)."""
    bus_models.build_all()
    people_models.build_all()
    prop_models.build_all()


def build(models=True):
    if models:
        build_models()
    p = Puzzles()
    sc = p.sc
    rng = random.Random(14041999)
    m = p.mat

    # --- Vật liệu chung ---
    iron = m("PzIron", (0.16, 0.14, 0.13), 0.6, 0.7, rim=0.3)
    tin_new = m("PzTin", (0.7, 0.68, 0.62), 0.35, 0.85, glint=0.03, rim=0.3)
    brass = m("PzBrass", (0.75, 0.56, 0.28), 0.35, 1.0, glint=0.08, rim=0.4)
    fire = sc.mat("PzFire", (1.0, 0.55, 0.15), 0.5, emission=(1.0, 0.45, 0.1), energy=5.0, unshaded=True)
    glow_paper = sc.mat("PzGlowPaper", (1.0, 0.95, 0.7), 0.6, emission=(1.0, 0.8, 0.45), energy=1.6, alpha=0.75)
    paper_old = m("PzPaperOld", (0.86, 0.8, 0.66), 0.95, png="bus/paper_crease_albedo.png", cull=False, glint=0.12,
                  normal_png="bus/paper_crease_normal.png", normal=0.6)
    red_string = m("PzString", (0.7, 0.08, 0.06), 0.8, glint=0.05)
    window_glass = m("PzDeckWindow", (0.15, 0.14, 0.13), 0.08, alpha=0.55, cull=False)

    # =======================================================================
    # XÁC XE
    # =======================================================================
    wreck = sc.empty("Wreck")
    rust_m = m("PzRustMetal", (0.95, 0.85, 0.78), 0.9, 0.3, tex="paint_flaking", rim=0.25)
    rust_heavy = m("PzRustHeavy", (0.9, 0.8, 0.75), 0.95, 0.2, tex="rust_heavy", rim=0.2)
    soot_glass = m("PzSootGlass", (0.3, 0.27, 0.2), 0.25, alpha=0.62, cull=False, png="bus/glass_grime.png",
                   uv=(3, 3), glint=0.05)

    # Đèn bão quấn bùa treo trên móc ở vách sau. Bùa vàng quấn kín bầu kính, đuôi bùa rủ xuống.
    a = p.area("Lamp", wreck, LAMP_POS, (0.26, 0.4, 0.26), "storm_lamp", "OBJ_STORM_LAMP_NAME", "PROMPT_LAMP_UNWRAP")
    lamp_metal = m("PzLampMetal", (0.42, 0.32, 0.24), 0.8, 0.5, tex="paint_flaking", rim=0.35, glint=0.03)
    storm_lamp(sc, "Model", a, (0, -0.13, 0), lamp_metal, soot_glass)
    tal = sc.empty("Talisman", a, (0, -0.13, 0))
    p.prop("Wrap", tal, "pz_talisman_wrap", {
        "paper": m("PzTalisman", (1.0, 0.92, 0.7), 0.85, png="bus/prop_talisman.png", scissor=True, cull=False,
                   glint=0.06, rim=0.3),
        "string": red_string}, shadow=0)
    p.prop("Hook", a, "pz_lamp_hook", {"iron": iron, "wire": iron}, (0, 0.215, 0))
    p.glint(a, (-0.1, 0.12, -0.3), 0.35, 0.8)

    # Chai dầu hỏa còn nguyên, lăn khỏi chiếc giỏ đổ nghiêng của bà Năm.
    g = sc.empty("Basket", wreck, (-1.1, 0.15, -0.8), basis=basis_mul(basis_y(-20), basis_x(-70)))
    sc.model("Wicker", g, "wicker_basket_01", (0, 0, 0))
    a = p.area("Kerosene", wreck, (-0.9, 0.1, -0.95), (0.22, 0.22, 0.22), "kerosene", "ITEM_KEROSENE_NAME",
               "PROMPT_ACTION_PICKUP", extra=[desc("ITEM_KEROSENE_DESC")])
    p.prop("Bottle", a, "pz_kerosene", {
        "glass": m("PzBottleGlass", (0.62, 0.78, 0.66), 0.06, alpha=0.4, cull=False, glint=0.1, rim=0.6),
        "oil": m("PzKerosene", (0.92, 0.66, 0.24), 0.1, alpha=0.8, glint=0.35),
        "cork": m("PzCorkPaper", (0.72, 0.6, 0.45), 0.95, png="bus/paper_crease_albedo.png", glint=0.08),
        "label": m("PzBottleLabel", (1, 1, 1), 0.9, png="bus/prop_label.png", cull=False, glint=0.12)},
        (-0.07, -0.06, -0.03), basis=basis_mul(basis_y(35), basis_z(-78)))
    p.glint(a, (0.12, 0.25, -0.1), 0.3, 0.65)

    # Cuộn chỉ bông kẹt trong khe ghế bà Năm, đầu chỉ trắng thò ra.
    nx, nz = seat_xz(NAM_SEAT)
    a = p.area("Thread", wreck, (nx, SEAT_Y + 0.08, nz + 0.17), (0.18, 0.14, 0.14), "cotton_thread",
               "ITEM_COTTON_THREAD_NAME", "PROMPT_ACTION_PICKUP", extra=[desc("ITEM_COTTON_THREAD_DESC")])
    p.prop("Spool", a, "pz_spool", {
        "wood": m("PzSpoolWood", (0.62, 0.45, 0.28), 0.7, tex="wood_dark", glint=0.05),
        "cotton": m("PzCotton", (0.95, 0.93, 0.86), 1.0, png="bus/paper_crease_albedo.png", uv=(8, 8), glint=0.3,
                    rim=0.5)}, (0, -0.01, 0), rot_y=15)
    p.glint(a, (0.05, 0.2, -0.15), 0.4, 0.6)

    # Hộp tôn sơn xanh của bác Tư trên taplô: khóa đồng ba vòng số quay về phía người chơi, nắp khắc "Số xe".
    # Bản lề nắp ở mép phía kính lái để tween rotation.x = -105° của BusWreckDirector lật nắp lên.
    a = p.area("TinBox", wreck, (0.25, 1.14, Z_FRONT + 0.38), (0.3, 0.2, 0.26), "driver_tin_box",
               "OBJ_DRIVER_TIN_BOX_NAME", "PROMPT_TIN_BOX_LOCK")
    tin_box = m("PzTinBox", (0.8, 0.92, 0.8), 0.8, 0.0, tex="paint_worn", uv=(4, 4), rim=0.35, glint=0.05)
    dial = m("PzDial", (1, 1, 1), 0.4, 0.6, png="bus/prop_dial.png", uv=(12.7, 40.0), uv_off=(0.0, -0.2),
             glint=0.12, rim=0.3)
    p.prop("Base", a, "pz_tin_box", {"tin": tin_box, "brass": brass, "dial": dial})
    lid = sc.empty("Lid", a, (0, 0.035, -0.07))
    p.prop("LidPlate", lid, "pz_tin_lid", {"tin": tin_box})
    sc.node("Engraving", "Label3D", lid, [
        ("transform", xform((0, 0.0125, 0.0725), basis=basis_x(-90))), ("pixel_size", "0.0008"),
        ("modulate", color((0.12, 0.08, 0.05))), ("outline_size", "0"), ("text", '"OBJ_TIN_BOX_ENGRAVING"'),
        ("font_size", "40"), ("alpha_cut", "1")])
    contents = sc.empty("Contents", a, props=[("visible", "false")])
    p.prop("MatchJar", contents, "pz_match_jar", {
        "glass": m("PzJarGlass", (0.8, 0.85, 0.8), 0.05, alpha=0.35, cull=False, rim=0.5),
        "lid": tin_new, "stick": m("PzMatchStick", (0.85, 0.72, 0.5), 0.9),
        "head": m("PzMatchHead", (0.55, 0.08, 0.06), 0.7)}, (-0.06, 0.0, 0.01))
    p.prop("License", contents, "pz_paper_sheet", {"paper": paper_old}, (0.03, -0.025, 0.02),
           basis=basis_mul(basis_y(8), basis_scale(0.08, 0.08, 0.055)))
    p.prop("Ledger", contents, "pz_book", {
        "cover": m("PzLedger", (0.42, 0.14, 0.1), 0.8, tex="vinyl", uv=(6, 6)), "pages": paper_old},
        (0.05, -0.02, -0.02), rot_y=-6)
    p.glint(a, (-0.1, 0.2, -0.2), 0.45, 0.7)

    # Giấy phép lưu hành nhòe nước, chỉ còn đọc được "...85".
    a = p.area("Permit", wreck, (-0.15, 1.115, Z_FRONT + 0.48), (0.18, 0.06, 0.14), "permit", "OBJ_PERMIT_NAME",
               "PROMPT_ACTION_READ", extra=[pages("DOC_PERMIT")])
    p.prop("Paper", a, "pz_paper_sheet", {
        "paper": m("PzPermit", (1, 1, 1), 0.9, png="bus/prop_permit.png", cull=False, glint=0.15, rim=0.3)},
        (0, -0.008, 0), basis=basis_mul(basis_y(-12), basis_scale(0.13, 0.13, 0.09)))

    # Decal số xe dán phía ngoài kính lái (chỉ để xem kỹ; chữ là Label3D trong Bus.tscn).
    p.area("NumberDecal", wreck, (0.62, 1.14, Z_FRONT - 0.0), (0.34, 0.2, 0.06), "number_decal",
           "OBJ_NUMBER_DECAL_NAME")

    # Hộp bánh quy: gỉ thủng dưới sàn, hoặc nằm khô trên giá nếu đã được dời lên ở Đêm 1999.
    a = p.area("TinRusted", wreck, TIN_FLOOR, (0.24, 0.16, 0.24), "biscuit_tin_rusted", "OBJ_BISCUIT_TIN_NAME")
    tin_rust = {"side": rust_heavy, "rim": rust_heavy, "top": rust_heavy}
    p.prop("Can", a, "pz_biscuit_can", tin_rust, (0, -0.07, 0), rot_y=20)
    p.prop("Lid", a, "pz_biscuit_lid", tin_rust, (0.01, 0.0, 0.0), basis=basis_mul(basis_y(40), basis_z(6)))
    sc.mesh("Hole", a, "cyl", (0.04, 0.04, 0.005, 8), (0.03, 0.022, 0.02), m("PzHole", (0.03, 0.025, 0.02), 1.0))
    p.glint(a, (0.1, 0.25, 0.05), 0.35, 0.6)
    a = p.area("TinDry", wreck, TIN_RACK, (0.3, 0.18, 0.3), "biscuit_tin_dry", "OBJ_BISCUIT_TIN_NAME",
               "PROMPT_TIN_OPEN", visible=False, extra=[pages("DOC_PATTERN_BOOK_1", "DOC_PATTERN_BOOK_2",
                                                              "DOC_PATTERN_BOOK_3")])
    tin_dry = {"side": m("PzTinDrySide", (0.75, 0.55, 0.5), 0.6, 0.5, png="bus/prop_biscuit_side.png",
                         uv=(1.59, 14.1), rim=0.3, glint=0.06),
               "rim": rust_m,
               "top": m("PzTinDryTop", (0.72, 0.55, 0.5), 0.6, 0.5, png="bus/prop_biscuit_lid.png", uv=(5.2, 5.2),
                        uv_off=(0.5, 0.5), rim=0.3, glint=0.06)}
    p.prop("Can", a, "pz_biscuit_can", tin_dry, (0, -0.065, 0), rot_y=20)
    p.prop("Lid", a, "pz_biscuit_lid", tin_dry, (0, 0.007, 0), rot_y=20)

    # Chiếc guốc mộc mục của bà Năm, quai còn hằn hoa mai.
    a = p.area("Clog", wreck, (-0.62, 0.03, -0.8), (0.18, 0.1, 0.24), "rotten_clog", "OBJ_ROTTEN_CLOG_NAME",
               rot_y=-25)
    p.prop("Clog", a, "pz_clog", {
        "wood": m("PzClogWood", (0.7, 0.62, 0.55), 0.95, tex="wood_weathered", glint=0.05, rim=0.3),
        "strap": m("PzStrapRotten", (0.32, 0.2, 0.16), 0.9, tex="vinyl", uv=(8, 8)),
        "nail": iron}, (0, -0.015, 0))
    p.glint(a, (0.0, 0.25, -0.1), 0.3, 0.55)

    # Chậu sắt cuối xe: chỗ hóa vàng.
    a = p.area("Basin", wreck, BASIN_POS, (0.45, 0.3, 0.45), "iron_basin", "OBJ_IRON_BASIN_NAME", "PROMPT_BASIN")
    p.prop("Bowl", a, "pz_basin", {"iron": m("PzBasinIron", (0.55, 0.47, 0.4), 0.9, 0.3, tex="paint_flaking", rim=0.25), "ash": m("PzAsh", (0.22, 0.21, 0.2), 1.0, tex="concrete_damp")})
    flames = sc.empty("Fire", a, props=[("visible", "false")])
    for k in range(5):
        sc.mesh("Flame", flames, "sphere", (0.04, 0.16 + 0.04 * (k % 2)),
                (0.07 * (k % 3 - 1), 0.12, 0.06 * ((k + 1) % 3 - 1)), fire, shadow=False)
    sc.node("Light", "OmniLight3D", flames, [
        ("transform", xform((0, 0.35, 0))), ("light_color", color((1.0, 0.55, 0.2))), ("light_energy", "2.5"),
        ("omni_range", "4.0"), ("shadow_enabled", "true")])
    p.glint(a, (0.0, 0.5, -0.2), 0.45, 0.9)

    # Đồ của Hùng ở xác xe: vở còn một trang khô (gợi ý bảng lộ trình) ló ra khỏi cặp mục,
    # khung đài gỉ trên ghế (mesh trong Bus.tscn).
    hx, hz = seat_xz(HUNG_SEAT)
    a = p.area("Notebook", wreck, (hx + 0.12, 0.14, hz - 0.3), (0.3, 0.26, 0.2), "hung_notebook",
               "OBJ_HUNG_NOTEBOOK_NAME", "PROMPT_ACTION_READ", extra=[pages("DOC_HUNG_NOTEBOOK")])
    p.prop("Book", a, "pz_open_notebook", {
        "pages": m("PzNotebookPages", (0.88, 0.84, 0.72), 0.95, png="bus/paper_crease_albedo.png", cull=False,
                   glint=0.18, rim=0.3),
        "cover": m("PzNotebookCover", (0.3, 0.42, 0.55), 0.9, tex="fabric", uv=(6, 6))},
        (-0.02, -0.125, -0.13), basis=basis_mul(basis_y(70), basis_z(-6)))
    p.glint(a, (0.0, 0.18, -0.25), 0.35, 0.6)
    p.area("DeckRusted", wreck, (hx, 0.56, hz - 0.02), (0.36, 0.16, 0.14), "deck_rusted", "OBJ_DECK_RUSTED_NAME")

    # =======================================================================
    # ĐÊM 1999
    # =======================================================================
    night = sc.empty("Night", props=[("visible", "false")])
    mu_coi = m("PzMuCoi", (0.36, 0.42, 0.24), 0.9, tex="fabric", uv=(6, 6), rim=0.3)
    herb = {"paper": m("PzHerbPaper", (0.82, 0.7, 0.52), 0.95, png="bus/paper_crease_albedo.png", uv=(4, 4),
                       normal_png="bus/paper_crease_normal.png", glint=0.03, rim=0.3),
            "string": red_string}
    dieu = {"bamboo": m("PzBamboo", (0.66, 0.54, 0.3), 0.5, png="bus/paper_crease_albedo.png", uv=(2, 12),
                        rim=0.4, glint=0.04),
            "node": m("PzBambooNode", (0.42, 0.32, 0.16), 0.6),
            "metal": brass}

    def effigy(name, seat, mats, **kw):
        x, z = seat_xz(seat)
        return seated_effigy(sc, name, night, (x, 0.0, z), mats, **kw)

    # Ba hành khách thường (không chấp niệm riêng): ghế 03, 04, 05. Đồ của họ văng xuống sàn.
    looks = {
        "03": dict(mats=effigy_materials(sc, "P03", (0.3, 0.58, 0.38), (0.14, 0.15, 0.2), "man"), style="shirt",
                   hair="khan"),
        "04": dict(mats=effigy_materials(sc, "P04", (0.5, 0.33, 0.2), (0.2, 0.24, 0.45), "old_man"), style="ao_dai"),
        "05": dict(mats=effigy_materials(sc, "P05", (0.88, 0.42, 0.52), (0.93, 0.9, 0.84), "woman"),
                   style="ao_dai", hair="bun"),
    }
    for num in ("03", "04", "05"):
        g = effigy("Passenger" + num, NUMBERED_SEATS[num], **looks[num])
        x, z = seat_xz(NUMBERED_SEATS[num])
        p.area("Seat" + num, night, (x, 0.95, z), (0.34, 0.75, 0.36), "passenger_" + num, "OBJ_PASSENGER_NAME",
               "PROMPT_PASSENGER")
        held = sc.empty("Held", g, props=[("visible", "true")])
        hn = sc.empty("non_coi", held, (0, 0.72, -0.25), props=[("visible", "false")])
        place(sc, "Hat", hn, "hat_mu_coi", {"hat": mu_coi}, (0, -0.05, 0), basis=basis_x(-12))
        ht = sc.empty("goi_thuoc_bac", held, (0, 0.7, -0.27), props=[("visible", "false")])
        p.prop("Pack", ht, "pz_herb_pack", herb)
        hd = sc.empty("dieu_cay", held, (0.12, 0.75, -0.25), props=[("visible", "false")])
        p.prop("Pipe", hd, "pz_dieu_cay", dieu, (0, 0.15, 0), basis=basis_x(-15))
    # Đồ rơi trên sàn lối đi.
    a = p.area("NonCoi", night, (-0.15, 0.06, -1.75), (0.36, 0.14, 0.36), "non_coi", "ITEM_NON_COI_NAME",
               "PROMPT_ACTION_PICKUP", extra=[desc("ITEM_NON_COI_DESC")])
    place(sc, "Hat", a, "hat_mu_coi", {"hat": mu_coi}, (0, 0.11, 0), basis=basis_z(160))
    p.glint(a, (0.1, 0.35, 0.1), GLINT_NIGHT_ENERGY, 0.7, GLINT_NIGHT)
    a = p.area("ThuocBac", night, (0.18, 0.06, -2.55), (0.28, 0.14, 0.24), "goi_thuoc_bac", "ITEM_THUOC_BAC_NAME",
               "PROMPT_ACTION_PICKUP", rot_y=30, extra=[desc("ITEM_THUOC_BAC_DESC")])
    p.prop("Pack", a, "pz_herb_pack", herb, (0, -0.01, 0), basis=basis_z(4))
    p.glint(a, (0.0, 0.3, 0.1), GLINT_NIGHT_ENERGY, 0.6, GLINT_NIGHT)
    a = p.area("DieuCay", night, (-0.22, 0.04, -0.95), (0.2, 0.12, 0.6), "dieu_cay", "ITEM_DIEU_CAY_NAME",
               "PROMPT_ACTION_PICKUP", rot_y=12, extra=[desc("ITEM_DIEU_CAY_DESC")])
    p.prop("Pipe", a, "pz_dieu_cay", dieu, (0, -0.012, 0), basis=basis_x(90))
    p.glint(a, (0.1, 0.3, 0.0), GLINT_NIGHT_ENERGY, 0.6, GLINT_NIGHT)

    # Bà Năm: chân trần, búi tóc, nón lá đặt ngửa trên đùi (mặt trong vành nón có tên bằng mực tím).
    effigy("BaNam", NAM_SEAT, effigy_materials(sc, "Nam", (0.5, 0.32, 0.2), (0.24, 0.16, 0.3), "old_woman"),
           style="ao_dai", hair="bun", feet="bare", lean=-4)
    p.area("Nam", night, (nx, 1.0, nz + 0.02), (0.34, 0.6, 0.3), "ba_nam", "OBJ_BA_NAM_NAME", "PROMPT_BA_NAM")
    a = p.area("Hat", night, (nx, 0.72, nz - 0.25), (0.34, 0.12, 0.3), "nam_hat", "OBJ_NAM_HAT_NAME",
               "PROMPT_LOOK_CLOSER", extra=[pages("DOC_NAM_HAT")])
    place(sc, "NonLa", a, "hat_non_la", {"hat": m("PzNonLa", (1.0, 0.94, 0.78), 0.8, tex="bamboo_weave", uv=(5, 5),
                                                 cull=False, rim=0.4, glint=0.06)},
          (0, 0.06, 0.02), basis=basis_x(-168))
    a = p.area("Tin", night, TIN_FLOOR, (0.24, 0.16, 0.24), "biscuit_tin", "ITEM_BISCUIT_TIN_NAME",
               "PROMPT_ACTION_PICKUP", extra=[desc("ITEM_BISCUIT_TIN_DESC")])
    tin_print = {"side": m("PzTinSide", (1, 1, 1), 0.3, 0.55, png="bus/prop_biscuit_side.png", uv=(1.59, 14.1),
                           rim=0.4, glint=0.08),
                 "rim": m("PzTinGold", (0.82, 0.64, 0.3), 0.3, 0.9, rim=0.4, glint=0.05),
                 "top": m("PzTinTop", (1, 1, 1), 0.3, 0.55, png="bus/prop_biscuit_lid.png", uv=(5.2, 5.2),
                          uv_off=(0.5, 0.5), rim=0.4, glint=0.08)}
    p.prop("Can", a, "pz_biscuit_can", tin_print, (0, -0.07, 0), rot_y=20)
    p.prop("Lid", a, "pz_biscuit_lid", tin_print, (0, 0.002, 0), rot_y=20)
    p.glint(a, (0.1, 0.3, 0.1), GLINT_NIGHT_ENERGY, 0.6, GLINT_NIGHT)
    a = p.area("Rack", night, (TIN_RACK[0], TIN_RACK[1] - 0.02, TIN_RACK[2]), (0.4, 0.16, 0.5), "luggage_rack",
               "OBJ_LUGGAGE_RACK_NAME", "PROMPT_RACK")
    placed = sc.empty("Placed", a, props=[("visible", "false")])
    p.prop("Can", placed, "pz_biscuit_can", tin_print, (0, -0.045, 0), rot_y=20)
    p.prop("Lid", placed, "pz_biscuit_lid", tin_print, (0, 0.027, 0), rot_y=20)
    # Đôi guốc mã mờ sáng cạnh chậu (sau khi hóa vàng ở xác xe), và lọ dầu gió bà để lại.
    # BusWreckDirector chép các MeshInstance3D con của GlowClogs sang chân hình nhân bà Năm.
    a = p.area("GlowClogs", night, (BASIN_POS[0], 0.05, BASIN_POS[2]), (0.3, 0.12, 0.3), "paper_clogs",
               "ITEM_PAPER_CLOGS_NAME", "PROMPT_ACTION_PICKUP", visible=False, extra=[desc("ITEM_PAPER_CLOGS_DESC")])
    for sx in (-1, 1):
        p.prop("Clog", a, "pz_clog", {"wood": glow_paper, "strap": glow_paper, "nail": glow_paper},
               (sx * 0.05, 0, 0), rot_y=sx * 6, shadow=0)
    sc.node("Glow", "OmniLight3D", a, [("transform", xform((0, 0.15, 0))), ("light_color", color((1, 0.8, 0.5))),
                                       ("light_energy", "0.8"), ("omni_range", "1.4")])
    a = p.area("WindOil", night, (nx, SEAT_Y + 0.08, nz - 0.05), (0.14, 0.14, 0.14), "wind_oil",
               "ITEM_WIND_OIL_NAME", "PROMPT_ACTION_PICKUP", visible=False, extra=[desc("ITEM_WIND_OIL_DESC")])
    p.prop("Vial", a, "pz_vial", {
        "glass": m("PzBalmGlass", (0.4, 0.75, 0.55), 0.05, alpha=0.5, cull=False, rim=0.6, glint=0.1),
        "oil": m("PzBalm", (0.3, 0.7, 0.4), 0.1, alpha=0.8, glint=0.3),
        "cap": m("PzBalmCap", (0.95, 0.82, 0.2), 0.35, 0.3, glint=0.1)})

    # Hùng: ôm chiếc đài cát-sét đã "ăn băng", cặp sách dưới chân.
    effigy("Hung", HUNG_SEAT, effigy_materials(sc, "Hung", (0.95, 0.95, 0.92), (0.16, 0.24, 0.5), "boy"),
           style="shirt", head_tilt=-8)
    a = p.area("Deck", night, (hx, 0.72, hz - 0.28), (0.38, 0.2, 0.18), "cassette_deck", "OBJ_CASSETTE_DECK_NAME",
               "PROMPT_DECK")
    p.prop("Body", a, "pz_boombox", {
        "body": m("PzDeckBody", (0.62, 0.62, 0.64), 0.35, 0.6, tex="paint_clean", uv=(3, 3), rim=0.4, glint=0.04),
        "grille": m("PzDeckGrille", (1, 1, 1), 0.6, png="bus/prop_grille.png", uv=(12, 12), uv_off=(0.5, 0.5)),
        "chrome": m("PzChrome", (0.85, 0.85, 0.86), 0.18, 1.0, rim=0.4, glint=0.05),
        "window": window_glass,
        "tape": m("PzTapeReel", (0.3, 0.2, 0.12), 0.4)})
    tangle = sc.empty("Tangle", a)
    tape = m("PzTape", (0.28, 0.17, 0.09), 0.25, 0.3, cull=False, rim=0.5)
    for k in range(9):
        sc.mesh("Tape", tangle, "box", (0.004, 0.003, 0.08 + rng.uniform(0, 0.08)),
                (rng.uniform(-0.04, 0.05), rng.uniform(-0.05, 0.03), -0.07 - rng.uniform(0, 0.05)), tape,
                basis=basis_mul(basis_y(rng.uniform(0, 180)), basis_x(rng.uniform(-50, 50))), shadow=False)
    p.glint(a, (0.1, 0.25, -0.3), GLINT_NIGHT_ENERGY, 0.7, GLINT_NIGHT)
    a = p.area("Schoolbag", night, (hx + 0.12, 0.13, hz - 0.3), (0.32, 0.26, 0.2), "hung_schoolbag",
               "OBJ_SCHOOLBAG_NAME", "PROMPT_SEARCH")
    p.prop("Bag", a, "pz_schoolbag", {
        "canvas": m("PzBagCanvas", (0.42, 0.55, 0.42), 0.95, tex="fabric", uv=(5, 5), rim=0.3, glint=0.04),
        "leather": m("PzBagLeather", (0.42, 0.26, 0.16), 0.6, tex="vinyl", uv=(6, 6), rim=0.3),
        "metal": brass}, (0, -0.005, 0), basis=basis_mul(basis_y(20), basis_x(-12)))

    # Bảng lộ trình: bốn tấm biển bến rơi dưới sàn; treo đúng thứ tự thì hiện trên bảng.
    plaque = {"wood": m("PzPlaqueWood", (0.6, 0.45, 0.3), 0.8, tex="wood_dark", rim=0.3),
              "paint": m("PzPlaquePaint", (0.92, 0.9, 0.82), 0.8, png="bus/paper_crease_albedo.png", uv=(3, 3),
                         glint=0.1, rim=0.3),
              "metal": iron}
    p.area("Board", night, (BOARD_POS[0] + 0.03, BOARD_POS[1], BOARD_POS[2]), (0.08, 0.5, 0.38), "route_board",
           "OBJ_ROUTE_BOARD_NAME", "PROMPT_ROUTE_BOARD")
    hung_plaques = sc.empty("BoardPlaques", night, props=[("visible", "false")])
    for k in range(4):
        p.prop("Plaque", hung_plaques, "pz_plaque", plaque,
               (BOARD_POS[0] + 0.03, BOARD_POS[1] + 0.1 - k * 0.1, BOARD_POS[2] - 0.02), rot_y=90)
        sc.node("Label", "Label3D", hung_plaques, [
            ("transform", xform((BOARD_POS[0] + 0.045, BOARD_POS[1] + 0.1 - k * 0.1, BOARD_POS[2] - 0.02), 90)),
            ("pixel_size", "0.0008"), ("modulate", color((0.55, 0.08, 0.05))), ("outline_size", "0"),
            ("text", '"ROUTE_STOP_%d"' % (k + 1)), ("font_size", "40"), ("alpha_cut", "1")])
    a = p.area("Plaques", night, (-0.8, 0.03, -3.35), (0.5, 0.1, 0.4), "fallen_plaques", "OBJ_FALLEN_PLAQUES_NAME",
               "PROMPT_LOOK_CLOSER", extra=[pages("DOC_FALLEN_PLAQUES")])
    for k in range(4):
        p.prop("Plaque", a, "pz_plaque", plaque, (rng.uniform(-0.15, 0.15), -0.02 + 0.013 * k, rng.uniform(-0.12, 0.12)),
               basis=basis_mul(basis_y(rng.uniform(0, 180)), basis_x(-90 + rng.uniform(-4, 4))))
    p.glint(a, (0.1, 0.35, 0.1), GLINT_NIGHT_ENERGY, 0.75, GLINT_NIGHT)

    # Chú Bảy đứng chắn cửa: tay phải giơ cao, đầu dây chuông quấn trong tay; tay trái cầm xấp cuống vé.
    standing_effigy(sc, "Bay", night, BAY_POS, 180,
                    effigy_materials(sc, "Bay", (0.28, 0.42, 0.72), (0.14, 0.14, 0.17), "man"))
    p.area("BayBody", night, (BAY_POS[0], 1.25, BAY_POS[2]), (0.36, 0.7, 0.3), "chu_bay", "OBJ_CHU_BAY_NAME",
           "PROMPT_CHU_BAY")
    leather = m("PzLeather", (0.55, 0.36, 0.22), 0.55, tex="vinyl", uv=(5, 5), rim=0.35, glint=0.03)
    a = p.area("Satchel", night, (BAY_POS[0] - 0.22, 1.12, BAY_POS[2] + 0.1), (0.24, 0.22, 0.14), "bay_satchel",
               "OBJ_SATCHEL_NAME", "PROMPT_SEARCH")
    p.prop("Bag", a, "pz_satchel", {"leather": leather, "metal": brass}, rot_y=180)
    p.prop("Strap", a, "pz_strap", {"leather": leather}, (0.08, 0.3, 0), basis=basis_z(-30))
    a = p.area("Stubs", night, (BAY_POS[0] + 0.25, 0.98, BAY_POS[2] + 0.1), (0.16, 0.16, 0.14), "ticket_stubs",
               "OBJ_TICKET_STUBS_NAME", "PROMPT_ACTION_READ", extra=[pages("DOC_TICKET_STUBS_1", "DOC_TICKET_STUBS_2")])
    p.prop("Stubs", a, "pz_tickets", {
        "ticket": m("PzTicket", (1, 1, 1), 0.9, png="bus/prop_ticket.png", scissor=True, cull=False, glint=0.18,
                    rim=0.3),
        "band": m("PzRubberBand", (0.6, 0.2, 0.15), 0.6)}, (0, 0, 0), basis=basis_x(-70))
    rope = m("PzRope", (0.72, 0.62, 0.45), 0.95, tex="fabric", uv=(20, 20), rim=0.3)
    a = p.area("BellRope", night, (BAY_POS[0] - 0.25, 1.95, BAY_POS[2]), (0.18, 0.4, 0.18), "bell_rope",
               "OBJ_BELL_ROPE_NAME", "PROMPT_BELL_ROPE")
    p.prop("Rope", a, "pz_bell_rope", {"rope": rope}, (0, 0.05, 0))
    sc.mesh("RopeToCeiling", night, "cyl", (0.006, 0.006, 0.6, 5), (0.45, 2.08, BAY_POS[2] + 0.0), rope,
            basis=basis_z(90))

    # Bác Tư ngủ gật trên ghế lái, ôm khư khư phích chè.
    seated_effigy(sc, "Tu", night, TU_POS, effigy_materials(sc, "Tu", (0.36, 0.48, 0.32), (0.26, 0.28, 0.2),
                                                           "old_man"), style="shirt", lean=10)
    p.area("TuBody", night, (TU_POS[0], 1.32, TU_POS[2] + 0.02), (0.3, 0.3, 0.3), "bac_tu", "OBJ_BAC_TU_NAME",
           "PROMPT_BAC_TU")
    a = p.area("Thermos", night, (TU_POS[0] + 0.16, 0.95, TU_POS[2] - 0.2), (0.16, 0.34, 0.16), "thermos",
               "OBJ_THERMOS_NAME", "PROMPT_THERMOS")
    p.prop("Flask", a, "pz_thermos", {
        "body": m("PzThermosBody", (1, 1, 1), 0.3, 0.2, png="bus/prop_thermos.png", uv=(3.54, 5.0), rim=0.4,
                  glint=0.06),
        "metal": m("PzThermosMetal", (0.75, 0.72, 0.66), 0.3, 0.9, rim=0.4),
        "cap": m("PzCupLid", (0.82, 0.78, 0.68), 0.45, rim=0.3)}, basis=basis_z(-15))

    # Ghế 08 (ngay sau ghế 07 của An): chiếc dép nhựa trẻ con, không có cuống vé.
    x8, z8 = seat_xz(NUMBERED_SEATS["08"])
    a = p.area("Seat08", night, (x8 - 0.02, SEAT_Y + 0.12, z8), (0.36, 0.2, 0.34), "seat_08", "OBJ_SEAT_08_NAME")
    sandal = m("PzSandal", (0.98, 0.5, 0.66), 0.35, rim=0.5, glint=0.1)
    p.prop("Sandal", a, "pz_sandal", {"plastic": sandal, "strap": sandal}, (0.02, -0.04, -0.03), rot_y=20)

    sc.save("scenes/bus/BusPuzzles.tscn")


if __name__ == "__main__":
    build()
