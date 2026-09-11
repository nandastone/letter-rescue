extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	_check_original_idle_fixture()
	_check_keyboard_idle_fixture()
	quit(1 if failures else 0)

func _check_original_idle_fixture() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_idle_clock.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(16 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var cmf := FileAccess.get_file_as_bytes("res://" + fixture.music_file)
	var exact := 0
	var residuals := 0
	var differences := {669:-4, 675:-10, 681:-12, 687:14, 804:-14, 809:12, 815:-2, 845:15, 850:-9, 903:13, 909:-3}
	for case in fixture.cases:
		var model = preload("res://scripts/wr1_idle_clock.gd").new()
		model.configure(cmf, case.initial, fixture.event_names)
		compare(roundi(model.hardware.observed_time() * 27000.0), case.start_cycle, "start")
		var admission: int = model.until_admission()
		if not case.input_changes.is_empty():
			residuals += 1
			compare(admission - int(case.end_cycle), differences[int(case.start_call)], "external input residual")
			continue
		exact += 1
		compare(admission, case.end_cycle, "admission")
		compare(model.hardware.snapshot(), case.expected, "hardware")
		compare(model.entries, case.entries, "IRQ entries")
		for key in case.game:
			compare(model.game[key], case.game[key], "game." + key)
		compare(model.music.snapshot(), case.music, "music")
		compare(model.opl.snapshot(), case.opl, "opl")
	compare(exact, 54, "exact waits")
	compare(residuals, 11, "input waits")
	print("WR1 continuous idle clock: %d exact waits, %d preserved input residuals, %d checks, %d failures" % [exact, residuals, checks, failures])

func _check_keyboard_idle_fixture() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_idle_keyboard_clock.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(16 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var cmf := FileAccess.get_file_as_bytes("res://" + fixture.music_file)
	compare(fixture.cases.size(), 65, "keyboard wait count")
	for case in fixture.cases:
		var model = preload("res://scripts/wr1_idle_clock.gd").new()
		model.configure(cmf, case.initial, fixture.event_names)
		compare(model.until_admission(2000000, case.input_events), case.end_cycle, "admission")
		compare(model.hardware.snapshot(), case.expected, "hardware")
		for pair in [[model.entries, case.entries], [model.keyboard_entries, case.keyboard_entries]]:
			compare(pair[0].size(), pair[1].size(), "entry count")
			for i in range(pair[0].size()):
				var actual: Dictionary = pair[0][i]
				var expected: Dictionary = pair[1][i]
				var observed := {}
				for key in expected.hardware:
					observed[key] = actual.hardware[key]
				compare(observed, expected.hardware, "entry hardware")
				for key in expected:
					if key != "hardware":
						compare(actual[key], expected[key], "entry." + key)
		for key in case.game:
			compare(model.game[key], case.game[key], "game." + key)
		compare(model.keyboard_game, case.keyboard_game, "keyboard game")
		compare(model.music.snapshot(), case.music, "music")
		compare(model.opl.snapshot(), case.opl, "opl")
	print("WR1 continuous idle with timed keys: 65 exact waits, %d cumulative checks, %d failures" % [checks, failures])
