extends Node
## New game only. The recovered simulation still updates about 12 times a second
## in 8-pixel steps; this draws it at the display rate. Logical positions are
## never touched: each frame shifts the drawing (Sprite2D/Camera2D offset) back
## toward the previous logical position by the part of the step not yet played.
## Offsets are cleared before every physics tick, so gameplay and the 320x200
## reference captures always see exact positions.

const SNAP_DISTANCE := 16.0 # Longer moves are teleports or reused pool sprites.

var game: Node
var logical := {} # drawn node -> logical position at the last present
var lag := {} # drawn node -> previous minus current logical position
var ticks_since := 0 # Physics ticks since the last logical update.
var ticks_needed := 1 # Physics ticks this update lasts before the next one.

func _ready() -> void:
	game = get_parent()
	process_priority = 1000 # After everything else has placed its nodes.
	process_physics_priority = -1000 # Before replay input, presentation and gameplay.
	# Connected after game.gd's handler, so every sprite is placed by now.
	game.player.original_presented.connect(_on_presented)

## Pairs of [node holding the logical position, node whose drawing is offset].
func _tracked() -> Array:
	var pairs := [[game.player, game.player.original_sprite], [game.camera, game.camera]]
	if game.original_backdrop != null:
		pairs.append([game.original_backdrop, game.original_backdrop])
	for sprite in game.original_actor_sprites + game.original_drip_sprites:
		pairs.append([sprite, sprite])
	return pairs

func _on_presented(_state: RefCounted) -> void:
	_draw_offsets(0.0) # Presents can also happen outside a physics tick.
	var current := {}
	lag.clear()
	for pair in _tracked():
		var source: Node2D = pair[0]
		var drawn: Node2D = pair[1]
		if not is_instance_valid(source) or not is_instance_valid(drawn):
			continue
		current[drawn] = source.position
		var previous: Vector2 = logical.get(drawn, source.position)
		if drawn.is_visible_in_tree() and previous.distance_to(source.position) <= SNAP_DISTANCE:
			lag[drawn] = previous - source.position
	logical = current
	# Updates only happen on physics ticks, so a step lasts a whole number of
	# ticks. The gate keeps its sub-tick remainder, which fixes that count now.
	var tick := 1.0 / Engine.physics_ticks_per_second
	ticks_since = 0
	ticks_needed = maxi(1, ceili((_step_seconds() - game.player.original_elapsed) / tick - 0.0001))

func _step_seconds() -> float:
	return maxi(1, GameManager.original_speed_ticks) * 12428.0 / 1193182.0

## Fraction of the way from the previous logical update to the next one.
func _phase() -> float:
	var player: Node2D = game.player
	if not game.replay_ready or player.is_dead or player.original_recap != null \
			or player.original_rescue != null or player.original_exit != null:
		return 1.0
	var fraction := Engine.get_physics_interpolation_fraction()
	if InputReplay.mode == InputReplay.Mode.REPLAYING:
		# A replay advances the gate by its recorded source frame times, not by
		# the physics tick, so count the phase in simulated time instead.
		var elapsed: float = player.original_elapsed + fraction / Engine.physics_ticks_per_second
		return clampf(elapsed / _step_seconds(), 0.0, 1.0)
	return clampf((ticks_since + fraction) / ticks_needed, 0.0, 1.0)

func _draw_offsets(remaining: float) -> void:
	for drawn in lag:
		if is_instance_valid(drawn):
			drawn.offset = lag[drawn] * remaining
	game.camera.force_update_scroll()

func _physics_process(_delta: float) -> void:
	ticks_since += 1
	_draw_offsets(0.0)

func _process(_delta: float) -> void:
	_draw_offsets(1.0 - _phase())
