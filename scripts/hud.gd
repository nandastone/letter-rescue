extends CanvasLayer

# Minimal HUD during the pixel-exact rebuild. Top/bottom chrome strips are
# baked in as static textures (see hud.tscn); dynamic elements aren't yet
# drawn. The update_* methods are stubs so existing callers in game.gd don't
# crash. Once the FONT.WR glyph-blit path lands, dynamic overlays will
# replace these stubs.

@onready var message_label: Label = $MessageLabel


func _ready() -> void:
	message_label.visible = false


func update_score(_value: int) -> void:
	pass


func update_slime(_count: int) -> void:
	pass


func update_level(_level: int) -> void:
	pass


func setup_mystery_word(_word: String, _next_index: int) -> void:
	pass


func update_mystery_letter(_index: int) -> void:
	pass


func add_matched_word(_word: String, _match_index: int) -> void:
	pass


func show_current_word(_word: String) -> void:
	pass


func hide_current_word() -> void:
	pass


func show_message(text: String, duration: float = 2.0) -> void:
	message_label.text = text
	message_label.visible = true
	await get_tree().create_timer(duration).timeout
	message_label.visible = false
