extends RefCounted
## Child selection resource ownership. The caller supplies completion events.
const Assets = preload("res://scripts/resource_startup_assets.gd")
const Title = preload("res://scripts/resource_title.gd")
const Palettes = preload("res://scripts/resource_palette.gd")
const Saved = preload("res://scripts/resource_saved_surface.gd")
const AnimationMemory = preload("res://scripts/resource_animation.gd")

static func prepare(state: Dictionary, config: Dictionary, observer: Callable = Callable()):
	var m = state.memory
	var loader = Palettes.new(state.catalogs)
	state.interfacePalettes = {}
	for palette in config.palettes:
		state.interfacePalettes[palette.id] = loader.load_palette(palette.id,palette.banks)
		Title.emit(observer,"interface-palette-%d" % palette.id,state)
	Assets.select_cursor(state,1)
	m.heap.pack(0xffffff)
	var background: int = state.interfacePalettes[config.palettes[0].id]
	var decoration: int = state.interfacePalettes[config.palettes[1].id]
	m.address(background)
	var bounds: Array = config.screenBounds
	state.entranceSurface = {"rows":m.near.allocate(2*(bounds[2]-bounds[0])),"pixels":m.allocate_raw((bounds[2]-bounds[0])*(bounds[3]-bounds[1])),"bounds":bounds.duplicate()}
	for pair in [[background,1],[background,2],[decoration,4],[background,3]]:
		m.free_handle(Title.load_shape(state,pair[0],pair[1]))
	state.childPalettes = []
	for palette in config.childPalettes:
		state.childPalettes.append(loader.load_palette(palette.id,palette.banks))
		Title.emit(observer,"child-palette-%d" % palette.id,state)
	m.address(state.childPalettes[1])
	state.entranceSaved = []
	for rectangle in config.savedBounds: state.entranceSaved.append(Saved.new(m,rectangle))
	return prepare_frame(state,config.childPalettes[0].id,state.childPalettes[0],config.script,observer)

static func prepare_frame(state: Dictionary, id: int, palette: int, script: Dictionary, observer: Callable = Callable()):
	assert(not state.has("entranceAnimation") or state.entranceAnimation.disposed)
	var m = state.memory
	Assets.select_cursor(state,1)
	var found = state.catalogs.resolve("SCR",id)
	assert(not found.is_empty())
	state.entranceScript = state.direct.load_copy(found.entry.payload,found.catalog.handle,found.entry.handle)
	var data: PackedByteArray = m.resource_payloads[palette]
	m.address(palette)
	Title.emit(observer,"entrance-animation-before",state)
	state.entranceAnimation = AnimationMemory.prepare(m,script,data.decode_u16(2),palette,func(relative): return Title.load_shape(state,palette,relative))
	state.entrancePhase = "prepared"
	Title.emit(observer,"entrance-animation-after",state)
	return state.entranceAnimation

static func finish_frame(state: Dictionary, query_sound: int) -> void:
	assert(state.entrancePhase == "prepared")
	Assets.select_cursor(state,0)
	var queried = Assets.load_sound(state,query_sound)
	if queried: state.memory.address(queried)
	state.entranceAnimation.dispose()
	state.direct.release(state.entranceScript)
	state.entranceScript = 0
	state.entrancePhase = "finished"

static func finish(state: Dictionary, music: int) -> void:
	assert(state.entrancePhase == "finished")
	var m = state.memory
	m.free_raw(state.entranceSurface.pixels)
	m.near.release(state.entranceSurface.rows)
	state.entranceSurface = null
	state.entranceMusic = Assets.load_sound(state,music)
	m.lock(state.entranceMusic)
	Assets.select_cursor(state,0)
	state.entrancePhase = "ready"

static func initialize(state: Dictionary, config: Dictionary, observer: Callable = Callable()) -> void:
	prepare(state,config,observer)
	finish_frame(state,config.querySound)
	state.girlEntranceSaved = Saved.new(state.memory,config.postPreviewBounds[0])
	state.entranceSaved[2].dispose()
	prepare_frame(state,config.childPalettes[1].id,state.childPalettes[1],config.scripts[1],
		func(stage,s): Title.emit(observer,stage.replace("entrance-animation-","entrance-animation-2-"),s))
	finish_frame(state,config.querySound)
	state.boyEntranceSaved = Saved.new(state.memory,config.postPreviewBounds[1])
	prepare_frame(state,config.childPalettes[0].id,state.childPalettes[0],config.scripts[0],
		func(stage,s): Title.emit(observer,stage.replace("entrance-animation-","entrance-animation-3-"),s))
	finish_frame(state,config.querySound)
	finish(state,config.music)
	Title.emit(observer,"entrance-ready",state)

static func select_child(state: Dictionary, config: Dictionary, sex: int, observer: Callable = Callable()) -> void:
	assert(state.entrancePhase == "ready" and sex in [0,1])
	var upper: Array = [state.boyEntranceSaved,state.girlEntranceSaved]
	var choices = [[sex,sex],[1-sex,1-sex],[sex,sex+2]]
	for i in choices.size():
		var child: int = choices[i][0]
		var script_index: int = choices[i][1]
		prepare_frame(state,config.childPalettes[0].id+script_index,state.childPalettes[child],config.scripts[script_index],
			func(label,s): Title.emit(observer,label.replace("entrance-animation-","selection-animation-%d-" % (i+1)),s))
		finish_frame(state,config.querySound)
		if i < 2: upper[child].dispose()
		if i > 0: state.entranceSaved[child].dispose()
	for palette in state.childPalettes: state.memory.free_handle(palette)
	state.childPalettes = []
	state.entrancePhase = "selected"
	state.selectedChild = sex
	Title.emit(observer,"selection-complete",state)

static func prepare_idle(state: Dictionary, cloud: int) -> void:
	assert(state.entrancePhase == "ready")
	state.memory.free_handle(Title.load_shape(state,state.interfacePalettes[170],cloud+1))

static func advance_credit(state: Dictionary, bounds: Array) -> void:
	assert(state.entrancePhase == "ready")
	var m = state.memory
	var rows = m.near.allocate(2*(bounds[2]-bounds[0]))
	var pixels = m.allocate_raw((bounds[2]-bounds[0])*(bounds[3]-bounds[1]))
	m.free_handle(Title.load_shape(state,state.interfacePalettes[0],2))
	state.entranceCredit = (state.get("entranceCredit",0)+1) % 8
	m.free_handle(Title.load_shape(state,state.interfacePalettes[6],state.entranceCredit+4))
	m.free_raw(pixels)
	m.near.release(rows)
