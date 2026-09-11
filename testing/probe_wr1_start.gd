extends SceneTree
## Exercise actual scene construction, with no native state injected.
func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var output := args[args.find("--probe-output") + 1]
	var manager = root.get_node("GameManager")
	var difficulty := args.find("--probe-difficulty")
	if difficulty >= 0:
		manager.current_difficulty = int(args[difficulty + 1])
	change_scene_to_file("res://scenes/game.tscn")
	await process_frame
	while current_scene == null or not current_scene.is_replay_ready():
		await process_frame
	var game = current_scene
	var actors = game.original_gruzzles
	var match_model = game.word_manager.original_model
	var result := {"seed":game.original_start_seed, "rng":actors.rng,
		"word_offset":match_model.word_offset, "picture_offset":match_model.picture_offset,
		"gruzzle_count":actors.actors.size(), "gruzzle_difficulty":actors.difficulty,
		"gruzzle_cadence":actors.cadence,"words":game.original_words.words,
		"word_cursor":game.original_words.offset,"gruzzles":[],
		"mystery_word":game.mystery_word.word}
	for i in range(actors.actors.size()):
		var actor: Dictionary = actors.actors[i].duplicate()
		actor["move_timer"] = actors.timers[i]
		result.gruzzles.append(actor)
	var file := FileAccess.open(output, FileAccess.WRITE)
	file.store_string(JSON.stringify(result))
	print("Fresh start scene probe PASS")
	quit()
