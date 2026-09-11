extends CanvasLayer
## Screen-space Benny and the mutable picture/word panel, above native chrome.
var hud: CanvasLayer
var words: Array[String] = []
var benny: Sprite2D
var panel_sprite: Sprite2D
var panel: Image
var reading_word := ""
var reading_opacity := 1.0

func configure(chrome: CanvasLayer, word_list: Array[String]) -> void:
	layer = 20
	hud = chrome
	words.assign(word_list)
	benny = Sprite2D.new()
	benny.centered = false
	add_child(benny)
	panel_sprite = Sprite2D.new()
	panel_sprite.centered = false
	add_child(panel_sprite)

func present(event: Dictionary) -> void:
	if event.kind in ["helper", "dissolve"]:
		benny.texture = load("res://assets/sprites/wr1_benny_%d.png" % event.frame)
		benny.position = event.position
		panel_sprite.visible = event.kind == "dissolve" or event.order >= 0
	if event.kind == "helper" and event.order >= 0:
		reading_word = words[event.word_index].to_lower()
		reading_opacity = 1.0
		panel = Image.create(65, 35, false, Image.FORMAT_RGBA8)
		panel.fill(Color.BLACK)
		panel.fill_rect(Rect2i(1, 1, 63, 33), Color.WHITE)
		panel.fill_rect(Rect2i(20, 2, 24, 23), Color.BLACK)
		panel.fill_rect(Rect2i(21, 3, 22, 21), Color.WHITE)
		# The native card interior is x+6..x+63, y+4..y+11.
		preload("res://scripts/core/wr1_text.gd").draw(panel, words[event.word_index].to_lower(),
			Vector2i(32 - 4 * words[event.word_index].length(), 26), Color.BLACK, Color.WHITE)
		panel_sprite.position = Vector2(event.position) + Vector2(90, -34)
	if event.kind == "transfer":
		panel.blit_rect(hud.original_top, Rect2i(144 + 23 * event.order, 5, 23, 23), Vector2i(20, 2))
		hud.clear_original_match(event.order)
	if event.kind == "dissolve":
		reading_opacity = maxf(0.0, reading_opacity - 0.05)
		for pixel in event.pixels:
			panel.set_pixelv(pixel, Color.WHITE)
	if event.kind == "clear":
		reading_word = ""
		panel.fill(Color.BLACK)
		panel.fill_rect(Rect2i(1, 1, 63, 33), Color.WHITE)
	if panel != null:
		panel_sprite.texture = ImageTexture.create_from_image(panel)
		preload("res://scripts/core/wr1_clear_text.gd").sprite_text(panel_sprite, panel, [
			{"erase":Rect2(1,26,63,8), "rect":Rect2(2,24,61,11), "text":reading_word, "background":Color.WHITE, "pixels":9, "alpha":reading_opacity, "baseline_adjustment":0.5}])
