extends SceneTree
const Render = preload("res://scripts/core/wr1_frontend_render.gd")
const Profiles = preload("res://scripts/core/wr1_profiles.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var output: String = args[args.find("--frontend-output")+1]
	Profiles.directory = output+"/profiles/"
	var context := {"words":["toe","pot","pen","rat","gun","cup","cop"],"character":1,"tileset":3,"mystery_word":"cup"}
	Render.menu(0,true).save_png(output+"/menu.png")
	Render.menu(2,true).save_png(output+"/menu_difficulty.png")
	Render.menu(10,false).save_png(output+"/menu_new_player.png")
	Render.selector("difficulty",0).save_png(output+"/difficulty.png")
	Render.sound(0).save_png(output+"/sound.png")
	Render.player_screen("name","",1,0,1).save_png(output+"/name.png")
	Render.player_screen("name","Dd",1,0,1,2).save_png(output+"/name_entered.png")
	Render.player_screen("character","Dd",1,0,1).save_png(output+"/character.png")
	Render.screen({"asset":"WR1.7","x":0,"y":0}).save_png(output+"/apogee.png")
	Render.screen(Render.metadata().startup.screens[0]).save_png(output+"/production.png")
	Render.screen(Render.metadata().startup.screens[3]).save_png(output+"/loading.png")
	for i in range(5): Render.screen(Render.metadata().story.screens[i]).save_png(output+"/story_%d.png" % i)
	Render.page("instructions",0,context).save_png(output+"/instructions_0.png")
	Render.page("instructions",2,context).save_png(output+"/instructions_2.png")
	for kind in ["instructions","ordering","about","bbs"]:
		for page in range(Render.metadata().pages[kind].size()):
			assert(Render.page(kind,page,context).save_png(output+"/%s_%d.png" % [kind,page]) == OK)
	var profile := {"level":5,"character":0,"word_cursor":28,"score":12345,
		"words":context.words,"difficulty":2,"custom_keys":true,"scancodes":[32,30,17,31,57],"joystick":false}
	Profiles.save_player("Reader",profile)
	var loaded := Profiles.load_player("READER")
	assert(loaded == profile,"Native profile round trip changed fields")
	assert(Profiles.decode(Profiles.encode(profile).slice(0,15)).is_empty())
	var other_episode := FileAccess.open(Profiles.directory+"visitor.wr2",FileAccess.WRITE)
	other_episode.store_buffer(Profiles.encode(profile))
	other_episode.close()
	var imported := Profiles.load_player("Visitor")
	assert(imported.level == 1 and imported.score == 0 and imported.character == profile.character)
	assert(imported.words == context.words and imported.difficulty == profile.difficulty and imported.scancodes == profile.scancodes)
	Profiles.update_high_score("Reader",100)
	Profiles.update_high_score("Other",100)
	Profiles.update_high_score("reader",50)
	assert(Profiles.high_scores()[0].name == "Reader" and Profiles.high_scores()[0].score == 100)
	Profiles.update_high_score("Other",200)
	assert(Profiles.high_scores()[0].name == "Other")
	change_scene_to_file("res://scenes/main_menu.tscn")
	await process_frame
	while current_scene == null: await process_frame
	var frontend: CanvasLayer = current_scene.get_child(current_scene.get_child_count()-1)
	assert(frontend.get_script().resource_path == "res://scripts/core/wr1_frontend.gd")
	# Preserve a sparse native file's row positions when displaying scores.
	Profiles.directory = output+"/native_scores/"
	DirAccess.make_dir_recursive_absolute(Profiles.directory)
	var native_scores := FileAccess.open(Profiles.directory+"high.wr1",FileAccess.WRITE)
	for i in range(10):
		if i == 8: native_scores.store_8(90)
		native_scores.store_8(0)
		native_scores.store_32(6596096 if i == 8 else 0)
	native_scores.close()
	frontend.open("high_scores")
	frontend.sprite.texture.get_image().save_png(output+"/high_scores.png")
	Profiles.directory = output+"/profiles/"
	frontend.open("redefine")
	var keys := [KEY_RIGHT,KEY_LEFT,KEY_UP,KEY_DOWN,KEY_SPACE]
	for i in range(6):
		frontend.sprite.texture.get_image().save_png(output+"/redefine_%d.png" % i)
		if i < 5: frontend.press(keys[i])
	frontend.press(KEY_N)
	frontend.open("joystick")
	frontend.sprite.texture.get_image().save_png(output+"/joystick.png")
	frontend.press(KEY_Y)
	assert(frontend.state == "joystick_center")
	frontend.press(KEY_J)
	assert(frontend.state == "menu")
	root.get_node("GameManager").original_joystick = false
	frontend.open("startup")
	frontend.index = 1
	frontend.redraw()
	frontend.sprite.texture.get_image().save_png(output+"/title.png")
	frontend.open("quit")
	frontend.sprite.texture.get_image().save_png(output+"/quit.png")
	frontend.open("name")
	frontend.press(KEY_A,97)
	frontend.press(KEY_B,98)
	frontend.press(KEY_HOME)
	frontend.press(KEY_DELETE)
	assert(frontend.name_input == "b" and frontend.name_cursor == 0)
	frontend.open("name")
	frontend.press(KEY_A,97)
	frontend.press(KEY_ENTER)
	assert(frontend.state == "character")
	frontend.press(KEY_RIGHT)
	frontend.press(KEY_ENTER)
	assert(frontend.state == "story")
	frontend.press(KEY_ESCAPE)
	assert(frontend.state == "menu")
	frontend.press(KEY_UP)
	assert(frontend.selection == 12)
	frontend.press(KEY_DOWN)
	assert(frontend.selection == 0)
	frontend.press(KEY_D)
	frontend.press(KEY_H)
	assert(frontend.state == "menu")
	frontend.press(KEY_I)
	assert(frontend.state == "instructions_help")
	frontend.sprite.texture.get_image().save_png(output+"/instructions_help.png")
	frontend.press(KEY_ENTER)
	assert(frontend.state == "instructions")
	frontend.press(KEY_ESCAPE)
	frontend.press(KEY_P)
	await process_frame
	while current_scene == null or not current_scene.has_method("is_replay_ready") or not current_scene.is_replay_ready():
		await process_frame
	var game := current_scene
	var word_list := Render.blank()
	game.draw_original_word_list(word_list)
	word_list.save_png(output+"/words.png")
	var gm := root.get_node("GameManager")
	assert(gm.original_character == 0 and gm.current_difficulty == 2)
	var start_x: int = game.player.original_state.x
	Input.action_press("move_right")
	await create_timer(0.3).timeout
	Input.action_release("move_right")
	assert(game.player.original_state.x != start_x)
	game.open_original_frontend()
	frontend = game.get_child(game.get_child_count()-1)
	if "--frontend-presented" in args:
		await RenderingServer.frame_post_draw
		var actual: Image = root.get_texture().get_image()
		actual.save_png(output+"/menu_presented.png")
	var before: Dictionary = game.original_interaction_snapshot()
	await create_timer(0.2).timeout
	assert(game.original_interaction_snapshot() == before,"Menu advanced the paused gameplay state")
	frontend.press(KEY_ESCAPE)
	assert(current_scene == game and game.replay_ready,"Resume replaced the active game")
	await process_frame
	game.open_original_frontend("sound")
	frontend = game.get_child(game.get_child_count()-1)
	frontend.press(KEY_3)
	assert(gm.original_sound == 2 and game.replay_ready)
	await process_frame
	game.open_original_frontend("redefine")
	frontend = game.get_child(game.get_child_count()-1)
	for key in [KEY_D,KEY_A,KEY_W,KEY_S,KEY_SPACE]: frontend.press(key)
	frontend.press(KEY_N)
	assert(not gm.original_custom_keys and gm.original_scancodes == [32,30,17,31,57])
	frontend.press(KEY_ESCAPE)
	await process_frame
	game.open_original_frontend("redefine")
	frontend = game.get_child(game.get_child_count()-1)
	for key in [KEY_D,KEY_A,KEY_W,KEY_S,KEY_SPACE]: frontend.press(key)
	frontend.press(KEY_Y)
	frontend.press(KEY_ESCAPE)
	await process_frame
	for pair in [[KEY_S,"move_down"],[KEY_W,"jump"],[KEY_UP,"jump"],[KEY_CTRL,"jump"],[KEY_ALT,"use_slime"]]:
		var event := InputEventKey.new()
		event.keycode = pair[0]
		event.physical_keycode = pair[0]
		event.pressed = true
		Input.parse_input_event(event)
		Input.flush_buffered_events()
		assert(Input.is_action_pressed(pair[1]) and game.replay_ready,"Remapping opened a shortcut or disabled default controls")
		event = event.duplicate()
		event.pressed = false
		Input.parse_input_event(event)
		Input.flush_buffered_events()
	preload("res://scripts/core/wr1_controls.gd").apply([17,30,17,31,57])
	var duplicate := InputEventKey.new()
	duplicate.physical_keycode = KEY_W
	assert(duplicate.is_action("jump") and not duplicate.is_action("move_right"),"Duplicate keys lost original ISR priority")
	preload("res://scripts/core/wr1_controls.gd").apply(gm.original_scancodes)
	gm.score = 1234
	gm.current_level = 15
	game.original_door_state = 2
	game.finish_original_exit({"up":false,"down":false,"left":false,"right":false,"slime_request":false},-1)
	assert(gm.current_level == 16)
	frontend = game.get_child(game.get_child_count()-1)
	for i in range(3):
		assert(frontend.state == "ending" and frontend.index == i)
		frontend.sprite.texture.get_image().save_png(output+"/ending_%d.png" % i)
		frontend.press(KEY_ENTER)
	assert(frontend.state == "ordering" and gm.score == 0 and gm.current_level == 1)
	assert(Profiles.high_scores()[0].score == 1234)
	frontend.press(KEY_ESCAPE)
	frontend.press(KEY_ENTER)
	await process_frame
	while current_scene == null or not current_scene.is_replay_ready(): await process_frame
	assert(current_scene != game,"Ending returned to the completed level")
	assert(gm.current_level == 1 and gm.score == 0 and current_scene.original_loaded_profile.level == 1)
	var completed_game := current_scene
	completed_game.open_original_frontend()
	frontend = completed_game.get_child(completed_game.get_child_count()-1)
	frontend.activate("new_player")
	for code in "reader".to_ascii_buffer(): frontend.press(code-32,code)
	frontend.press(KEY_ENTER)
	assert(frontend.state == "menu" and frontend.selection == 10 and gm.score == 12345)
	frontend.press(KEY_P)
	await process_frame
	while current_scene == null or not current_scene.is_replay_ready(): await process_frame
	assert(current_scene != completed_game and gm.current_level == 5 and gm.score == 12345)
	assert(Profiles.load_player("Reader").score == 12345,"Old game overwrote the selected player's save")
	print("Original frontend pages, native profiles, resume, controls and ending PASS")
	quit()
