extends SceneTree
var checks := 0
var failures := 0
var rendered: Array = []
var p: RefCounted
var actors: RefCounted

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_rescue_stages.json"))
	var start: Dictionary = fixture.begin
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_01.json"))
	p = preload("res://scripts/wr1_motion.gd").new()
	p.configure(data)
	for key in ["x", "y", "gx", "gy", "camera_x", "camera_y", "phase", "facing", "background_frame"]:
		p.set(key, int(start[key]))
	p.frame = int(start.sprite)
	actors = preload("res://scripts/wr1_gruzzles.gd").new()
	actors.configure([], 0, start)
	actors.death = true
	var rescue = preload("res://scripts/wr1_rescue.gd").new()
	rescue.begin(p, Vector2i(start.destination_x, start.destination_y), 0.0)
	var done := false
	for tick in range(194):
		done = rescue.advance(rescue.IRQ_SECONDS, p, present)
		if tick < 193:
			check(not done, "Rescue must wait through IRQ %d" % (tick + 1))
	check(done, "194 IRQs complete the measured rescue")
	check(rendered.size() == fixture.renders.size(), "Exactly 23 extra renderer calls")
	for i in range(mini(rendered.size(), fixture.renders.size())):
		var native: Dictionary = fixture.renders[i]
		for key in ["x", "y", "gx", "gy", "camera_x", "camera_y", "sprite", "background_frame", "rng", "entity_timer", "gruzzles"]:
			check(JSON.parse_string(JSON.stringify(rendered[i][key])) == native[key], "Rescue renderer %d: %s" % [i, key])
	check(p.x == 48 and p.y == 136 and p.frame == 17 and p.camera_y == 5, "Final native return pose")
	var saved_timers: Array = actors.timers.duplicate()
	var reset: Dictionary = actors.restart([[52,17],[52,2],[62,6],[102,6]], 0)
	check(reset == {"word_offset":3,"picture_offset":4,"mystery_index":1}, "Native reset RNG choices")
	check(actors.rng == 3482209081 and actors.actors[0].type == 0, "All ten reset slots consume RNG")
	check(actors.entity_timer == 58 and actors.timers == saved_timers, "Reset preserves slot and action timers")
	check(not actors.death and actors.actors[0].gx == 52 and actors.actors[0].gy == 17, "Respawn restores active actor")
	for mode in range(3):
		actors.slime_used = 5
		actors.restart([[52,17]], mode)
		check(actors.slime_used == [0,3,5][mode], "Difficulty-specific death refill")
	print("WR1 rescue: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)

func present(kind: String, _position: Vector2i) -> void:
	if kind in ["descend", "ascend"]:
		actors.render_step(p)
		var state: Dictionary = p.snapshot()
		state.merge(actors.snapshot())
		rendered.append(state)
