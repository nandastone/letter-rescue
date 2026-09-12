extends SceneTree
## Real-scene regression for motion that keeps wobbling after input is released.
## godot --headless --fixed-fps 120 --path . --script tools/smoke_motion_settling.gd -- --original-seed 20716

var waited := 0
var sampler: Node

func _initialize() -> void:
	change_scene_to_file.call_deferred("res://scenes/game.tscn")
	process_frame.connect(_attach)

func _attach() -> void:
	waited += 1
	if waited > 4000:
		printerr("settling FAILED: game did not finish the sample")
		quit(1)
	var game := current_scene
	if sampler != null or game == null or not game.has_method("is_replay_ready") or not game.is_replay_ready():
		return
	sampler = SettlingSampler.new()
	sampler.process_priority = 5000
	game.add_child(sampler)

class SettlingSampler extends Node:
	const WALK_SECONDS := 1.75
	const REST_SECONDS := 1.5
	var direction := "move_right"
	var elapsed := 0.0
	var last_positions := {}
	var stationary_since := {}
	var moved := {}
	var violations := {}
	var checked := {}
	var peak_offset := 0.0
	var previous_offsets := {}
	var rebounds := {}
	var checked_seconds := {}

	func _ready() -> void:
		Input.action_press(direction)

	func _process(delta: float) -> void:
		elapsed += delta
		var game := get_parent()
		var player: Node2D = game.player
		if elapsed >= WALK_SECONDS:
			Input.action_release(direction)
		var step_seconds: float = maxi(1, get_node("/root/GameManager").original_speed_ticks) * 12428.0 / 1193182.0
		var allowance := step_seconds + 2.0 / Engine.physics_ticks_per_second
		for pair in [["player", player, player.original_sprite], ["camera", game.camera, game.camera]]:
			var label: String = pair[0]
			var source: Node2D = pair[1]
			var drawn: Node2D = pair[2]
			if not last_positions.has(label) or last_positions[label] != source.position:
				if last_positions.has(label):
					moved[label] = true
				last_positions[label] = source.position
				stationary_since[label] = elapsed
			if elapsed >= WALK_SECONDS and elapsed - float(stationary_since[label]) > allowance:
				checked[label] = int(checked.get(label, 0)) + 1
				checked_seconds[label] = float(checked_seconds.get(label, 0.0)) + delta
				peak_offset = maxf(peak_offset, drawn.offset.length())
				if drawn.offset.length() > 0.001:
					violations[label] = int(violations.get(label, 0)) + 1
				if previous_offsets.has(label) and drawn.offset.length() > float(previous_offsets[label]) + 0.001:
					rebounds[label] = int(rebounds.get(label, 0)) + 1
				previous_offsets[label] = drawn.offset.length()
		if elapsed >= WALK_SECONDS + REST_SECONDS:
			var failures: Array[String] = []
			for label in ["player", "camera"]:
				if not moved.has(label) or float(checked_seconds.get(label, 0.0)) < 1.0:
					failures.append("%s did not move then remain stationary long enough" % label)
				if violations.has(label):
					failures.append("%s still offset on %d stationary frames" % [label, violations[label]])
			print("settling[%s]: checked %s, late offsets %s, rebounds %s, peak late offset %.3f px" % [direction, checked, violations, rebounds, peak_offset])
			for failure in failures:
				printerr("settling FAILED: " + failure)
			if failures or direction == "move_left":
				get_tree().quit(1 if failures else 0)
				return
			# Restart after a full rest, then stop in the opposite direction too.
			direction = "move_left"
			elapsed = 0.0
			last_positions.clear()
			stationary_since.clear()
			moved.clear()
			checked.clear()
			checked_seconds.clear()
			previous_offsets.clear()
			Input.action_press(direction)
