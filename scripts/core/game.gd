extends Node2D

# Main game scene. Coordinates level loading, player, and all game systems.

const TILE_SIZE := 16
const TILESET_COLS := 20

# Wiki: animated tiles cycle through the BG tile at (tx,ty) plus the next
# three tiles to the right of it in the tileset image. The original renderer
# advances them (WR1Motion.background_frame) on each presented update.
var anim_cells: Array = []  # list of Vector2i tile-grid coords (16x16)
var anim_base_atlas: Array[Vector2i] = []  # atlas cell for frame 0 at each anim index
var original_backdrop: Sprite2D

# Standard EGA 16-colour palette, matching DOSBox's VGA output for EGA content.
# Level files store `bg_colour` as an index 0-15; we fill the Background layer
# with the matching RGB so the sky/wall/floor colour matches the original.
const EGA_PALETTE: Array[Color] = [
	Color8(0, 0, 0),       Color8(0, 0, 170),       Color8(0, 170, 0),       Color8(0, 170, 170),
	Color8(170, 0, 0),     Color8(170, 0, 170),     Color8(170, 170, 0),     Color8(170, 170, 170),
	Color8(85, 85, 85),    Color8(85, 85, 255),     Color8(85, 255, 85),     Color8(85, 255, 255),
	Color8(255, 85, 85),   Color8(255, 85, 255),    Color8(255, 255, 85),    Color8(255, 255, 255),
]

@onready var player: Node2D = $Player
@onready var camera: Camera2D = $Camera
@onready var hud: CanvasLayer = $HUD
@onready var bg_tilemap: TileMapLayer = $BackgroundTileMapLayer
@onready var fg_tilemap: TileMapLayer = $ForegroundTileMapLayer
@onready var background: ColorRect = $Background
@onready var entities: Node2D = $Entities
@onready var word_manager: Node = $WordManager
@onready var mystery_word: Node = $MysteryWord

var question_block_scene: PackedScene
var collectible_scene: PackedScene
var exit_door_scene: PackedScene

var level_data: Dictionary = {}
var exit_door: Node2D = null
var original_books: RefCounted
var original_gruzzles: RefCounted
var original_slime_pickups: RefCounted
var original_letters: RefCounted
var original_picture_animation: RefCounted
var original_reward: RefCounted
var original_reward_sprite: Sprite2D
var original_actor_sprites: Array[Sprite2D] = []
var replay_ready: bool = false
var original_restart: Dictionary = {}
var original_presentation: Node
var original_recap_pending: bool = false
var original_recap_view: CanvasLayer
var original_door_state: int = 0
var original_drips: RefCounted
var original_words: RefCounted
var original_drip_sprites: Array[Sprite2D] = []
var original_entrance: Sprite2D
var original_entrance_timer: int = 60
var original_level_title: CanvasLayer
var original_start_seed: int = -1
var original_initialization: Dictionary = {}
var original_loaded_profile: Dictionary = {}
var berserker_mode: Node

func _exit_tree() -> void:
	save_original_profile()
	AudioManager.end_original_session()

func is_replay_ready() -> bool:
	return replay_ready

func _ready() -> void:
	question_block_scene = load("res://scenes/question_block.tscn")
	collectible_scene = load("res://scenes/collectible.tscn")
	exit_door_scene = load("res://scenes/exit_door.tscn")

	word_manager.correct_match.connect(_on_correct_match)
	word_manager.wrong_match.connect(_on_wrong_match)
	word_manager.all_words_matched.connect(_on_all_words_matched)
	word_manager.word_revealed.connect(_on_word_revealed)
	player.original_presented.connect(_on_original_presented)
	player.original_moved.connect(_on_original_moved)

	# Loaded by path: each export ships only its own half of the presentation.
	original_presentation = load("res://scripts/legacy/wr1_presentation.gd").new() if LaunchArgs.legacy() \
		else load("res://scripts/game/game_presentation.gd").new()
	add_child(original_presentation)
	if not LaunchArgs.legacy():
		add_child(load("res://scripts/game/smooth_motion.gd").new())
		berserker_mode = load("res://scripts/game/berserker_mode.gd").new()
		add_child(berserker_mode)
		berserker_mode.configure(self)
	load_current_level()

func queue_original_video(elapsed_after_event: float = 0.0, ordinary_draw: bool = false) -> void:
	if original_presentation != null and replay_ready:
		var page: int = original_gruzzles.render_page if original_gruzzles != null else 0
		original_presentation.submit(page, elapsed_after_event, ordinary_draw)

func load_current_level() -> void:
	replay_ready = false
	var path :=LevelLoader.get_level_path(GameManager.current_level)
	level_data = LevelLoader.load_level(path)

	if level_data.is_empty():
		push_error("No level data found: " + path)
		return

	_prepare_original_initialization()
	AudioManager.begin_original_level(GameManager.current_level)
	await _show_original_level_title(true)
	_build_level_from_data()

