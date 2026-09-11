extends RefCounted
## Original graphics-library work from live device and call state.
var instructions: Dictionary
var path: Array
var span_cache := {}

func configure() -> void:
	instructions = JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/original/driver_work.json")).graphics_instructions
	span_cache.clear()


func _span(start: int, end: int) -> void:
	# Tile copies repeat these immutable instruction spans thousands of times.
	# Cache their expansion, while live state still selects every branch/call.
	var key := Vector2i(start,end)
	if span_cache.has(key):
		path.append_array(span_cache[key])
		return
	var expanded: Array = []
	while start <= end:
		var instruction: Array = instructions[str(start)]
		expanded.append([instruction[0], start])
		start = int(instruction[1])
	span_cache[key] = expanded
	path.append_array(expanded)

func _active_device(initial: Dictionary) -> void:
	assert(initial.device_handle >= 0 and initial.device_handle <= 40, "Invalid graphics handle")
	_span(0x1934e, 0x19377)

func _resolve_device(initial: Dictionary) -> void:
	var handle := int(initial.device_handle)
	var slot := int(initial.device_slot)
	var record: Array = initial.device_record
	var descriptor: Array = initial.device_descriptor
	assert(handle >= 0 and handle <= 40 and slot >= 0 and slot < 44 and record[0] == handle and record[2] == descriptor[0], "Invalid graphics device lookup")
	_span(0x1913a, 0x1914f)
	_span(0x19159, 0x1915b)
	_span(0x190ef, 0x19104)
	_span(0x1910e, 0x19111)
	for i in range(slot + 1):
		_span(0x19114, 0x19116)
		if i < slot:
			_span(0x19118, 0x1911b)
	_span(0x19125, 0x19137)
	_span(0x1915e, 0x1915e)
	_span(0x19166, 0x1917b)
	_span(0x19185, 0x19197)

func draw_page(initial: Dictionary) -> Dictionary:
	path = []
	var page := int(initial.args[0]) & 65535
	var descriptor := PackedByteArray(initial.device_descriptor)
	assert((page & 255) < descriptor[0x1f], "Invalid graphics page")
	_span(0xf3f5, 0xf404)
	_active_device(initial)
	_span(0xf409, 0xf40b)
	_span(0xf412, 0xf413)
	_resolve_device(initial)
	_span(0xf418, 0xf418)
	_span(0xf421, 0xf42c)
	_span(0xf435, 0xf452)
	var state := PackedByteArray(initial.graphics_state)
	state.encode_u16(8, page)
	state.encode_u16(10, (page * descriptor.decode_u16(0x22)) & 65535)
	return {"work":path, "state":Array(state)}

func _video_mode(initial: Dictionary) -> void:
	var flags: Dictionary = initial.graphics_flags
	var code := PackedByteArray(flags.video_code)
	assert(flags.display_type != 7 and code.slice(0, 2) == PackedByteArray([0xfe, 0x38]) and code[4] == 0xcf, "Unsupported BIOS video-mode handler")
	var vector := int(flags.video_handler)
	var base := ((vector >> 16) << 4) + (vector & 65535)
	_span(0x1919a, 0x191ae)
	_span(0x191c1, 0x191c4)
	path.append_array([["callback", base], ["iret", base + 4]])
	_span(0x191c6, 0x191d7)

