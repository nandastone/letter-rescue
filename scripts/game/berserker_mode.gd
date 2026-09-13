extends Node
## Default-game power-up. Art, firing timeline and sound share one paused clock.
const CHEAT_CODES: Array[String] = ["IDKFA", "IDGAF"]
const SHOT_SECONDS := 0.62
const EJECT_SECONDS := 0.18
const ART = preload("res://scripts/game/berserker_art.gd")
var game: Node2D
var active := false
var typed := ""
var held_keys := {}
var warp_entry := false
var warp_digits := ""
var shot_age := SHOT_SECONDS
var shell_ejected := true
var banner_seconds := 0.0
var last_viewport_size := Vector2.ZERO
var overlay: CanvasLayer
var tint: ColorRect
var banner: Label
var effects: Node2D
var shot_player: AudioStreamPlayer
var pump_player: AudioStreamPlayer
var gib_player: AudioStreamPlayer
var particles: Array[Dictionary] = []
var shot_direction := 1.0
var shot_origin := Vector2.ZERO
var flash: Sprite2D
var shell_texture: Texture2D
var smoke_texture: Texture2D
var rng := RandomNumberGenerator.new()

func configure(host: Node2D) -> void:
	game = host
	process_priority = 1100 # After the character's smoothing.
	_build_overlay()
	effects = Node2D.new()
	effects.z_index = 8
	game.add_child(effects)
	flash = Sprite2D.new()
	flash.texture = ART.muzzle_flash()
	effects.add_child(flash)
	flash.hide()
	shell_texture = ART.shell()
	smoke_texture = ART.smoke()
	shot_player = _audio("dsshotgn", -5.0)
	pump_player = _audio("dssgcock", -7.0)
	gib_player = _audio("dsslop", -11.0)
	rng.seed = 7291

func handle_key(event: InputEventKey) -> bool:
	var physical := event.physical_keycode if event.physical_keycode != 0 else event.keycode
	if not event.pressed:
		held_keys.erase(physical)
		return warp_entry
	if event.echo:
		return warp_entry
	held_keys[physical] = true
	if warp_entry:
		_handle_warp_key(event, physical)
		return true
	if not game.replay_ready or game.player.is_dead or event.ctrl_pressed or event.alt_pressed or event.meta_pressed:
		typed = ""
		return false
	if _held(KEY_L) and _held(KEY_Z):
		held_keys.clear()
		typed = ""
		_begin_warp()
		return true
	if _held(KEY_P) and _held(KEY_S):
		held_keys.clear()
		typed = ""
		_refill_slime()
		return true
	var text_key := event.unicode
	if text_key == 0:
		text_key = event.keycode
	var letter := String.chr(text_key).to_upper()
	if letter.length() != 1 or letter < "A" or letter > "Z":
		typed = ""
		return false
	typed = (typed + letter).right(8)
	for code in CHEAT_CODES:
		if typed.ends_with(code):
			typed = ""
			set_active(not active)
			return true
	return false
func _held(key: Key) -> bool:
	return held_keys.has(key)


func _begin_warp() -> void:
	warp_entry = true
	warp_digits = ""
	game.player.set_physics_process(false)
	_update_warp_banner()


func _handle_warp_key(event: InputEventKey, key: int) -> void:
	if key == KEY_ESCAPE:
		_cancel_warp()
		return
	if key == KEY_BACKSPACE:
		warp_digits = warp_digits.left(maxi(0, warp_digits.length() - 1))
		_update_warp_banner()
		return
	if key in [KEY_ENTER, KEY_KP_ENTER]:
		if warp_digits.is_empty():
			_cancel_warp()
			return
		var level := int(warp_digits)
		if level < 1 or level > GameManager.MAX_LEVELS:
			_show_banner("LEVEL WARP\nCHOOSE 1-%d" % GameManager.MAX_LEVELS, 1.4)
			warp_digits = ""
			return
		warp_entry = false
		warp_digits = ""
		banner.hide()
		game.warp_to_original_level(level)
		return
	if event.unicode >= 48 and event.unicode <= 57 and warp_digits.length() < 2:
		warp_digits += String.chr(event.unicode)
		_update_warp_banner()


func _update_warp_banner() -> void:
	var value := warp_digits if not warp_digits.is_empty() else "_"
	_show_banner("LEVEL WARP: %s\nTYPE 1-%d, ENTER" % [value, GameManager.MAX_LEVELS], -1.0)


func _cancel_warp() -> void:
	warp_entry = false
	warp_digits = ""
	held_keys.clear()
	_show_banner("LEVEL WARP CANCELLED", 1.0)
	if game.replay_ready:
		game.player.set_physics_process(true)


