extends Node
## Default game only. The recovered simulation updates about 12 times a second
## in 8-pixel steps (and its rescue/exit sequences on their own cadences); this
## draws them at the display rate. Logical positions are never touched: each
## frame shifts the drawing (Sprite2D/Camera2D offset) back toward the previous
## logical position by the part of the step not yet played. Offsets are cleared
## before every physics tick, so gameplay and the 320x200 reference captures
## always see exact positions.

const SNAP_DISTANCE := 16.0 # Longer moves are teleports or reused pool sprites.
const MAX_INTERVAL_TICKS := 64

var game: Node
var logical := {} # drawn node -> position when it last moved
var lag := {} # drawn node -> previous minus current logical position
var moved_at := {} # drawn node -> physics tick when it last moved
var interval := {} # drawn node -> fixed duration of its current interpolation
var ticks: int = 0

func _ready() -> void:
	game = get_parent()
	process_priority = 1000 # After everything else has placed its nodes.
	process_physics_priority = -1000 # Before replay input, presentation and gameplay.

## Pairs of [node holding the logical position, node whose drawing is offset].
func _tracked() -> Array:
	var player: Node2D = game.player
	var pairs := [[game.camera, game.camera]]
	if player.original_sprite != null:
		pairs.append([player, player.original_sprite])
	if player.original_rescue_sprite != null:
		pairs.append([player.original_rescue_sprite, player.original_rescue_sprite])
	if game.original_backdrop != null:
		pairs.append([game.original_backdrop, game.original_backdrop])
	for sprite in game.original_actor_sprites + game.original_drip_sprites:
		pairs.append([sprite, sprite])
	return pairs

## Record moved nodes and fix the duration of each new interpolation.
func _sample() -> void:
	var seen := {}
	for pair in _tracked():
		var source: Node2D = pair[0]
		var drawn: Node2D = pair[1]
		if not is_instance_valid(source) or not is_instance_valid(drawn):
			continue
		seen[drawn] = true
		if not logical.has(drawn):
			logical[drawn] = source.position # First sight: nothing to interpolate yet.
			moved_at[drawn] = ticks
			continue
		var previous: Vector2 = logical[drawn]
		if previous == source.position:
			continue
		logical[drawn] = source.position
		interval[drawn] = clampi(ticks - int(moved_at.get(drawn, ticks)), 1, MAX_INTERVAL_TICKS)
		moved_at[drawn] = ticks
		if drawn == game.player.original_sprite or drawn == game.camera:
			var player: Node2D = game.player
			var ordinary: bool = game.replay_ready and not player.is_dead and player.original_recap == null \
				and player.original_rescue == null and player.original_exit == null
			if ordinary and InputReplay.mode != InputReplay.Mode.REPLAYING:
				# Fix the deadline when the move happens. Recomputing it every frame
				# extends the last move at each idle update, making its offset rebound
				# and decay long after the player and camera have stopped.
				interval[drawn] = _step_ticks()
		var snap_distance := SNAP_DISTANCE
		if game.berserker_mode != null and game.berserker_mode.active and drawn in [game.player.original_sprite, game.camera]:
			snap_distance = 32.0
		if drawn.is_visible_in_tree() and previous.distance_to(source.position) <= snap_distance:
			lag[drawn] = previous - source.position
		else:
			lag.erase(drawn) # Teleport, reused pool sprite, or a hidden node.
	for drawn in lag.keys():
		if not seen.has(drawn):
			lag.erase(drawn)

func _step_ticks() -> int:
	var step: float = maxi(1, GameManager.original_speed_ticks) * 12428.0 / 1193182.0
	var remainder: float = game.player.original_elapsed
	return maxi(1, ceili((step - remainder) * Engine.physics_ticks_per_second - 0.0001))

## How far through its current move each node should be drawn.
func _weight(drawn: Node2D) -> float:
	var expected: int = int(interval.get(drawn, 1))
	var elapsed: float = ticks - int(moved_at.get(drawn, ticks)) + Engine.get_physics_interpolation_fraction()
	return clampf(elapsed / maxf(1.0, float(expected)), 0.0, 1.0)

func _draw_offsets(played: bool) -> void:
	for drawn in lag:
		if is_instance_valid(drawn):
			drawn.offset = lag[drawn] * (1.0 - _weight(drawn) if played else 0.0)
	game.camera.force_update_scroll()

func _physics_process(_delta: float) -> void:
	ticks += 1
	_draw_offsets(false)
	# Sample after gameplay has moved everything for this tick.
	_sample.call_deferred()

func _process(_delta: float) -> void:
	_draw_offsets(true)
