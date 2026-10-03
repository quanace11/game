#!/usr/bin/env python3
"""Sinh bối cảnh xe khách nông thôn thập niên 199x: scenes/levels/Bus.tscn

Chạy:  python3 tools/bus_blockout.py

Một scene, hai trạng thái (BusLevel.gd bật/tắt):
- Day: chiều muộn, xe đông khách đang chạy trên đường làng (cảnh ngoài cửa sổ trôi
  qua nhờ ScrollingScenery.gd), nắng vàng xiên qua cửa kính.
- Derelict: cùng chiếc xe nhưng mục nát, vắng tanh, đỗ im trong sương đêm, đèn tuýp
  chập chờn, ghế rách, kính vỡ, vàng mã rải trên sàn.

Phần dùng chung cho cả hai trạng thái (vỏ xe, khung ghế, tay vịn, buồng lái) có va chạm;
đồ riêng của từng trạng thái chỉ là mesh trang trí để bật/tắt không ảnh hưởng va chạm.

Hệ tọa độ: đầu xe hướng -Z, cửa lên xuống bên phải (+X), sàn xe ở y = 0.
LƯU Ý: chạy lại script sẽ GHI ĐÈ scenes/levels/Bus.tscn.
"""

import math
import random

from level_blockout import (Scene, basis_mul, basis_x, basis_y, basis_z, bulb, color, dust, f, vec3,
                            xform, DECAL)

# --- Kích thước lòng xe (mét) ---
HALF_W = 1.25          # nửa bề ngang lòng xe
H = 2.15               # chiều cao lòng xe
Z_FRONT = -5.0         # kính chắn gió
Z_BACK = 4.6           # vách sau
WALL = 0.08
ROWS = [-2.9 + 0.8 * i for i in range(9)]  # hàng ghế đôi hai bên
BENCH_Z = 4.2          # băng ghế cuối
SEAT_W = 0.42
SEAT_X = (0.61, 1.03)  # tâm ghế trong (sát lối đi) và ghế ngoài (sát cửa sổ), mỗi bên
SEAT_Y = 0.45
WIN_Y = (0.92, 1.68)   # mép dưới / trên ô cửa sổ
WIN_W = 0.66
DOOR_Z = (-4.6, -3.7)  # cửa lên xuống bên phải

# Ghế của An (bên phải, hàng 4, sát cửa sổ) và ghế bà cụ (bên kia lối đi).
AN_ROW = 3
OLD_WOMAN_ROW = 3

random.seed(1999)


def env_resource(sc, rid, top, horizon, ground, ambient, ambient_energy, fog_color, fog_density,
                 exposure=1.0, sky_energy=1.0):
    sc.sub_res("ProceduralSkyMaterial", "SkyMat_" + rid, [
        ("sky_top_color", color(top)), ("sky_horizon_color", color(horizon)),
        ("ground_bottom_color", color(ground)), ("ground_horizon_color", color(horizon)),
        ("sky_energy_multiplier", f(sky_energy)),
    ])
    sc.sub_res("Sky", "Sky_" + rid, [("sky_material", 'SubResource("SkyMat_%s")' % rid)])
    return sc.sub_res("Environment", "Env_" + rid, [
        ("background_mode", "2"), ("sky", 'SubResource("Sky_%s")' % rid),
        ("ambient_light_source", "3"), ("ambient_light_color", color(ambient)),
        ("ambient_light_sky_contribution", "0.25"), ("ambient_light_energy", f(ambient_energy)),
        ("tonemap_mode", "3"), ("tonemap_exposure", f(exposure)),
        ("ssao_enabled", "true"), ("ssao_radius", "0.8"), ("ssao_intensity", "2.0"),
        ("glow_enabled", "true"), ("glow_intensity", "0.5"), ("glow_bloom", "0.04"),
        ("fog_enabled", "true"), ("fog_light_color", color(fog_color)), ("fog_density", f(fog_density)),
        ("fog_sky_affect", "0.6"),
    ])


def directional(sc, name, parent, pitch, yaw, light_color, energy, shadow=True):
    b = basis_mul(basis_y(yaw), basis_x(pitch))
    sc.node(name, "DirectionalLight3D", parent, [
        ("transform", xform((0, 6, 0), basis=b)),
        ("light_color", color(light_color)), ("light_energy", f(energy)),
        ("shadow_enabled", "true" if shadow else "false"),
        ("directional_shadow_max_distance", "30.0"),
    ])


# ---------------------------------------------------------------------------
# Người ngồi / đứng kiểu low-poly, không mặt (giống hình nộm giấy). Mặt trước -Z.
# ---------------------------------------------------------------------------

def seated_person(sc, name, parent, pos, shirt, pants, skin, hair, hat=None, hat_mat=None, lean=0.0,
                  head_tilt=0.0, rot_y=0.0):
    g = sc.empty(name, parent, pos, rot_y)
    sc.mesh("Thighs", g, "box", (0.36, 0.14, 0.4), (0, 0.52, -0.1), pants)
    sc.mesh("Shins", g, "box", (0.32, 0.44, 0.13), (0, 0.24, -0.33), pants)
    sc.mesh("Feet", g, "box", (0.3, 0.07, 0.2), (0, 0.035, -0.4), hair)
    body = sc.empty("Upper", g, (0, 0.58, 0.06), basis=basis_x(lean))
    sc.mesh("Torso", body, "box", (0.38, 0.55, 0.22), (0, 0.28, 0), shirt)
    for sx in (-1, 1):
        sc.mesh("Arm", body, "box", (0.09, 0.36, 0.1), (sx * 0.235, 0.33, 0), shirt)
        sc.mesh("Forearm", body, "box", (0.085, 0.085, 0.3), (sx * 0.2, 0.06, -0.16), shirt)
        sc.mesh("Hand", body, "box", (0.07, 0.05, 0.08), (sx * 0.17, 0.05, -0.33), skin)
    sc.mesh("Neck", body, "cyl", (0.05, 0.05, 0.08, 8), (0, 0.6, 0), skin)
    head = sc.empty("Head", body, (0, 0.72, 0), basis=basis_z(head_tilt))
    sc.mesh("Face", head, "sphere", (0.105, 0.24), (0, 0, 0), skin)
    sc.mesh("Hair", head, "sphere", (0.112, 0.2), (0, 0.04, 0.02), hair)
    if hat == "non_la":
        sc.mesh("NonLa", head, "cyl", (0.005, 0.24, 0.15, 18), (0, 0.15, 0), hat_mat)
    elif hat == "mu_coi":
        sc.mesh("MuCoi", head, "sphere", (0.15, 0.17), (0, 0.07, 0), hat_mat)
        sc.mesh("Brim", head, "cyl", (0.17, 0.17, 0.012, 18), (0, 0.03, 0), hat_mat)
    elif hat == "khan":
        sc.mesh("Khan", head, "sphere", (0.118, 0.2), (0, 0.035, 0.015), hat_mat)
    return g


