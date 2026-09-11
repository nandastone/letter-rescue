extends "res://scripts/wr1_graphics_work.gd"
## Original renderer opening, generated from current state without trace timings.
var graphics = preload("res://scripts/wr1_graphics_work.gd").new()
var text = preload("res://scripts/wr1_text_work.gd").new()
var device: Dictionary
var calls: Array

func configure() -> void:
	super.configure()
	graphics.configure()
	text.configure()

func _signed(value: int) -> int:
	return ((value + 32768) & 65535) - 32768

func _child(kind: String, args: Array) -> void:
	device.args = args
	var start := path.size()
	var result: Dictionary
	var ret: int
	if kind == "copy_rect":
		result = graphics.copy_rect(device)
		ret = result.get("return_ip", 0x13d79)
	elif kind == "masked_sprite":
		result = {"work":graphics.masked_sprite(device)}
		ret = 0x16995
	elif kind == "draw_page":
		result = graphics.draw_page(device)
		device.graphics_state = result.state
		ret = 0xf453
	elif kind == "text_font":
		result = text.font(device)
		device.graphics_state = result.state
		device.text_state = result.font
		ret = 0x1033e
	elif kind == "text_background":
		result = text.style(kind, device)
		device.graphics_state = result.state
		ret = 0xf73c
	elif kind == "text_cursor":
		result = text.cursor(device)
		device.graphics_state = result.state
		ret = 0xdbcf
	elif kind == "text_string":
		result = text.string(device)
		device.graphics_state = result.state
		ret = 0x10587
	else:
		result = graphics.call(kind, device)
		device.graphics_state = result.state
		ret = 0xf557 if kind == "fill_style" else 0xf3ce
	path.append_array(result.work)
	calls.append({"kind":kind, "args":args, "start":start, "return":path.size()})
	_span(ret, ret)

func _reward_text(caption: Dictionary, x: int, y: int) -> void:
	_span(0xa333, 0xa33c)
	_child("text_cursor", [_signed(y), _signed(x)])
	_span(0xa341, 0xa347)
	device.text_bytes = caption.bytes
	var pointer := int(caption.pointer)
	_child("text_string", [_signed(pointer & 65535), pointer >> 16])
	_span(0xa34c, 0xa34d)

func prefix(initial: Dictionary, initial_graphics: Dictionary) -> Dictionary:
	path = []
	var state := initial.duplicate(true)
	device = initial_graphics.duplicate(true)
	calls = []
	_span(0xab25, 0xab32)
	if state.animation_enabled == 0:
		_span(0xab34, 0xab34)
	else:
		_span(0xab37, 0xab39)
		for i in range(8):
			_span(0xac1f, 0xac22)
			if i == 7:
				break
			_span(0xac24, 0xac24)
			_span(0xab3c, 0xab4b)
			state.counters[i] = (int(state.counters[i]) + 1) & 65535
			if _signed(state.counters[i]) <= 7:
				_span(0xab4d, 0xab4d)
			else:
				_span(0xab50, 0xab7a)
				state.counters[i] = 0
				var phase := _signed(int(state.phases[i]) + 1) % 2
				state.phases[i] = phase & 65535
				var slot := _signed(state.word_slots[i])
				if slot >= 7:
					_span(0xab7c, 0xab7c)
				else:
					assert(slot >= 0 and slot < 7 and phase in [0, 1], "Invalid animated picture state")
					_span(0xab7f, 0xac19)
					var rect: Array = state.source_rects[phase][i]
					_child("copy_rect", [5, 5, slot * 23 + 144, 4, rect[3], rect[2], rect[1], rect[0]])
			_span(0xac1e, 0xac1e)
	_span(0xac27, 0xac36)
	var dx := 0
	var dy := 0
	var left := false
	if _signed(state.camera_x) > 0:
		_span(0xac38, 0xac3e)
		left = _signed(state.player_x) < 144
	if left:
		_span(0xac40, 0xac4e)
		state.camera_x = (int(state.camera_x) - 1) & 65535
		state.player_x = (int(state.player_x) + 8) & 65535
		dx = 8
	else:
		_span(0xac50, 0xac5a)
		if _signed(int(state.attr_width) - 36) > _signed(state.camera_x):
			_span(0xac5c, 0xac62)
			if _signed(state.player_x) > 144:
				_span(0xac64, 0xac6d)
				state.camera_x = (int(state.camera_x) + 1) & 65535
				state.player_x = (int(state.player_x) - 8) & 65535
				dx = -8
	_span(0xac72, 0xac77)
	var up := false
	if _signed(state.camera_y) > 0:
		_span(0xac79, 0xac7e)
		up = _signed(state.player_y) < 108
	if up:
		_span(0xac80, 0xac8e)
		state.camera_y = (int(state.camera_y) - 1) & 65535
		state.player_y = (int(state.player_y) + 8) & 65535
		dy = 8
	else:
		_span(0xac90, 0xac9a)
		if _signed(int(state.attr_height) - 19) > _signed(state.camera_y):
			_span(0xac9c, 0xaca2)
			if _signed(state.player_y) > 132:
				_span(0xaca4, 0xacad)
				state.camera_y = (int(state.camera_y) + 1) & 65535
				state.player_y = (int(state.player_y) - 8) & 65535
				dy = -8
	_span(0xacb2, 0xacc0)
	assert(int(state.render_page) in [0, 1], "Invalid render page")
	var page := (int(state.render_page) + 1) % 2
	_child("draw_page", [page])
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":{"dx":dx, "dy":dy, "page":page}}

