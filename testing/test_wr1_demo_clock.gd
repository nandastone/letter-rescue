extends SceneTree
## A single hardware/music checkpoint must predict the entire native demo gate.
func _initialize() -> void:
	var replay: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_demo_level4_replay.json"))
	var fixture: Dictionary = read_evidence("res://testing/fixtures/wr1_demo_level4_boundaries.json")
	var frontend = preload("res://scripts/legacy/wr1_frontend_clock.gd").new()
	var clock = preload("res://scripts/legacy/wr1_music_clock.gd").new()
	frontend.configure(replay.original_music_clock)
	clock.configure(replay.original_music_clock)
	var cursor := 0
	var failures := 0
	var overshoots := 0
	for frame in range(int(replay.total_frames)):
		for admission in clock.advance(frontend.next_seconds()):
			if cursor >= fixture.updates.size():
				break
			var counter: int = replay.source_start_frame + frame + 1
			var expected: Dictionary = fixture.updates[cursor].begin
			if counter != int(expected.launch_call):
				failures += 1
				push_error("Demo gate %d: counter %d != %d" % [cursor + 1, counter, int(expected.launch_call)])
			if admission.timer > 8:
				overshoots += 1
			cursor += 1
		if cursor == fixture.updates.size():
			break
	if cursor != 1624 or overshoots != 1:
		failures += 1
	print("WR1 demo clock: %d admissions, %d timer overshoots, %d failures" % [cursor, overshoots, failures])
	quit(1 if failures else 0)

func read_evidence(path: String) -> Dictionary:
	if FileAccess.file_exists(path):
		return JSON.parse_string(FileAccess.get_file_as_string(path))
	var packed := FileAccess.get_file_as_bytes(path + ".gz")
	return JSON.parse_string(packed.decompress_dynamic(512 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
