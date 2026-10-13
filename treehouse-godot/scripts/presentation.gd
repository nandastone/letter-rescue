extends RefCounted
## Pinned reference VGA PART scanout, fed only independently rendered pixels.
signal presented(frame: Image, milliseconds: float)
# Mode 13h: 800 dots/line at 25.175 MHz, 400 visible physical lines.
const PART_MS = 800.0*100.0/25175000.0*1000.0
# VGA_SetupDrawing retains the previous mode-3 vertical period: the difference
# from mode 13h is below its 0.0001 ms change threshold (vga_draw.cpp:1578).
const FRAME_MS = 900.0*449.0/28322000.0*1000.0
var part_ms: float
var frame_ms: float
var parts: int
var time_ms: float = 0.0
var start_ms: float = 0.0
var part: int = 0
var source: Image
var scanning: Image
var image: Image
var count: int = 0

func _init(read_period: float = PART_MS, frame_period: float = FRAME_MS, bands: int = 4) -> void:
	assert(is_finite(read_period) and read_period>0 and bands>0)
	assert(is_finite(frame_period) and frame_period>=read_period*bands)
	# PIC_AddEvent receives float delays in the pinned core.
	part_ms = PackedFloat32Array([read_period])[0]
	frame_ms = PackedFloat32Array([frame_period])[0]
	parts = bands

func reset(milliseconds: float, framebuffer: Image) -> void:
	assert(is_finite(milliseconds) and framebuffer.get_height()%parts==0)
	time_ms = milliseconds
	start_ms = milliseconds
	part = 0
	count = 0
	source = framebuffer.duplicate()
	scanning = framebuffer.duplicate()
	image = framebuffer.duplicate()

func commit(milliseconds: float, framebuffer: Image) -> void:
	if source==null:
		reset(milliseconds,framebuffer)
		return
	assert(framebuffer.get_size()==source.get_size())
	advance_to(milliseconds,false)
	source.copy_from(framebuffer)
	advance_to(milliseconds)

func advance_to(milliseconds: float, inclusive: bool = true) -> void:
	assert(is_finite(milliseconds) and milliseconds>=time_ms)
	if source==null:
		return
	while true:
		var read_at = start_ms+(part+1)*part_ms
		if read_at>milliseconds or (not inclusive and read_at==milliseconds):
			break
		var rows = int(source.get_height()/parts)
		var region = Rect2i(0,part*rows,source.get_width(),rows)
		scanning.blit_rect(source,region,region.position)
		part += 1
		if part==parts:
			image = scanning.duplicate()
			count += 1
			presented.emit(image,read_at)
			part = 0
			start_ms += frame_ms
	time_ms = milliseconds
