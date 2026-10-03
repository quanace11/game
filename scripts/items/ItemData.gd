## Dữ liệu một vật phẩm nằm trong Hotbar.
class_name ItemData
extends Resource

@export var id: StringName
## Key dịch tên vật phẩm.
@export var name_key: String
## Key dịch mô tả manh mối, hiện trong khung Inspect.
@export var description_key: String
## Icon hiện trong ô Hotbar (để trống thì chỉ hiện tên).
@export var icon: Texture2D
## Khác rỗng: bấm phím số của ô này sẽ mở sổ đặc biệt ([signal EventBus.book_requested])
## thay vì khung Inspect, ví dụ &"expense_book_1999".
@export var document_id: StringName


func get_display_name() -> String:
	return tr(name_key) if not name_key.is_empty() else String(id)


func get_description() -> String:
	return tr(description_key) if not description_key.is_empty() else ""
