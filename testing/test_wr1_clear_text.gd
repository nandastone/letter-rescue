extends SceneTree
## Exercise both actual display paths with the same paused gameplay state.
var output: String

func _initialize() -> void:
	run.call_deferred()

func capture(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	assert(root.get_texture().get_image().save_png(output + "/" + name + ".png") == OK)

func run() -> void:
	var args := OS.get_cmdline_user_args()
	output = args[args.find("--clear-output") + 1]
	var clear := preload("res://scripts/wr1_clear_text.gd").enabled()
	root.get_node("GameManager").progress_path = output + "/progress.json"
	preload("res://scripts/wr1_profiles.gd").directory = output + "/profiles/"
	var replay := root.get_node("InputReplay")
	replay.mode = replay.Mode.REPLAYING # Fixtures begin after loading.
	paused = true
	change_scene_to_file("res://scenes/game.tscn")
	while current_scene == null or not current_scene.is_replay_ready(): await process_frame
	var game = current_scene
	var before := JSON.stringify([game.player.original_state.snapshot(), game.original_interaction_snapshot()])
	var reference: Image = game.original_presentation.rasterize()
	assert(reference.get_size() == Vector2i(320, 200))
	reference.save_png(output + "/reference.png")
	game.hud.show_current_word("elephant")
	game.hud.setup_mystery_word("rabbit", 2)
	game.original_presentation.output_texture.update(game.original_presentation.rasterize())
	await capture("reading")
	if clear:
		game.hud.show_current_word("gypqj")
		game.hud.setup_mystery_word("gypqj", 5)
		var reference_layer := CanvasLayer.new()
		reference_layer.layer = 90
		game.add_child(reference_layer)
		var panel := ColorRect.new()
		panel.position = Vector2(59, 40)
		panel.size = Vector2(69, 40)
		panel.color = Color8(0, 170, 170)
		panel.visibility_layer = 2
		reference_layer.add_child(panel)
		var full_label := Label.new()
		full_label.text = "gypqj"
		full_label.position = panel.position
		full_label.size = panel.size
		full_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		full_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		full_label.add_theme_font_override("font", preload("res://assets/fonts/andika/Andika-Regular.ttf"))
		full_label.add_theme_font_size_override("font_size", game.hud.clear_text.current.layout().pixels)
		full_label.visibility_layer = 2
		reference_layer.add_child(full_label)
		var bonus_panel := panel.duplicate()
		bonus_panel.position.x = 128
		bonus_panel.size.x = 64
		reference_layer.add_child(bonus_panel)
		var bonus_label := full_label.duplicate()
		bonus_label.position.x = 128
		bonus_label.size.x = 64
		bonus_label.add_theme_font_size_override("font_size", game.hud.clear_text.mystery.layout().pixels)
		reference_layer.add_child(bonus_label)
		await capture("descenders")
		reference_layer.free()
		game.hud.show_current_word("elephant")
		game.hud.setup_mystery_word("rabbit", 2)
	if clear:
		assert(root.get_texture().get_size().x > 320, "Text must render above the original resolution")
		assert(game.hud.clear_text.current.word == "elephant")
		assert(game.hud.clear_text.mystery.prefix == 2)
		assert(not game.hud.clear_text.mystery.hide_suffix)
		assert(game.original_presentation.reference_viewport.gui_disable_input)
		var letters := 0
		for entity in game.entities.get_children():
			if entity.has_node("ClearLetter"):
				letters += 1
				assert(entity.get_node("ClearLetter").word == entity.data.to_lower())
		assert(letters > 0)
	root.get_node("GameManager").current_difficulty = 2
	game.hud.setup_mystery_word("rabbit", 2)
	if clear: assert(game.hud.clear_text.mystery.hide_suffix)
	await capture("hard_hidden")
	game.hud._draw_mystery(true)
	game.hud.update_mystery_letter(2)
	if clear:
		assert(not game.hud.clear_text.mystery.hide_suffix, "Book hint must survive collecting another letter")
		assert(game.hud.clear_text.mystery.prefix == 3)
	await capture("hard_hint")
	game.hud.hide_current_word()
	if clear: assert(game.hud.clear_text.current.word.is_empty())
	var old_camera: Vector2 = game.camera.global_position
	for entity in game.entities.get_children():
		if entity.get("type") == "letter":
			game.camera.global_position = entity.global_position + Vector2(8, -24)
			game.camera.force_update_scroll()
			await capture("letters")
			break
	game.camera.global_position = old_camera
	game.camera.force_update_scroll()
	root.get_node("GameManager").current_difficulty = 0
	assert(before == JSON.stringify([game.player.original_state.snapshot(), game.original_interaction_snapshot()]), "Reading presentation mutated gameplay")
	# Exercise the actual world-card and reward/recap presentation paths as well
	# as the HUD. Their reference pixels must remain identical in both modes.
	var block = game.word_manager.blocks[0]
	block.show_word()
	game.hud.update_score(12345)
	game.original_presentation.rasterize().save_png(output + "/cards_reference.png")
	await capture("cards")
	block.reset_to_idle()
	var recap := preload("res://scripts/wr1_recap_view.gd").new()
	game.add_child(recap)
	recap.configure(game.hud, ["gypqj"])
	recap.present({"kind":"helper", "frame":0, "order":0, "word_index":0, "position":Vector2(64,100)})
	game.original_presentation.rasterize().save_png(output + "/recap_reference.png")
	await capture("recap")
	for i in range(20): recap.present({"kind":"dissolve", "frame":0, "position":Vector2(64,100), "pixels":[]})
	if clear: assert(recap.panel_sprite.get_meta("reading_view").get_child(0).modulate.a < 0.001)
	recap.free()
	var old_door: Vector2 = game.exit_door.position
	game.exit_door.position = game.player.position + Vector2(32,0)
	game.exit_door.present_original_frame(0,true,0)
	game.original_presentation.rasterize().save_png(output + "/bonus_reference.png")
	await capture("bonus")
	game.exit_door.position = old_door
	if clear:
		var titles: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_titles.json"))
		var longest := 0
		for i in range(titles.titles.size()):
			if titles.titles[i].name.length() > titles.titles[longest].name.length(): longest = i
		var title := preload("res://scripts/wr1_level_title.gd").new()
		game.add_child(title)
		title.configure(longest + 1)
		await capture("level_title")
		title.free()
		preload("res://scripts/wr1_profiles.gd").update_high_score("gypqj Reader",12345)
	var frontend = load("res://scripts/wr1_frontend.gd").new()
	game.add_child(frontend)
	frontend.begin("words", game)
	await capture("words")
	if clear: assert(frontend.get_node("ClearPage").get_child_count() == 7)
	frontend.open("menu")
	assert(not frontend.has_node("ClearWords"), "Reading list leaked onto another menu")
	await capture("menu")
	if clear:
		frontend.set_art_visible(false)
		assert(not frontend.get_node("ClearPage").visible, "Menu text leaked into attract gameplay")
		frontend.set_art_visible(true)
		for kind in ["apogee", "startup", "name", "character", "resume", "difficulty", "instructions", "ordering", "about", "bbs", "story", "ending", "redefine", "joystick", "joystick_center", "high_scores", "help", "sound", "quit"]:
			var count := 1
			var metadata: Dictionary = preload("res://scripts/wr1_frontend_render.gd").metadata()
			if metadata.pages.has(kind): count = metadata.pages[kind].size()
			elif kind in ["startup", "story", "ending"]: count = metadata[kind].screens.size()
			frontend.state = kind
			if kind == "name":
				frontend.name_input = "gypqj Reader"
				frontend.name_cursor = frontend.name_input.length()
			for page_index in range(count):
				frontend.index = page_index
				frontend.redraw()
				assert(frontend.get_node("ClearPage").get_child_count() > 0, "Missing readable text: " + kind)
				await capture("page_%s_%d" % [kind, page_index])
		root.size = Vector2i(960, 600)
		frontend.open("words")
		await capture("words_resized")
		assert(root.get_texture().get_image().get_size() == Vector2i(960, 600))
		var before_resize: Image = game.original_presentation.rasterize()
		root.size = Vector2i(1000, 600)
		await process_frame
		game.camera.force_update_scroll()
		assert(game.original_presentation.rasterize().get_data() == before_resize.get_data(), "Window aspect ratio changed the original projection")
		await capture("words_letterboxed")
	print("Clear Text display, original capture, hidden letters, hint persistence and word list PASS")
	quit()
