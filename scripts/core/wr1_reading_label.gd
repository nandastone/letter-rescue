extends Control
## A presentation-only word: actual font glyphs, never a source of game state.
const TYPEFACE = preload("res://assets/fonts/andika/Andika-Regular.ttf")
static var metrics: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/fonts/andika/metrics.json"))
var word := ""
var prefix := -1
var hide_suffix := false
var ink := Color.WHITE
var prefix_ink := Color8(255, 255, 85)
var font_size := 14
var outline := false
var outline_size := 1
var alignment := HORIZONTAL_ALIGNMENT_CENTER
var baseline_adjustment := 1.5
var caret_index := -1
# Fine optical adjustment for a symbol. Keep it in the drawing coordinates:
# the pixel-art viewport snaps Control positions to whole game pixels.
var ink_offset := Vector2.ZERO

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visibility_layer = 2

func set_word(value: String, collected: int = -1, hidden: bool = false) -> void:
	word = value
	prefix = collected
	hide_suffix = hidden
	queue_redraw()

func layout() -> Dictionary:
	# Use the bundled font's Latin ink bounds, including g/j/p/q/y, rather
	# than its much taller multilingual line spacing. Reserve padding on all
	# sides and keep one stable baseline for words with and without descenders.
	var height_ratio: float = (metrics.ascent + metrics.descent) / float(metrics.units_per_em)
	var lines := word.split("\n")
	var pixels := font_size
	while pixels > 4 and (_width(lines, pixels) > size.x - 2 or pixels * (height_ratio + 1.25 * (lines.size() - 1)) > size.y - 2):
		pixels -= 1
	var width := _width(lines, pixels)
	var baseline := floorf((size.y - pixels * (height_ratio + 1.25 * (lines.size() - 1))) * 0.5 + pixels * float(metrics.ascent) / float(metrics.units_per_em))
	# Andika's visible letters sit high against the original panel frames.
	# This optical adjustment is shared by HUD, cards, symbols and page text.
	baseline += baseline_adjustment
	return {"pixels":pixels, "pen":Vector2(_left(width), baseline) + ink_offset}

func _width(lines: PackedStringArray, pixels: int) -> float:
	var width := 0.0
	for line in lines: width = maxf(width, TYPEFACE.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels).x)
	return width

func _left(width: float) -> float:
	if alignment == HORIZONTAL_ALIGNMENT_LEFT: return 1.0
	if alignment == HORIZONTAL_ALIGNMENT_RIGHT: return size.x - width - 1.0
	return (size.x - width) * 0.5

func _draw() -> void:
	if word.is_empty() and caret_index < 0: return
	var placement := layout()
	var pixels: int = placement.pixels
	var pen: Vector2 = placement.pen
	if caret_index >= 0:
		var caret_x := pen.x + TYPEFACE.get_string_size(word.left(caret_index), HORIZONTAL_ALIGNMENT_LEFT, -1, pixels).x + 1.0
		draw_line(Vector2(caret_x, pen.y - pixels * float(metrics.ascent) / float(metrics.units_per_em)),
			Vector2(caret_x, pen.y + pixels * float(metrics.descent) / float(metrics.units_per_em)), ink, 0.5)
	if "\n" in word:
		for line in word.split("\n"):
			pen.x = _left(TYPEFACE.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels).x)
			if outline: draw_string_outline(TYPEFACE, pen, line, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels, outline_size, Color.BLACK)
			draw_string(TYPEFACE, pen, line, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels, ink)
			pen.y += pixels * 1.25
		return
	var shown := word.left(prefix) if prefix >= 0 and hide_suffix else word
	if outline: draw_string_outline(TYPEFACE, pen, shown, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels, outline_size, Color.BLACK)
	draw_string(TYPEFACE, pen, shown, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels, ink)
	if prefix >= 0:
		draw_string(TYPEFACE, pen, word.left(prefix), HORIZONTAL_ALIGNMENT_LEFT, -1, pixels, prefix_ink)
