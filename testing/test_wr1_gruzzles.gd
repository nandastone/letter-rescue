extends SceneTree
## Edge conditions recovered from WR1.EXE; native replay tests cover full scenes.
var checks := 0
var failures := 0

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(message)

func _initialize() -> void:
	var p = preload("res://scripts/core/wr1_motion.gd").new()
	var grid: Array = []
	for y in range(40):
		var row: Array = []
		row.resize(100)
		row.fill(0x73 if y == 30 else 0)
		grid.append(row)
	p.configure({"attributes":grid,"start":[10,30]})
	p.camera_x = 0
	p.camera_y = 10
	p.gx = 10
	p.gy = 30
	var model = preload("res://scripts/core/wr1_gruzzles.gd").new()
	model.configure([[15,12]],0)
	model.entity_timer = 7
	model.slime_request = true
	model.step(p)
	check(model.actors[0].state == 0 and model.slime_used == 1, "Facing scan reaches an actor eighteen cells above player")
	check(p.frame == 11 and model.entity_timer == 0, "Accepted action sets pose and resets cooldown")
	var reward := 0
	for i in range(24):
		reward += model.render_step(p)
	check(reward == 10 and model.actors[0].state == 24, "One reward at slime completion")
	model.render_step(p)
	check(not model.action_busy, "Completed slime releases action lock")
	# A removed actor does not bring its old movement timer into the earlier slot.
	model.configure([[80,17]],0)
	model.actors[0].state = 24
	model.spawn(Vector2i(90,17))
	model.actors[1].state = -1
	model.timers[0] = 6
	model.timers[1] = 99
	model.step(p)
	check(model.actors.size() == 1 and model.actors[0].gx == 90, "Offscreen corpse compacts actors")
	check(model.timers[0] == 8 and model.timers[1] == 99, "Compacted actor visits retained slot timer a second time")
	# Exhaustion still accepts the action/cooldown but cannot start another slime.
	model.configure([[15,12]],0)
	model.slime_used = 5
	model.entity_timer = 7
	model.slime_request = true
	model.step(p)
	check(model.slime_used == 5 and model.actors[0].state == -1 and model.entity_timer == 0, "Five-use cap")
	model.action_busy = true
	model.entity_timer = 20
	model.slime_request = true
	model.step(p)
	check(model.entity_timer == 21 and not model.slime_request, "Busy request is consumed without resetting timer")
	# Collision bounds use cell anchors and ignore non-normal actors.
	model.configure([[12,29]],0)
	model.step(p)
	check(model.death, "Normal actor contact marks player death")
	model.configure([[12,29]],0)
	model.actors[0].state = 4
	model.step(p)
	check(not model.death, "Sliming actor is harmless")
	print("WR1 gruzzles: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