def standing_person(sc, name, parent, pos, rot_y, shirt, pants, skin, hair, arm_up=True, bag=None):
    g = sc.empty(name, parent, pos, rot_y)
    for sx in (-1, 1):
        sc.mesh("Leg", g, "box", (0.14, 0.82, 0.15), (sx * 0.09, 0.41, 0), pants)
        sc.mesh("Foot", g, "box", (0.12, 0.06, 0.24), (sx * 0.09, 0.03, -0.04), hair)
    sc.mesh("Torso", g, "box", (0.4, 0.6, 0.22), (0, 1.12, 0), shirt)
    sc.mesh("ArmL", g, "box", (0.09, 0.62, 0.1), (-0.25, 1.1, 0), shirt)
    if arm_up:
        sc.mesh("ArmR", g, "box", (0.09, 0.62, 0.1), (0.25, 1.68, 0), shirt)
    else:
        sc.mesh("ArmR", g, "box", (0.09, 0.62, 0.1), (0.25, 1.1, 0), shirt)
    sc.mesh("Neck", g, "cyl", (0.05, 0.05, 0.08, 8), (0, 1.46, 0), skin)
    sc.mesh("Face", g, "sphere", (0.105, 0.24), (0, 1.6, 0), skin)
    sc.mesh("Hair", g, "sphere", (0.112, 0.2), (0, 1.64, 0.02), hair)
    if bag:
        sc.mesh("Bag", g, "box", (0.24, 0.2, 0.08), (-0.22, 0.9, -0.08), bag)
        sc.mesh("Strap", g, "box", (0.03, 0.75, 0.02), (0.02, 1.2, -0.12), bag, basis=basis_z(35))
    return g


# ---------------------------------------------------------------------------

