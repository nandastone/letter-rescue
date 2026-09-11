extends "res://testing/test_wr1_hardware.gd"
## The shared comparison helper checks every final hardware field.

func _initialize() -> void:
	_check_music("wr1_music_hardware", 561)
	_check_music("wr1_music_hardware_loop", 9281)
	_check_music("wr1_music_hardware_repeat", 9641)
	quit(1 if failures else 0)

func _check_music(name: String, count: int) -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/%s.json.gz" % name)
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var bytes := FileAccess.get_file_as_bytes("res://" + fixture.music_file)
	var music = preload("res://scripts/wr1_music.gd").new()
	var opl = preload("res://scripts/wr1_opl.gd").new()
	var work = preload("res://scripts/wr1_music_work.gd").new()
	music.configure(bytes, fixture.initial_music)
	opl.configure(bytes, fixture.initial_opl)
	work.configure(bool(fixture.dispatcher_use_dx), int(fixture.get("external_timer", -1)))
	for i in range(count):
		var case: Dictionary = fixture.cases[i]
		var result: Dictionary = work.tick(music, opl)
		var model = preload("res://scripts/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "%d.end_cycle" % i)
		compare(model.snapshot(), case.expected, str(i))
		compare(result.writes, case.writes, "%d.writes" % i)
		compare(music.snapshot(), case.music, "%d.music" % i)
		compare(opl.snapshot(), case.opl, "%d.opl" % i)
	print("WR1 complete music interrupt: %d calls, %d checks, %d failures" % [count, checks, failures])
	for case in fixture.get("repeat_memory_cases", []):
		var model = preload("res://scripts/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		model.run_driver([["rep:%d" % int(case.count), int(case.ip)]])
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "rep.end_cycle")
		compare(model.snapshot(), case.expected, "rep.hardware")
	if fixture.has("repeat_memory_cases"):
		print("WR1 REP memory: %d calls, %d cumulative checks, %d failures" % [fixture.repeat_memory_cases.size(), checks, failures])
