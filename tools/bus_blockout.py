#!/usr/bin/env python3
"""Sinh bối cảnh xe khách liên tỉnh thập niên 199x: scenes/levels/Bus.tscn

Chạy:  python3 -m pip install pillow && python3 tools/bus_blockout.py
(script tự sinh lại texture vẽ tay ở assets/textures/bus/ và mesh ở assets/models/bus/,
sau đó mở Godot một lần - hoặc chạy `godot --headless --import` - để nhập file mới.)

Một scene, ba lớp nhìn (BusLevel.gd bật/tắt):
- Day: chiếc xe thật năm 2006, chiều muộn, đông khách, cảnh ngoài cửa sổ trôi qua
  (ScrollingScenery.gd), nắng vàng xiên qua kính.
- Derelict: xác chiếc xe năm 1999 nằm bãi sông: gỉ sét, vệt nước ngập ngang giá hành lý,
  rêu, kính vỡ, nệm rách, đèn tuýp chập chờn.
- Night1999: đêm 14/04/1999 ngay trước tai nạn: xe nguyên vẹn nhưng cũ, mất điện, mưa
  đứng yên ngoài kính, chỉ có đèn bão của phụ xe và đèn pha rọi vào màn mưa.

Hình học chi tiết (vỏ xe, ghế, buồng lái...) sinh bằng tools/bus_models.py; ba lớp dùng chung
mesh, chỉ khác vật liệu. Va chạm là các hộp đơn giản trong node Collision (dùng chung).

Hệ tọa độ: đầu xe hướng -Z, cửa lên xuống bên phải (+X), sàn xe ở y = 0.
LƯU Ý: chạy lại script sẽ GHI ĐÈ scenes/levels/Bus.tscn.
"""

import math
import random

from level_blockout import (CC0, Scene, basis_mul, basis_scale, basis_x, basis_y, basis_z, color, dust, f,
                            vec3, xform)

# --- Kích thước lòng xe (mét) ---
HALF_W = 1.25          # nửa bề ngang lòng xe
H = 2.15               # chiều cao lòng xe (giữa trần)
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

# ---------------------------------------------------------------------------
# Chương 2: chỗ ngồi của các hồn trên chuyến xe đêm 14/04/1999.
# (bên, hàng, sát cửa sổ). Bên trái L = -1, bên phải R = 1.
# ---------------------------------------------------------------------------
L_SIDE, R_SIDE = -1, 1
NUMBERED_SEATS = {  # số ghế dán trên vách, khớp sổ phụ xe
    "03": (L_SIDE, 1, True), "04": (L_SIDE, 1, False), "05": (L_SIDE, 2, True),
    "07": (R_SIDE, AN_ROW, True), "08": (R_SIDE, AN_ROW + 1, True),
}
NAM_SEAT = (L_SIDE, OLD_WOMAN_ROW, False)   # bà Năm = bà cụ ngồi cạnh An trên xe ban ngày
HUNG_SEAT = (R_SIDE, 2, False)
LAMP_POS = (1.0, 1.5, Z_BACK - 0.1)        # móc treo đèn bão, vách sau bên phải
BOARD_POS = (-HALF_W + 0.02, 1.45, -3.42)  # bảng lộ trình trên vách trái, sau ghế lái
WATERLINE_Y = 1.72                          # vệt nước ngập, ngay dưới giá hành lý
RACK_Y = 1.82


def seat_xz(seat):
    side, row, outer = seat
    return side * SEAT_X[1 if outer else 0], ROWS[row]


# Người ngồi / đứng (hành khách xe 2006, thân xác An) và hình nhân giấy dựng chung một bộ khung:
# xem tools/people_models.py.
def seated_person(*args, **kw):
    import people_models
    return people_models.seated_person(*args, **kw)


def standing_person(*args, **kw):
    import people_models
    return people_models.standing_person(*args, **kw)


def storm_lamp(sc, name, parent, pos, metal, glass_mat, flame=None, rot_y=0.0):
    """Đèn bão có quai xách (mesh tiện tròn ở tools/people_models.py). Gốc tọa độ ở đáy đèn."""
    import people_models
    return people_models.storm_lamp(sc, name, parent, pos, metal, glass_mat, flame, rot_y)


def windshield_number(sc, parent):
    """Decal số xe dán phía NGOÀI kính lái: đứng trong xe nhìn ra thì chữ bị ngược như soi gương."""
    for txt, y, size, pix in (("385", 1.16, 96, 0.0016), ("BUS_DECAL_ROUTE", 1.07, 40, 0.0012)):
        sc.node("NumberDecal", "Label3D", parent, [
            ("transform", xform((0.62, y, Z_FRONT - 0.035), 180)),
            ("pixel_size", f(pix)), ("modulate", color((0.95, 0.86, 0.55))), ("outline_size", "0"),
            ("alpha_cut", "1"), ("text", '"%s"' % txt), ("font_size", str(size)),
        ])


# ---------------------------------------------------------------------------
# Vật liệu
# ---------------------------------------------------------------------------

def uvmat(sc, name, tex, tint=(1, 1, 1), rough=1.0, metallic=0.0, normal=1.0, scale=1.0):
    """Vật liệu PBR CC0 cho mesh có UV tính bằng mét (mesh sinh ở tools/bus_models.py)."""
    k = 1.0 / (CC0[tex]["size_m"] * scale)
    return sc.pbr(name, tex, tint, rough=rough, normal=normal, metallic=metallic, triplanar=False, uv_scale=(k, k))


def texmat(sc, name, png, tint=(1, 1, 1, 1), rough=0.8, alpha=False, uv=(1, 1), emission=None, energy=1.0,
           metallic=0.0, normal_png=None, normal=1.0, cull=True, unshaded=False):
    """Vật liệu dùng ảnh vẽ tay ở assets/textures/bus/."""
    if name in sc.materials:
        return sc.materials[name]
    t = sc.ext_res("Texture2D", "res://assets/textures/bus/" + png)
    props = []
    if alpha:
        props += [("transparency", "1")]
    if not cull:
        props.append(("cull_mode", "2"))
    if unshaded:
        props.append(("shading_mode", "0"))
    props += [("albedo_color", color(tint)), ("albedo_texture", 'ExtResource("%s")' % t)]
    if metallic:
        props.append(("metallic", f(metallic)))
    props.append(("roughness", f(rough)))
    if emission:
        props += [("emission_enabled", "true"), ("emission", color(emission)),
                  ("emission_energy_multiplier", f(energy)), ("emission_operator", "1"),
                  ("emission_texture", 'ExtResource("%s")' % t)]
    if normal_png:
        n = sc.ext_res("Texture2D", "res://assets/textures/bus/" + normal_png)
        props += [("normal_enabled", "true"), ("normal_scale", f(normal)), ("normal_texture", 'ExtResource("%s")' % n)]
    props += [("uv1_scale", vec3((uv[0], uv[1], 1))), ("texture_filter", "5")]
    rid = sc.sub_res("StandardMaterial3D", "Mat_" + name, props)
    sc.materials[name] = rid
    return rid


def glass_mat(sc, name, tint, alpha, rough=0.05, png=None, uv=(1.6, 1.6), metallic=0.0):
    if name in sc.materials:
        return sc.materials[name]
    props = [("transparency", "1"), ("cull_mode", "2"), ("depth_draw_mode", "0"),
             ("albedo_color", color(tuple(tint) + (alpha,)))]
    if png:
        t = sc.ext_res("Texture2D", "res://assets/textures/bus/" + png)
        props.append(("albedo_texture", 'ExtResource("%s")' % t))
    props += [("metallic", f(metallic)), ("metallic_specular", "0.8"), ("roughness", f(rough)),
              ("uv1_scale", vec3((uv[0], uv[1], 1))), ("texture_filter", "5")]
    rid = sc.sub_res("StandardMaterial3D", "Mat_" + name, props)
    sc.materials[name] = rid
    return rid


_WRECK = {}


def wreck_mat(sc, name, tex, tint=(1, 1, 1), rust=0.35, moss=0.4, silt=0.65, mildew=0.35, metallic=0.0,
              rough=0.0, world_uv=False, scale=1.0):
    """Vật liệu xác xe (shaders/bus_wreck.gdshader): texture gốc + gỉ + vệt nước ngập + rêu."""
    if name in sc.materials:
        return sc.materials[name]
    if not _WRECK.get(id(sc)):
        _WRECK[id(sc)] = {
            "shader": sc.ext_res("Shader", "res://shaders/bus_wreck.gdshader"),
            "noise": sc.ext_res("Texture2D", "res://assets/textures/bus/wreck_noise.png"),
            "rust_a": sc.ext_res("Texture2D", "res://assets/textures/rust_heavy_albedo.jpg"),
            "rust_n": sc.ext_res("Texture2D", "res://assets/textures/rust_heavy_normal.jpg"),
            "moss_a": sc.ext_res("Texture2D", "res://assets/textures/moss_albedo.jpg"),
        }
    w = _WRECK[id(sc)]
    k = 1.0 / (CC0[tex]["size_m"] * scale)
    a = sc.ext_res("Texture2D", "res://assets/textures/%s_albedo.jpg" % tex)
    n = sc.ext_res("Texture2D", "res://assets/textures/%s_normal.jpg" % tex)
    o = sc.ext_res("Texture2D", "res://assets/textures/%s_orm.jpg" % tex)
    props = [
        ("render_priority", "0"), ("shader", 'ExtResource("%s")' % w["shader"]),
        ("shader_parameter/base_albedo", 'ExtResource("%s")' % a),
        ("shader_parameter/base_normal", 'ExtResource("%s")' % n),
        ("shader_parameter/base_orm", 'ExtResource("%s")' % o),
        ("shader_parameter/tint", color(tint)),
        ("shader_parameter/uv_scale", f(k)),
        ("shader_parameter/world_uv", "true" if world_uv else "false"),
        ("shader_parameter/metallic_amount", f(metallic)),
        ("shader_parameter/roughness_offset", f(rough)),
        ("shader_parameter/noise_tex", 'ExtResource("%s")' % w["noise"]),
        ("shader_parameter/rust_albedo", 'ExtResource("%s")' % w["rust_a"]),
        ("shader_parameter/rust_normal", 'ExtResource("%s")' % w["rust_n"]),
        ("shader_parameter/rust_amount", f(rust)),
        ("shader_parameter/moss_albedo", 'ExtResource("%s")' % w["moss_a"]),
        ("shader_parameter/moss_amount", f(moss)),
        ("shader_parameter/waterline_y", f(WATERLINE_Y)),
        ("shader_parameter/silt_amount", f(silt)),
        ("shader_parameter/mildew_amount", f(mildew)),
    ]
    rid = sc.sub_res("ShaderMaterial", "Mat_" + name, props)
    sc.materials[name] = rid
    return rid


