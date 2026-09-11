extends Node

# Manages the word-picture matching flow for a level.

var words: Array[String] = []
var current_word_index: int = 0
var matched_count: int = 0
var active_block: Node2D = null
var blocks: Array[Node2D] = []
var original_model: RefCounted
var original_last_index: int = 255
var original_contact_grid := Vector2i.ZERO

func configure_original(data: Dictionary, words_rotation: int = 5, pictures_rotation: int = 0) -> void:
	# Reset clears the active flag but retains DS:032e's last word index.
	original_model = preload("res://scripts/wr1_matching.gd").new()
	original_model.configure(data, words_rotation, pictures_rotation)
	original_model.active_index = original_last_index
	# Resolve stable slot IDs from raw coordinates rather than array order.
	var ordered: Array[Node2D] = []
	ordered.resize(7)
	for block in blocks:
		var grid := Vector2i(block.position / 8.0)
		var slot: int = original_model.slots.find(grid)
		assert(slot >= 0)
		ordered[slot] = block
		block.setup(words[original_model.word_index(slot)], slot)
		block.set_original_picture(words[original_model.picture_index(slot)])
	blocks = ordered
	_refresh_original()

func scan_original(gx: int, gy: int, collect_cell: Callable = Callable()) -> Dictionary:
	var result: Dictionary = original_model.scan(gx, gy, collect_cell)
	if result.is_empty():
		return result
	matched_count = original_model.matched_count
	if result.has("target"):
		original_contact_grid = original_model.slots[int(result.target)]
	current_word_index = int(result.word_index)
	active_block = blocks[original_model.active_slot] if original_model.active_slot >= 0 else null
	_refresh_original()
	match result.kind:
		"reveal": word_revealed.emit(words[current_word_index])
		"correct":
			correct_match.emit(words[current_word_index])
			if result.complete:
				all_words_matched.emit()
		"wrong": wrong_match.emit(Vector2(result.spawn_grid) * 8.0)
	return result

func _refresh_original() -> void:
	for slot in range(7):
		var block := blocks[slot]
		if original_model.active_slot >= 0:
			block.state = block.State.SHOWING_WORD if slot == original_model.active_slot else block.State.SHOWING_PICTURE
		else:
			block.state = block.State.IDLE if original_model.question_visible(slot) else block.State.MATCHED
		block.update_visual()

signal word_revealed(word: String)
signal correct_match(word: String)
signal wrong_match(block_position: Vector2)
signal all_words_matched

func setup(word_list: Array, block_nodes: Array) -> void:
	if original_model != null:
		original_last_index = original_model.active_index
	original_model = null
	words = []
	for w in word_list:
		words.append(w as String)
	blocks = []
	for b in block_nodes:
		blocks.append(b as Node2D)
	current_word_index = 0
	matched_count = 0
	active_block = null
	for i in range(min(words.size(), blocks.size())):
		blocks[i].setup(words[i], i)
