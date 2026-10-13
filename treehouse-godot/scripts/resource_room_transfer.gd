extends RefCounted
## Board-bound ring/bubble ownership for the initial central-room arrangement.
## The caller drives SCR display, sound and completion events.
const Assets = preload("res://scripts/resource_startup_assets.gd")
const Title = preload("res://scripts/resource_title.gd")
const Palettes = preload("res://scripts/resource_palette.gd")
const Saved = preload("res://scripts/resource_saved_surface.gd")
const AnimationMemory = preload("res://scripts/resource_animation.gd")

static func temporary(state: Dictionary, bounds: Array) -> Dictionary:
	return {"rows":state.memory.near.allocate(2*(bounds[2]-bounds[0])),"pixels":state.memory.allocate_raw((bounds[2]-bounds[0])*(bounds[3]-bounds[1]))}

static func release_surface(state: Dictionary, surface: Dictionary) -> void:
	state.memory.free_raw(surface.pixels)
	state.memory.near.release(surface.rows)

static func draw(state: Dictionary, palette: int, relative: int) -> void:
	state.memory.free_handle(Title.load_shape(state,palette,relative))

static func begin(state: Dictionary, config: Dictionary, observer: Callable = Callable()):
	assert(state.entrancePhase == "room")
	var m = state.memory
	state.transferPalette = Palettes.new(state.catalogs).load_palette(config.palette.id,config.palette.banks)
	state.transferSound = Assets.load_sound(state,config.sound)
	m.lock(state.transferSound)
	Assets.select_cursor(state,1)
	var found = state.catalogs.resolve("SCR",config.palette.id)
	assert(not found.is_empty())
	state.transferScript = state.direct.load_copy(found.entry.payload,found.catalog.handle,found.entry.handle)
	var data: PackedByteArray = m.resource_payloads[state.transferPalette]
	m.address(state.transferPalette)
	Title.emit(observer,"transfer-animation-before",state)
	state.transferAnimation = AnimationMemory.prepare(m,config.script,data.decode_u16(2),state.transferPalette,
		func(relative): return Title.load_shape(state,state.transferPalette,relative),true,Callable(),
		func(_scene): draw(state,state.roomPalettes[20500],1))
	state.entrancePhase = "transfer-prepared"
	Title.emit(observer,"transfer-animation-after",state)
	return state.transferAnimation

static func start_ring(state: Dictionary) -> void:
	assert(state.entrancePhase == "transfer-prepared")
	Assets.select_cursor(state,0)
	state.entrancePhase = "ring-playing"

static func compose_ring(state: Dictionary) -> void:
	assert(state.entrancePhase == "ring-playing")
	draw(state,state.roomPalettes[20500],1)

static func prepare_bubble(state: Dictionary, config: Dictionary, observer: Callable = Callable()):
	assert(state.entrancePhase == "ring-playing")
	var m = state.memory
	var queried = Assets.load_sound(state,config.querySound)
	if queried: m.address(queried)
	state.transferAnimation.dispose()
	state.direct.release(state.transferScript)
	state.transferScript = 0
	var bounds: Array = state.characterSaved.bounds.duplicate()
	var surface = temporary(state,bounds)
	state.characterSaved.dispose()
	draw(state,state.transferPalette,6)
	state.characterSaved = Saved.new(m,bounds)
	draw(state,state.roomPalettes[20500],1)
	release_surface(state,surface)
	m.discardable(state.transferPalette)
	state.transferPalette = 0
	var inlet = temporary(state,config.inletBounds)
	state.inletSaved = Saved.new(m,config.inletBounds)
	draw(state,state.interfacePalettes[900],27)
	release_surface(state,inlet)
	Assets.select_cursor(state,1)
	var found = state.catalogs.resolve("SCR",config.id)
	assert(not found.is_empty())
	state.transferScript = state.direct.load_copy(found.entry.payload,found.catalog.handle,found.entry.handle)
	var list = state.catalogs.resolve("PSL",config.id)
	assert(not list.is_empty())
	var list_handle = state.catalogs.load_source(list.catalog.handle,"PSL",config.id)
	var sounds: PackedByteArray = m.resource_payloads[list_handle]
	m.address(list_handle)
	var count = sounds.decode_u16(0)
	assert(sounds.size() == 2+count*2)
	for i in count:
		m.address(list_handle)
		Assets.load_sound(state,sounds.decode_u16(2+2*i))
	m.free_handle(list_handle)
	var palette: int = state.roomPalettes[1100]
	var data: PackedByteArray = m.resource_payloads[palette]
	m.address(palette)
	Title.emit(observer,"bubble-animation-before",state)
	state.transferAnimation = AnimationMemory.prepare(m,config.script,data.decode_u16(2),palette,
		func(relative): return Title.load_shape(state,palette,relative))
	state.entrancePhase = "bubble-prepared"
	Title.emit(observer,"bubble-animation-after",state)
	return state.transferAnimation

static func start_bubble(state: Dictionary) -> void:
	assert(state.entrancePhase == "bubble-prepared")
	Assets.select_cursor(state,0)
	state.entrancePhase = "bubble-playing"

static func play_bubble_sound(state: Dictionary, id: int) -> void:
	assert(state.entrancePhase == "bubble-playing")
	var sound = Assets.load_sound(state,id)
	if state.transferSound: state.memory.unlock(state.transferSound)
	state.transferSound = sound
	state.memory.lock(sound)

static func finish(state: Dictionary, query_sound: int, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "bubble-playing")
	var m = state.memory
	var queried = Assets.load_sound(state,query_sound)
	if queried: m.address(queried)
	if state.transferSound: m.unlock(state.transferSound)
	state.transferSound = 0
	state.transferAnimation.dispose()
	state.direct.release(state.transferScript)
	state.transferScript = 0
	var surface = temporary(state,state.inletSaved.bounds)
	state.inletSaved.dispose()
	state.inletSaved = null
	release_surface(state,surface)
	state.entrancePhase = "transfer-complete"
	Title.emit(observer,"transfer-complete",state)

static func release_room(state: Dictionary, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "transfer-complete")
	Title.emit(observer,"room-release-before",state)
	for item in state.roomObjects: item.saved.dispose()
	state.theaterSaved.dispose()
	state.characterSaved.dispose()
	for id in [20500,1200,1250,1100]: state.memory.discardable(state.roomPalettes[id])
	state.roomPalettes.clear()
	state.memory.heap.pack(0xffffff)
	state.entrancePhase = "room-released"
	Title.emit(observer,"room-release-after",state)
