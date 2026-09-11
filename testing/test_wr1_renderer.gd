extends "res://testing/test_wr1_hardware.gd"

func _initialize() -> void:
	_check_renderer("prefix")
	_check_renderer("background")
	_check_renderer("tiles")
	_check_renderer("doors")
	_check_renderer("matching")
	_check_renderer("player")
	_check_renderer("actors")
	_check_renderer("complete")
	_check_renderer("complete", "rewards", 85)
	quit(1 if failures else 0)

func _check_renderer(kind: String, fixture_name: String = "", expected_count: int = 75) -> void:
	var label := kind if fixture_name.is_empty() else fixture_name
	var raw := FileAccess.get_file_as_bytes("res://testing/fixtures/wr1_renderer_%s.json.gz" % label)
	var fixture: Dictionary = JSON.parse_string(raw.decompress_dynamic(32 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var work = preload("res://scripts/wr1_renderer_work.gd").new()
	work.configure()
	var count := 0
	for case in fixture.cases:
		var result: Dictionary
		if kind == "prefix":
			result = work.prefix(case.initial_prefix, case.graphics)
		elif kind == "background":
			result = work.background(case.initial_prefix, case.graphics, case.background)
		elif kind == "tiles":
			result = work.tiles(case.initial_prefix, case.graphics, case.background, case.tiles)
			compare(result.tiles, case.expected_tiles, "tile animation state")
		elif kind == "doors":
			result = work.doors(case.initial_prefix, case.graphics, case.background, case.tiles, case.doors)
			compare(result.tiles, case.expected_tiles, "tile animation state")
			compare(result.doors, case.expected_doors, "entrance countdown and door state")
		else:
			if kind == "matching":
				result = work.matching(case.initial_prefix, case.graphics, case.background, case.tiles, case.doors, case.matching)
			elif kind == "player":
				result = work.player(case.initial_prefix, case.graphics, case.background, case.tiles, case.doors, case.matching, case.player)
			elif kind == "actors":
				result = work.actors(case.initial_prefix, case.graphics, case.background, case.tiles, case.doors, case.matching, case.player, case.actors, case.actor_images)
				compare(result.actors, case.expected_actors, "enemy animation and drip state")
			else:
				result = work.complete(case.initial_prefix, case.graphics, case.background, case.tiles, case.doors, case.matching, case.player, case.actors, case.actor_images, case.tail)
				compare(result.actors, case.expected_actors, "enemy animation and effect state")
				compare(result.tail, case.expected_tail, "renderer tail state")
			compare(result.tiles, case.expected_tiles, "tile animation state")
			compare(result.doors, case.expected_doors, "entrance countdown and door state")
			compare(case.matching, case.expected_matching, "unchanged matching state")
			compare(case.player, case.expected_player, "unchanged player frame and image headers")
		var model = preload("res://scripts/wr1_hardware.gd").new()
		model.configure(case.initial, fixture.event_names)
		model.run_driver(result.work)
		compare(roundi(model.observed_time() * 27000.0), case.end_cycle, "prefix completion")
		compare(model.snapshot(), case.expected, "prefix hardware")
		compare(result.state, case.prefix, "camera and animation state")
		compare(result.graphics_state, case.expected_graphics_state, "graphics state")
		compare(result.calls.size(), case.calls.size(), "child call count")
		for i in range(result.calls.size()):
			var call: Dictionary = result.calls[i]
			var expected: Dictionary = case.calls[i]
			compare(call.kind, expected.kind, "generated call kind")
			compare(call.args, expected.args, "generated call arguments")
			for boundary in [["start", "entry_cycle", "initial"], ["return", "return_cycle", "expected"]]:
				model = preload("res://scripts/wr1_hardware.gd").new()
				model.configure(case.initial, fixture.event_names)
				model.run_driver(result.work.slice(0, int(call[boundary[0]])))
				compare(roundi(model.observed_time() * 27000.0), expected[boundary[1]], "child boundary cycle")
				compare(model.snapshot(), expected[boundary[2]], "child boundary hardware")
		count += 1
	compare(count, expected_count, "native renderer interval count")
	print("WR1 renderer %s: %d exact intervals and child-call boundaries, %d cumulative checks, %d failures" % [label, count, checks, failures])
