## Sinh bộ texture PBR (albedo / normal / roughness) và các decal cho hai bối cảnh.
##
## Chạy (không cần mở editor):
##   godot --headless --path . -s tools/bake_textures.gd
## Kết quả nằm trong res://assets/textures/. Mọi texture đều lặp liền mạch (tileable)
## để dùng với triplanar mapping trên CSG. Seed cố định nên chạy lại cho ra đúng ảnh cũ.
##
## Bộ nào đã có texture CC0 thật (ghi trong assets/textures/cc0_sets.json, tải bằng
## tools/fetch_cc0_assets.py) thì bị bỏ qua để không ghi đè ảnh thật.
extends SceneTree

const OUT := "res://assets/textures/"
const DECAL := "res://assets/textures/decals/"


func _init() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(DECAL))
	var only := OS.get_environment("BAKE_ONLY")
	var jobs := [
		"oak_floor", "plaster_white", "limewash_old", "tile_terracotta", "brick_red", "roof_tile",
		"concrete_damp", "earth", "fabric", "reed_mat", "bamboo_weave", "rust_metal", "lacquer_red",
		"wood_dark", "wood_weathered", "painted_wood", "grass", "rug_dream", "newspaper",
		"decals",
	]
	var cc0 := {}
	if FileAccess.file_exists(OUT + "cc0_sets.json"):
		cc0 = JSON.parse_string(FileAccess.get_file_as_string(OUT + "cc0_sets.json"))
	for job in jobs:
		if only != "" and not (job in only.split(",")):
			continue
		if cc0.has(job):
			print("skip %s (CC0 texture)" % job)
			continue
		var t := Time.get_ticks_msec()
		call("bake_" + job)
		print("baked %s in %d ms" % [job, Time.get_ticks_msec() - t])
	quit()


# ---------------------------------------------------------------------------
# Tiện ích nhiễu liền mạch
# ---------------------------------------------------------------------------

## Nhiễu liền mạch dạng mảng 0..1, [param cycles] = số "đốm" trên một cạnh ảnh.
func noise(seed_: int, cycles: float, size: int, octaves := 5,
		type := FastNoiseLite.TYPE_SIMPLEX_SMOOTH) -> PackedFloat32Array:
	var fn := FastNoiseLite.new()
	fn.seed = seed_
	fn.noise_type = type
	fn.frequency = cycles / float(size)
	fn.fractal_octaves = octaves
	fn.fractal_type = FastNoiseLite.FRACTAL_FBM if octaves > 1 else FastNoiseLite.FRACTAL_NONE
	return _img_to_floats(fn.get_seamless_image(size, size, false, false, 0.15, true))


## Nhiễu tế bào: trả về khoảng cách tới biên tế bào (nhỏ = gần biên), dùng vẽ vết nứt.
func cells(seed_: int, cycles: float, size: int, jitter := 1.0) -> PackedFloat32Array:
	var fn := FastNoiseLite.new()
	fn.seed = seed_
	fn.noise_type = FastNoiseLite.TYPE_CELLULAR
	fn.frequency = cycles / float(size)
	fn.fractal_type = FastNoiseLite.FRACTAL_NONE
	fn.cellular_return_type = FastNoiseLite.RETURN_DISTANCE2_SUB
	fn.cellular_jitter = jitter
	fn.domain_warp_enabled = false
	return _img_to_floats(fn.get_seamless_image(size, size, false, false, 0.1, true))


func _img_to_floats(img: Image) -> PackedFloat32Array:
	img.convert(Image.FORMAT_L8)
	var data := img.get_data()
	var out := PackedFloat32Array()
	out.resize(data.size())
	for i in data.size():
		out[i] = data[i] / 255.0
	return out


## Nhiễu dị hướng liền mạch (vân gỗ, sợi vải): lấy mẫu 4 góc rồi trộn có bù phương sai.
class Aniso:
	var fn := FastNoiseLite.new()
	var px: float
	var py: float

	func _init(seed_: int, px_: float, py_: float, octaves := 4) -> void:
		fn.seed = seed_
		fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
		fn.frequency = 1.0
		fn.fractal_octaves = octaves
		fn.fractal_type = FastNoiseLite.FRACTAL_FBM if octaves > 1 else FastNoiseLite.FRACTAL_NONE
		px = px_
		py = py_

	func at(u: float, v: float, ox := 0.0) -> float:
		var x := u * px + ox
		var y := v * py
		var wa := (1.0 - u) * (1.0 - v)
		var wb := u * (1.0 - v)
		var wc := (1.0 - u) * v
		var wd := u * v
		var s := wa * fn.get_noise_2d(x, y) + wb * fn.get_noise_2d(x - px, y) \
				+ wc * fn.get_noise_2d(x, y - py) + wd * fn.get_noise_2d(x - px, y - py)
		return s / sqrt(wa * wa + wb * wb + wc * wc + wd * wd)


static func ss(e0: float, e1: float, x: float) -> float:
	return smoothstep(e0, e1, x)


static func hash1(a: int, b := 0) -> float:
	var h := (a * 374761393 + b * 668265263) & 0x7fffffff
	h = ((h ^ (h >> 13)) * 1274126177) & 0x7fffffff
	return float(h % 10000) / 10000.0


# ---------------------------------------------------------------------------
# Lưu bộ ảnh
# ---------------------------------------------------------------------------

class TexSet:
	var size: int
	var alb := PackedFloat32Array()
	var hgt := PackedFloat32Array()
	var rgh := PackedFloat32Array()

	func _init(s: int) -> void:
		size = s
		alb.resize(s * s * 3)
		hgt.resize(s * s)
		rgh.resize(s * s)

	func put(i: int, c: Vector3, h: float, r: float) -> void:
		alb[i * 3] = c.x
		alb[i * 3 + 1] = c.y
		alb[i * 3 + 2] = c.z
		hgt[i] = h
		rgh[i] = r


