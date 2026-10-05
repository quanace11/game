## Vật thể người chơi có thể tương tác.
##
## Cách dùng: tạo node Area3D gắn script này, cho mesh của vật và một
## CollisionShape3D làm con. Tâm ngắm (PlayerInteractor) rọi trúng vùng này
## thì hiện tên vật và lời nhắc.
##
## Hai kiểu tương tác:
## - [member can_pickup] = true: bấm E thì vật vào Hotbar và biến mất khỏi cảnh.
## - [member can_pickup] = false: bấm E thì mở trình đọc với [member pages]
##   (nếu có trang), vật vẫn ở yên chỗ.
## Với cả hai kiểu, nếu có [member document_id] hoặc [member pages] thì trình đọc
## mở ngay sau khi tương tác (vật nhặt được vẫn vào Hotbar).
## Độc lập với hai kiểu trên, MEMORY_TRIGGER còn mở khóa ký ức qua MemoryManager.
class_name Interactable
extends Area3D

## Physics layer dành riêng cho vật tương tác. Tâm ngắm quét đúng layer này.
const INTERACTABLE_LAYER := 3

enum InteractionType {
	ITEM,           ## Đồ vật thường.
	MEMORY_TRIGGER, ## Vật kích hoạt ký ức: mở khóa memory và monologue nội tâm.
}

## Phát ra sau khi người chơi tương tác thành công.
signal interacted(actor: Node)

## ID duy nhất. Với MEMORY_TRIGGER, đây cũng là ID ký ức được mở khóa.
@export var item_id: StringName
## Key dịch tên vật, hiện dưới tâm ngắm và trong Hotbar.
@export var display_name_key: String
@export var can_pickup: bool = false
@export var interaction_type: InteractionType = InteractionType.ITEM

@export_group("Vật nhặt được")
## Key dịch mô tả manh mối, hiện khi bấm phím số để Inspect.
@export var description_key: String
@export var icon: Texture2D
## Sổ đặc biệt mở ngay khi nhặt (và khi bấm phím số trên Hotbar), ví dụ &"expense_book_1999".
@export var document_id: StringName

@export_group("Tài liệu đọc tại chỗ")
## Key dịch từng trang. Chỉ dùng khi can_pickup = false.
@export var pages: Array[String] = []

@export_group("Nâng cao")
## Ghi đè lời nhắc mặc định ("[E] Nhặt lấy" / "[E] Đọc / Xem").
@export var prompt_text_key: String
## Key dịch monologue nội tâm khi kích hoạt ký ức (chỉ dùng cho MEMORY_TRIGGER).
@export var monologue_key: String
## ID âm thanh phát tại vị trí vật khi tương tác thành công (ví dụ &"sfx_key_jingle").
@export var interact_sfx: StringName
## Tắt tương tác sau lần dùng đầu tiên.
@export var one_shot: bool = false
## Tắt thì tâm ngắm bỏ qua vật này (tia ngắm đi xuyên qua, không bị vật đang tắt che mất).
@export var enabled: bool = true:
	set(value):
		enabled = value
		if is_node_ready():
			set_collision_layer_value(INTERACTABLE_LAYER, value)


func _ready() -> void:
	# Vật tương tác chỉ cần được tâm ngắm rọi trúng, không cần tự quét ai.
	monitoring = false
	monitorable = true
	collision_layer = 0
	collision_mask = 0
	set_collision_layer_value(INTERACTABLE_LAYER, enabled)


func is_memory_trigger() -> bool:
	return interaction_type == InteractionType.MEMORY_TRIGGER


## Tên vật đã dịch.
func get_display_name() -> String:
	return tr(display_name_key) if not display_name_key.is_empty() else ""


## Lời nhắc đã dịch theo kiểu tương tác.
func get_prompt_text() -> String:
	if not prompt_text_key.is_empty():
		return tr(prompt_text_key)
	return tr(&"PROMPT_ACTION_PICKUP") if can_pickup else tr(&"PROMPT_ACTION_READ")


func to_item_data() -> ItemData:
	var item := ItemData.new()
	item.id = item_id
	item.name_key = display_name_key
	item.description_key = description_key
	item.icon = icon
	item.document_id = document_id
	return item


## Gọi bởi PlayerInteractor. Trả về false nếu vật đang tắt hoặc Hotbar đầy.
func interact(actor: Node) -> bool:
	if not enabled:
		return false
	if can_pickup and Inventory.add_item(to_item_data()) == -1:
		EventBus.inventory_full.emit()
		return false

	interacted.emit(actor)
	EventBus.interaction_requested.emit(self, actor)
	if not interact_sfx.is_empty():
		EventBus.sfx_requested.emit(interact_sfx, global_position)
	_open_reading()

	if can_pickup:
		enabled = false
		queue_free()
		return true
	if one_shot:
		enabled = false
	return true


## Mở sổ đặc biệt hoặc trình đọc tài liệu nếu vật có nội dung để đọc.
func _open_reading() -> void:
	if not document_id.is_empty():
		EventBus.book_requested.emit(document_id)
		return
	if pages.is_empty():
		return
	var translated: Array[String] = []
	for key in pages:
		translated.append(tr(key))
	EventBus.document_requested.emit(get_display_name(), translated)
