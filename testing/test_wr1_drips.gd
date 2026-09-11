extends SceneTree
var checks := 0
var failures := 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_drips_stages.json"))
	var level: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/levels/level_14.json"))
	var model = preload("res://scripts/core/wr1_drips.gd").new()
	model.configure(level.drips)
	check(JSON.parse_string(JSON.stringify(model.snapshot())) == fixture.begin.drips, "Native drip initialization")
	for state in fixture.updates:
		check(not model.step(state.gx,state.gy,0), "Easy drips cannot kill")
		check(JSON.parse_string(JSON.stringify(model.snapshot())) == state.drips, "Native drip positions, release frames and reset at %d" % state.launch_call)
	# Exercise each side of the binary's strict collision inequalities.
	for difficulty in range(3):
		for gx in range(26,33):
			for gy in range(56,63):
				var drop = preload("res://scripts/core/wr1_drips.gd").new()
				drop.configure([level.drips[0]]) # first release is x30,y57
				var expected := difficulty > 0 and gx in [28,29] and gy in [59,60]
				check(drop.step(gx,gy,difficulty) == expected, "Strict lethal contact %d,%d/%d" % [gx,gy,difficulty])
				check(drop.drips[0].frame == (2 if expected else 1), "Impact uses frame2")
	var drop = preload("res://scripts/core/wr1_drips.gd").new()
	drop.configure([level.drips[0]])
	drop.step(28,60,1)
	check(drop.draws(29,56).size() == 1, "Impact frame can be drawn")
	check(drop.draws(30,56).is_empty() and drop.draws(-6,56).is_empty(), "Strict horizontal viewport edges")
	check(drop.draws(29,57).is_empty() and drop.draws(29,38).is_empty(), "Strict vertical viewport edges")
	# New-file loader initializes Y but never writes the persistent frame slots.
	drop.configure([level.drips[0]])
	check(drop.drips[0].frame == 2 and drop.drips[0].y == 54, "Reload preserves frame slot while restoring origin")
	print("WR1 drips: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
