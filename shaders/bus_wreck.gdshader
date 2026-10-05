// Vật liệu xác xe khách nằm bãi sông (chương 2): phủ lên texture gốc (sơn, giả da, sàn gỗ...)
// - gỉ sét loang theo nhiễu,
// - vệt nước ngập: dưới mép nước bạc màu + phủ phù sa, đúng mép nước là một vạch bùn đậm,
//   bên dưới có vệt chảy dọc,
// - rêu mọc ở mặt hướng lên và sát sàn,
// - mốc đen lấm tấm ở phần trên mép nước.
// Mọi lớp phủ tính theo tọa độ thế giới (chiếu ba mặt) nên ráp liền giữa các mesh.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D base_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D base_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D base_orm : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
// UV của mesh tính bằng mét: uv_scale = 1 / kích thước thật của texture.
uniform float uv_scale = 1.0;
// true: bỏ UV, chiếu ba mặt theo tọa độ thế giới (cho mesh nguyên khối BoxMesh...).
uniform bool world_uv = false;
uniform float metallic_amount = 0.0;
uniform float roughness_offset = 0.0;
uniform float normal_depth = 1.0;

uniform sampler2D noise_tex : hint_default_white, filter_linear_mipmap, repeat_enable;

uniform sampler2D rust_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rust_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float rust_scale = 0.45;
uniform float rust_amount : hint_range(0.0, 1.0) = 0.35;

uniform sampler2D moss_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float moss_scale = 0.6;
uniform float moss_amount : hint_range(0.0, 1.0) = 0.4;

uniform float waterline_y = 1.72;
uniform vec4 silt_color : source_color = vec4(0.46, 0.41, 0.33, 1.0);
uniform vec4 tide_color : source_color = vec4(0.13, 0.1, 0.07, 1.0);
uniform float silt_amount : hint_range(0.0, 1.0) = 0.65;
uniform float mildew_amount : hint_range(0.0, 1.0) = 0.35;

varying vec3 w_pos;
varying vec3 w_nrm;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

vec3 tri_weights(vec3 n) {
	vec3 w = pow(abs(n), vec3(4.0));
	return w / max(w.x + w.y + w.z, 1e-4);
}

// Godot không cho một hàm nhận các sampler khác kiểu lọc/gợi ý, nên mỗi loại ảnh một hàm.
vec4 tri_c(sampler2D t, vec3 p, vec3 w, float s) {
	return texture(t, p.zy * s) * w.x + texture(t, p.xz * s) * w.y + texture(t, p.xy * s) * w.z;
}

vec4 tri_n(sampler2D t, vec3 p, vec3 w, float s) {
	return texture(t, p.zy * s) * w.x + texture(t, p.xz * s) * w.y + texture(t, p.xy * s) * w.z;
}

vec4 tri_orm(sampler2D t, vec3 p, vec3 w, float s) {
	return texture(t, p.zy * s) * w.x + texture(t, p.xz * s) * w.y + texture(t, p.xy * s) * w.z;
}

vec4 tri_noise(sampler2D t, vec3 p, vec3 w, float s) {
	return texture(t, p.zy * s) * w.x + texture(t, p.xz * s) * w.y + texture(t, p.xy * s) * w.z;
}

