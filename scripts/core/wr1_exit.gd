extends RefCounted
## WR1.EXE 3dad..3fa9. Door blits do not run the world renderer.
const IRQ_SECONDS: float = 12428.0 / 1193182.0
var elapsed: float = 0.0
var frame: int = 0
var flash: int = 0
var bonus: bool = false
var finished: bool = false

static func touches(gx: int, gy: int, door: Vector2i) -> bool:
	return gx in [door.x - 1, door.x] and gy == door.y + 5

func begin(irq_phase: float, never_slimed: bool) -> void:
	elapsed = fposmod(irq_phase, IRQ_SECONDS)
	frame = 0
	flash = 0
	bonus = never_slimed
	finished = false

func advance(seconds: float, present: Callable) -> bool:
	elapsed += seconds
	while not finished and elapsed + 0.000000001 >= 12 * IRQ_SECONDS:
		elapsed -= 12 * IRQ_SECONDS
		if frame < 5:
			frame += 1
		else:
			flash += 1
		present.call(frame, bonus, flash)
		finished = frame == 5 and (not bonus or flash == 6)
	return finished