func _prepare_original_initialization() -> void:
	if original_words != null:
		return
	# Existing native replays start at a measured post-load checkpoint. Older
	# recordings without a seed also retain their historical deterministic start.
	if InputReplay.mode == InputReplay.Mode.REPLAYING and InputReplay.original_start_seed < 0:
		return
	var args := LaunchArgs.user_args()
	for override_option in ["--word-offset", "--picture-offset", "--mystery-word"]:
		if override_option in args:
			if InputReplay.original_start_seed >= 0:
				push_error("A seeded start cannot also override its words or pictures")
				get_tree().quit(1)
			return # Preserve explicitly customized legacy research starts.
	original_start_seed = InputReplay.original_start_seed
	if original_start_seed < 0:
		original_start_seed = preload("res://scripts/core/wr1_startup.gd").seed_from_dos_time(Time.get_datetime_dict_from_system())
	var starts: Array = []
	for pos in level_data.get("gruzzles", []):
		starts.append([int(pos[0] * 2), int(pos[1] * 2)])
	original_words = preload("res://scripts/core/wr1_words.gd").new()
	var actors = preload("res://scripts/core/wr1_gruzzles.gd").new()
	if not GameManager.original_pending_profile.is_empty():
		original_loaded_profile = GameManager.original_pending_profile.duplicate(true)
		original_words.words.assign(GameManager.original_pending_profile.words)
		original_words.offset = int(GameManager.original_pending_profile.word_cursor)
		original_initialization = actors.start(starts, GameManager.current_difficulty, original_start_seed, func(_random): pass)
		GameManager.original_pending_profile = {}
	else:
		original_initialization = actors.start(starts, GameManager.current_difficulty, original_start_seed, original_words.next_words)
	original_initialization["actors"] = actors

func _show_original_level_title(initial: bool) -> void:
	# Native-input replays begin after loading; their frame zero excludes this UI.
	if InputReplay.mode == InputReplay.Mode.REPLAYING:
		return
	replay_ready = false
	player.set_physics_process(false)
	original_level_title = preload("res://scripts/core/wr1_level_title.gd").new()
	original_level_title.configure(GameManager.current_level)
	add_child(original_level_title)
	await get_tree().process_frame
	if initial:
		await original_level_title.wait_for_start()

func _hide_original_level_title() -> void:
	if original_level_title != null:
		original_level_title.hide()
		original_level_title.queue_free()
		original_level_title = null

func restart_original_level() -> void:
	if AudioManager.original != null:
		AudioManager.original.stop_effect() # 4E71 silences the speaker, retaining music.
	var starts: Array = []
	for pos in level_data.get("gruzzles", []):
		starts.append([int(pos[0] * 2), int(pos[1] * 2)])
	original_restart = original_gruzzles.restart(starts, GameManager.current_difficulty)
	original_restart["actors"] = original_gruzzles
	# Cached death reset retains DS:014c/014e/0150/0160. The fresh loader
	# clears reward coordinates at 6cdd; the cached path does not call it.
	original_restart["reward"] = original_reward
	# DS:0334 survives a cached death restart; a new level starts a new count.
	original_restart["mistakes"] = word_manager.original_model.mistakes
	_build_level_from_data()

func warp_to_original_level(level: int) -> void:
	if InputReplay.mode == InputReplay.Mode.REPLAYING or not replay_ready:
		return
	var target := clampi(level, 1, GameManager.MAX_LEVELS)
	if target == GameManager.current_level:
		restart_original_level()
		return
	replay_ready = false
	player.set_physics_process(false)
	GameManager.current_level = target
	level_data = LevelLoader.load_level(LevelLoader.get_level_path(target))
	if level_data.is_empty():
		push_error("No level data found for warp target: %d" % target)
		player.set_physics_process(true)
		return
	if AudioManager.original != null:
		AudioManager.original.stop_effect()
	AudioManager.begin_original_level(target)
	var starts: Array = []
	for pos in level_data.get("gruzzles", []):
		starts.append([int(pos[0] * 2), int(pos[1] * 2)])
	# A warp to a different map follows the same fresh-load path as the exit:
	# advance the word stream and initialize every map-specific system again.
	original_restart = original_gruzzles.restart(starts, GameManager.current_difficulty, true, original_words.next_words)
	original_restart["actors"] = original_gruzzles
	original_restart["advancing"] = true
	await _show_original_level_title(false)
	_build_level_from_data()