func save_set(name: String, t: TexSet, normal_strength := 2.0) -> void:
	var s := t.size
	var a := PackedByteArray()
	a.resize(s * s * 3)
	for i in s * s * 3:
		a[i] = int(clampf(t.alb[i], 0.0, 1.0) * 255.0 + 0.5)
	Image.create_from_data(s, s, false, Image.FORMAT_RGB8, a).save_jpg(OUT + name + "_albedo.jpg", 0.9)
	var r := PackedByteArray()
	r.resize(s * s)
	for i in s * s:
		r[i] = int(clampf(t.rgh[i], 0.0, 1.0) * 255.0 + 0.5)
	Image.create_from_data(s, s, false, Image.FORMAT_L8, r).save_jpg(OUT + name + "_rough.jpg", 0.9)
	var n := PackedByteArray()
	n.resize(s * s * 3)
	var k := normal_strength * s / 512.0
	for y in s:
		var ym := ((y - 1 + s) % s) * s
		var yp := ((y + 1) % s) * s
		for x in s:
			var xm := (x - 1 + s) % s
			var xp := (x + 1) % s
			var dx := (t.hgt[y * s + xm] - t.hgt[y * s + xp]) * k
			var dy := (t.hgt[ym + x] - t.hgt[yp + x]) * k
			var v := Vector3(dx, dy, 1.0).normalized()
			var i := (y * s + x) * 3
			n[i] = int((v.x * 0.5 + 0.5) * 255.0)
			# Godot dùng normal map kiểu OpenGL (Y+).
			n[i + 1] = int((-v.y * 0.5 + 0.5) * 255.0)
			n[i + 2] = int((v.z * 0.5 + 0.5) * 255.0)
	Image.create_from_data(s, s, false, Image.FORMAT_RGB8, n).save_png(OUT + name + "_normal.png")


## Ảnh RGBA cho decal/tranh. [param fn] nhận (u, v) trả Color (sRGB, có alpha).
func save_rgba(path: String, s: int, fn: Callable) -> void:
	var b := PackedByteArray()
	b.resize(s * s * 4)
	for y in s:
		for x in s:
			var c: Color = fn.call((x + 0.5) / s, (y + 0.5) / s)
			var i := (y * s + x) * 4
			b[i] = int(clampf(c.r, 0, 1) * 255)
			b[i + 1] = int(clampf(c.g, 0, 1) * 255)
			b[i + 2] = int(clampf(c.b, 0, 1) * 255)
			b[i + 3] = int(clampf(c.a, 0, 1) * 255)
	Image.create_from_data(s, s, false, Image.FORMAT_RGBA8, b).save_png(path)


# ---------------------------------------------------------------------------
# Gỗ
# ---------------------------------------------------------------------------

## Vân gỗ chạy theo trục U. Trả về (giá trị vân 0..1, độ sáng sợi).
func _grain(g: Aniso, f: Aniso, u: float, v: float, ox: float) -> Vector2:
	var w := g.at(u, v, ox)
	# Vòng năm: lấy phần lẻ của giá trị nhiễu kéo giãn để ra các sọc cong.
	var ring := fposmod(w * 5.0 + v * 3.0, 1.0)
	ring = ss(0.0, 0.15, ring) * (1.0 - ss(0.55, 1.0, ring))
	var fiber := f.at(u, v, ox) * 0.5 + 0.5
	return Vector2(ring, fiber)


func bake_oak_floor() -> void:
	# Sàn gỗ sồi sáng: 6 hàng ván trên một ô texture (ô = 1.2 m).
	var s := 1024
	var t := TexSet.new(s)
	var g := Aniso.new(11, 3.0, 36.0, 4)
	var f := Aniso.new(12, 6.0, 420.0, 2)
	var dirt := noise(13, 6, s, 4)
	var rows := 6
	var base := Vector3(0.80, 0.62, 0.42)
	for y in s:
		var v := (y + 0.5) / s
		var row := int(v * rows)
		var lv := v * rows - row
		var tone := 0.88 + 0.22 * hash1(row, 1)
		var hue := hash1(row, 2) * 0.08
		var off := hash1(row, 3)
		var plen := 0.5 if hash1(row, 4) > 0.5 else 1.0
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var gr := _grain(g, f, u, v * rows, row * 1.7)
			var pu := fposmod(u - off, plen) / plen
			var gap := 1.0 - (ss(0.0, 0.006, lv) * (1.0 - ss(0.994, 1.0, lv)))
			var joint := 1.0 - ss(0.0, 0.004 / plen, pu) * (1.0 - ss(1.0 - 0.004 / plen, 1.0, pu))
			gap = maxf(gap, joint)
			var k := tone * (0.82 + 0.22 * gr.y - 0.16 * gr.x) - 0.1 * dirt[i] * 0.5
			var c := Vector3(base.x * k, base.y * k * (1.0 - hue * 0.5), base.z * k * (1.0 - hue))
			c = c.lerp(Vector3(0.3, 0.2, 0.13), gap * 0.7)
			var h := 0.85 + 0.08 * gr.x + 0.05 * gr.y - 0.8 * gap
			t.put(i, c, h, 0.42 + 0.12 * gr.x + 0.1 * dirt[i] + gap * 0.4)
	save_set("oak_floor", t, 1.5)


func _wood(name: String, seed_: int, base: Vector3, dark: Vector3, rough: float, s := 512) -> void:
	var t := TexSet.new(s)
	var g := Aniso.new(seed_, 2.0, 14.0, 4)
	var f := Aniso.new(seed_ + 1, 4.0, 200.0, 2)
	var wear := noise(seed_ + 2, 4, s, 5)
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var gr := _grain(g, f, u, v, 0.0)
			var k := 0.75 + 0.35 * gr.y
			var c := base.lerp(dark, gr.x * 0.6) * k
			c = c.lerp(c * 0.7, ss(0.55, 0.8, wear[i]))
			t.put(i, c, 0.6 + 0.2 * gr.y - 0.15 * gr.x, rough + 0.1 * gr.x + 0.15 * ss(0.5, 0.8, wear[i]))
	save_set(name, t, 1.2)


func bake_wood_dark() -> void:
	# Gỗ lim/xoan đã sẫm màu theo năm tháng: tủ chè, giường, bàn ghế nhà cũ.
	_wood("wood_dark", 21, Vector3(0.36, 0.21, 0.12), Vector3(0.16, 0.08, 0.04), 0.5)


