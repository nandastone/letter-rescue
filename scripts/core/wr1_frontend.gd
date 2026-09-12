extends CanvasLayer
## Original menu/startup flow. A live game is suspended, never reconstructed to resume.
const Render = preload("res://scripts/core/wr1_frontend_render.gd")
const Profiles = preload("res://scripts/core/wr1_profiles.gd")
const Controls = preload("res://scripts/core/wr1_controls.gd")
var state := "menu"
var index := 0
var selection := 0
var menu_selection := 0
var previous_difficulty := 0
var name_input := ""
var name_cursor := 0
var first_player := true
var game: Node
var was_ready := false
var old_process_mode: int
var sprite := Sprite2D.new()
var timer := 0.0
var redefine_codes: Array = []
var demo_game: Node
var demo_index := 0
var demo_backup: Dictionary = {}
var session_backup: Dictionary = {}
var hidden_layers: Array[CanvasLayer] = []
var backdrop: Image

func set_art_visible(value: bool) -> void:
	sprite.visible = value
	for child_name in ["ClearPage"]:
		var child := get_node_or_null(child_name)
		if child != null: child.visible = value

func _ready() -> void:
	preload("res://scripts/core/wr1_clear_text.gd").configure_window(get_window())
	layer = 120
	process_mode = Node.PROCESS_MODE_ALWAYS
	sprite.centered = false
	sprite.visibility_layer = 2
	add_child(sprite)
	set_process(false)

func begin(kind: String = "startup", live_game: Node = null) -> void:
	game = live_game
	first_player = kind == "startup"
	if game != null:
		if game.original_presentation != null:
			var frame: Image = game.original_presentation.frame_image()
			if frame != null:
				backdrop = frame
		was_ready = game.replay_ready
		old_process_mode = game.process_mode
		game.replay_ready = false
		game.process_mode = Node.PROCESS_MODE_DISABLED
		game.save_original_profile()
		if kind in ["words","help","sound"] and AudioManager.original != null:
			AudioManager.original.stop_effect()
	if kind == "startup":
		AudioManager.begin_original_level(1)
		apply_sound()
		if "--skip-intro" in LaunchArgs.user_args():
			kind = "name"
		else:
			kind = "apogee"
	open(kind)

func open(kind: String) -> void:
	state = kind
	index = 0
	timer = 0.0
	set_process(state in ["startup","apogee"])
	if kind == "difficulty":
		previous_difficulty = GameManager.current_difficulty
		selection = previous_difficulty
	elif kind == "sound":
		selection = GameManager.original_sound
	elif kind == "name":
		name_input = ""
		name_cursor = 0
	elif kind == "redefine":
		redefine_codes.clear()
	elif kind == "menu":
		selection = menu_selection
	elif kind == "ending":
		AudioManager.begin_original_level(2)
	redraw()

func _process(delta: float) -> void:
	timer += delta
	if state == "startup":
		var seconds: float = Render.metadata().startup.screens[index].threshold_seconds
		if timer > seconds:
			advance_startup()
	elif state == "apogee" and timer > 1.0:
		open("startup") # The original shows this image during initialization.
	elif state == "demo_title" and timer >= 7.0:
		state = "demo_story"
		index = 0
		timer = 0.0
		redraw()
	elif state == "demo_story" and timer >= 10.0:
		index += 1
		timer = 0.0
		if index >= 5: launch_next_demo()
		else: redraw()

func advance_startup() -> void:
	index += 1
	timer = 0.0
	if index >= Render.metadata().startup.screens.size():
		open("name")
	else:
		redraw()

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		get_viewport().set_input_as_handled()
		if state == "redefine" and event.keycode == KEY_SHIFT and event.location != KEY_LOCATION_RIGHT: return
		press(event.keycode if event.keycode != 0 else event.physical_keycode, event.unicode)
	elif event is InputEventJoypadButton and event.pressed:
		get_viewport().set_input_as_handled()
		var keys := {JOY_BUTTON_DPAD_UP:KEY_UP,JOY_BUTTON_DPAD_DOWN:KEY_DOWN,
			JOY_BUTTON_DPAD_LEFT:KEY_LEFT,JOY_BUTTON_DPAD_RIGHT:KEY_RIGHT,JOY_BUTTON_BACK:KEY_ESCAPE}
		press(keys.get(event.button_index,KEY_ENTER))

