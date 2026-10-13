extends RefCounted
## Title resource ownership at semantic boundaries. Playback owns the clock.
const Assets = preload("res://scripts/resource_startup_assets.gd")
const Palettes = preload("res://scripts/resource_palette.gd")
const AnimationMemory = preload("res://scripts/resource_animation.gd")

static func emit(observer: Callable, stage: String, state: Dictionary) -> void:
	if observer.is_valid(): observer.call(stage,state)

static func load_shape(state: Dictionary, palette: int, relative: int) -> int:
	var data: PackedByteArray = state.memory.resource_payloads[palette]
	var id = data.decode_u16(0)+relative-1
	var found = state.catalogs.resolve("SHAP",id)
	assert(not found.is_empty())
	return state.catalogs.load_shape(found.catalog.handle,id,palette)

static func prepare(state: Dictionary, config: Dictionary, observer: Callable = Callable()):
	var m = state.memory
	var palettes = Palettes.new(state.catalogs)
	state.driverSound = Assets.load_sound(state,65535)
	emit(observer,"driver-sound",state)
	var background = palettes.load_palette(config.backgroundPalette.id,config.backgroundPalette.banks)
	emit(observer,"background-palette",state)
	m.free_handle(load_shape(state,background,1))
	emit(observer,"background-drawn",state)
	var bounds: Array = config.backgroundBounds
	state.titleSurface = {"rows":m.near.allocate(2*(bounds[2]-bounds[0])),"pixels":m.allocate_raw((bounds[3]-bounds[1])*(bounds[2]-bounds[0])),"bounds":bounds.duplicate()}
	emit(observer,"title-surface",state)
	m.free_handle(load_shape(state,background,2))
	m.free_handle(background)
	emit(observer,"background-released",state)
	state.titlePalette = palettes.load_palette(config.animationPalette.id,config.animationPalette.banks)
	emit(observer,"title-palette",state)
	state.titleSound = Assets.load_sound(state,config.sound)
	m.lock(state.titleSound)
	emit(observer,"title-sound",state)
	return prepare_animation(state,config.animationPalette.id,config.script,config.animationOrigin,observer)

static func prepare_animation(state: Dictionary, id: int, script: Dictionary, origin: Array, observer: Callable = Callable()):
	assert(not state.has("titleAnimation") or state.titleAnimation.disposed)
	var m = state.memory
	Assets.select_cursor(state,1)
	var found = state.catalogs.resolve("SCR",id)
	assert(not found.is_empty())
	state.titleScript = state.direct.load_copy(found.entry.payload,found.catalog.handle,found.entry.handle)
	var bounds: Array = script.bounds.duplicate()
	var height: int = bounds[2]-bounds[0]
	var width: int = bounds[3]-bounds[1]
	bounds[0] = origin[1]-height
	bounds[2] = origin[1]
	bounds[1] = origin[0]-int(width/2)
	bounds[3] = bounds[1]+width
	var data: PackedByteArray = m.resource_payloads[state.titlePalette]
	var positioned: Dictionary = script.duplicate()
	positioned.bounds = bounds
	emit(observer,"animation-before",state)
	state.titleAnimation = AnimationMemory.prepare(m,positioned,data.decode_u16(2),state.titlePalette,func(relative): return load_shape(state,state.titlePalette,relative))
	state.titlePhase = "prepared"
	emit(observer,"animation-after",state)
	return state.titleAnimation

static func start_animation(state: Dictionary) -> void:
	assert(state.titlePhase == "prepared")
	Assets.select_cursor(state,0)
	state.titlePhase = "playing"

static func finish_animation(state: Dictionary, query_sound: int) -> void:
	assert(state.titlePhase == "playing")
	var queried = Assets.load_sound(state,query_sound)
	if queried: state.memory.address(queried)
	state.titleAnimation.dispose()
	state.direct.release(state.titleScript)
	state.titleScript = 0
	state.titlePhase = "finished"

static func release_title(state: Dictionary) -> void:
	assert(state.titlePhase == "finished")
	var m = state.memory
	m.free_handle(state.titlePalette)
	state.titlePalette = 0
	m.free_raw(state.titleSurface.pixels)
	m.near.release(state.titleSurface.rows)
	state.titleSurface = null
	state.titlePhase = "released"

static func finish_music(state: Dictionary) -> void:
	if state.titleSound:
		state.memory.unlock(state.titleSound)
		state.titleSound = 0
