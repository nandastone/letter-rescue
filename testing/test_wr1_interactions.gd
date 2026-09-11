extends SceneTree

var failures: int = 0
var checks: int = 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	run.call_deferred()

func check_native_image(actual: Image, fixture: String) -> void:
	var expected := Image.load_from_file("res://testing/fixtures/" + fixture + ".png")
	actual.convert(Image.FORMAT_RGB8)
	expected.convert(Image.FORMAT_RGB8)
	check(actual.get_size() == expected.get_size() and actual.get_data() == expected.get_data(), "Native pixels: " + fixture)

func run() -> void:
	# This is a state/render integration test, not an audio playback test.
	root.get_node("AudioManager").sounds.clear()
	change_scene_to_file("res://scenes/game.tscn")
	for i in range(20):
		await process_frame
		if current_scene != null and current_scene.original_books != null:
			break
	var game = current_scene
	var player = game.player
	if player.original_state == null:
		push_error("Run with -- --original-rules")
		quit(1)
		return
	player.set_physics_process(false)
	player.get_node("Hurtbox").monitoring = false
	game.entities.process_mode = Node.PROCESS_MODE_DISABLED
	var state = player.original_state
	check(state.attributes[20][10] == 0x84, "Loader stamps book marker")
	var font = preload("res://scripts/wr1_text.gd")
	var zero := Image.create(8, 8, false, Image.FORMAT_RGB8)
	font.draw(zero, "0", Vector2i.ZERO, Color.BLACK, Color8(0, 170, 170))
	var native: Image = load("res://assets/extracted/hud_top.png").get_image().get_region(Rect2i(89, 19, 8, 8))
	native.convert(Image.FORMAT_RGB8)
	check(zero.get_data() == native.get_data(), "BIOS score raster matches reference")
	# Native right walk: books at logical movement steps4,8,12 (world X80,112,144).
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_books_walk.json"))
	Input.action_press("move_right")
	for step in range(1, 13):
		player._original_physics(player.WR1Motion.STEP_SECONDS)
		var actual: Dictionary = state.snapshot()
		actual.merge(game.original_interaction_snapshot())
		for key in fixture.updates[step - 1]:
			if key != "replay_frame":
				check(actual[key] == int(fixture.updates[step - 1][key]), "Native book walk step%d %s" % [step, key])
		if step % 4 == 0:
			var tile := Vector2i(5 + (step / 4 - 1) * 2, 10)
			check(game.bg_tilemap.get_cell_source_id(tile) == -1, "Collected book restores empty background")
		if step == 4:
			check_native_image(game.hud.original_top.get_region(Rect2i(89, 19, 8, 8)), "wr1_score_5")
	Input.action_release("move_right")
	check(state.world_position().x == 144, "Native twelve-step walk distance")
	# Remaining books: check the original final reward replacement and no re-collection.
	var initial_score: int = root.get_node("GameManager").score
	for position in game.original_books.positions:
		game._collect_original_cell(position.x * 2, position.y * 2)
	check(game.original_books.collected_count == 24, "All books collected exactly once")
	check(root.get_node("GameManager").score == 23 * 5 + 500, "Final book replaces +5 with +500")
	check(initial_score == 15, "Three native books give15")
	# Mismatch is nonterminal and restores the word source.
	var manager = game.word_manager
	var model = manager.original_model
	var source: Vector2i = model.slots[0]
	var target: Vector2i = model.slots[4]
	manager.scan_original(source.x, source.y)
	check(manager.blocks[0].original_word_sprite.visible, "Source displays original word card")
	check(manager.blocks[4].get_node("PictureSprite").visible, "Other location displays picture")
	check(manager.blocks[4].picture_texture != null, "Original picture resolves")
	check_native_image(manager.blocks[4].picture_texture.get_image(), "wr1_picture_gun")
	# The native player covers the left20pixels of this card; compare the
	# unobscured text and border instead of treating the player as card pixels.
	check_native_image(manager.blocks[0].original_word_sprite.texture.get_image().get_region(Rect2i(20, 0, 52, 18)), "wr1_word_cup_right")
	check_native_image(game.hud.original_top.get_region(Rect2i(79, 5, 24, 8)), "wr1_current_cup")
	var count_before: int = game.original_gruzzles.actors.size()
	manager.scan_original(target.x, target.y)
	check(model.mistakes == 1 and model.available(0), "Scene mismatch restores source")
	check(game.original_gruzzles.actors.size() == count_before + 1, "Scene mismatch spawns gruzzle")
	var spawned: Dictionary = game.original_gruzzles.actors[-1]
	check(Vector2i(spawned.gx, spawned.gy) == Vector2i(25, 13) and spawned.state == 64, "Mismatch spawn uses original grid and countdown")
	# Complete every word through real manager signals, reward handlers, HUD and door.
	while model.matched_count < 7:
		var slot: int = -1
		for candidate in range(7):
			if model.question_visible(candidate):
				slot = candidate
				break
		if slot < 0:
			check(false, "A source remains available")
			break
		source = model.slots[slot]
		target = model.slots[(slot + 5) % 7]
		manager.scan_original(source.x, source.y)
		manager.scan_original(target.x, target.y)
	check(manager.matched_count == 7, "Scene completes seven words")
	check(not game.exit_door.is_locked, "Seven matches unlock door")
	check_native_image(game.hud.original_top.get_region(Rect2i(144 + 23 * model.completion_order[4], 5, 24, 24)), "wr1_picture_gun")
	check(root.get_node("GameManager").score == 615 + 140, "Mistake suppresses perfect bonus through scene handlers")
	print("WR1 interactions: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
