extends Node

# Manages the word-picture matching flow for a level.

var words: Array[String] = []
var current_word_index: int = 0
var matched_count: int = 0
var active_block: Area2D = null
var blocks: Array[Area2D] = []

signal word_revealed(word: String)
signal correct_match(word: String)
signal wrong_match(block_position: Vector2)
signal all_words_matched

func setup(word_list: Array, block_nodes: Array) -> void:
	words = []
	for w in word_list:
		words.append(w as String)
	blocks = []
	for b in block_nodes:
		blocks.append(b as Area2D)
	current_word_index = 0
	matched_count = 0
	active_block = null

	# Assign words to blocks.
	for i in range(min(words.size(), blocks.size())):
		blocks[i].setup(words[i], i)
		blocks[i].block_touched.connect(_on_block_touched)

func _on_block_touched(block: Area2D) -> void:
	if active_block == null:
		# First touch: reveal this block's word, show pictures on others.
		activate_block(block)
	elif block == active_block:
		# Touching the active word block again does nothing.
		pass
	else:
		# Touching another block while a word is active: this is a match attempt.
		attempt_match(block)

func activate_block(block: Area2D) -> void:
	active_block = block
	block.show_word()
	word_revealed.emit(block.word)

	# Show pictures on all other unmatched blocks.
	for b in blocks:
		if b != block and b.state != b.State.MATCHED:
			b.show_picture()

func attempt_match(picture_block: Area2D) -> void:
	if active_block == null:
		return

	if picture_block.word == active_block.word:
		# Correct match.
		active_block.mark_matched()
		picture_block.mark_matched()
		correct_match.emit(active_block.word)
		matched_count += 1
		active_block = null

		# Reset remaining blocks.
		for b in blocks:
			b.reset_to_idle()

		if matched_count >= words.size():
			all_words_matched.emit()
	else:
		# Wrong match: spawn a gruzzle at the wrong picture's position.
		var spawn_pos := picture_block.global_position
		wrong_match.emit(spawn_pos)

		# Reset all blocks back to question marks.
		active_block = null
		for b in blocks:
			b.reset_to_idle()

func reset() -> void:
	current_word_index = 0
	matched_count = 0
	active_block = null
	for b in blocks:
		if b.block_touched.is_connected(_on_block_touched):
			b.block_touched.disconnect(_on_block_touched)
