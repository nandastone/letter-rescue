extends SceneTree
var checks := 0
var failures := 0
var frames: Array[int] = []

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_exit_stages.json"))
	var start: Dictionary = fixture.begin
	var transition = preload("res://scripts/wr1_exit.gd").new()
	for x in range(75, 81):
		for y in range(20, 24):
			check(transition.touches(x,y,Vector2i(78,17)) == (x in [77,78] and y == 22), "Exact original door contact")
	var p = preload("res://scripts/wr1_motion.gd").new()
	p.configure(JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_01.json")))
	for key in ["x", "y", "gx", "gy", "camera_x", "camera_y", "phase", "facing", "background_frame"]:
		p.set(key, int(start[key]))
	p.frame = int(start.sprite)
	var actors = preload("res://scripts/wr1_gruzzles.gd").new()
	actors.configure([],0,start)
	actors.render_page = int(start.render_page)
	actors.actors.clear()
	p.render_step()
	actors.render_step(p)
	var state: Dictionary = p.snapshot()
	state.merge(actors.snapshot())
	for key in ["x", "y", "gx", "gy", "camera_x", "camera_y", "sprite", "background_frame", "rng", "gruzzles", "entity_timer"]:
		check(JSON.parse_string(JSON.stringify(state[key])) == fixture.extra_render[key], "Exit extra render: " + key)
	transition.begin(0.0, true)
	for irq in range(132):
		var done: bool = transition.advance(transition.IRQ_SECONDS, present)
		check(done == (irq == 131), "Five door waits plus six bonus flashes")
	check(frames == [1,2,3,4,5,5,5,5,5,5,5], "Door frame sequence")
	check(p.background_frame == int(fixture.end.background_frame) and actors.rng == int(fixture.end.rng), "Door blits do not update the world")
	check(fixture.end.score == start.score, "Original bonus caption does not add an exit reward in this trace")
	var level: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/levels/level_02.json"))
	var starts: Array = []
	for pos in level.gruzzles:
		starts.append([int(pos[0]*2),int(pos[1]*2)])
	var reset: Dictionary = actors.restart(starts,0,true)
	check(reset == {"word_offset":5,"picture_offset":6,"mystery_index":4}, "New-level random choices")
	check(actors.rng == int(fixture.reset_end.rng), "17 loader random calls, including four overwritten types")
	check(JSON.parse_string(JSON.stringify(actors.snapshot().gruzzles)) == fixture.reset_end.gruzzles, "New-level actors and retained slot timers")
	var spawn = preload("res://scripts/wr1_motion.gd").new()
	spawn.configure(JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_02.json")))
	for key in ["x","y","gx","gy","camera_x","camera_y"]:
		check(spawn.get(key) == int(fixture.reset_end[key]), "Fresh-level spawn: " + key)
	frames.clear()
	transition.begin(0.0, false)
	check(not transition.advance(59 * transition.IRQ_SECONDS, present), "Slime-used exit waits 60 IRQs")
	check(transition.advance(transition.IRQ_SECONDS, present) and frames == [1,2,3,4,5], "Slime-used exit omits bonus flash")
	print("WR1 exit: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)

func present(frame: int, _bonus: bool, _flash: int) -> void:
	frames.append(frame)
