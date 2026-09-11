extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	_check_irq("wr1_irq_hardware", 561)
	_check_irq("wr1_irq_hardware_loop", 9641)
	quit(1 if failures else 0)

func _check_irq(name: String, count: int) -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/%s.json.gz" % name)
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(64 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var bytes := FileAccess.get_file_as_bytes("res://" + fixture.music_file)
	var music = preload("res://scripts/wr1_music.gd").new()
	var opl = preload("res://scripts/wr1_opl.gd").new()
	var work = preload("res://scripts/wr1_irq_work.gd").new()
	music.configure(bytes, fixture.initial_music)
	opl.configure(bytes, fixture.initial_opl)
	work.configure(bool(fixture.dispatcher_use_dx), int(fixture.external_timer))
	compare(fixture.cases.size(), count, "case_count")
	for i in range(fixture.cases.size()):
		var case: Dictionary = fixture.cases[i]
		var result: Dictionary = work.body(music, opl, case.initial_game)
		var model = preload("res://scripts/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "%d.end_cycle" % i)
		compare(model.snapshot(), case.expected, str(i))
		compare(result.state, case.expected_game, "%d.game" % i)
		compare(result.writes, case.writes, "%d.writes" % i)
		compare(music.snapshot(), case.music, "%d.music" % i)
		compare(opl.snapshot(), case.opl, "%d.opl" % i)
	print("WR1 timer body: %d calls, %d cumulative checks, %d failures" % [count, checks, failures])