func _background_tile(background_state: Dictionary, x: int, y: int, dest_x: int, dest_y: int, page: int, test_start: int, test_end: int, draw_start: int, draw_end: int) -> void:
	_span(test_start, test_end)
	var source: Array = background_state.source_columns[x][y]
	var sx := int(source[0])
	var sy := int(source[1])
	if _signed(sx) >= 0:
		_span(draw_start, draw_end)
		_child("copy_rect", [page, dest_y, dest_x, 3, sy + 15, sx + 15, sy, sx])

func background(initial: Dictionary, initial_graphics: Dictionary, background_state: Dictionary) -> Dictionary:
	var opening := prefix(initial, initial_graphics)
	var state: Dictionary = opening.state
	var local: Dictionary = opening.locals
	var page := int(local.page)
	var dx := int(local.dx)
	var dy := int(local.dy)
	var cx := int(state.camera_x)
	var cy := int(state.camera_y)
	var x0 := cx / 2
	var y0 := cy / 2
	var x1 := x0 + (cx & 1) + 18
	var y1 := y0 + 10
	var px := 16 - (cx & 1) * 8
	var py := 32 - (cy & 1) * 8
	_span(0xacc5, 0xad39)
	if background_state.full_redraw != 0:
		_span(0xad3e, 0xad54)
		_child("copy_rect", [page,0,0,2,199,319,0,0])
		_span(0xad59, 0xad5f)
		for y in range(y0, y1 + 1):
			_span(0xae00, 0xae06)
			if y == y1:
				break
			_span(0xae08, 0xae08)
			_span(0xad62, 0xad6b)
			for x in range(x0, x1 + 1):
				_span(0xadf1, 0xadf4)
				if x == x1:
					break
				_span(0xadf6, 0xadf6)
				_background_tile(background_state, x, y, px + (x-x0)*16, py + (y-y0)*16,
					page, 0xad6e, 0xad83, 0xad85, 0xade8)
				_span(0xaded, 0xadf0)
			_span(0xadf9, 0xadfd)
		_span(0xae0b, 0xae0b)
		return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":local}
	_span(0xad3b, 0xad3b)
	_span(0xae0e, 0xae39)
	_child("copy_rect", [page, 32 + dy, 16 + dx, 2, 183, 303, 32, 16])
	_span(0xae3e, 0xae46)
	_child("fill_style", [0, background_state.color, 0])
	_span(0xae4b, 0xae51)
	if dx == -8:
		_span(0xae53, 0xae53)
	else:
		_span(0xae56, 0xae59)
		if dx != 8:
			_span(0xae5b, 0xae5b)
	if dx == 8:
		_span(0xae5e, 0xae72)
		_child("fill_rect", [2, 183, 23, 32, 16])
		_span(0xae77, 0xae7d)
		for y in range(y0, y1 + 1):
			_span(0xaf0b, 0xaf11)
			if y == y1:
				break
			_span(0xaf13, 0xaf13)
			_background_tile(background_state, x0, y, px, py + (y - y0) * 16, page, 0xae80, 0xae96, 0xae98, 0xaeff)
			_span(0xaf04, 0xaf08)
		_span(0xaf16, 0xaf16)
	elif dx == -8:
		_span(0xaf19, 0xaf34)
		_child("fill_rect", [2, 183, 303, 32, 296])
		_span(0xaf39, 0xaf43)
		for y in range(y0, y1 + 1):
			_span(0xafcc, 0xafd2)
			if y == y1:
				break
			_span(0xafd4, 0xafd4)
			_background_tile(background_state, x1 - 1, y, 288 + (cx & 1) * 8, py + (y - y0) * 16, page, 0xaf46, 0xaf5b, 0xaf5d, 0xafc0)
			_span(0xafc5, 0xafc9)
	_span(0xafd7, 0xafe3)
	if dy == -8:
		_span(0xafe5, 0xafe5)
	else:
		_span(0xafe8, 0xafeb)
		if dy != 8:
			_span(0xafed, 0xafed)
	if dy == 8:
		_span(0xaff0, 0xb00d)
		_child("fill_rect", [2, 39, 303, 32, 16])
		_span(0xb012, 0xb018)
		for x in range(x0, x1 + 1):
			_span(0xb0a5, 0xb0ab)
			if x == x1:
				break
			_span(0xb0ad, 0xb0ad)
			_background_tile(background_state, x, y0, px + (x - x0) * 16, py, page, 0xb01b, 0xb031, 0xb033, 0xb09a)
			_span(0xb09f, 0xb0a2)
		_span(0xb0b0, 0xb0b0)
	elif dy == -8:
		_span(0xb0b3, 0xb0d0)
		_child("fill_rect", [2, 183, 303, 176, 16])
		_span(0xb0d5, 0xb0df)
		for x in range(x0, x1 + 1):
			_span(0xb165, 0xb168)
			if x == x1:
				break
			_span(0xb16a, 0xb16a)
			_background_tile(background_state, x, y1 - 1, px + (x - x0) * 16, 168 + (1 ^ (cy & 1)) * 8, page, 0xb0e2, 0xb0f7, 0xb0f9, 0xb15c)
			_span(0xb161, 0xb164)
	_span(0xb16d, 0xb18c)
	_child("copy_rect", [2, 32, 16, page, 183, 303, 32, 16])
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":local}