def layer_materials(sc, layer):
    """Bảng vật liệu theo slot của mesh bus_models cho từng lớp xe."""
    M = {}
    if layer == "day":
        # Xe 2006: sơn kem / xanh còn mới, ghế giả da xanh, khăn trùm trắng viền xanh, sàn cao su.
        chrome = sc.mat("DayChrome", (0.82, 0.82, 0.8), 0.16, metallic=1.0)
        alu = sc.mat("DayAlu", (0.72, 0.73, 0.74), 0.32, metallic=0.9)
        paint_up = uvmat(sc, "DayWallUp", "paint_clean", (0.93, 0.9, 0.82), rough=0.75)
        M.update({
            "wall_low": uvmat(sc, "DayWallLow", "paint_clean", (0.3, 0.42, 0.55), rough=0.7),
            "wall_up": paint_up, "reveal": paint_up, "door": paint_up,
            "ceiling": uvmat(sc, "DayCeiling", "paint_clean", (0.95, 0.94, 0.9), rough=0.85),
            "rib": sc.mat("DayRib", (0.86, 0.86, 0.84), 0.5),
            "floor": uvmat(sc, "DayFloor", "rubber_mat", (0.62, 0.6, 0.58), rough=1.0),
            "runner": uvmat(sc, "DayRunner", "rubber_mat", (0.32, 0.32, 0.34), rough=1.0, scale=0.5),
            "trim": alu, "alu": alu, "arch": uvmat(sc, "DayArch", "paint_clean", (0.3, 0.42, 0.55), rough=0.7),
            "step": uvmat(sc, "DayStep", "rubber_mat", (0.3, 0.3, 0.3), scale=0.4),
            "rubber": sc.mat("DayRubber", (0.04, 0.04, 0.045), 0.7),
            "glass": glass_mat(sc, "DayGlass", (0.75, 0.86, 0.86), 0.1),
            "glass_front": glass_mat(sc, "DayGlassFront", (0.85, 0.88, 0.84), 0.08),
            "rod": chrome, "cloth": uvmat(sc, "DayCurtain", "curtain_damask", (0.62, 0.17, 0.15), rough=0.95),
            "frame": sc.mat("DaySeatFrame", (0.18, 0.19, 0.2), 0.4, metallic=0.7),
            "vinyl": uvmat(sc, "DayVinyl", "vinyl", (0.2, 0.3, 0.55), rough=0.55),
            "shell": sc.mat("DaySeatShell", (0.74, 0.74, 0.72), 0.45),
            "chrome": chrome,
            "seat_cloth_R:cloth": texmat(sc, "DaySeatCloth", "seat_cloth.png", rough=0.95, cull=False),
            "housing": sc.mat("DayLampHousing", (0.85, 0.85, 0.82), 0.4),
            "diffuser": sc.mat("DayDiffuser", (0.92, 0.94, 0.96), 0.3, emission=(0.85, 0.9, 1.0), energy=0.25),
            "grille": sc.mat("DayGrille", (0.12, 0.12, 0.13), 0.6),
            "dash": uvmat(sc, "DayDash", "paint_clean", (0.16, 0.17, 0.19), rough=0.85),
            "panel": sc.mat("DayPanel", (0.08, 0.08, 0.09), 0.6),
            "gauge": texmat(sc, "DayGauge", "gauge_face.png", rough=0.2, emission=(0.4, 0.6, 0.5), energy=0.2),
            "grip": sc.mat("Bakelite", (0.05, 0.045, 0.04), 0.35),
            "spoke": sc.mat("SteeringSpoke", (0.1, 0.1, 0.11), 0.4, metallic=0.4),
            "column": sc.mat("DaySteerCol", (0.12, 0.12, 0.13), 0.5),
            "knob": sc.mat("Bakelite", (0.05, 0.045, 0.04), 0.35),
            "panel_paint": uvmat(sc, "DayWallLow", "paint_clean", (0.3, 0.42, 0.55), rough=0.7),
            "mirror": sc.mat("Mirror", (0.9, 0.92, 0.92), 0.02, metallic=1.0),
            "visor": sc.mat("DayVisor", (0.4, 0.38, 0.34), 0.7),
            "board": uvmat(sc, "SignWoodUV", "wood_weathered", (0.7, 0.62, 0.55)),
        })
        M["driver_seat:vinyl"] = uvmat(sc, "DayDriverVinyl", "vinyl", (0.12, 0.12, 0.13), rough=0.5)
        M["cab_misc:vinyl"] = uvmat(sc, "DayEngineVinyl", "vinyl", (0.14, 0.13, 0.13), rough=0.55)
        for k in ("seat_cloth_L", "bench_cloth"):
            M[k + ":cloth"] = M["seat_cloth_R:cloth"]
    elif layer == "night":
        # Xe 1999 nguyên vẹn nhưng cũ: tôn sơn xanh lá bong gỉ lấm tấm, vách trên sơn kem ố,
        # ghế giả da đỏ nâu, khăn trùm vải trắng ngả vàng, sàn ván gỗ, rèm vàng đất.
        chrome = sc.mat("NightChrome", (0.72, 0.71, 0.68), 0.26, metallic=1.0)
        alu = sc.mat("NightAlu", (0.6, 0.6, 0.58), 0.42, metallic=0.85)
        paint_up = uvmat(sc, "NightWallUp", "paint_clean", (0.78, 0.74, 0.6), rough=0.8)
        green = uvmat(sc, "NightWallLow", "paint_worn", (0.9, 1.0, 0.95), rough=0.9)
        M.update({
            "wall_low": green, "wall_up": paint_up, "reveal": paint_up, "door": green, "arch": green,
            "panel_paint": green,
            "ceiling": uvmat(sc, "NightCeiling", "paint_clean", (0.74, 0.7, 0.6), rough=0.9),
            "rib": sc.mat("NightRib", (0.62, 0.6, 0.55), 0.5, metallic=0.5),
            "floor": uvmat(sc, "NightFloor", "wood_weathered", (0.6, 0.55, 0.5), rough=1.0),
            "runner": uvmat(sc, "NightRunner", "rubber_mat", (0.24, 0.22, 0.2), rough=1.0, scale=0.5),
            "trim": alu, "alu": alu, "step": uvmat(sc, "NightStep", "rubber_mat", (0.25, 0.24, 0.22), scale=0.4),
            "rubber": sc.mat("NightRubber", (0.03, 0.03, 0.03), 0.8),
            "glass": glass_mat(sc, "NightGlass", (0.75, 0.82, 0.85), 0.55, png="glass_rain.png", rough=0.1),
            "glass_front": glass_mat(sc, "NightGlassFront", (0.75, 0.82, 0.85), 0.5, png="glass_rain.png", rough=0.1),
            "rod": chrome, "cloth": uvmat(sc, "NightCurtain", "curtain_damask", (0.55, 0.4, 0.2), rough=0.95),
            "frame": sc.mat("NightSeatFrame", (0.2, 0.22, 0.2), 0.55, metallic=0.6),
            "vinyl": uvmat(sc, "NightVinyl", "vinyl", (0.42, 0.12, 0.08), rough=0.6),
            "shell": uvmat(sc, "NightSeatShell", "paint_worn", (0.85, 0.95, 0.9), rough=0.8),
            "chrome": chrome,
            "seat_cloth_R:cloth": uvmat(sc, "NightSeatCloth", "fabric", (0.62, 0.57, 0.45), rough=1.0, scale=0.5),
            "housing": sc.mat("NightLampHousing", (0.6, 0.58, 0.52), 0.5),
            "diffuser": sc.mat("NightDiffuser", (0.5, 0.5, 0.48), 0.4),
            "grille": sc.mat("NightGrille", (0.1, 0.1, 0.1), 0.6),
            "dash": uvmat(sc, "NightDash", "paint_worn", (0.35, 0.4, 0.38), rough=0.9),
            "panel": sc.mat("NightPanel", (0.06, 0.06, 0.06), 0.6),
            "gauge": texmat(sc, "NightGauge", "gauge_face.png", rough=0.25, emission=(0.35, 1.0, 0.55), energy=0.9),
            "grip": sc.mat("Bakelite", (0.05, 0.045, 0.04), 0.35),
            "spoke": sc.mat("SteeringSpoke", (0.1, 0.1, 0.11), 0.4, metallic=0.4),
            "column": sc.mat("NightSteerCol", (0.1, 0.1, 0.1), 0.6),
            "knob": sc.mat("Bakelite", (0.05, 0.045, 0.04), 0.35),
            "mirror": sc.mat("Mirror", (0.9, 0.92, 0.92), 0.02, metallic=1.0),
            "visor": sc.mat("NightVisor", (0.3, 0.28, 0.24), 0.8),
            "board": uvmat(sc, "SignWoodUV", "wood_weathered", (0.7, 0.62, 0.55)),
        })
        M["driver_seat:vinyl"] = uvmat(sc, "NightDriverVinyl", "vinyl", (0.2, 0.14, 0.1), rough=0.6)
        M["cab_misc:vinyl"] = uvmat(sc, "NightEngineVinyl", "vinyl", (0.3, 0.1, 0.07), rough=0.65)
        for k in ("seat_cloth_L", "bench_cloth"):
            M[k + ":cloth"] = M["seat_cloth_R:cloth"]
    else:
        # Xác xe: mọi bề mặt qua shader gỉ / ngập nước / rêu.
        rust_metal = wreck_mat(sc, "WreckMetal", "paint_flaking", (0.7, 0.7, 0.68), rust=0.55, moss=0.2,
                               metallic=0.6, world_uv=True)
        paint_low = wreck_mat(sc, "WreckWallLow", "paint_clean", (0.36, 0.5, 0.42), rust=0.32, moss=0.45)
        paint_up = wreck_mat(sc, "WreckWallUp", "paint_clean", (0.78, 0.74, 0.6), rust=0.2, moss=0.25)
        M.update({
            "wall_low": paint_low, "wall_up": paint_up, "reveal": paint_up, "door": paint_low, "arch": paint_low,
            "panel_paint": paint_low,
            "ceiling": wreck_mat(sc, "WreckCeiling", "paint_clean", (0.62, 0.6, 0.52), rust=0.12, moss=0.0,
                                 mildew=0.9),
            "rib": rust_metal,
            "floor": wreck_mat(sc, "WreckFloor", "wood_weathered", (0.5, 0.45, 0.4), rust=0.0, moss=0.75, silt=0.9),
            "runner": wreck_mat(sc, "WreckRunner", "rubber_mat", (0.3, 0.28, 0.25), rust=0.0, moss=0.6, silt=0.9),
            "trim": rust_metal, "alu": wreck_mat(sc, "WreckAlu", "paint_clean", (0.5, 0.5, 0.48), rust=0.3, moss=0.1,
                                                 metallic=0.7, world_uv=True),
            "step": rust_metal,
            "rubber": sc.mat("WreckRubber", (0.05, 0.05, 0.045), 0.9),
            "glass": glass_mat(sc, "WreckGlass", (0.55, 0.5, 0.4), 0.85, png="glass_grime.png", rough=0.5),
            "glass_front": glass_mat(sc, "WreckGlassFront", (0.55, 0.5, 0.4), 0.85, png="glass_grime.png", rough=0.5),
            "rod": rust_metal, "cloth": uvmat(sc, "WreckCurtain", "curtain_damask", (0.22, 0.18, 0.13), rough=1.0),
            "frame": rust_metal,
            "vinyl": wreck_mat(sc, "WreckVinyl", "vinyl", (0.4, 0.13, 0.1), rust=0.0, moss=0.35, silt=0.45),
            "shell": wreck_mat(sc, "WreckSeatShell", "paint_clean", (0.4, 0.52, 0.44), rust=0.28, moss=0.3),
            "chrome": rust_metal,
            "seat_cloth_R:cloth": wreck_mat(sc, "WreckSeatCloth", "fabric", (0.5, 0.45, 0.36), rust=0.0, moss=0.3,
                                            silt=0.9, scale=0.5),
            "housing": rust_metal,
            "diffuser": sc.mat("WreckDiffuser", (0.3, 0.3, 0.28), 0.6),
            "grille": sc.mat("WreckGrille", (0.08, 0.07, 0.06), 0.8),
            "dash": wreck_mat(sc, "WreckDash", "paint_clean", (0.3, 0.36, 0.32), rust=0.4, moss=0.12),
            "panel": sc.mat("WreckPanel", (0.06, 0.055, 0.05), 0.8),
            "gauge": texmat(sc, "WreckGauge", "gauge_face.png", (0.45, 0.4, 0.32, 1), rough=0.6),
            "grip": sc.mat("WreckGrip", (0.06, 0.05, 0.04), 0.7),
            "spoke": rust_metal, "column": rust_metal,
            "knob": sc.mat("WreckGrip", (0.06, 0.05, 0.04), 0.7),
            "mirror": sc.mat("WreckMirror", (0.3, 0.3, 0.28), 0.4, metallic=0.8),
            "visor": sc.mat("WreckVisor", (0.18, 0.16, 0.13), 0.9),
            "board": uvmat(sc, "SignWoodUV", "wood_weathered", (0.7, 0.62, 0.55)),
        })
        M["driver_seat:vinyl"] = wreck_mat(sc, "WreckDriverVinyl", "vinyl", (0.2, 0.15, 0.12), rust=0.0, moss=0.3)
        M["cab_misc:vinyl"] = M["vinyl"]
        for k in ("seat_cloth_L", "bench_cloth"):
            M[k + ":cloth"] = M["seat_cloth_R:cloth"]
    # Đồ dùng chung mọi lớp
    M.update({
        "lens": sc.mat("HeadlightLensOff", (0.8, 0.82, 0.8), 0.1, metallic=0.2),
        "sack": uvmat(sc, "SackUV", "fabric", (0.8, 0.72, 0.55), scale=0.6),
        "rope": sc.mat("Rope", (0.62, 0.55, 0.4), 0.9),
        "carton": uvmat(sc, "CartonUV", "painted_wood", (0.62, 0.48, 0.32)),
        "case": uvmat(sc, "SuitcaseUV", "vinyl", (0.3, 0.2, 0.12), rough=0.6),
        "metal": sc.mat("CaseMetal", (0.6, 0.58, 0.55), 0.35, metallic=0.9),
        "wood": uvmat(sc, "AltarWood", "lacquer_red", (1, 1, 1), rough=0.5),
        "gold": sc.mat("Gold", (0.85, 0.62, 0.26), 0.3, metallic=1.0),
        "ceramic": sc.mat("Ceramic", (0.9, 0.88, 0.82), 0.15),
        "incense": sc.mat("Incense", (0.7, 0.12, 0.08), 0.8),
        "leaf": sc.mat("PlasticLeaf", (0.15, 0.48, 0.2), 0.45),
        "flower": sc.mat("PlasticFlower", (0.92, 0.2, 0.38), 0.45),
        "flower2": sc.mat("PlasticFlowerYellow", (0.95, 0.75, 0.15), 0.45),
        "tassel": sc.mat("TasselRed", (0.75, 0.05, 0.06), 0.7),
    })
    return M


