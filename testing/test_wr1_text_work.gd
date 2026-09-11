extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	var text = preload("res://scripts/wr1_text_work.gd").new()
	text.configure()
	for item in [["wr1_contact_graphics", 7], ["wr1_text_matching_graphics", 151], ["wr1_reward_graphics", 237]]:
		var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/%s.json.gz" % item[0])
		var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(64 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
		var count := 0
		for case in fixture.cases:
			var kind: String = case.kind
			if not kind.begins_with("text_") and kind != "string_length":
				continue
			count += 1
			var result: Dictionary
			if kind in ["text_color", "text_background"]:
				result = text.style(kind, case)
			elif kind == "text_cursor":
				result = text.cursor(case)
			elif kind == "string_length":
				result = text.length(case)
				compare(result.value, case.result_ax, "string length")
				result.state = case.graphics_state
			elif kind == "text_font":
				result = text.font(case)
				compare(result.font, case.expected_text_state, "font state")
			else:
				result = text.string(case)
			var model = preload("res://scripts/wr1_hardware.gd").new()
			model.configure(case.initial, fixture.event_names)
			model.run_driver(result.work)
			compare(roundi(model.observed_time() * 27000.0), case.end_cycle, kind + " cycle")
			compare(model.snapshot(), case.expected, kind + " hardware")
			compare(result.state, case.expected_graphics_state, kind + " state")
		compare(count, item[1], "native text count")
		print("%s: %d text calls, %d cumulative checks, %d failures" % [item[0], count, checks, failures])
	quit(1 if failures else 0)