func bake_wood_weathered() -> void:
	# Gỗ mộc bạc màu, khô: bậc thang hầm, thùng, kệ.
	var s := 512
	var t := TexSet.new(s)
	var g := Aniso.new(31, 2.0, 18.0, 4)
	var f := Aniso.new(32, 3.0, 260.0, 3)
	var stain := noise(33, 3, s, 5)
	var crack := Aniso.new(34, 1.5, 60.0, 1)
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var gr := _grain(g, f, u, v, 0.0)
			var cr := absf(crack.at(u, v))
			var split := 1.0 - ss(0.0, 0.03, cr)
			var c := Vector3(0.45, 0.38, 0.3) * (0.7 + 0.4 * gr.y)
			c = c.lerp(Vector3(0.22, 0.18, 0.14), gr.x * 0.4 + ss(0.5, 0.85, stain[i]) * 0.5)
			c = c.lerp(Vector3(0.06, 0.05, 0.04), split * 0.8)
			t.put(i, c, 0.6 + 0.3 * gr.y - 0.5 * split, 0.85 + 0.1 * gr.y)
	save_set("wood_weathered", t, 2.5)


func bake_painted_wood() -> void:
	# Ván gỗ sơn xanh ngọc đã bong tróc: cánh cửa, cửa chớp nhà cũ.
	var s := 512
	var t := TexSet.new(s)
	var g := Aniso.new(41, 1.0, 16.0, 4)
	var f := Aniso.new(42, 2.0, 220.0, 2)
	var peel := noise(43, 7, s, 6)
	var grime := noise(44, 3, s, 4)
	var boards := 5
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			# Ván dọc: vân chạy theo V.
			var gr := _grain(g, f, v, u, 0.0)
			var lb := fposmod(u * boards, 1.0)
			var gap := 1.0 - ss(0.0, 0.02, lb) * (1.0 - ss(0.98, 1.0, lb))
			var p := ss(0.68, 0.72, peel[i])
			var rim := ss(0.64, 0.68, peel[i]) * (1.0 - p)
			var paint := Vector3(0.36, 0.52, 0.5) * (0.9 + 0.15 * grime[i])
			var wood := Vector3(0.42, 0.36, 0.29) * (0.7 + 0.4 * gr.y)
			var c := paint.lerp(wood, p).lerp(Vector3(0.2, 0.22, 0.2), rim * 0.4)
			c = c.lerp(c * 0.55, ss(0.55, 0.9, grime[i]) * 0.6)
			c = c.lerp(Vector3(0.05, 0.05, 0.05), gap * 0.8)
			var h := 0.7 - 0.25 * p + 0.04 * gr.y * p - 0.6 * gap
			t.put(i, c, h, lerpf(0.6, 0.9, p) + 0.1 * grime[i])
	save_set("painted_wood", t, 2.0)


func bake_lacquer_red() -> void:
	# Sơn son bàn thờ: đỏ thẫm bóng, mòn ở chỗ hay chạm, lộ gỗ sẫm.
	var s := 512
	var t := TexSet.new(s)
	var wear := noise(51, 5, s, 6)
	var cloud := noise(52, 2, s, 4)
	var scratch := Aniso.new(53, 2.0, 90.0, 1)
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var w := ss(0.78, 0.84, wear[i])
			var sc := 1.0 - ss(0.0, 0.02, absf(scratch.at(u, v)))
			var c := Vector3(0.42, 0.06, 0.04) * (0.85 + 0.25 * cloud[i])
			c = c.lerp(Vector3(0.14, 0.06, 0.03), w).lerp(Vector3(0.6, 0.35, 0.25), sc * 0.25)
			t.put(i, c, 0.8 - 0.1 * w - 0.05 * sc, 0.3 + 0.45 * w + 0.25 * sc + 0.1 * cloud[i])
	save_set("lacquer_red", t, 1.0)


# ---------------------------------------------------------------------------
# Tường, trần
# ---------------------------------------------------------------------------

func bake_plaster_white() -> void:
	# Tường sơn trắng ngà mịn (phòng trong mơ): gần như phẳng, chỉ hơi gợn.
	var s := 512
	var t := TexSet.new(s)
	var a := noise(61, 3, s, 5)
	var b := noise(62, 60, s, 3)
	for i in s * s:
		var k := 0.97 + 0.04 * a[i] + 0.02 * b[i]
		t.put(i, Vector3(0.93, 0.915, 0.88) * k, b[i] * 0.4 + a[i] * 0.2, 0.85 + 0.08 * b[i])
	save_set("plaster_white", t, 0.6)


func bake_limewash_old() -> void:
	# Tường quét vôi vàng nhà cũ: loang ố, mốc chân tường, bong lớp vôi lộ vữa xám, nứt chân chim.
	var s := 1024
	var t := TexSet.new(s)
	var big := noise(71, 2.5, s, 6)
	var mid := noise(72, 9, s, 5)
	var fine := noise(73, 120, s, 2)
	var peel := noise(74, 6, s, 6)
	var crk := cells(75, 7, s, 0.9)
	var crk_mask := noise(76, 3, s, 4)
	var spot := noise(77, 40, s, 3)
	var base := Vector3(0.80, 0.71, 0.49)
	for i in s * s:
		var c := base * (0.94 + 0.08 * mid[i] + 0.05 * fine[i])
		# Vệt ố nước loang.
		var stain := ss(0.55, 0.85, big[i])
		c = c.lerp(Vector3(0.56, 0.47, 0.32), stain * 0.45)
		var tide := ss(0.5, 0.53, big[i]) * (1.0 - ss(0.55, 0.6, big[i]))
		c = c.lerp(Vector3(0.45, 0.36, 0.22), tide * 0.2)
		# Đốm mốc nhỏ.
		var mold := ss(0.78, 0.86, spot[i]) * ss(0.55, 0.8, big[i])
		c = c.lerp(Vector3(0.16, 0.17, 0.12), mold * 0.6)
		# Bong vôi lộ vữa xi măng.
		var p := ss(0.8, 0.83, peel[i])
		var rim := ss(0.76, 0.8, peel[i]) * (1.0 - p)
		c = c.lerp(Vector3(0.6, 0.56, 0.48) * (0.85 + 0.3 * fine[i]), p)
		c = c.lerp(Vector3(0.35, 0.3, 0.22), rim * 0.5)
		# Vết nứt chỉ hiện ở vài vùng.
		var cr := (1.0 - ss(0.0, 0.015, crk[i])) * ss(0.74, 0.85, crk_mask[i])
		c = c.lerp(Vector3(0.25, 0.2, 0.15), cr * 0.7)
		var h := 0.6 + 0.08 * mid[i] + 0.05 * fine[i] - 0.25 * p - 0.4 * cr
		t.put(i, c, h, 0.88 + 0.08 * fine[i] - 0.05 * stain)
	save_set("limewash_old", t, 2.0)