func tiles(initial: Dictionary, initial_graphics: Dictionary, background_state: Dictionary, initial_tiles: Dictionary) -> Dictionary:
	var prior := background(initial, initial_graphics, background_state)
	var state: Dictionary = prior.state
	var local: Dictionary = prior.locals
	var result := initial_tiles.duplicate(true)
	assert(result.pickups.size() == 7 and result.animated_count == result.animated.size(), "Incomplete live tile state")
	var cx := int(state.camera_x)
	var cy := int(state.camera_y)
	var x0 := cx / 2
	var y0 := cy / 2
	var x1 := x0 + (cx & 1) + 18
	var y1 := y0 + 10
	_span(0xb191, 0xb193)
	for i in range(8):
		_span(0xb21e, 0xb221)
		if i == 7:
			break
		_span(0xb223, 0xb223)
		var x := _signed(result.pickups[i][0])
		var y := _signed(result.pickups[i][1])
		_span(0xb196, 0xb1a1)
		var visible := false
		if x < x0:
			_span(0xb1a3, 0xb1a3)
		else:
			_span(0xb1a6, 0xb1b1)
			if x < x1:
				_span(0xb1b3, 0xb1be)
				if y >= y0:
					_span(0xb1c0, 0xb1cb)
					visible = y < y1
		if visible:
			_span(0xb1cd, 0xb218)
			_child("copy_rect", [local.page, y * 16 + 32 - cy * 8, x * 16 + 16 - cx * 8, 2, 15, i * 16 + 15, 0, i * 16])
		_span(0xb21d, 0xb21d)
	_span(0xb226, 0xb230)
	result.phase = (int(result.phase) + 1) & 65535
	if _signed(result.phase) > 3:
		_span(0xb232, 0xb232)
		result.phase = 0
	_span(0xb238, 0xb23a)
	for i in range(result.animated.size() + 1):
		_span(0xb35f, 0xb363)
		if i == result.animated.size():
			break
		_span(0xb365, 0xb365)
		var x := _signed(result.animated[i][0])
		var y := _signed(result.animated[i][1])
		var visible := true
		for branch in [[0xb23d, 0xb248, 0xb24a, x >= x0], [0xb24d, 0xb258, 0xb25a, x < x1], [0xb25d, 0xb268, 0xb26a, y >= y0], [0xb26d, 0xb278, 0xb27a, y < y1]]:
			_span(branch[0], branch[1])
			if not branch[3]:
				_span(branch[2], branch[2])
				visible = false
				break
		if visible:
			_span(0xb27d, 0xb359)
			var source: Array = background_state.source_columns[x][y]
			var sx := int(source[0]) + 16 * int(result.phase)
			var sy := int(source[1])
			_child("copy_rect", [local.page, y * 16 + 32 - cy * 8, x * 16 + 16 - cx * 8, 3, sy + 15, sx + 15, sy, sx])
		_span(0xb35e, 0xb35e)
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":local, "tiles":result}

