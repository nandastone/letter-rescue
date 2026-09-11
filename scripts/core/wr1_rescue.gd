extends RefCounted
## WR1.EXE 4ce1..4e6c and 5862..594b. All waits count the original IRQ0.
const IRQ_SECONDS: float = 12428.0 / 1193182.0
const Motion = preload("res://scripts/core/wr1_motion.gd")
enum Stage { DESCEND, ASCEND, HOLD, WALK, DONE }
var stage: Stage = Stage.DONE
var elapsed: float = 0.0
var wait_ticks: int = 1
var rescue_x: int
var rescue_y: int
var target_y: int
var destination: Vector2i
var direction: Vector2i
var walk_index: int = -1
var service_clock: RefCounted
var clock_position_ms: float
var clock_irq_cursor: int = 0

func begin(p: RefCounted, spawn: Vector2i, irq_phase: float, clock: RefCounted = null) -> void:
	destination = spawn
	rescue_x = maxi(p.x - 48, 0)
	rescue_y = 8
	target_y = p.y - 72
	elapsed = fposmod(irq_phase, IRQ_SECONDS)
	service_clock = clock
	if clock != null:
		clock_position_ms = clock.now_ms - irq_phase * 1000.0
		clock_irq_cursor = 0
	stage = Stage.DESCEND
	wait_ticks = 1
	if rescue_y >= target_y:
		stage = Stage.ASCEND
		wait_ticks = 8
		p.frame = 0

func advance(seconds: float, p: RefCounted, present: Callable) -> bool:
	if service_clock == null:
		elapsed += seconds
	while stage != Stage.DONE and _wait_ready():
		match stage:
			Stage.DESCEND:
				p.render_step()
				present.call("descend", Vector2i(rescue_x, rescue_y))
				rescue_y += 8
				if rescue_y >= target_y:
					stage = Stage.ASCEND
					wait_ticks = 8
					p.frame = 0
			Stage.ASCEND:
				p.render_step()
				present.call("ascend", Vector2i(rescue_x, rescue_y))
				rescue_y -= 4
				p.y -= 4
				if rescue_y <= 0:
					stage = Stage.HOLD
					wait_ticks = 15
					present.call("hold", Vector2i.ZERO)
			Stage.HOLD:
				direction = Vector2i(-8 if p.x > destination.x else 8, -8 if p.y > destination.y else 8)
				stage = Stage.WALK
				wait_ticks = 4
				if p.x == destination.x:
					stage = Stage.DONE
				else:
					# First walk wait sees the 15 ticks already accumulated.
					_walk(p)
					if p.x == destination.x:
						stage = Stage.DONE
					else:
						_walk(p)
						present.call("walk", Vector2i.ZERO)
			Stage.WALK:
				if p.x == destination.x:
					stage = Stage.DONE
				else:
					_walk(p)
					present.call("walk", Vector2i.ZERO)
	return stage == Stage.DONE

func _wait_ready() -> bool:
	if service_clock == null:
		if elapsed + 0.000000001 < wait_ticks * IRQ_SECONDS:
			return false
		elapsed -= wait_ticks * IRQ_SECONDS
		return true
	# The original resets its counter at each wait. Count serviced interrupts,
	# including music delays and coalesced PIT edges, rather than ideal periods.
	var interrupts: Array = service_clock.idle.entries
	while clock_irq_cursor < interrupts.size() and float(interrupts[clock_irq_cursor].return_ms) <= clock_position_ms:
		clock_irq_cursor += 1
	var last: int = clock_irq_cursor + wait_ticks - 1
	if last >= interrupts.size() or float(interrupts[last].return_ms) > service_clock.now_ms:
		return false
	clock_position_ms = float(interrupts[last].return_ms)
	elapsed = (service_clock.now_ms - clock_position_ms) / 1000.0
	return true

func _walk(p: RefCounted) -> void:
	walk_index = (walk_index + 1) % 6
	p.frame = (Motion.LEFT_WALK if direction.x < 0 else Motion.RIGHT_WALK)[walk_index]
	p.x += direction.x
	if p.y != destination.y:
		p.y += direction.y