func _refill_slime() -> void:
	if game.original_gruzzles == null:
		return
	game.original_gruzzles.slime_used = 0
	game.hud.update_original_slime(0, true)
	_show_banner("SLIME REFILLED", 1.4)


func _show_banner(message: String, duration: float) -> void:
	banner.text = message
	banner.modulate = Color.WHITE
	banner.show()
	banner_seconds = duration


func set_active(enabled: bool) -> void:
	active = enabled
	shot_age = SHOT_SECONDS
	shell_ejected = true
	flash.hide()
	tint.visible = active
	_show_banner("BERSERKER MODE\nRIP AND SPELL" if active else "BERSERKER MODE OFF", 1.8)
	present_player()
	if active and game.original_gruzzles != null:
		game.original_gruzzles.death = false
		game.original_gruzzles.slime_request = false
	if not active:
		_clear_particles()

func _ordinary() -> bool:
	return game.replay_ready and not game.player.is_dead and game.player.original_recap == null and game.player.original_rescue == null and game.player.original_exit == null

func present_player() -> void:
	var sprite: Sprite2D = game.player.original_sprite
	if sprite == null:
		return
	var armed := active and _ordinary()
	var character: String = game.player.original_character
	var texture: Texture2D = ART.player(character) if armed else load("res://assets/sprites/wr1_%s.png" % character)
	if sprite.texture != texture:
		sprite.texture = texture
		sprite.hframes = ART.frame_count(character) if armed else 26
	sprite.position = Vector2(0, -20 if armed else -16)
	sprite.frame = game.player.original_state.frame
	sprite.flip_h = armed and ART.flip_player(character, sprite.frame, game.player.original_state.facing == 1)
	if armed and character == "boy" and shot_age < EJECT_SECONDS:
		# No generated firing poses: keep the authored movement pose and kick
		# it back briefly. Position is reset above on every presentation pass.
		sprite.position.x = -shot_direction * 2.0 * (1.0 - shot_age / EJECT_SECONDS)
	elif armed and character != "boy" and shot_age < 0.42:
		sprite.frame = 26 if shot_age < EJECT_SECONDS else 27

func can_fire() -> bool:
	return active and _ordinary() and shot_age >= SHOT_SECONDS

func fire(hits: Array) -> void:
	if not can_fire():
		return
	shot_age = 0.0
	shell_ejected = false
	shot_direction = -1.0 if game.player.original_state.facing == 1 else 1.0
	_play(shot_player)
	present_player()
	shot_origin = _muzzle()
	for hit in hits:
		_explode(hit)
	if not hits.is_empty():
		_play(gib_player)

func _muzzle() -> Vector2:
	var sprite: Sprite2D = game.player.original_sprite
	return sprite.to_global(sprite.offset + ART.muzzle_offset(game.player.original_character, sprite.frame, sprite.flip_h))

func _process(delta: float) -> void:
	if game == null or game.player.original_state == null:
		return
	var viewport_size := get_viewport().get_visible_rect().size
	if viewport_size != last_viewport_size:
		_layout_overlay(viewport_size)
	var ordinary := _ordinary()
	present_player()
	tint.visible = active and ordinary
	flash.visible = active and ordinary and shot_age < 0.075
	if flash.visible:
		shot_origin = _muzzle()
		flash.position = shot_origin
		flash.flip_h = shot_direction < 0.0
		flash.scale = Vector2.ONE * (1.0 if shot_age < 0.035 else 0.7)
	if not ordinary:
		banner.hide()
		_clear_particles()
		shot_age = SHOT_SECONDS
		return
	if active:
		shot_age += delta
		if not shell_ejected and shot_age >= EJECT_SECONDS:
			shell_ejected = true
			_play(pump_player)
			var eject_at := _muzzle() - Vector2(shot_direction * 13, 1)
			_particle(shell_texture, eject_at, Vector2(-shot_direction * 65, -100), 1.25, 230.0, 13.0, true)
		tint.color = Color(0.65, 0, 0, 0.16 + (0.05 if shot_age < 0.08 else 0.0))
		if shot_age < 0.11:
			_particle(smoke_texture, shot_origin, Vector2(shot_direction * 25, -20), 0.32, -5, 0, false)
	if warp_entry:
		banner.visible = true
		banner.modulate.a = 1.0
	elif banner_seconds > 0.0:
		banner_seconds -= delta
		banner.visible = true
		banner.modulate.a = clampf(banner_seconds * 2.0, 0.0, 1.0)
	else:
		banner.hide()
	_advance_particles(delta)