func _draw_door(x: int, y: int, entrance: bool, cx: int, cy: int, page: int, theme: int) -> void:
	var visibility: Array
	var clips: Array
	if entrance:
		visibility = [[0xb4cf, 0xb4d9, 0xb4db, cx - 4 < x], [0xb4de, 0xb4e8, 0xb4ea, cx + 36 > x], [0xb4ed, 0xb4f7, 0xb4f9, cy - 5 < y], [0xb4fc, 0xb506, 0xb508, cy + 19 > y]]
		clips = [[0xb50b, 0xb512, 0xb514, 0xb516, 0xb518, 0xb51b, 0xb51f, 0xb537], [0xb53b, 0xb548, 0xb54a, 0xb54c, 0xb54e, 0xb558, 0xb55b, 0xb564], [0xb567, 0xb56e, 0xb570, 0xb572, 0xb574, 0xb577, 0xb57b, 0xb5ac], [0xb5ad, 0xb5ba, 0xb5bc, 0xb5be, 0xb5c0, 0xb5ca, 0xb5cd, 0xb5f1]]
	else:
		visibility = [[0xb38a, 0xb394, 0xb396, cx - 4 < x], [0xb399, 0xb3a3, 0xb3a5, cx + 36 > x], [0xb3a8, 0xb3b2, 0xb3b4, cy - 5 < y], [0xb3b7, 0xb3c1, 0xb3c3, cy + 19 > y]]
		clips = [[0xb3c6, 0xb3cd, 0xb3cf, 0xb3d1, 0xb3d3, 0xb3d6, 0xb3da, 0xb3f2], [0xb3f6, 0xb403, 0xb405, 0xb407, 0xb409, 0xb413, 0xb416, 0xb41f], [0xb422, 0xb429, 0xb42b, 0xb42d, 0xb42f, 0xb432, 0xb436, 0xb467], [0xb468, 0xb475, 0xb477, 0xb479, 0xb47b, 0xb485, 0xb488, 0xb4ac]]
	for branch in visibility:
		_span(branch[0], branch[1])
		if not branch[3]:
			_span(branch[2], branch[2])
			return
	var edges := [cx - x, cx + 36 - x - 4, cy - y, cy + 19 - y - (5 if entrance else 4)]
	for i in range(clips.size()):
		var block: Array = clips[i]
		_span(block[0], block[1])
		var zero: bool = edges[i] < 0 if i % 2 == 0 else edges[i] > 0
		_span(block[2] if zero else block[4], block[3] if zero else block[5])
		_span(block[6], block[7])
	var left := maxi(0, edges[0]) * 8
	var top := maxi(0, edges[2]) * 8
	var sx := 16 + left
	var sy := theme * 40 + 33 + top
	var ex := 47 + mini(0, edges[1]) * 8
	var ey := theme * 40 + 72 + mini(0, edges[3]) * 8
	_child("copy_rect", [page, 32 + (y - cy) * 8 + top, 16 + (x - cx) * 8 + left, 5, ey, ex, sy, sx])

func doors(initial: Dictionary, initial_graphics: Dictionary, background_state: Dictionary, initial_tiles: Dictionary, initial_doors: Dictionary) -> Dictionary:
	var prior := tiles(initial, initial_graphics, background_state, initial_tiles)
	var state: Dictionary = prior.state
	var local: Dictionary = prior.locals
	var result := initial_doors.duplicate(true)
	var cx := int(state.camera_x)
	var cy := int(state.camera_y)
	_span(0xb368, 0xb387)
	_draw_door(result.exit_x, result.exit_y, false, cx, cy, local.page, result.theme)
	_span(0xb4b1, 0xb4b6)
	if result.entrance_timer == 0:
		_span(0xb4b8, 0xb4b8)
	else:
		_span(0xb4bb, 0xb4c4)
		result.entrance_timer = (int(result.entrance_timer) - 1) & 65535
		var show := true
		if _signed(result.entrance_timer) <= 10:
			_span(0xb4c6, 0xb4ca)
			if local.page == 0:
				_span(0xb4cc, 0xb4cc)
				show = false
		if show:
			_draw_door(result.entrance_x, result.entrance_y, true, cx, cy, local.page, result.theme)
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":local, "tiles":prior.tiles, "doors":result}

func _matching_visible(branches: Array) -> bool:
	for branch in branches:
		_span(branch[0], branch[1])
		if not branch[3]:
			_span(branch[2], branch[2])
			return false
	return true

func _matching_clipped(x: int, y: int, rect: Array, width: int, height: int, blocks: Array, source_page: int, page: int, active: bool) -> void:
	var conditions := [x > 0, x >= 0, 320 - maxi(0, x) - width >= 0, y > 0, y >= 0, 200 - maxi(0, y) - height >= 0]
	for i in range(blocks.size()):
		var block: Array = blocks[i]
		_span(block[0], block[1])
		_span(block[2] if conditions[i] else block[4], block[3] if conditions[i] else block[5])
		_span(block[6], block[7])
	var args := [page, maxi(0, y), maxi(0, x), source_page, int(rect[3]) + mini(0, 200 - maxi(0, y) - height), int(rect[2]) + mini(0, 320 - maxi(0, x) - width), int(rect[1]) - mini(0, y), int(rect[0]) - mini(0, x)]
	_span(0xb886 if active else 0xb9c9, 0xb89d if active else 0xb9de)
	_child("copy_rect", args)

