extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	_check_page()
	_check_copy()
	_check_masked()
	_check_display()
	_check_fills()
	quit(1 if failures else 0)

func _check_page() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_graphics_profile.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(16 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/legacy/wr1_graphics_work.gd").new()
	work.configure()
	var count := 0
	for case in fixture.cases:
		if case.kind != "draw_page":
			continue
		var model = preload("res://scripts/legacy/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		var result: Dictionary = work.draw_page(case)
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "completion")
		compare(model.snapshot(), case.expected, "hardware")
		compare(result.state, case.expected_graphics_state, "drawing state")
		compare(case.result_ax, 0, "return status")
		count += 1
	compare(count, 129, "drawing page cases")
	print("WR1 graphics: %d exact drawing-page selections, %d checks, %d failures" % [count, checks, failures])

func _check_copy() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_copy_bios.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/legacy/wr1_graphics_work.gd").new()
	work.configure()
	var count := 0
	for case in fixture.cases:
		if case.kind != "copy_rect":
			continue
		var model = preload("res://scripts/legacy/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		var result: Dictionary = work.copy_rect(case)
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "copy completion")
		compare(model.snapshot(), case.expected, "copy hardware")
		compare(result.args, case.expected_args, "clipped copy arguments")
		compare(case.result_ax, 0, "copy return status")
		compare(case.clock_state, case.expected_clock_state, "no timer IRQ in sample")
		count += 1
	compare(count, 1050, "copy count")
	print("WR1 graphics: %d exact aligned EGA copies, %d cumulative checks, %d failures" % [count, checks, failures])

func _check_masked() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_masked_work.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/legacy/wr1_graphics_work.gd").new()
	work.configure()
	var count := 0
	for case in fixture.cases:
		if case.kind != "masked_sprite":
			continue
		var model = preload("res://scripts/legacy/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		model.run_driver(work.masked_sprite(case))
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "sprite completion")
		compare(model.snapshot(), case.expected, "sprite hardware")
		compare(case.result_ax, 0, "sprite return status")
		compare(case.image_header, case.expected_image_header, "unchanged image header")
		compare(case.clock_state, case.expected_clock_state, "no timer IRQ in sprite sample")
		count += 1
	compare(count, 198, "sprite count")
	print("WR1 graphics: %d exact masked sprite draws, %d cumulative checks, %d failures" % [count, checks, failures])

func _check_display() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_display_work.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/legacy/wr1_graphics_work.gd").new()
	work.configure()
	var count := 0
	for case in fixture.cases:
		if case.kind != "display_page":
			continue
		var model = preload("res://scripts/legacy/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		var result: Dictionary = work.display_page(case)
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "display completion")
		compare(model.snapshot(), case.expected, "display hardware")
		compare(result.state, case.expected_display_state, "BIOS and game display state")
		compare(case.result_ax, 0, "display return status")
		count += 1
	compare(count, 64, "display count")
	print("WR1 graphics: %d exact display-page selections, %d cumulative checks, %d failures" % [count, checks, failures])

func _check_fills() -> void:
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_fill_work.json.gz")
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/legacy/wr1_graphics_work.gd").new()
	work.configure()
	var counts := {"fill_style":0, "fill_rect":0, "fill_raw":0}
	for case in fixture.cases:
		if not counts.has(case.kind):
			continue
		var model = preload("res://scripts/legacy/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		var result: Dictionary = work.call(case.kind, case)
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "fill completion")
		compare(model.snapshot(), case.expected, "fill hardware")
		compare(case.result_ax, 0, "fill status")
		compare(case.fill_state, case.expected_fill_state, "unchanged fill dispatch")
		if case.kind == "fill_raw":
			compare(case.graphics_state, case.expected_graphics_state, "unchanged graphics state")
		else:
			compare(result.state, case.expected_graphics_state, "fill graphics state")
		if case.kind != "fill_style":
			compare(result.args, case.expected_args, "fill arguments")
			compare(case.clock_state, case.expected_clock_state, "no timer IRQ during fill")
		counts[case.kind] += 1
	compare(counts, {"fill_style":128, "fill_rect":58, "fill_raw":58}, "fill counts")
	print("WR1 graphics: 128 fill styles, 58 rectangles and 58 EGA children, %d cumulative checks, %d failures" % [checks, failures])