func copy_rect(initial: Dictionary) -> Dictionary:
	path = []
	var descriptor := PackedByteArray(initial.device_descriptor)
	var flags: Dictionary = initial.graphics_flags
	assert(flags.copy_ready == 1, "Copy initialization not modeled")
	assert(descriptor[0] == 2 and descriptor[0x17] == 1 and descriptor.decode_u16(0x34) == 0x3c1, "Copy requires observed EGA descriptor")
	var a: Array[int] = []
	for value in initial.args:
		a.append(int(value) & 65535)
	var page := a[0]
	var dy := a[1]
	var dx := a[2]
	var source := a[3]
	var ey := a[4]
	var ex := a[5]
	var sy := a[6]
	var sx := a[7]
	var max_x := descriptor.decode_u16(24) - 1
	var max_y := descriptor.decode_u16(26) - 1
	_span(0x138d8, 0x138ed)
	_span(0x138f3, 0x138f3)
	_active_device(initial)
	_span(0x138f8, 0x138fd)
	_span(0x13905, 0x13906)
	_resolve_device(initial)
	_span(0x1390b, 0x1390b)
	_span(0x13915, 0x1391e)
	if flags.check_mode == 1:
		_span(0x13920, 0x13924)
		if descriptor[0] != 9:
			_span(0x13926, 0x13926)
			_video_mode(initial)
			assert((int(flags.video_mode) & 127) == descriptor[0x16], "Mismatched graphics video mode")
			_span(0x1392b, 0x1392f)
	_span(0x13939, 0x1394a)
	if sx > max_x:
		return _copy_rejected(0x1394c, 0x13951)
	_span(0x13954, 0x13957)
	if ex > max_x:
		_span(0x13959, 0x13959)
		ex = max_x
	_span(0x1395c, 0x1395f)
	if dx > max_x:
		return _copy_rejected(0x13961, 0x13966)
	_span(0x13969, 0x13974)
	var right := ex - sx + dx
	if right > max_x:
		_span(0x13976, 0x13976)
		right = max_x
	ex = right - dx + sx
	var width := ex - sx + 1
	_span(0x13978, 0x1399a)
	_span(0x1399d, 0x139ab)
	if sy > max_y:
		return _copy_rejected(0x139ad, 0x139b2)
	_span(0x139b5, 0x139b8)
	if ey > max_y:
		_span(0x139ba, 0x139ba)
		ey = max_y
	_span(0x139bd, 0x139c0)
	if dy > max_y:
		return _copy_rejected(0x139c2, 0x139c7)
	_span(0x139ca, 0x139d5)
	var bottom := ey - sy + dy
	if bottom > max_y:
		_span(0x139d7, 0x139d7)
		bottom = max_y
	ey = bottom - dy + sy
	var height := ey - sy + 1
	_span(0x139d9, 0x13a08)
	var first := mini(width, 8 - dx % 8)
	var tail := (dx + width) % 8 != 0 and width > first
	var shift := (dx - sx) & 7
	@warning_ignore("integer_division")
	var middle := (width - first) / 8
	var remainder := (width - first) % 8
	_span(0x13a0d, 0x13a3b)
	if width <= 8 - dx % 8:
		_span(0x13a3d, 0x13a45)
		if (dx + width) % 8 != 0: _span(0x13a47, 0x13a4a)
	_span(0x13a4e, 0x13a78)
	if sx % 8 > dx % 8: _span(0x13a7a, 0x13a7a)
	_span(0x13a7d, 0x13a8f)
	if remainder == 0: _span(0x13a91, 0x13a91)
	_span(0x13a95, 0x13a9d)
	if remainder > shift: _span(0x13a9f, 0x13a9f)
	_span(0x13aa2, 0x13ab6)
	if tail: _span(0x13ab8, 0x13ab8)
	_span(0x13ab9, 0x13adc)
	_span(0x13c91, 0x13c97)
	var aligned := sx % 8 == 0
	if aligned:
		_span(0x13c99, 0x13c9f)
		aligned = dx % 8 == 0
	if aligned:
		_span(0x13ca1, 0x13cad)
		aligned = width % 8 == 0
	if not aligned:
		_span(0x13cdf, 0x13ce5)
		var forward := sy > dy
		if forward:
			_span(0x13ce7, 0x13ce7)
		else:
			_span(0x13cea, 0x13ced)
			if sy != dy:
				_span(0x13cef, 0x13cef)
			else:
				_span(0x13cf2, 0x13cf8)
				if sx < dx: _span(0x13cfa, 0x13cfa)
				else:
					_span(0x13cfd, 0x13d00)
					forward = sx > dx
					if forward: _span(0x13d02, 0x13d02)
					else:
						_span(0x13d04, 0x13d04)
						_span(0x13d62, 0x13d78)
						return {"work":path,"args":[page,dy,dx,source,ey,ex,sy,sx]}
		if forward: _copy_forward(height, int(descriptor[0x1e]), middle, shift, sx % 8 > dx % 8, tail, remainder > shift)
		else: _copy_backward(height, int(descriptor[0x1e]), width, ex, right)
		return {"work":path,"args":[page,dy,dx,source,ey,ex,sy,sx],"return_ip":0x13ef6 if forward else 0x1413d}
	_span(0x13caf, 0x13cb5)
	if source == page:
		var separate := false
		for test in [[0x13cb7,0x13cbd,sy > dy], [0x13cbf,0x13cc5,sx > right], [0x13cc7,0x13ccd,ex < dx], [0x13ccf,0x13cd5,sy > bottom], [0x13cd7,0x13cdd,ey < dy]]:
			_span(test[0], test[1])
			if test[2]:
				separate = true
				break
		assert(separate, "Overlapping EGA copy")
	_span(0x13d06, 0x13d17)
	_span(0x163b6, 0x163d8)
	_span(0x13d1b, 0x13d35)
	_span(0x163b6, 0x163d8)
	_span(0x13d39, 0x13d51)
	for row in range(height):
		_span(0x13d52, 0x13d52)
		@warning_ignore("integer_division")
		var count := width / 8
		path.append(["rep:%d" % count, 0x13d55])
		_span(0x13d57, 0x13d5e)
		if row < height - 1:
			_span(0x13d60, 0x13d60)
	_span(0x13d62, 0x13d78)
	return {"work":path, "args":[page, dy, dx, source, ey, ex, sy, sx]}

