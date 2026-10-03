// Hiệu ứng màn hình cho phân cảnh: mờ nhòe, mí mắt (nhắm/mở), vignette lạnh.
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform float blur : hint_range(0.0, 6.0) = 0.0;
uniform float eyes_open : hint_range(0.0, 1.0) = 1.0;
uniform float vignette : hint_range(0.0, 1.0) = 0.0;
uniform vec4 vignette_color : source_color = vec4(0.04, 0.08, 0.16, 1.0);

void fragment() {
	vec3 col = textureLod(screen_tex, SCREEN_UV, blur).rgb;
	vec2 c = UV - 0.5;

	float v = smoothstep(0.2, 0.75, length(c * vec2(1.0, 1.3))) * vignette;
	col = mix(col, vignette_color.rgb, clamp(v, 0.0, 1.0));

	// Mí mắt: khe mở hình hạt cau, cong ở hai bên.
	float half_open = eyes_open * 0.8;
	float lid = smoothstep(half_open - 0.08, half_open, abs(c.y) + c.x * c.x * 0.9);
	col = mix(col, vec3(0.0), lid * step(eyes_open, 0.999));

	COLOR = vec4(col, 1.0);
}
