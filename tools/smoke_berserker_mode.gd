extends SceneTree
## Focused smoke test for the default game's cheat codes and hidden mode.
##
##   godot --headless --fixed-fps 120 --path . \
##     --script tools/smoke_berserker_mode.gd -- \
##     --original-seed 20716

var waited := 0
var warp_waited := 0
var warp_game: Node
var warp_mode: Node


func _initialize() -> void:
	change_scene_to_file.call_deferred("res://scenes/game.tscn")
	process_frame.connect(_check)


func _check() -> void:
	waited += 1
	var game := current_scene
	if game == null or not game.has_method("is_replay_ready") or not game.is_replay_ready():
		if waited > 2400:
			_fail("game never became ready")
		return
	process_frame.disconnect(_check)
	if not _speed_check():
		return
	var mode: Node = game.berserker_mode
	if mode == null or mode.active:
		_fail("default game did not create an inactive berserker mode")
		return
	var initial_character: String = game.player.original_character
	game.player.original_character = "girl" # Retain coverage of the legacy 28-frame sheet.
	_type_code(mode, "IDKFA")
	if not mode.active or not mode.tint.visible or game.player.original_sprite.hframes != 28:
		_fail("IDKFA did not enable the visuals")
		return

	var p: RefCounted = game.player.original_state
	var direction := -1 if p.facing == 1 else 1
	var target_x: int = p.gx + direction * 10
	var timer_count: int = game.original_gruzzles.timers.size()
	game.original_gruzzles.actors.append({"gx": target_x, "gy": p.gy, "type": 0,
		"state": -1, "animation_index": 0, "jump_phase": -1})
	var target_at := Vector2(target_x * 8, p.gy * 8 - 23)
	game.original_gruzzles.draws.append({"kind":"gruzzle", "type":0, "frame":0, "position":target_at})
	var manager := root.get_node("GameManager")
	var score_before: int = manager.score
	var sound_before: int = manager.original_sound
	manager.original_sound = 2 # Headless AudioServer retains a playing WAV at shutdown.
	game._try_use_slime()
	manager.original_sound = sound_before
	for actor in game.original_gruzzles.actors:
		if int(actor.gx) == target_x and int(actor.gy) == p.gy:
			_fail("shotgun left its guaranteed target alive")
			return
	if manager.score <= score_before:
		_fail("shotgun hit did not award points")
		return
	if game.original_gruzzles.timers.size() != timer_count:
		_fail("shotgun compacted the engine's fixed actor cadence slots")
		return
	if mode.can_fire() or mode.particles.size() < 10 or game.player.original_sprite.frame != 26:
		_fail("shot did not produce recoil, gibs and cooldown")
		return
	for draw in game.original_gruzzles.draws:
		if draw.position == target_at:
			_fail("dead Gruzzle remained in the cached draw list")
			return
	mode._process(0.19)
	mode._process(0.0)
	var shells := 0
	for particle in mode.particles:
		if particle.node.texture == mode.shell_texture:
			shells += 1
	if shells != 1 or game.player.original_sprite.frame != 27:
		_fail("pump pose and exactly one ejected shell were not synchronized")
		return
	mode._process(0.45)
	if not mode.can_fire():
		_fail("shotgun never finished its pump cycle")
		return
	if not _boy_pose_check(mode):
		return
	var facing: int = p.facing
	p.facing = 1
	p.frame = 0
	mode.present_player()
	if not game.player.original_sprite.flip_h:
		_fail("idle shotgun pose ignored left-facing direction")
		return
	p.facing = facing
	mode.present_player()
	mode.banner_seconds = 0
	mode._process(0.0)
	if mode.banner.visible:
		_fail("activation banner stayed visible")
		return
	game.player.is_dead = true
	mode._process(0.0)
	if mode.can_fire() or mode.tint.visible or game.player.original_sprite.hframes != 26:
		_fail("rescue state retained armed visuals or allowed shooting")
		return
	game.player.is_dead = false
	game.player.original_character = initial_character
	mode.present_player()
	# A fresh shot gives optional visual QA a recoil/fragment frame.
	mode.fire([{"type":0,"frame":0,"position":target_at}])
	mode._process(0.04)
	var args := OS.get_cmdline_user_args()
	if "--capture-ready" in args:
		mode._clear_particles()
		mode.shot_age = mode.SHOT_SECONDS
		mode._process(0.0)
	var screenshot_arg := args.find("--screenshot")
	if screenshot_arg >= 0 and screenshot_arg + 1 < args.size():
		var screenshot_path: String = args[screenshot_arg + 1]
		RenderingServer.frame_post_draw.connect(func() -> void:
			var image := root.get_texture().get_image()
			if image == null or image.save_png(screenshot_path) != OK:
				_fail("could not save the requested screenshot")
				return
			_finish(mode), CONNECT_ONE_SHOT)
		return
	_finish(mode)