# ---------------------------------------------------------------------------
# Đặt mesh bus_models vào scene
# ---------------------------------------------------------------------------

def place(sc, name, parent, model, M, pos=(0, 0, 0), basis=None, rot_y=0.0, shadow=1):
    import bus_models
    slots = bus_models.MODELS[model]
    rid = sc.ext_res("ArrayMesh", bus_models.RES + model + ".obj")
    props = [("transform", xform(pos, rot_y, basis))]
    if shadow != 1:
        props.append(("cast_shadow", str(shadow)))
    props.append(("mesh", 'ExtResource("%s")' % rid))
    for i, s in enumerate(slots):
        m = M.get(model + ":" + s) or M.get(s)
        if m is None:
            raise KeyError("thiếu vật liệu cho %s:%s" % (model, s))
        props.append(("surface_material_override/%d" % i, 'SubResource("%s")' % m))
    return sc.node(name, "MeshInstance3D", parent, props)


def pivot_basis(deg, pivot):
    """Xoay quanh trục X qua điểm pivot: trả về (vị trí gốc mới, basis)."""
    b = basis_x(deg)
    px, py, pz = pivot
    ny = b[4] * py + b[5] * pz
    nz = b[7] * py + b[8] * pz
    return (0.0, py - ny, pz - nz), b


def build_seats(sc, parent, M, layer, rng):
    """Ghế đôi hai bên + băng ghế cuối + ghế lái."""
    seats = sc.empty("Seats", parent)
    broken = {}
    if layer == "wreck":
        broken = {"L1": "torn", "R2": "snapped", "L3": "torn", "R5": "torn", "L6": "snapped", "R7": "missing",
                  "L8": "torn", "R9": "snapped"}
    foam = sc.mat("Foam", (0.62, 0.52, 0.28), 1.0)
    for side in (-1, 1):
        sl = "L" if side < 0 else "R"
        cx = side * (SEAT_X[0] + SEAT_X[1]) / 2
        for r, z in enumerate(ROWS):
            nm = "%s%d" % (sl, r + 1)
            kind = broken.get(nm)
            g = sc.empty("Seat" + nm, seats, (cx, 0, z))
            place(sc, "Frame", g, "seat_frame_" + sl, M)
            if kind == "missing":
                continue
            place(sc, "Cushion", g, "seat_cushion_" + sl, M)
            back_pos, back_b = (0, 0, 0), None
            if kind == "snapped":
                back_pos, back_b = pivot_basis(38, (0, 0.5, 0.17))
            place(sc, "Back", g, "seat_back_" + sl, M, back_pos, back_b)
            if layer != "wreck" or (r % 3 == 0 and kind != "snapped"):
                place(sc, "Cloth", g, "seat_cloth_" + sl, M, back_pos, back_b)
            if kind in ("torn", "snapped"):
                # Nệm rách lòi mút vàng
                for k in range(2):
                    sc.mesh("Foam", g, "sphere", (rng.uniform(0.07, 0.11), rng.uniform(0.04, 0.07)),
                            (rng.uniform(-0.3, 0.3), 0.515, rng.uniform(-0.12, 0.1)), foam,
                            basis=basis_scale(1.0, 0.6, 1.0))
    g = sc.empty("Bench", seats, (0, 0, BENCH_Z))
    place(sc, "Base", g, "bench_base", M)
    place(sc, "Cushion", g, "bench_cushion", M)
    place(sc, "Back", g, "bench_back", M)
    if layer != "wreck":
        place(sc, "Cloth", g, "bench_cloth", M)
    place(sc, "DriverSeat", seats, "driver_seat", M, (-0.7, 0, -4.02))