func press(key: int, unicode: int = 0) -> void:
	if state.begins_with("demo"):
		if state == "demo_stopping": return
		finish_demos()
		return
	match state:
		"apogee": open("startup")
		"startup": advance_startup()
		"name":
			if key == KEY_ENTER and not name_input.is_empty():
				accept_name()
			elif key == KEY_BACKSPACE:
				if name_cursor > 0:
					name_input = name_input.left(name_cursor-1)+name_input.substr(name_cursor)
					name_cursor -= 1
			elif key == KEY_DELETE:
				name_input = name_input.left(name_cursor)+name_input.substr(name_cursor+1)
			elif key == KEY_LEFT: name_cursor = maxi(0,name_cursor-1)
			elif key == KEY_RIGHT: name_cursor = mini(name_input.length(),name_cursor+1)
			elif key == KEY_HOME: name_cursor = 0
			elif key == KEY_END: name_cursor = name_input.length()
			elif unicode >= 32 and unicode < 127:
				var updated := Profiles.normalized_name(name_input.left(name_cursor)+String.chr(unicode)+name_input.substr(name_cursor))
				if updated != name_input:
					name_cursor = mini(name_cursor+1,8)
					name_input = updated
		"character":
			if key == KEY_LEFT: GameManager.original_character = 1
			elif key == KEY_RIGHT: GameManager.original_character = 0
			elif key == KEY_ENTER:
				open("story" if first_player else "menu")
				first_player = false
			elif key == KEY_Q: open("quit")
		"resume":
			open("story" if first_player else "menu")
			first_player = false
		"menu":
			if key == KEY_UP: selection = posmod(selection-1,13)
			elif key == KEY_DOWN: selection = posmod(selection+1,13)
			elif key == KEY_ENTER: activate(Render.metadata().menu.entries[selection].action)
			else:
				for entry in Render.metadata().menu.entries:
					for shortcut in entry.keys:
						if (shortcut == "Escape" and key == KEY_ESCAPE) or (shortcut.length() == 1 and key == shortcut.unicode_at(0)):
							activate(entry.action)
		"difficulty":
			if key == KEY_UP: selection = maxi(0,selection-1)
			elif key == KEY_DOWN: selection = mini(2,selection+1)
			elif key in [KEY_ENTER,KEY_ESCAPE,KEY_E,KEY_M,KEY_H]:
				if key == KEY_ESCAPE: selection = previous_difficulty
				elif key == KEY_E: selection = 0
				elif key == KEY_M: selection = 1
				elif key == KEY_H: selection = 2
				GameManager.current_difficulty = selection
				if game != null: game.apply_original_difficulty(selection)
				InputReplay.record_setting("difficulty",selection)
				selection = 0
				open("menu")
		"sound":
			if key == KEY_UP: selection = maxi(0,selection-1)
			elif key == KEY_DOWN: selection = mini(2,selection+1)
			elif key in [KEY_ENTER,KEY_ESCAPE,KEY_1,KEY_2,KEY_3]:
				if key in [KEY_1,KEY_2,KEY_3]: selection = key - KEY_1
				GameManager.original_sound = selection
				apply_sound()
				resume_game()
		"instructions", "ordering", "about", "bbs":
			index += 1
			if key == KEY_ESCAPE or index >= Render.metadata().pages[state].size(): open("menu")
		"instructions_help":
			open("menu" if key == KEY_ESCAPE else "instructions")
		"story":
			index += 1
			if key == KEY_ESCAPE or index >= 5: open("menu")
		"ending":
			index += 1
			if index >= 3:
				Profiles.update_high_score(GameManager.original_player_name,GameManager.score)
				GameManager.current_level = 1
				GameManager.score = 0
				if game != null and game.original_words != null:
					game.original_words.next_words(game.original_gruzzles.random_word)
					game.save_original_profile()
				GameManager.original_pending_profile = Profiles.load_player(GameManager.original_player_name)
				open("ordering")
		"high_scores": open("menu")
		"help", "words": resume_game()
		"joystick":
			GameManager.original_joystick = key == KEY_Y
			open("joystick_center" if GameManager.original_joystick else "menu")
		"joystick_center":
			calibrate_joystick()
			open("menu")
		"redefine":
			if redefine_codes.size() < 5:
				var scan := Controls.scan_for_key(key)
				if scan >= 0:
					redefine_codes.append(scan)
					if redefine_codes.size() == 5:
						GameManager.original_scancodes = redefine_codes.duplicate()
						Controls.apply(redefine_codes)
			else:
				GameManager.original_custom_keys = key == KEY_Y
				Controls.apply(GameManager.original_scancodes if GameManager.original_custom_keys else Controls.DEFAULTS)
				open("menu")
		"quit":
			if key == KEY_Q:
				if game != null: game.save_original_profile()
				get_tree().quit()
			elif key == KEY_ESCAPE: resume_game()
	if is_inside_tree(): redraw()

