extends RefCounted
## DOSBox Pure's WR1 OPL wait, PIT reads and relevant hardware event scheduling.
## Initialized hardware state is independent of all future observed outcomes.

var names: Dictionary
var ids := {}
var ticks := 0
var cycle_left := 0
var cycles := 0
var pending := 0
var extra_polls := 0
var pit: Array
var queue: Array
var vga: Dictionary
var interrupts: Dictionary
var keyboard: Dictionary
var float_bytes := PackedByteArray([0, 0, 0, 0])
var record_video_completions := false
var video_completions: Array[float] = []
var video_handoffs: Array[int] = []

func _f32(value: float) -> float:
	float_bytes.encode_float(0, value)
	return float_bytes.decode_float(0)

func configure(initial: Dictionary, event_names: Dictionary) -> void:
	names = event_names.duplicate()
	ids = {}
	for key in names:
		ids[names[key]] = int(key)
	ticks = int(initial.pic_ticks)
	cycle_left = int(initial.cycle_left)
	cycles = int(initial.cycles_remaining)
	pending = int(initial.get("pending_cycles", 0))
	interrupts = initial.get("pic_interrupts", {}).duplicate(true)
	keyboard = initial.get("keyboard", {}).duplicate(true)
	for key in interrupts:
		interrupts[key] = int(interrupts[key])
	assert(interrupts.is_empty() or (not interrupts.special and not interrupts.auto_eoi), "Unsupported PIC priority mode")
	pit = initial.pit.duplicate(true)
	queue = initial.pic_queue.duplicate(true)
	vga = initial.vga_timing.duplicate(true)
	for p in pit:
		p.delay = _f32(p.delay)
		assert(int(p.mode) == 2 and not p.bcd and not p.new_mode and not p.counterstatus_set, "Unsupported original PIT mode")
	for item in queue:
		item.id = int(item.id)
		item.index = _f32(item.index)
		assert(names.has(str(item.id)), "Unmodeled hardware callback")
	assert(not vga.vblank_skip, "Unmodeled VGA blanking skip")

func _time() -> float:
	return ticks + _f32((27000.0 - cycle_left - cycles) / 27000.0)

func observed_time() -> float:
	return _time() + pending / 27000.0

func snapshot() -> Dictionary:
	var result := {"pit":pit.duplicate(true), "pic_queue":queue.duplicate(true),
		"vga_timing":vga.duplicate(true), "pic_ticks":ticks, "cycle_left":cycle_left,
		"cycles_remaining":cycles, "pending_cycles":pending}
	if not interrupts.is_empty():
		result.pic_interrupts = interrupts.duplicate()
	if not keyboard.is_empty():
		result.keyboard = keyboard.duplicate(true)
	return result

func _schedule_keyboard() -> void:
	keyboard.scheduled = true
	var index := _f32((27000.0 - cycle_left - cycles) / 27000.0)
	_add_event("KEYBOARD_TransferBuffer", 0.3, index)
	var budget := int(_f32(_f32(queue[0].index - index) * 27000.0))
	if budget < cycles:
		cycle_left += cycles
		cycles = 0

func _keyboard_read() -> int:
	assert(not keyboard.is_empty(), "Keyboard IO requires controller state")
	_io_delay(26)
	keyboard.changed = false
	if not keyboard.scheduled and not keyboard.buffer.is_empty():
		_schedule_keyboard()
	return int(keyboard.port60)

func keyboard_key(key: int, scan: int, pressed: bool, extended: bool = false) -> void:
	assert(not keyboard.is_empty(), "Key delivery requires controller state")
	if pressed:
		keyboard.repeat_wait = keyboard.repeat_rate if keyboard.repeat_key == key else keyboard.repeat_pause
		keyboard.repeat_key = key
	elif keyboard.repeat_key == key:
		keyboard.repeat_key = 0
		keyboard.repeat_wait = 0
	var bytes: Array = [0xe0] if extended else []
	bytes.append(scan | (0 if pressed else 128))
	for value in bytes:
		if keyboard.buffer.size() >= 32:
			continue
		keyboard.buffer.append(value)
		if not keyboard.scheduled and not keyboard.changed:
			_schedule_keyboard()