def build_interior(sc, parent, M, layer, rng):
    """Toàn bộ lòng xe cho một lớp (cùng hình học, khác vật liệu)."""
    variant = {"day": "day", "night": "night", "wreck": "wreck"}[layer]
    g = sc.empty("Interior", parent)
    place(sc, "Shell", g, "bus_shell", M, shadow=2)
    place(sc, "Floor", g, "bus_floor", M)
    place(sc, "WindowFrames", g, "bus_window_frames", M)
    place(sc, "Glass", g, "bus_glass_" + variant, M, shadow=0)
    place(sc, "Curtains", g, "bus_curtains_" + variant, M)
    place(sc, "Racks", g, "bus_racks", M)
    place(sc, "CeilingLights", g, "bus_ceiling_lights", M)
    place(sc, "Dashboard", g, "dashboard", M)
    place(sc, "SteeringWheel", g, "steering_wheel", M, (-0.7, 1.16, Z_FRONT + 0.76), basis_x(38))
    place(sc, "CabMisc", g, "cab_misc", M)
    build_seats(sc, g, M, layer, rng)
    return g


def env_resource(sc, rid, top, horizon, ground, ambient, ambient_energy, fog_color, fog_density,
                 exposure=1.0, sky_energy=1.0, vol=None, adjust=(1.0, 1.05, 1.0), glow=0.5, ssao=1.6,
                 fog_sky=0.6, fog_height=None):
    """Môi trường từng lớp. vol = (mật độ, màu albedo, độ dài, bơm ánh sáng nền): sương khối (Forward+)."""
    sc.sub_res("ProceduralSkyMaterial", "SkyMat_" + rid, [
        ("sky_top_color", color(top)), ("sky_horizon_color", color(horizon)),
        ("ground_bottom_color", color(ground)), ("ground_horizon_color", color(horizon)),
        ("sky_energy_multiplier", f(sky_energy)),
    ])
    sc.sub_res("Sky", "Sky_" + rid, [("sky_material", 'SubResource("SkyMat_%s")' % rid)])
    props = [
        ("background_mode", "2"), ("sky", 'SubResource("Sky_%s")' % rid),
        ("ambient_light_source", "3"), ("ambient_light_color", color(ambient)),
        ("ambient_light_sky_contribution", "0.25"), ("ambient_light_energy", f(ambient_energy)),
        ("tonemap_mode", "3"), ("tonemap_exposure", f(exposure)), ("tonemap_white", "6.0"),
        ("ssao_enabled", "true"), ("ssao_radius", "0.6"), ("ssao_intensity", f(ssao)), ("ssao_power", "1.4"),
        ("ssao_detail", "0.6"), ("ssao_light_affect", "0.15"),
        ("glow_enabled", "true"), ("glow_intensity", f(glow)), ("glow_strength", "0.9"), ("glow_bloom", "0.05"),
        ("glow_hdr_threshold", "0.9"), ("glow_blend_mode", "1"),
        ("fog_enabled", "true"), ("fog_light_color", color(fog_color)), ("fog_density", f(fog_density)),
        ("fog_sky_affect", f(fog_sky)),
    ]
    if fog_height is not None:
        props += [("fog_height", f(fog_height[0])), ("fog_height_density", f(fog_height[1]))]
    if vol:
        props += [
            ("volumetric_fog_enabled", "true"), ("volumetric_fog_density", f(vol[0])),
            ("volumetric_fog_albedo", color(vol[1])), ("volumetric_fog_length", f(vol[2])),
            ("volumetric_fog_ambient_inject", f(vol[3])), ("volumetric_fog_anisotropy", "0.45"),
            ("volumetric_fog_detail_spread", "1.5"),
        ]
    props += [("adjustment_enabled", "true"), ("adjustment_brightness", f(adjust[0])),
              ("adjustment_contrast", f(adjust[1])), ("adjustment_saturation", f(adjust[2]))]
    return sc.sub_res("Environment", "Env_" + rid, props)


def directional(sc, name, parent, pitch, yaw, light_color, energy, shadow=True, fog=1.0):
    b = basis_mul(basis_y(yaw), basis_x(pitch))
    sc.node(name, "DirectionalLight3D", parent, [
        ("transform", xform((0, 6, 0), basis=b)),
        ("light_color", color(light_color)), ("light_energy", f(energy)),
        ("light_volumetric_fog_energy", f(fog)),
        ("shadow_enabled", "true" if shadow else "false"), ("shadow_blur", "1.5"),
        ("directional_shadow_max_distance", "24.0"),
    ])


def reflection_probe(sc, parent, intensity=1.0):
    sc.node("ReflectionProbe", "ReflectionProbe", parent, [
        ("transform", xform((0, 1.3, -0.2))),
        ("size", vec3((2 * HALF_W + 0.2, 2.4, Z_BACK - Z_FRONT + 0.2))),
        ("origin_offset", vec3((0, -0.2, 0))),
        ("box_projection", "true"), ("interior", "true"), ("intensity", f(intensity)),
    ])


# ---------------------------------------------------------------------------
# Chương 2: dấu vết đêm 1999 trên xác xe, lớp "Đêm 1999" và cảnh xe 2006 đông cứng
# ---------------------------------------------------------------------------

def build_wreck_traces(sc, der, rng, rust, chrome, wood_sign):
    """Xác xe: decal số xe, đồ của Hùng mục nát, dây chuông đứt (vệt nước ngập nằm trong shader)."""
    windshield_number(sc, der)
    # Đồ của Hùng: khung đài cát-sét gỉ trên ghế, cặp sách mục dưới chân.
    hx, hz = seat_xz(HUNG_SEAT)
    deck_rust = wreck_mat(sc, "DeckRust", "paint_flaking", (0.75, 0.66, 0.6), rust=0.5, moss=0.2, metallic=0.4)
    deck_dark = wreck_mat(sc, "DeckRustDark", "rust_heavy", (0.5, 0.45, 0.4), rust=0.2, moss=0.1)
    place(sc, "DeckRusted", der, "pz_boombox", {"body": deck_rust, "chrome": deck_rust, "grille": deck_dark,
                                                "window": deck_dark, "tape": deck_dark},
          (hx, 0.58, hz - 0.02), rot_y=8)
    bag_rot = wreck_mat(sc, "BagRotten", "fabric", (0.22, 0.26, 0.2), rust=0.0, moss=0.5, world_uv=True, scale=0.5)
    place(sc, "SchoolbagRotten", der, "pz_schoolbag", {"canvas": bag_rot, "leather": bag_rot, "metal": deck_rust},
          (hx + 0.12, 0.12, hz - 0.3), basis=basis_mul(basis_y(20), basis_x(-12)))
    # Dây chuông mục đứt, một đoạn rủ xuống lối đi.
    rope = sc.mat("RopeRotten", (0.3, 0.26, 0.2), 1.0)
    sc.mesh("BellRope", der, "cyl", (0.006, 0.006, 3.4, 5), (0.3, 2.1, -2.5), rope, basis=basis_x(90))
    sc.mesh("BellRopeEnd", der, "cyl", (0.006, 0.006, 0.6, 5), (0.3, 1.82, -0.8), rope, basis=basis_z(12))
    sc.mesh("Bell", der, "cyl", (0.03, 0.05, 0.06, 10), (0.3, 2.1, -4.3), rust)


