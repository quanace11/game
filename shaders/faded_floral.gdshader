// Vải hoa cũ bạc màu cho áo của bé gái: hoa năm cánh lặp lại, lệch hàng.
shader_type spatial;
render_mode diffuse_lambert_wrap;

uniform vec3 base_color : source_color = vec3(0.58, 0.54, 0.46);
uniform vec3 flower_color : source_color = vec3(0.52, 0.27, 0.27);
uniform vec3 core_color : source_color = vec3(0.72, 0.64, 0.42);
uniform vec2 scale = vec2(10.0, 7.0);
uniform float fade : hint_range(0.0, 1.0) = 0.35;

void fragment() {
	vec2 uv = UV * scale;
	uv.x += step(1.0, mod(floor(uv.y), 2.0)) * 0.5;
	vec2 cell = fract(uv) - 0.5;
	float r = length(cell);
	float a = atan(cell.y, cell.x);
	float petal = 0.2 + 0.09 * cos(a * 5.0);
	float flower = 1.0 - smoothstep(petal - 0.03, petal, r);
	float core = 1.0 - smoothstep(0.04, 0.07, r);
	vec3 col = mix(base_color, flower_color, flower);
	col = mix(col, core_color, core);
	ALBEDO = mix(col, base_color, fade);
	ROUGHNESS = 0.95;
}