func bake_bamboo_weave() -> void:
	# Trần cót (phên tre đan lóng mốt) màu vàng xỉn, ố nước mưa dột.
	var s := 1024
	var t := TexSet.new(s)
	var strips := 32
	var fu := Aniso.new(81, 8.0, 300.0, 2)
	var fv := Aniso.new(82, 8.0, 300.0, 2)
	var stain := noise(83, 2.5, s, 6)
	var tone := noise(84, 30, s, 2)
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var cu := int(u * strips)
			var cv := int(v * strips)
			var horiz := ((cu + cv) % 4) < 2
			var lu := u * strips - cu
			var lv := v * strips - cv
			var across := lv if horiz else lu
			var edge := ss(0.0, 0.12, across) * (1.0 - ss(0.88, 1.0, across))
			var fib := (fu.at(u, v) if horiz else fv.at(v, u)) * 0.5 + 0.5
			var c := Vector3(0.72, 0.6, 0.38) * (0.75 + 0.3 * fib) * (0.85 + 0.15 * tone[i])
			c *= (0.92 if horiz else 1.0)
			c = c.lerp(Vector3(0.18, 0.13, 0.08), (1.0 - edge) * 0.7)
			var st := ss(0.55, 0.85, stain[i])
			c = c.lerp(Vector3(0.38, 0.27, 0.15), st * 0.6)
			var ring := ss(0.53, 0.56, stain[i]) * (1.0 - ss(0.58, 0.62, stain[i]))
			c = c.lerp(Vector3(0.25, 0.16, 0.08), ring * 0.5)
			t.put(i, c, edge * (0.7 + 0.2 * fib) + (0.0 if horiz else 0.1), 0.85 + 0.1 * fib)
	save_set("bamboo_weave", t, 2.0)


func bake_newspaper() -> void:
	# Báo cũ dán tường (giấy ngả vàng, cột chữ là các vạch mờ, không phải chữ thật).
	var s := 512
	var t := TexSet.new(s)
	var age := noise(91, 3, s, 5)
	var fine := noise(92, 80, s, 2)
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var col := fposmod(u * 4.0, 1.0)
			var in_col := ss(0.04, 0.06, col) * (1.0 - ss(0.94, 0.96, col))
			var line := fposmod(v * 70.0, 1.0)
			var word := hash1(int(u * 4.0 * 14.0), int(v * 70.0))
			var ink := in_col * ss(0.3, 0.4, line) * (1.0 - ss(0.75, 0.85, line)) * (1.0 if word > 0.15 else 0.0)
			var head := 1.0 if fposmod(v, 0.5) < 0.06 and in_col > 0.5 else 0.0
			ink = maxf(ink * 0.55, head * 0.8)
			var c := Vector3(0.82, 0.76, 0.6).lerp(Vector3(0.58, 0.47, 0.3), ss(0.4, 0.9, age[i]))
			c *= 0.95 + 0.08 * fine[i]
			c = c.lerp(Vector3(0.12, 0.11, 0.1), ink)
			t.put(i, c, 0.5 + 0.1 * fine[i], 0.9)
	save_set("newspaper", t, 0.5)


# ---------------------------------------------------------------------------
# Sàn, gạch, ngói, đất
# ---------------------------------------------------------------------------

func bake_tile_terracotta() -> void:
	# Gạch lá nem đỏ 30 x 30 cm (4 x 4 viên trên một ô 1.2 m), mòn, bẩn mạch vữa.
	var s := 1024
	var t := TexSet.new(s)
	var n := 4
	var dirt := noise(101, 7, s, 6)
	var fine := noise(102, 90, s, 3)
	var chip := noise(103, 24, s, 3)
	var wearn := noise(104, 8, s, 5)
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var tx := int(u * n)
			var ty := int(v * n)
			var lu := u * n - tx
			var lv := v * n - ty
			var d := minf(minf(lu, 1.0 - lu), minf(lv, 1.0 - lv))
			var grout := 1.0 - ss(0.012, 0.022, d + (chip[i] - 0.5) * 0.015)
			var bevel := ss(0.012, 0.05, d)
			var hv := hash1(tx + 17, ty + 3)
			var c := Vector3(0.52, 0.31, 0.22).lerp(Vector3(0.44, 0.27, 0.2), hv)
			c *= 0.88 + 0.16 * fine[i] + 0.1 * hash1(tx, ty)
			# Mòn ở giữa viên (chỗ hay đi) sáng và nhạt hơn.
			c = c.lerp(Vector3(0.62, 0.42, 0.32), ss(0.5, 0.8, wearn[i]) * 0.35)
			c = c.lerp(c * 0.6, ss(0.5, 0.9, dirt[i]) * 0.5)
			c = c.lerp(Vector3(0.16, 0.14, 0.12), grout)
			var h := 0.75 * bevel + 0.05 * fine[i]
			t.put(i, c, h, 0.78 + 0.12 * fine[i] - 0.1 * ss(0.5, 0.8, wearn[i]) + 0.1 * grout)
	save_set("tile_terracotta", t, 2.0)


func bake_brick_red() -> void:
	# Gạch chỉ đỏ xây kiểu so le (tường rào, bệ bếp): ô 1 m = 4 viên x 13 hàng.
	var s := 1024
	var t := TexSet.new(s)
	var rows := 13
	var cols := 4
	var fine := noise(111, 70, s, 3)
	var moss := noise(112, 4, s, 6)
	var chip := noise(113, 30, s, 3)
	for y in s:
		var v := (y + 0.5) / s
		var r := int(v * rows)
		var lv := v * rows - r
		var shift := 0.5 if r % 2 == 1 else 0.0
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var cu := fposmod(u * cols + shift, float(cols))
			var cidx := int(cu)
			var lu := cu - cidx
			var d := minf(minf(lu * 0.25 * rows / cols * 4.0, (1.0 - lu) * 0.25 * rows / cols * 4.0), minf(lv, 1.0 - lv))
			var mortar := 1.0 - ss(0.06, 0.11, d + (chip[i] - 0.5) * 0.06)
			var hv := hash1(cidx + 31 * r, 7)
			var c := Vector3(0.55, 0.24, 0.15).lerp(Vector3(0.4, 0.18, 0.12), hv)
			c = c.lerp(Vector3(0.62, 0.36, 0.24), hash1(cidx, r) * 0.3)
			c *= 0.85 + 0.25 * fine[i]
			c = c.lerp(Vector3(0.45, 0.43, 0.38) * (0.8 + 0.3 * fine[i]), mortar)
			var m := ss(0.62, 0.8, moss[i])
			c = c.lerp(Vector3(0.14, 0.17, 0.09), m * 0.75)
			t.put(i, c, 0.8 * (1.0 - mortar) + 0.1 * fine[i], 0.85 + 0.1 * fine[i] + 0.05 * mortar)
	save_set("brick_red", t, 3.0)


