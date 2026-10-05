#!/usr/bin/env python3
"""Sinh đồ vật câu đố chương 2 "Chuyến xe không về bến": scenes/bus/BusPuzzles.tscn

Chạy:  python3 tools/bus_puzzles_blockout.py

Scene này được instance vào scenes/bus/BusRide.tscn, chồng đúng tọa độ lên
scenes/levels/Bus.tscn. Hai nhóm, BusWreckDirector bật/tắt theo lớp xe:
- Wreck: đồ trong xác xe (đèn bão quấn bùa, hộp tôn bác Tư, chậu sắt hóa vàng...).
- Night: Đêm 1999, hình nhân giấy của những người trên chuyến xe và đồ của họ.

Mỗi vật tương tác là Area3D gắn Interactable.gd; BusWreckDirector tìm theo tên node.
LƯU Ý: chạy lại script sẽ GHI ĐÈ scenes/bus/BusPuzzles.tscn.
"""

import random

from level_blockout import Scene, basis_mul, basis_x, basis_y, basis_z, color, f, vec3, xform
from bus_blockout import (BOARD_POS, HALF_W, LAMP_POS, NAM_SEAT, HUNG_SEAT, NUMBERED_SEATS, RACK_Y, ROWS, SEAT_Y,
                          Z_FRONT, seat_xz, seated_person, standing_person, storm_lamp)

BASIN_POS = (0.0, 0.0, 3.85)
TIN_FLOOR = (-0.38, 0.07, -0.98)        # hộp bánh quy dưới chân bà Năm
TIN_RACK = (-1.0, RACK_Y + 0.07, ROWS[3])  # trên giá hành lý, ngay trên ghế bà
BAY_POS = (0.85, 0.2, -4.05)            # chú Bảy đứng trên bậc cửa
TU_POS = (-0.7, 0.05, -4.0)


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


def pages(*keys):
    return ("pages", 'Array[String]([%s])' % ", ".join('"%s"' % k for k in keys))


def desc(key):
    return ("description_key", '"%s"' % key)


