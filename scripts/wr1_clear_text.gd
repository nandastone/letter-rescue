extends RefCounted
## Optional display adapter. Original assets and simulation work stay intact.
const ReadingLabel = preload("res://scripts/wr1_reading_label.gd")
const CYAN := Color8(0, 170, 170)
var top: Sprite2D
var bottom: Sprite2D
var current: Control
var mystery: Control
var score: Control
const CHROME = preload("res://assets/extracted/hud_top.png")

static func enabled() -> bool:
	return "--clear-text" in LaunchArgs.user_args()

static func configure_window(window: Window) -> void:
	if enabled():
		window.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		window.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP

static func label(parent: Node, rect: Rect2, value: String, color: Color = Color.WHITE, pixels: int = 14) -> Control:
	var item := ReadingLabel.new()
	item.position = rect.position
	item.size = rect.size
	item.ink = color
	item.font_size = pixels
	parent.add_child(item)
	item.set_word(value)
	return item

func configure_hud(hud: CanvasLayer) -> void:
	# Layer 4 is visible only to the original 320x200 reference capture.
	hud.get_node("HudTop").visibility_layer = 4
	hud.get_node("HudBottom").visibility_layer = 4
	top = Sprite2D.new()
	top.centered = false
	top.visibility_layer = 2
	top.z_index = 1
	hud.add_child(top)
	bottom = Sprite2D.new()
	bottom.centered = false
	bottom.visibility_layer = 2
	bottom.position.y = 184
	hud.add_child(bottom)
	current = label(hud, Rect2(60, 3, 67, 12), "", Color.WHITE, 10)
	current.baseline_adjustment = 0.75
	current.z_index = 2
	score = label(hud, Rect2(60, 17, 67, 12), "0", Color.BLACK, 9)
	score.z_index = 2
	mystery = label(hud, Rect2(128, 185, 64, 14), "", Color8(85, 255, 255), 10)
	mystery.baseline_adjustment = 0.75
	mystery.z_index = 2
	refresh_hud(hud)

func refresh_hud(hud: CanvasLayer) -> void:
	var upper: Image = hud.original_top.duplicate()
	# Restore the original empty panel, including its bevel. Fit the lettering
	# inside that panel instead of enlarging the background around the text.
	var original_chrome: Image = CHROME.get_image()
	original_chrome.convert(Image.FORMAT_RGBA8)
	upper.blit_rect(original_chrome, Rect2i(59, 1, 69, 16), Vector2i(59, 1))
	upper.fill_rect(Rect2i(60, 18, 67, 10), CYAN)
	var lower: Image = hud.original_bottom.duplicate()
	lower.fill_rect(Rect2i(128, 4, 64, 8), CYAN)
	if top.texture == null:
		top.texture = ImageTexture.create_from_image(upper)
		bottom.texture = ImageTexture.create_from_image(lower)
	else:
		top.texture.update(upper)
		bottom.texture.update(lower)
	current.set_word(hud.current_word)
	score.set_word(str(hud.displayed_score))
	mystery.set_word(hud.mystery_text, hud.mystery_prefix, not hud.mystery_revealed)

static func configure_letter(collectible: Node2D) -> void:
	collectible.get_node("Sprite2D").visibility_layer = 4
	var item := label(collectible, Rect2(-4, -7, 24, 30), collectible.data.to_lower(), Color8(255, 255, 85), 24)
	item.outline = true
	item.outline_size = 2
	item.name = "ClearLetter"

static func sprite_text(source: Sprite2D, raster: Image, runs: Array) -> void:
	if not enabled(): return
	var view: Sprite2D = source.get_meta("reading_view") if source.has_meta("reading_view") else null
	if view == null:
		view = Sprite2D.new()
		view.centered = false
		view.visibility_layer = 2
		source.get_parent().add_child(view)
		source.set_meta("reading_view", view)
		source.visibility_layer = 4
	var clean := raster.duplicate()
	for child in view.get_children():
		view.remove_child(child)
		child.queue_free()
	for run in runs:
		clean.fill_rect(Rect2i(run.erase), run.get("background", Color.TRANSPARENT))
		var item := label(view, run.rect, run.text, run.get("color", Color.BLACK), run.get("pixels", 10))
		item.position += source.offset - (Vector2(raster.get_size()) * 0.5 if source.centered else Vector2.ZERO)
		item.modulate.a = run.get("alpha", 1.0)
		item.outline = run.get("outline", false)
		item.baseline_adjustment = run.get("baseline_adjustment", 1.5)
	view.texture = ImageTexture.create_from_image(clean)
	sync_sprite(source)

static func sync_sprite(source: Sprite2D) -> void:
	var view: Sprite2D = source.get_meta("reading_view") if source.has_meta("reading_view") else null
	if view == null: return
	view.transform = source.transform
	view.centered = source.centered
	view.offset = source.offset
	view.z_index = source.z_index
	view.visible = source.visible

static func reward(source: Sprite2D, raster: Image, caption: String, amount: String, color: Color) -> void:
	if not enabled(): return
	sprite_text(source, raster, [
		{"erase":Rect2(0,0,64,16), "rect":Rect2(0,-10,64,14), "text":caption, "color":color, "pixels":8, "outline":true},
		{"erase":Rect2(0,0,0,0), "rect":Rect2(4,4,56,18), "text":amount, "color":color, "pixels":12, "outline":true}])

static func word_list(frontend: CanvasLayer, source: Image) -> Image:
	var result := source.duplicate()
	# Popups sit over the paused readable scene, rather than baking the old
	# bitmap lettering from the reference framebuffer back into the display.
	var popup_rects := {"words":Rect2i(192,0,128,192), "help":Rect2i(72,16,168,176),
		"sound":Rect2i(96,56,128,80), "quit":Rect2i(60,58,197,27)}
	if frontend.game != null and popup_rects.has(frontend.state):
		result.fill(Color.TRANSPARENT)
		var rect: Rect2i = popup_rects[frontend.state]
		result.blit_rect(source, rect, rect.position)
	# Word-panel runs already come from the shared frontend renderer. Drawing
	# a second set here would superimpose two differently sized copies.
	return result

static func frontend_labels(frontend: CanvasLayer, runs: Array) -> void:
	var old := frontend.get_node_or_null("ClearPage")
	if old != null:
		frontend.remove_child(old)
		old.queue_free()
	var page := Node2D.new()
	page.name = "ClearPage"
	page.visibility_layer = 2
	frontend.add_child(page)
	for run in runs:
		var item := label(page, run.rect, run.text, run.get("color", Color.BLACK), run.get("pixels", 10))
		item.alignment = run.get("align", HORIZONTAL_ALIGNMENT_CENTER)
		item.caret_index = run.get("caret", -1)