func bake_roof_tile() -> void:
	# Ngói mũi hài (vảy cá) Bắc Bộ, đỏ sẫm, rêu đen.
	var s := 512
	var t := TexSet.new(s)
	var rows := 8
	var cols := 8
	var moss := noise(121, 3, s, 6)
	var fine := noise(122, 60, s, 3)
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			# Mỗi hàng ngói chồng lên hàng phía dưới; mép dưới là đường cong.
			var r := int(v * rows)
			var lv := v * rows - r
			var shift := 0.5 if r % 2 == 1 else 0.0
			var cu := fposmod(u * cols + shift, float(cols))
			var lu := cu - int(cu)
			var curve := 0.82 + 0.18 * sqrt(maxf(0.0, 1.0 - pow((lu - 0.5) * 2.0, 2.0)))
			var below := lv > curve
			var hv := hash1(int(cu) + 13 * r, 2)
			var shade := 1.0 - 0.45 * ss(0.0, 1.0, lv) if not below else 0.45
			var c := Vector3(0.5, 0.22, 0.13).lerp(Vector3(0.36, 0.17, 0.11), hv) * shade
			var side := 1.0 - ss(0.0, 0.06, minf(lu, 1.0 - lu))
			c *= 1.0 - side * 0.6
			c *= 0.85 + 0.25 * fine[i]
			c = c.lerp(Vector3(0.07, 0.08, 0.05), ss(0.55, 0.8, moss[i]) * 0.8)
			var h := (1.0 - lv) * 0.7 if not below else 0.0
			t.put(i, c, h + 0.05 * fine[i], 0.8 + 0.15 * fine[i])
	save_set("roof_tile", t, 3.0)


func bake_concrete_damp() -> void:
	# Xi măng/vữa hầm ẩm: xám, rỗ, mảng thấm nước sẫm.
	var s := 512
	var t := TexSet.new(s)
	var a := noise(131, 3, s, 6)
	var b := noise(132, 50, s, 3)
	var pores := noise(133, 140, s, 1)
	for i in s * s:
		var damp := ss(0.45, 0.75, a[i])
		var pore := ss(0.78, 0.86, pores[i])
		var c := Vector3(0.5, 0.49, 0.45) * (0.85 + 0.25 * b[i])
		c = c.lerp(Vector3(0.22, 0.22, 0.2), damp * 0.7).lerp(Vector3(0.1, 0.1, 0.1), pore * 0.6)
		t.put(i, c, 0.6 + 0.2 * b[i] - 0.4 * pore, 0.9 - 0.35 * damp)
	save_set("concrete_damp", t, 2.0)


func bake_earth() -> void:
	# Đất nện/đất sân: nâu, sỏi nhỏ.
	var s := 512
	var t := TexSet.new(s)
	var a := noise(141, 4, s, 6)
	var b := noise(142, 60, s, 3)
	var peb := cells(143, 40, s, 1.0)
	for i in s * s:
		var p := ss(0.25, 0.1, peb[i])
		var c := Vector3(0.33, 0.26, 0.19) * (0.75 + 0.4 * a[i]) * (0.9 + 0.2 * b[i])
		c = c.lerp(Vector3(0.45, 0.42, 0.38) * (0.8 + 0.3 * b[i]), p * 0.6)
		t.put(i, c, 0.4 * a[i] + 0.3 * b[i] + 0.5 * p, 0.92)
	save_set("earth", t, 2.5)


func bake_grass() -> void:
	var s := 512
	var t := TexSet.new(s)
	var a := noise(151, 5, s, 6)
	var b := noise(152, 160, s, 2)
	for i in s * s:
		var c := Vector3(0.22, 0.38, 0.14).lerp(Vector3(0.38, 0.45, 0.2), a[i]) * (0.7 + 0.5 * b[i])
		t.put(i, c, b[i], 0.9)
	save_set("grass", t, 2.0)


# ---------------------------------------------------------------------------
# Vải, chiếu, kim loại
# ---------------------------------------------------------------------------

func bake_fabric() -> void:
	# Vải dệt trơn màu trắng xám, nhân màu bằng albedo_color trong material.
	var s := 512
	var t := TexSet.new(s)
	var slub := Aniso.new(161, 6.0, 120.0, 2)
	var stain := noise(162, 3, s, 5)
	var th := 96.0
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var wu := sin(u * th * TAU) * 0.5 + 0.5
			var wv := sin(v * th * TAU) * 0.5 + 0.5
			var over := (int(u * th) + int(v * th)) % 2 == 0
			var w := wu if over else wv
			var sl := slub.at(u, v) * 0.5 + 0.5
			var k := 0.86 + 0.1 * w + 0.06 * sl - 0.05 * ss(0.6, 0.9, stain[i])
			t.put(i, Vector3(k, k, k * 0.98), w * 0.6 + sl * 0.2, 0.95)
	save_set("fabric", t, 0.8)