func activate(action: String) -> void:
	for i in range(Render.metadata().menu.entries.size()):
		if Render.metadata().menu.entries[i].action == action:
			menu_selection = i
	match action:
		"play": resume_game()
		"new_player":
			if game != null: game.save_original_profile()
			open("name")
		"demo": begin_demos()
		"instructions": open("instructions_help")
		_: open(action)

func accept_name() -> void:
	if name_input.to_lower() == "q":
		get_tree().quit()
		return
	GameManager.original_player_name = name_input
	GameManager.original_pending_profile = Profiles.load_player(name_input)
	var profile := GameManager.original_pending_profile
	GameManager.restart_game()
	GameManager.original_character = 1
	GameManager.original_scancodes = Controls.DEFAULTS.duplicate()
	GameManager.original_custom_keys = false
	GameManager.original_joystick = false
	GameManager.original_joystick_center = Vector2.ZERO
	if not profile.is_empty():
		GameManager.current_level = int(profile.level)
		GameManager.score = int(profile.score)
		GameManager.original_character = int(profile.character)
		GameManager.current_difficulty = int(profile.difficulty)
		GameManager.original_scancodes = profile.scancodes.duplicate()
		GameManager.original_custom_keys = profile.custom_keys
		GameManager.original_joystick = profile.joystick
		if profile.joystick: calibrate_joystick()
	# Selecting a new player must start/load their level, not resume the old one.
	if game != null:
		game.set_meta("frontend_replaced",true)
	if profile.is_empty(): open("character")
	else: open("resume" if first_player else "menu")

func resume_game() -> void:
	if game != null and not game.has_meta("frontend_replaced") and GameManager.current_level <= 15 and game.original_door_state != 2:
		game.process_mode = old_process_mode
		game.replay_ready = was_ready
		queue_free()
		return
	InputReplay.replay_character = "girl" if GameManager.original_character == 1 else "boy"
	Controls.apply(GameManager.original_scancodes if GameManager.original_custom_keys else Controls.DEFAULTS)
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func apply_sound() -> void:
	if AudioManager.original != null:
		AudioManager.original.set_music_enabled(GameManager.original_sound == 0)
		AudioManager.original.set_effects_enabled(GameManager.original_sound < 2)

func calibrate_joystick() -> void:
	GameManager.original_joystick_center = Vector2.ZERO
	var devices := Input.get_connected_joypads()
	if not devices.is_empty():
		GameManager.original_joystick_center = Vector2(Input.get_joy_axis(devices[0],JOY_AXIS_LEFT_X),Input.get_joy_axis(devices[0],JOY_AXIS_LEFT_Y))