func _build_level_from_data() -> void:
	replay_ready = false
	original_recap_pending = false
	original_door_state = 0
	player.set_physics_process(false)
	# Renderer order: player BA1C, enemies BA38, drips BBA0, then
	# foreground at BC5E. Keep each layer distinct as actors are spawned.
	$ForegroundTileMapLayer.z_index = 6
	original_books = null
	original_gruzzles = null
	original_slime_pickups = null
	original_letters = null
	original_reward = null
	original_reward_sprite = null
	original_actor_sprites.clear()
	original_drip_sprites.clear()
	hud.reset_original_chrome()
	# Clear existing entities.
	for child in entities.get_children():
		if not original_restart.is_empty():
			entities.remove_child(child)
		child.queue_free()

	# Wait one frame for queue_free to process.
	if original_restart.is_empty():
		await get_tree().process_frame

	# Background colour from the level's EGA index.
	var bg_idx: int = int(level_data.get("bg_colour_ega", 0))
	if bg_idx >= 0 and bg_idx < EGA_PALETTE.size():
		background.color = EGA_PALETTE[bg_idx]
	if original_backdrop == null:
		original_backdrop = Sprite2D.new()
		original_backdrop.centered = false
		original_backdrop.z_index = -9
		add_child(original_backdrop)
	var backdrop_index: int = int(level_data.get("backdrop", 0))
	original_backdrop.visible = backdrop_index != 0
	if backdrop_index != 0:
		original_backdrop.texture = load("res://assets/tiles/backdrop_%d.png" % backdrop_index)

	player.is_dead = false

	# Spawn doorway backdrop: the decorative 32x40 pink-checker frame with
	# dark-red outer trim and black inner frame. Extracted from STATIC.WR at
	# (16, 73), frame 0 (empty) of the girl doorway-animation row.
	# Top-left offset (-8, -32) from raw player_start aligns it pixel-exact
	# with the DOSBox reference.
	var start = level_data.get("player_start", [2, 10])
	var raw_start := Vector2(float(start[0]) * TILE_SIZE, float(start[1]) * TILE_SIZE)
	var doorway_sprite := Sprite2D.new()
	doorway_sprite.texture = preload("res://assets/sprites/spawn_doorway.png")
	doorway_sprite.centered = false
	doorway_sprite.position = raw_start + Vector2(-8, -32)
	entities.add_child(doorway_sprite)
	original_entrance = doorway_sprite
	original_entrance_timer = 60 # WR1.EXE 4e77: reset on both fresh and cached loads.
	if original_restart.is_empty() and not InputReplay.original_level_start.is_empty():
		original_entrance_timer = int(InputReplay.original_level_start.entrance_timer)

	# Build tilemaps. WR1 engine overwrites bg cells at level-load with
	# entity-specific tile indices (per wr1.exe disassembly at 0x6e6a/0x6eea):
	#   books -> tile 239, letters -> tile 238
	var texture: Texture2D = load("res://assets/tiles/tileset_back%d.png" % int(level_data.tileset))
	for layer in [bg_tilemap, fg_tilemap]:
		# Keep the scene tile definitions and give each map its own atlas.
		layer.tile_set = layer.tile_set.duplicate(true)
		(layer.tile_set.get_source(0) as TileSetAtlasSource).texture = texture
	if level_data.has("background_tiles"):
		_build_background(level_data["background_tiles"])
	_build_foreground(level_data.get("fg_tiles", []), level_data.get("background_tiles", []))
	_setup_animations(level_data.get("animations", []), level_data.get("background_tiles", []))

	var door_pos = level_data.get("exit_door", [10, 10])
	exit_door = exit_door_scene.instantiate() as Node2D
	exit_door.global_position = Vector2(door_pos[0] * TILE_SIZE, door_pos[1] * TILE_SIZE)
	entities.add_child(exit_door)

	# Word/picture slots at their raw attr-cell positions; word_manager
	# resolves slot identity from these coordinates.
	var blocks: Array[Node2D] = []
	for pos in level_data.get("question_blocks", []):
		var block := question_block_scene.instantiate() as Node2D
		block.global_position = Vector2(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE)
		entities.add_child(block)
		blocks.append(block)

	if original_words == null:
		original_words = preload("res://scripts/core/wr1_words.gd").new()
		if InputReplay.original_level_start.is_empty():
			original_words.next_words()
		else:
			original_words.words.assign(InputReplay.original_level_start.words)
			original_words.offset = int(InputReplay.original_level_start.word_cursor)
	var words: Array = preload("res://scripts/core/vocabulary.gd").display_words(original_words.words)
	word_manager.setup(words, blocks)

	var mystery: String = words[5] # Recorded initial session; later loads use the RNG index.
	if not original_restart.is_empty():
		mystery = words[original_restart.mystery_index]
	elif not original_initialization.is_empty():
		mystery = words[original_initialization.mystery_index]
	elif not InputReplay.original_level_start.is_empty():
		mystery = words[int(InputReplay.original_level_start.mystery_index)]
	else:
		var user_args := LaunchArgs.user_args()
		var mystery_arg := user_args.find("--mystery-word")
		if mystery_arg >= 0 and mystery_arg + 1 < user_args.size():
			var override_word: String = user_args[mystery_arg + 1].to_lower()
			if override_word.length() >= 1 and override_word.length() <= 7 and override_word.is_valid_identifier():
				mystery = override_word
	mystery_word.setup(mystery)
	hud.setup_mystery_word(mystery.to_upper(), mystery_word.next_index)

	for pos in level_data.get("slime_buckets", []):
		_spawn_collectible(Vector2(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE), "slime_bucket")
	for pos in level_data.get("books", []):
		_spawn_collectible(Vector2(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE), "book")
	var mystery_upper = mystery.to_upper()
	var letter_positions = level_data.get("mystery_letters", [])
	for i in range(min(mystery_upper.length(), letter_positions.size())):
		_spawn_collectible(
			Vector2(letter_positions[i][0] * TILE_SIZE, letter_positions[i][1] * TILE_SIZE),
			"letter",
			mystery_upper[i]
		)

	# Fresh loader prints the score at 6d13; cached death reset skips that path.
	if original_restart.is_empty() or original_restart.get("advancing", false):
		hud.update_score(GameManager.score)

	var rules := LevelLoader.load_level("res://data/wr1/level_%02d.json" % GameManager.current_level)
	if rules.is_empty():
		push_error("Original rules require extracted WR1 map data")
		return
	player.configure_original(rules, not original_restart.is_empty(), original_restart.get("advancing", false))
	original_books = preload("res://scripts/core/wr1_books.gd").new()
	original_books.configure(rules)
	original_slime_pickups = preload("res://scripts/core/wr1_slime_pickups.gd").new()
	original_slime_pickups.configure(rules, level_data.get("slime_buckets", []))
	original_letters = preload("res://scripts/core/wr1_letters.gd").new()
	original_letters.configure(rules, letter_positions, mystery)
	if original_drips == null:
		original_drips = preload("res://scripts/core/wr1_drips.gd").new()
		original_drips.configure(level_data.get("drips", []))
		if not InputReplay.original_level_start.is_empty():
			original_drips.drips.assign(InputReplay.original_level_start.get("drips", []))
			for i in range(original_drips.drips.size()):
				original_drips.frames[i] = int(original_drips.drips[i].frame)
	elif original_restart.get("advancing", false):
		original_drips.configure(level_data.get("drips", []))
	original_reward = original_restart.get("reward")
	if original_reward == null:
		original_reward = preload("res://scripts/core/wr1_reward_popup.gd").new()
	original_reward_sprite = Sprite2D.new()
	original_reward_sprite.centered = false
	original_reward_sprite.z_index = 10
	entities.add_child(original_reward_sprite)
	# Recorded reference session defaults; explicit rotations allow other
	# native saves to be reproduced without pretending RNG is synchronized.
	var args := LaunchArgs.user_args()
	var rotations := [5, 0]
	for i in range(2):
		var option := args.find(["--word-offset", "--picture-offset"][i])
		if option >= 0 and option + 1 < args.size():
			rotations[i] = posmod(int(args[option + 1]), 7)
	if rotations[0] == rotations[1]:
		push_error("Word and picture rotations must differ")
		rotations = [5, 0]
	if not original_restart.is_empty():
		rotations = [original_restart.word_offset, original_restart.picture_offset]
	elif not original_initialization.is_empty():
		rotations = [original_initialization.word_offset, original_initialization.picture_offset]
	elif not InputReplay.original_level_start.is_empty():
		rotations = [int(InputReplay.original_level_start.word_offset), int(InputReplay.original_level_start.picture_offset)]
		word_manager.original_last_index = int(InputReplay.original_level_start.active_index)
	word_manager.configure_original(rules, rotations[0], rotations[1])
	word_manager.original_model.mistakes = int(original_restart.get("mistakes", 0))
	if original_picture_animation == null:
		original_picture_animation = preload("res://scripts/core/wr1_picture_animation.gd").new()
		original_picture_animation.configure(InputReplay.original_picture_start)
	elif not original_restart.is_empty():
		original_picture_animation.enabled = true
	if original_restart.is_empty():
		if not original_initialization.is_empty():
			original_gruzzles = original_initialization.actors
		else:
			original_gruzzles = preload("res://scripts/core/wr1_gruzzles.gd").new()
			original_gruzzles.demo_mode = InputReplay.demo_mode
			var starts: Array = []
			for pos in level_data.get("gruzzles", []):
				starts.append([int(pos[0] * 2), int(pos[1] * 2)])
			original_gruzzles.configure(starts, GameManager.current_difficulty, InputReplay.original_entity_start)
		if not InputReplay.original_level_start.is_empty():
			original_gruzzles.present_checkpoint(player.original_state)
			_present_original_gruzzles()
			_present_original_drips(player.original_state)
	else:
		original_gruzzles = original_restart.actors
	hud.update_original_slime(original_gruzzles.slime_used, true)
	if original_restart.is_empty():
		player._record_original({})
	player.set_physics_process(true)
	original_restart = {}
	original_initialization = {}
	replay_ready = true
	if original_presentation.initialized:
		queue_original_video(player.original_elapsed)
		_hide_original_level_title()
	else:
		replay_ready = false
		_finish_original_video_start.call_deferred()