func _copy_rejected(start: int, end: int) -> Dictionary:
	_span(start, end)
	_span(0x13ae0, 0x13ae9)
	return {"work":path, "rejected":true, "return_ip":0x13aea}

func masked_sprite(initial: Dictionary) -> Array:
	path = []
	var header := PackedByteArray(initial.image_header)
	var descriptor := PackedByteArray(initial.device_descriptor)
	var flags: Dictionary = initial.graphics_flags
	assert(flags.sprite_ready == 1 and descriptor[0] == 2 and descriptor.decode_u16(0x2a) == 0x316, "Sprite initialization or different graphics device")
	assert(header.decode_u16(0) == 0xca00 and header.decode_u16(0x16) == 0 and header.decode_u16(0x1a) != 0, "Sprite requires an image in conventional memory")
	var planes := int(header[0x12])
	assert(planes in [1, 4], "Unsupported EGA plane count")
	var y := int(initial.args[1]) & 65535
	var x := int(initial.args[2]) & 65535
	var width := header.decode_u16(0x2c)
	var height := header.decode_u16(0x2e)
	var count := header.decode_u16(0x30)
	var mask := int(header[0x32])
	var available_x := descriptor.decode_u16(24) - x
	var available_y := descriptor.decode_u16(26) - y
	assert(available_x > 0 and available_y > 0 and width > 0 and height > 0, "Sprite outside drawable rectangle")
	_span(0x164e2, 0x164f6)
	_span(0x164fc, 0x1650f)
	_span(0x18c5a, 0x18c71)
	_span(0x18c8a, 0x18c91)
	_span(0x18c93, 0x18c9a)
	_span(0x18ca4, 0x18ce0)
	_span(0x18ce6, 0x18ce6)
	_span(0x18dbe, 0x18dcb)
	_span(0x16514, 0x16516)
	_span(0x1651e, 0x1651e)
	_active_device(initial)
	_span(0x16523, 0x16525)
	_span(0x1652d, 0x16531)
	_resolve_device(initial)
	_span(0x16536, 0x16536)
	_span(0x16540, 0x16548)
	if flags.check_mode == 1:
		_span(0x1654a, 0x1654e)
		_span(0x16550, 0x16550)
		_video_mode(initial)
		assert((int(flags.video_mode) & 127) == descriptor[0x16], "Mismatched sprite video mode")
		_span(0x16555, 0x16559)
	_span(0x16563, 0x16576)
	_span(0x1657f, 0x16582)
	if available_x < width:
		_span(0x16584, 0x16593)
		@warning_ignore("integer_division")
		var clipped_count := (available_x + 7) / 8
		count = clipped_count
		if available_x % 8:
			_span(0x16595, 0x16595)
		_span(0x16596, 0x165a9)
		mask = (255 << ((8 - available_x % 8) % 8)) & 255
	_span(0x165ac, 0x165b9)
	_span(0x165c2, 0x165c5)
	if available_y < height:
		_span(0x165c7, 0x165c7)
		height = available_y
	_span(0x165ca, 0x165ea)
	_span(0x167f6, 0x16838)
	if planes != 1:
		_span(0x1683a, 0x1684c)
	_span(0x16851, 0x16861)
	_span(0x163b6, 0x163d8)
	_span(0x16865, 0x16883)
	var shift := (8 - x % 8) % 8
	if shift == 0 and mask == 255:
		_masked_aligned(height, planes, count)
	else:
		_masked_shifted(height, planes, count, shift)
	_span(0x1695e, 0x16994)
	return path