func bake_reed_mat() -> void:
	# Chiếu cói: sợi cói ngang, sợi gai dọc, vài sọc đỏ nhuộm.
	var s := 512
	var t := TexSet.new(s)
	var fib := Aniso.new(171, 10.0, 160.0, 2)
	var age := noise(172, 3, s, 5)
	var strands := 128.0
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var lv := fposmod(v * strands, 1.0)
			var rnd := sin(lv * PI)
			var warp := fposmod(u * 16.0, 1.0)
			var warp_line := 1.0 - ss(0.0, 0.08, absf(warp - 0.5))
			var c := Vector3(0.78, 0.68, 0.42) * (0.7 + 0.3 * rnd) * (0.85 + 0.2 * (fib.at(u, v) * 0.5 + 0.5))
			var band := fposmod(v * 4.0, 1.0)
			if band > 0.08 and band < 0.13:
				c = Vector3(0.55, 0.12, 0.1) * (0.7 + 0.3 * rnd)
			c = c.lerp(c * 0.6, ss(0.5, 0.9, age[i]) * 0.6)
			c = c.lerp(Vector3(0.3, 0.25, 0.15), warp_line * 0.5)
			t.put(i, c, rnd * 0.7 - warp_line * 0.2, 0.8)
	save_set("reed_mat", t, 1.5)


func bake_rust_metal() -> void:
	# Sắt sơn đen gỉ (song cửa, hòm sắt, bếp dầu).
	var s := 512
	var t := TexSet.new(s)
	var a := noise(181, 6, s, 6)
	var b := noise(182, 70, s, 3)
	for i in s * s:
		var r := ss(0.6, 0.8, a[i])
		var c := Vector3(0.11, 0.11, 0.11).lerp(Vector3(0.38, 0.17, 0.07) * (0.7 + 0.5 * b[i]), r)
		t.put(i, c, 0.5 + 0.3 * r * b[i], 0.5 + 0.45 * r)
	save_set("rust_metal", t, 1.5)


func bake_rug_dream() -> void:
	# Thảm len màu kem có viền, phủ cả tấm (UV 0..1, không lặp).
	var s := 512
	var t := TexSet.new(s)
	var b := noise(191, 200, s, 1)
	for y in s:
		var v := (y + 0.5) / s
		for x in s:
			var u := (x + 0.5) / s
			var i := y * s + x
			var d := minf(minf(u, 1.0 - u), minf(v, 1.0 - v))
			var c := Vector3(0.84, 0.79, 0.7)
			if d > 0.06 and d < 0.08:
				c = Vector3(0.55, 0.6, 0.62)
			elif d > 0.1 and d < 0.105:
				c = Vector3(0.66, 0.6, 0.52)
			c *= 0.9 + 0.15 * b[i]
			t.put(i, c, b[i], 1.0)
	save_set("rug_dream", t, 1.0)


# ---------------------------------------------------------------------------
# Decal, tranh ảnh (RGBA)
# ---------------------------------------------------------------------------

