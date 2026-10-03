## Vật thể người chơi có thể tương tác (đồ vật thường hoặc Memory Trigger).
##
## Cách dùng: thêm node Area3D có script này vào vật thể, gắn CollisionShape3D
## làm con. PlayerInteractor của nhân vật sẽ tự phát hiện nó.
##
## Khi được tương tác, node phát [signal interacted] và
## [signal EventBus.interaction_requested] để các hệ thống khác (MemoryManager,
## inventory...) xử lý.
class_name Interactable
extends Area3D

## Physics layer dành riêng cho vật tương tác (đặt tên trong Project Settings
## > Layer Names > 3D Physics). PlayerInteractor quét đúng layer này.
const INTERACTABLE_LAYER := 3

enum InteractionType {
	ITEM,           ## Đồ vật thường: nhặt, xem xét...
	MEMORY_TRIGGER, ## Vật kích hoạt ký ức: mở khóa memory và monologue nội tâm.
}

## Phát ra sau khi người chơi tương tác thành công.
signal interacted(actor: Node)

## ID duy nhất của vật. Với MEMORY_TRIGGER, đây cũng là ID ký ức được mở khóa.
@export var item_id: StringName
## Key dịch cho lời nhắc, ví dụ "PROMPT_EXAMINE". Hiển thị qua [method get_prompt_text].
@export var prompt_text_key: String = "PROMPT_INTERACT"
@export var interaction_type: InteractionType = InteractionType.ITEM
## Key dịch cho monologue nội tâm khi kích hoạt ký ức (chỉ dùng cho MEMORY_TRIGGER).
@export var monologue_key: String
## Tắt tương tác sau lần dùng đầu tiên.
@export var one_shot: bool = false
## Có thể tương tác hay không. Tắt thì PlayerInteractor bỏ qua vật này.
@export var enabled: bool = true


func _ready() -> void:
	# Vật tương tác chỉ cần được phát hiện, không cần tự quét ai.
	monitoring = false
	monitorable = true
	collision_layer = 0
	collision_mask = 0
	set_collision_layer_value(INTERACTABLE_LAYER, true)


func is_memory_trigger() -> bool:
	return interaction_type == InteractionType.MEMORY_TRIGGER


## Lời nhắc đã dịch theo ngôn ngữ hiện tại.
func get_prompt_text() -> String:
	return tr(prompt_text_key)


## Gọi bởi PlayerInteractor. Trả về false nếu vật đang bị tắt.
func interact(actor: Node) -> bool:
	if not enabled:
		return false
	interacted.emit(actor)
	EventBus.interaction_requested.emit(self, actor)
	if one_shot:
		enabled = false
	return true
