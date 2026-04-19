extends Node2D

# Main game scene. Coordinates level loading, player, and all game systems.

const TILE_SIZE := 16
const TILESET_COLS := 20

# Wiki: animated tiles cycle through the BG tile at (tx,ty) plus the next
# three tiles to the right of it in the tileset image. Frame rate was not
# pinned down in disassembly; tune against reference if needed.
const ANIM_FRAMES_PER_CYCLE := 4
const ANIM_TICKS_PER_FRAME := 8

var anim_cells: Array = []  # list of Vector2i tile-grid coords (16x16)
var anim_base_atlas: Array[Vector2i] = []  # atlas cell for frame 0 at each anim index
var anim_tick_count: int = 0

# Standard EGA 16-colour palette, matching DOSBox's VGA output for EGA content.
# Level files store `bg_colour` as an index 0-15; we fill the Background layer
# with the matching RGB so the sky/wall/floor colour matches the original.
const EGA_PALETTE: Array[Color] = [
	Color8(0, 0, 0),       Color8(0, 0, 170),       Color8(0, 170, 0),       Color8(0, 170, 170),
	Color8(170, 0, 0),     Color8(170, 0, 170),     Color8(170, 170, 0),     Color8(170, 170, 170),
	Color8(85, 85, 85),    Color8(85, 85, 255),     Color8(85, 255, 85),     Color8(85, 255, 255),
	Color8(255, 85, 85),   Color8(255, 85, 255),    Color8(255, 255, 85),    Color8(255, 255, 255),
]

@onready var player: CharacterBody2D = $Player
@onready var camera: Camera2D = $Camera
@onready var hud: CanvasLayer = $HUD
@onready var bg_tilemap: TileMapLayer = $BackgroundTileMapLayer
@onready var fg_tilemap: TileMapLayer = $ForegroundTileMapLayer
@onready var tilemap: TileMapLayer = $CollisionTileMapLayer
@onready var platform_tilemap: TileMapLayer = $PlatformTileMapLayer
@onready var background: ColorRect = $Background
@onready var entities: Node2D = $Entities
@onready var word_manager: Node = $WordManager
@onready var slime_system: Node = $SlimeSystem
@onready var mystery_word: Node = $MysteryWord
@onready var level_complete_ui: Control = $LevelCompleteUI

var question_block_scene: PackedScene
var gruzzle_scene: PackedScene
var collectible_scene: PackedScene
var exit_door_scene: PackedScene
var drip_scene: PackedScene

var spawn_position: Vector2 = Vector2.ZERO
var level_data: Dictionary = {}
var exit_door: Area2D = null
var is_level_ending: bool = false

func _ready() -> void:
	question_block_scene = load("res://scenes/question_block.tscn")
	gruzzle_scene = load("res://scenes/gruzzle.tscn")
	collectible_scene = load("res://scenes/collectible.tscn")
	exit_door_scene = load("res://scenes/exit_door.tscn")
	drip_scene = load("res://scenes/drip_hazard.tscn")

	# Connect signals.
	player.died.connect(_on_player_died)
	word_manager.correct_match.connect(_on_correct_match)
	word_manager.wrong_match.connect(_on_wrong_match)
	word_manager.all_words_matched.connect(_on_all_words_matched)
	word_manager.word_revealed.connect(_on_word_revealed)
	slime_system.slime_used.connect(hud.update_slime)
	slime_system.slime_collected.connect(hud.update_slime)
	mystery_word.letter_collected.connect(_on_mystery_letter_collected)
	mystery_word.word_completed.connect(_on_mystery_word_completed)
	level_complete_ui.next_level_requested.connect(_on_next_level)

	# Camera follows player.
	camera.target = camera.get_path_to(player)

	# Show level number.
	hud.update_level(GameManager.current_level)
	load_current_level()

func load_current_level() -> void:
	is_level_ending = false
	var path := LevelLoader.get_level_path(GameManager.current_level)
	level_data = LevelLoader.load_level(path)

	if level_data.is_empty():
		push_warning("No level data found, using test layout.")
		_setup_test_level()
		return

	_build_level_from_data()