def build_night_1999(sc, rng, M, rust, chrome, wood_sign, d_talisman, trunk):
    """Đêm 14/04/1999: xe nguyên vẹn, mất điện, mưa đứng yên ngoài cửa kính, cầu ngay trước mũi xe."""
    night = sc.empty("Night1999", ".", props=[("visible", "false")])
    build_interior(sc, night, M, "night", rng)
    for z in (-2.5, 0.5, 3.0):
        sc.mesh("TubeDead", night, "cyl", (0.016, 0.016, 1.1, 8), (0, H - 0.06, z), sc.mat("TubeDead", (0.3, 0.3, 0.28), 0.6),
                basis=basis_x(90), shadow=False)
    sc.decal("Talisman", night, (0, 1.75, Z_FRONT + 0.06), "+z", (0.12, 0.3), d_talisman, offset=0.0)
    windshield_number(sc, night)
    # Bàn thờ nhỏ của bác Tư trên taplô (không hương khói, đêm ấy chưa ai thắp).
    import bus_models  # noqa: F401
    place(sc, "DashAltar", night, "dash_altar", M, (0.42, 1.1, Z_FRONT + 0.26), rot_y=0)

    # Đèn bão của phụ xe treo ở vách sau: nguồn sáng chính trong xe.
    tin = sc.mat("LampTin", (0.42, 0.4, 0.34), 0.45, metallic=0.8)
    lamp_glass = sc.mat("LampGlass", (1.0, 0.9, 0.7), 0.05, alpha=0.3)
    flame = sc.mat("LampFlame", (1.0, 0.7, 0.3), 0.5, emission=(1.0, 0.62, 0.25), energy=8.0, unshaded=True)
    storm_lamp(sc, "ConductorLamp", night, LAMP_POS, tin, lamp_glass, flame)
    sc.node("LampLight", "OmniLight3D", night, [
        ("transform", xform((LAMP_POS[0] - 0.05, LAMP_POS[1] + 0.12, LAMP_POS[2] - 0.15))),
        ("light_color", color((1.0, 0.6, 0.3))), ("light_energy", "1.3"), ("omni_range", "9.0"),
        ("omni_attenuation", "1.6"), ("shadow_enabled", "true"), ("shadow_blur", "2.5"),
        ("light_volumetric_fog_energy", "2.0"),
    ])
    sc.node("Fill", "OmniLight3D", night, [
        ("transform", xform((0, 1.9, -1.5))),
        ("light_color", color((0.4, 0.55, 0.62))), ("light_energy", "0.22"), ("omni_range", "7.0"),
        ("light_volumetric_fog_energy", "0.0"),
    ])
    sc.node("DashGlow", "OmniLight3D", night, [
        ("transform", xform((-0.7, 1.3, Z_FRONT + 0.6))),
        ("light_color", color((0.4, 0.95, 0.55))), ("light_energy", "0.35"), ("omni_range", "1.4"),
    ])
    # Ánh đèn pha hắt lại từ màn mưa phía trước, lạnh và nhạt, rọi ngược vào khoang xe.
    sc.node("RainBounce", "SpotLight3D", night, [
        ("transform", xform((0, 1.75, Z_FRONT + 0.12), basis=basis_mul(basis_y(180), basis_x(-10)))),
        ("light_color", color((0.55, 0.68, 0.82))), ("light_energy", "0.6"), ("spot_range", "11.0"),
        ("spot_angle", "55.0"), ("spot_attenuation", "1.4"), ("shadow_enabled", "true"),
        ("light_volumetric_fog_energy", "0.3"),
    ])
    # Đèn pha rọi vào màn mưa đứng yên.
    beam = sc.mat("HeadlightLens", (1, 0.95, 0.8), 0.2, emission=(1, 0.95, 0.8), energy=6.0)
    hl = dict(M)
    hl["lens"] = beam
    for sx in (-1, 1):
        place(sc, "HeadlightLens", night, "headlight", hl, (sx * 0.85, 0.35, Z_FRONT - WALL - 0.03), shadow=0)
        sc.node("Headlight", "SpotLight3D", night, [
            ("transform", xform((sx * 0.85, 0.35, Z_FRONT - WALL - 0.12), basis=basis_x(-3))),
            ("light_color", color((1.0, 0.93, 0.78))), ("light_energy", "9.0"), ("spot_range", "34.0"),
            ("spot_angle", "22.0"), ("spot_attenuation", "0.7"), ("shadow_enabled", "true"),
            ("light_volumetric_fog_energy", "3.0"),
        ])
    reflection_probe(sc, night, 0.6)

    # Bảng lộ trình trên vách trái (bốn tấm biển bến đã rơi xuống sàn).
    place(sc, "RouteBoard", night, "route_board", dict(M, frame=sc.mat("BoardFrame", (0.22, 0.14, 0.08), 0.6)),
          BOARD_POS)
    sc.node("RouteTitle", "Label3D", night, [
        ("transform", xform((BOARD_POS[0] + 0.012, BOARD_POS[1] + 0.2, BOARD_POS[2]), 90)),
        ("pixel_size", "0.0012"), ("modulate", color((0.15, 0.1, 0.06))), ("outline_size", "0"),
        ("text", '"BUS_ROUTE_BOARD_TITLE"'), ("font_size", "40"),
    ])
    for k in range(4):
        sc.mesh("Hook", night, "cyl", (0.004, 0.004, 0.03, 6),
                (BOARD_POS[0] + 0.02, BOARD_POS[1] + 0.12 - k * 0.1, BOARD_POS[2] - 0.12), chrome, basis=basis_z(90))
    # Dây chuông chạy dọc trần, chuông đồng trên đầu bác tài.
    rope = sc.mat("Rope", (0.62, 0.55, 0.4), 0.9)
    brass = sc.mat("Brass", (0.75, 0.6, 0.3), 0.3, metallic=0.9)
    sc.mesh("BellRope", night, "cyl", (0.006, 0.006, 7.6, 5), (0.3, 2.1, -0.4), rope, basis=basis_x(90))
    sc.mesh("Bell", night, "cyl", (0.03, 0.05, 0.06, 10), (0.3, 2.1, -4.3), brass)
    for k, (z, model) in enumerate([(ROWS[1], "luggage_sack"), (ROWS[6], "luggage_case"), (ROWS[3] + 0.6, "luggage_box")]):
        place(sc, "Luggage", night, model, M, (1.0 if k != 2 else -1.0, 1.93, z), rot_y=rng.uniform(-8, 8))

    # Ngoài trời: mặt cầu, lan can, thành cầu ngay trước mũi xe, sông tối bên dưới.
    out = sc.empty("Outside", night)
    concrete = sc.pbr("BridgeConcrete", "concrete_damp", (0.62, 0.62, 0.6))
    wet = sc.pbr("WetAsphalt", "concrete_damp", (0.22, 0.22, 0.24), rough=0.35, triplanar=False, uv_scale=(3, 30))
    water = sc.mat("RiverNight", (0.02, 0.035, 0.045), 0.03, metallic=0.5)
    sc.node("Deck", "MeshInstance3D", out, [
        ("transform", xform((0.4, -0.95, -30))), ("cast_shadow", "0"),
        ("mesh", 'SubResource("%s")' % sc.sub_res("PlaneMesh", "Mesh_BridgeDeck", [("size", "Vector2(7.5, 80)")])),
        ("material_override", 'SubResource("%s")' % wet)])
    sc.node("River", "MeshInstance3D", out, [
        ("transform", xform((0, -7.0, 0))), ("cast_shadow", "0"),
        ("mesh", 'SubResource("%s")' % sc.sub_res("PlaneMesh", "Mesh_River", [("size", "Vector2(300, 300)")])),
        ("material_override", 'SubResource("%s")' % water)])
    for sx in (-1, 1):
        x = 0.4 + sx * 3.75
        sc.mesh("RailBeam", out, "box", (0.15, 0.12, 80), (x, -0.05, -30), concrete)
        for k in range(40):
            sc.mesh("RailPost", out, "box", (0.14, 0.9, 0.14), (x, -0.5, 9.5 - k * 2.0), concrete)
    # Thành cầu chắn ngang trước mũi xe (xe đang chệch lái lao vào). Director nhích nó lại gần mỗi nhịp thời gian.
    rail = sc.empty("BridgeRail", out, (1.6, -0.95, -8.5), -28)
    sc.mesh("Beam", rail, "box", (7.0, 0.14, 0.16), (0, 0.9, 0), concrete)
    sc.mesh("BeamLow", rail, "box", (7.0, 0.1, 0.14), (0, 0.45, 0), concrete)
    for k in range(8):
        sc.mesh("Post", rail, "box", (0.15, 0.95, 0.15), (-3.3 + k * 0.94, 0.475, 0), concrete)
    # Biển bến Thôn Đoài bên kia cầu, chỉ hiện khi bác Tư đạp phanh.
    sign = sc.empty("StopSign", out, (-2.6, -0.95, -11.0), props=[("visible", "false")])
    sc.mesh("Post", sign, "box", (0.08, 2.3, 0.08), (0, 1.15, 0), rust)
    sc.mesh("Board", sign, "box", (1.0, 0.45, 0.03), (0, 2.25, 0), wood_sign)
    sc.node("Label", "Label3D", sign, [
        ("transform", xform((0, 2.25, 0.02))),
        ("pixel_size", "0.0024"), ("modulate", color((0.12, 0.1, 0.08))), ("outline_size", "0"),
        ("text", '"SIGN_BUS_STOP_THON_DOAI"'), ("font_size", "64"), ("width", "400.0"), ("autowrap_mode", "3"),
        ("horizontal_alignment", "1"),
    ])
    for k, (x, z) in enumerate([(-7.0, -14.0), (8.0, -18.0), (-10.0, -26.0)]):
        g = sc.empty("Tree%d" % k, out, (x, -0.95, z), k * 70)
        sc.mesh("Trunk", g, "cyl", (0.1, 0.22, 4.0, 8), (0, 2.0, 0), trunk)
    # Mưa đứng yên: BusLevel rải hạt mưa (MultiMesh) vào node này lúc chạy.
    sc.empty("Rain", night)