func _finish(mode: Node) -> void:
	_type_code(mode, "IDKFA")
	if mode.active or mode.tint.visible or current_scene.player.original_sprite.hframes != 26 or not mode.particles.is_empty():
		_fail("second IDKFA did not disable the mode")
		return
	var game := current_scene
	game.original_gruzzles.slime_used = 5
	game.hud.update_original_slime(5)
	_chord(mode, KEY_P, KEY_S)
	if game.original_gruzzles.slime_used != 0 or game.hud.original_slime_used != 0:
		_fail("P+S did not refill slime")
		return
	_chord(mode, KEY_L, KEY_Z)
	if not mode.warp_entry or game.player.is_physics_processing():
		_fail("L+Z did not pause play for level entry")
		return
	_key(mode, KEY_ESCAPE)
	if mode.warp_entry or not game.player.is_physics_processing():
		_fail("Escape did not cancel level entry")
		return
	_chord(mode, KEY_L, KEY_Z)
	_key(mode, KEY_1, 49)
	_key(mode, KEY_4, 52)
	_key(mode, KEY_ENTER)
	var manager := root.get_node("GameManager")
	if mode.warp_entry or manager.current_level != 14 or game.replay_ready:
		_fail("level 14 warp did not begin a fresh load")
		return
	warp_game = game
	warp_mode = mode
	process_frame.connect(_check_warp)


func _check_warp() -> void:
	warp_waited += 1
	if warp_game.original_level_title != null and warp_game.original_level_title.waiting:
		warp_game.original_level_title._dismiss()
	if not warp_game.replay_ready:
		if warp_waited > 2400:
			_fail("level warp never became ready")
		return
	process_frame.disconnect(_check_warp)
	if warp_game.level_data.get("name") != "Level 14":
		_fail("level warp loaded the wrong map")
		return
	print("cheat smoke: berserker art/effects, slime refill, cancel and level warp passed")
	for player in [warp_mode.shot_player, warp_mode.pump_player, warp_mode.gib_player]:
		player.stop()
		player.stream = null
	current_scene.queue_free()
	process_frame.connect(_quit_after_cleanup, CONNECT_ONE_SHOT)


func _quit_after_cleanup() -> void:
	process_frame.connect(func() -> void: quit(0), CONNECT_ONE_SHOT)


func _type_code(mode: Node, code: String) -> void:
	for letter in code:
		_key(mode, letter.unicode_at(0), letter.unicode_at(0))


func _chord(mode: Node, first: Key, second: Key) -> void:
	_key(mode, first, first, true, false)
	_key(mode, second, second, true, false)
	_key(mode, first, 0, false, false)
	_key(mode, second, 0, false, false)


func _key(mode: Node, key: Key, unicode: int = 0, pressed: bool = true, release: bool = true) -> void:
	var event := InputEventKey.new()
	event.keycode = key
	event.physical_keycode = key
	event.unicode = unicode
	event.pressed = pressed
	mode.handle_key(event)
	if pressed and release:
		event = event.duplicate()
		event.pressed = false
		mode.handle_key(event)