func _build_level_from_data() -> void:
	# Clear existing entities.
	for child in entities.get_children():
		child.queue_free()

	# Wait one frame for queue_free to process.
	await get_tree().process_frame

	# Background colour from the level's EGA index.
	var bg_idx: int = int(level_data.get("bg_colour_ega", 0))
	if bg_idx >= 0 and bg_idx < EGA_PALETTE.size():
		background.color = EGA_PALETTE[bg_idx]

	# Player spawn. The level format's player_start is "bottom middle of the
	# exit-door image" (per ModdingWiki); for our clone's player, whose origin
	# is at feet, we snap to the next tile boundary so the character stands
	# on the ground at frame 0 instead of falling ~8px before landing.
	var start = level_data.get("player_start", [2, 10])
	var spawn_tile_y: float = ceil(float(start[1]))
	spawn_position = Vector2(start[0] * TILE_SIZE, spawn_tile_y * TILE_SIZE)
	player.global_position = spawn_position
	player.is_dead = false
	player.velocity = Vector2.ZERO

	# Build tilemaps. WR1 engine overwrites bg cells at level-load with
	# entity-specific tile indices (per wr1.exe disassembly at 0x6e6a/0x6eea):
	#   books -> tile 239, letters -> tile 238
	if level_data.has("collision"):
		_build_tilemap(level_data["collision"])
	if level_data.has("background_tiles"):
		_build_background(level_data["background_tiles"])
	_build_foreground(level_data.get("fg_tiles", []), level_data.get("background_tiles", []))
	_setup_animations(level_data.get("animations", []), level_data.get("background_tiles", []))

	# Spawn exit door.
	var door_pos = level_data.get("exit_door", [10, 10])
	exit_door = exit_door_scene.instantiate() as Area2D
	exit_door.global_position = Vector2(door_pos[0] * TILE_SIZE, door_pos[1] * TILE_SIZE)
	exit_door.player_entered_door.connect(_on_door_entered)
	entities.add_child(exit_door)

	# Question blocks: extracted STATIC.WR sprite, with the inner Sprite2D
	# offset (+26, +18) inside the entity scene (sprite-center = entity_pos
	# + (26, 18)). Derived from template-matching the extracted sprite
	# against reference frame 325, which lands the QB at world center
	# (entity_pos.x + 26, entity_pos.y + 18) = level data position +
	# (1 tile, 0.5 tile) + sprite-half = (16+10, 8+10) = (26, 18) world.
	var blocks: Array[Area2D] = []
	var block_positions = level_data.get("question_blocks", [])
	for pos in block_positions:
		var block := question_block_scene.instantiate() as Area2D
		block.global_position = Vector2(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE)
		entities.add_child(block)
		blocks.append(block)

	# Setup word manager.
	var words = level_data.get("words", ["cat", "dog", "hat", "sun", "cup", "bed", "pen"])
	word_manager.setup(words, blocks)

	# Setup mystery word from level data.
	var mystery: String = level_data.get("mystery_word", "word")
	mystery_word.setup(mystery)
	hud.setup_mystery_word(mystery.to_upper(), mystery_word.next_index)

	# Spawn gruzzles (limited by difficulty).
	var gruzzle_positions = level_data.get("gruzzles", [])
	var max_gruzzles := GameManager.get_gruzzle_count()
	for i in range(min(gruzzle_positions.size(), max_gruzzles)):
		_spawn_gruzzle(Vector2(gruzzle_positions[i][0] * TILE_SIZE, gruzzle_positions[i][1] * TILE_SIZE))

	# Spawn drip hazards.
	for drip_data in level_data.get("drips", []):
		var drip_pos = drip_data.get("pos", [0, 0])
		var drip_node := drip_scene.instantiate() as Node2D
		drip_node.global_position = Vector2(drip_pos[0] * TILE_SIZE, drip_pos[1] * TILE_SIZE)
		drip_node.setup(drip_data.get("max_y", 10))
		entities.add_child(drip_node)

	# Spawn slime buckets.
	for pos in level_data.get("slime_buckets", []):
		_spawn_collectible(Vector2(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE), "slime_bucket")

	# Books re-enabled with reference-cropped sprite + (+24, +6) offset.
	for pos in level_data.get("books", []):
		_spawn_collectible(Vector2(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE), "book")

	# Spawn mystery letters.
	var mystery_upper = mystery.to_upper()
	var letter_positions = level_data.get("mystery_letters", [])
	for i in range(min(mystery_upper.length(), letter_positions.size())):
		_spawn_collectible(
			Vector2(letter_positions[i][0] * TILE_SIZE, letter_positions[i][1] * TILE_SIZE),
			"letter",
			mystery_upper[i]
		)

	# Reset slime.
	slime_system.reset()
	hud.update_slime(slime_system.slime_count)
	hud.update_score(GameManager.score)
	hud.update_level(GameManager.current_level)

	# Set camera limits. The reference engine has a (+16, +40) viewport
	# offset — playfield starts at screen (16, 40). Mirror this by pulling
	# limit_left to -16 so the camera center can sit at world x=144 when the
	# player is at spawn (x=32), placing world x=0 at screen x=16.
	var map_width = level_data.get("width", 30)
	var map_height = level_data.get("height", 20)
	camera.limit_left = -16
	camera.limit_top = 0
	camera.limit_right = map_width * TILE_SIZE
	camera.limit_bottom = map_height * TILE_SIZE + 16

