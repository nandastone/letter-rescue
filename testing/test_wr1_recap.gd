extends SceneTree
var checks := 0
var failures := 0
var p: RefCounted
var actors: RefCounted
var pictures: RefCounted
var reward: RefCounted
var rendered: Array = []
var recap: RefCounted

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _initialize() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://testing/fixtures/wr1_recap_stages.json"))
	var start: Dictionary = fixture.begin
	p = preload("res://scripts/wr1_motion.gd").new()
	p.configure(JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_01.json")))
	for key in ["x", "y", "gx", "gy", "camera_x", "camera_y", "phase", "facing", "background_frame"]:
		p.set(key, int(start[key]))
	p.frame = int(start.sprite)
	actors = preload("res://scripts/wr1_gruzzles.gd").new()
	actors.configure([], 0, start)
	actors.render_page = int(start.render_page)
	pictures = preload("res://scripts/wr1_picture_animation.gd").new()
	pictures.configure(start)
	pictures.enabled = false
	reward = preload("res://scripts/wr1_reward_popup.gd").new()
	reward.ticks = int(start.reward_timer)
	reward.grid = Vector2i(start.reward_x, start.reward_y)
	reward.bonus = int(start.reward_bonus)
	recap = preload("res://scripts/wr1_recap.gd").new()
	recap.begin(p, fixture.completion_order, 0.0)
	var irqs := 0
	while not recap.finished and irqs < 4000:
		recap.advance(recap.IRQ_SECONDS, p, actors.random_word, render, present)
		irqs += 1
	check(recap.finished, "Recap returns to gameplay")
	check(irqs == 1580, "Recovered waits total 1580 IRQs; DOS drawing overhead is separate")
	check(recap.random_calls == 11200 and actors.rng == int(fixture.end.rng), "All 11200 random calls reach native return seed")
	check(rendered.size() == fixture.renders.size(), "Native recap renderer count")
	for i in range(mini(rendered.size(), fixture.renders.size())):
		var expected: Dictionary = fixture.renders[i]
		check(rendered[i].draw == expected.draw, "Recap draw %d: frame, position, word, order" % i)
		for key in ["x", "y", "gx", "gy", "camera_x", "camera_y", "phase", "sprite", "facing", "background_frame",
				"rng", "entity_timer", "gruzzles", "render_page", "picture_timers", "picture_frames", "picture_animation_enabled", "reward_timer"]:
			check(rendered[i].state[key] == expected.state[key], "Recap draw %d: %s" % [i, key])
	check(p.ticks == 0 and actors.entity_timer == int(start.entity_timer), "Recap admits no gameplay updates")
	# Skip must preserve exactly the RNG already consumed, including mid-word.
	recap.begin(p, fixture.completion_order, 0.0)
	recap.advance(20 * recap.IRQ_SECONDS, p, actors.random_word, render, present)
	var seed: int = actors.rng
	recap.skip()
	check(recap.advance(100.0, p, actors.random_word, render, present) and actors.rng == seed, "Skip does not fast-forward RNG")
	# Drawing work must count timer edges independently of the host's frame
	# rate. The median workload is an estimate, so compare its duration to the
	# native envelope separately from the exact same-input return-frame test.
	var native_seconds: float = (float(fixture.end.pic_ms) - float(start.pic_ms)) / 1000.0
	for fps in [60,70,120]:
		recap.begin(p, fixture.completion_order, 0.0, true)
		var frames := 0
		var old_count := rendered.size()
		while not recap.finished and frames < fps * 20:
			recap.advance(1.0 / fps,p,actors.random_word,render,present)
			frames += 1
		check(recap.finished and rendered.size()-old_count == 180, "Drawing clock preserves all renders at %d Hz" % fps)
		check(recap.random_calls == 11200, "Drawing clock preserves RNG call count")
		check(absf(float(frames)/fps-native_seconds) <= 2 * recap.IRQ_SECONDS, "Median work stays within two IRQs of native duration")
	print("WR1 recap: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)

func render() -> void:
	actors.render_step(p)
	pictures.step()
	reward.render_step(p, actors.render_page)

func present(event: Dictionary) -> void:
	if event.kind not in ["helper", "dissolve"]:
		return
	var state: Dictionary = p.snapshot()
	state.merge(actors.snapshot())
	state.merge(pictures.snapshot())
	state.merge(reward.snapshot())
	state["render_page"] = actors.render_page
	var draw := event.duplicate()
	draw.erase("wait")
	draw.erase("pixels")
	draw.position = [int(event.position.x), int(event.position.y)]
	rendered.append(JSON.parse_string(JSON.stringify({"draw":draw, "state":state})))