def build_bus():
    sc = Scene("Bus")
    p_rid = sc.ext_res("PackedScene", "res://scenes/player/Player.tscn")
    level_script = sc.ext_res("Script", "res://scripts/bus/BusLevel.gd")
    scroll_script = sc.ext_res("Script", "res://scripts/bus/ScrollingScenery.gd")

    # --- Vật liệu dùng chung ---
    paint_in = sc.pbr("BusPaintInterior", "painted_wood", (0.62, 0.8, 0.74), normal=0.6)  # xanh ngọc cũ
    paint_out = sc.pbr("BusPaintExterior", "painted_wood", (0.45, 0.62, 0.85), normal=0.8)
    floor_wood = sc.pbr("BusFloor", "wood_weathered", (0.75, 0.68, 0.6), normal=1.0)
    ceiling = sc.pbr("BusCeiling", "plaster_white", (0.86, 0.84, 0.76), normal=0.6)
    rust = sc.pbr("Rust", "rust_metal", (1, 1, 1), metallic=0.5)
    chrome = sc.mat("BusChrome", (0.66, 0.66, 0.64), 0.3, metallic=0.9)
    rubber = sc.mat("Rubber", (0.06, 0.06, 0.06), 0.85)
    dash = sc.mat("Dashboard", (0.12, 0.12, 0.13), 0.7)
    seat_frame = sc.mat("SeatFrame", (0.25, 0.27, 0.28), 0.5, metallic=0.6)
    tube_off = sc.mat("TubeOff", (0.82, 0.84, 0.86), 0.3)

    # --- Vật liệu ban ngày ---
    vinyl = sc.mat("VinylRed", (0.55, 0.12, 0.09), 0.45)
    vinyl_blue = sc.mat("VinylBlue", (0.16, 0.26, 0.5), 0.45)
    glass = sc.mat("BusGlass", (0.75, 0.85, 0.85), 0.05, alpha=0.18)
    curtain = sc.pbr("Curtain", "fabric", (0.85, 0.62, 0.4), normal=0.8)
    flower = sc.mat("PlasticFlower", (0.9, 0.2, 0.35), 0.5)
    leaf = sc.mat("PlasticLeaf", (0.2, 0.55, 0.25), 0.5)
    gold = sc.mat("Gold", (0.75, 0.56, 0.24), 0.35, metallic=0.85)
    tube_on = sc.mat("TubeDay", (0.9, 0.92, 0.95), 0.3, emission=(0.8, 0.85, 0.9), energy=0.3)
    skin = sc.mat("Skin", (0.62, 0.46, 0.36), 0.8)
    skin_old = sc.mat("SkinOld", (0.55, 0.42, 0.34), 0.85)
    hair = sc.mat("Hair", (0.05, 0.045, 0.04), 0.9)
    hair_grey = sc.mat("HairGrey", (0.55, 0.53, 0.5), 0.9)
    non_la = sc.mat("NonLa", (0.78, 0.7, 0.5), 0.9, cull=True)
    mu_coi = sc.mat("MuCoi", (0.3, 0.36, 0.22), 0.7)
    khan = sc.mat("KhanRan", (0.2, 0.18, 0.16), 0.95)
    shirts = [sc.mat("Shirt%d" % i, c, 0.95) for i, c in enumerate([
        (0.85, 0.83, 0.78), (0.35, 0.4, 0.3), (0.5, 0.32, 0.22), (0.3, 0.38, 0.55), (0.78, 0.7, 0.55),
        (0.62, 0.25, 0.22), (0.86, 0.86, 0.9), (0.4, 0.3, 0.38)])]
    pants = [sc.mat("Pants%d" % i, c, 0.95) for i, c in enumerate([
        (0.08, 0.08, 0.09), (0.25, 0.28, 0.22), (0.18, 0.2, 0.28), (0.3, 0.26, 0.2)])]
    ao_nau = sc.mat("AoNau", (0.38, 0.24, 0.15), 0.95)  # áo nâu bà cụ
    sack = sc.pbr("Sack", "fabric", (0.8, 0.72, 0.55), normal=1.2)
    basket = sc.pbr("Basket", "bamboo_weave", (1, 0.9, 0.75), normal=1.0)
    chicken = sc.mat("Chicken", (0.62, 0.38, 0.18), 0.9)
    comb = sc.mat("Comb", (0.75, 0.1, 0.08), 0.7)

    # --- Vật liệu hoang tàn ---
    vinyl_rot = sc.mat("VinylRotten", (0.24, 0.1, 0.08), 0.8)
    vinyl_rot_blue = sc.mat("VinylRottenBlue", (0.1, 0.13, 0.2), 0.8)
    foam = sc.mat("Foam", (0.58, 0.5, 0.3), 1.0)
    glass_dirty = sc.mat("GlassDirty", (0.22, 0.22, 0.2), 0.4, alpha=0.38)
    curtain_rot = sc.pbr("CurtainRotten", "fabric", (0.32, 0.26, 0.2), normal=1.4)
    tube_dead = sc.mat("TubeDead", (0.3, 0.3, 0.28), 0.6)
    tube_cold = sc.mat("TubeCold", (0.85, 0.95, 1.0), 0.3, emission=(0.7, 0.85, 1.0), energy=2.5)
    hat_rot = sc.mat("NonLaRotten", (0.3, 0.26, 0.18), 1.0, cull=True)
    leaf_dry = sc.mat("LeafDry", (0.32, 0.24, 0.12), 1.0, cull=True)
    shard = sc.mat("GlassShard", (0.7, 0.75, 0.75), 0.05, metallic=0.4, alpha=0.6)
    stain = sc.mat("DarkStain", (0.08, 0.02, 0.02), 0.6)
    wood_sign = sc.pbr("SignWood", "wood_weathered", (0.7, 0.62, 0.55), normal=1.4)

    d_mold = sc.decal_mat("DecalMold", "mold.png", (0.6, 0.65, 0.5, 0.9))
    d_soot = sc.decal_mat("DecalSoot", "soot.png", (1, 1, 1, 0.85))
    d_stain = sc.decal_mat("DecalStain", "stain_damp.png", (0.9, 0.85, 0.75, 0.9))
    d_scratch = sc.decal_mat("DecalScratch", "scratches.png", (0.9, 0.9, 0.9, 0.8))
    d_hand = sc.decal_mat("DecalHand", "handprint.png", (0.35, 0.06, 0.05, 0.9))
    d_crack = sc.decal_mat("DecalCrack", "crack.png", (1, 1, 1, 0.9))
    d_web = sc.decal_mat("DecalWeb", "cobweb.png", (1, 1, 1, 0.85))
    d_joss = sc.decal_mat("DecalJoss", "joss_paper.png", (1, 1, 1, 1))
    d_talisman = sc.decal_mat("DecalTalisman", "talisman.png", (1, 1, 1, 1))

    # --- Môi trường ---
    env_day = env_resource(sc, "Day", (0.32, 0.48, 0.72), (0.95, 0.72, 0.45), (0.2, 0.18, 0.12),
                           (1.0, 0.86, 0.68), 0.55, (0.95, 0.78, 0.55), 0.004, exposure=1.0)
    env_derelict = env_resource(sc, "Derelict", (0.02, 0.025, 0.04), (0.08, 0.1, 0.12), (0.02, 0.02, 0.02),
                                (0.3, 0.38, 0.48), 0.22, (0.12, 0.15, 0.18), 0.09, exposure=1.1,
                                sky_energy=0.3)

    sc.nodes[0] = ('[node name="Bus" type="Node3D"]\nscript = ExtResource("%s")\n'
                   'day_environment = SubResource("%s")\nderelict_environment = SubResource("%s")\n'
                   % (level_script, env_day, env_derelict))
    sc.node("WorldEnvironment", "WorldEnvironment", ".", [("environment", 'SubResource("%s")' % env_day)])

    length = Z_BACK - Z_FRONT
    zc = (Z_BACK + Z_FRONT) / 2

    # =======================================================================
    # VỎ XE (dùng chung, có va chạm)
    # =======================================================================
    body = sc.group("Shell")
    sc.box("Outer", body, (0, H / 2 - 0.1, zc), (2 * HALF_W + 2 * WALL, H + 0.2 + WALL, length + 2 * WALL),
           paint_out)
    sc.box("Inner", body, (0, H / 2, zc), (2 * HALF_W, H, length), paint_in, subtract=True)
    for side in (-1, 1):
        for i, z in enumerate(ROWS + [BENCH_Z]):
            sc.box("Window", body, (side * (HALF_W + WALL / 2), (WIN_Y[0] + WIN_Y[1]) / 2, z),
                   (WALL * 3, WIN_Y[1] - WIN_Y[0], WIN_W), rubber, subtract=True)
    # Ô kính trên cánh cửa lên xuống, kính chắn gió, kính sau.
    door_zc = (DOOR_Z[0] + DOOR_Z[1]) / 2
    sc.box("DoorWindow", body, (HALF_W + WALL / 2, 1.35, door_zc), (WALL * 3, 0.8, 0.7), rubber, subtract=True)
    sc.box("Windshield", body, (0, 1.45, Z_FRONT - WALL / 2), (2 * HALF_W - 0.2, 0.85, WALL * 3), rubber,
           subtract=True)
    sc.box("RearWindow", body, (0, 1.4, Z_BACK + WALL / 2), (1.6, 0.6, WALL * 3), rubber, subtract=True)

    fx = sc.empty("Fixtures")
    sc.mesh("Floor", fx, "box", (2 * HALF_W, 0.01, length), (0, 0.005, zc), floor_wood)
    sc.mesh("CeilingPanel", fx, "box", (2 * HALF_W, 0.01, length), (0, H - 0.005, zc), ceiling)
    lower = sc.pbr("BusPaintLower", "painted_wood", (0.34, 0.46, 0.42), normal=0.8)
    sc.mesh("Wainscot_L", fx, "box", (0.01, 0.9, length), (-HALF_W + 0.005, 0.45, zc), lower)
    sc.mesh("Wainscot_R", fx, "box", (0.01, 0.9, length), (HALF_W - 0.005, 0.45, zc), lower)
    for side in (-1, 1):
        # Tay vịn trần dọc lối đi + giá hành lý trên đầu ghế.
        sc.mesh("Rail", fx, "cyl", (0.016, 0.016, length - 1.2, 10), (side * 0.42, 1.95, zc + 0.4), chrome,
                basis=basis_x(90))
        sc.mesh("RackBar", fx, "cyl", (0.012, 0.012, length - 1.2, 8), (side * 0.85, 1.82, zc + 0.4), chrome,
                basis=basis_x(90))
        sc.mesh("RackBar", fx, "cyl", (0.012, 0.012, length - 1.2, 8), (side * 1.18, 1.82, zc + 0.4), chrome,
                basis=basis_x(90))
        for z in ROWS[::2]:
            sc.mesh("RackBracket", fx, "box", (0.36, 0.02, 0.02), (side * 1.02, 1.82, z), chrome)
            sc.mesh("RailHanger", fx, "cyl", (0.008, 0.008, 0.2, 6), (side * 0.42, 2.05, z), chrome)
        for i, z in enumerate(ROWS + [BENCH_Z]):
            # Khung cửa sổ: thanh trượt nhôm giữa ô kính.
            sc.mesh("WinTrack", fx, "box", (0.03, 0.025, WIN_W), (side * (HALF_W - 0.01), WIN_Y[0] + 0.01, z), chrome)
    # Đèn tuýp trên trần (ban ngày tắt, mesh dùng chung).
    for z in (-2.5, 0.5, 3.0):
        sc.mesh("TubeHousing", fx, "box", (0.12, 0.04, 1.2), (0, H - 0.03, z), seat_frame)
    # Buồng lái.
    cab = sc.group("Cab", ".", (0, 0, 0))
    sc.box("DashBase", cab, (0, 0.55, Z_FRONT + 0.35), (2 * HALF_W, 1.1, 0.6), dash)
    sc.box("EngineHump", cab, (-0.05, 0.3, Z_FRONT + 0.95), (0.7, 0.6, 0.8), rust)
    sc.box("DriverSeatBase", cab, (-0.7, 0.25, -4.05), (0.5, 0.5, 0.5), seat_frame)
    sc.box("DriverSeatBack", cab, (-0.7, 0.85, -3.8), (0.5, 0.7, 0.08), vinyl_rot_blue)
    sc.box("DriverPartition", cab, (-0.72, 0.55, -3.62), (0.95, 1.1, 0.04), paint_in)
    sc.box("Step", cab, (0.95, 0.1, door_zc), (0.6, 0.2, 0.9), rubber)
    sc.mesh("SteeringColumn", fx, "cyl", (0.03, 0.03, 0.5, 8), (-0.7, 1.0, Z_FRONT + 0.55), dash,
            basis=basis_x(-55))
    sc.mesh("SteeringWheel", fx, "torus", (0.19, 0.22), (-0.7, 1.15, Z_FRONT + 0.75), dash,
            basis=basis_x(35))
    sc.mesh("GearStick", fx, "cyl", (0.012, 0.012, 0.5, 6), (-0.2, 0.75, -4.2), chrome, basis=basis_x(15))
    sc.mesh("GearKnob", fx, "sphere", (0.035, 0.07), (-0.2, 1.0, -4.27), dash)
    sc.mesh("Mirror", fx, "box", (0.32, 0.1, 0.02), (0, 1.95, Z_FRONT + 0.15), chrome)
    # Cánh cửa: tấm dưới đặc, phần trên là khung bao quanh ô kính (DoorWindow).
    dx = HALF_W - 0.012
    sc.mesh("DoorPanel", fx, "box", (0.02, 0.95, 0.85), (dx, 0.475, door_zc), paint_out)
    sc.mesh("DoorFrameTop", fx, "box", (0.02, 0.15, 0.85), (dx, 1.825, door_zc), paint_out)
    sc.mesh("DoorFrameFront", fx, "box", (0.02, 0.8, 0.075), (dx, 1.35, door_zc - 0.3875), paint_out)
    sc.mesh("DoorFrameBack", fx, "box", (0.02, 0.8, 0.075), (dx, 1.35, door_zc + 0.3875), paint_out)
    sc.mesh("DoorHandle", fx, "box", (0.04, 0.03, 0.18), (HALF_W - 0.04, 1.0, door_zc + 0.25), chrome)
    sc.mesh("DoorPole", fx, "cyl", (0.018, 0.018, H, 10), (0.55, H / 2, -3.62), chrome)
    sc.mesh("WindshieldBar", fx, "box", (0.05, 0.85, 0.05), (0, 1.45, Z_FRONT - 0.02), rubber)

    # =======================================================================
    # KHUNG GHẾ (dùng chung, có va chạm): mặt ngồi + chân ghế + khung lưng.
    # =======================================================================
    seats = sc.group("Seats")
    seat_rows = []  # (tên, tâm x, z) mỗi cặp ghế, dùng lại cho nệm ở hai trạng thái
    for side in (-1, 1):
        cx = side * (SEAT_X[0] + SEAT_X[1]) / 2
        pw = SEAT_X[1] - SEAT_X[0] + SEAT_W
        for r, z in enumerate(ROWS):
            nm = "%s%d" % ("L" if side < 0 else "R", r + 1)
            seat_rows.append((nm, cx, z, pw))
            sc.box("Pan" + nm, seats, (cx, SEAT_Y - 0.04, z), (pw, 0.05, SEAT_W), seat_frame)
            sc.box("Leg" + nm, seats, (side * SEAT_X[0], (SEAT_Y - 0.06) / 2, z - 0.1), (0.04, SEAT_Y - 0.06, 0.04),
                   seat_frame)
            sc.box("Strut" + nm, seats, (cx, 0.2, z + 0.15), (pw, 0.03, 0.03), seat_frame)
            sc.box("BackFrame" + nm, seats, (cx, 0.78, z + SEAT_W / 2), (pw, 0.62, 0.035), seat_frame,
                   basis=basis_x(8))
            sc.box("Grab" + nm, seats, (side * SEAT_X[0], 1.13, z + SEAT_W / 2 + 0.04), (0.18, 0.03, 0.03), chrome)
    sc.box("BenchPan", seats, (0, SEAT_Y - 0.04, BENCH_Z), (2 * HALF_W, 0.05, SEAT_W), seat_frame)
    sc.box("BenchBase", seats, (0, 0.2, BENCH_Z), (2 * HALF_W, 0.4, SEAT_W - 0.05), seat_frame)
    sc.box("BenchBack", seats, (0, 0.8, BENCH_Z + SEAT_W / 2 + 0.02), (2 * HALF_W, 0.7, 0.04), seat_frame)

    def cushions(parent, mats, broken=()):
        """Nệm ngồi + nệm lưng mỗi cặp ghế. broken: {tên: kiểu hỏng}."""
        broken = dict(broken)
        for i, (nm, cx, z, pw) in enumerate(seat_rows):
            m = mats[i % len(mats)]
            kind = broken.get(nm)
            if kind == "missing":
                continue
            seat_pos = (cx, SEAT_Y + 0.03, z - 0.01)
            back_basis = basis_x(8)
            back_pos = (cx, 0.8, z + SEAT_W / 2 - 0.035)
            if kind == "snapped":
                back_basis = basis_x(48)
                back_pos = (cx, 0.62, z + SEAT_W / 2 + 0.18)
            sc.mesh("Cushion" + nm, parent, "box", (pw - 0.04, 0.07, SEAT_W - 0.03), seat_pos, m)
            sc.mesh("Backrest" + nm, parent, "box", (pw - 0.04, 0.56, 0.06), back_pos, m, basis=back_basis)
            if kind in ("torn", "snapped"):
                # Nệm rách lòi mút vàng.
                sc.mesh("FoamSeat" + nm, parent, "box", (0.22, 0.02, 0.18),
                        (cx + random.uniform(-0.15, 0.15), SEAT_Y + 0.066, z), foam)
                sc.mesh("FoamBack" + nm, parent, "box", (0.18, 0.2, 0.02),
                        (back_pos[0] - 0.1, back_pos[1] + 0.05, back_pos[2] - 0.035), foam, basis=back_basis)
        sc.mesh("BenchCushion", parent, "box", (2 * HALF_W - 0.04, 0.07, SEAT_W - 0.03),
                (0, SEAT_Y + 0.03, BENCH_Z), mats[0])
        sc.mesh("BenchBackrest", parent, "box", (2 * HALF_W - 0.04, 0.6, 0.06),
                (0, 0.82, BENCH_Z + SEAT_W / 2 - 0.02), mats[0])

    # =======================================================================
    # TRẠNG THÁI 1: CHIỀU MUỘN, XE ĐÔNG KHÁCH ĐANG CHẠY
    # =======================================================================
    day = sc.empty("Day")
    cushions(sc.empty("Cushions", day), [vinyl, vinyl, vinyl_blue])
    for side in (-1, 1):
        for i, z in enumerate(ROWS + [BENCH_Z]):
            sc.mesh("Glass", day, "box", (0.008, WIN_Y[1] - WIN_Y[0], WIN_W),
                    (side * (HALF_W + WALL / 2), (WIN_Y[0] + WIN_Y[1]) / 2, z), glass, shadow=False)
            if i % 3 == 1:
                # Rèm vải cột gọn một bên ô cửa.
                sc.mesh("Curtain", day, "box", (0.03, 0.62, 0.12),
                        (side * (HALF_W - 0.03), 1.38, z - WIN_W / 2 + 0.06), curtain)
    sc.mesh("GlassDoor", day, "box", (0.008, 0.8, 0.7), (HALF_W + WALL / 2, 1.35, door_zc), glass, shadow=False)
    sc.mesh("GlassFront", day, "box", (2 * HALF_W - 0.2, 0.85, 0.008), (0, 1.45, Z_FRONT - WALL / 2), glass,
            shadow=False)
    sc.mesh("GlassRear", day, "box", (1.6, 0.6, 0.008), (0, 1.4, Z_BACK + WALL / 2), glass, shadow=False)
    for z in (-2.5, 0.5, 3.0):
        sc.mesh("Tube", day, "cyl", (0.018, 0.018, 1.1, 8), (0, H - 0.06, z), tube_on, basis=basis_x(90),
                shadow=False)

    # Bàn thờ nhỏ trên taplô: tượng Phật, lọ hoa nhựa, dây hoa treo kính.
    altar = sc.empty("DashAltar", day, (0.45, 1.1, Z_FRONT + 0.3))
    sc.mesh("Buddha", altar, "sphere", (0.05, 0.14), (0, 0.07, 0), gold)
    sc.mesh("BuddhaBase", altar, "cyl", (0.05, 0.06, 0.03, 12), (0, 0.015, 0), gold)
    sc.mesh("Vase", altar, "cyl", (0.025, 0.02, 0.1, 10), (0.15, 0.05, 0), gold)
    for k in range(4):
        sc.mesh("Flower", altar, "sphere", (0.03, 0.05), (0.15 + (k - 1.5) * 0.03, 0.14 + (k % 2) * 0.03, 0),
                flower)
    for k in range(9):
        x = -1.0 + k * 0.25
        sc.mesh("Garland", day, "sphere", (0.035, 0.06), (x, 1.92 - 0.06 * math.sin(k / 8 * math.pi),
                                                          Z_FRONT + 0.08), flower if k % 2 else leaf, shadow=False)
    sc.decal("Talisman", day, (0, 1.75, Z_FRONT + 0.1), "+z", (0.12, 0.3), d_talisman, offset=0.0)

    # Hành khách.
    pas = sc.empty("Passengers", day)
    L, R = -1, 1

    def seat_pos(side, row, outer):
        return (side * SEAT_X[1 if outer else 0], 0, ROWS[row])

    seated_person(sc, "Driver", pas, (-0.7, 0.05, -4.0), shirts[1], pants[1], skin, hair, "mu_coi", mu_coi)
    standing_person(sc, "Conductor", pas, (0.62, 0.0, -4.0), 150, shirts[3], pants[0], skin, hair, True,
                    sc.mat("LeatherBag", (0.3, 0.18, 0.1), 0.6))
    seated_person(sc, "Farmer", pas, seat_pos(L, 0, True), shirts[1], pants[1], skin, hair, "mu_coi", mu_coi)
    seated_person(sc, "Wife", pas, seat_pos(L, 0, False), shirts[4], pants[0], skin, hair, "khan", khan)
    seated_person(sc, "Trader", pas, seat_pos(R, 0, True), shirts[5], pants[0], skin, hair, "non_la", non_la,
                  head_tilt=6)
    seated_person(sc, "OldMan", pas, seat_pos(L, 1, True), shirts[0], pants[3], skin_old, hair_grey, lean=-6)
    seated_person(sc, "Mother", pas, seat_pos(R, 2, False), shirts[2], pants[0], skin, hair, "non_la", non_la)
    seated_person(sc, "OldWoman", pas, seat_pos(L, OLD_WOMAN_ROW, False), ao_nau, pants[0], skin_old, hair_grey,
                  "khan", khan, rot_y=-15)
    seated_person(sc, "Sleeper", pas, seat_pos(R, AN_ROW + 1, True), shirts[6], pants[2], skin, hair,
                  lean=-12, head_tilt=-22)
    seated_person(sc, "Student1", pas, seat_pos(L, 5, True), shirts[6], pants[2], skin, hair)
    seated_person(sc, "Student2", pas, seat_pos(L, 5, False), shirts[6], pants[2], skin, hair, head_tilt=8)
    seated_person(sc, "Soldier", pas, seat_pos(R, 6, False), shirts[1], pants[1], skin, hair, "mu_coi", mu_coi)
    seated_person(sc, "Woman2", pas, seat_pos(L, 7, True), shirts[7], pants[0], skin, hair, "non_la", non_la)

    # Giỏ gà dưới chân bà cụ, bao tải gạo và quang gánh ở cuối xe.
    props = sc.empty("Props", day)
    bx, bz = -SEAT_X[1] + 0.02, ROWS[OLD_WOMAN_ROW] - 0.42
    sc.mesh("Basket", props, "cyl", (0.2, 0.15, 0.24, 14), (bx, 0.12, bz), basket)
    sc.mesh("ChickenBody", props, "sphere", (0.11, 0.18), (bx, 0.3, bz), chicken)
    sc.mesh("ChickenHead", props, "sphere", (0.045, 0.09), (bx, 0.42, bz - 0.08), chicken)
    sc.mesh("ChickenComb", props, "box", (0.012, 0.04, 0.05), (bx, 0.47, bz - 0.08), comb)
    sc.mesh("NonLaLap", props, "cyl", (0.005, 0.24, 0.12, 18), (-SEAT_X[0], 0.68, ROWS[OLD_WOMAN_ROW] - 0.2),
            non_la, basis=basis_x(-70))
    for k, (x, y, rz) in enumerate([(-0.8, 0.62, 0), (-0.35, 0.62, 10), (0.15, 0.62, -6), (0.7, 0.62, 4),
                                     (0.35, 0.95, 80)]):
        sc.mesh("RiceSack", props, "box", (0.42, 0.32, 0.3), (x, y, BENCH_Z), sack, basis=basis_z(rz))
    for z in (ROWS[1] - 0.05, ROWS[5]):
        sc.mesh("Luggage", props, "box", (0.4, 0.22, 0.5), (1.02, 1.95, z), sack)
        sc.mesh("Luggage", props, "box", (0.36, 0.2, 0.42), (-1.02, 1.94, z + 0.4), basket)

    # Nắng chiều xiên từ bên phải xe.
    directional(sc, "Sun", day, -16, 65, (1.0, 0.78, 0.5), 2.2)
    dust(sc, "SunDust", day, (0.4, 1.3, 0.0), (0.9, 0.6, 3.5), amount=90, col=(1, 0.9, 0.7, 0.45))

    # Ngoài cửa sổ: mặt đất + đường (texture trôi) và cây cối, cột điện (trôi theo +Z).
    ground_mat = sc.pbr("PaddyGround", "grass", (0.42, 0.62, 0.22), triplanar=False, uv_scale=(60, 60))
    road_mat = sc.pbr("RoadEarth", "earth", (0.75, 0.68, 0.58), triplanar=False, uv_scale=(2, 60))
    out = sc.empty("Outside", day)
    sc.node("Ground", "MeshInstance3D", out, [
        ("transform", xform((0, -0.95, 0))), ("cast_shadow", "0"),
        ("mesh", 'SubResource("%s")' % sc.sub_res("PlaneMesh", "Mesh_Ground", [("size", "Vector2(200, 200)")])),
        ("material_override", 'SubResource("%s")' % ground_mat)])
    sc.node("Road", "MeshInstance3D", out, [
        ("transform", xform((0.3, -0.94, 0))), ("cast_shadow", "0"),
        ("mesh", 'SubResource("%s")' % sc.sub_res("PlaneMesh", "Mesh_Road", [("size", "Vector2(6.5, 200)")])),
        ("material_override", 'SubResource("%s")' % road_mat)])
    trunk = sc.mat("Trunk", (0.3, 0.24, 0.18), 0.9)
    foliage = sc.mat("Foliage", (0.22, 0.38, 0.14), 0.8)
    bamboo = sc.mat("Bamboo", (0.42, 0.52, 0.22), 0.7)
    pole = sc.mat("ConcretePole", (0.62, 0.6, 0.56), 0.9)
    straw = sc.mat("Haystack", (0.72, 0.6, 0.32), 1.0)
    wall_house = sc.mat("HouseWall", (0.82, 0.72, 0.5), 0.9)
    roof = sc.mat("HouseRoof", (0.55, 0.25, 0.15), 0.9)
    sc_node = sc.node("Scenery", "Node3D", out, [
        ("script", 'ExtResource("%s")' % scroll_script),
        ("scrolling_materials", 'Array[BaseMaterial3D]([SubResource("%s"), SubResource("%s")])'
         % (ground_mat, road_mat)),
    ])
    # Lũy tre làng xa xa: dải cây liền dọc hai bên đường, đủ xa để không cần trôi.
    for side in (-1, 1):
        for k, (x, h) in enumerate([(32, 6.0), (55, 9.0)]):
            sc.mesh("TreeLine", out, "box", (6.0, h, 200.0), (side * x + random.uniform(-2, 2), -0.95 + h / 2, 0),
                    foliage if k == 0 else sc.mat("TreeLineFar", (0.3, 0.42, 0.28), 1.0), shadow=False)
            for b in range(14):
                z = -95 + b * 14 + random.uniform(-4, 4)
                sc.mesh("TreeTop", out, "sphere", (4.0, 5.5), (side * x, -0.95 + h + 0.5, z), foliage, shadow=False)
        # Bờ ruộng chạy song song với đường.
        for x in (8.0, 14.0, 21.0):
            sc.mesh("Dike", out, "box", (0.5, 0.18, 200.0), (side * x, -0.88, 0), road_mat, shadow=False)
    span = 120.0
    for k in range(26):
        side = 1 if k % 2 == 0 else -1
        z = -span / 2 + k * span / 26 + random.uniform(-1.5, 1.5)
        x = side * random.uniform(5.0, 16.0)
        kind = random.choice(["tree", "tree", "bamboo", "bamboo", "hay", "house"])
        g = sc.empty("Prop%d" % k, sc_node, (x, -0.95, z), random.uniform(0, 360))
        if kind == "tree":
            sc.mesh("Trunk", g, "cyl", (0.12, 0.18, 2.6, 8), (0, 1.3, 0), trunk)
            sc.mesh("Crown", g, "sphere", (1.6, 2.4), (0, 3.2, 0), foliage)
        elif kind == "bamboo":
            for b in range(5):
                sc.mesh("Cane", g, "cyl", (0.05, 0.06, 5.5, 6), (b * 0.25 - 0.5, 2.6, (b % 2) * 0.3), bamboo,
                        basis=basis_z(-6 + b * 3))
            sc.mesh("Leaves", g, "sphere", (1.4, 2.0), (0, 5.0, 0), foliage)
        elif kind == "hay":
            sc.mesh("Hay", g, "cyl", (0.3, 1.1, 1.8, 12), (0, 0.9, 0), straw)
        else:
            sc.mesh("Walls", g, "box", (4.0, 2.4, 3.0), (0, 1.2, 0), wall_house)
            sc.mesh("Roof", g, "prism", (4.6, 1.3, 3.4), (0, 3.05, 0), roof, basis=basis_y(90))
    for k in range(6):
        g = sc.empty("Pole%d" % k, sc_node, (3.6, -0.95, -span / 2 + k * span / 6))
        sc.mesh("Post", g, "box", (0.2, 7.0, 0.2), (0, 3.5, 0), pole)
        sc.mesh("Arm", g, "box", (1.4, 0.1, 0.1), (0, 6.6, 0), pole)

    # =======================================================================
    # TRẠNG THÁI 2: XE BỎ HOANG, ĐỖ IM TRONG SƯƠNG ĐÊM
    # =======================================================================
    der = sc.empty("Derelict", ".", props=[("visible", "false")])
    cushions(sc.empty("Cushions", der), [vinyl_rot, vinyl_rot, vinyl_rot_blue], broken={
        "L1": "torn", "R2": "snapped", "L3": "torn", "R5": "torn", "L6": "snapped", "R7": "missing",
        "L8": "torn", "R9": "snapped",
    })
    broken_windows = {("R", 1), ("L", 4), ("R", 7), ("L", 8)}
    for side in (-1, 1):
        sname = "L" if side < 0 else "R"
        for i, z in enumerate(ROWS + [BENCH_Z]):
            gx = side * (HALF_W + WALL / 2)
            if (sname, i) in broken_windows:
                sc.mesh("GlassShardEdge", der, "prism", (0.008, 0.22, WIN_W * 0.6),
                        (gx, WIN_Y[0] + 0.11, z), shard, shadow=False)
                continue
            sc.mesh("Glass", der, "box", (0.008, WIN_Y[1] - WIN_Y[0], WIN_W), (gx, (WIN_Y[0] + WIN_Y[1]) / 2, z),
                    glass_dirty, shadow=False)
            if i % 3 == 2:
                sc.decal("Crack", der, (side * (HALF_W - 0.01), 1.3, z), "-x" if side > 0 else "+x", (0.5, 0.5),
                         d_crack, roll=random.uniform(0, 360), offset=0.0)
            if i % 3 == 0:
                sc.mesh("CurtainRag", der, "box", (0.02, 0.85, 0.2),
                        (side * (HALF_W - 0.03), 1.25, z + WIN_W / 2 - 0.1), curtain_rot, basis=basis_x(4))
    sc.mesh("GlassDoor", der, "box", (0.008, 0.8, 0.7), (HALF_W + WALL / 2, 1.35, door_zc), glass_dirty,
            shadow=False)
    sc.mesh("GlassFront", der, "box", (2 * HALF_W - 0.2, 0.85, 0.008), (0, 1.45, Z_FRONT - WALL / 2), glass_dirty,
            shadow=False)
    sc.decal("CrackFront", der, (-0.6, 1.5, Z_FRONT + 0.0), "+z", (0.9, 0.9), d_crack, roll=40, offset=0.01)
    sc.mesh("GlassRear", der, "box", (1.6, 0.6, 0.008), (0, 1.4, Z_BACK + WALL / 2), glass_dirty, shadow=False)
    # Bàn tay in trên kính cửa xe và một ô kính bên phải, như ai đó ở ngoài áp vào.
    sc.decal("HandDoor", der, (HALF_W - 0.005, 1.45, door_zc + 0.1), "-x", (0.2, 0.24), d_hand, roll=-8,
             offset=0.0)
    sc.decal("HandWindow", der, (HALF_W - 0.005, 1.35, ROWS[AN_ROW] + 0.12), "-x", (0.2, 0.24), d_hand, roll=12,
             offset=0.0)
    sc.decal("HandWindow", der, (HALF_W - 0.005, 1.2, ROWS[AN_ROW] - 0.15), "-x", (0.2, 0.24), d_hand, roll=-20,
             offset=0.0)

    # Đèn tuýp: một bóng còn chập chờn, hai bóng chết.
    for z in (-2.5, 3.0):
        sc.mesh("TubeDead", der, "cyl", (0.018, 0.018, 1.1, 8), (0, H - 0.06, z), tube_dead, basis=basis_x(90),
                shadow=False)
    sc.mesh("TubeHanging", der, "cyl", (0.018, 0.018, 1.1, 8), (0.1, H - 0.35, 3.0), tube_dead,
            basis=basis_mul(basis_x(90), basis_z(-30)), shadow=False)
    tube_light = sc.node("TubeLight", "OmniLight3D", der, [
        ("transform", xform((0, H - 0.12, 0.5))),
        ("light_color", color((0.72, 0.86, 1.0))), ("light_energy", "1.1"), ("omni_range", "6.0"),
        ("omni_attenuation", "1.2"), ("shadow_enabled", "true"), ("shadow_blur", "1.5"),
        ("script", 'ExtResource("%s")' % sc.ext_res("Script", "res://scripts/levels/LightFlicker.gd")),
        ("hum", "0.12"), ("calm_range", "Vector2(1.5, 5)"), ("burst_count", "Vector2i(3, 9)"), ("dip", "0.02"),
        ("emissive_mesh", 'NodePath("Tube")'),
    ])
    sc.mesh("Tube", tube_light, "cyl", (0.018, 0.018, 1.1, 8), (0, 0.06, 0), tube_cold, basis=basis_x(90),
            shadow=False)
    sc.node("DashGlow", "OmniLight3D", der, [
        ("transform", xform((0.45, 1.3, Z_FRONT + 0.4))),
        ("light_color", color((0.9, 0.2, 0.12))), ("light_energy", "0.35"), ("omni_range", "1.8"),
    ])
    directional(sc, "Moon", der, -24, 160, (0.42, 0.52, 0.72), 0.25)

    # Vết mục: mốc, muội, ố, cào xước trên vách, trần và sàn.
    for k in range(14):
        side = random.choice((-1, 1))
        z = random.uniform(Z_FRONT + 1.5, Z_BACK - 0.3)
        y = random.choice((random.uniform(0.25, 0.8), random.uniform(1.75, 2.0)))
        mat = random.choice((d_mold, d_soot, d_stain, d_stain))
        sc.decal("WallRot", der, (side * (HALF_W - 0.01), y, z), "-x" if side > 0 else "+x",
                 (random.uniform(0.5, 1.1),) * 2, mat, roll=random.uniform(0, 360), offset=0.002)
    for k in range(7):
        sc.decal("CeilRot", der, (random.uniform(-1.0, 1.0), H - 0.012, random.uniform(-3.5, 4.0)), "-y",
                 (random.uniform(0.6, 1.3),) * 2, random.choice((d_mold, d_stain, d_soot)),
                 roll=random.uniform(0, 360), offset=0.0)
    for k in range(6):
        sc.decal("FloorGrime", der, (random.uniform(-0.4, 0.4), 0.012, random.uniform(-3.5, 4.0)), "+y",
                 (random.uniform(0.6, 1.1),) * 2, random.choice((d_stain, d_soot)), roll=random.uniform(0, 360),
                 offset=0.0)
    sc.decal("Scratch", der, (-HALF_W + 0.01, 1.2, ROWS[2] + 0.4), "+x", (0.5, 0.4), d_scratch, offset=0.003)
    sc.decal("Scratch", der, (0.28, 0.85, ROWS[AN_ROW] + SEAT_W / 2 + 0.07), "+z", (0.3, 0.3), d_scratch,
             roll=90, offset=0.0)
    for x, y, z, facing in [(-HALF_W + 0.01, 1.95, Z_BACK - 0.2, "+x"), (HALF_W - 0.01, 1.95, Z_FRONT + 1.4, "-x"),
                            (-HALF_W + 0.01, 1.9, ROWS[4], "+x"), (0.9, H - 0.012, ROWS[1], "-y")]:
        sc.decal("Cobweb", der, (x, y, z), facing, (0.7, 0.7), d_web, offset=0.0)
    sc.decal("TalismanTorn", der, (0, 1.75, Z_FRONT + 0.1), "+z", (0.12, 0.3), d_talisman, roll=14, offset=0.0)

    # Rác trên sàn: vàng mã, lá khô, mảnh kính, nệm rơi, giỏ gà đổ, nón mục của bà cụ.
    deb = sc.empty("Debris", der)
    for k in range(26):
        x = random.uniform(-1.1, 1.1)
        z = random.uniform(Z_FRONT + 1.4, Z_BACK - 0.3)
        sc.decal("Joss", deb, (x, 0.014 + k * 0.0004, z), "+y", (0.16, 0.2), d_joss, roll=random.uniform(0, 360),
                 offset=0.0)
    for k in range(30):
        sc.mesh("DryLeaf", deb, "box", (0.07, 0.004, 0.04),
                (random.uniform(-1.1, 1.1), 0.015, random.uniform(Z_FRONT + 1.4, Z_BACK - 0.3)), leaf_dry,
                rot_y=random.uniform(0, 360), shadow=False)
    for (wx, wi) in ((1, 1), (-1, 4), (1, 7), (-1, 8)):
        z = (ROWS + [BENCH_Z])[wi]
        for k in range(6):
            sc.mesh("Shard", deb, "prism", (0.06, 0.004, 0.05),
                    (wx * random.uniform(0.25, 1.0), 0.47 if k < 2 else 0.015, z + random.uniform(-0.3, 0.3)),
                    shard, rot_y=random.uniform(0, 360), shadow=False)
    sc.mesh("FallenCushion", deb, "box", (0.82, 0.07, 0.39), (0.15, 0.05, ROWS[6] - 0.3), vinyl_rot,
            basis=basis_mul(basis_y(24), basis_z(6)))
    sc.mesh("FallenFoam", deb, "box", (0.25, 0.02, 0.2), (0.25, 0.09, ROWS[6] - 0.25), foam, rot_y=24)
    bx, bz = -SEAT_X[1] + 0.05, ROWS[OLD_WOMAN_ROW] - 0.42
    sc.mesh("BasketTipped", deb, "cyl", (0.2, 0.15, 0.24, 14), (bx, 0.17, bz), basket,
            basis=basis_mul(basis_y(30), basis_z(80)))
    for k in range(5):
        sc.mesh("Feather", deb, "box", (0.05, 0.003, 0.015), (bx + random.uniform(0.1, 0.5), 0.016,
                                                              bz + random.uniform(-0.2, 0.3)),
                sc.mat("Feather", (0.45, 0.32, 0.2), 1.0), rot_y=random.uniform(0, 360), shadow=False)
    sc.mesh("Bag", deb, "box", (0.4, 0.22, 0.5), (1.02, 1.95, ROWS[1] - 0.05), sack, rot_y=8)
    # Năm vết thâm đen trên lưng ghế An vừa tựa (khớp 5 vết đinh trên người An).
    back_z = ROWS[AN_ROW] + SEAT_W / 2 - 0.075
    for k, (dx, dy) in enumerate([(0.0, 0.25), (-0.1, 0.12), (0.1, 0.12), (-0.07, -0.02), (0.07, -0.02)]):
        sc.mesh("Stain%d" % (k + 1), deb, "cyl", (0.022, 0.026, 0.004, 10),
                (SEAT_X[1] + dx, 0.82 + dy, back_z), stain, basis=basis_x(98), shadow=False)
    dust(sc, "Dust", der, (0, 1.2, 0.0), (1.1, 0.8, 4.3), amount=140, col=(0.8, 0.88, 1.0, 0.4))

    # Bên ngoài: bãi đất trống, cột biển báo bến xe mục, cây chết trong sương.
    outd = sc.empty("OutsideDerelict", der)
    sc.node("Ground", "MeshInstance3D", outd, [
        ("transform", xform((0, -0.95, 0))),
        ("mesh", 'SubResource("Mesh_Ground")'),
        ("material_override", 'SubResource("%s")' % sc.pbr("DeadGround", "earth", (0.35, 0.33, 0.3)))])
    sign = sc.empty("BusStopSign", outd, (2.6, -0.95, ROWS[AN_ROW] - 1.2), -90)
    sc.mesh("Post", sign, "box", (0.08, 2.3, 0.08), (0, 1.15, 0), rust, basis=basis_z(4))
    sc.mesh("Board", sign, "box", (0.9, 0.42, 0.03), (0.05, 2.25, 0), wood_sign, basis=basis_z(-7))
    sc.node("Label", "Label3D", sign, [
        ("transform", xform((0.05, 2.25, 0.02), basis=basis_z(-7))),
        ("pixel_size", "0.0022"), ("modulate", color((0.12, 0.1, 0.08))), ("outline_size", "0"),
        ("text", '"SIGN_BUS_STOP_THON_DOAI"'), ("font_size", "64"), ("width", "380.0"), ("autowrap_mode", "3"),
        ("horizontal_alignment", "1"),
    ])
    for k, (x, z) in enumerate([(-6.0, -3.0), (7.5, 4.0), (-9.0, 9.0), (5.0, -9.0)]):
        g = sc.empty("DeadTree%d" % k, outd, (x, -0.95, z), k * 70)
        sc.mesh("Trunk", g, "cyl", (0.1, 0.22, 4.0, 8), (0, 2.0, 0), trunk)
        for b in range(4):
            sc.mesh("Branch", g, "cyl", (0.03, 0.07, 1.8, 6), (0.3 * (b - 1.5), 3.2 + b * 0.25, 0), trunk,
                    basis=basis_mul(basis_y(b * 80), basis_z(40 + b * 6)))

    # Người chơi đứng ở chân cửa xe, nhìn dọc lối đi về phía sau.
    sc.instance("Player", p_rid, props=[("transform", xform((0.0, 0.05, -3.1), 180))])
    sc.save("scenes/levels/Bus.tscn")


if __name__ == "__main__":
    build_bus()