func _build_tilemap(collision_data: Array) -> void:
	# Collision at 8x8 resolution. Data in the JSON is the full mapWidth*2
	# wide attr grid in row-major 8x8 order. No padding/shift — disk byte 0
	# is world 8x8 cell (0, 0). Verified against DOSBox q-block positions
	# for level 1.
	tilemap.clear()
	platform_tilemap.clear()

	for y in range(collision_data.size()):
		var row = collision_data[y]
		for x in range(row.size()):
			if row[x] == 1:
				tilemap.set_cell(Vector2i(x, y), 0, Vector2i(0, 0))
			elif row[x] == 2:
				platform_tilemap.set_cell(Vector2i(x, y), 0, Vector2i(0, 0))

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
	# three tiles to the right in the tileset image. Physics tick drives it.
	anim_cells = []
	anim_base_atlas = []
	anim_tick_count = 0
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


func _physics_process(_delta: float) -> void:
	if anim_cells.is_empty():
		return
	anim_tick_count += 1
	var frame: int = (anim_tick_count / ANIM_TICKS_PER_FRAME) % ANIM_FRAMES_PER_CYCLE
	for i in range(anim_cells.size()):
		var cell: Vector2i = anim_cells[i]
		var base: Vector2i = anim_base_atlas[i]
		bg_tilemap.set_cell(cell, 0, Vector2i(base.x + frame, base.y))


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

func _setup_test_level() -> void:
	tilemap.clear()
	platform_tilemap.clear()

	# Simple test level.
	for x in range(40):
		tilemap.set_cell(Vector2i(x, 18), 0, Vector2i(0, 0))
		tilemap.set_cell(Vector2i(x, 19), 0, Vector2i(0, 0))

	for y in range(20):
		tilemap.set_cell(Vector2i(0, y), 0, Vector2i(0, 0))
		tilemap.set_cell(Vector2i(39, y), 0, Vector2i(0, 0))

	# Platforms.
	for x in range(5, 10):
		platform_tilemap.set_cell(Vector2i(x, 15), 0, Vector2i(0, 0))
	for x in range(15, 20):
		platform_tilemap.set_cell(Vector2i(x, 12), 0, Vector2i(0, 0))

	spawn_position = Vector2(2 * TILE_SIZE, 17 * TILE_SIZE)
	player.global_position = spawn_position

	# Exit door.
	exit_door = exit_door_scene.instantiate() as Area2D
	exit_door.global_position = Vector2(35 * TILE_SIZE, 17 * TILE_SIZE)
	exit_door.player_entered_door.connect(_on_door_entered)
	entities.add_child(exit_door)

	var test_words := ["cat", "dog", "hat", "sun", "cup", "bed", "pen"]
	var block_positions := [
		Vector2(6, 14), Vector2(12, 17), Vector2(18, 11),
		Vector2(25, 17), Vector2(30, 17), Vector2(8, 17), Vector2(16, 17)
	]

	var blocks: Array[Area2D] = []
	for i in range(test_words.size()):
		var block := question_block_scene.instantiate() as Area2D
		block.global_position = block_positions[i] * TILE_SIZE
		entities.add_child(block)
		blocks.append(block)

	word_manager.setup(test_words, blocks)
	mystery_word.setup("star")
	hud.setup_mystery_word(mystery_word.word, mystery_word.next_index)
	_spawn_gruzzle(Vector2(20 * TILE_SIZE, 17 * TILE_SIZE))
	slime_system.reset()
	hud.update_slime(slime_system.slime_count)
	hud.update_score(GameManager.score)
	hud.update_level(GameManager.current_level)
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = 40 * TILE_SIZE
	camera.limit_bottom = 20 * TILE_SIZE