def build_day_glimpse(sc, rng, shirts, pants, skin, hair, basket):
    """Xe 2006 đông cứng (cảnh nhìn thấy một lần) và giỏ hàng mã của bà cụ."""
    props = "Day/Props"
    # Giỏ hàng mã của bà cụ đặt trên ghế cạnh bà.
    bx, bz = seat_xz((L_SIDE, OLD_WOMAN_ROW, True))
    sc.mesh("PaperBasket", props, "cyl", (0.17, 0.13, 0.18, 14), (bx, 0.61, bz), basket)
    for k, (c, dx, dz, h) in enumerate([((0.85, 0.12, 0.1), -0.05, 0.03, 0.16), ((0.9, 0.7, 0.2), 0.06, -0.02, 0.2),
                                         ((0.3, 0.5, 0.85), 0.0, 0.07, 0.12)]):
        sc.mesh("PaperGoods", props, "box", (0.08, h, 0.07), (bx + dx, 0.64 + h / 2, bz + dz),
                sc.mat("PaperGoods%d" % k, c, 0.9), rot_y=k * 25)

    g = sc.empty("Glimpse", "Day", props=[("visible", "false")])
    # Thân xác An ngủ gục ở ghế 07.
    ax, az = seat_xz(NUMBERED_SEATS["07"])
    seated_person(sc, "AnBody", g, (ax, 0.05, az), shirts[3], pants[2], skin, hair, lean=14, head_tilt=24)
    # Ghế bà cụ trống trơn, chỉ còn tro giấy.
    nx, nz = seat_xz(NAM_SEAT)
    ash = sc.mat("PaperAsh", (0.16, 0.15, 0.14), 1.0)
    ember = sc.mat("PaperAshEdge", (0.5, 0.45, 0.4), 1.0)
    for k in range(9):
        sc.mesh("Ash", g, "cyl", (0.03, 0.035, 0.004, 7),
                (nx + rng.uniform(-0.15, 0.15), SEAT_Y + 0.08, nz + rng.uniform(-0.12, 0.12)),
                ash if k % 3 else ember, rot_y=rng.uniform(0, 360), shadow=False)
    # Cốc nước trên taplô đổ dở, nước treo lơ lửng.
    water = sc.mat("FrozenWater", (0.7, 0.85, 0.95), 0.05, alpha=0.5)
    cup = sc.mat("CupGlass", (0.85, 0.9, 0.9), 0.05, alpha=0.3)
    cx, cy, cz = 0.25, 1.14, Z_FRONT + 0.45
    sc.mesh("Cup", g, "cyl", (0.035, 0.03, 0.1, 12), (cx, cy + 0.04, cz), cup, basis=basis_z(-55), shadow=False)
    for k in range(7):
        t = k / 6.0
        sc.mesh("WaterDrop", g, "sphere", (0.012 - t * 0.004, 0.024 - t * 0.008),
                (cx + 0.07 + t * 0.12, cy + 0.06 - t * t * 0.18, cz + rng.uniform(-0.01, 0.01)), water,
                shadow=False)
    # Qua kính lái: đầu cây cầu ngay trước mặt.
    concrete = sc.pbr("BridgeConcrete", "concrete_damp", (0.62, 0.62, 0.6))
    for sx in (-1, 1):
        sc.mesh("BridgeBeam", g, "box", (0.15, 0.12, 40), (0.3 + sx * 3.75, -0.05, -32), concrete)
        for k in range(20):
            sc.mesh("BridgePost", g, "box", (0.14, 0.9, 0.14), (0.3 + sx * 3.75, -0.5, -12.5 - k * 2.0), concrete)


def seat_numbers(sc):
    """Số ghế dán trên vách, ngay dưới giá hành lý (có ở cả ba lớp xe)."""
    for num, seat in NUMBERED_SEATS.items():
        x, z = seat_xz(seat)
        side = seat[0]
        sc.node("SeatNo" + num, "Label3D", "Fixtures", [
            ("transform", xform((side * (HALF_W - 0.012), 1.8, z), 90 if side < 0 else -90)),
            ("pixel_size", "0.0011"), ("modulate", color((0.92, 0.9, 0.82))), ("outline_size", "6"),
            ("outline_modulate", color((0.1, 0.1, 0.1))), ("text", '"%s"' % num), ("font_size", "48"),
        ])


# ---------------------------------------------------------------------------
# Va chạm dùng chung (giữ đúng khối của bản dựng hộp cũ để tia tương tác không đổi)
# ---------------------------------------------------------------------------

def build_collision(sc):
    body = sc.node("Collision", "StaticBody3D", ".", [])
    shapes = {}

    def box(name, center, size, basis=None):
        key = tuple(round(s, 4) for s in size)
        if key not in shapes:
            shapes[key] = sc.sub_res("BoxShape3D", "Col_%d" % (len(shapes) + 1), [("size", vec3(size))])
        sc.node(name, "CollisionShape3D", body, [("transform", xform(center, basis=basis)),
                                                 ("shape", 'SubResource("%s")' % shapes[key])])

    length = Z_BACK - Z_FRONT
    zc = (Z_BACK + Z_FRONT) / 2
    box("Floor", (0, -0.05, zc), (2 * HALF_W + 2 * WALL, 0.1, length + 2 * WALL))
    box("Ceiling", (0, H + 0.05, zc), (2 * HALF_W + 2 * WALL, 0.1, length + 2 * WALL))
    for sx in (-1, 1):
        box("Wall", (sx * (HALF_W + WALL / 2), H / 2, zc), (WALL, H + 0.2, length + 2 * WALL))
    box("Front", (0, H / 2, Z_FRONT - WALL / 2), (2 * HALF_W, H + 0.2, WALL))
    box("Back", (0, H / 2, Z_BACK + WALL / 2), (2 * HALF_W, H + 0.2, WALL))
    for side in (-1, 1):
        cx = side * (SEAT_X[0] + SEAT_X[1]) / 2
        pw = SEAT_X[1] - SEAT_X[0] + SEAT_W
        for r, z in enumerate(ROWS):
            nm = "%s%d" % ("L" if side < 0 else "R", r + 1)
            box("Pan" + nm, (cx, SEAT_Y - 0.04, z), (pw, 0.05, SEAT_W))
            box("Leg" + nm, (side * SEAT_X[0], (SEAT_Y - 0.06) / 2, z - 0.1), (0.04, SEAT_Y - 0.06, 0.04))
            box("Strut" + nm, (cx, 0.2, z + 0.15), (pw, 0.03, 0.03))
            box("BackFrame" + nm, (cx, 0.78, z + SEAT_W / 2), (pw, 0.62, 0.035), basis_x(8))
            box("Grab" + nm, (side * SEAT_X[0], 1.13, z + SEAT_W / 2 + 0.04), (0.18, 0.03, 0.03))
    box("BenchPan", (0, SEAT_Y - 0.04, BENCH_Z), (2 * HALF_W, 0.05, SEAT_W))
    box("BenchBase", (0, 0.2, BENCH_Z), (2 * HALF_W, 0.4, SEAT_W - 0.05))
    box("BenchBack", (0, 0.8, BENCH_Z + SEAT_W / 2 + 0.02), (2 * HALF_W, 0.7, 0.04))
    door_zc = (DOOR_Z[0] + DOOR_Z[1]) / 2
    box("DashBase", (0, 0.55, Z_FRONT + 0.35), (2 * HALF_W, 1.1, 0.6))
    box("EngineHump", (-0.05, 0.3, Z_FRONT + 0.95), (0.7, 0.6, 0.8))
    box("DriverSeatBase", (-0.7, 0.25, -4.05), (0.5, 0.5, 0.5))
    box("DriverSeatBack", (-0.7, 0.85, -3.8), (0.5, 0.7, 0.08))
    box("DriverPartition", (-0.72, 0.55, -3.62), (0.95, 1.1, 0.04))
    box("Step", (0.95, 0.1, door_zc), (0.6, 0.2, 0.9))


# ---------------------------------------------------------------------------

