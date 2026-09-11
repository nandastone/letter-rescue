extends SceneTree
## Smoke test for the default game: play headlessly and check that it runs and
## that motion is drawn between the 12 Hz updates. The demo parity suite covers
## legacy only; this is the default game's gate.
##
##   godot --headless --fixed-fps 120 --path . --script tools/smoke_default_game.gd
##   godot --headless --fixed-fps 120 --path . --script tools/smoke_default_game.gd \
##       -- --replay data/wr1/demos/level1.json
##
## Live play admits updates on the default game's own 240 Hz tick, so the drawn
## step stays near 8 px / 20 ticks. A replay follows its recorded 70 Hz source
## clock, so an update can land up to a tick away from its ideal time.

const FRAMES := 900
const MIN_MOVING_FRAMES := 100

var sampler: Node
var replaying: bool
var checked: bool
var waited: int

func _initialize() -> void:
	replaying = "--replay" in OS.get_cmdline_user_args()
	change_scene_to_file.call_deferred("res://scenes/game.tscn")
	process_frame.connect(_attach)


func _attach() -> void:
	var game := current_scene
	waited += 1
	if waited > FRAMES * 4:
		# Also catches a sampler that never reported (e.g. a script error).
		printerr("smoke FAILED: no sampled run after %d frames" % waited)
		quit(1)
	if sampler != null or game == null or not game.has_method("is_replay_ready") or not game.is_replay_ready():
		return
	if not replaying:
		Input.action_press("move_right") # Live play: walk for the whole sample.
	sampler = Node.new()
	sampler.process_priority = 5000
	sampler.set_script(load("res://tools/smoke_sampler.gd"))
	sampler.frames = FRAMES
	sampler.done.connect(_check)
	game.add_child(sampler)

func _check(rows: Array) -> void:
	checked = true
	var moved: Array[float] = []
	var largest := 0.0
	var teleports := 0
	for i in range(1, rows.size()):
		if rows[i][3] or rows[i - 1][3]:
			continue # Death, rescue, recap or exit sequence.
		var step := absf(rows[i][1] - rows[i - 1][1]) + absf(rows[i][2] - rows[i - 1][2])
		if step >= 16.0:
			teleports += 1 # Death respawn or level change; smoothing snaps on purpose.
			continue
		largest = maxf(largest, step)
		if step > 0.0:
			moved.append(step)
	# Deaths, rescues and level changes snap by design, so judge the typical
	# frame: without smoothing every moving frame would step a whole 8 px.
	moved.sort()
	var typical: float = moved[int(moved.size() * 0.99)] if moved.size() > 0 else 0.0
	var limit := 4.0 if replaying else 2.0
	var updates: int = rows[-1][0] - rows[0][0]
	var failures: Array[String] = []
	if updates < 10:
		failures.append("only %d logical updates ran" % updates)
	if moved.size() < MIN_MOVING_FRAMES:
		failures.append("player moved on %d frames, expected at least %d" % [moved.size(), MIN_MOVING_FRAMES])
	if typical > limit:
		failures.append("99th percentile drawn step %.2f px exceeds %.2f (motion is not being smoothed)" % [typical, limit])
	print("smoke[%s]: %d frames, %d updates, moved on %d frames, 99th pct step %.2f px, largest %.2f px, %d teleports" % [
		"replay" if replaying else "live", rows.size(), updates, moved.size(), typical, largest, teleports])
	for failure in failures:
		printerr("smoke FAILED: " + failure)
	quit(1 if failures else 0)
