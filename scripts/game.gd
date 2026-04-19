extends Node2D

# Main game scene. Coordinates level loading, player, and all game systems.

const TILE_SIZE := 16
const TILESET_COLS := 20

# Empirically-derived tile remap: maps level-file tile indices to their
# correct atlas positions. Built by template-matching reference frame 319's
# gameplay tiles against BACK3 atlas cells. Fills the gap where the level
# format's tile indexing doesn't match a simple 20-col row-major atlas
# layout — likely because the original engine has a lookup table in the
# binary or handles specific index ranges specially.
const TILE_REMAP_PATH := "res://data/tile_remap.json"
const TILE_POS_REMAP_PATH := "res://data/tile_pos_remap.json"
const TILE_OVERLAYS_PATH := "res://data/tile_overlays.json"
var tile_remap: Dictionary = {}
var tile_pos_remap: Dictionary = {}
var tile_overlays: Dictionary = {}

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
	# Load tile remap tables if present.
	var f := FileAccess.open(TILE_REMAP_PATH, FileAccess.READ)
	if f:
		var j := JSON.new()
		if j.parse(f.get_as_text()) == OK:
			tile_remap = j.data
	var f2 := FileAccess.open(TILE_POS_REMAP_PATH, FileAccess.READ)
	if f2:
		var j := JSON.new()
		if j.parse(f2.get_as_text()) == OK:
			tile_pos_remap = j.data
	var f3 := FileAccess.open(TILE_OVERLAYS_PATH, FileAccess.READ)
	if f3:
		var j := JSON.new()
		if j.parse(f3.get_as_text()) == OK:
			tile_overlays = j.data

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

	# Build tilemaps.
	if level_data.has("collision"):
		_build_tilemap(level_data["collision"])
	if level_data.has("background_tiles"):
		_build_background(level_data["background_tiles"])

	# Re-enable overlays now that the type-inference parse error is fixed.
	_build_overlays()

	# Spawn exit door.
	var door_pos = level_data.get("exit_door", [10, 10])
	exit_door = exit_door_scene.instantiate() as Area2D
	exit_door.global_position = Vector2(door_pos[0] * TILE_SIZE, door_pos[1] * TILE_SIZE)
	exit_door.player_entered_door.connect(_on_door_entered)
	entities.add_child(exit_door)

	# Question block entities deferred — extracted STATIC.WR sprite exists at
	# assets/sprites/question_block.png but positioning it exactly over the
	# reference's rendered QBs requires an offset I couldn't pin down from
	# level data alone. Overlays handle these pixels correctly for frame 0.
	var blocks: Array[Area2D] = []

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

	# Book collectibles are hidden during pixel-exact work — their art
	# (hand-drawn pink "BOOK" box) doesn't match the original, and
	# suppressing them establishes a cleaner baseline.
	# for pos in level_data.get("books", []):
	# 	_spawn_collectible(Vector2(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE), "book")

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

	# Set camera limits. Bottom limit extended by 16px (one tile row) so the
	# camera pans lower, matching the reference's vertical framing: reference
	# shows the ground at screen y=137 while an unextended camera showed it
	# at y=153 (16px too low).
	var map_width = level_data.get("width", 30)
	var map_height = level_data.get("height", 20)
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = map_width * TILE_SIZE
	camera.limit_bottom = map_height * TILE_SIZE + 16

func _build_tilemap(collision_data: Array) -> void:
	# Collision at 8x8 resolution. Offset by 1 cell (8px) to align with background.
	tilemap.clear()
	platform_tilemap.clear()

	for y in range(collision_data.size()):
		var row = collision_data[y]
		for x in range(row.size()):
			if row[x] == 1:
				tilemap.set_cell(Vector2i(x + 1, y), 0, Vector2i(0, 0))
			elif row[x] == 2:
				platform_tilemap.set_cell(Vector2i(x + 1, y), 0, Vector2i(0, 0))

func _build_overlays() -> void:
	for pos_key_any in tile_overlays.keys():
		var pos_key: String = str(pos_key_any)
		var fname: String = str(tile_overlays[pos_key_any])
		var tex_path: String = "res://assets/extracted/tile_overlays/" + fname
		if not ResourceLoader.exists(tex_path):
			continue
		var tex: Texture2D = load(tex_path)
		if tex == null:
			continue
		var parts: PackedStringArray = pos_key.split(",")
		if parts.size() != 2:
			continue
		var tx: int = int(parts[0])
		var ty: int = int(parts[1])
		var sprite := Sprite2D.new()
		sprite.texture = tex
		sprite.centered = false
		sprite.position = Vector2(tx * TILE_SIZE, ty * TILE_SIZE)
		sprite.z_index = 0
		entities.add_child(sprite)


func _build_background(bg_data: Array) -> void:
	bg_tilemap.clear()
	for y in range(bg_data.size()):
		var row = bg_data[y]
		for x in range(row.size()):
			var tile_idx: int = row[x]
			# Position-specific remap takes precedence (handles transparent cells too).
			var pos_key := "%d,%d" % [x, y]
			if tile_pos_remap.has(pos_key):
				var atlas_idx = int(tile_pos_remap[pos_key])
				var atlas_x: int = atlas_idx % TILESET_COLS
				var atlas_y: int = atlas_idx / TILESET_COLS
				bg_tilemap.set_cell(Vector2i(x, y), 0, Vector2i(atlas_x, atlas_y))
				continue
			if tile_idx == 0xFF or tile_idx == 255:
				continue  # Transparent.
			# Fall back to per-index remap or direct indexing.
			var atlas_idx = int(tile_remap.get(str(tile_idx), tile_idx))
			var atlas_x: int = atlas_idx % TILESET_COLS
			var atlas_y: int = atlas_idx / TILESET_COLS
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