def build_bus():
    import bake_bus_textures
    import bus_models
    bake_bus_textures.main()
    bus_models.build_all()
    import people_models
    people_models.build_all()
    import prop_models
    prop_models.build_all()

    sc = Scene("Bus")
    p_rid = sc.ext_res("PackedScene", "res://scenes/player/Player.tscn")
    level_script = sc.ext_res("Script", "res://scripts/bus/BusLevel.gd")
    scroll_script = sc.ext_res("Script", "res://scripts/bus/ScrollingScenery.gd")
    rng_seats = random.Random(77)

    # --- Vật liệu dùng chung ---
    rust = sc.pbr("Rust", "rust_metal", (1, 1, 1), metallic=0.5)
    chrome = sc.mat("BusChrome", (0.66, 0.66, 0.64), 0.3, metallic=0.9)
    wood_sign = sc.pbr("SignWood", "wood_weathered", (0.7, 0.62, 0.55), normal=1.4)
    skin = sc.mat("Skin", (0.62, 0.46, 0.36), 0.7)
    skin_old = sc.mat("SkinOld", (0.56, 0.42, 0.34), 0.75)
    hair = sc.mat("Hair", (0.04, 0.035, 0.03), 0.55)
    hair_grey = sc.mat("HairGrey", (0.55, 0.53, 0.5), 0.7)
    non_la = sc.pbr("NonLa", "bamboo_weave", (1.0, 0.92, 0.72), triplanar=True)
    mu_coi = sc.mat("MuCoi", (0.3, 0.36, 0.22), 0.6)
    khan = sc.mat("KhanRan", (0.2, 0.18, 0.16), 0.95)
    cloth = lambda name, c: uvmat(sc, name, "fabric", c, rough=1.0, scale=0.6)
    shirts = [cloth("Shirt%d" % i, c) for i, c in enumerate([
        (0.85, 0.83, 0.78), (0.35, 0.4, 0.3), (0.5, 0.32, 0.22), (0.3, 0.38, 0.55), (0.78, 0.7, 0.55),
        (0.62, 0.25, 0.22), (0.9, 0.9, 0.92), (0.4, 0.3, 0.38)])]
    pants = [cloth("Pants%d" % i, c) for i, c in enumerate([
        (0.08, 0.08, 0.09), (0.25, 0.28, 0.22), (0.16, 0.18, 0.26), (0.3, 0.26, 0.2)])]
    ao_nau = cloth("AoNau", (0.38, 0.24, 0.15))  # áo nâu bà cụ
    sack = sc.pbr("Sack", "fabric", (0.8, 0.72, 0.55), normal=1.2)
    basket = sc.pbr("Basket", "bamboo_weave", (1, 0.9, 0.75), normal=1.0)
    chicken = sc.mat("Chicken", (0.62, 0.38, 0.18), 0.9)
    comb = sc.mat("Comb", (0.75, 0.1, 0.08), 0.7)
    leaf_dry = sc.mat("LeafDry", (0.32, 0.24, 0.12), 1.0, cull=True)
    shard = sc.mat("GlassShard", (0.7, 0.75, 0.75), 0.05, metallic=0.4, alpha=0.6)
    stain = sc.mat("DarkStain", (0.08, 0.02, 0.02), 0.6)
    foam = sc.mat("Foam", (0.62, 0.52, 0.28), 1.0)
    trunk = sc.pbr("Trunk", "wood_dark", (0.5, 0.42, 0.36))

    d_mold = sc.decal_mat("DecalMold", "mold.png", (0.6, 0.65, 0.5, 0.9))
    d_soot = sc.decal_mat("DecalSoot", "soot.png", (1, 1, 1, 0.85))
    d_stain = sc.decal_mat("DecalStain", "stain_damp.png", (0.9, 0.85, 0.75, 0.9))
    d_scratch = sc.decal_mat("DecalScratch", "scratches.png", (0.9, 0.9, 0.9, 0.8))
    d_hand = sc.decal_mat("DecalHand", "handprint.png", (0.35, 0.06, 0.05, 0.9))
    d_crack = sc.decal_mat("DecalCrack", "crack.png", (1, 1, 1, 0.9))
    d_web = sc.decal_mat("DecalWeb", "cobweb.png", (1, 1, 1, 0.85))
    d_joss = sc.decal_mat("DecalJoss", "joss_paper.png", (1, 1, 1, 1))
    d_talisman = sc.decal_mat("DecalTalisman", "talisman.png", (1, 1, 1, 1))
    d_moss = texmat(sc, "DecalMoss", "moss_patch.png", alpha=True, rough=1.0)

    # --- Môi trường ---
    # Ban ngày: nắng chiều vàng, sương khối mỏng cho tia nắng xiên qua cửa kính.
    env_day = env_resource(sc, "Day", (0.32, 0.48, 0.72), (0.95, 0.72, 0.45), (0.2, 0.18, 0.12),
                           (1.0, 0.86, 0.68), 0.5, (0.95, 0.78, 0.55), 0.004, exposure=1.0,
                           vol=(0.012, (1.0, 0.92, 0.8), 24.0, 0.15), adjust=(1.0, 1.08, 1.05), glow=0.55)
    # Xác xe: đêm sương lạnh, hơi nước đặc trong lòng xe.
    env_derelict = env_resource(sc, "Derelict", (0.02, 0.025, 0.04), (0.08, 0.1, 0.12), (0.02, 0.02, 0.02),
                                (0.32, 0.4, 0.5), 0.2, (0.12, 0.15, 0.18), 0.06, exposure=1.15,
                                sky_energy=0.3, vol=(0.035, (0.7, 0.78, 0.85), 18.0, 0.4),
                                adjust=(1.0, 1.12, 0.8), glow=0.6, ssao=2.0)
    # Đêm 1999: mưa đen, đèn bão vàng cam trong xe, đèn pha xé màn mưa.
    env_night = env_resource(sc, "Night1999", (0.01, 0.018, 0.022), (0.03, 0.05, 0.05), (0.01, 0.01, 0.012),
                             (0.3, 0.42, 0.45), 0.14, (0.05, 0.08, 0.08), 0.035, exposure=1.2, sky_energy=0.2,
                             vol=(0.03, (0.75, 0.82, 0.88), 32.0, 0.2), adjust=(1.0, 1.1, 0.85), glow=0.7,
                             ssao=2.0)

    sc.nodes[0] = ('[node name="Bus" type="Node3D"]\nscript = ExtResource("%s")\n'
                   'day_environment = SubResource("%s")\nderelict_environment = SubResource("%s")\n'
                   'night_environment = SubResource("%s")\n'
                   % (level_script, env_day, env_derelict, env_night))
    sc.node("WorldEnvironment", "WorldEnvironment", ".", [("environment", 'SubResource("%s")' % env_day)])

    build_collision(sc)
    sc.empty("Fixtures")

    M_day = layer_materials(sc, "day")
    M_wreck = layer_materials(sc, "wreck")
    M_night = layer_materials(sc, "night")

    # =======================================================================
    # TRẠNG THÁI 1: CHIỀU MUỘN, XE 2006 ĐÔNG KHÁCH ĐANG CHẠY
    # =======================================================================
    day = sc.empty("Day")
    build_interior(sc, day, M_day, "day", rng_seats)
    for z in (-2.5, 0.5, 3.0):
        sc.mesh("Tube", day, "cyl", (0.016, 0.016, 1.1, 8), (0, H - 0.06, z),
                sc.mat("TubeDay", (0.9, 0.92, 0.95), 0.3, emission=(0.8, 0.85, 0.9), energy=0.3),
                basis=basis_x(90), shadow=False)
    # Bàn thờ nhỏ trên taplô: tượng Phật, bát hương, lọ hoa nhựa; dây hoa vắt ngang kính lái.
    place(sc, "DashAltar", day, "dash_altar", M_day, (0.42, 1.1, Z_FRONT + 0.26))
    place(sc, "Garland", day, "garland", M_day, shadow=0)
    sc.decal("Talisman", day, (0, 1.75, Z_FRONT + 0.06), "+z", (0.12, 0.3), d_talisman, offset=0.0)
    reflection_probe(sc, day, 0.8)

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

    # Giỏ gà dưới chân bà cụ, bao tải gạo ở cuối xe, hành lý trên giá.
    props = sc.empty("Props", day)
    bx, bz = -SEAT_X[1] + 0.02, ROWS[OLD_WOMAN_ROW] - 0.42
    sc.mesh("Basket", props, "cyl", (0.2, 0.15, 0.24, 14), (bx, 0.12, bz), basket)
    sc.mesh("ChickenBody", props, "sphere", (0.11, 0.18), (bx, 0.3, bz), chicken)
    sc.mesh("ChickenHead", props, "sphere", (0.045, 0.09), (bx, 0.42, bz - 0.08), chicken)
    sc.mesh("ChickenComb", props, "box", (0.012, 0.04, 0.05), (bx, 0.47, bz - 0.08), comb)
    import people_models
    people_models.place_hat(sc, "NonLaLap", props, "non_la", non_la, (-SEAT_X[0], 0.66, ROWS[OLD_WOMAN_ROW] - 0.2),
                            basis_x(-70))
    for k, (x, y, rz) in enumerate([(-0.8, 0.66, 0), (-0.35, 0.66, 10), (0.15, 0.66, -6), (0.7, 0.66, 4),
                                     (0.35, 0.98, 80)]):
        place(sc, "RiceSack", props, "luggage_sack", M_day, (x, y, BENCH_Z - 0.02),
              basis_mul(basis_z(rz), basis_y(90)))
    lug = [("luggage_sack", 1.0, ROWS[1] - 0.05), ("luggage_box", -1.0, ROWS[1] + 0.35),
           ("luggage_case", 1.0, ROWS[3] + 0.3), ("luggage_sack", -1.0, ROWS[5] + 0.4),
           ("luggage_box", 1.0, ROWS[5]), ("luggage_case", -1.0, ROWS[7]), ("luggage_sack", 1.0, ROWS[7] + 0.2)]
    for model, x, z in lug:
        y = 1.93 if model != "luggage_case" else 1.92
        place(sc, "Luggage", props, model, M_day, (x, y, z), rot_y=rng_seats.uniform(-10, 10))

    # Nắng chiều xiên từ bên phải xe.
    directional(sc, "Sun", day, -16, 65, (1.0, 0.78, 0.5), 2.4, fog=1.5)
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
    people_models.build_day_scenery(sc, out, scroll_script, ground_mat, road_mat)

    # =======================================================================
    # TRẠNG THÁI 2: XÁC XE NẰM BÃI SÔNG
    # =======================================================================
    der = sc.empty("Derelict", ".", props=[("visible", "false")])
    build_interior(sc, der, M_wreck, "wreck", rng_seats)
    windows = WIN_Y
    for side in (-1, 1):
        for i, z in enumerate(ROWS + [BENCH_Z]):
            if i % 3 == 2:
                sc.decal("Crack", der, (side * (HALF_W + 0.025), 1.3, z), "-x" if side > 0 else "+x", (0.5, 0.5),
                         d_crack, roll=random.uniform(0, 360), offset=0.0)
    sc.decal("CrackFront", der, (-0.6, 1.5, Z_FRONT - 0.015), "+z", (0.9, 0.9), d_crack, roll=40, offset=0.0)
    # Bàn tay in trên kính cửa xe và một ô kính bên phải, như ai đó ở ngoài áp vào.
    door_zc = (DOOR_Z[0] + DOOR_Z[1]) / 2
    sc.decal("HandDoor", der, (HALF_W + 0.012, 1.45, door_zc + 0.1), "-x", (0.2, 0.24), d_hand, roll=-8,
             offset=0.0)
    sc.decal("HandWindow", der, (HALF_W + 0.022, 1.35, ROWS[AN_ROW] + 0.12), "-x", (0.2, 0.24), d_hand, roll=12,
             offset=0.0)
    sc.decal("HandWindow", der, (HALF_W + 0.022, 1.2, ROWS[AN_ROW] - 0.15), "-x", (0.2, 0.24), d_hand, roll=-20,
             offset=0.0)

    # Đèn tuýp: một bóng còn chập chờn, hai bóng chết, một bóng rơi lủng lẳng.
    tube_dead = sc.mat("TubeDead", (0.3, 0.3, 0.28), 0.6)
    tube_cold = sc.mat("TubeCold", (0.85, 0.95, 1.0), 0.3, emission=(0.7, 0.85, 1.0), energy=3.0)
    sc.mesh("TubeDead", der, "cyl", (0.016, 0.016, 1.1, 8), (0, H - 0.06, -2.5), tube_dead, basis=basis_x(90),
            shadow=False)
    sc.mesh("TubeHanging", der, "cyl", (0.016, 0.016, 1.1, 8), (0.1, H - 0.35, 3.0), tube_dead,
            basis=basis_mul(basis_x(90), basis_z(-30)), shadow=False)
    tube_light = sc.node("TubeLight", "OmniLight3D", der, [
        ("transform", xform((0, H - 0.12, 0.5))),
        ("light_color", color((0.72, 0.86, 1.0))), ("light_energy", "1.2"), ("omni_range", "6.5"),
        ("omni_attenuation", "1.2"), ("shadow_enabled", "true"), ("shadow_blur", "1.5"),
        ("light_volumetric_fog_energy", "1.5"),
        ("script", 'ExtResource("%s")' % sc.ext_res("Script", "res://scripts/levels/LightFlicker.gd")),
        ("hum", "0.12"), ("calm_range", "Vector2(1.5, 5)"), ("burst_count", "Vector2i(3, 9)"), ("dip", "0.02"),
        ("emissive_mesh", 'NodePath("Tube")'),
    ])
    sc.mesh("Tube", tube_light, "cyl", (0.016, 0.016, 1.1, 8), (0, 0.06, 0), tube_cold, basis=basis_x(90),
            shadow=False)
    sc.node("DashGlow", "OmniLight3D", der, [
        ("transform", xform((0.45, 1.3, Z_FRONT + 0.4))),
        ("light_color", color((0.9, 0.2, 0.12))), ("light_energy", "0.35"), ("omni_range", "1.8"),
    ])
    directional(sc, "Moon", der, -24, 160, (0.42, 0.52, 0.72), 0.3, fog=2.0)
    reflection_probe(sc, der, 0.5)

    # Vết mục: mốc, muội, ố, cào xước trên vách, trần và sàn; rêu bám chân vách và sàn.
    for k in range(14):
        side = random.choice((-1, 1))
        z = random.uniform(Z_FRONT + 1.5, Z_BACK - 0.3)
        y = random.choice((random.uniform(0.25, 0.8), random.uniform(1.75, 1.84)))
        mat = random.choice((d_mold, d_soot, d_stain, d_stain))
        sc.decal("WallRot", der, (side * (HALF_W - 0.01), y, z), "-x" if side > 0 else "+x",
                 (random.uniform(0.5, 1.1),) * 2, mat, roll=random.uniform(0, 360), offset=0.002)
    for k in range(7):
        sc.decal("CeilRot", der, (random.uniform(-0.55, 0.55), H - 0.003, random.uniform(-3.5, 4.0)), "-y",
                 (random.uniform(0.6, 1.1),) * 2, random.choice((d_mold, d_stain, d_soot)),
                 roll=random.uniform(0, 360), offset=0.0)
    for k in range(6):
        sc.decal("FloorGrime", der, (random.uniform(-0.4, 0.4), 0.012, random.uniform(-3.5, 4.0)), "+y",
                 (random.uniform(0.6, 1.1),) * 2, random.choice((d_stain, d_soot)), roll=random.uniform(0, 360),
                 offset=0.0)
    mrng = random.Random(31)
    for k in range(16):
        side = mrng.choice((-1, 1))
        if k < 10:
            sc.decal("Moss", der, (side * mrng.uniform(0.6, 1.15), 0.015, mrng.uniform(-3.3, 4.3)), "+y",
                     (mrng.uniform(0.4, 0.9),) * 2, d_moss, roll=mrng.uniform(0, 360), offset=0.0)
        else:
            sc.decal("Moss", der, (side * (HALF_W - 0.012), mrng.uniform(0.05, 0.3), mrng.uniform(-3.0, 4.2)),
                     "-x" if side > 0 else "+x", (mrng.uniform(0.4, 0.8),) * 2, d_moss, roll=mrng.uniform(0, 360),
                     offset=0.0)
    # Vũng nước đọng phản chiếu trên sàn.
    puddle = sc.mat("Puddle", (0.04, 0.045, 0.04), 0.02, metallic=0.3, alpha=0.82)
    for k, (x, z, s) in enumerate([(0.05, -1.9, 0.6), (-0.1, 1.2, 0.8), (0.15, 3.4, 0.5)]):
        sc.mesh("Puddle", der, "cyl", (s * 0.5, s * 0.5, 0.002, 18), (x, 0.012, z), puddle,
                basis=basis_scale(1.0, 1.0, 1.6), shadow=False)
    sc.decal("Scratch", der, (-HALF_W + 0.01, 1.2, ROWS[2] + 0.4), "+x", (0.5, 0.4), d_scratch, offset=0.003)
    sc.decal("Scratch", der, (0.28, 0.85, ROWS[AN_ROW] + SEAT_W / 2 + 0.07), "+z", (0.3, 0.3), d_scratch,
             roll=90, offset=0.0)
    for x, y, z, facing in [(-HALF_W + 0.01, 1.82, Z_BACK - 0.2, "+x"), (HALF_W - 0.01, 1.82, Z_FRONT + 1.4, "-x"),
                            (-HALF_W + 0.01, 1.8, ROWS[4], "+x"), (0.5, H - 0.003, ROWS[1], "-y")]:
        sc.decal("Cobweb", der, (x, y, z), facing, (0.7, 0.7), d_web, offset=0.0)
    sc.decal("TalismanTorn", der, (0, 1.75, Z_FRONT + 0.06), "+z", (0.12, 0.3), d_talisman, roll=14, offset=0.0)

    # Rác trên sàn: vàng mã, lá khô, mảnh kính, nệm rơi, giỏ gà đổ.
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
                    (wx * random.uniform(0.25, 1.0), 0.53 if k < 2 else 0.015, z + random.uniform(-0.3, 0.3)),
                    shard, rot_y=random.uniform(0, 360), shadow=False)
    place(sc, "FallenCushion", deb, "seat_cushion_R", M_wreck, (0.62, -0.42, ROWS[6] - 0.3),
          basis_mul(basis_y(24), basis_z(6)))
    sc.mesh("FallenFoam", deb, "box", (0.25, 0.02, 0.2), (0.25, 0.11, ROWS[6] - 0.25), foam, rot_y=24)
    bx, bz = -SEAT_X[1] + 0.05, ROWS[OLD_WOMAN_ROW] - 0.42
    basket_rot = wreck_mat(sc, "BasketRotten", "bamboo_weave", (0.6, 0.5, 0.4), rust=0.0, moss=0.5, world_uv=True)
    sc.mesh("BasketTipped", deb, "cyl", (0.2, 0.15, 0.24, 14), (bx, 0.17, bz), basket_rot,
            basis=basis_mul(basis_y(30), basis_z(80)))
    for k in range(5):
        sc.mesh("Feather", deb, "box", (0.05, 0.003, 0.015), (bx + random.uniform(0.1, 0.5), 0.016,
                                                              bz + random.uniform(-0.2, 0.3)),
                sc.mat("Feather", (0.45, 0.32, 0.2), 1.0), rot_y=random.uniform(0, 360), shadow=False)
    place(sc, "Bag", deb, "luggage_sack", dict(M_wreck, sack=wreck_mat(sc, "SackRotten", "fabric", (0.5, 0.45, 0.35),
                                                                     rust=0.0, moss=0.5, scale=0.6),
                                             rope=sc.mat("RopeRotten", (0.3, 0.26, 0.2), 1.0)),
          (1.0, 1.92, ROWS[1] - 0.05), rot_y=8)
    # Năm vết thâm đen trên lưng ghế An vừa tựa (khớp 5 vết đinh trên người An).
    back_z = ROWS[AN_ROW] + 0.2 - 0.075 / 2 - 0.03
    for k, (dx, dy) in enumerate([(0.0, 0.25), (-0.1, 0.12), (0.1, 0.12), (-0.07, -0.02), (0.07, -0.02)]):
        y = 0.84 + dy
        z = back_z + (y - 0.5) * math.tan(math.radians(10)) - 0.004
        sc.mesh("Stain%d" % (k + 1), deb, "cyl", (0.022, 0.026, 0.004, 10),
                (SEAT_X[1] + dx, y, z), stain, basis=basis_x(100), shadow=False)
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

    # =======================================================================
    # CHƯƠNG 2: dấu vết đêm 1999 trên xác xe, lớp "Đêm 1999" và cảnh xe 2006 đông cứng.
    # Dùng bộ sinh số riêng để phần trên không đổi khi sửa phần này.
    # =======================================================================
    rng = random.Random(1404)
    build_wreck_traces(sc, der, rng, rust, chrome, wood_sign)
    build_night_1999(sc, rng, M_night, rust, chrome, wood_sign, d_talisman, trunk)
    build_day_glimpse(sc, rng, shirts, pants, skin, hair, basket)
    seat_numbers(sc)

    # Người chơi đứng ở chân cửa xe, nhìn dọc lối đi về phía sau.
    sc.instance("Player", p_rid, props=[("transform", xform((0.0, 0.05, -3.1), 180))])
    sc.save("scenes/levels/Bus.tscn")


if __name__ == "__main__":
    build_bus()
