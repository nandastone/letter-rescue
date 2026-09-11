extends SceneTree
## Native OPL call experiments, without feeding the model future hardware events.
var failures := 0
var checks := 0

func compare(actual: Variant, expected: Variant, path: String) -> void:
	if actual is Dictionary:
		for key in actual:
			compare(actual[key], expected[key], path + "." + str(key))
	elif actual is Array:
		if actual.size() != expected.size():
			failures += 1
			push_error("Different hardware array length: " + path)
			return
		for i in range(actual.size()):
			compare(actual[i], expected[i], "%s[%d]" % [path, i])
	else:
		checks += 1
		var equal: bool = absf(float(actual) - float(expected)) < 1e-8 if actual is float or actual is int else actual == expected
		if not equal:
			if failures < 3:
				push_error("%s: expected %s, got %s" % [path, expected, actual])
			failures += 1

func _initialize() -> void:
	for name in ["wr1_opl_hardware", "wr1_opl_hardware_loop"]:
		check_recording(name)
	check_driver()
	quit(1 if failures else 0)

func check_recording(name: String) -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/%s.json.gz" % name)
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	for i in range(fixture.cases.size()):
		var case: Dictionary = fixture.cases[i]
		var model = preload("res://scripts/legacy/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		compare(model.opl(), case.cycles, "%d.cycles" % i)
		compare(model.snapshot(), case.expected, str(i))
	print("WR1 hardware: %d OPL calls, %d checks, %d failures" % [fixture.cases.size(), checks, failures])

func check_driver() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_driver_hardware.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/legacy/wr1_driver_work.gd").new()
	work.configure()
	var opl = preload("res://scripts/legacy/wr1_opl.gd").new()
	opl.configure(FileAccess.get_file_as_bytes("res://" + fixture.music_file), fixture.initial_opl)
	for i in range(fixture.cases.size()):
		var case: Dictionary = fixture.cases[i]
		var model = preload("res://scripts/legacy/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		var path: Array = work.event(case.midi, opl.state)
		compare(path, case.work, "%d.work" % i)
		compare(opl.event(case.midi), case.writes, "%d.writes" % i)
		model.run_driver(path)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "%d.end_cycle" % i)
		compare(model.snapshot(), case.expected, str(i))
	print("WR1 hardware: %d complete MIDI calls, %d checks, %d failures" % [fixture.cases.size(), checks, failures])