func _masked_aligned(height: int, planes: int, count: int) -> void:
	for row in range(height):
		for plane in range(planes):
			_span(0x16885, 0x16886)
			for byte in range(count):
				_span(0x16889, 0x1688e)
			_span(0x16890, 0x16898)
			if planes != 1:
				_span(0x1689a, 0x168a3)
				if plane == planes - 1:
					_span(0x168a5, 0x168a8)
			if plane == planes - 1:
				_span(0x168ab, 0x168b1)
				if row == height - 1:
					_span(0x168b3, 0x168b3)
					break
			_span(0x168b6, 0x168bf)

func _masked_shifted(height: int, planes: int, count: int, shift: int) -> void:
	_span(0x168c1, 0x168cb)
	if count == 1:
		_span(0x168cd, 0x168d1)
	_span(0x168d3, 0x168e0)
	for row in range(height):
		for plane in range(planes):
			_span(0x168e3, 0x168f3)
			if shift:
				_span(0x168fa, 0x16900)
			else:
				_span(0x168f5, 0x168f6)
				if count == 1:
					_span(0x168f8, 0x168f8)
			if shift or count > 1:
				_span(0x16901, 0x1690c)
				for byte in range(maxi(0, count - 2)):
					_span(0x1690e, 0x16917)
			_span(0x16919, 0x16943)
			if plane == planes - 1:
				_span(0x16945, 0x16951)
				if row == height - 1:
					break
			_span(0x16953, 0x1695c)

func display_page(initial: Dictionary) -> Dictionary:
	path = []
	var descriptor := PackedByteArray(initial.device_descriptor)
	var flags: Dictionary = initial.graphics_flags
	var page := int(initial.args[0]) & 65535
	assert(descriptor[0] == 2 and page < mini(8, descriptor[0x1f]), "Unsupported display page/device")
	_span(0x17606, 0x17615)
	_active_device(initial)
	_span(0x1761a, 0x1761c)
	_span(0x17623, 0x17624)
	_resolve_device(initial)
	_span(0x17629, 0x17629)
	_span(0x17632, 0x17641)
	_span(0x1764a, 0x1764e)
	_span(0x17668, 0x17668)
	_video_mode(initial)
	assert((int(flags.video_mode) & 127) == descriptor[0x16], "Mismatched display mode")
	_span(0x1766d, 0x17671)
	_span(0x1767a, 0x17683)
	var vector := int(flags.video_handler)
	var base := ((vector >> 16) << 4) + (vector & 65535)
	path.append_array([["video_page_callback", base], ["iret", base + 4]])
	_span(0x17685, 0x17694)
	var state: Dictionary = initial.display_state.duplicate(true)
	state.game_page = page
	state.bios_page = page
	state.bios_start = (page * int(state.page_size)) & 65535
	return {"work":path, "state":state}

func fill_style(initial: Dictionary) -> Dictionary:
	path = []
	var transparent := int(initial.args[0]) & 65535
	var color := int(initial.args[1]) & 65535
	var pattern := int(initial.args[2]) & 65535
	assert(pattern >= 0 and pattern <= 11, "Invalid fill pattern")
	_span(0xf508, 0xf539)
	if transparent != 1:
		_span(0xf53b, 0xf53b)
	_span(0xf53e, 0xf546)
	_span(0xf54d, 0xf556)
	var state := PackedByteArray(initial.graphics_state)
	state.encode_u16(0x22, pattern)
	state.encode_u16(0x24, color)
	state.encode_u16(0x26, int(transparent == 1))
	return {"work":path, "state":Array(state)}

func _signed_word(value: int) -> int:
	return ((value + 32768) & 65535) - 32768

