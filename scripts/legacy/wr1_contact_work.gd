extends "res://scripts/legacy/wr1_graphics_work.gd"
## Initial nearby attributes and words choose contact work and graphics calls.
## Matching outcomes and pickup subroutines remain explicit boundaries.
var graphics = preload("res://scripts/legacy/wr1_graphics_work.gd").new()
var text = preload("res://scripts/legacy/wr1_text_work.gd").new()
var device: Dictionary
var state: Dictionary
var attributes: Array
var calls: Array

func configure() -> void:
	super.configure()
	graphics.configure()
	text.configure()

func _signed(value: int) -> int:
	return ((value + 32768) & 65535) - 32768

func child(kind: String, args: Array, text_bytes: Array = []) -> void:
	var initial := device.duplicate(true)
	initial.args = args
	if not text_bytes.is_empty():
		initial.text_bytes = text_bytes
	var start := path.size()
	var result: Dictionary
	var ret: int
	if kind in ["text_color", "text_background"]:
		result = text.style(kind, initial)
		ret = 0xf6ef if kind == "text_color" else 0xf73c
	elif kind == "text_cursor":
		result = text.cursor(initial)
		ret = 0xdbcf
	elif kind == "text_string":
		result = text.string(initial)
		ret = 0x10587
	elif kind == "string_length":
		result = text.length(initial)
		result.state = initial.graphics_state
		ret = 0x2247a
	elif kind == "draw_page":
		result = graphics.draw_page(initial)
		ret = 0xf453
	else:
		assert(kind == "fill_style", "Unknown contact child")
		result = graphics.fill_style(initial)
		ret = 0xf557
	path.append_array(result.work)
	device.graphics_state = result.state
	calls.append({"kind":kind, "args":args, "start":start, "return":path.size()})
	_span(ret, ret)

func body(initial: Dictionary, initial_attributes: Array, initial_graphics: Dictionary) -> Dictionary:
	path = []
	calls = []
	state = initial.duplicate(true)
	# JSON fixture scalars are floats; original scalar state is integer-valued.
	for key in state:
		if state[key] is float:
			state[key] = int(state[key])
	attributes = initial_attributes.duplicate(true)
	device = initial_graphics.duplicate(true)
	_span(0xc1aa, 0xc1bc)
	child("fill_style", [0, 3, 0])
	_span(0xc1c1, 0xc1c6)
	var active: bool = state.active_word == 1
	if not active:
		_span(0xc1c8, 0xc1c8)
	scan(active)
	_span(0xc6f3, 0xc6f7)
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "attributes":attributes, "calls":calls}

func scan(active: bool) -> void:
	var s := state
	_span(0xc1cb if active else 0xc57a, 0xc1d1 if active else 0xc580)
	var row := maxi(_signed(s.gy - 5), 0)
	if row > 0:
		_span(0xc1d3 if active else 0xc582, 0xc1da if active else 0xc589)
	else:
		_span(0xc1dc if active else 0xc58b, 0xc1dc if active else 0xc58b)
	_span(0xc1de if active else 0xc58d, 0xc1de if active else 0xc58d)
	while true:
		_span(0xc563 if active else 0xc6e2, 0xc567 if active else 0xc6e6)
		if row > s.gy:
			if active:
				_span(0xc569, 0xc569)
			return
		_span(0xc56c if active else 0xc6e8, 0xc572 if active else 0xc6ee)
		if row >= _signed(s.map_height - 1):
			if active:
				_span(0xc577, 0xc577)
			return
		_span(0xc574 if active else 0xc6f0, 0xc574 if active else 0xc6f0)
		_span(0xc1e1 if active else 0xc590, 0xc1e5 if active else 0xc594)
		var col := maxi(_signed(s.gx - 1), 0)
		if col > 0:
			_span(0xc1e7 if active else 0xc596, 0xc1ec if active else 0xc59b)
		else:
			_span(0xc1ee if active else 0xc59d, 0xc1ee if active else 0xc59d)
		_span(0xc1f0 if active else 0xc59f, 0xc1f0 if active else 0xc59f)
		while true:
			_span(0xc54d if active else 0xc6cc, 0xc555 if active else 0xc6d4)
			if col >= _signed(s.gx + 4):
				break
			_span(0xc557 if active else 0xc6d6, 0xc55d if active else 0xc6dc)
			if col >= _signed(s.map_width - 1):
				break
			_span(0xc55f if active else 0xc6de, 0xc55f if active else 0xc6de)
			_span(0xc1f3 if active else 0xc5a2, 0xc201 if active else 0xc5b0)
			assert(col >= 0 and col < attributes.size() and row >= 0 and row < attributes[col].size(), "Contact read outside initial attribute map")
			var value := int(attributes[col][row])
			if value < (14 if active else 7):
				if active:
					_span(0xc206, 0xc20a)
					if col == s.source_x:
						_span(0xc20c, 0xc210)
						if row == s.source_y:
							_span(0xc212, 0xc212)
							return
					assert(false, "Matching result graphics/score/RNG work")
				_span(0xc5b5, 0xc5ba)
				if col == s.last_x:
					_span(0xc5bc, 0xc5c1)
					if row == s.last_y:
						_span(0xc5c3, 0xc5c3)
						return
				reveal(col, row, value)
				return
			_span(0xc203 if active else 0xc5b2, 0xc203 if active else 0xc5b2)
			_span(0xc52c if active else 0xc6ab, 0xc530 if active else 0xc6af)
			if col >= s.gx:
				_span(0xc532 if active else 0xc6b1, 0xc540 if active else 0xc6bf)
				assert(value <= 0x7a, "Pickup graphics/score work")
			_span(0xc54c if active else 0xc6cb, 0xc54c if active else 0xc6cb)
			col = _signed(col + 1)
		_span(0xc562 if active else 0xc6e1, 0xc562 if active else 0xc6e1)
		row = _signed(row + 1)

func reveal(col: int, row: int, value: int) -> void:
	var s := state
	_span(0xc5c6, 0xc629)
	assert(s.word_offset >= 0 and s.word_offset < 7, "Invalid word rotation")
	var index: int = (value + s.word_offset) % 7
	s.merge({"active_word":1, "active_index":index, "source_x":col, "source_y":row, "last_x":col, "last_y":row}, true)
	attributes[col][row] = value + 7
	if s.sound_mode:
		_span(0xc62b, 0xc635)
		s.merge({"speaker_segment":s.data_segment, "speaker_offset":0x4ba, "speaker_index":0}, true)
	_span(0xc63b, 0xc63f)
	child("text_background", [12])
	_span(0xc644, 0xc648)
	child("text_color", [3])
	_span(0xc64d, 0xc651)
	child("text_background", [15])
	_span(0xc656, 0xc65a)
	child("text_color", [3])
	_span(0xc65f, 0xc663)
	child("draw_page", [5])
	var data: Array = Array(String(s.words[index]).to_ascii_buffer())
	data.append(0)
	var args := [_signed(0x9970 + 8 * index), s.data_segment]
	_span(0xc668, 0xc677)
	child("string_length", args, data)
	_span(0xc67c, 0xc690)
	child("text_cursor", [5, 59 + 4 * (8 - (data.size() - 1))])
	_span(0xc695, 0xc6a4)
	child("text_string", args, data)
	_span(0xc6a9, 0xc6a9)
