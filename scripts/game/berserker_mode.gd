extends Node

## A deliberately non-canonical, default-game-only easter egg.  Keeping this
## outside scripts/core means the recovered Legacy presentation never sees it.

const CHEAT_CODES: Array[String] = ["IDKFA", "IDGAF"]
const BUFFER_LENGTH := 8
const SHOT_COOLDOWN_MS := 180

var game: Node2D
var active := false
var typed := ""
var last_shot_ms := -SHOT_COOLDOWN_MS
var flash_seconds := 0.0
var banner_seconds := 0.0
var particles: Array[Dictionary] = []
var last_viewport_size := Vector2.ZERO

var overlay: CanvasLayer
var tint: ColorRect
var banner: Label
var weapon: Sprite2D
var effects: Node2D
var shot_player: AudioStreamPlayer
var spark_textures: Array[Texture2D] = []


func configure(host: Node2D) -> void:
	game = host
	_build_overlay()
	_build_weapon()
	_build_audio()
	set_process(true)


func handle_key(event: InputEventKey) -> bool:
	if event.unicode <= 0:
		return false
	var letter := String.chr(event.unicode).to_upper()
	if letter.length() != 1 or letter < "A" or letter > "Z":
		typed = ""
		return false
	typed = (typed + letter).right(BUFFER_LENGTH)
	for code in CHEAT_CODES:
		if typed.ends_with(code):
			typed = ""
			set_active(not active)
			return true
	return false


func set_active(enabled: bool) -> void:
	active = enabled
	tint.visible = active
	weapon.visible = active
	banner.text = "BERSERKER MODE\nRIP AND SPELL" if active else "BERSERKER MODE OFF"
	banner.modulate = Color.WHITE
	banner.show()
	banner_seconds = 1.8
	flash_seconds = 0.0
	if active and game.original_gruzzles != null:
		# Clear a collision registered on the same slow, original-engine tick.
		game.original_gruzzles.death = false


func can_fire() -> bool:
	return active and Time.get_ticks_msec() - last_shot_ms >= SHOT_COOLDOWN_MS


func fire(hit_positions: Array) -> void:
	if not can_fire():
		return
	last_shot_ms = Time.get_ticks_msec()
	flash_seconds = 0.13
	if GameManager.original_sound < 2:
		shot_player.play()

	var direction := -1.0 if game.player.original_state.facing == 1 else 1.0
	var muzzle := weapon.global_position + Vector2(direction * 15.0, -1.0)
	_spawn_burst(muzzle, direction, false)
	for position in hit_positions:
		_spawn_burst(Vector2(position), direction, true)


func _process(delta: float) -> void:
	if game == null or not is_instance_valid(game.player) or game.player.original_state == null:
		return
	var viewport_size := get_viewport().get_visible_rect().size
	if viewport_size != last_viewport_size:
		_layout_overlay(viewport_size)
	if active:
		var facing_left: bool = game.player.original_state.facing == 1
		weapon.flip_h = facing_left
		weapon.position = Vector2(-10.0 if facing_left else 10.0, -18.0)
		var pulse := (sin(Time.get_ticks_msec() / 125.0) + 1.0) * 0.012
		tint.color = Color(0.72, 0.0, 0.0, 0.18 + pulse + (0.12 if flash_seconds > 0.0 else 0.0))
	if flash_seconds > 0.0:
		flash_seconds -= delta
	if banner_seconds > 0.0:
		banner_seconds -= delta
		banner.modulate.a = clampf(banner_seconds * 2.0, 0.0, 1.0)
	else:
		banner.hide()

	for i in range(particles.size() - 1, -1, -1):
		var particle: Dictionary = particles[i]
		particle.life = float(particle.life) - delta
		if particle.life <= 0.0 or not is_instance_valid(particle.node):
			if is_instance_valid(particle.node):
				particle.node.queue_free()
			particles.remove_at(i)
			continue
		particle.velocity.y += 45.0 * delta
		particle.node.position += Vector2(particle.velocity) * delta
		particle.node.modulate.a = clampf(float(particle.life) / float(particle.duration), 0.0, 1.0)


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


func _build_weapon() -> void:
	effects = Node2D.new()
	effects.z_index = 12
	game.add_child(effects)
	weapon = Sprite2D.new()
	weapon.texture = _shotgun_texture()
	weapon.centered = true
	weapon.z_index = 8
	weapon.hide()
	game.player.add_child(weapon)
	for color in [Color8(255, 255, 85), Color8(255, 85, 85), Color8(170, 0, 0)]:
		var image := Image.create(2, 2, false, Image.FORMAT_RGBA8)
		image.fill(color)
		spark_textures.append(ImageTexture.create_from_image(image))


func _shotgun_texture() -> Texture2D:
	var image := Image.create(30, 12, false, Image.FORMAT_RGBA8)
	image.fill(Color.TRANSPARENT)
	# Chunky EGA-ish side view: twin steel barrels, dark receiver and stock.
	image.fill_rect(Rect2i(12, 3, 18, 2), Color8(170, 170, 170))
	image.fill_rect(Rect2i(12, 5, 17, 2), Color8(85, 85, 85))
	image.fill_rect(Rect2i(10, 2, 5, 7), Color8(30, 30, 30))
	image.fill_rect(Rect2i(4, 5, 8, 5), Color8(170, 85, 0))
	image.fill_rect(Rect2i(0, 7, 7, 4), Color8(85, 45, 0))
	image.fill_rect(Rect2i(11, 8, 3, 4), Color8(85, 45, 0))
	image.set_pixel(29, 3, Color8(255, 255, 255))
	return ImageTexture.create_from_image(image)


func _spawn_burst(origin: Vector2, direction: float, impact: bool) -> void:
	var count := 12 if impact else 7
	for i in range(count):
		var sprite := Sprite2D.new()
		sprite.texture = spark_textures[i % spark_textures.size()]
		sprite.position = origin
		sprite.z_index = 12
		effects.add_child(sprite)
		var spread := float((i * 37) % 11 - 5)
		var speed := 35.0 + float((i * 19) % 55)
		var velocity := Vector2(direction * speed, spread * (7.0 if impact else 4.0))
		if impact:
			velocity.x *= -1.0 if i % 3 == 0 else 0.45
		var duration := 0.28 + float(i % 4) * 0.035
		particles.append({"node": sprite, "velocity": velocity, "life": duration, "duration": duration})


func _build_audio() -> void:
	shot_player = AudioStreamPlayer.new()
	shot_player.volume_db = -4.0
	game.add_child(shot_player)
	var wave := AudioStreamWAV.new()
	wave.format = AudioStreamWAV.FORMAT_8_BITS
	wave.mix_rate = 11025
	wave.stereo = false
	var sample_count := 2200
	var data := PackedByteArray()
	data.resize(sample_count)
	var noise := 0x1d872b41
	var filtered := 0.0
	for i in range(sample_count):
		noise = int((noise * 1103515245 + 12345) & 0x7fffffff)
		var raw := float((noise >> 16) & 255) - 128.0
		filtered = filtered * 0.62 + raw * 0.38
		var envelope := pow(1.0 - float(i) / sample_count, 2.4)
		var thump := sin(float(i) * 0.075) * 34.0 * maxf(0.0, 1.0 - float(i) / 520.0)
		data[i] = clampi(int(128.0 + filtered * envelope * 0.72 + thump), 0, 255)
	wave.data = data
	shot_player.stream = wave