func _activate_irq() -> void:
	interrupts.irq_check = 1
	cycle_left += cycles
	cycles = 0

func _raise_irq(number: int) -> void:
	if interrupts.is_empty():
		return
	var bit := 1 << number
	if not interrupts.irr & bit:
		interrupts.irr |= bit
		if not (interrupts.imr | interrupts.isr) & bit and number < interrupts.active_irq:
			_activate_irq()

func _acknowledge_irq() -> void:
	assert(not interrupts.is_empty(), "IRQ acknowledgement requires initial PIC registers")
	if interrupts.active_irq == 8:
		return
	interrupts.isr &= ~(1 << interrupts.active_irq)
	interrupts.active_irq = 8
	for i in range(8):
		if interrupts.isr & (1 << i):
			interrupts.active_irq = i
			break
	var possible: int = interrupts.irr & ~interrupts.imr & ~interrupts.isr & 255
	if possible:
		if possible & ((1 << interrupts.active_irq) - 1):
			_activate_irq()
		else:
			interrupts.irq_check = 0

func run_driver(timeline: Array) -> Array[int]:
	var count := pending
	var decoded := count
	pending = 0
	var waits: Array[int] = []
	for instruction in timeline:
		var operation: String = instruction[0]
		if operation.begins_with("scas:"):
			# SCAS falls back from dyn-x86 to a one-cycle normal-core run.
			# Each byte costs the dynamic opcode and leaves normal cycles=-2.
			var remaining := int(operation.get_slice(":", 1))
			assert(remaining >= 1, "SCAS work requires a compared byte")
			for _byte in range(remaining):
				if count == 0:
					begin_block()
				end_block(count + 1)
				cycle_left += cycles
				cycles = -2
				count = 0
				decoded = 0
				begin_block()
		elif operation.begins_with("rep:"):
			if count == 0:
				begin_block()
			decoded += 1
			end_block(count + 1)
			count = 0
			var remaining := int(operation.get_slice(":", 1))
			while remaining:
				cycles -= 1
				remaining -= 1
				if cycles <= 0:
					begin_block()
					end_block(1)
					decoded = 1
			# dyn_check_bool_exception_al restores one deferred cycle after
			# dyn_string clears its accounting, even without a memory fault.
			count = 1
			if decoded == 32:
				end_block(count)
				count = 0
				decoded = 0
		elif operation == "opl":
			assert(count == 0, "OPL must follow a completed CALL block")
			waits.append(opl())
			end_block(pending + 1)
			pending = 0
			decoded = 0
		else:
			if count == 0:
				begin_block()
			if operation == "keyboard_read":
				_keyboard_read()
			elif operation == "video_page_callback":
				_io_delay(8 * 19)
			elif operation == "in":
				_io_delay(26)
			elif operation == "out":
				_io_delay(19)
			elif operation == "eoi":
				_io_delay(19)
				_acknowledge_irq()
			count += 1
			decoded += 1
			if operation.begins_with("j") or operation in ["ljmp", "call", "lcall", "ret", "retf", "loop", "int", "iret", "callback", "video_page_callback"] or decoded == 32:
				end_block(count)
				count = 0
				decoded = 0
	pending = count
	# The next-instruction hook is after PIC admits the next block. IRET may
	# have exhausted the millisecond budget and its overshoot is then discarded.
	if count == 0:
		begin_block()
	return waits

func _add_event(kind: String, delay: float, origin: float, value: int = 0) -> void:
	var item := {"id":ids[kind], "index":_f32(_f32(delay) + origin), "value":value}
	# Native insertion puts a new event after existing equal-time events.
	for i in range(queue.size()):
		if queue[i].index > item.index:
			queue.insert(i, item)
			return
	queue.append(item)