func bake_decals() -> void:
	var s := 512
	var nz := noise(201, 6, s, 6)
	var nz2 := noise(202, 30, s, 3)
	var cr := cells(203, 5, s, 0.9)
	var idx := func(u: float, v: float) -> int:
		return clampi(int(v * s), 0, s - 1) * s + clampi(int(u * s), 0, s - 1)

	# Vết ố nước loang (dùng ở chân tường, trần).
	save_rgba(DECAL + "stain_damp.png", s, func(u: float, v: float) -> Color:
		var d := Vector2(u - 0.5, v - 0.5).length() * 2.0
		var n: float = nz[idx.call(u, v)]
		var m := ss(1.0, 0.55, d + (n - 0.5) * 0.8)
		var edge := ss(0.0, 0.15, m) * (1.0 - ss(0.15, 0.4, m))
		var c := Color(0.36, 0.27, 0.16).lerp(Color(0.25, 0.17, 0.08), edge)
		return Color(c.r, c.g, c.b, m * 0.55 + edge * 0.35))

	# Mốc đen loang từ dưới lên (đặt sát chân tường, mép dưới của ảnh = chân tường).
	save_rgba(DECAL + "mold.png", s, func(u: float, v: float) -> Color:
		var n: float = nz[idx.call(u, v)]
		var f: float = nz2[idx.call(u, v)]
		var side := ss(0.0, 0.2, u) * ss(1.0, 0.8, u)
		var m := ss(0.15, 1.0, v + (n - 0.5) * 0.9) * side
		var spots := ss(0.45, 0.6, f) * m
		var a := clampf(m * 0.55 + spots * 0.4, 0.0, 0.92)
		return Color(0.08, 0.09, 0.06, a))

	# Vết nứt tường.
	save_rgba(DECAL + "crack.png", s, func(u: float, v: float) -> Color:
		var c: float = cr[idx.call(u, v)]
		var d := Vector2(u - 0.5, v - 0.5).length() * 2.0
		var line := (1.0 - ss(0.0, 0.03, c)) * ss(1.0, 0.6, d)
		return Color(0.08, 0.06, 0.05, line * 0.95))

	# Muội khói bếp: đen đậm ở trên, loang xuống.
	save_rgba(DECAL + "soot.png", s, func(u: float, v: float) -> Color:
		var n: float = nz[idx.call(u, v)]
		var side := ss(0.0, 0.35, u) * ss(1.0, 0.65, u)
		var a := ss(1.0, 0.1, v + (n - 0.5) * 0.5) * side
		return Color(0.04, 0.035, 0.03, a * 0.92))

	# Dấu bàn tay (dính bẩn/máu khô) bị kéo trượt xuống.
	save_rgba(DECAL + "handprint.png", s, func(u: float, v: float) -> Color:
		var p := Vector2(u, v)
		var palm := Vector2((u - 0.5) / 0.2, (v - 0.62) / 0.17).length()
		var m := ss(1.1, 0.9, palm)
		var tips := [Vector2(0.33, 0.48), Vector2(0.41, 0.25), Vector2(0.5, 0.2), Vector2(0.59, 0.24), Vector2(0.67, 0.33)]
		var bases := [Vector2(0.38, 0.6), Vector2(0.44, 0.5), Vector2(0.5, 0.48), Vector2(0.56, 0.5), Vector2(0.62, 0.55)]
		for k in 5:
			var pa: Vector2 = bases[k]
			var pb: Vector2 = tips[k]
			var ab := pb - pa
			var h := clampf((p - pa).dot(ab) / ab.dot(ab), 0.0, 1.0)
			var dist := (p - pa - ab * h).length()
			m = maxf(m, ss(0.045, 0.03, dist))
		# Vệt kéo xuống dưới.
		var drag := ss(0.2, 0.15, absf(u - 0.5)) * ss(0.7, 1.0, v) * ss(1.0, 0.75, v) * 0.5
		var n: float = nz2[idx.call(u, v)]
		var a := clampf(maxf(m, drag) * (0.55 + 0.45 * n), 0.0, 1.0)
		return Color(0.22, 0.07, 0.05, a * 0.85))

	# Vết cào móng tay: 4 vạch song song.
	save_rgba(DECAL + "scratches.png", s, func(u: float, v: float) -> Color:
		var a := 0.0
		for k in 4:
			var x0 := 0.32 + k * 0.11 + (v - 0.5) * 0.12
			var line := ss(0.012, 0.0, absf(u - x0 - sin(v * 9.0 + k) * 0.01))
			a = maxf(a, line * ss(0.1, 0.2 + k * 0.02, v) * ss(0.95 - k * 0.04, 0.8, v))
		var n: float = nz2[idx.call(u, v)]
		return Color(0.1, 0.07, 0.06, a * (0.6 + 0.4 * n)))

	# Mạng nhện góc phòng: đặt ở góc, tâm mạng là góc trên trái của ảnh.
	save_rgba(DECAL + "cobweb.png", s, func(u: float, v: float) -> Color:
		var p := Vector2(u, v)
		var r := p.length()
		var ang := atan2(v, u)
		var spokes := 0.0
		for k in 9:
			var sa := (k + 0.5) / 9.0 * PI * 0.5
			var d := absf(sin(ang - sa)) * r
			spokes = maxf(spokes, ss(0.006, 0.0, d))
		var ring_f := fposmod(r * 14.0 + sin(ang * 9.0) * 0.15, 1.0)
		var rings := ss(0.05, 0.0, absf(ring_f - 0.5) - 0.44)
		var a := maxf(spokes, rings * 0.8) * ss(1.0, 0.75, r)
		a = maxf(a, ss(0.25, 0.0, r) * 0.25)
		return Color(0.85, 0.85, 0.82, a * 0.75))

	# Dấu chân ướt trẻ con (phòng trong mơ, rất mờ).
	save_rgba(DECAL + "footprint.png", s, func(u: float, v: float) -> Color:
		var sole := Vector2((u - 0.5) / 0.16, (v - 0.6) / 0.3).length()
		var heel_cut := ss(0.0, 0.05, absf(v - 0.62) - 0.02)
		var m := ss(1.0, 0.85, sole) * (0.6 + 0.4 * heel_cut)
		for k in 5:
			var c := Vector2(0.38 + k * 0.06, 0.24 - (0.04 - absf(k - 1.0) * 0.012))
			m = maxf(m, ss(0.035, 0.02, Vector2(u, v).distance_to(c)))
		var n: float = nz2[idx.call(u, v)]
		return Color(0.2, 0.17, 0.13, m * (0.5 + 0.3 * n)))

	# Vàng mã (giấy tiền) vương vãi: giấy vàng, ô vuông in đỏ.
	save_rgba(DECAL + "joss_paper.png", 256, func(u: float, v: float) -> Color:
		var d := minf(minf(u, 1.0 - u), minf(v, 1.0 - v))
		var c := Color(0.86, 0.66, 0.22)
		if d > 0.18 and d < 0.22:
			c = Color(0.6, 0.12, 0.08)
		var inner := Vector2(u - 0.5, v - 0.5).length()
		if inner < 0.12:
			c = Color(0.75, 0.55, 0.18)
		return c)

	# Lá bùa: giấy vàng dài, nét chữ đỏ ngoằn ngoèo (chỉ là nét, không phải chữ thật).
	save_rgba(DECAL + "talisman.png", 256, func(u: float, v: float) -> Color:
		var c := Color(0.85, 0.7, 0.3)
		var n: float = nz[idx.call(u, v)]
		c = c.lerp(Color(0.6, 0.45, 0.2), ss(0.5, 0.9, n) * 0.6)
		var stroke := absf(sin(v * 40.0 + sin(v * 7.0) * 3.0) * 0.12 + 0.5 - u)
		var sym := ss(0.03, 0.015, stroke) * ss(0.12, 0.15, v) * ss(0.9, 0.85, v)
		var ring := ss(0.02, 0.0, absf(Vector2(u - 0.5, (v - 0.22) * 0.5).length() - 0.15))
		c = c.lerp(Color(0.62, 0.05, 0.04), clampf(sym + ring, 0, 1))
		return c)

	# Ảnh thờ: chân dung đen trắng ngả vàng, mặt nhòe, mắt chỉ là hai hốc tối.
	save_rgba(DECAL + "portrait.png", 256, func(u: float, v: float) -> Color:
		var n: float = nz2[idx.call(u, v)]
		var k := 0.5 + 0.12 * (1.0 - v)
		var face := ss(1.0, 0.8, Vector2((u - 0.5) / 0.15, (v - 0.4) / 0.2).length())
		var hair := ss(1.0, 0.85, Vector2((u - 0.5) / 0.18, (v - 0.36) / 0.22).length())
		var body := ss(0.02, -0.02, absf(u - 0.5) - (0.1 + maxf(0.0, v - 0.6) * 1.1)) * ss(0.56, 0.62, v)
		k = lerpf(k, 0.16, maxf(hair, body))
		face *= ss(0.24, 0.3, v)
		k = lerpf(k, 0.72, face)
		var eyes := 0.0
		for ex in [0.45, 0.55]:
			eyes = maxf(eyes, ss(0.028, 0.012, Vector2(u - ex, (v - 0.4) * 1.3).length()))
		k = lerpf(k, 0.08, eyes * face)
		k = lerpf(k, 0.45, ss(0.02, 0.0, absf(v - 0.5) - 0.0) * ss(0.03, 0.0, absf(u - 0.5)) * face * 0.5)
		k += (n - 0.5) * 0.14
		var c := Color(k, k * 0.9, k * 0.7)
		if minf(minf(u, 1.0 - u), minf(v, 1.0 - v)) < 0.05:
			c = Color(0.85, 0.8, 0.68)
		return c)

	# Ảnh gia đình: 4 người đứng, người thứ ba bị cào mất mặt.
	save_rgba(DECAL + "family_photo.png", 256, func(u: float, v: float) -> Color:
		var n: float = nz2[idx.call(u, v)]
		var k := 0.6 - 0.15 * v + (n - 0.5) * 0.1
		var xs := [0.22, 0.4, 0.6, 0.78]
		var hs := [0.32, 0.28, 0.45, 0.3]
		for j in 4:
			var cx: float = xs[j]
			var top: float = hs[j]
			var head := ss(0.06, 0.05, Vector2(u - cx, (v - top) * 0.9).length())
			var body := ss(0.01, 0.0, absf(u - cx) - (0.07 + (v - top - 0.06) * 0.2)) * ss(top + 0.05, top + 0.08, v)
			var tone := 0.25 if j != 1 else 0.3
			k = lerpf(k, tone, maxf(body, head * 0.0))
			k = lerpf(k, 0.7, head)
			if j == 2:
				# Mặt bị cào xước trắng.
				var sc := ss(0.08, 0.06, Vector2(u - cx, v - top).length()) * (0.5 + 0.5 * sin(u * 300.0 + v * 120.0))
				k = lerpf(k, 0.95, sc)
		var frame := minf(minf(u, 1.0 - u), minf(v, 1.0 - v)) < 0.04
		var c := Color(k, k * 0.92, k * 0.75)
		if frame:
			c = Color(0.9, 0.88, 0.8)
		return c)

	# Lịch bloc treo tường: tờ ngày to, số "15" đỏ (rằm), nét chữ giả.
	save_rgba(DECAL + "calendar.png", 256, func(u: float, v: float) -> Color:
		var c := Color(0.9, 0.86, 0.76)
		if v < 0.18:
			c = Color(0.62, 0.1, 0.08)
		# Số 1 và 5 vẽ bằng nét.
		var one := ss(0.03, 0.02, absf(u - 0.38)) * ss(0.3, 0.32, v) * ss(0.72, 0.7, v)
		var five := 0.0
		if v > 0.3 and v < 0.72:
			five = maxf(five, ss(0.03, 0.02, absf(v - 0.32)) * ss(0.5, 0.52, u) * ss(0.72, 0.7, u))
			five = maxf(five, ss(0.03, 0.02, absf(u - 0.52)) * ss(0.3, 0.32, v) * ss(0.5, 0.48, v))
			var arc := absf(Vector2((u - 0.58) / 0.12, (v - 0.6) / 0.1).length() - 1.0)
			five = maxf(five, ss(0.25, 0.15, arc) * ss(0.5, 0.53, u))
		c = c.lerp(Color(0.7, 0.08, 0.06), clampf(one + five, 0, 1))
		var lines := ss(0.3, 0.4, fposmod(v * 30.0, 1.0)) * ss(0.6, 0.5, fposmod(v * 30.0, 1.0))
		if v > 0.8 and u > 0.15 and u < 0.85:
			c = c.lerp(Color(0.3, 0.28, 0.25), lines * 0.6)
		return c)

	# Mặt đồng hồ: kim chỉ 12 giờ (dùng cho cả giờ Tý ở nhà cũ và giờ Ngọ trong mơ).
	save_rgba(DECAL + "clock_face.png", 256, func(u: float, v: float) -> Color:
		var p := Vector2(u - 0.5, v - 0.5)
		var r := p.length()
		if r > 0.5:
			return Color(0, 0, 0, 0)
		var c := Color(0.92, 0.9, 0.84)
		if r > 0.46:
			c = Color(0.2, 0.18, 0.16)
		var ang := atan2(p.x, -p.y)
		var tick := fposmod(ang / TAU * 12.0 + 0.5, 1.0)
		if r > 0.38 and r < 0.44 and absf(tick - 0.5) < 0.06:
			c = Color(0.1, 0.1, 0.1)
		# Hai kim cùng chỉ lên số 12.
		if absf(p.x) < 0.012 and p.y < 0.02 and p.y > -0.38:
			c = Color(0.05, 0.05, 0.05)
		if absf(p.x) < 0.02 and p.y < 0.02 and p.y > -0.26:
			c = Color(0.05, 0.05, 0.05)
		return c)

	# Tranh treo phòng mơ: phong cảnh trừu tượng sông nước, nắng nhạt.
	save_rgba(DECAL + "painting.png", 512, func(u: float, v: float) -> Color:
		var n: float = nz[idx.call(u, v)]
		var hill := 0.55 + 0.08 * sin(u * 6.0) + 0.04 * sin(u * 17.0 + 1.0)
		var c := Color(0.78, 0.86, 0.9).lerp(Color(0.95, 0.88, 0.75), v)
		if v > hill:
			c = Color(0.5, 0.62, 0.55).lerp(Color(0.35, 0.48, 0.45), (v - hill) * 3.0)
		if v > 0.78:
			c = Color(0.6, 0.72, 0.78).lerp(Color(0.45, 0.58, 0.66), n)
		# Một bóng người nhỏ đứng bên sông (chi tiết lạnh gáy, rất nhỏ).
		if absf(u - 0.71) < 0.006 and v > 0.7 and v < 0.77:
			c = Color(0.12, 0.12, 0.14)
		if Vector2(u - 0.71, v - 0.695).length() < 0.008:
			c = Color(0.12, 0.12, 0.14)
		c = c.lerp(c * (0.9 + 0.2 * n), 0.5)
		return c)

	# Tranh vẽ sáp màu của trẻ con: nhà, mặt trời, ba người nắm tay, người thứ tư tô đen.
	save_rgba(DECAL + "child_drawing.png", 256, func(u: float, v: float) -> Color:
		var c := Color(0.97, 0.96, 0.92)
		var sun := absf(Vector2(u - 0.82, v - 0.18).length() - 0.08)
		if sun < 0.012:
			c = Color(0.95, 0.7, 0.1)
		var ground := absf(v - 0.85 - sin(u * 12.0) * 0.01)
		if ground < 0.01:
			c = Color(0.3, 0.6, 0.2)
		for j in 4:
			var cx := 0.18 + j * 0.2
			var head := absf(Vector2(u - cx, v - 0.5).length() - 0.045)
			var body := absf(u - cx) < 0.006 and v > 0.545 and v < 0.7
			var col := Color(0.2, 0.3, 0.8) if j < 3 else Color(0.05, 0.05, 0.05)
			if j == 3:
				if Vector2(u - cx, v - 0.5).length() < 0.05 or (absf(u - cx) < 0.03 and v > 0.54 and v < 0.75):
					c = col
			elif head < 0.008 or body:
				c = col
		return c)