func fill_raw(initial: Dictionary) -> Dictionary:
	path = []
	var state := PackedByteArray(initial.graphics_state)
	var fill: Dictionary = initial.fill_state
	assert(fill.ready == 1 and state.decode_u16(0x3c) == 0 and state.decode_u16(0x18) != 1, "Unsupported fill initialization, transform or clipping")
	assert(PackedByteArray(fill.record).decode_u16(12) == 0x4ca, "Non-EGA fill dispatch")
	var ey := _signed_word(initial.args[0])
	var ex := _signed_word(initial.args[1])
	var sy := _signed_word(initial.args[2])
	var sx := _signed_word(initial.args[3])
	_span(0xce38, 0xce4c)
	_span(0xce52, 0xce59)
	_span(0xce87, 0xce8f)
	if state.decode_u16(0x30) or state.decode_u16(0x32):
		_span(0xce91, 0xce9d)
		sx = _signed_word(sx + state.decode_u16(0x30))
		ex = _signed_word(ex + state.decode_u16(0x30))
		sy = _signed_word(sy + state.decode_u16(0x32))
		ey = _signed_word(ey + state.decode_u16(0x32))
	_span(0xcea0, 0xcea4)
	_span(0xcecc, 0xced8)
	if ey < sy:
		_span(0xceda, 0xcee2)
		var temp := sy
		sy = ey
		ey = temp
	_span(0xcee5, 0xceec)
	if state.decode_u16(0) == 1:
		_span(0xceee, 0xcef4)
	else:
		assert(fill.mode >= 0 and fill.mode <= 16, "Invalid fill mode")
		_span(0xcef6, 0xcf05)
	_span(0xcf0e, 0xcf1b)
	_span(0xd2fa, 0xd312)
	if ex < sx:
		_span(0xd314, 0xd31c)
		var temp := sx
		sx = ex
		ex = temp
	assert(mini(sx, sy) >= 0 and ex < 320 and ey < 200, "Fill outside EGA screen")
	_span(0xd31f, 0xd326)
	_span(0xd2d1, 0xd2f9)
	_span(0xd329, 0xd359)
	var count := ex / 8 - sx / 8
	for row in range(ey - sy + 1):
		_span(0xd35b, 0xd35f)
		var repeats := count
		if sx % 8:
			_span(0xd361, 0xd363)
			if count == 0:
				_span(0xd365, 0xd367)
			else:
				_span(0xd369, 0xd36d)
				repeats -= 1
		if sx % 8 == 0 or count != 0:
			_span(0xd36e, 0xd370)
			path.append(["rep:%d" % repeats, 0xd371])
		_span(0xd373, 0xd37c)
		if row < ey - sy:
			_span(0xd37e, 0xd383)
	_span(0xd385, 0xd39f)
	return {"work":path, "args":[ey, ex, sy, sx]}

func fill_rect(initial: Dictionary) -> Dictionary:
	path = []
	var state := PackedByteArray(initial.graphics_state)
	var mode := _signed_word(initial.args[0])
	var ey := _signed_word(initial.args[1])
	var ex := _signed_word(initial.args[2])
	var sy := _signed_word(initial.args[3])
	var sx := _signed_word(initial.args[4])
	assert(mode == 2 and state.decode_u16(0x3c) == 0 and state.decode_u16(0x22) == 0 and state.decode_u16(0x16) == 0, "Unsupported outlined, transformed, patterned or non-copy fill")
	_span(0xf174, 0xf18a)
	_span(0xf1b8, 0xf1be)
	if ey < sy:
		_span(0xf1c0, 0xf1c3)
		var temp := sy
		sy = ey
		ey = temp
	_span(0xf1c6, 0xf1cc)
	if ex < sx:
		_span(0xf1ce, 0xf1d1)
		var temp := sx
		sx = ex
		ex = temp
	_span(0xf1d4, 0xf1e5)
	_span(0xf2af, 0xf2d3)
	var opening := path
	var child := initial.duplicate(true)
	child.args = [ey, ex, sy, sx]
	var child_state := state.duplicate()
	child_state.encode_u16(0xe, state.decode_u16(0x24))
	child.graphics_state = Array(child_state)
	var body: Dictionary = fill_raw(child)
	path = opening + body.work
	_span(0xd3a0, 0xd3a0)
	_span(0xf2d8, 0xf2de)
	_span(0xf3b1, 0xf3cd)
	state.encode_u16(0x10, 1)
	return {"work":path, "state":Array(state), "args":[mode, ey, ex, sy, sx]}