func _finish_original_video_start() -> void:
	original_presentation.initialize()
	replay_ready = true
	_hide_original_level_title()

func _build_foreground(fg_coords: Array, bg_data: Array) -> void:
	# Wiki: fg_tiles are (x,y) pairs in 16x16 tile units. The drawn tile is
	# the same BG cell at that coord, rendered on top of the player (z=5) so
	# the character passes behind it.
	fg_tilemap.clear()
	for coord in fg_coords:
		var tx: int = int(coord[0])
		var ty: int = int(coord[1])
		if ty < 0 or ty >= bg_data.size():
			continue
		var row = bg_data[ty]
		if tx < 0 or tx >= row.size():
			continue
		var tile_idx: int = row[tx]
		if tile_idx == 0xFF or tile_idx == 255:
			continue
		var atlas_x: int = tile_idx % TILESET_COLS
		var atlas_y: int = tile_idx / TILESET_COLS
		fg_tilemap.set_cell(Vector2i(tx, ty), 0, Vector2i(atlas_x, atlas_y))


func _setup_animations(coords: Array, bg_data: Array) -> void:
	# Wiki: animated tile cycles through the BG tile at (tx,ty) plus the next
	# three tiles to the right in the tileset image. _on_original_presented
	# sets each cell's frame from the renderer's background phase.
	anim_cells = []
	anim_base_atlas = []
	for coord in coords:
		var tx: int = int(coord[0])
		var ty: int = int(coord[1])
		if ty < 0 or ty >= bg_data.size():
			continue
		var row = bg_data[ty]
		if tx < 0 or tx >= row.size():
			continue
		var tile_idx: int = row[tx]
		if tile_idx == 0xFF or tile_idx == 255:
			continue
		anim_cells.append(Vector2i(tx, ty))
		anim_base_atlas.append(Vector2i(tile_idx % TILESET_COLS, tile_idx / TILESET_COLS))

