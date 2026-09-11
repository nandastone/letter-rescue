extends SceneTree

# Runs the real production matcher and block scenes through all level-1 pairs.
# This is a diagnostic, not an assertion that today's broken result is desired.
# godot --headless --path . --script res://testing/audit_matching.gd
func _initialize() -> void:
	call_deferred("run_audit")

func run_audit() -> void:
	var level = JSON.parse_string(FileAccess.get_file_as_string("res://data/levels/level_01.json"))
	var manager = load("res://scripts/word_manager.gd").new()
	root.add_child(manager)
	var nodes: Array = []
	for i in range(level.words.size()):
		var block = load("res://scenes/question_block.tscn").instantiate()
		root.add_child(block)
		nodes.append(block)
	manager.setup(level.words, nodes)
	var possible_matches: Array = []
	var attempts := 0
	var missing_pictures: Array = []
	for block in nodes:
		if block.picture_texture == null:
			missing_pictures.append(block.word)
	for source in nodes:
		for target in nodes:
			if source == target:
				continue
			for block in nodes:
				block.state = block.State.IDLE
			manager.matched_count = 0
			manager.active_block = null
			manager.activate_block(source)
			manager.attempt_match(target)
			attempts += 1
			if manager.matched_count > 0:
				possible_matches.append([source.word, target.word])
	var result := {"words": level.words, "ordered_pair_attempts": attempts,
		"successful_pairs": possible_matches, "missing_picture_textures": missing_pictures}
	print(JSON.stringify(result, "  "))
	quit()
