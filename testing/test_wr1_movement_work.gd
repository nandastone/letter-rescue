extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	for item in [["wr1_movement_work", 65], ["wr1_movement_walk_jump", 71], ["wr1_movement_held_jump", 41]]:
		var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/%s.json.gz" % item[0])
		var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
		compare(fixture.cases.size(), item[1], "movement count")
		var work = preload("res://scripts/wr1_movement_work.gd").new()
		work.configure()
		for case in fixture.cases:
			var before: Dictionary = case.movement.duplicate(true)
			var result: Dictionary = work.step(case.movement, case.attributes)
			compare(result.state, case.expected_movement, "movement state")
			var model = preload("res://scripts/wr1_hardware.gd").new()
			model.configure(case.initial, fixture.event_names)
			model.run_driver(result.work)
			compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "movement cycle")
			compare(model.snapshot(), case.expected, "movement hardware")
			compare(case.movement, before, "initial movement preserved")
		print("%s: %d intervals, %d cumulative checks, %d failures" % [item[0], fixture.cases.size(), checks, failures])
	quit(1 if failures else 0)
