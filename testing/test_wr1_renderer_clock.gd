extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_renderer_clock.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(64 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var cmf := FileAccess.get_file_as_bytes("res://" + fixture.music_file)
	compare(fixture.cases.size(), 64, "renderer-to-admission count")
	compare(fixture.excluded.size(), 11, "explicit transition exclusions")
	for case in fixture.cases:
		var model = preload("res://scripts/wr1_renderer_clock.gd").new()
		model.configure(cmf, case.initial, fixture.event_names)
		model.finish_render(case.renderer, case.post, case.display_state, int(case.return_cs))
		var renderer: Dictionary = case.renderer
		var expected := {"renderer_return":{"hardware":renderer.expected, "cycle":renderer.end_cycle},
			"display_entry":case.display_entry, "display_return":case.display_return, "update_done":case.update_done}
		for name in expected:
			compare(model.checkpoints[name].cycle, expected[name].cycle, name + " cycle")
			var observed := {}
			for key in expected[name].hardware:
				observed[key] = model.checkpoints[name].hardware[key]
			compare(observed, expected[name].hardware, name + " hardware")
		compare(model.display_state, case.display_return.state, "display state")
		for pair in [["state", "prefix"], ["graphics_state", "expected_graphics_state"],
			["tiles", "expected_tiles"], ["doors", "expected_doors"], ["actors", "expected_actors"], ["tail", "expected_tail"]]:
			compare(model.result[pair[0]], renderer[pair[1]], pair[0])
		var wait: Dictionary = case.wait
		compare(model.until_admission(wait.input_events), case.end_cycle, "admission cycle")
		compare(model.idle.hardware.snapshot(), wait.expected, "admission hardware")
		for pair in [[model.idle.entries, wait.entries], [model.idle.keyboard_entries, wait.keyboard_entries]]:
			compare(pair[0].size(), pair[1].size(), "IRQ entry count")
			for i in range(pair[0].size()):
				var actual: Dictionary = pair[0][i]
				var entry: Dictionary = pair[1][i]
				var observed := {}
				for key in entry.hardware:
					observed[key] = actual.hardware[key]
				compare(observed, entry.hardware, "IRQ hardware")
				for key in entry:
					if key != "hardware":
						compare(actual[key], entry[key], "IRQ " + key)
		for key in wait.game:
			compare(model.idle.game[key], wait.game[key], "game " + key)
		compare(model.idle.keyboard_game, wait.keyboard_game, "keyboard game")
		compare(model.idle.music.snapshot(), wait.music, "music")
		compare(model.idle.opl.snapshot(), wait.opl, "OPL")
	print("WR1 renderer through admission: 64 exact intervals, %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