func matching(initial: Dictionary, initial_graphics: Dictionary, background_state: Dictionary, initial_tiles: Dictionary, initial_doors: Dictionary, matching_state: Dictionary) -> Dictionary:
	var prior := doors(initial, initial_graphics, background_state, initial_tiles, initial_doors)
	var state: Dictionary = prior.state
	var page := int(prior.locals.page)
	var offset_x := 16 - 8 * int(state.camera_x)
	var offset_y := 32 - 8 * int(state.camera_y)
	var active: bool = matching_state.active != 0
	assert(matching_state.locations.size() == 7, "Incomplete matching locations")
	var question_blocks := [[0xb94c,0xb94e,0xb950,0xb952,0xb954,0xb954,0xb956,0xb95b], [0xb95e,0xb960,0xb966,0xb966,0xb962,0xb964,0xb968,0xb968], [0xb96a,0xb972,0xb97e,0xb97e,0xb974,0xb97c,0xb980,0xb983], [0xb986,0xb98a,0xb98c,0xb98e,0xb990,0xb990,0xb993,0xb998], [0xb99b,0xb99f,0xb9a5,0xb9a5,0xb9a1,0xb9a3,0xb9a8,0xb9a8], [0xb9ab,0xb9b4,0xb9c1,0xb9c1,0xb9b6,0xb9bf,0xb9c3,0xb9c6]]
	var word_blocks := [[0xb678,0xb67a,0xb67c,0xb67e,0xb680,0xb680,0xb682,0xb692], [0xb695,0xb697,0xb69d,0xb69d,0xb699,0xb69b,0xb69f,0xb69f], [0xb6a1,0xb6b6,0xb6c2,0xb6c2,0xb6b8,0xb6c0,0xb6c4,0xb6c7], [0xb6ca,0xb6ce,0xb6d0,0xb6d2,0xb6d4,0xb6d4,0xb6d7,0xb6e7], [0xb6ea,0xb6ee,0xb6f4,0xb6f4,0xb6f0,0xb6f2,0xb6f7,0xb6f7], [0xb6fa,0xb710,0xb71d,0xb71d,0xb712,0xb71b,0xb71f,0xb725]]
	var picture_blocks := [[0xb781,0xb7a5,0xb7a7,0xb7a9,0xb7ab,0xb7ab,0xb7ad,0xb7b2], [0xb7b5,0xb7b7,0xb7bd,0xb7bd,0xb7b9,0xb7bb,0xb7bf,0xb7bf], [0xb7c1,0xb7eb,0xb7f7,0xb7f7,0xb7ed,0xb7f5,0xb7f9,0xb7fc], [0xb7ff,0xb825,0xb827,0xb829,0xb82b,0xb82b,0xb82e,0xb833], [0xb836,0xb83a,0xb840,0xb840,0xb83c,0xb83e,0xb843,0xb843], [0xb846,0xb871,0xb87e,0xb87e,0xb873,0xb87c,0xb880,0xb883]]
	_span(0xb5f6, 0xb5fb)
	if active:
		_span(0xb600, 0xb602)
	else:
		_span(0xb5fd, 0xb5fd)
		_span(0xb8ae, 0xb8b0)
	for i in range(8):
		_span(0xb8a3 if active else 0xb9e4, 0xb8a6 if active else 0xb9e7)
		if i == 7:
			break
		_span(0xb8a8 if active else 0xb9e9, 0xb8a8 if active else 0xb9e9)
		var location: Array = matching_state.locations[i]
		var wx := _signed(location[0])
		var wy := _signed(location[1])
		var attr := int(location[2])
		var gx := wx / 8
		var gy := wy / 8
		var x := wx + offset_x
		var y := wy + offset_y
		if active:
			_span(0xb605, 0xb62e)
			var is_word := false
			if gx != matching_state.source_x:
				_span(0xb630, 0xb630)
			else:
				_span(0xb633, 0xb63a)
				if gy != matching_state.source_y:
					_span(0xb63c, 0xb63c)
				else:
					is_word = true
			if is_word:
				var shown := _matching_visible([[0xb63f,0xb65b,0xb65d,x > -64], [0xb660,0xb664,0xb666,x < 320], [0xb669,0xb66b,0xb66d,y > 0], [0xb670,0xb673,0xb675,y < 192]])
				if shown:
					_matching_clipped(x, y, matching_state.word_rects[int(matching_state.active_index)], 64, 16, word_blocks, 4, page, active)
			else:
				_span(0xb728, 0xb745)
				var index := (attr + int(matching_state.picture_offset)) % 7
				var shown := _matching_visible([[0xb748,0xb764,0xb766,x > -24], [0xb769,0xb76d,0xb76f,x < 320], [0xb772,0xb774,0xb776,y > 0], [0xb779,0xb77c,0xb77e,y < 192]])
				if shown:
					_matching_clipped(x, y, state.source_rects[int(state.phases[i])][index], 24, 24, picture_blocks, 4, page, active)
		else:
			_span(0xb8b3, 0xb8e3)
			var eligible := attr < 7
			if not eligible:
				_span(0xb8e5, 0xb8e5)
			else:
				_span(0xb8e8, 0xb8fa)
				if gx == matching_state.last_x:
					_span(0xb8fc, 0xb90e)
					if gy == matching_state.last_y:
						_span(0xb910, 0xb910)
						eligible = false
			if eligible:
				var shown := _matching_visible([[0xb913,0xb92f,0xb931,x > -24], [0xb934,0xb938,0xb93a,x < 320], [0xb93d,0xb93f,0xb941,y > 0], [0xb944,0xb947,0xb949,y < 192]])
				if shown:
					_matching_clipped(x, y, [208,40,231,63], 24, 24, question_blocks, 5, page, active)
		_span(0xb8a2 if active else 0xb9e3, 0xb8a2 if active else 0xb9e3)
	if active:
		_span(0xb8ab, 0xb8ab)
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":prior.locals, "tiles":prior.tiles, "doors":prior.doors}

