// Một tờ giấy cũ trên giao diện: màu giấy, thớ xơ, ố vàng từ mép, đốm ố, vết nước loang
// có viền khô, nếp gấp, nhàu, mép rách / răng cưa cuống vé, bóng đổ, và lớp mực
// (SubViewport trong suốt) thấm vào giấy: bám không đều theo thớ, nhòe trong vết nước.
// Dùng cho ColorRect có kích thước = paper_size + 2 * margin (xem PaperSheet.gd).
shader_type canvas_item;

uniform sampler2D ink_tex : filter_linear;
uniform sampler2D fiber_tex : filter_linear_mipmap, repeat_enable;
uniform sampler2D stain_tex : filter_linear_mipmap, repeat_enable;

uniform vec2 paper_size = vec2(560.0, 720.0);
uniform float margin = 48.0;
uniform vec4 paper_color : source_color = vec4(0.88, 0.83, 0.70, 1.0);
uniform vec4 age_color : source_color = vec4(0.60, 0.45, 0.25, 1.0);
// Ố vàng từ mép vào (0..1) và bề rộng dải ố (px).
uniform float age = 0.5;
uniform float age_width = 90.0;
uniform float grain = 0.6;
uniform float foxing = 0.3;
// Diện tích vết nước (0..1); stain_bias_y > 0 thì nước ngấm từ mép dưới lên.
uniform float stain = 0.0;
uniform float stain_bias_y = 0.0;
uniform vec2 stain_shift = vec2(0.0);
// Mực trong vết nước nhòe và phai bao nhiêu.
uniform float ink_wash = 0.7;
// Mực bám không đều theo thớ giấy (bút chì, mực dấu cao hơn).
uniform float ink_grain = 0.25;
uniform float ink_opacity = 1.0;
// Mép rách: độ sâu (px) và tần số.
uniform float tear = 3.0;
uniform float tear_freq = 1.0;
uniform float corner_round = 2.0;
// Số nếp gấp dọc, ngang.
uniform vec2 folds = vec2(0.0);
uniform float fold_strength = 0.6;
uniform float crumple = 0.0;
// Răng cưa xé theo đường đục lỗ: trái, trên, phải, dưới.
uniform vec4 perforate = vec4(0.0);
// Bóng loáng (túi nilông, decal nhựa).
uniform float sheen = 0.0;
// Ánh sáng: tâm vùng sáng (UV giấy) và độ tối ở góc xa.
uniform vec2 light_pos = vec2(0.35, 0.25);
uniform float light_falloff = 0.22;
uniform float shadow_alpha = 0.6;
uniform vec2 shadow_offset = vec2(7.0, 12.0);
uniform float shadow_blur = 20.0;
// Khói hương lượn quanh tờ giấy (động).
uniform float smoke = 0.0;
uniform vec4 smoke_color : source_color = vec4(0.85, 0.82, 0.78, 1.0);
// Đốt giấy (hóa vàng): 0 nguyên vẹn -> 1 cháy hết. Lửa ăn từ mép dưới lên, viền than đỏ rực.
uniform float burn = 0.0;

float sd_box(vec2 p, vec2 half_size) {
	vec2 d = abs(p) - half_size;
	return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}

vec4 ink_at(vec2 uv) {
	return texture(ink_tex, uv);
}