def build():
    p = Puzzles()
    sc = p.sc
    rng = random.Random(14041999)

    # --- Vật liệu ---
    rust = sc.mat("PzRust", (0.36, 0.2, 0.12), 0.95, metallic=0.4)
    tin_new = sc.mat("PzTin", (0.55, 0.52, 0.46), 0.35, metallic=0.8)
    soot_glass = sc.mat("PzSootGlass", (0.18, 0.16, 0.12), 0.3, alpha=0.7)
    talisman = sc.mat("PzTalisman", (0.92, 0.78, 0.25), 0.9)
    ink_red = sc.mat("PzInkRed", (0.65, 0.06, 0.04), 0.9)
    bottle = sc.mat("PzBottle", (0.45, 0.6, 0.45), 0.08, alpha=0.6)
    kerosene = sc.mat("PzKerosene", (0.75, 0.6, 0.25), 0.1, alpha=0.75)
    cotton = sc.mat("PzCotton", (0.9, 0.88, 0.8), 1.0)
    paper_old = sc.mat("PzPaperOld", (0.72, 0.64, 0.46), 1.0)
    biscuit_red = sc.mat("PzBiscuitTin", (0.62, 0.12, 0.1), 0.4, metallic=0.6)
    biscuit_gold = sc.mat("PzBiscuitGold", (0.8, 0.62, 0.25), 0.35, metallic=0.8)
    wood_clog = sc.mat("PzClogWood", (0.28, 0.2, 0.13), 1.0)
    iron = sc.mat("PzIron", (0.12, 0.11, 0.1), 0.7, metallic=0.6)
    ash = sc.mat("PzAsh", (0.2, 0.19, 0.18), 1.0)
    fire = sc.mat("PzFire", (1.0, 0.55, 0.15), 0.5, emission=(1.0, 0.45, 0.1), energy=5.0, unshaded=True)
    glow_paper = sc.mat("PzGlowPaper", (1.0, 0.95, 0.7), 0.6, emission=(1.0, 0.8, 0.45), energy=1.6, alpha=0.75)
    paper = sc.mat("PzEffigyPaper", (0.9, 0.88, 0.8), 1.0, emission=(0.12, 0.13, 0.12), energy=1.0)
    paper_shade = sc.mat("PzEffigyPaperShade", (0.72, 0.7, 0.64), 1.0)
    paper_hair = sc.mat("PzEffigyHair", (0.06, 0.06, 0.07), 1.0)
    cheek = sc.mat("PzCheek", (0.85, 0.16, 0.16), 1.0)
    paper_brown = sc.mat("PzEffigyBrown", (0.45, 0.3, 0.2), 1.0)
    paper_blue = sc.mat("PzEffigyBlue", (0.28, 0.36, 0.55), 1.0)
    paper_green = sc.mat("PzEffigyGreen", (0.3, 0.42, 0.3), 1.0)
    non_la = sc.mat("PzNonLa", (0.8, 0.72, 0.52), 0.9, cull=True)
    mu_coi = sc.mat("PzMuCoi", (0.32, 0.38, 0.22), 0.7)
    bamboo = sc.mat("PzBamboo", (0.6, 0.5, 0.28), 0.7)
    herb = sc.mat("PzHerbPaper", (0.68, 0.58, 0.4), 1.0)
    string = sc.mat("PzString", (0.85, 0.2, 0.15), 1.0)
    plastic = sc.mat("PzDeckPlastic", (0.12, 0.12, 0.13), 0.4)
    tape = sc.mat("PzTape", (0.25, 0.15, 0.08), 0.3)
    bag_green = sc.mat("PzSchoolbag", (0.22, 0.32, 0.25), 0.9)
    leather = sc.mat("PzLeather", (0.3, 0.18, 0.1), 0.6)
    sandal = sc.mat("PzSandal", (0.95, 0.45, 0.6), 0.4)
    plaque = sc.mat("PzPlaque", (0.85, 0.82, 0.7), 0.9)
    flask = sc.mat("PzThermos", (0.2, 0.45, 0.32), 0.35, metallic=0.3)
    bell_rope = sc.mat("PzRope", (0.62, 0.55, 0.4), 0.9)
    balm = sc.mat("PzBalm", (0.25, 0.55, 0.35), 0.2, alpha=0.8)

    # =======================================================================
    # XÁC XE
    # =======================================================================
    wreck = sc.empty("Wreck")

    # Đèn bão quấn bùa treo ở vách sau.
    a = p.area("Lamp", wreck, LAMP_POS, (0.26, 0.4, 0.26), "storm_lamp", "OBJ_STORM_LAMP_NAME", "PROMPT_LAMP_UNWRAP")
    storm_lamp(sc, "Model", a, (0, -0.0, 0), rust, soot_glass)
    tal = sc.empty("Talisman", a)
    sc.mesh("Wrap", tal, "cyl", (0.062, 0.062, 0.1, 12, False), (0, 0.135, 0), talisman, shadow=False)
    sc.mesh("Strip", tal, "box", (0.03, 0.22, 0.004), (0.02, 0.12, -0.065), talisman, rot_y=-10, shadow=False)
    sc.mesh("Glyph", tal, "box", (0.012, 0.08, 0.002), (0.02, 0.14, -0.068), ink_red, rot_y=-10, shadow=False)
    sc.mesh("Hook", wreck, "cyl", (0.005, 0.005, 0.12, 6), (LAMP_POS[0], LAMP_POS[1] + 0.33, LAMP_POS[2] + 0.04),
            iron, basis=basis_x(30))

    # Chai dầu hỏa còn nguyên trong giỏ mục của bà Năm.
    a = p.area("Kerosene", wreck, (-0.9, 0.1, -0.95), (0.22, 0.22, 0.22), "kerosene", "ITEM_KEROSENE_NAME",
               "PROMPT_ACTION_PICKUP", extra=[desc("ITEM_KEROSENE_DESC")])
    sc.mesh("Bottle", a, "cyl", (0.03, 0.035, 0.16, 10), (0, 0.0, 0), bottle, basis=basis_z(70))
    sc.mesh("Oil", a, "cyl", (0.028, 0.033, 0.09, 10), (-0.03, -0.01, 0), kerosene, basis=basis_z(70))
    sc.mesh("Cork", a, "cyl", (0.014, 0.014, 0.03, 8), (0.09, 0.03, 0), sc.mat("PzCork", (0.5, 0.36, 0.22), 1.0),
            basis=basis_z(70))

    # Cuộn chỉ bông kẹt trong khe ghế bà Năm.
    nx, nz = seat_xz(NAM_SEAT)
    a = p.area("Thread", wreck, (nx, SEAT_Y + 0.08, nz + 0.17), (0.18, 0.14, 0.14), "cotton_thread",
               "ITEM_COTTON_THREAD_NAME", "PROMPT_ACTION_PICKUP", extra=[desc("ITEM_COTTON_THREAD_DESC")])
    sc.mesh("Spool", a, "cyl", (0.025, 0.025, 0.05, 10), (0, 0, 0), cotton, basis=basis_z(90))
    sc.mesh("Core", a, "cyl", (0.012, 0.012, 0.056, 8), (0, 0, 0), paper_old, basis=basis_z(90))

    # Hộp tôn của bác Tư trên taplô, khóa số ba vòng, nắp khắc "Số xe".
    a = p.area("TinBox", wreck, (0.25, 1.14, Z_FRONT + 0.38), (0.3, 0.2, 0.26), "driver_tin_box",
               "OBJ_DRIVER_TIN_BOX_NAME", "PROMPT_TIN_BOX_LOCK")
    sc.mesh("Base", a, "box", (0.22, 0.07, 0.14), (0, 0, 0), rust)
    lid = sc.empty("Lid", a, (0, 0.035, 0.07))
    sc.mesh("LidPlate", lid, "box", (0.225, 0.012, 0.145), (0, 0.006, -0.0725), rust)
    sc.node("Engraving", "Label3D", lid, [
        ("transform", xform((0, 0.0125, -0.0725), basis=basis_x(-90))), ("pixel_size", "0.0008"),
        ("modulate", color((0.12, 0.08, 0.05))), ("outline_size", "0"), ("text", '"OBJ_TIN_BOX_ENGRAVING"'),
        ("font_size", "40"), ("alpha_cut", "1")])
    for k in range(3):
        sc.mesh("Dial", a, "cyl", (0.012, 0.012, 0.012, 10), (-0.03 + k * 0.03, 0.0, -0.075), iron,
                basis=basis_z(90))
    contents = sc.empty("Contents", a, props=[("visible", "false")])
    sc.mesh("MatchJar", contents, "cyl", (0.022, 0.022, 0.06, 10), (-0.06, 0.0, 0.01), bottle)
    sc.mesh("License", contents, "box", (0.08, 0.004, 0.055), (0.03, 0.0, 0.02), paper_old, rot_y=8)
    sc.mesh("Ledger", contents, "box", (0.09, 0.012, 0.12), (0.05, 0.01, -0.02), sc.mat("PzLedger",
            (0.3, 0.12, 0.1), 1.0), rot_y=-6)

    # Giấy phép lưu hành nhòe nước, chỉ còn đọc được "...85".
    p.area("Permit", wreck, (-0.15, 1.115, Z_FRONT + 0.48), (0.18, 0.06, 0.14), "permit", "OBJ_PERMIT_NAME",
           "PROMPT_ACTION_READ", extra=[pages("DOC_PERMIT")])
    sc.mesh("Paper", "Wreck/Permit", "box", (0.13, 0.002, 0.09), (0, -0.01, 0), paper_old, rot_y=-12)

    # Decal số xe dán phía ngoài kính lái (chỉ để xem kỹ).
    p.area("NumberDecal", wreck, (0.62, 1.14, Z_FRONT - 0.0), (0.34, 0.2, 0.06), "number_decal",
           "OBJ_NUMBER_DECAL_NAME")

    # Hộp bánh quy: gỉ thủng dưới sàn, hoặc nằm khô trên giá nếu đã được dời lên ở Đêm 1999.
    a = p.area("TinRusted", wreck, TIN_FLOOR, (0.24, 0.16, 0.24), "biscuit_tin_rusted", "OBJ_BISCUIT_TIN_NAME")
    sc.mesh("Can", a, "cyl", (0.1, 0.1, 0.09, 16), (0, -0.025, 0), rust, rot_y=20)
    sc.mesh("Hole", a, "cyl", (0.04, 0.04, 0.005, 8), (0.03, 0.022, 0.02), ash)
    a = p.area("TinDry", wreck, TIN_RACK, (0.3, 0.18, 0.3), "biscuit_tin_dry", "OBJ_BISCUIT_TIN_NAME",
               "PROMPT_TIN_OPEN", visible=False, extra=[pages("DOC_PATTERN_BOOK_1", "DOC_PATTERN_BOOK_2",
                                                              "DOC_PATTERN_BOOK_3")])
    sc.mesh("Can", a, "cyl", (0.1, 0.1, 0.09, 16), (0, -0.02, 0), rust, rot_y=20)
    sc.mesh("Lid", a, "cyl", (0.103, 0.103, 0.015, 16), (0, 0.03, 0), sc.mat("PzRustLid", (0.42, 0.24, 0.14), 0.9,
                                                                               metallic=0.4))

    # Chiếc guốc mộc mục của bà Năm, quai còn hằn hoa mai.
    a = p.area("Clog", wreck, (-0.62, 0.03, -0.8), (0.18, 0.1, 0.24), "rotten_clog", "OBJ_ROTTEN_CLOG_NAME",
               rot_y=-25)
    sc.mesh("Sole", a, "box", (0.08, 0.025, 0.2), (0, 0, 0), wood_clog)
    sc.mesh("Strap", a, "box", (0.085, 0.02, 0.03), (0, 0.022, -0.04), sc.mat("PzStrapRotten", (0.2, 0.12, 0.1), 1.0))

    # Chậu sắt cuối xe: chỗ hóa vàng.
    a = p.area("Basin", wreck, BASIN_POS, (0.45, 0.3, 0.45), "iron_basin", "OBJ_IRON_BASIN_NAME", "PROMPT_BASIN")
    sc.mesh("Bowl", a, "cyl", (0.2, 0.14, 0.12, 16, False), (0, 0.06, 0), iron)
    sc.mesh("Bottom", a, "cyl", (0.14, 0.14, 0.01, 16), (0, 0.005, 0), iron)
    sc.mesh("OldAsh", a, "cyl", (0.13, 0.13, 0.01, 12), (0, 0.02, 0), ash)
    flames = sc.empty("Fire", a, props=[("visible", "false")])
    for k in range(5):
        sc.mesh("Flame", flames, "sphere", (0.04, 0.16 + 0.04 * (k % 2)),
                (0.07 * (k % 3 - 1), 0.12, 0.06 * ((k + 1) % 3 - 1)), fire, shadow=False)
    sc.node("Light", "OmniLight3D", flames, [
        ("transform", xform((0, 0.35, 0))), ("light_color", color((1.0, 0.55, 0.2))), ("light_energy", "2.5"),
        ("omni_range", "4.0"), ("shadow_enabled", "true")])

    # Đồ của Hùng ở xác xe: vở còn một trang khô (gợi ý bảng lộ trình), khung đài gỉ.
    hx, hz = seat_xz(HUNG_SEAT)
    p.area("Notebook", wreck, (hx + 0.12, 0.14, hz - 0.3), (0.3, 0.26, 0.2), "hung_notebook",
           "OBJ_HUNG_NOTEBOOK_NAME", "PROMPT_ACTION_READ", extra=[pages("DOC_HUNG_NOTEBOOK")])
    p.area("DeckRusted", wreck, (hx, 0.56, hz - 0.02), (0.36, 0.16, 0.14), "deck_rusted", "OBJ_DECK_RUSTED_NAME")

    # =======================================================================
    # ĐÊM 1999
    # =======================================================================
    night = sc.empty("Night", props=[("visible", "false")])

    def face(head_path):
        for sx in (-1, 1):
            sc.mesh("Eye", head_path, "box", (0.025, 0.008, 0.004), (sx * 0.038, 0.015, -0.103), paper_hair,
                    shadow=False)
            sc.mesh("Cheek", head_path, "cyl", (0.018, 0.018, 0.003, 10), (sx * 0.05, -0.025, -0.098), cheek,
                    basis=basis_x(90), shadow=False)
        sc.mesh("Mouth", head_path, "box", (0.02, 0.006, 0.004), (0, -0.05, -0.103), cheek, shadow=False)

    def effigy(name, seat, shirt, pants, feet=None, hat=None, hat_mat=None, lean=0.0, head_tilt=0.0):
        x, z = seat_xz(seat)
        g = seated_person(sc, name, night, (x, 0.0, z), shirt, pants, paper, feet or paper_hair, hat, hat_mat,
                          lean=lean, head_tilt=head_tilt)
        face(g + "/Upper/Head")
        return g

    # Ba hành khách thường (không chấp niệm riêng): ghế 03, 04, 05. Đồ của họ văng xuống sàn.
    for num, shirt in (("03", paper_green), ("04", paper_shade), ("05", paper_brown)):
        g = effigy("Passenger" + num, NUMBERED_SEATS[num], shirt, paper_shade)
        x, z = seat_xz(NUMBERED_SEATS[num])
        p.area("Seat" + num, night, (x, 0.95, z), (0.34, 0.75, 0.36), "passenger_" + num, "OBJ_PASSENGER_NAME",
               "PROMPT_PASSENGER")
        held = sc.empty("Held", g, props=[("visible", "true")])
        hn = sc.empty("non_coi", held, (0, 0.72, -0.25), props=[("visible", "false")])
        sc.mesh("Dome", hn, "sphere", (0.15, 0.17), (0, 0.05, 0), mu_coi)
        sc.mesh("Brim", hn, "cyl", (0.17, 0.17, 0.012, 18), (0, 0.0, 0), mu_coi)
        ht = sc.empty("goi_thuoc_bac", held, (0, 0.7, -0.27), props=[("visible", "false")])
        sc.mesh("Pack", ht, "box", (0.2, 0.1, 0.14), (0, 0, 0), herb)
        sc.mesh("Tie", ht, "box", (0.205, 0.105, 0.012), (0, 0, 0), string)
        hd = sc.empty("dieu_cay", held, (0.12, 0.75, -0.25), props=[("visible", "false")])
        sc.mesh("Pipe", hd, "cyl", (0.025, 0.025, 0.55, 10), (0, 0.15, 0), bamboo, basis=basis_x(-15))
    # Đồ rơi trên sàn lối đi.
    a = p.area("NonCoi", night, (-0.15, 0.06, -1.75), (0.36, 0.14, 0.36), "non_coi", "ITEM_NON_COI_NAME",
               "PROMPT_ACTION_PICKUP", extra=[desc("ITEM_NON_COI_DESC")])
    sc.mesh("Dome", a, "sphere", (0.15, 0.17), (0, 0.0, 0), mu_coi, basis=basis_z(160))
    sc.mesh("Brim", a, "cyl", (0.17, 0.17, 0.012, 18), (0, 0.01, 0), mu_coi, basis=basis_z(160))
    a = p.area("ThuocBac", night, (0.18, 0.06, -2.55), (0.28, 0.14, 0.24), "goi_thuoc_bac", "ITEM_THUOC_BAC_NAME",
               "PROMPT_ACTION_PICKUP", rot_y=30, extra=[desc("ITEM_THUOC_BAC_DESC")])
    sc.mesh("Pack", a, "box", (0.2, 0.1, 0.14), (0, -0.01, 0), herb)
    sc.mesh("Tie", a, "box", (0.205, 0.105, 0.012), (0, -0.01, 0), string)
    a = p.area("DieuCay", night, (-0.22, 0.04, -0.95), (0.2, 0.12, 0.6), "dieu_cay", "ITEM_DIEU_CAY_NAME",
               "PROMPT_ACTION_PICKUP", rot_y=12, extra=[desc("ITEM_DIEU_CAY_DESC")])
    sc.mesh("Pipe", a, "cyl", (0.025, 0.025, 0.55, 10), (0, 0, 0), bamboo, basis=basis_x(90))
    sc.mesh("Bowl", a, "cyl", (0.012, 0.012, 0.06, 8), (0, 0.03, 0.2), bamboo)

    # Bà Năm: chân trần, nón lá đặt trên đùi (mặt trong vành nón có tên bằng mực tím).
    effigy("BaNam", NAM_SEAT, paper_brown, paper_hair, feet=paper, lean=-4)
    p.area("Nam", night, (nx, 1.0, nz + 0.02), (0.34, 0.6, 0.3), "ba_nam", "OBJ_BA_NAM_NAME", "PROMPT_BA_NAM")
    a = p.area("Hat", night, (nx, 0.72, nz - 0.25), (0.34, 0.12, 0.3), "nam_hat", "OBJ_NAM_HAT_NAME",
               "PROMPT_LOOK_CLOSER", extra=[pages("DOC_NAM_HAT")])
    sc.mesh("Cone", a, "cyl", (0.005, 0.22, 0.13, 18), (0, 0, 0), non_la, basis=basis_x(-160))
    a = p.area("Tin", night, TIN_FLOOR, (0.24, 0.16, 0.24), "biscuit_tin", "ITEM_BISCUIT_TIN_NAME",
               "PROMPT_ACTION_PICKUP", extra=[desc("ITEM_BISCUIT_TIN_DESC")])
    sc.mesh("Can", a, "cyl", (0.1, 0.1, 0.09, 16), (0, -0.025, 0), biscuit_red, rot_y=20)
    sc.mesh("Lid", a, "cyl", (0.103, 0.103, 0.015, 16), (0, 0.025, 0), biscuit_gold)
    a = p.area("Rack", night, (TIN_RACK[0], TIN_RACK[1] - 0.02, TIN_RACK[2]), (0.4, 0.16, 0.5), "luggage_rack",
               "OBJ_LUGGAGE_RACK_NAME", "PROMPT_RACK")
    placed = sc.empty("Placed", a, props=[("visible", "false")])
    sc.mesh("Can", placed, "cyl", (0.1, 0.1, 0.09, 16), (0, 0.0, 0), biscuit_red, rot_y=20)
    sc.mesh("Lid", placed, "cyl", (0.103, 0.103, 0.015, 16), (0, 0.05, 0), biscuit_gold)
    # Đôi guốc mã mờ sáng cạnh chậu (sau khi hóa vàng ở xác xe), và lọ dầu gió bà để lại.
    a = p.area("GlowClogs", night, (BASIN_POS[0], 0.05, BASIN_POS[2]), (0.3, 0.12, 0.3), "paper_clogs",
               "ITEM_PAPER_CLOGS_NAME", "PROMPT_ACTION_PICKUP", visible=False, extra=[desc("ITEM_PAPER_CLOGS_DESC")])
    for sx in (-1, 1):
        sc.mesh("Clog", a, "box", (0.075, 0.03, 0.18), (sx * 0.05, 0, 0), glow_paper, shadow=False)
    sc.node("Glow", "OmniLight3D", a, [("transform", xform((0, 0.15, 0))), ("light_color", color((1, 0.8, 0.5))),
                                       ("light_energy", "0.8"), ("omni_range", "1.4")])
    a = p.area("WindOil", night, (nx, SEAT_Y + 0.08, nz - 0.05), (0.14, 0.14, 0.14), "wind_oil",
               "ITEM_WIND_OIL_NAME", "PROMPT_ACTION_PICKUP", visible=False, extra=[desc("ITEM_WIND_OIL_DESC")])
    sc.mesh("Vial", a, "cyl", (0.018, 0.02, 0.06, 10), (0, 0, 0), balm)
    sc.mesh("Cap", a, "cyl", (0.012, 0.012, 0.015, 8), (0, 0.037, 0), sc.mat("PzBalmCap", (0.9, 0.85, 0.2), 0.4))

    # Hùng: ôm chiếc đài cát-sét đã "ăn băng", cặp sách dưới chân.
    effigy("Hung", HUNG_SEAT, paper_blue, paper_shade, head_tilt=-8)
    a = p.area("Deck", night, (hx, 0.72, hz - 0.28), (0.38, 0.2, 0.18), "cassette_deck", "OBJ_CASSETTE_DECK_NAME",
               "PROMPT_DECK")
    sc.mesh("Body", a, "box", (0.32, 0.12, 0.09), (0, 0, 0), plastic)
    sc.mesh("Handle", a, "torus", (0.05, 0.06), (0, 0.08, 0), plastic, basis=basis_x(90))
    tangle = sc.empty("Tangle", a)
    for k in range(9):
        sc.mesh("Tape", tangle, "box", (0.004, 0.003, 0.08 + rng.uniform(0, 0.08)),
                (rng.uniform(-0.06, 0.08), rng.uniform(-0.06, 0.04), -0.06 - rng.uniform(0, 0.05)), tape,
                basis=basis_mul(basis_y(rng.uniform(0, 180)), basis_x(rng.uniform(-50, 50))), shadow=False)
    a = p.area("Schoolbag", night, (hx + 0.12, 0.13, hz - 0.3), (0.32, 0.26, 0.2), "hung_schoolbag",
               "OBJ_SCHOOLBAG_NAME", "PROMPT_SEARCH")
    sc.mesh("Bag", a, "box", (0.3, 0.24, 0.1), (0, 0, 0), bag_green, basis=basis_mul(basis_y(20), basis_x(-12)))

    # Bảng lộ trình: bốn tấm biển bến rơi dưới sàn; treo đúng thứ tự thì hiện trên bảng.
    p.area("Board", night, (BOARD_POS[0] + 0.03, BOARD_POS[1], BOARD_POS[2]), (0.08, 0.5, 0.38), "route_board",
           "OBJ_ROUTE_BOARD_NAME", "PROMPT_ROUTE_BOARD")
    hung_plaques = sc.empty("BoardPlaques", night, props=[("visible", "false")])
    for k in range(4):
        sc.mesh("Plaque", hung_plaques, "box", (0.012, 0.075, 0.24),
                (BOARD_POS[0] + 0.03, BOARD_POS[1] + 0.1 - k * 0.1, BOARD_POS[2] - 0.02), plaque)
        sc.node("Label", "Label3D", hung_plaques, [
            ("transform", xform((BOARD_POS[0] + 0.04, BOARD_POS[1] + 0.1 - k * 0.1, BOARD_POS[2] - 0.02), 90)),
            ("pixel_size", "0.0008"), ("modulate", color((0.2, 0.1, 0.05))), ("outline_size", "0"),
            ("text", '"ROUTE_STOP_%d"' % (k + 1)), ("font_size", "40"), ("alpha_cut", "1")])
    a = p.area("Plaques", night, (-0.8, 0.03, -3.35), (0.5, 0.1, 0.4), "fallen_plaques", "OBJ_FALLEN_PLAQUES_NAME",
               "PROMPT_LOOK_CLOSER", extra=[pages("DOC_FALLEN_PLAQUES")])
    for k in range(4):
        sc.mesh("Plaque", a, "box", (0.24, 0.012, 0.075), (rng.uniform(-0.15, 0.15), 0.0, rng.uniform(-0.12, 0.12)),
                plaque, rot_y=rng.uniform(0, 180))

    # Chú Bảy đứng chắn cửa: tay phải giơ cao, đầu dây chuông quấn trong tay; tay trái cầm xấp cuống vé.
    g = standing_person(sc, "Bay", night, BAY_POS, 180, paper_blue, paper_hair, paper, paper_hair, arm_up=True)
    face(sc.empty("Head", g, (0, 1.6, 0)))
    p.area("BayBody", night, (BAY_POS[0], 1.25, BAY_POS[2]), (0.36, 0.7, 0.3), "chu_bay", "OBJ_CHU_BAY_NAME",
           "PROMPT_CHU_BAY")
    a = p.area("Satchel", night, (BAY_POS[0] - 0.22, 1.12, BAY_POS[2] + 0.1), (0.24, 0.22, 0.14), "bay_satchel",
               "OBJ_SATCHEL_NAME", "PROMPT_SEARCH")
    sc.mesh("Bag", a, "box", (0.22, 0.18, 0.08), (0, 0, 0), leather)
    sc.mesh("Strap", a, "box", (0.03, 0.6, 0.02), (0.08, 0.3, 0), leather, basis=basis_z(-30))
    a = p.area("Stubs", night, (BAY_POS[0] + 0.25, 0.98, BAY_POS[2] + 0.1), (0.16, 0.16, 0.14), "ticket_stubs",
               "OBJ_TICKET_STUBS_NAME", "PROMPT_ACTION_READ", extra=[pages("DOC_TICKET_STUBS_1", "DOC_TICKET_STUBS_2")])
    for k in range(4):
        sc.mesh("Stub", a, "box", (0.06, 0.002, 0.1), (0, 0.004 * k, 0), paper_old, rot_y=k * 6)
    a = p.area("BellRope", night, (BAY_POS[0] - 0.25, 1.95, BAY_POS[2]), (0.18, 0.4, 0.18), "bell_rope",
               "OBJ_BELL_ROPE_NAME", "PROMPT_BELL_ROPE")
    sc.mesh("Rope", a, "cyl", (0.006, 0.006, 0.4, 5), (0, 0.05, 0), bell_rope)
    sc.mesh("RopeToCeiling", night, "cyl", (0.006, 0.006, 0.6, 5), (0.45, 2.08, BAY_POS[2] + 0.0), bell_rope,
            basis=basis_z(90))

    # Bác Tư ngủ gật trên ghế lái, ôm khư khư phích chè.
    g = seated_person(sc, "Tu", night, TU_POS, paper_green, paper_hair, paper, paper_hair, lean=10, head_tilt=0)
    face(g + "/Upper/Head")
    p.area("TuBody", night, (TU_POS[0], 1.32, TU_POS[2] + 0.02), (0.3, 0.3, 0.3), "bac_tu", "OBJ_BAC_TU_NAME",
           "PROMPT_BAC_TU")
    a = p.area("Thermos", night, (TU_POS[0] + 0.16, 0.95, TU_POS[2] - 0.2), (0.16, 0.34, 0.16), "thermos",
               "OBJ_THERMOS_NAME", "PROMPT_THERMOS")
    sc.mesh("Flask", a, "cyl", (0.045, 0.045, 0.28, 12), (0, 0, 0), flask, basis=basis_z(-15))
    sc.mesh("Cup", a, "cyl", (0.048, 0.04, 0.05, 12), (0.04, 0.16, 0), sc.mat("PzCupLid", (0.75, 0.72, 0.65), 0.4),
            basis=basis_z(-15))

    # Ghế 08 (ngay sau ghế 07 của An): chiếc dép nhựa trẻ con, không có cuống vé.
    x8, z8 = seat_xz(NUMBERED_SEATS["08"])
    a = p.area("Seat08", night, (x8 - 0.02, SEAT_Y + 0.12, z8), (0.36, 0.2, 0.34), "seat_08", "OBJ_SEAT_08_NAME")
    sc.mesh("Sandal", a, "box", (0.07, 0.02, 0.15), (0.02, -0.03, -0.03), sandal, rot_y=20)
    sc.mesh("SandalStrap", a, "box", (0.072, 0.025, 0.02), (0.02, -0.01, -0.06), sandal, rot_y=20)

    sc.save("scenes/bus/BusPuzzles.tscn")


if __name__ == "__main__":
    build()
