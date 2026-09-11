extends SceneTree
## CMF and live voice state -> work, checked against original-binary path digests.

func read_fixture(name: String) -> Dictionary:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/" + name)
	if name.ends_with(".gz"):
		raw = raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP)
	return JSON.parse_string(raw.get_string_from_utf8())

func _initialize() -> void:
	var failures := 0
	var all_work := read_fixture("wr1_driver_work.json.gz")
	for recording in all_work.recordings:
		var path: String = "res://testing/fixtures/" + recording.source
		if FileAccess.get_sha256(path) != recording.source_sha256:
			push_error("Stale work fixture: " + recording.source)
			failures += 1
			continue
		var fixture := read_fixture(recording.source)
		var bytes := FileAccess.get_file_as_bytes("res://" + fixture.music_file)
		var music = preload("res://scripts/wr1_music.gd").new()
		var opl = preload("res://scripts/wr1_opl.gd").new()
		var work = preload("res://scripts/wr1_driver_work.gd").new()
		music.configure(bytes, fixture.initial)
		opl.configure(bytes, fixture.initial_opl)
		work.configure()
		var index := 0
		for tick in fixture.ticks:
			if tick.tick > recording.last_tick:
				break
			var writes := []
			for midi in music.tick():
				var actual: Array = work.event(midi, opl.state)
				if index >= recording.events.size() or JSON.stringify(actual).sha256_text() != recording.events[index].work_sha256:
					if failures < 3:
						push_error("Different original work path: %s event %d" % [recording.source, index])
					failures += 1
				writes.append_array(opl.event(midi))
				index += 1
			if JSON.parse_string(JSON.stringify(writes)) != tick.writes:
				failures += 1
		if index != recording.events.size():
			failures += 1
		print("WR1 live driver work: %s, %d event paths, %d failures" % [recording.source, index, failures])
	var work = preload("res://scripts/wr1_driver_work.gd").new()
	work.configure()
	for case in all_work.constructed_cases:
		var opl = preload("res://scripts/wr1_opl.gd").new()
		opl.configure(FileAccess.get_file_as_bytes("res://" + all_work.constructed_music_file), case.initial_opl)
		var actual: Array = work.event(case.midi, opl.state)
		var writes: Array = opl.event(case.midi)
		if JSON.stringify(actual).sha256_text() != case.work_sha256 or JSON.parse_string(JSON.stringify(writes)) != case.writes or JSON.parse_string(JSON.stringify(opl.state)) != case.expected_opl:
			push_error("Different constructed driver path/state: " + case.label)
			failures += 1
	print("WR1 source experiments: %d constructed cases, %d failures" % [all_work.constructed_cases.size(), failures])
	quit(1 if failures else 0)