func _particle(texture: Texture2D, at: Vector2, velocity: Vector2, duration: float, gravity: float, spin: float, bounce: bool) -> void:
	if particles.size() >= 160:
		particles[0].node.queue_free()
		particles.pop_front()
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.position = at
	effects.add_child(sprite)
	particles.append({"node":sprite, "velocity":velocity, "life":duration, "duration":duration, "gravity":gravity, "spin":spin, "bounce":bounce})

func _explode(hit: Dictionary) -> void:
	var texture: Texture2D = load("res://assets/sprites/wr1_gruzzle_%d.png" % (int(hit.type) * 4 + int(hit.frame)))
	var source := texture.get_image()
	# Gibs retain the enemy's skin, eyes and teeth instead of generic sparks.
	for y in range(0, source.get_height(), 6):
		for x in range(0, source.get_width(), 6):
			var rect := Rect2i(x, y, mini(6, source.get_width()-x), mini(6, source.get_height()-y))
			var fragment := source.get_region(rect)
			if fragment.is_invisible():
				continue
			var at := Vector2(hit.position) + Vector2(x+3, y+3)
			var velocity := Vector2(rng.randf_range(-110, 110) + shot_direction * 45, rng.randf_range(-150, -35))
			_particle(ImageTexture.create_from_image(fragment), at, velocity, rng.randf_range(0.7, 1.3), 260, rng.randf_range(-12,12), true)
	for i in range(10):
		_particle(ART.gore(int(hit.type), i), Vector2(hit.position) + Vector2(16, 12), Vector2(rng.randf_range(-95,95), rng.randf_range(-100,25)), 0.65, 210, 5, true)

func _advance_particles(delta: float) -> void:
	for i in range(particles.size()-1, -1, -1):
		var p: Dictionary = particles[i]
		p.life -= delta
		if p.life <= 0:
			p.node.queue_free()
			particles.remove_at(i)
			continue
		p.velocity.y += float(p.gravity) * delta
		var next: Vector2 = p.node.position + Vector2(p.velocity) * delta
		var state: RefCounted = game.player.original_state
		if p.bounce and p.velocity.y > 0 and state.attr(floori(next.x/8), floori(next.y/8)) in [0x73,0x74]:
			p.velocity.y *= -0.35
			p.velocity.x *= 0.65
			p.spin *= 0.6
		else:
			p.node.position = next
		p.node.rotation += float(p.spin) * delta
		p.node.modulate.a = minf(1.0, float(p.life) * 3)

func _clear_particles() -> void:
	for p in particles:
		if is_instance_valid(p.node):
			p.node.queue_free()
	particles.clear()

func _audio(name: String, volume: float) -> AudioStreamPlayer:
	var player := AudioStreamPlayer.new()
	player.stream = load("res://assets/audio/berserker/%s.wav" % name)
	player.volume_db = volume
	add_child(player)
	return player

func _play(player: AudioStreamPlayer) -> void:
	if GameManager.original_sound < 2 and "--mute-original-audio" not in LaunchArgs.user_args() and DisplayServer.get_name() != "headless":
		player.play()

func _build_overlay() -> void:
	overlay = CanvasLayer.new()
	overlay.layer = 10
	game.add_child(overlay)
	tint = ColorRect.new()
	tint.color = Color(0.72, 0.0, 0.0, 0.18)
	tint.position = Vector2.ZERO
	tint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tint.z_index = 0
	tint.hide()
	overlay.add_child(tint)

	banner = Label.new()
	banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	banner.add_theme_font_override("font", preload("res://assets/fonts/andika/Andika-Regular.ttf"))
	banner.add_theme_color_override("font_color", Color(1.0, 0.88, 0.35))
	banner.add_theme_color_override("font_shadow_color", Color(0.18, 0.0, 0.0, 1.0))
	banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	banner.z_index = 1
	banner.hide()
	overlay.add_child(banner)
	_layout_overlay(get_viewport().get_visible_rect().size)


func _layout_overlay(viewport_size: Vector2) -> void:
	last_viewport_size = viewport_size
	tint.size = viewport_size
	var scale_factor := minf(viewport_size.x / 320.0, viewport_size.y / 200.0)
	var banner_size := Vector2(240.0, 58.0) * scale_factor
	banner.position = Vector2((viewport_size.x - banner_size.x) * 0.5,
		(viewport_size.y - banner_size.y) * 0.5)
	banner.size = banner_size
	banner.add_theme_font_size_override("font_size", maxi(12, roundi(18.0 * scale_factor)))
	banner.add_theme_constant_override("shadow_offset_x", maxi(1, roundi(2.0 * scale_factor)))
	banner.add_theme_constant_override("shadow_offset_y", maxi(1, roundi(2.0 * scale_factor)))
