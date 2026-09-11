extends SceneTree
## One initial checkpoint, then CMF -> MIDI -> AdLib with native register evidence.

func _initialize() -> void:
	var failures := 0
	for name in ["wr1_opl_ticks.json", "wr1_opl_startup_ticks.json", "wr1_opl_loop_ticks.json.gz"]:
		failures += _check_fixture(name)
	quit(1 if failures else 0)

func _check_fixture(name: String) -> int:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/" + name)
	if name.ends_with(".gz"):
		raw = raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP)
	var fixture: Dictionary = JSON.parse_string(raw.get_string_from_utf8())
	var music = preload("res://scripts/legacy/wr1_music.gd").new()
	var opl = preload("res://scripts/legacy/wr1_opl.gd").new()
	var bytes := FileAccess.get_file_as_bytes("res://" + fixture.music_file)
	music.configure(bytes, fixture.initial)
	opl.configure(bytes, fixture.initial_opl)
	var failures := 0
	var count := 0
	for tick in fixture.ticks:
		var events: Array = music.tick()
		var writes := []
		for midi in events:
			writes.append_array(opl.event(midi))
		if music.restarted:
			writes.append_array(opl.restart())
		count += writes.size()
		# Round-trip actual values to normalize parsed float versus int values.
		for pair in [[events, tick.events], [writes, tick.writes], [music.snapshot(), tick.state], [opl.snapshot(), tick.opl_state]]:
			if JSON.parse_string(JSON.stringify(pair[0])) != pair[1]:
				if failures < 3:
					push_error("OPL tick %d: expected %s, got %s" % [tick.tick, pair[1], pair[0]])
				failures += 1
	print("WR1 AdLib: %d IRQ ticks, %d register writes, %d failures" % [fixture.ticks.size(), count, failures])
	return failures