func _service(item: Dictionary) -> void:
	var kind: String = names[str(int(item.id))]
	var origin: float = item.index
	match kind:
		"PIT0_Event":
			_raise_irq(0)
			pit[0].start += pit[0].delay
			_add_event(kind, pit[0].delay, origin)
		"VGA_VerticalTimer":
			vga.frame_start = _time()
			_add_event(kind, vga.vtotal, origin)
			_add_event("VGA_DisplayStartLatch", vga.vrstart, origin)
			_add_event("VGA_PanningLatch", vga.vrend, origin)
			_add_event("VGA_VertInterrupt", vga.vdend + 0.005, origin)
			vga.parts_left = 4
			vga.lines_done = 0
			_add_event("VGA_DrawPart", vga.parts, origin, int(vga.parts_lines))
		"VGA_DrawPart":
			vga.lines_done += item.value
			vga.parts_left -= 1
			if vga.parts_left:
				var lines := int(vga.parts_lines if int(vga.parts_left) != 1 else vga.lines_total - vga.lines_done)
				_add_event(kind, vga.parts, origin, lines)
			elif record_video_completions:
				video_completions.append(_time())
				video_handoffs.append(ticks + 1)
		"KEYBOARD_TransferBuffer":
			if not keyboard.is_empty():
				keyboard.scheduled = false
				if keyboard.buffer.is_empty():
					return
				keyboard.port60 = keyboard.buffer.pop_front()
				keyboard.changed = true
			_raise_irq(1)
		"VGA_VertInterrupt", "VGA_DisplayStartLatch", "VGA_PanningLatch":
			pass # These callbacks add no CPU work or follow-up events during the wait.
		_:
			assert(false, "Unknown hardware callback")

func begin_block() -> void:
	if cycles > 0:
		return
	cycle_left += cycles
	cycles = 0
	if cycle_left <= 0:
		# TIMER_AddTick replaces the exhausted budget and discards overshoot.
		ticks += 1
		if not keyboard.is_empty() and keyboard.repeat_wait:
			keyboard.repeat_wait -= 1
			assert(keyboard.repeat_wait, "Keyboard repeat injection requires frontend key state")
		cycle_left = 27000
		for item in queue:
			item.index = _f32(item.index - 1.0)
	var index := 27000 - cycle_left
	while not queue.is_empty() and _f32(queue[0].index * 27000.0) <= index:
		_service(queue.pop_front())
	var budget := cycle_left
	if not queue.is_empty():
		budget = maxi(1, int(_f32(_f32(queue[0].index * 27000.0) - index)))
	cycles = mini(budget, cycle_left)
	cycle_left -= cycles

func end_block(count: int) -> void:
	cycles -= count

func _io_delay(amount: int) -> void:
	cycles -= mini(amount, cycles)

func _read_pit(channel: int) -> int:
	var p: Dictionary = pit[channel]
	if p.go_read_latch:
		p.go_read_latch = false
		var index := fmod(_time() - float(p.start), float(p.delay))
		p.read_latch = int(float(p.count) - (index / float(p.delay)) * float(p.count)) & 65535
	var value := 0
	match int(p.read_state):
		0:
			value = int(p.read_latch) >> 8
			p.read_state = 3
			p.go_read_latch = true
		3:
			value = int(p.read_latch) & 255
			p.read_state = 0
		1, 2:
			value = int(p.read_latch) & 255 if int(p.read_state) == 1 else int(p.read_latch) >> 8
			p.go_read_latch = true
		_:
			assert(false, "Unsupported PIT read state")
	return value

func _read_word() -> int:
	_io_delay(26)
	return _read_pit(0) | (_read_pit(1) << 8)

func _status() -> void:
	_io_delay(26)
	_io_delay(13)

func opl() -> int:
	assert(pending == 0, "Commit the preceding block before another OPL call")
	var start := observed_time()
	extra_polls = 0
	begin_block()
	_io_delay(19)
	_status()
	end_block(9)
	for i in range(99):
		begin_block()
		_status()
		end_block(2)
	for iteration in range(30):
		begin_block()
		if iteration == 0:
			_io_delay(19)
		var previous := _read_word()
		var current := _read_word()
		end_block(9 if iteration == 0 else 5)
		while current == previous:
			extra_polls += 1
			assert(extra_polls <= 1000, "PIT poll failed to progress")
			begin_block()
			current = _read_word()
			end_block(3)
		begin_block()
		end_block(1)
	begin_block()
	pending = 4 # Four POPs precede the native before-RET observation.
	return roundi((observed_time() - start) * 27000.0)
