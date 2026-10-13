extends RefCounted
## Independent interpreter for the recovered sixteen-slot SCR format.
signal sound_requested(id: int)
signal callback_requested(slot: int, argument: int)
signal displayed
var store
var archive: String
var id: int
var palette_id: int
var script_data: Dictionary
var origin: Vector2i
var pc: int = 0
var repeat: int = 0
var delay: int = 0
var last: int = 0
var start_tick: int
var done: bool = false
var suppress: bool = false
var slots: Array = []
var display: Array = []
var prepared: Array = []
var frame_updates: int = 0
var sound_due: int = 0

func _init(resources, source: String, script_id: int, palette: int, tick: int = 0) -> void:
	store = resources
	archive = source
	id = script_id
	palette_id = palette
	start_tick = tick
	script_data = store.data.scripts[store.key(archive,id)]
	origin = Vector2i(int(script_data.bounds[1]),int(script_data.bounds[0]))
	for i in 16:
		slots.append(empty_slot())

static func u16(b: Array, at: int = 0) -> int:
	return int(b[at]) | (int(b[at+1]) << 8)

static func s16(b: Array, at: int = 0) -> int:
	var value = u16(b,at)
	return value-65536 if value >= 32768 else value

static func wrap32(value: int) -> int:
	value &= 0xffffffff
	return value-0x100000000 if value >= 0x80000000 else value

static func s32(b: Array, at: int = 0) -> int:
	return wrap32(u16(b,at) | (u16(b,at+2) << 16))

func empty_slot() -> Dictionary:
	return {"shape":0,"first":0,"end":0,"flags":2,"x":-2147483648,"y":-2147483648,"vx":0,"vy":0,"ax":0,"ay":0,"sc":0,"mc":0}

func advance_slots() -> void:
	for s in slots:
		if s.shape == 0:
			continue
		var sc = s.sc
		var mc = s.mc
		s.sc = (sc+1)&255
		s.mc = (mc+1)&255
		if s.first != s.end and sc >= ((s.flags >> 8)&15):
			s.sc = 0
			s.shape += -1 if s.flags&0x1000 else 1
			if s.shape > s.end:
				if s.flags&0x2000:
					s.shape = s.end-1
					s.flags |= 0x1000
				else:
					s.shape = s.first
			elif s.shape < s.first:
				if s.flags&0x2000:
					s.shape = s.first+1
					s.flags &= ~0x1000
				else:
					s.shape = s.end
		if mc >= ((s.flags >> 4)&15):
			s.mc = 0
			s.x = wrap32(s.x+s.vx)
			s.y = wrap32(s.y+s.vy)
			s.vx = wrap32(s.vx+s.ax)
			s.vy = wrap32(s.vy+s.ay)

func step(tick: int) -> bool:
	if done:
		return false
	var now = (tick-start_tick)&0xffffffff
	for budget in 1024:
		assert(pc < script_data.code.size(), "SCR runs past terminator")
		var op = script_data.code[pc]
		var code = int(op[0])
		var b = op[1]
		var slot = code&15
		var s = slots[slot]
		var due = now >= ((last+delay)&0xffffffff)
		if code == 0:
			if due:
				done = true
			return false
		if code == 1:
			if not due:
				return false
			last = now
			frame_updates += 1
			display = prepared if suppress else slots.duplicate(true)
			prepared = []
			displayed.emit()
			suppress = false
			advance_slots()
			if repeat == 0:
				repeat = u16(b)
				delay = u16(b,2)
			repeat = (repeat-1)&65535
			if repeat == 0:
				pc += 1
			return true
		if code == 3:
			if not due:
				return false
			sound_requested.emit(u16(b))
			pc += 1
			return true
		if code == 7:
			prepared = slots.duplicate(true)
			suppress = true
			pc += 1
			return true
		if code >= 0x10 and code <= 0x13:
			callback_requested.emit(code&3,u16(b))
		else:
			match code&0xf0:
				0x90:
					var flags = (s.flags&u16(b))|u16(b,2)
					if flags&0x0f00 != s.flags&0x0f00:
						s.sc = 0
					if flags&0x00f0 != s.flags&0x00f0:
						s.mc = 0
					s.flags = flags
				0xa0:
					s.x = wrap32(s.x+(s16(b)<<16))
					s.y = wrap32(s.y+(s16(b,2)<<16))
				0xb0:
					s.x = s16(b)<<16
					s.y = s16(b,2)<<16
				0xc0:
					if u16(b) == 0:
						slots[slot] = empty_slot()
					else:
						s.shape = u16(b)
						s.first = s.shape
						s.end = u16(b,2)
				0xd0:
					s.vx = s32(b)
					s.vy = s32(b,4)
				0xe0:
					s.ax = s32(b)
					s.ay = s32(b,4)
				_:
					assert(false, "Unsupported SCR opcode %x" % code)
		pc += 1
	assert(false, "SCR instruction budget exceeded")
	return false

func update(tick: int) -> void:
	for calls in 1024:
		if not step(tick):
			return
	assert(false, "SCR fails to yield")

func draw(surface) -> void:
	var palette = store.palette(archive,palette_id)
	var b = script_data.bounds
	var clip = [origin.y,origin.x,origin.y+int(b[2]-b[0]),origin.x+int(b[3]-b[1])]
	for s in display:
		if s.shape:
			surface.draw(store,archive,int(palette.first)+s.shape-1,palette_id,origin.x+(s.x>>16),origin.y+(s.y>>16),s.flags&15,clip)