func _on_original_presented(state: RefCounted) -> void:
	if original_backdrop != null and original_backdrop.visible:
		# AD3E..AD54 copies the whole backdrop at screen (0,0), without scroll.
		original_backdrop.position = Vector2(state.camera_x * 8 - 16, state.camera_y * 8 - 32)
	if original_gruzzles != null:
		# b4b1..b4cc: decrement even offscreen; last ten calls blink on page 1.
		# Setup presents the checkpoint with no render admission (actors still null).
		original_entrance.visible = false
		if original_entrance_timer > 0:
			original_entrance_timer -= 1
			original_entrance.visible = original_entrance_timer > 10 or original_gruzzles.render_page == 0
	if original_picture_animation != null and word_manager.original_model != null:
		var changed: Array[int] = original_picture_animation.step()
		for i in range(7):
			var phase_index: int = word_manager.original_model.picture_phase_indices[i]
			word_manager.blocks[i].set_original_picture_frame(original_picture_animation.frames[phase_index])
		for i in changed:
			var order: int = word_manager.original_model.completion_order[i]
			if order < 7:
				hud.add_matched_word(word_manager.words[i], order, original_picture_animation.frames[i])
	for i in range(anim_cells.size()):
		var base: Vector2i = anim_base_atlas[i]
		bg_tilemap.set_cell(anim_cells[i], 0, Vector2i(base.x + state.background_frame, base.y))
	if original_gruzzles != null:
		var reward: int = original_gruzzles.render_step(state)
		if reward:
			GameManager.add_score(reward)
			hud.update_score(GameManager.score)
			original_reward.start(10, original_gruzzles.last_reward_grid)
		_present_original_gruzzles()
	_present_original_drips(state)
	if original_reward != null and original_gruzzles != null:
		var draw: Dictionary = original_reward.render_step(state, original_gruzzles.render_page)
		original_reward_sprite.visible = not draw.is_empty()
		if not draw.is_empty():
			var raster := Image.create(64,16,false,Image.FORMAT_RGBA8)
			raster.fill(Color.TRANSPARENT)
			preload("res://scripts/core/wr1_text.gd").draw(raster, draw.text, Vector2i(20,8), draw.color, Color.TRANSPARENT)
			if draw.has("caption"):
				preload("res://scripts/core/wr1_text.gd").draw(raster, draw.caption, Vector2i.ZERO, draw.color, Color.TRANSPARENT)
			original_reward_sprite.texture = ImageTexture.create_from_image(raster)
			original_reward_sprite.position = Vector2(draw.position) - Vector2(20,8)
			preload("res://scripts/core/wr1_clear_text.gd").reward(original_reward_sprite, raster, draw.get("caption", ""), draw.text, draw.color)
		preload("res://scripts/core/wr1_clear_text.gd").sync_sprite(original_reward_sprite)

func _present_original_drips(state: RefCounted) -> void:
	if original_drips == null:
		return
	var drops: Array = original_drips.draws(state.camera_x, state.camera_y)
	while original_drip_sprites.size() < drops.size():
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.z_index = 5
		entities.add_child(sprite)
		original_drip_sprites.append(sprite)
	for i in range(original_drip_sprites.size()):
		var sprite := original_drip_sprites[i]
		sprite.visible = i < drops.size()
		if sprite.visible:
			sprite.texture = load("res://assets/sprites/wr1_drip_%d.png" % drops[i].frame)
			sprite.position = drops[i].position

