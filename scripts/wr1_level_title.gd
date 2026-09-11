extends CanvasLayer
## WR1.EXE 8361..845b: title card during fresh map loads, never cached respawns.
signal dismissed

const Text = preload("res://scripts/wr1_text.gd")
const INITIAL_WAIT_SECONDS := 300.0 * 12428.0 / 1193182.0
var remaining := 0.0
var waiting := false

static func render(level: int) -> Image:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_titles.json"))
	assert(level >= 1 and level <= data.titles.size())
	var title: Dictionary = data.titles[level - 1]
	var result := Image.create(320, 200, false, Image.FORMAT_RGBA8)
	var cyan := Color8(85, 255, 255)
	result.fill(Color8(170, 170, 170))
	# Inclusive GX rectangle: (40,58)..(279,84), one-pixel black border.
	result.fill_rect(Rect2i(40, 58, 240, 27), Color.BLACK)
	result.fill_rect(Rect2i(41, 59, 238, 25), cyan)
	Text.draw(result, title.heading, Vector2i(128, 62), Color.BLACK, cyan)
	Text.draw(result, title.name, Vector2i(160 - title.name.length() * 4, 72), Color.BLACK, cyan)
	return result

func configure(level: int) -> void:
	layer = 101
	var sprite := Sprite2D.new()
	sprite.centered = false
	# The gameplay rasterizer uses layer 1; presentation and this card use 2.
	sprite.visibility_layer = 2
	sprite.texture = ImageTexture.create_from_image(render(level))
	add_child(sprite)
	if preload("res://scripts/wr1_clear_text.gd").enabled():
		var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_titles.json"))
		var title: Dictionary = data.titles[level - 1]
		var clean := render(level)
		clean.fill_rect(Rect2i(41,59,238,25), Color8(85,255,255))
		sprite.texture = ImageTexture.create_from_image(clean)
		preload("res://scripts/wr1_clear_text.gd").label(self, Rect2(42,59,236,12), title.heading, Color.BLACK, 9)
		preload("res://scripts/wr1_clear_text.gd").label(self, Rect2(42,71,236,12), title.name, Color.BLACK, 9)
	set_process(false)
	set_process_input(false)

func wait_for_start() -> void:
	remaining = INITIAL_WAIT_SECONDS
	waiting = true
	set_process(true)
	set_process_input(true)
	await dismissed

func _process(delta: float) -> void:
	remaining -= delta
	if remaining <= 0.0:
		_dismiss()

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		get_viewport().set_input_as_handled()
		_dismiss()

func _dismiss() -> void:
	if not waiting:
		return
	waiting = false
	set_process(false)
	set_process_input(false)
	dismissed.emit()
