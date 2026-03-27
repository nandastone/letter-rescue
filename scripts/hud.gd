extends CanvasLayer

@onready var score_label: Label = $TopBar/ScoreBarBot/ScoreLabel
@onready var revealed_word: Label = $TopBar/ScoreBarTop/RevealedWord
@onready var match_boxes: HBoxContainer = $TopBar/MatchBoxContainer/MysteryBoxes
@onready var word_bar: ColorRect = $BottomBar/WordBar
@onready var word_label: Label = $BottomBar/WordBar/WordLabel
@onready var message_label: Label = $MessageLabel

var _mystery_labels: Array[Label] = []

const DIM_COLOR := Color(0.0, 0.35, 0.35, 1.0)
const LIT_COLOR := Color.WHITE
const FONT_SIZE := 8
const DARK_TEXT := Color(0.1, 0.1, 0.1, 1.0)

func _ready() -> void:
	message_label.visible = false
	word_label.visible = false
	revealed_word.visible = false
	# Score: dark text on cyan background.
	score_label.add_theme_font_size_override("font_size", FONT_SIZE)
	score_label.add_theme_color_override("font_color", DARK_TEXT)
	# Revealed word: dark text on lighter cyan.
	revealed_word.add_theme_font_size_override("font_size", FONT_SIZE)
	revealed_word.add_theme_color_override("font_color", DARK_TEXT)
	# Bottom word bar: white text on cyan.
	word_label.add_theme_font_size_override("font_size", FONT_SIZE)
	word_label.add_theme_color_override("font_color", Color.WHITE)
	# Message: white text.
	message_label.add_theme_font_size_override("font_size", FONT_SIZE)
	message_label.add_theme_color_override("font_color", Color.WHITE)
	_reset_match_boxes()

func _reset_match_boxes() -> void:
	for i in range(match_boxes.get_child_count()):
		var box: ColorRect = match_boxes.get_child(i)
		box.color = Color(0.5, 0.5, 0.5, 1.0)
		box.visible = true
		var label: Label = box.get_node("Letter")
		label.text = ""
		for child in box.get_children():
			if child is Sprite2D:
				child.queue_free()

func update_score(value: int) -> void:
	score_label.text = "%d" % value

func update_slime(_count: int) -> void:
	pass

func update_level(_level: int) -> void:
	_reset_match_boxes()

func setup_mystery_word(word: String, next_index: int) -> void:
	for lbl in _mystery_labels:
		lbl.queue_free()
	_mystery_labels.clear()

	if word.is_empty():
		return

	var char_width: float = 10.0
	var total_width: float = word.length() * char_width
	var start_x: float = (word_bar.size.x - total_width) / 2.0

	for i in range(word.length()):
		var lbl := Label.new()
		lbl.text = word[i].to_upper()
		lbl.add_theme_font_size_override("font_size", FONT_SIZE)
		lbl.add_theme_color_override("font_color", LIT_COLOR if i < next_index else DIM_COLOR)
		lbl.position = Vector2(start_x + i * char_width, 0)
		lbl.size = Vector2(char_width, word_bar.size.y)
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		word_bar.add_child(lbl)
		_mystery_labels.append(lbl)

func update_mystery_letter(index: int) -> void:
	if index >= 0 and index < _mystery_labels.size():
		_mystery_labels[index].add_theme_color_override("font_color", LIT_COLOR)

func add_matched_word(word: String, match_index: int) -> void:
	var box_index: int = match_index - 1
	if box_index < 0 or box_index >= match_boxes.get_child_count():
		return
	var box: ColorRect = match_boxes.get_child(box_index)
	box.color = Color(0.0, 0.5, 0.5, 1.0)
	var label: Label = box.get_node("Letter")
	var pic_path := "res://assets/pictures/%s.png" % word.to_lower()
	if ResourceLoader.exists(pic_path):
		var pic_sprite := Sprite2D.new()
		pic_sprite.texture = load(pic_path)
		pic_sprite.position = box.size / 2
		var pic_size: Vector2 = pic_sprite.texture.get_size()
		var sx: float = box.size.x / pic_size.x * 0.9
		var sy: float = box.size.y / pic_size.y * 0.9
		var s: float = min(sx, sy)
		pic_sprite.scale = Vector2(s, s)
		box.add_child(pic_sprite)
		label.text = ""
	else:
		label.text = word[0].to_upper()
		label.add_theme_color_override("font_color", Color(1.0, 1.0, 0.33))
		label.add_theme_font_size_override("font_size", 10)

func show_current_word(word: String) -> void:
	revealed_word.text = word.to_upper()
	revealed_word.visible = true

func hide_current_word() -> void:
	revealed_word.visible = false

func show_message(text: String, duration: float = 2.0) -> void:
	message_label.text = text
	message_label.visible = true
	await get_tree().create_timer(duration).timeout
	message_label.visible = false
