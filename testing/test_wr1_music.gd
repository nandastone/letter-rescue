extends SceneTree
## One observed initial state, then independent sequencing through native IRQs.

func _initialize() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_music_ticks.json"))
	var model = preload("res://scripts/legacy/wr1_music.gd").new()
	var bytes := FileAccess.get_file_as_bytes("res://" + fixture.music_file)
	model.configure(bytes, fixture.initial)
	var checks := 0
	var failures := 0
	var events := 0
	for tick in fixture.ticks:
		# JSON numbers parse as floats; nested Dictionary equality is type-strict.
		for track in tick.state.tracks:
			for key in track:
				track[key] = int(track[key])
		events += model.tick().size()
		var actual: Dictionary = model.snapshot()
		for key in tick.state:
			checks += 1
			if actual[key] != tick.state[key]:
				if failures < 3:
					push_error("Music tick %d field %s: expected %s, got %s" % [tick.tick,key,tick.state[key],actual[key]])
				failures += 1
	print("WR1 music: %d IRQ ticks, %d events, %d checks, %d failures" % [fixture.ticks.size(),events,checks,failures])
	quit(1 if failures else 0)
