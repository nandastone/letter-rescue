extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_keyboard_hardware.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(4 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/wr1_keyboard_work.gd").new()
	work.configure()
	compare(fixture.cases.size(), 24, "keyboard body count")
	for case in fixture.cases:
		var model = preload("res://scripts/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		var result: Dictionary = work.body(case.initial_game, int(case.initial.keyboard.port60))
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "keyboard completion")
		compare(model.snapshot(), case.expected, "keyboard hardware")
		compare(result.state, case.game, "keyboard game state")
	print("WR1 keyboard: 24 exact interrupt bodies, %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
