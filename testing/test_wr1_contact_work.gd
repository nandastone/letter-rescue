extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_contact_graphics.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(64 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/wr1_contact_work.gd").new()
	work.configure()
	var text = preload("res://scripts/wr1_text_work.gd").new()
	text.configure()
	var contacts := 0
	var primitives := 0
	for case in fixture.cases:
		var kind: String = case.kind
		if kind.begins_with("text_") or kind == "string_length":
			primitives += 1
			var result: Dictionary
			if kind in ["text_color", "text_background"]:
				result = text.style(kind, case)
			elif kind == "text_cursor":
				result = text.cursor(case)
			elif kind == "string_length":
				result = text.length(case)
				compare(result.value, case.result_ax, "string length")
				result.state = case.graphics_state
			else:
				result = text.string(case)
			var model = preload("res://scripts/wr1_hardware.gd").new()
			model.configure(case.initial, fixture.event_names)
			model.run_driver(result.work)
			compare(roundi(model.observed_time() * 27000.0), case.end_cycle, kind + " cycle")
			compare(model.snapshot(), case.expected, kind + " hardware")
			compare(result.state, case.expected_graphics_state, kind + " state")
		if kind != "contact":
			continue
		contacts += 1
		var before: Dictionary = case.duplicate(true)
		var graphics := {}
		for key in ["args", "graphics_state", "device_handle", "device_slot", "device_record", "device_descriptor", "graphics_flags", "fill_state", "text_state"]:
			graphics[key] = case[key]
		var result: Dictionary = work.body(case.contact, case.contact_attributes, graphics)
		compare(result.state, case.expected_contact, "contact state")
		compare(result.graphics_state, case.expected_graphics_state, "contact graphics")
		compare(result.attributes, case.expected_contact_attributes, "contact attributes")
		var model = preload("res://scripts/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "contact cycle")
		compare(model.snapshot(), case.expected, "contact hardware")
		var children: Array = []
		for child in fixture.cases:
			if child.kind != "contact" and child.start_cycle > case.start_cycle and child.end_cycle < case.end_cycle:
				children.append(child)
		children.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.start_cycle < b.start_cycle)
		compare(result.calls.size(), children.size(), "contact child count")
		for i in range(children.size()):
			var child: Dictionary = result.calls[i]
			var expected: Dictionary = children[i]
			compare(child.kind, expected.kind, "child kind")
			compare(child.args, expected.args, "child args")
			for item in [["start", "start_cycle", "initial"], ["return", "end_cycle", "expected"]]:
				model = preload("res://scripts/wr1_hardware.gd").new()
				model.configure(case.initial, fixture.event_names)
				model.run_driver(result.work.slice(0, int(child[item[0]])))
				compare(roundi(model.observed_time() * 27000.0), expected[item[1]], "child " + item[0])
				compare(model.snapshot(), expected[item[2]], "child hardware")
		compare(case, before, "preserved contact evidence")
	compare(contacts, 64, "native contacts")
	compare(primitives, 7, "native text primitives")
	print("WR1 contacts and text: %d contacts, %d text calls, %d checks, %d failures" % [contacts, primitives, checks, failures])
	quit(1 if failures else 0)