func player(initial: Dictionary, initial_graphics: Dictionary, background_state: Dictionary, initial_tiles: Dictionary, initial_doors: Dictionary, matching_state: Dictionary, player_state: Dictionary) -> Dictionary:
	var prior := matching(initial, initial_graphics, background_state, initial_tiles, initial_doors, matching_state)
	var state: Dictionary = prior.state
	_span(0xb9ec, 0xb9f1)
	if player_state.visible:
		for i in range(player_state.images.size()):
			_span(0xb9f3 if i == 0 else 0xba1c, 0xba17 if i == 0 else 0xba33)
			var source: Dictionary = player_state.images[i]
			var pointer := int(source.pointer)
			device.image_header = source.header
			_child("masked_sprite", [prior.locals.page, int(state.player_y) - 32, state.player_x, i + 1, _signed(pointer & 65535), pointer >> 16])
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":prior.locals, "tiles":prior.tiles, "doors":prior.doors}

func _actor_image(offset: int, x: int, y: int, operation: int, page: int, data_segment: int, images: Dictionary) -> void:
	offset &= 65535
	device.image_header = images[str(offset)]
	_child("masked_sprite", [page, y, x, operation, _signed(offset), data_segment])

func _actor_visible(branches: Array) -> bool:
	for branch in branches:
		_span(branch[0], branch[1])
		if not branch[3]:
			if branch[2] != null:
				_span(branch[2], branch[2])
			return false
	return true

func actors(initial: Dictionary, initial_graphics: Dictionary, background_state: Dictionary, initial_tiles: Dictionary, initial_doors: Dictionary, matching_state: Dictionary, player_state: Dictionary, actor_state: Dictionary, images: Dictionary) -> Dictionary:
	var prior := player(initial, initial_graphics, background_state, initial_tiles, initial_doors, matching_state, player_state)
	var state: Dictionary = prior.state
	var local: Dictionary = prior.locals
	var result := actor_state.duplicate(true)
	assert(result.enemy_count == result.enemies.size() and result.drip_count == result.drips.size(), "Incomplete actor arrays")
	var cx := int(state.camera_x)
	var cy := int(state.camera_y)
	_span(0xba38, 0xba3a)
	for i in range(result.enemies.size() + 1):
		_span(0xbb97, 0xbb9b)
		if i == result.enemies.size():
			break
		_span(0xbb9d, 0xbb9d)
		var enemy: Dictionary = result.enemies[i]
		var x := int(enemy.x)
		var y := int(enemy.y)
		var mode := _signed(enemy.state)
		_span(0xba3d, 0xba46)
		if mode == 24:
			_span(0xba48, 0xba48)
		elif _actor_visible([[0xba4b,0xba5c,0xba5e,x > cx - 2], [0xba61,0xba72,0xba74,x < cx + 35], [0xba77,0xba88,0xba8a,y > cy - 2], [0xba8d,0xba9e,0xbaa0,y <= cy + 19]]):
			_span(0xbaa3, 0xbaf0)
			var frame := int(result.animation_frames[int(enemy.animation_index)])
			var offset := int(enemy.type) * 512 + frame * 128
			var dx := (x - cx) * 8 + 16
			var dy := (y - cy) * 8 + 9
			if mode < 24:
				_span(0xbaf2, 0xbb14)
				_actor_image(0xb98b + offset, dx, dy, 1, local.page, result.data_segment, images)
				_span(0xbb19, 0xbb3b)
				_actor_image(0xaf8c + offset, dx, dy, 2, local.page, result.data_segment, images)
				_span(0xbb40, 0xbb49)
				if mode == -1:
					_span(0xbb4b, 0xbb5a)
					enemy.animation_index = (int(enemy.animation_index) + 1) & 65535
					if _signed(enemy.animation_index) > 11:
						_span(0xbb5c, 0xbb66)
						enemy.animation_index = 0
			else:
				_span(0xbb68, 0xbb6d)
				if state.render_page == 0:
					_span(0xbb6f, 0xbb91)
					_actor_image(0xb98b + offset, dx, dy, 1, local.page, result.data_segment, images)
		_span(0xbb96, 0xbb96)
	_span(0xbba0, 0xbba2)
	for i in range(result.drips.size() + 1):
		_span(0xbc55, 0xbc59)
		if i == result.drips.size():
			break
		_span(0xbc5b, 0xbc5b)
		var drip: Dictionary = result.drips[i]
		var x := int(drip.x)
		var y := int(drip.y)
		if _actor_visible([[0xbba5,0xbbb1,0xbbb3,x > cx], [0xbbb6,0xbbc7,0xbbc9,x < cx + 36], [0xbbcc,0xbbd8,null,y > cy], [0xbbda,0xbbeb,null,y < cy + 19]]):
			_span(0xbbed, 0xbc2e)
			_actor_image(0xa986 + int(drip.frame) * 128, (x - cx) * 8 + 16, (y - cy) * 8 + 32, 1, local.page, result.data_segment, images)
			_span(0xbc33, 0xbc4f)
			_actor_image(0x8513 + int(drip.frame) * 128, (x - cx) * 8 + 16, (y - cy) * 8 + 32, 2, local.page, result.data_segment, images)
		_span(0xbc54, 0xbc54)
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":local, "tiles":prior.tiles, "doors":prior.doors, "actors":result}