func _present_original_gruzzles() -> void:
	while original_actor_sprites.size() < original_gruzzles.draws.size():
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.z_index = 4
		entities.add_child(sprite)
		original_actor_sprites.append(sprite)
	for i in range(original_actor_sprites.size()):
		var sprite := original_actor_sprites[i]
		sprite.visible = i < original_gruzzles.draws.size()
		if sprite.visible:
			var draw: Dictionary = original_gruzzles.draws[i]
			# BA38 draws actors, BD6A restores foreground tiles, then BD79..BF50
			# paints slime over those tiles. Pooled sprites can change kind.
			sprite.z_index = 7 if draw.kind == "slime" else 4
			sprite.modulate = Color.BLACK if draw.get("mask", false) else Color.WHITE
			var index: int = draw.frame + (draw.type * 4 if draw.kind == "gruzzle" else 0)
			sprite.texture = load("res://assets/sprites/wr1_%s_%d.png" % [draw.kind, index])
			sprite.position = draw.position

func _on_original_moved(state: RefCounted) -> void:
	var door_grid := Vector2i(Vector2(level_data.exit_door[0], level_data.exit_door[1]) * 2)
	if original_door_state != 0 and preload("res://scripts/core/wr1_exit.gd").touches(state.gx, state.gy, door_grid):
		original_door_state = 2
	# 3d72 -> 40a6: the bottom row enters rescue before cell/actor updates.
	if state.gy >= state.height:
		original_gruzzles.death = true
		return
	if word_manager.original_model != null:
		word_manager.scan_original(state.gx, state.gy, _collect_original_cell)
	if original_gruzzles != null:
		var slime_before: int = original_gruzzles.slime_used
		var miss_before: int = original_gruzzles.miss_timer
		original_gruzzles.step(state, _step_original_drips)
		if berserker_mode != null and berserker_mode.active:
			original_gruzzles.death = false
		if original_gruzzles.slime_used > slime_before:
			AudioManager.play_original("slime")
		elif original_gruzzles.miss_timer > miss_before:
			AudioManager.play_original("slime_miss")
		hud.update_original_slime(original_gruzzles.slime_used)

func _step_original_drips() -> void:
	if original_drips != null and original_drips.step(player.original_state.gx, player.original_state.gy, GameManager.current_difficulty):
		original_gruzzles.death = berserker_mode == null or not berserker_mode.active

func original_interaction_snapshot() -> Dictionary:
	var result := {"score": GameManager.score, "level_index":GameManager.current_level - 1,
		"door_state":original_door_state, "recap_pending":int(original_recap_pending),
		"entrance_timer":original_entrance_timer}
	if original_words != null:
		result["word_cursor"] = original_words.offset
		result["words"] = original_words.words.duplicate()
	if original_gruzzles != null:
		result.merge(original_gruzzles.snapshot())
		result["slime_ever_used"] = int(original_gruzzles.slime_ever_used)
	if original_drips != null:
		result["drips"] = original_drips.snapshot()
	if original_slime_pickups != null:
		result["slime_pickups"] = original_slime_pickups.snapshot()
	if original_letters != null:
		result.merge(original_letters.snapshot())
	if original_picture_animation != null:
		result.merge(original_picture_animation.snapshot())
	if original_reward != null:
		result.merge(original_reward.snapshot())
	if original_books != null:
		result["books_collected"] = original_books.collected_count
	if word_manager.original_model != null:
		var model = word_manager.original_model
		result.merge({"active_word": int(model.active_slot >= 0), "active_index": model.active_index,
			"matched_count": model.matched_count, "mistakes": model.mistakes,
			"word_offset": model.word_offset, "picture_offset": model.picture_offset})
	return result

func original_player_dead() -> bool:
	return original_gruzzles != null and original_gruzzles.death

func begin_original_recap() -> bool:
	if not original_recap_pending or player.original_state.attr(player.original_state.gx + 1, player.original_state.gy) not in [0x73, 0x74]:
		return false
	original_recap_pending = false
	original_picture_animation.enabled = false
	player.original_recap = preload("res://scripts/core/wr1_recap.gd").new()
	player.original_recap.begin(player.original_state, word_manager.original_model.completion_order, player.original_elapsed, true, player.original_music_clock)
	player.original_recap.sound_output = AudioManager.play_original
	if LaunchArgs.legacy():
		# Legacy times recap drawing with the recovered renderer cost model; the
		# default game uses the recorded per-event seconds in wr1_recap.gd.
		var scene_work = load("res://scripts/legacy/wr1_scene_work.gd").new()
		player.original_recap.scene_drawing = func(event: Dictionary) -> float: return scene_work.recap_seconds(self, player.original_state, event)
	original_recap_view = preload("res://scripts/core/wr1_recap_view.gd").new()
	add_child(original_recap_view)
	original_recap_view.configure(hud, word_manager.words)
	return true

func present_original_recap(event: Dictionary) -> void:
	original_recap_view.present(event)
	queue_original_video(player.original_recap.elapsed)

