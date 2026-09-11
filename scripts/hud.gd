extends CanvasLayer

# The original chrome, updated with the recovered BIOS text and picture blits.

const WR1Text = preload("res://scripts/wr1_text.gd")
const CYAN := Color8(0, 170, 170)
var original_top: Image
var original_top_texture: ImageTexture
var original_bottom: Image
var original_bottom_texture: ImageTexture
var mystery_text: String = ""
var mystery_prefix: int = 0
var original_slime_used: int = -1
var current_word := ""
var displayed_score := 0
var mystery_revealed := false
var clear_text: RefCounted


func _ready() -> void:
	reset_original_chrome()
	if preload("res://scripts/wr1_clear_text.gd").enabled():
		clear_text = preload("res://scripts/wr1_clear_text.gd").new()
		clear_text.configure_hud(self)

func refresh_reading_text() -> void:
	if clear_text != null: clear_text.refresh_hud(self)

func reset_original_chrome() -> void:
	current_word = ""
	original_slime_used = -1
	$HudTop.z_index = 1 # Matched cards may cover x304, above the side chrome.
	original_top = preload("res://assets/extracted/hud_top.png").get_image()
	original_top.convert(Image.FORMAT_RGBA8)
	original_top.fill_rect(Rect2i(60, 18, 67, 10), CYAN)
	original_top_texture = ImageTexture.create_from_image(original_top)
	$HudTop.texture = original_top_texture
	original_bottom = preload("res://assets/extracted/hud_bottom.png").get_image()
	original_bottom.convert(Image.FORMAT_RGBA8)
	original_bottom_texture = ImageTexture.create_from_image(original_bottom)
	$HudBottom.texture = original_bottom_texture
	refresh_reading_text()


func update_score(value: int) -> void:
	displayed_score = value
	original_top.fill_rect(Rect2i(60, 18, 67, 10), CYAN)
	var text := str(value)
	WR1Text.draw(original_top, text, Vector2i(93 - 4 * text.length(), 19), Color.BLACK, CYAN)
	original_top_texture.update(original_top)
	refresh_reading_text()


func update_original_slime(used: int, restored: bool = false) -> void:
	if used == original_slime_used and not restored:
		return
	original_slime_used = used
	original_top.fill_rect(Rect2i(18, 20, 24, 4), Color8(255, 85, 255))
	# WR1 5256..52a5 erases four pixels per successful use with palette0.
	# The reset helper 5eb8 instead fills through 41-used*4 inclusively,
	# leaving one extra pink column until the next successful slime use.
	var left: int = 18 if used >= 5 else (42 if restored else 41) - used * 4
	if used > 0:
		original_top.fill_rect(Rect2i(left, 20, 42 - left, 4), Color.BLACK)
	original_top_texture.update(original_top)
	refresh_reading_text()


func setup_mystery_word(word: String, next_index: int) -> void:
	mystery_text = word.to_lower()
	mystery_prefix = next_index
	_draw_mystery()


func update_mystery_letter(index: int) -> void:
	mystery_prefix = index + 1
	# A59D..A5FD paints only the collected prefix into saved page 5. The
	# uncollected suffix may already be visible from the 20-book hint.
	var origin := Vector2i(160 - 4 * mystery_text.length(), 4)
	WR1Text.draw(original_bottom, mystery_text.left(mystery_prefix), origin, Color8(255, 255, 85), CYAN)
	original_bottom_texture.update(original_bottom)
	refresh_reading_text()

func _draw_mystery(reveal_hidden: bool = false) -> void:
	mystery_revealed = GameManager.current_difficulty != GameManager.Difficulty.HARD or reveal_hidden
	original_bottom.fill_rect(Rect2i(128, 4, 64, 8), CYAN)
	var origin := Vector2i(160 - 4 * mystery_text.length(), 4)
	if GameManager.current_difficulty != GameManager.Difficulty.HARD or reveal_hidden:
		WR1Text.draw(original_bottom, mystery_text, origin, Color8(85, 255, 255), CYAN)
	WR1Text.draw(original_bottom, mystery_text.left(mystery_prefix), origin, Color8(255, 255, 85), CYAN)
	original_bottom_texture.update(original_bottom)
	refresh_reading_text()


func add_matched_word(word: String, match_index: int, frame: int = 0) -> void:
	var picture: Texture2D = preload("res://scripts/wr1_pictures.gd").load_picture(word, frame)
	if picture != null:
		original_top.blit_rect(picture.get_image(), Rect2i(0, 0, 24, 24), Vector2i(144 + 23 * match_index, 5))
		original_top_texture.update(original_top)
		refresh_reading_text()

func clear_original_match(match_index: int) -> void:
	# 9d6a..9d80 loads KEY.WR into the saved page-5 strip. Each rescued
	# picture exposes one section of that key, rather than an empty HUD box.
	var template: Image = preload("res://assets/extracted/wr1_1_png/KEY.WR.png").get_image()
	template.convert(Image.FORMAT_RGBA8)
	var region := Rect2i(23 * match_index, 0, 23, 23)
	original_top.blit_rect(template, region, Vector2i(144 + 23 * match_index, 5))
	original_top_texture.update(original_top)
	refresh_reading_text()

func clear_original_matches() -> void:
	for i in range(7):
		clear_original_match(i)


func show_current_word(word: String) -> void:
	current_word = word.to_lower()
	WR1Text.draw(original_top, word.to_lower(), Vector2i(91 - 4 * word.length(), 5), Color.WHITE, CYAN)
	original_top_texture.update(original_top)
	refresh_reading_text()


func hide_current_word() -> void:
	current_word = ""
	original_top.fill_rect(Rect2i(60, 4, 67, 11), CYAN)
	original_top_texture.update(original_top)
	refresh_reading_text()

