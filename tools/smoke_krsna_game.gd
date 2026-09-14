extends SceneTree
## Boots real levels with every custom word; verifies cards, HUD and help.
## Run with --fixed-fps 120, optionally followed by -- --legacy.

const Vocabulary = preload("res://scripts/core/vocabulary.gd")
const Content = preload("res://scripts/game/krsna_vocabulary.gd")
var failures: Array[String] = []

func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var manager = root.get_node("GameManager")
	var originals: Array = Content.REPLACEMENTS.keys()
	originals.append_array(["pot", "crown"])
	for start in range(0, originals.size(), 7):
		var batch: Array = originals.slice(start, mini(start + 7, originals.size()))
		while batch.size() < 7:
			batch.append("pen")
		manager.original_pending_profile = {"words": batch, "word_cursor": 0}
		manager.current_level = 1
		var game = load("res://scenes/game.tscn").instantiate()
		# Exercise profile loading without writing a test profile on shutdown.
		game.set_meta("frontend_replaced", true)
		root.add_child(game)
		current_scene = game
		var waited := 0
		while not game.is_replay_ready() and waited < 1200:
			await process_frame
			waited += 1
		if not game.is_replay_ready():
			failures.append("level failed to initialize")
		elif not _check_level(game, batch):
			failures.append("level verification did not finish")
		game.queue_free()
		await process_frame
		current_scene = null
	for failure in failures:
		printerr("Krsna game FAILED: " + failure)
	if failures.is_empty():
		print("Krsna game: all 19 custom words verified in real level cards, HUD and help; original save words preserved")
	quit(0 if failures.is_empty() else 1)


func _check_level(game, originals: Array) -> bool:
	var displayed := Vocabulary.display_words(originals)
	if game.original_words.words != originals or game.word_manager.words != displayed:
		failures.append("level vocabulary or underlying save words differ")
	var model = game.word_manager.original_model
	for slot in range(7):
		var block = game.word_manager.blocks[slot]
		var expected_word: String = displayed[model.word_index(slot)]
		var expected_picture: String = displayed[model.picture_index(slot)]
		if block.word != expected_word:
			failures.append("wrong card word: " + expected_word)
		for frame in range(2):
			if not _same(block.original_picture_frames[frame].get_image(), Vocabulary.load_picture(expected_picture, frame).get_image()):
				failures.append("wrong card picture: " + expected_picture)
			block.set_original_picture_frame(frame)
			if not _same(block.get_node("PictureSprite").texture.get_image(), Vocabulary.load_picture(expected_picture, frame).get_image()):
				failures.append("card did not display animation frame: " + expected_picture)
	if game.original_letters.word not in displayed:
		failures.append("mystery word was not translated")
	var help := Image.create(320, 200, false, Image.FORMAT_RGBA8)
	help.fill(Color.BLACK)
	game.draw_original_word_list(help)
	for i in range(7):
		var expected: Image = Vocabulary.load_picture(displayed[i]).get_image()
		if not _same(help.get_region(Rect2i(287, 7 + i * 26, 24, 24)), expected):
			failures.append("wrong help picture: " + displayed[i])
		for frame in range(2):
			game.hud.add_matched_word(displayed[i], i, frame)
			if not _same(game.hud.original_top.get_region(Rect2i(144 + 23 * i, 5, 24, 24)), Vocabulary.load_picture(displayed[i], frame).get_image()):
				failures.append("wrong matched HUD picture frame: " + displayed[i])
	var frontend = load("res://scripts/core/wr1_frontend.gd").new()
	game.add_child(frontend)
	frontend.game = game
	if frontend.page_context().words != displayed:
		failures.append("frontend uses untranslated words")
	frontend.free()
	return true


func _same(actual: Image, expected: Image) -> bool:
	actual.convert(Image.FORMAT_RGBA8)
	expected.convert(Image.FORMAT_RGBA8)
	return actual.get_size() == expected.get_size() and actual.get_data() == expected.get_data()