func redraw() -> void:
	Render.begin_reading(preload("res://scripts/core/wr1_clear_text.gd").enabled())
	var result: Image
	match state:
		"apogee": result = Render.screen({"asset":"WR1.7","x":0,"y":0})
		"startup", "demo_title":
			var stage := 1 if state == "demo_title" else index
			result = Render.screen(Render.metadata().startup.screens[stage])
			if stage == 1:
				for row in Render.metadata().startup.title_overlays:
					Render.text(result,row.text,int(row.x),int(row.y),int(row.color),11 if row.text == "SHAREWARE" else 9)
		"name", "character", "resume":
			result = Render.player_screen(state,name_input,GameManager.original_character,GameManager.score,GameManager.current_level,name_cursor)
		"menu": result = Render.menu(selection,game != null and not game.has_meta("frontend_replaced"))
		"difficulty": result = Render.selector("difficulty",selection)
		"instructions", "ordering", "about", "bbs": result = Render.page(state,index,page_context())
		"story", "ending": result = Render.screen(Render.metadata()[state].screens[index])
		"demo_story": result = Render.screen(Render.metadata().story.screens[index])
		"redefine":
			result = Render.selector("redefine",0)
			for i in range(mini(redefine_codes.size()+1,5)):
				var row: Dictionary = Render.metadata().redefine.prompts[i]
				Render.text(result,row.text,int(row.x),int(row.y),4)
				if i < redefine_codes.size(): Render.text(result,Render.metadata().redefine.key_names[redefine_codes[i]],224,int(row.y),4)
			if redefine_codes.size() == 5: Render.text(result,"Save this? (Y/N)",80,136,4)
		"joystick", "joystick_center":
			result = Render.blank(7)
			result.fill_rect(Rect2i(36,58,248,27),Render.PALETTE[11])
			Render.outline(result,Rect2i(36,58,248,27),4)
			var row: Dictionary = Render.metadata().joystick.question if state == "joystick" else Render.metadata().joystick.calibration
			Render.text(result,row.text,int(row.x),int(row.y),4,11)
			Render.align_reading(Rect2(37,59,246,25), HORIZONTAL_ALIGNMENT_CENTER, 10)
		"high_scores":
			result = Render.blank()
			result.fill_rect(Rect2i(60,20,195,141),Render.PALETTE[9])
			Render.outline(result,Rect2i(60,20,195,141),15)
			Render.text(result,"High Scores",106,28,15,9)
			Render.align_reading(Rect2(61,23,193,18), HORIZONTAL_ALIGNMENT_CENTER, 10)
			var scores := Profiles.high_scores()
			for i in range(scores.size()):
				if scores[i].score > 0:
					Render.text(result,scores[i].name,68,44+i*10,15,9)
					var value := str(scores[i].score)
					Render.text(result,value,248-value.length()*8,44+i*10,15,9)
					Render.align_reading(Rect2(248-value.length()*8,43+i*10,value.length()*8,10), HORIZONTAL_ALIGNMENT_RIGHT, 8)
		"help", "instructions_help":
			result = backdrop.duplicate() if state == "help" and backdrop != null else Render.blank()
			result.blit_rect(Render.display_asset("HELP.WR"),Rect2i(0,0,168,176),Vector2i(72,16))
			Render.reading_asset("HELP.WR",72,16)
		"sound":
			result = Render.sound(selection,backdrop)
		"words":
			result = backdrop.duplicate() if backdrop != null else Render.blank()
			if game != null: game.draw_original_word_list(result)
		"quit":
			result = backdrop.duplicate() if backdrop != null else Render.blank()
			result.fill_rect(Rect2i(60,58,197,27),Render.PALETTE[11])
			Render.outline(result,Rect2i(60,58,197,27),0)
			Render.text(result,"Press 'Q' to quit",88,62,0,11)
			Render.align_reading(Rect2(61,59,195,12))
			Render.text(result,"'ESC' to return to game",64,72,0,11)
			Render.align_reading(Rect2(61,71,195,12))
		"demo", "demo_transition", "demo_stopping":
			Render.reading = false
			return
		_: result = Render.blank()
	if preload("res://scripts/core/wr1_clear_text.gd").enabled():
		result = preload("res://scripts/core/wr1_clear_text.gd").word_list(self, result)
		preload("res://scripts/core/wr1_clear_text.gd").frontend_labels(self, Render.reading_runs)
	Render.reading = false
	sprite.texture = ImageTexture.create_from_image(result)

