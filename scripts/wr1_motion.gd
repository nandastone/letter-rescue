extends RefCounted
## Original WR1 movement/animation/camera, one call per logical gameplay update.
## Sources and deliberate limitations: testing/wr1_movement_research.md and peers.

const STEP_SECONDS: float = 12428.0 * 8.0 / 1193182.0
const LEFT_WALK := [13, 14, 14, 15, 16, 17, 17, 18]
const RIGHT_WALK := [3, 4, 4, 5, 6, 7, 7, 8]
const POSES := [[9, 10, 9, 25], [19, 20, 19, 24]]

var attributes: Array = []
var width: int
var height: int
# Original screen anchors: x is sprite LEFT, y is sprite BOTTOM.
var x: int
var y: int
var gx: int
var gy: int
var camera_x: int
var camera_y: int
var phase: int = 0
var frame: int = 0
var facing: int = 0
var idle_ticks: int = 3
var left_index: int = -1
var right_index: int = -1
var climbing: bool = false
var ticks: int = 0
var background_frame: int = 0

func configure(data: Dictionary) -> void:
	attributes = data["attributes"]
	height = attributes.size()
	width = attributes[0].size()
	var start: Array = data["start"]
	camera_x = mini(maxi(int(start[0]) - 18, 0), width - 37)
	camera_y = mini(maxi(int(start[1]) - 11, 0), height - 20)
	x = (int(start[0]) - camera_x) * 8 + 16
	y = (int(start[1]) - camera_y) * 8 + 40
	gx = int(float(x - 16) / 8.0) + camera_x - 1
	gy = int(float(y - 31) / 8.0) + camera_y
	phase = 0
	frame = 0
	# Live level-1 startup and jump trace confirm main-entry facing wins (right).
	facing = 0
	idle_ticks = 3
	left_index = -1
	right_index = -1
	ticks = 0

func attr(cx: int, cy: int) -> int:
	# Safe world boundary for the clone; original out-of-map memory is undefined.
	if cx < 0 or cx >= width or cy < 0:
		return 0x73
	if cy >= height:
		return 0
	return int(attributes[cy][cx])

func step(up: bool, down: bool, left: bool, right: bool) -> void:
	var old_y: int = y
	if frame == 9:
		frame = 0
	var support: int = attr(gx + 1, gy)
	if support != 0x73 and support != 0x74:
		support = 0
	climbing = false
	if up:
		idle_ticks = 0
		climbing = ((support == 0x74 and attr(gx + 1, gy - 2) == 0x74)
			or (attr(gx + 1, gy - 1) == 0x74 and attr(gx + 1, gy - 3) == 0x74))
		if climbing:
			frame = 23 if frame == 22 else 22
			phase = 0
		elif support != 0:
			frame = POSES[facing][0]
			phase = 0
		else:
			frame = POSES[facing][1 if phase < 9 else 3]
		if phase < 9:
			y -= 8
			gy -= 1
			for col in range(gx, gx + 3):
				if attr(col, gy - 4) == 0x73:
					y += 8
					gy += 1
					phase = 16
					break
		else:
			y += 8
			gy += 1
			frame = POSES[facing][3]
	elif support == 0 or (down and support == 0x74):
		climbing = ((support == 0x74 or attr(gx + 1, gy + 1) == 0x74)
			and (attr(gx + 1, gy - 1) == 0x74 or attr(gx + 1, gy - 2) == 0x74))
		frame = (23 if frame == 22 else 22) if climbing else POSES[facing][3]
		if attr(gx, gy - 1) == 0x73:
			gx += 1
			x += 8
		if attr(gx + 2, gy - 1) == 0x73:
			gx -= 1
			x -= 8
		y += 8
		gy += 1
	phase = mini(phase + 1, 16)
	if not (up or down or left or right):
		_idle(support)
	if left:
		idle_ticks = 0
		x -= 8
		gx -= 1
		for row in range(gy - 4, gy):
			if attr(gx, row) == 0x73:
				gx += 1
				x += 8
				break
		facing = 1
		right_index = -1
		left_index = (left_index + 1) % 8
		if y == old_y and frame != 9:
			frame = LEFT_WALK[left_index]
	if right:
		idle_ticks = 0
		x += 8
		gx += 1
		for row in range(gy - 4, gy):
			if attr(gx + 2, row) == 0x73:
				gx -= 1
				x -= 8
				# No break in WR1: later rows inspect the shifted column again.
		facing = 0
		left_index = -1
		right_index = (right_index + 1) % 8
		if y == old_y and frame != 9:
			frame = RIGHT_WALK[right_index]
	ticks += 1

func _idle(support: int) -> void:
	idle_ticks += 1
	if idle_ticks > 17:
		if frame < 2:
			idle_ticks = 0
			frame ^= 1
		elif frame < 22:
			frame = 0
			idle_ticks = 0
		elif frame == 24 or frame == 25:
			frame = POSES[facing][2]
	elif frame in [0, 1, 11, 21, 22, 23]:
		pass
	elif frame in [10, 25]:
		if support != 0:
			frame = 9
	elif frame in [20, 24]:
		if support != 0:
			frame = 19
	elif left_index > -1:
		left_index = 0
		right_index = -1
		frame = 12
	else:
		right_index = 0
		frame = 2

func scroll_camera() -> void:
	# Called at the normal original render point, not on each Godot draw frame.
	if camera_x > 0 and x < 144:
		camera_x -= 1
		x += 8
	elif camera_x < width - 36 and x > 144:
		camera_x += 1
		x -= 8
	if camera_y > 0 and y < 108:
		camera_y -= 1
		y += 8
	elif camera_y < height - 19 and y > 132:
		camera_y += 1
		y -= 8

func render_step() -> void:
	scroll_camera()
	# DS:41be advances on every original renderer invocation, even offscreen.
	background_frame = (background_frame + 1) % 4

func world_position() -> Vector2i:
	return Vector2i(x + camera_x * 8, y + camera_y * 8)

func snapshot() -> Dictionary:
	return {"tick": ticks, "x": x, "y": y, "gx": gx, "gy": gy,
		"camera_x": camera_x, "camera_y": camera_y, "phase": phase,
		"sprite": frame, "facing": facing, "idle_ticks": idle_ticks,
		"left_index": left_index, "right_index": right_index,
		"world_x": world_position().x, "world_y": world_position().y,
		"background_frame": background_frame}
