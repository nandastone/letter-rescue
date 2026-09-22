extends SceneTree
## Integration checks for episode content, real scenes, matching and persistence.
## --headless --fixed-fps 120 --script tools/smoke_episodes.gd
const Profiles = preload("res://scripts/core/wr1_profiles.gd")
const Words = preload("res://scripts/core/wr1_words.gd")
const Pictures = preload("res://scripts/core/wr1_pictures.gd")
const Vocabulary = preload("res://scripts/core/vocabulary.gd")
const Render = preload("res://scripts/core/wr1_frontend_render.gd")
var failures: Array[String] = []
var elapsed_frames := 0
var levels_checked := 0

func _initialize() -> void:
	process_frame.connect(func():
		elapsed_frames += 1
		if elapsed_frames > 18000:
			printerr("Episode smoke timed out")
			quit(1))
	_run.call_deferred()

func check(value: bool, message: String) -> void:
	if not value:
		failures.append("episode %d: %s" % [Episode.current, message])

func _run() -> void:
	var manager = root.get_node("GameManager")
	var replay = root.get_node("InputReplay")
	Profiles.directory = "user://episode-smoke-%d/" % Time.get_ticks_usec()
	for number in [1, 2, 3]:
		Episode.select(number)
		manager.original_pending_profile = {}
		manager.original_player_name = ""
		var words := Words.new()
		words.next_words()
		var initial_words := words.words.duplicate()
		var stream: String = JSON.parse_string(FileAccess.get_file_as_string(Episode.data_path("word_list.json"))).text
		var unique := {}
		for word in stream.split(" ", false):
			word = word.strip_edges()
			if word.is_empty() or unique.has(word): continue
			unique[word] = true
			for frame in range(2):
				check(Pictures.load_picture(word, frame) != null, "missing original picture " + word)
				check(Vocabulary.load_picture(word, frame) != null, "missing displayed picture " + word)
		var profile := {"level":Episode.level_count(), "character":0, "word_cursor":words.offset,
			"score":number * 100, "words":initial_words, "difficulty":2,
			"custom_keys":false, "scancodes":[77,75,72,80,57], "joystick":false}
		Profiles.save_player("Porttest", profile)
		check(Profiles.load_player("Porttest") == profile, "last-level profile failed to round trip")
		Profiles.update_high_score("Porttest", number * 100)
		check(Profiles.high_scores()[0].score == number * 100, "high score leaked across episodes")
		for level in range(1, Episode.level_count() + 1):
			manager.current_level = level
			manager.current_difficulty = 2
			manager.score = 0
			replay.original_start_seed = 20716
			replay.mode = replay.Mode.REPLAYING # Only skip the title wait; no recorded input.
			var game = load("res://scenes/game.tscn").instantiate()
			game.set_meta("frontend_replaced", true)
			root.add_child(game)
			current_scene = game
			var waited := 0
			while not game.is_replay_ready() and waited < 500:
				await process_frame
				waited += 1
			check(game.is_replay_ready(), "level %d failed to initialize" % level)
			if not game.is_replay_ready():
				game.queue_free()
				await process_frame
				continue
			if level == 1 and number > 1:
				var audio = root.get_node("AudioManager").original
				audio.enabled = true
				for music_level in [2, 3, 1]: audio.level(music_level)
				check(audio.music.stream != null, "valid episode music failed to load")
				audio.enabled = false
				audio.music.stop()
			check(game.word_manager.blocks.size() == 7, "level %d does not have seven cards" % level)
			check(game.original_gruzzles.actors.size() == game.level_data.gruzzles.size(), "Hard lost map enemies")
			# Drive the real physics path. These are smoke inputs, not route/parity claims.
			replay.mode = replay.Mode.DISABLED
			Input.action_press("move_right")
			Input.action_press("jump")
			for frame in range(120): await process_frame
			Input.action_release("move_right")
			Input.action_release("jump")
			check(game.player.original_state.ticks > 0, "level %d never updated" % level)
			game.player.set_physics_process(false)
			# Every map's seven indexed locations must support a full matching round.
			var model = game.word_manager.original_model
			for slot in range(7):
				model.attributes[model.slots[slot].y][model.slots[slot].x] = slot
			model.active_slot = -1
			model.last_touched = Vector2i(-1, -1)
			model.matched_count = 0
			for slot in range(7):
				var reveal: Dictionary = model.touch(slot)
				check(reveal.get("kind") == "reveal", "cannot reveal slot %d on level %d" % [slot, level])
				var target: int = posmod(model.word_index(slot) - model.picture_offset, 7)
				var matched: Dictionary = model.touch(target)
				check(matched.get("kind") == "correct", "cannot match slot %d on level %d" % [slot, level])
			check(model.matched_count == 7, "matching round did not complete")
			if level == Episode.level_count():
				replay.demo_mode = false
				game.finish_original_exit({}, 0)
				check(manager.current_level == Episode.level_count() + 1, "last exit did not reach ending")
				var ending: CanvasLayer = game.get_child(game.get_child_count() - 1)
				check(ending.state == "ending", "last exit did not open ending frontend")
				for page in range(Render.metadata().ending.screens.size()): ending.press(KEY_ENTER)
				check(manager.current_level == 1, "ending did not reset level")
				check(ending.state == ("ordering" if number == 1 else "menu"), "wrong ending return")
			levels_checked += 1
			game.queue_free()
			await process_frame
			current_scene = null
		print("Episode %d: %d levels, %d picture words, matching and final exit checked" % [number, Episode.level_count(), unique.size()])
	# Existing episode saves still contain independent level/score/word streams.
	for number in [3, 1, 2]:
		Episode.select(number)
		var saved := Profiles.load_player("Porttest")
		check(saved.level == Episode.level_count() and saved.score == number * 100, "another episode overwrote progress")
	# Test option import from a completed WR2 profile without copying progress.
	Episode.select(2)
	var donor := Profiles.load_player("Porttest")
	Profiles.save_player("Visitor", donor)
	Episode.select(1)
	var imported := Profiles.load_player("Visitor")
	check(imported.level == 1 and imported.score == 0 and imported.character == donor.character, "cross-episode option import")
	check(imported.words[0] == "toe", "cross-episode import retained the wrong word stream")
	for failure in failures: printerr(failure)
	print("Episode smoke: %d levels, %d failures" % [levels_checked, failures.size()])
	quit(0 if failures.is_empty() else 1)
