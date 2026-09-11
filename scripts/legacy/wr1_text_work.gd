extends "res://scripts/legacy/wr1_graphics_work.gd"
## Initialized GX EGA text work. Font initialization and clipping remain boundaries.

func word(data: Array, offset: int) -> int:
	return PackedByteArray(data).decode_u16(offset)

func _put(state: Array, offset: int, value: int) -> void:
	state[offset] = value & 255
	state[offset + 1] = (value >> 8) & 255

func font(initial: Dictionary) -> Dictionary:
	path = []
	var state: Array = initial.graphics_state.duplicate()
	var font_state: Dictionary = initial.text_state.duplicate()
	var transparent := int(initial.args[0]) & 65535
	var font_id := int(initial.args[1]) & 65535
	assert(font_id == 3, "Other original font sizes")
	_span(0x10296, 0x102ae)
	_span(0x102c1, 0x102d0)
	if transparent != 1:
		_span(0x102d2, 0x102d2)
	_span(0x102d5, 0x102e9)
	var fixed: bool = int(initial.device_handle) <= 1
	if not fixed:
		_span(0x102eb, 0x102f0)
		fixed = int(initial.device_handle) == 9
	if fixed:
		_span(0x10323, 0x10329)
		font_state.font_pointer = 0xf000fa6e
	else:
		assert(int(font_state.font_id) == 3 and int(font_state.height) == 8, "Unknown initial BIOS 8x8 font pointer")
		var flags: Dictionary = initial.graphics_flags
		assert(PackedByteArray(flags.video_code).slice(0, 2) == PackedByteArray([0xfe, 0x38]) and int(flags.video_code[4]) == 0xcf, "Unknown font-info BIOS callback")
		_span(0x102f2, 0x102fc)
		var vector := int(flags.video_handler)
		var base := ((vector >> 16) << 4) + (vector & 65535)
		path.append_array([["callback", base], ["iret", base + 4]])
		_span(0x102fe, 0x1030d)
	_span(0x1032f, 0x1033d)
	_put(state, 0x50, font_id)
	_put(state, 0x52, int(transparent == 1))
	font_state.font_id = font_id
	font_state.height = 8
	return {"work":path, "state":state, "font":font_state}

func style(kind: String, initial: Dictionary) -> Dictionary:
	path = []
	var state: Array = initial.graphics_state.duplicate()
	if kind == "text_color":
		_span(0xf6c8, 0xf6ee)
		_put(state, 0x0e, int(initial.args[0]))
	else:
		assert(kind == "text_background", "Unknown text style")
		_span(0xf715, 0xf73b)
		_put(state, 0x0c, int(initial.args[0]))
	return {"work":path, "state":state}

func cursor(initial: Dictionary) -> Dictionary:
	path = []
	var state: Array = initial.graphics_state.duplicate()
	_span(0xdb86, 0xdb9c)
	assert(word(state, 0x3c) != 1, "Transformed text cursor")
	_span(0xdbb4, 0xdbce)
	_put(state, 0x12, int(initial.args[1]))
	_put(state, 0x14, int(initial.args[0]))
	return {"work":path, "state":state}

func _valid_string(data: Array) -> void:
	assert(not data.is_empty() and int(data[-1]) == 0, "Require a complete NUL-terminated string")
	for i in range(data.size() - 1):
		assert(int(data[i]) != 0, "Embedded NUL in text input")

func length(initial: Dictionary) -> Dictionary:
	path = []
	var data: Array = initial.text_bytes
	_valid_string(data)
	_span(0x22460, 0x2246b)
	path.append(["scas:%d" % data.size(), 0x2246e])
	_span(0x22470, 0x22479)
	return {"work":path, "value":data.size() - 1}

func string(initial: Dictionary) -> Dictionary:
	path = []
	var state: Array = initial.graphics_state.duplicate()
	var font: Dictionary = initial.text_state
	var data: Array = initial.text_bytes
	_valid_string(data)
	assert(data.size() <= 128, "String exceeds original scan limit")
	assert(state.size() >= 88, "Text work requires the complete GX state")
	assert(int(font.ready) == 1 and word(state, 0x50) == int(font.font_id), "Text font initialization/change")
	_span(0x103d3, 0x103fe)
	for _byte in data:
		_span(0x10401, 0x10406)
	_span(0x10408, 0x1040e)
	_span(0x10414, 0x1041e)
	_span(0x1042a, 0x10472)
	path.append(["scas:%d" % data.size(), 0x10475])
	_span(0x10477, 0x10481)
	var count := data.size() - 1
	if count == 0:
		_span(0x10483, 0x10483)
	else:
		var x := (word(state, 0x12) + word(state, 0x30)) & 65535
		_span(0x10486, 0x1048a)
		var align := word(state, 0x54)
		if align != 1:
			_span(0x1048c, 0x10496)
			if align == 4:
				_span(0x10498, 0x104a0)
				x = (x - 8 * count) & 65535
			else:
				_span(0x104a2, 0x104a9)
				x = (x - 4 * count) & 65535
		_span(0x104ac, 0x104b0)
		align = word(state, 0x56)
		if align != 1:
			_span(0x104b2, 0x104b9)
			if align == 4:
				_span(0x104bb, 0x104c3)
			else:
				_span(0x104c5, 0x104cc)
		_span(0x104cf, 0x104d8)
		assert(word(state, 0x18) != 1, "Clipped text work")
		_span(0x1052f, 0x10532)
		var mode: int
		if word(state, 0) == 1:
			_span(0x10534, 0x1053a)
			mode = word(state, 2)
		else:
			_span(0x1053c, 0x10546)
			mode = int(initial.fill_state.mode)
			_span(0x10548, 0x1054b)
		assert(mode == 2 and word(initial.fill_state.record, 8) == 0x552, "Non-EGA text driver")
		_span(0x10554, 0x1055f)
		_span(0x10567, 0x10567)
		_span(0x107b2, 0x107bf)
		_span(0x10739, 0x1075c)
		_span(0x107c2, 0x107ee)
		var shifted := x % 8 != 0
		var transparent := word(state, 0x52) == 1
		var height := int(font.height)
		assert(height > 0 and height <= 32, "Unsupported font height")
		for i in range(count):
			_span(0x107f1, 0x10804)
			if not shifted:
				_span(0x10806, 0x10806)
				for _row in range(height):
					_span(0x10808, 0x10812)
					if not transparent:
						_span(0x10814, 0x10817)
					_span(0x1081a, 0x1081e)
				_span(0x10820, 0x10820)
			else:
				for _row in range(height):
					_span(0x10822, 0x10837)
					if not transparent:
						_span(0x10839, 0x1083e)
					_span(0x10841, 0x1084f)
					if not transparent:
						_span(0x10851, 0x10856)
					_span(0x1085a, 0x1085f)
			_span(0x10861, 0x1086d)
			if i < count - 1:
				_span(0x1086f, 0x1086f)
		_span(0x10871, 0x10888)
		_span(0x1056a, 0x10575)
		_put(state, 0x12, (x + 8 * count) & 65535)
	_span(0x10578, 0x10586)
	return {"work":path, "state":state}