func _spawn_gruzzle(pos: Vector2) -> void:
	var gruzzle := gruzzle_scene.instantiate() as CharacterBody2D
	gruzzle.global_position = pos
	gruzzle.set_player_reference(player)
	entities.add_child(gruzzle)

func _spawn_collectible(pos: Vector2, type: String, data: String = "") -> void:
	var collectible := collectible_scene.instantiate() as Area2D
	collectible.global_position = pos
	collectible.setup(type, data)
	entities.add_child(collectible)

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("use_slime") and not player.is_dead and not is_level_ending:
		_try_use_slime()
	# Return to menu on Escape.
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://scenes/main_menu.tscn")

func _try_use_slime() -> void:
	var nearest_dist := 64.0
	var nearest_gruzzle: CharacterBody2D = null

	for child in entities.get_children():
		if child is CharacterBody2D and child.has_method("get_slimed") and not child.is_slimed:
			var dist := player.global_position.distance_to(child.global_position)
			if dist < nearest_dist:
				var dir: float = child.global_position.x - player.global_position.x
				if (dir > 0 and player.facing_right) or (dir < 0 and not player.facing_right):
					nearest_dist = dist
					nearest_gruzzle = child

	if nearest_gruzzle and slime_system.use_slime():
		nearest_gruzzle.get_slimed()
		AudioManager.play("slime")
		GameManager.add_score(25)
		hud.update_score(GameManager.score)

func _on_player_died() -> void:
	AudioManager.play("death")
	hud.show_message("Oops! Try again!")
	await get_tree().create_timer(1.5).timeout
	word_manager.reset()
	load_current_level()

func _on_word_revealed(word: String) -> void:
	AudioManager.play("reveal")
	hud.show_current_word(word)

func _on_correct_match(word: String) -> void:
	AudioManager.play("correct")
	hud.hide_current_word()
	GameManager.add_score(50)
	hud.update_score(GameManager.score)
	hud.add_matched_word(word, word_manager.matched_count)
	hud.show_message("Great! You found: %s" % word.to_upper())

func _on_wrong_match(pos: Vector2) -> void:
	AudioManager.play("wrong")
	hud.hide_current_word()
	_spawn_gruzzle(pos)
	hud.show_message("Not quite! Try again!")

func _on_all_words_matched() -> void:
	AudioManager.play("unlock")
	hud.show_message("All words rescued! Find the exit door!")
	if exit_door:
		exit_door.unlock()

func _on_door_entered() -> void:
	if is_level_ending:
		return
	is_level_ending = true
	AudioManager.play("level_complete")
	GameManager.add_score(200)
	hud.update_score(GameManager.score)
	GameManager.save_progress()
	player.is_dead = true
	player.velocity = Vector2.ZERO
	level_complete_ui.show_results(
		GameManager.current_level,
		GameManager.score,
		word_manager.matched_count
	)

func _on_next_level() -> void:
	if GameManager.current_level >= 15:
		# All levels complete. Return to menu.
		hud.show_message("Congratulations! All levels complete!")
		await get_tree().create_timer(2.0).timeout
		get_tree().change_scene_to_file("res://scenes/main_menu.tscn")
		return
	GameManager.advance_level()
	load_current_level()

func _on_mystery_letter_collected(_letter: String, index: int) -> void:
	AudioManager.play("collect")
	GameManager.add_score(5)
	hud.update_score(GameManager.score)
	hud.update_mystery_letter(index)

func _on_mystery_word_completed(_word: String) -> void:
	AudioManager.play("correct")
	GameManager.add_score(100)
	hud.update_score(GameManager.score)
	slime_system.refill()
	hud.update_slime(slime_system.slime_count)
	hud.show_message("Mystery word complete! Slime refilled!")
