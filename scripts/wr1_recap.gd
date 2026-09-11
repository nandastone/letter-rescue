extends RefCounted
## WR1.EXE 594c..5eb7. The recap renders without admitting gameplay updates.
const IRQ_SECONDS: float = 12428.0 / 1193182.0
var elapsed: float = 0.0
var events: Array[Dictionary] = []
var cursor: int = 0
var anchor := Vector2i.ZERO
var finished: bool = true
var skipped: bool = false
var random_calls: int = 0
var model_drawing_time: bool = false
var work_phase: float = 0.0
var drawing_work: Dictionary = {}
var scene_drawing: Callable
var sound_output: Callable
var service_clock: RefCounted
var clock_position_ms: float
var clock_irq_cursor: int = 0

func begin(p: RefCounted, completion_order: Array, irq_phase: float, drawing_time: bool = false, clock: RefCounted = null) -> void:
	assert(completion_order.size() == 7)
	var order_by_word: Array[int] = []
	order_by_word.assign(completion_order)
	events.clear()
	cursor = 0
	random_calls = 0
	finished = false
	skipped = false
	elapsed = fposmod(irq_phase, IRQ_SECONDS)
	model_drawing_time = drawing_time
	service_clock = clock
	if clock != null:
		clock_position_ms = clock.now_ms - irq_phase * 1000.0
		clock_irq_cursor = 0
	work_phase = 0.0
	if drawing_time:
		drawing_work = JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/recap_work.json")).work
	p.frame = 0
	p.facing = 1
	anchor = Vector2i(clampi(p.x - 80 if p.x > 66 else p.x + 8, 8, 152), 8)
	var target := clampi(p.y - 64, 66, 134)
	while anchor.y < target - 32:
		_helper(0)
		anchor.y += 8
	_helper(1)
	while anchor.y <= target:
		_helper(2)
		anchor.y += 4
	for frame in range(2, 6):
		_helper(frame)
	for order in range(7):
		var word_index: int = order_by_word.find(order)
		assert(word_index >= 0)
		_helper(6, order, word_index)
		# The DOS pixel-copy loop has no IRQ wait. The timing profile accounts
		# for its work; the visual transfer still appears as one completed blit.
		events.append({"kind":"transfer", "wait":0, "position":anchor, "order":order, "word_index":word_index})
		events.append({"kind":"wait", "wait":10, "sound":"recap"})
		for draw in range(20):
			events.append({"kind":"dissolve", "wait":8, "position":anchor,
				"frame":6 + draw % 5, "order":order, "word_index":word_index})
		events.append({"kind":"clear", "wait":0, "position":anchor})
		events.append({"kind":"wait", "wait":10})
	while anchor.y > 0:
		_helper(2)
		anchor.y -= 4

func _helper(frame: int, order: int = -1, word_index: int = -1) -> void:
	events.append({"kind":"helper", "wait":8, "position":anchor,
		"frame":frame, "order":order, "word_index":word_index})

func _work_seconds(event: Dictionary) -> float:
	if not model_drawing_time:
		return 0.0
	if scene_drawing.is_valid():
		var seconds: float = scene_drawing.call(event)
		if seconds >= 0.0:
			return seconds
	var kind: String = "panel" if event.kind == "helper" and event.order >= 0 else event.kind
	return float(drawing_work[kind].seconds) if drawing_work.has(kind) else 0.0

func _delay(event: Dictionary) -> float:
	return (event.wait * IRQ_SECONDS - work_phase if event.wait > 0 else 0.0) + _work_seconds(event)

func advance(seconds: float, p: RefCounted, random_word: Callable, render: Callable, present: Callable) -> bool:
	if service_clock != null:
		return _advance_serviced(p, random_word, render, present)
	elapsed += seconds
	while not finished and elapsed + 0.000000001 >= _delay(events[cursor]):
		var event: Dictionary = events[cursor].duplicate()
		var delay := _delay(event)
		elapsed -= delay
		work_phase = fposmod(work_phase + delay, IRQ_SECONDS)
		if event.has("sound") and sound_output.is_valid():
			sound_output.call(event.sound)
		if event.kind in ["helper", "dissolve"]:
			p.render_step()
			render.call()
		if event.kind == "dissolve":
			var pixels: Array[Vector2i] = []
			for i in range(40):
				var x: int = random_word.call() % 62 + 1
				var y: int = random_word.call() % 32 + 1
				pixels.append(Vector2i(x, y))
			random_calls += 80
			event["pixels"] = pixels
		if event.kind != "wait":
			present.call(event)
		cursor += 1
		finished = cursor == events.size()
		if finished:
			# Main gameplay inherits the timer phase, not just time left after
			# the final blit completed within the current frontend frame.
			elapsed += work_phase
	return finished

func _advance_serviced(p: RefCounted, random_word: Callable, render: Callable, present: Callable) -> bool:
	# Every helper resets DS:0F2E and waits for actual IRQ service. Music work
	# can coalesce PIT edges; elapsed wall time is not an interrupt counter.
	var interrupts: Array = service_clock.idle.entries
	var frame_end: float = service_clock.now_ms
	while not finished:
		while clock_irq_cursor < interrupts.size() and float(interrupts[clock_irq_cursor].return_ms) <= clock_position_ms:
			clock_irq_cursor += 1
		var event: Dictionary = events[cursor].duplicate()
		var ready: float = clock_position_ms
		if int(event.wait) > 0:
			var last: int = clock_irq_cursor + int(event.wait) - 1
			if last >= interrupts.size():
				break
			ready = float(interrupts[last].return_ms)
		var completed: float = ready + _work_seconds(event) * 1000.0
		# The CPU cannot draw while servicing the music driver. In particular,
		# a late wait completion can leave less than one drawing call before the
		# next IRQ, so its work must finish before the following timer reset.
		for index in range(clock_irq_cursor, interrupts.size()):
			var irq: Dictionary = interrupts[index]
			var started: float = float(irq.pic_cycle) / 27000.0
			if started >= completed:
				break
			if started >= ready:
				completed += float(irq.return_ms) - started
		if completed > frame_end:
			break
		clock_position_ms = completed
		elapsed = (frame_end - completed) / 1000.0
		if event.has("sound") and sound_output.is_valid():
			sound_output.call(event.sound)
		if event.kind in ["helper", "dissolve"]:
			p.render_step()
			render.call()
		if event.kind == "dissolve":
			var pixels: Array[Vector2i] = []
			for i in range(40):
				pixels.append(Vector2i(random_word.call() % 62 + 1, random_word.call() % 32 + 1))
			random_calls += 80
			event["pixels"] = pixels
		if event.kind != "wait":
			present.call(event)
		cursor += 1
		finished = cursor == events.size()
	return finished

func skip() -> void:
	# Unvisited dissolution draws must not consume randomness on a skip.
	finished = true
	skipped = true
	cursor = events.size()