func _boy_pose_check(mode: Node) -> bool:
	var player: Node = current_scene.player
	var state: RefCounted = player.original_state
	var saved_frame: int = state.frame
	var saved_facing: int = state.facing
	player.original_character = "boy"
	mode.present_player()
	var sprite: Sprite2D = player.original_sprite
	if sprite.hframes != 26 or not sprite.texture.resource_path.ends_with("berserker_boy_handdrawn.png"):
		_fail("boy did not receive the native 26-frame sheet")
		return false
	var sheet := sprite.texture.get_image()
	var source: Image = load("res://tools/art/pixelorama/boy-shotgun-all-poses.png").get_image()
	sheet.convert(Image.FORMAT_RGBA8)
	source.convert(Image.FORMAT_RGBA8)
	if sheet.get_size() != Vector2i(1248,40) or sheet.get_data() != source.get_data():
		_fail("runtime boy sheet differs from the approved Pixelorama export")
		return false
	var original: Image = load("res://assets/sprites/wr1_boy.png").get_image()
	for frame in range(26):
		# Derive the gun bounds from the actual exported pixels, independently
		# of the runtime muzzle table. Body pixels outside the gun are unchanged.
		var low := Vector2i(48,40)
		var high := Vector2i(-1,-1)
		for y in range(40):
			for x in range(48):
				var baseline := original.get_pixel(frame*24+x-12,y-8) if x >= 12 and x < 36 and y >= 8 else Color.TRANSPARENT
				var pixel := sheet.get_pixel(frame*48+x,y)
				if pixel == baseline or (pixel.a == 0 and baseline.a == 0):
					continue
				low = Vector2i(mini(low.x,x),mini(low.y,y))
				high = Vector2i(maxi(high.x,x),maxi(high.y,y))
		var native_left := frame >= 12 and frame <= 21 or frame == 24
		var tip := Vector2(low.x if native_left else high.x+1,low.y+1.5) - Vector2(24,20)
		for facing in range(2):
			state.frame = frame
			state.facing = facing
			var flipped := (facing == 1) != native_left
			for age in [0.0, 0.19, mode.SHOT_SECONDS]:
				mode.shot_age = age
				mode.shot_direction = -1.0 if facing == 1 else 1.0
				mode.present_player()
				if sprite.frame != frame or sprite.flip_h != flipped or sprite.position.y != -20:
					_fail("boy pose/direction/anchor changed during firing: %d" % frame)
					return false
				var expected_tip := Vector2(-tip.x if flipped else tip.x,tip.y)
				if not mode._muzzle().is_equal_approx(sprite.to_global(sprite.offset + expected_tip)):
					_fail("boy muzzle is detached from gun in frame %d" % frame)
					return false
				var recoil: float = -mode.shot_direction*2 if age == 0 else 0
				if not is_equal_approx(sprite.position.x,recoil):
					_fail("boy recoil did not reset")
					return false
	# Boy firing still uses the shared shell/pump clock without invalid frames.
	mode._clear_particles()
	mode.fire([])
	mode._process(0.19)
	mode._process(0.0)
	var shells := 0
	for particle in mode.particles:
		if particle.node.texture == mode.shell_texture:
			shells += 1
	if shells != 1 or not mode.shell_ejected or sprite.frame != state.frame:
		_fail("boy firing lost its native pose or shell ejection")
		return false
	mode.set_active(false)
	if sprite.hframes != 26 or sprite.flip_h or sprite.position != Vector2(0,-16) or not sprite.texture.resource_path.ends_with("wr1_boy.png"):
		_fail("boy did not restore the unarmed sprite")
		return false
	player.original_character = "girl"
	state.frame = saved_frame
	state.facing = saved_facing
	mode.set_active(true)
	return true


func _speed_check() -> bool:
	var rows: Array = []
	for y in range(30):
		var row: Array = []
		row.resize(100)
		row.fill(0x73 if y == 10 else 0)
		rows.append(row)
	var data := {"attributes":rows,"start":[8,9]}
	var normal = load("res://scripts/core/wr1_motion.gd").new()
	var fast = load("res://scripts/core/wr1_motion.gd").new()
	normal.configure(data)
	fast.configure(data)
	var start: int = normal.gx
	normal.step(false,false,false,true)
	fast.step(false,false,false,true,3)
	if normal.gx-start != 1 or fast.gx-start != 3:
		_fail("boost was not exactly three horizontal steps")
		return false
	fast.configure(data)
	for y in range(6,10):
		rows[y][start+4] = 0x73
	fast.step(false,false,false,true,3)
	if fast.gx != start+1:
		_fail("boost skipped an intermediate wall collision")
		return false
	return true


func _fail(message: String) -> void:
	printerr("berserker smoke FAILED: " + message)
	quit(1)