func complete(initial: Dictionary, initial_graphics: Dictionary, background_state: Dictionary, initial_tiles: Dictionary, initial_doors: Dictionary, matching_state: Dictionary, player_state: Dictionary, actor_state: Dictionary, images: Dictionary, tail: Dictionary) -> Dictionary:
	var prior := actors(initial, initial_graphics, background_state, initial_tiles, initial_doors, matching_state, player_state, actor_state, images)
	var state: Dictionary = prior.state
	var actor_result: Dictionary = prior.actors
	var result := tail.duplicate(true)
	var cx := int(state.camera_x)
	var cy := int(state.camera_y)
	var page := int(prior.locals.page)
	var data_segment := int(actor_result.data_segment)
	var x0 := cx / 2
	var y0 := cy / 2
	var x1 := x0 + (cx & 1) + 18
	var y1 := y0 + 10
	assert(result.foreground_count == result.foreground.size(), "Incomplete foreground")
	_span(0xbc5e, 0xbc60)
	for i in range(result.foreground.size() + 1):
		_span(0xbd70, 0xbd74)
		if i == result.foreground.size():
			break
		_span(0xbd76, 0xbd76)
		var x := int(result.foreground[i][0])
		var y := int(result.foreground[i][1])
		if _actor_visible([[0xbc63,0xbc6e,0xbc70,x >= x0], [0xbc73,0xbc7e,0xbc80,x < x1], [0xbc83,0xbc8e,0xbc90,y >= y0], [0xbc93,0xbc9e,0xbca0,y < y1]]):
			_span(0xbca3, 0xbd6a)
			var source: Array = background_state.source_columns[x][y]
			var sx := int(source[0])
			var sy := int(source[1])
			_child("copy_rect", [page, y * 16 + 32 - cy * 8, x * 16 + 16 - cx * 8, 3, sy + 15, sx + 15, sy, sx])
		_span(0xbd6f, 0xbd6f)
	_span(0xbd79, 0xbd81)
	result.action_busy = 0
	for i in range(actor_result.enemies.size() + 1):
		_span(0xbf47, 0xbf4b)
		if i == actor_result.enemies.size():
			break
		_span(0xbf4d, 0xbf4d)
		var enemy: Dictionary = actor_result.enemies[i]
		var mode := _signed(enemy.state)
		_span(0xbd84, 0xbd8d)
		if mode < 0:
			_span(0xbd8f, 0xbd8f)
		else:
			_span(0xbd92, 0xbd9b)
			if mode > 24:
				_span(0xbd9d, 0xbd9d)
			else:
				_span(0xbda0, 0xbdd6)
				var x := (int(enemy.x) - cx) * 8 + 16
				var y := (int(enemy.y) - cy) * 8 - 55
				var corpse := mode == 24
				if corpse:
					_span(0xbdd8, 0xbdd8)
				else:
					_span(0xbddb, 0xbde0)
					if result.death:
						_span(0xbde2, 0xbde2)
						corpse = true
				if corpse:
					_span(0xbf13, 0xbf2c)
					_actor_image(0xa206, x, y + 64, 1, page, data_segment, images)
					_span(0xbf31, 0xbf41)
					_actor_image(0x8a13, x, y + 64, 2, page, data_segment, images)
				else:
					_span(0xbde5, 0xbdfe)
					result.action_busy = 1
					var frame := int(result.rescue_frames[mode])
					if frame >= 0 and _actor_visible([[0xbe00,0xbe03,null,frame < 24], [0xbe05,0xbe07,null,x >= 0], [0xbe09,0xbe0d,null,x < 288], [0xbe0f,0xbe13,null,y >= 0], [0xbe15,0xbe19,null,y < 104]]):
						_span(0xbe1b, 0xbe2f)
						_actor_image(0x9e86 + 128 * frame, x, y, 1, page, data_segment, images)
						_span(0xbe34, 0xbe4b)
						_actor_image(0x8693 + 128 * frame, x, y, 2, page, data_segment, images)
					_span(0xbe50, 0xbe5f)
					enemy.state = mode + 1
					assert(mode + 1 != 24, "Rescue score update and text work are not yet modeled")
					_span(0xbe61, 0xbe61)
		_span(0xbf46, 0xbf46)
	_span(0xbf50, 0xbf55)
	if result.miss_timer:
		_span(0xbf57, 0xbf7f)
		result.miss_timer = (int(result.miss_timer) - 1) & 65535
		var x := (int(result.miss_x) - cx) * 8 + 16
		var y := (int(result.miss_y) - cy - 8) * 8 + 33
		if _actor_visible([[0xbf82,0xbf84,null,x >= 0], [0xbf86,0xbf8a,null,x < 288], [0xbf8c,0xbf8e,null,y >= 0], [0xbf90,0xbf93,null,y < 104]]):
			_span(0xbf95, 0xbfa5)
			_actor_image(0xa286, x, y, 1, page, data_segment, images)
			_span(0xbfaa, 0xbfba)
			_actor_image(0x8a93, x, y, 2, page, data_segment, images)
	_span(0xbfbf, 0xbfc4)
	if result.reward_timer == 0:
		_span(0xbfc6, 0xbfc6)
	elif _actor_visible([[0xbfc9,0xbfd0,null,result.reward_x >= cx], [0xbfd2,0xbfdc,null,cx + 36 >= result.reward_x], [0xbfde,0xbfe5,null,result.reward_y >= cy], [0xbfe7,0xbff1,null,cy + 19 >= result.reward_y]]):
		_span(0xbffc, 0xc004)
		_child("text_font", [1, 3])
		_span(0xc009, 0xc010)
		_child("text_background", [page + 13])
		_span(0xc015, 0xc018)
		_child("draw_page", [page])
		_span(0xc01d, 0xc04b)
		var rx := int(result.reward_x)
		var ry := int(result.reward_y)
		_reward_text(result.reward_text, (rx - cx) * 8 + 16, (ry - cy) * 8 + int(result.reward_timer) + 32)
		_span(0xc050, 0xc058)
		if result.reward_bonus == 3:
			_span(0xc05a, 0xc064)
			if _signed(rx - 3) >= cx:
				_span(0xc066, 0xc075)
				if _signed(rx + 3) <= _signed(cx + 36):
					_span(0xc077, 0xc0a2)
					_reward_text(result.perfect_text, (rx - cx) * 8 - 4, (ry - cy) * 8 + int(result.reward_timer) + 24)
					_span(0xc0a7, 0xc0a7)
		_span(0xc0aa, 0xc0af)
		if result.reward_bonus == 1:
			_span(0xc0b1, 0xc0bb)
			if _signed(rx - 3) >= cx:
				_span(0xc0bd, 0xc0cc)
				if _signed(rx + 3) <= _signed(cx + 36):
					_span(0xc0ce, 0xc0f9)
					_reward_text(result.bonus_text, (rx - cx) * 8 - 4, (ry - cy) * 8 + int(result.reward_timer) + 24)
					_span(0xc0fe, 0xc0fe)
		_span(0xc101, 0xc10c)
		result.reward_timer = (int(result.reward_timer) - 1) & 65535
		_child("text_font", [0, 3])
	else:
		_span(0xbff3, 0xbff9)
		result.reward_timer = 0
	for call in [[0xc111,0xc128,[page,0,0,5,31,319,0,0]], [0xc12d,0xc14a,[page,32,0,5,199,15,32,0]], [0xc14f,0xc16e,[page,32,304,5,199,319,32,304]], [0xc173,0xc190,[page,184,0,5,199,319,184,0]]]:
		_span(call[0], call[1])
		_child("copy_rect", call[2])
	_span(0xc195, 0xc19c)
	state.render_page = page
	_child("draw_page", [page])
	_span(0xc1a1, 0xc1a8)
	return {"work":path, "state":state, "graphics_state":device.graphics_state, "calls":calls, "locals":prior.locals, "tiles":prior.tiles, "doors":prior.doors, "actors":actor_result, "tail":result}