func finish_original_recap() -> void:
	if AudioManager.original != null:
		AudioManager.original.stop_effect("recap")
	original_recap_view.queue_free()
	original_recap_view = null

func finish_original_exit(held: Dictionary, source_frame: int) -> void:
	if InputReplay.demo_mode:
		# 3F94 returns to the attract loop before advancing the selected level.
		player._record_original(held, source_frame)
		InputReplay.finish_original_demo()
		replay_ready = false
		return
	GameManager.advance_level()
	player._record_original(held, source_frame)
	if GameManager.current_level > GameManager.MAX_LEVELS:
		open_original_frontend("ending")
		return
	level_data = LevelLoader.load_level(LevelLoader.get_level_path(GameManager.current_level))
	if AudioManager.original != null:
		AudioManager.original.stop_effect()
	AudioManager.begin_original_level(GameManager.current_level)
	var starts: Array = []
	for pos in level_data.get("gruzzles", []):
		starts.append([int(pos[0] * 2), int(pos[1] * 2)])
	original_restart = original_gruzzles.restart(starts, GameManager.current_difficulty, true, original_words.next_words)
	original_restart["actors"] = original_gruzzles
	original_restart["advancing"] = true
	if OS.has_feature("web"):
		# DOS players leave through Quit, which saves; browser tabs just close.
		# Save once the new level's words exist so the profile resumes here.
		save_original_profile()
	await _show_original_level_title(false)
	_build_level_from_data()

func _collect_original_cell(col: int, row: int) -> void:
	var result: Dictionary = original_books.collect_cell(col, row)
	var pickup_type := "book"
	if result.is_empty() and original_slime_pickups != null:
		result = original_slime_pickups.collect_cell(col, row)
		pickup_type = "slime_bucket"
		if not result.is_empty():
			original_gruzzles.refill(GameManager.current_difficulty)
			# A69D calls the same inclusive fill helper as a level reset.
			hud.update_original_slime(original_gruzzles.slime_used, true)
	if result.is_empty() and original_letters != null:
		result = original_letters.collect_cell(col, row)
		pickup_type = "letter"
		if not result.is_empty():
			if result.advanced:
				mystery_word.next_index = original_letters.prefix
				hud.update_mystery_letter(original_letters.prefix - 1)
			if result.complete:
				original_gruzzles.slime_used = 0
				hud.update_original_slime(0)
	if result.is_empty():
		return
	var tile: Vector2i = result.tile
	var background_tile: int = result.background
	for layer in [bg_tilemap, fg_tilemap]:
		if layer == fg_tilemap and layer.get_cell_source_id(tile) == -1:
			continue
		if background_tile == 255:
			layer.erase_cell(tile)
		else:
			layer.set_cell(tile, 0, Vector2i(background_tile % TILESET_COLS, background_tile / TILESET_COLS))
	for child in entities.get_children():
		if child.get_script() == preload("res://scripts/core/collectible.gd") and child.type == pickup_type and child.position == Vector2(tile * 16):
			child.queue_free()
	GameManager.add_score(int(result.reward))
	original_reward.start(int(result.reward), Vector2i(col,row - 2), 1 if pickup_type == "book" and result.reward == 500 else 0)
	hud.update_score(GameManager.score)
	if pickup_type == "book" and original_books.collected_count == 20:
		hud._draw_mystery(true)
	if pickup_type == "book":
		AudioManager.play_original("book")
	elif pickup_type == "letter":
		AudioManager.play_original("mystery_complete" if result.complete else "correct")


func _build_background(bg_data: Array) -> void:
	bg_tilemap.clear()
	for y in range(bg_data.size()):
		var row = bg_data[y]
		for x in range(row.size()):
			var tile_idx: int = row[x]
			if tile_idx == 0xFF or tile_idx == 255:
				continue  # Transparent.
			var atlas_x: int = tile_idx % TILESET_COLS
			var atlas_y: int = tile_idx / TILESET_COLS
			bg_tilemap.set_cell(Vector2i(x, y), 0, Vector2i(atlas_x, atlas_y))

func _spawn_collectible(pos: Vector2, type: String, data: String = "") -> void:
	var collectible := collectible_scene.instantiate() as Node2D
	collectible.global_position = pos
	if type == "slime_bucket":
		# Tile 238 belongs to this level's atlas, including its opaque surround.
		collectible.original_tileset = bg_tilemap.tile_set.get_source(0).texture
	collectible.setup(type, data)
	entities.add_child(collectible)