void fragment() {
	vec3 w = tri_weights(w_nrm);
	vec3 alb;
	vec3 orm;
	vec3 nmap;
	if (world_uv) {
		alb = tri_c(base_albedo, w_pos, w, uv_scale).rgb;
		orm = tri_orm(base_orm, w_pos, w, uv_scale).rgb;
		nmap = tri_n(base_normal, w_pos, w, uv_scale).rgb;
	} else {
		vec2 uv = UV * uv_scale;
		alb = texture(base_albedo, uv).rgb;
		orm = texture(base_orm, uv).rgb;
		nmap = texture(base_normal, uv).rgb;
	}
	alb *= tint.rgb;
	float ao = orm.r;
	float rough = clamp(orm.g + roughness_offset, 0.04, 1.0);
	float metal = orm.b * metallic_amount;

	vec3 nz = tri_noise(noise_tex, w_pos, w, 0.9).rgb;    // r: mảng lớn, g: chi tiết, b: vệt chảy
	vec3 nz2 = tri_noise(noise_tex, w_pos, w, 3.1).rgb;
	vec3 nz3 = tri_noise(noise_tex, w_pos, w, 9.0).rgb;

	// Mép nước ngập
	float wob = (nz2.g - 0.5) * 0.025 + (nz.r - 0.5) * 0.02;
	float edge = waterline_y + wob;
	float below = 1.0 - smoothstep(edge - 0.004, edge + 0.004, w_pos.y);
	float depth = clamp((edge - w_pos.y) / 1.6, 0.0, 1.0);
	// Vệt chảy dọc: nhiễu kênh B kéo giãn theo phương đứng (chỉ trên mặt đứng)
	float vert = 1.0 - abs(w_nrm.y);
	// lấy mẫu nhiễu kéo dài theo phương đứng để ra vệt chảy chứ không ra đốm
	float hcoord = w_pos.x * w.z + w_pos.z * w.x;
	float streak = texture(noise_tex, vec2(hcoord * 5.0, w_pos.y * 0.25)).b;
	float drip = smoothstep(0.55, 0.85, streak) * vert * (0.4 + 0.6 * smoothstep(0.0, 0.6, edge - w_pos.y) * (1.0 - depth * 0.6));

	// Phần dưới mép nước: bạc màu, phủ lớp phù sa xám nâu, loang lổ, có vệt chảy đậm hơn.
	vec3 grey = vec3(dot(alb, vec3(0.3, 0.5, 0.2)));
	vec3 faded = mix(alb, grey, 0.4) * (0.9 + 0.1 * nz2.g);
	float film = silt_amount * (0.3 + 0.35 * depth) * (0.8 + 0.4 * nz.g);
	vec3 silt = silt_color.rgb * (0.85 + 0.25 * nz2.r);
	vec3 silted = mix(faded, silt, clamp(film, 0.0, 1.0));
	silted *= 1.0 - drip * 0.22;
	alb = mix(alb, silted, below);
	// Vạch bùn đậm đúng mép nước + vạch mờ thứ hai thấp hơn (nước rút dần)
	float band = exp(-pow((w_pos.y - edge) / 0.01, 2.0)) * 0.9 + 0.45 * exp(-pow((w_pos.y - edge + 0.05) / 0.012, 2.0));
	alb = mix(alb, tide_color.rgb, clamp(band, 0.0, 1.0) * vert);
	rough = mix(rough, 0.95, below * 0.8);
	metal *= 1.0 - below * 0.7;

	// Gỉ sét: mảng lớn có rìa vụn
	float rust_n = nz.r * 0.88 + nz2.g * 0.1 + nz3.r * 0.02 + (1.0 - smoothstep(0.0, 0.9, w_pos.y)) * 0.08;
	float rmask = smoothstep(1.0 - rust_amount, 1.0 - rust_amount + 0.1, rust_n) * (0.75 + 0.25 * nz3.g);
	vec3 rust = tri_c(rust_albedo, w_pos, w, rust_scale).rgb;
	rust = mix(rust, vec3(dot(rust, vec3(0.3, 0.5, 0.2))), 0.35) * vec3(0.8, 0.68, 0.6);
	rust = mix(rust, rust * silt_color.rgb * 1.6, below * 0.5);
	alb = mix(alb, rust, rmask);
	rough = mix(rough, 0.92, rmask);
	metal = mix(metal, 0.1, rmask);
	nmap = mix(nmap, tri_n(rust_normal, w_pos, w, rust_scale).rgb, rmask * 0.8);

	// Mốc đen lấm tấm ở phần khô phía trên
	// cụm lớn mềm (nz) chứa các chấm nhỏ (nz3), không tạo vết đốm sắc cạnh
	float cluster = smoothstep(0.5, 0.9, nz.g);
	float mildew = cluster * (0.35 + 0.65 * smoothstep(0.45, 0.75, nz3.g));
	mildew *= (1.0 - below) * mildew_amount;
	alb = mix(alb, alb * vec3(0.32, 0.34, 0.26), clamp(mildew, 0.0, 0.85));

	// Rêu: chủ yếu trên mặt hướng lên và sát sàn, mặt đứng chỉ có ở chân vách
	float up = smoothstep(0.55, 0.9, w_nrm.y);
	float low = 1.0 - smoothstep(0.02, 0.35, w_pos.y);
	float moss_n = nz.g * 0.55 + nz2.r * 0.3 + nz3.g * 0.15;
	float want = max(up * (0.55 + 0.45 * below), low * 0.9) * moss_amount;
	float mmask = smoothstep(0.5, 0.6, moss_n + want * 0.15) * smoothstep(0.05, 0.35, want);
	vec3 moss = tri_c(moss_albedo, w_pos, w, moss_scale).rgb;
	// rêu sông khô bám bùn: bớt xanh tươi, ngả xám nâu
	moss = mix(moss, vec3(dot(moss, vec3(0.3, 0.5, 0.2))), 0.35) * vec3(0.72, 0.8, 0.56);
	alb = mix(alb, moss, mmask);
	rough = mix(rough, 1.0, mmask);
	ao *= 1.0 - mmask * 0.3;

	ALBEDO = alb;
	ROUGHNESS = rough;
	METALLIC = metal;
	AO = ao;
	AO_LIGHT_AFFECT = 0.3;
	NORMAL_MAP = nmap;
	NORMAL_MAP_DEPTH = normal_depth;
}
