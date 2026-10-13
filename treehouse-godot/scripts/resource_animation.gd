extends RefCounted
## Main C39D/BD14 object ownership and resident VGA surface storage.
var memory
var first: int
var last: int
var bounds: Array
var save_background: bool
var object_bytes: int
var object: int
var width: int
var height: int
var row_table: int = 0
var surface: int = 0
var backup: int = 0
var images: Dictionary = {}
var disposed: bool = false

func _init(model, first_shape: int, last_shape: int, rectangle: Array, save: bool = true) -> void:
	assert(first_shape >= 1 and last_shape >= first_shape and last_shape <= 255 and rectangle.size() == 4)
	memory = model
	first = first_shape
	last = last_shape
	bounds = rectangle.duplicate()
	save_background = save
	width = bounds[3]-bounds[1]
	height = bounds[2]-bounds[0]
	assert(width > 0 and height > 0)
	object_bytes = 2*(0x14e+last-first+1)
	object = memory.near.allocate(object_bytes)

static func prepare(model, script: Dictionary, last_shape: int, palette_handle: int, load_shape: Callable,
		save: bool = true, release_temporary_surface: Callable = Callable(), compose_initial: Callable = Callable()):
	# Scan the full script, then preload each used relative shape in order.
	var marked: Dictionary = {}
	for instruction in script.code:
		var code: int = instruction[0]
		var operand: Array = instruction[1]
		if code == 0: break
		if (code & 0xf0) != 0xc0: continue
		var beginning: int = operand[0] | (operand[1] << 8)
		var ending: int = operand[2] | (operand[3] << 8)
		if not beginning: continue
		for relative in range(beginning,ending+1):
			assert(relative >= 1 and relative <= last_shape)
			marked[relative] = true
	var saved: int = model.handle(palette_handle).state
	var scene = load("res://scripts/resource_animation.gd").new(model,1,last_shape,script.bounds,save)
	model.lock(palette_handle)
	var ordered = marked.keys()
	ordered.sort()
	for relative in ordered: scene.own(relative,load_shape.call(relative))
	model.unlock(palette_handle)
	model.retain(palette_handle)
	if release_temporary_surface.is_valid(): release_temporary_surface.call()
	scene.create_surface()
	if save: scene.create_backup()
	if compose_initial.is_valid(): compose_initial.call(scene)
	model.flags(palette_handle,saved)
	return scene

func own(relative: int, handle: int) -> int:
	assert(not disposed and relative >= first and relative <= last and not images.has(relative))
	images[relative] = handle
	return handle

func create_surface() -> int:
	assert(not disposed and not surface)
	row_table = memory.near.allocate(2*height)
	surface = memory.allocate_raw(width*height)
	return surface

func create_backup() -> int:
	assert(not disposed and surface and save_background and not backup)
	backup = memory.allocate_raw(width*height)
	return backup

func dispose() -> void:
	assert(not disposed)
	var ordered = images.keys()
	ordered.sort()
	for relative in ordered: memory.free_handle(images[relative])
	memory.free_raw(surface)
	if row_table: memory.near.release(row_table)
	memory.free_raw(backup)
	memory.near.release(object)
	disposed = true