func _input(event: InputEvent) -> void:
	if player.original_recap != null:
		if event.is_action_pressed("ui_cancel"):
			player.original_recap_skip_requested = true
			hud.clear_original_matches()
		return
	if InputReplay.mode != InputReplay.Mode.REPLAYING and event is InputEventKey:
		if berserker_mode != null and berserker_mode.handle_key(event):
			get_viewport().set_input_as_handled()
			return
	if InputReplay.mode != InputReplay.Mode.REPLAYING and event is InputEventKey and event.pressed and not event.echo:
		var scan := preload("res://scripts/core/wr1_controls.gd").scan_for_key(event.physical_keycode if event.physical_keycode != 0 else event.keycode)
		if GameManager.original_custom_keys and scan in GameManager.original_scancodes:
			if event.is_action_pressed("use_slime") and not player.is_dead:
				_try_use_slime()
			get_viewport().set_input_as_handled()
			return
		if event.keycode in [KEY_PLUS,KEY_EQUAL,KEY_KP_ADD,KEY_MINUS,KEY_KP_SUBTRACT]:
			if event.keycode in [KEY_PLUS,KEY_EQUAL,KEY_KP_ADD]: GameManager.original_speed_ticks = maxi(0,GameManager.original_speed_ticks-1)
			else: GameManager.original_speed_ticks = (GameManager.original_speed_ticks+1) & 0xffff
			InputReplay.record_setting("speed",GameManager.original_speed_ticks)
			get_viewport().set_input_as_handled()
			return
		var pages := {KEY_ESCAPE:"menu", KEY_H:"help", KEY_S:"sound", KEY_W:"words", KEY_Q:"quit"}
		for key in range(KEY_F1,KEY_F10+1): pages[key] = "help"
		if pages.has(event.keycode) and replay_ready:
			get_viewport().set_input_as_handled()
			open_original_frontend(pages[event.keycode])
			return
	if GameManager.original_joystick and event is InputEventJoypadButton and event.pressed and event.button_index in [JOY_BUTTON_A,JOY_BUTTON_B]:
		_try_use_slime()
		return
	if event.is_action_pressed("use_slime") and not player.is_dead:
		_try_use_slime()
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://scenes/main_menu.tscn")

func open_original_frontend(kind: String = "menu") -> void:
	var frontend := preload("res://scripts/core/wr1_frontend.gd").new()
	add_child(frontend)
	frontend.begin(kind,self)

func save_original_profile() -> void:
	if not is_instance_valid(player) or original_words == null or InputReplay.mode == InputReplay.Mode.REPLAYING or has_meta("frontend_replaced"):
		return
	var profile := {"level":clampi(GameManager.current_level,1,15), "character":GameManager.original_character,
		"score":GameManager.score,"word_cursor":original_words.offset,"words":original_words.words,
		"difficulty":GameManager.current_difficulty,"custom_keys":GameManager.original_custom_keys,
		"scancodes":GameManager.original_scancodes,"joystick":GameManager.original_joystick}
	preload("res://scripts/core/wr1_profiles.gd").save_player(GameManager.original_player_name,profile)
	preload("res://scripts/core/wr1_profiles.gd").update_high_score(GameManager.original_player_name,GameManager.score)

func apply_original_difficulty(mode: int) -> void:
	if original_gruzzles == null:
		return
	original_gruzzles.change_difficulty(mode)

func draw_original_word_list(image: Image) -> void:
	if original_words == null:
		return
	var renderer = preload("res://scripts/core/wr1_frontend_render.gd")
	var words := preload("res://scripts/core/vocabulary.gd").display_words(original_words.words)
	image.blit_rect(renderer.asset("HELP.WR"),Rect2i(192,0,128,192),Vector2i(192,0))
	for i in range(7):
		var picture: Texture2D = preload("res://scripts/core/vocabulary.gd").load_picture(words[i])
		image.blit_rect(picture.get_image(),Rect2i(0,0,24,24),Vector2i(287,7+i*26))
		renderer.illustration(image,{"kind":"word_panel","slot":i,"destination":[200,10+i*26]}, {"words":words})

func _try_use_slime() -> void:
	if original_gruzzles == null:
		return
	if berserker_mode != null and berserker_mode.active:
		if not replay_ready or player.is_dead or player.original_recap != null or player.original_exit != null:
			return
		if not berserker_mode.can_fire():
			return
		var hits: Array[Dictionary] = original_gruzzles.berserker_blast(player.original_state)
		berserker_mode.fire(hits)
		if not hits.is_empty():
			GameManager.add_score(hits.size() * 50)
			hud.update_score(GameManager.score)
		_present_original_gruzzles()
	else:
		original_gruzzles.slime_request = true

func _on_word_revealed(word: String) -> void:
	hud.show_current_word(word)

func _on_correct_match(word: String) -> void:
	AudioManager.play_original("correct")
	hud.hide_current_word()
	GameManager.add_score(20)
	original_reward.start(20, word_manager.original_contact_grid + Vector2i(0,-2))
	hud.update_score(GameManager.score)
	hud.add_matched_word(word, word_manager.matched_count - 1)

func _on_wrong_match(pos: Vector2) -> void:
	AudioManager.play_original("wrong")
	hud.hide_current_word()
	if original_gruzzles != null:
		original_gruzzles.spawn(Vector2i(pos / 8.0))

func _on_all_words_matched() -> void:
	original_recap_pending = true
	original_door_state = 1
	if word_manager.original_model.mistakes == 0:
		GameManager.add_score(500)
		original_reward.start(500, word_manager.original_contact_grid + Vector2i(0,-2), 3)
		hud.update_score(GameManager.score)
