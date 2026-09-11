extends SceneTree

const Matching = preload("res://scripts/wr1_matching.gd")
var failures: int = 0
var checks: int = 0

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func fresh(w: int, p: int) -> RefCounted:
	var model := Matching.new()
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_01.json"))
	model.configure(data, w, p)
	return model

func _initialize() -> void:
	# Every distinct rotation must allow seven successes using reusable targets.
	for w in range(7):
		for p in range(7):
			if w == p:
				continue
			var model := fresh(w, p)
			var reward: int = 0
			for order in range(7):
				var source: int = -1
				for slot in range(7):
					if model.question_visible(slot):
						source = slot
						break
				check(source >= 0, "A source must remain reachable at match %d" % order)
				if source < 0:
					break
				var reveal: Dictionary = model.touch(source)
				check(reveal.kind == "reveal", "Source activates")
				check(model.touch(source).is_empty(), "Standing on source does not fail")
				var target: int = posmod(source + w - p, 7)
				var target_available: bool = model.available(target)
				var result: Dictionary = model.touch(target)
				check(result.kind == "correct", "Rotated target matches")
				check(result.order == order and model.matched_count == order + 1, "Completion order")
				check(not model.available(source), "Successful source consumed")
				check(model.available(target) == target_available, "Target availability unchanged")
				check(result.complete == (order == 6), "Unlock only after seven")
				reward += int(result.reward)
			check(reward == 640, "Seven perfect matches reward 140 + 500")
			check(model.completion_order.count(9) == 0, "Every word completed once")
	var wrong := fresh(5, 0)
	wrong.touch(0)
	var failed: Dictionary = wrong.touch(4)
	check(failed.kind == "wrong" and wrong.mistakes == 1, "Wrong picture records mistake")
	check(wrong.available(0) and wrong.available(4), "Wrong match restores source only")
	check(wrong.mistakes_for_word[5] == 1, "Mistake belongs to selected word")
	check(failed.spawn_grid == Vector2i(25, 13), "Gruzzle spawns one raw cell below target")
	check(wrong.touch(4).is_empty(), "Last target does not immediately activate")
	var total: int = 0
	while wrong.matched_count < 7:
		var source: int = -1
		for slot in range(7):
			if wrong.question_visible(slot):
				source = slot
				break
		if source < 0:
			check(false, "After mistake all remaining sources must be reachable")
			break
		wrong.touch(source)
		total += int(wrong.touch((source + 5) % 7).reward)
	check(total == 140, "One mistake suppresses perfect bonus")
	var scan := fresh(5, 0)
	check(scan.scan(7, 17).is_empty(), "One column outside contact does nothing")
	check(scan.scan(8, 18).is_empty(), "One row outside contact does nothing")
	check(scan.scan(8, 17).get("source", -1) == 0, "Inclusive five-row/three-column scan reaches source")
	check(scan.scan(8, 17).is_empty(), "Active source contact stops scan")
	var native := fresh(5, 0)
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_matching_events.json"))
	for event in fixture.events:
		native.touch(int(event.slot))
		for key in event.expected:
			var actual: int = int(native.active_slot >= 0) if key == "active_word" else int(native.get(key))
			check(actual == int(event.expected[key]), "Native matching transition: " + key)
	print("WR1 matching: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)
