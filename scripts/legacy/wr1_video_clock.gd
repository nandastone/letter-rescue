extends RefCounted
## Two video pages and independent VGA latch/scanout. Times are seconds.
## Drawing submissions contain owned images, never live gameplay objects.
var now: float = 0.0
var period: float = 1.0 / 70.086304
var retrace: float = 0.013092353525323
var part_period: float = 0.003177755710030
var next_start: float
var next_latch: float
var next_part: float = INF
var selected_page: int = 0
var latched_page: int = 0
var scan_page: int = 0
var part: int = 0
var pages: Array[Image] = []
var scan: Image
var completed: Image
var pending: Array[Dictionary] = []
var sequence: int = 0
var completed_frames: int = 0

static func valid_timing(timing: Dictionary) -> bool:
	var defaults := {"period": 1.0 / 70.086304, "retrace": 0.013092353525323,
		"part_period": 0.003177755710030, "frame_start": 0.0, "page": 0}
	for key in timing:
		if not defaults.has(key) or not (timing[key] is float or timing[key] is int):
			return false
		if not is_finite(float(timing[key])):
			return false
		defaults[key] = timing[key]
	return ((float(defaults.page) == 0.0 or float(defaults.page) == 1.0) and defaults.period > 0.0
		and defaults.retrace > 0.0 and defaults.retrace < defaults.period
		and defaults.part_period > 0.0 and defaults.part_period * 4.0 < defaults.period
		and defaults.frame_start <= 0.0 and defaults.frame_start >= -defaults.period)

func reset(initial: Image, timing: Dictionary = {}) -> void:
	assert(initial.get_size() == Vector2i(320, 200))
	assert(valid_timing(timing), "Invalid initial VGA timing")
	now = 0.0
	period = float(timing.get("period", 1.0 / 70.086304))
	retrace = float(timing.get("retrace", 0.013092353525323))
	part_period = float(timing.get("part_period", 0.003177755710030))
	assert(period > 0.0 and retrace > 0.0 and retrace < period)
	assert(part_period > 0.0 and part_period * 4.0 < period)
	selected_page = int(timing.get("page", 0))
	latched_page = selected_page
	scan_page = selected_page
	pages.assign([initial.duplicate(), initial.duplicate()])
	scan = initial.duplicate()
	completed = initial.duplicate()
	pending.clear()
	sequence = 0
	completed_frames = 0
	var start: float = float(timing.get("frame_start", 0.0))
	# The checkpoint supplies the already visible image. Complete the remaining
	# scanout from that image; never simulate loading or invent an older screen.
	while start + period <= 0.0:
		start += period
	while start > 0.0:
		start -= period
	next_start = start + period
	next_latch = start + retrace
	if next_latch <= 0.0:
		next_latch += period
	part = clampi(int(floor(-start / part_period)), 0, 4)
	next_part = start + (part + 1) * part_period if part < 4 else INF

func write_page(at: float, page: int, image: Image) -> void:
	assert(page in [0, 1] and image.get_size() == Vector2i(320, 200))
	_enqueue({"at": at, "kind": "write", "page": page, "image": image.duplicate()})

func select_page(at: float, page: int) -> void:
	assert(page in [0, 1])
	_enqueue({"at": at, "kind": "select", "page": page})

func _enqueue(event: Dictionary) -> void:
	assert(float(event.at) + 0.000000001 >= now, "Cannot submit drawing into elapsed video time")
	event["at"] = maxf(now, float(event.at))
	event["sequence"] = sequence
	sequence += 1
	pending.append(event)
	pending.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return a.sequence < b.sequence if a.at == b.at else a.at < b.at)

func advance(to: float) -> void:
	assert(to + 0.000000001 >= now, "Video clock cannot run backwards")
	while true:
		var write_time: float = INF if pending.is_empty() else float(pending[0].at)
		var due: float = minf(minf(write_time, next_latch), minf(next_start, next_part))
		if due > to + 0.000000001:
			break
		now = due
		if due == write_time:
			var event: Dictionary = pending.pop_front()
			if event.kind == "write":
				pages[int(event.page)] = event.image
			else:
				selected_page = int(event.page)
		elif due == next_latch:
			latched_page = selected_page
			next_latch += period
		elif due == next_start:
			scan_page = latched_page
			part = 0
			next_part = next_start + part_period
			next_start += period
		else:
			# The page can be rewritten during scanout. Each 50-row chunk reads
			# the image current at its own time, not a frozen whole-frame copy.
			scan.blit_rect(pages[scan_page], Rect2i(0, part * 50, 320, 50), Vector2i(0, part * 50))
			part += 1
			if part == 4:
				completed = scan.duplicate()
				completed_frames += 1
				next_part = INF
			else:
				next_part += part_period
	now = maxf(now, to)

func image() -> Image:
	return completed.duplicate()