func _copy_forward(height: int, planes: int, middle: int, shift: int, extra_first: bool, tail: bool, extra_last: bool) -> void:
	_span(0x13d7c, 0x13dba)
	if planes != 1: _span(0x13dbc, 0x13dcd)
	_span(0x13dce, 0x13de0)
	_span(0x163b6, 0x163d8)
	_span(0x13de4, 0x13e01)
	_span(0x163b6, 0x163d8)
	_span(0x13e05, 0x13e0a)
	for row_plane in range(height * planes):
		_span(0x13e0b, 0x13e1b)
		if extra_first: _span(0x13e1d, 0x13e1e)
		_span(0x13e20, 0x13e31)
		if middle > 0:
			_span(0x13e33, 0x13e3d)
			if shift != 0:
				for byte in range(middle): _span(0x13e41, 0x13e4a)
				_span(0x13e4c, 0x13e4c)
			else:
				_span(0x13e3f, 0x13e3f)
				_span(0x13e4e, 0x13e50)
				path.append(["rep:%d" % (middle >> 1), 0x13e52])
				_span(0x13e54, 0x13e54)
				path.append(["rep:%d" % (middle & 1), 0x13e56])
		_span(0x13e58, 0x13e5d)
		if tail:
			_span(0x13e5f, 0x13e69)
			if extra_last: _span(0x13e6b, 0x13e6b)
			_span(0x13e6c, 0x13e76)
		_span(0x13e77, 0x13e7a)
		if row_plane == height * planes - 1: break
		_span(0x13e7c, 0x13e85)
		if planes != 1:
			_span(0x13e87, 0x13e8e)
			if row_plane % planes == planes - 1: _span(0x13e90, 0x13e92)
			_span(0x13e95, 0x13e9f)
		_span(0x13ea0, 0x13ea9)
		if planes != 1:
			_span(0x13eab, 0x13eb2)
			if row_plane % planes == planes - 1: _span(0x13eb4, 0x13eb6)
			_span(0x13eb9, 0x13ec3)
		_span(0x13ec4, 0x13ec4)
	_span(0x13ec7, 0x13ef5)

func _copy_backward(height: int, planes: int, width: int, ex: int, right: int) -> void:
	_span(0x13ef9, 0x13f37)
	if planes != 1: _span(0x13f39, 0x13f4a)
	var first := mini(width, (right & 7) + 1)
	var tail := (right + 1 - width) % 8 != 0 and width > first
	var shift := (ex - right) & 7
	@warning_ignore("integer_division")
	var middle := (width - first) / 8
	var remainder := (width - first) % 8
	_span(0x13f4b, 0x13f75)
	if width <= (right & 7) + 1:
		_span(0x13f77, 0x13f7f)
		_span(0x13f81, 0x13f84)
	_span(0x13f88, 0x13fab)
	if (ex & 7) < (right & 7): _span(0x13fad, 0x13fad)
	_span(0x13fb0, 0x13fc2)
	if remainder == 0: _span(0x13fc4, 0x13fc4)
	_span(0x13fc8, 0x13fd0)
	if remainder > shift: _span(0x13fd2, 0x13fd2)
	_span(0x13fd5, 0x13fe9)
	if tail: _span(0x13feb, 0x13feb)
	_span(0x13fec, 0x14021)
	_span(0x163b6, 0x163d8)
	_span(0x14025, 0x14042)
	_span(0x163b6, 0x163d8)
	_span(0x14046, 0x1404b)
	for row_plane in range(height * planes):
		_span(0x1404c, 0x1405e)
		if (ex & 7) < (right & 7): _span(0x14060, 0x14062)
		_span(0x14063, 0x14076)
		if middle > 0:
			_span(0x14078, 0x14082)
			if shift != 0:
				for byte in range(middle): _span(0x14086, 0x14094)
				_span(0x14096, 0x14096)
			else:
				_span(0x14084, 0x14084)
				_span(0x14098, 0x14098)
				path.append(["rep:%d" % middle, 0x1409a])
		_span(0x1409c, 0x140a1)
		if tail:
			_span(0x140a3, 0x140ad)
			if remainder > shift: _span(0x140af, 0x140b1)
			_span(0x140b2, 0x140bc)
		_span(0x140bd, 0x140c0)
		if row_plane == height * planes - 1: break
		_span(0x140c2, 0x140cb)
		if planes != 1:
			_span(0x140cd, 0x140d4)
			if row_plane % planes == planes - 1: _span(0x140d6, 0x140d8)
			_span(0x140db, 0x140e5)
		_span(0x140e6, 0x140ef)
		if planes != 1:
			_span(0x140f1, 0x140f8)
			if row_plane % planes == planes - 1: _span(0x140fa, 0x140fc)
			_span(0x140ff, 0x14109)
		_span(0x1410a, 0x1410a)
	_span(0x1410d, 0x1413c)
