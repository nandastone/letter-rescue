extends SceneTree
## Clock-only research probe. This does not execute gameplay or render images.
## Future native observations are read only after prediction, for comparison.

func fail(message: String) -> void:
	printerr(message)
	quit(2)

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 3 or args.size() > 4 or not args[0].is_valid_int() or not args[1].is_valid_int():
		fail("Usage: LEVEL UPDATE_COUNT OUTPUT_JSON [CANDIDATE_CLOCK_SCRIPT]")
		return
	var level := int(args[0])
	var count := int(args[1])
	var output: String = args[2]
	if level < 1 or level > 15 or count < 1 or FileAccess.file_exists(output):
		fail("Require level 1..15, positive update count, and a new output file")
		return
	var candidate: String = args[3] if args.size() == 4 else "res://scripts/wr1_music_clock.gd"
	var prefix := "res://testing/fixtures/wr1_demo_level%d" % level
	var replay_path := prefix + "_replay.json"
	var fixture_path := prefix + "_boundaries.json.gz"
	var replay: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(replay_path))
	var packed := FileAccess.get_file_as_bytes(fixture_path)
	var fixture: Dictionary = JSON.parse_string(packed.decompress_dynamic(512*1024*1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	if not fixture.get("complete", false) or count > fixture.updates.size():
		fail("Incomplete evidence or requested prefix exceeds recorded ordinary updates")
		return
	# This probe has no recap/rescue controller. Refuse prefixes crossing a
	# missing ordinary admission; silently comparing later indices is invalid.
	for index in range(count):
		var completed: Dictionary = fixture.updates[index].completed
		if completed.recap_pending or completed.death or completed.door_state:
			fail("Requested prefix reaches recap, rescue or exit state; use actual-game parity")
			return
		if index > 0 and int(fixture.updates[index].demo_index) != int(fixture.updates[index-1].demo_index) + 1:
			fail("Requested prefix crosses a modal/omitted admission; use actual-game parity")
			return
	for interrupted in fixture.interrupted_admissions:
		if float(interrupted.begin.pic_ms) <= float(fixture.updates[count-1].begin.pic_ms):
			fail("Requested prefix crosses an interrupted admission; use actual-game parity")
			return
	var frontend = preload("res://scripts/wr1_frontend_clock.gd").new()
	var clock = load(candidate).new()
	frontend.configure(replay.original_music_clock)
	clock.configure(replay.original_music_clock)
	var predicted: Array = []
	for frame in range(int(replay.total_frames)):
		for admission in clock.advance(frontend.next_seconds()):
			predicted.append({"counter":int(replay.source_start_frame)+frame+1,
				"pic_ms":clock.origin_ms + float(admission.at)*1000.0})
			if predicted.size() == count:
				break
		if predicted.size() == count:
			break
	if predicted.size() != count:
		fail("Clock did not produce the requested admissions")
		return
	var differences: Array = []
	for index in range(count):
		var native: Dictionary = fixture.updates[index].begin
		var model: Dictionary = predicted[index]
		if model.counter != int(native.launch_call):
			differences.append({"tick":index+1,"native_counter":native.launch_call,
				"model_counter":model.counter,"native_ms":native.pic_ms,"model_ms":model.pic_ms,
				"cycle_difference":roundi(model.pic_ms*27000.0)-roundi(float(native.pic_ms)*27000.0)})
	var report := {"scope":"Clock-only ordinary prefix; no gameplay, pixels or terminal validation",
		"level":level,"checked":count,"differences":differences,"predicted":predicted,
		"candidate":candidate,"candidate_sha256":FileAccess.get_sha256(candidate),
		"replay_sha256":FileAccess.get_sha256(replay_path),
		"fixture_sha256":FileAccess.get_sha256(fixture_path)}
	var error := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output.get_base_dir()))
	if error != OK:
		fail("Cannot create output directory: %s" % error_string(error))
		return
	var stream := FileAccess.open(output, FileAccess.WRITE)
	if stream == null:
		fail("Cannot write output: %s" % error_string(FileAccess.get_open_error()))
		return
	stream.store_string(JSON.stringify(report, "\t") + "\n")
	stream.close()
	print("Clock-only level %d: %d admissions, %d counter differences; %s" % [level,count,differences.size(),output])
	quit(0 if differences.is_empty() else 1)