void fragment() {
	vec2 total = paper_size + vec2(margin * 2.0);
	vec2 px = UV * total - vec2(margin);
	vec2 puv = px / paper_size;
	vec2 tuv = px / 1024.0 + stain_shift;
	vec2 center = paper_size * 0.5;

	// --- Hình dạng tờ giấy -------------------------------------------------------
	float n_low = texture(stain_tex, px * 0.0045 * tear_freq + stain_shift * 3.0).a;
	float n_fine = texture(fiber_tex, px * 0.012 * tear_freq + stain_shift).r;
	float rough = tear * (0.35 + (n_low - 0.5) * 1.5 + (n_fine - 0.5) * 1.2);
	float d = sd_box(px - center, center - vec2(corner_round)) - corner_round;
	d += max(rough, 0.0);
	// Răng cưa đường đục lỗ: các vết khuyết tròn cách đều 7px.
	float bite_y = 0.5 + 0.5 * cos(px.y * 6.2832 / 7.0);
	float bite_x = 0.5 + 0.5 * cos(px.x * 6.2832 / 7.0);
	d += perforate.x * 2.6 * bite_y * (1.0 - smoothstep(0.0, 8.0, px.x));
	d += perforate.z * 2.6 * bite_y * (1.0 - smoothstep(0.0, 8.0, paper_size.x - px.x));
	d += perforate.y * 2.6 * bite_x * (1.0 - smoothstep(0.0, 8.0, px.y));
	d += perforate.w * 2.6 * bite_x * (1.0 - smoothstep(0.0, 8.0, paper_size.y - px.y));
	float paper_a = clamp(0.5 - d, 0.0, 1.0);

	// Bóng đổ của tờ giấy xuống mặt dưới.
	float ds = sd_box(px - center - shadow_offset, center) ;
	float shadow = shadow_alpha * (1.0 - smoothstep(-shadow_blur * 0.4, shadow_blur, ds));

	// --- Màu giấy ------------------------------------------------------------------
	float fib = texture(fiber_tex, tuv).r;
	vec3 col = paper_color.rgb * (1.0 + (fib - 0.5) * grain * 0.55);
	float inside = -sd_box(px - center, center);
	float edge_age = 1.0 - smoothstep(0.0, age_width, inside + (n_low - 0.5) * age_width * 0.6);
	edge_age *= edge_age;
	col = mix(col, col * age_color.rgb * 1.35, clamp(edge_age * age * 0.5, 0.0, 1.0));
	col *= 1.0 - (n_low - 0.5) * 0.14 * age;
	float fox = texture(stain_tex, tuv * 1.3 + vec2(0.37, 0.11)).b;
	col = mix(col, age_color.rgb * 0.75, fox * foxing * 0.6);

	// Vết nước: lấy ngưỡng trường ố; viền ngưỡng là vệt nước khô đậm màu.
	float field = texture(stain_tex, tuv * 0.75).r + stain_bias_y * (puv.y - 0.55) * 0.9;
	float thr = 1.0 - stain;
	float wet = smoothstep(thr, thr + 0.05, field) * step(0.001, stain);
	float ring = smoothstep(thr - 0.03, thr, field) * (1.0 - smoothstep(thr, thr + 0.025, field));
	ring *= (0.35 + texture(stain_tex, tuv * 2.0).g * 0.6) * step(0.001, stain);
	col = mix(col, col * vec3(0.90, 0.84, 0.72), wet * 0.5);
	col = mix(col, col * age_color.rgb * 1.1, clamp(ring, 0.0, 1.0) * 0.45);

	// Nếp gấp: mỗi nếp là một rãnh tối mảnh, hai bên sáng tối lệch nhau; các ô gấp nghiêng khác nhau.
	float fold_shade = 0.0;
	for (int i = 1; i <= 3; i++) {
		if (float(i) <= folds.x) {
			float fx = (puv.x - float(i) / (folds.x + 1.0)) * paper_size.x;
			fold_shade += -sign(fx) * exp(-abs(fx) / 16.0) * 0.07 - exp(-abs(fx) / 1.4) * 0.16;
		}
		if (float(i) <= folds.y) {
			float fy = (puv.y - float(i) / (folds.y + 1.0)) * paper_size.y;
			fold_shade += -sign(fy) * exp(-abs(fy) / 16.0) * 0.07 - exp(-abs(fy) / 1.4) * 0.16;
		}
	}
	float panel = mod(floor(puv.x * (folds.x + 1.0)) + floor(puv.y * (folds.y + 1.0)), 2.0);
	fold_shade += (panel - 0.5) * 0.05 * step(0.5, folds.x + folds.y);
	col *= 1.0 + fold_shade * fold_strength;

	// Nhàu: coi nhiễu thấp như độ cao, chiếu sáng theo hướng đèn.
	if (crumple > 0.0) {
		// Lấy mức mipmap thô để chỉ còn các nếp nhàu lớn, không lấm tấm như đá.
		vec2 cuv = px * 0.0016 + stain_shift * 1.7;
		vec2 e = vec2(0.03, 0.0);
		float h0 = textureLod(stain_tex, cuv, 5.0).r + textureLod(stain_tex, cuv * 2.3, 4.0).r * 0.35;
		float hx = textureLod(stain_tex, cuv + e.xy, 5.0).r + textureLod(stain_tex, (cuv + e.xy) * 2.3, 4.0).r * 0.35;
		float hy = textureLod(stain_tex, cuv + e.yx, 5.0).r + textureLod(stain_tex, (cuv + e.yx) * 2.3, 4.0).r * 0.35;
		col *= 1.0 + ((h0 - hx) * 1.0 + (h0 - hy) * 0.7) * crumple * 3.0;
	}

	// --- Mực ---------------------------------------------------------------------
	vec2 texel = 1.0 / paper_size;
	vec4 ink = ink_at(puv);
	vec4 soft = (ink_at(puv + vec2(texel.x, 0.0)) + ink_at(puv - vec2(texel.x, 0.0))
			+ ink_at(puv + vec2(0.0, texel.y)) + ink_at(puv - vec2(0.0, texel.y))) * 0.25;
	vec4 wide = vec4(0.0);
	for (int k = 0; k < 8; k++) {
		float a = float(k) * 0.785 + n_fine * 2.0;
		wide += ink_at(puv + vec2(cos(a), sin(a) + 0.6) * texel * 4.5);
	}
	wide /= 8.0;
	float wash = wet * ink_wash;
	// Mực ngấm nhẹ vào giấy (viền mềm), trong vết nước thì loang và trôi xuống.
	vec4 inkc = mix(mix(ink, soft, 0.35), wide, wash * 0.8);
	float bite = mix(1.0, smoothstep(0.30, 0.62, fib + (n_low - 0.5) * 0.2), ink_grain);
	inkc *= ink_opacity * bite * (1.0 - wash * 0.6);
	col = inkc.rgb + col * (1.0 - inkc.a);

	// Bóng loáng nhựa: dải sáng chéo.
	float band = 1.0 - smoothstep(0.0, 0.16, abs(puv.x * 0.8 + puv.y * 0.45 - 0.62));
	col += sheen * (band * 0.22 + 0.04);

	// Ánh sáng đèn: sáng ở light_pos, tối dần ra góc.
	float lit = 1.0 - light_falloff * smoothstep(0.0, 1.0, length((puv - light_pos) * vec2(1.0, 0.8)));
	col *= lit;

	// Đốt: phần đã cháy trong suốt, sát đó là than đen rồi viền lửa.
	if (burn > 0.0) {
		float front = n_low * 0.45 + n_fine * 0.15 + (1.0 - puv.y) * 0.55;
		float b = burn * 1.25 - 0.1;
		float intact = smoothstep(b - 0.01, b + 0.01, front);
		float ember = 1.0 - smoothstep(0.0, 0.05, front - b);
		float char_band = 1.0 - smoothstep(0.0, 0.12, front - b);
		col = mix(col, vec3(0.08, 0.05, 0.03), char_band * 0.85);
		col += vec3(1.0, 0.45, 0.1) * ember * intact * 1.4;
		paper_a *= intact;
		shadow *= 1.0 - burn;
	}

	// --- Ghép giấy + bóng --------------------------------------------------------
	float out_a = paper_a + shadow * (1.0 - paper_a);
	vec3 out_rgb = col * paper_a / max(out_a, 0.0001);

	// Khói hương: hai lớp nhiễu trôi ngược chiều, dày ở mép giấy, lan ra ngoài.
	if (smoke > 0.0) {
		vec2 suv = px * 0.0022;
		float s1 = texture(stain_tex, suv + vec2(0.0, -TIME * 0.018)).a;
		float s2 = texture(stain_tex, suv * 1.7 + vec2(TIME * 0.011, -TIME * 0.03)).r;
		float wisps = smoothstep(0.45, 0.95, s1 * 0.6 + s2 * 0.6);
		float near_edge = 1.0 - smoothstep(-30.0, 70.0, inside);
		float sa = wisps * smoke * mix(0.15, 0.75, near_edge) * (1.0 - smoothstep(0.0, margin, -inside));
		out_rgb = mix(out_rgb, smoke_color.rgb, sa / max(out_a + sa, 0.0001));
		out_a = out_a + sa * (1.0 - out_a);
	}
	COLOR = vec4(out_rgb, out_a);
}