func page_context() -> Dictionary:
	var words: Array = []
	var tileset := 3
	if game != null and game.original_words != null:
		words = game.original_words.words
		tileset = int(game.level_data.tileset)
	elif not GameManager.original_pending_profile.is_empty():
		words = GameManager.original_pending_profile.words
	else:
		var initial := preload("res://scripts/core/wr1_words.gd").new()
		initial.next_words()
		words = initial.words
	return {"words":words,"tileset":tileset,"character":GameManager.original_character,
		"mystery_word":game.original_letters.word if game != null and game.original_letters != null else words[0],
		"background_color":int(game.level_data.bg_colour_ega) if game != null else 11}

func begin_demos() -> void:
	# Save the paused live session independently from each demo's initial state.
	demo_backup.clear()
	for property in InputReplay.get_property_list():
		if int(property.usage) & PROPERTY_USAGE_SCRIPT_VARIABLE and property.name not in ["ACTIONS"]:
			var value = InputReplay.get(property.name)
			demo_backup[property.name] = value.duplicate(true) if value is Array or value is Dictionary else value
	session_backup = {"level":GameManager.current_level,"difficulty":GameManager.current_difficulty,"score":GameManager.score,
		"speed":GameManager.original_speed_ticks,"profile":GameManager.original_pending_profile.duplicate(true)}
	if AudioManager.original != null:
		session_backup.music_position = AudioManager.original.music.get_playback_position()
	GameManager.original_demo_host = self
	demo_index = maxi(0,GameManager.current_level-1)
	state = "demo"
	set_art_visible(false)
	if game != null: game.hide()
	if game != null:
		for node in game.find_children("*","CanvasLayer",true,false):
			if node != self and node.visible:
				hidden_layers.append(node)
				node.hide()
	next_demo(false)

func next_demo(interlude: bool = true) -> void:
	state = "demo_transition"
	if is_instance_valid(demo_game):
		demo_game.queue_free()
		await get_tree().process_frame
	if GameManager.original_demo_host != self: return
	if interlude:
		AudioManager.begin_original_level(GameManager.current_level)
		state = "demo_title"
		timer = 0.0
		set_art_visible(true)
		set_process(true)
		redraw()
	else:
		launch_next_demo()

func launch_next_demo() -> void:
	set_process(false)
	state = "demo"
	set_art_visible(false)
	var level: int = int(Render.metadata().demo_order[demo_index % 15])
	InputReplay._start_replay("res://data/wr1/demos/level%d.json" % level)
	demo_index += 1

func launch_demo_game() -> void:
	# Each recording has its own initial music-driver checkpoint.
	AudioManager.end_original_session()
	demo_game = load("res://scenes/game.tscn").instantiate()
	get_tree().root.add_child(demo_game)
	get_tree().current_scene = demo_game

func finish_demos() -> void:
	state = "demo_stopping"
	set_process(false)
	GameManager.original_demo_host = null
	if is_instance_valid(demo_game):
		demo_game.queue_free()
		await get_tree().process_frame
	for key in demo_backup: InputReplay.set(key,demo_backup[key])
	GameManager.current_level = session_backup.level
	GameManager.current_difficulty = session_backup.difficulty
	GameManager.score = session_backup.score
	GameManager.original_speed_ticks = session_backup.speed
	GameManager.original_pending_profile = session_backup.profile
	get_tree().current_scene = game if game != null else get_parent()
	if game != null:
		game.show()
		game.camera.make_current()
		for node in hidden_layers:
			if is_instance_valid(node): node.show()
		hidden_layers.clear()
		if game.original_presentation.enabled: game.get_viewport().canvas_cull_mask = game.original_presentation.display_mask()
	AudioManager.begin_original_level(GameManager.current_level)
	if session_backup.has("music_position") and AudioManager.original.enabled:
		AudioManager.original.music.seek(session_backup.music_position)
	apply_sound()
	set_art_visible(true)
	selection = 0
	open("menu")
