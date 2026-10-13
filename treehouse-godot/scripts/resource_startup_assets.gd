extends RefCounted
## Startup source ownership for the pinned VGA/Sound Blaster launch profile.
const Startup = preload("res://scripts/resource_startup.gd")
const Cache = preload("res://scripts/resource_cache.gd")
const Catalog = preload("res://scripts/resource_catalog.gd")
const FontResources = preload("res://scripts/resource_font.gd")
const Cursor = preload("res://scripts/resource_cursor.gd")
const Saved = preload("res://scripts/resource_saved_surface.gd")
const Direct = preload("res://scripts/resource_direct.gd")
const Sound = preload("res://scripts/resource_sound.gd")

static func emit(observer: Callable, stage: String, phase: int, state: Dictionary) -> void:
	if observer.is_valid(): observer.call(stage,phase,state)

static func decode(value):
	# JSON integers arrive as floats; archive transport is compact base64.
	if value is float: return int(value)
	if value is Array: return value.map(decode)
	if value is Dictionary:
		var copy = {}
		for key in value: copy[key] = decode(value[key])
		return copy
	return value

static func from_data(encoded: Dictionary, observer: Callable = Callable()) -> Dictionary:
	var input: Dictionary = decode(encoded)
	for asset in input.builtins.values(): asset.payload = Marshalls.base64_to_raw(asset.payload)
	for archive in input.archives: archive.archive = Marshalls.base64_to_raw(archive.archive)
	return create(input,observer)

static func create(input: Dictionary, observer: Callable = Callable()) -> Dictionary:
	assert(input.archives.size() >= 2)
	var state = Startup.memory(input.startup)
	var m = state.memory
	state.soundRateLimits = input.soundRateLimits
	state.embeddedAssets = input.builtins
	state.builtins = Cache.new(m,0,true)
	state.catalogs = Catalog.new(m)
	var font = state.builtins.source("builtin:FONT:0",input.builtins.FONT.payload,input.builtins.FONT.flags)
	emit(observer,"font-activation",0,state)
	FontResources.activate(state.builtins,font)
	emit(observer,"font-activation",1,state)
	state.font = font
	state.cursor = Cursor.new(state.builtins,input.pixelsPerByte)
	emit(observer,"cursor-source",0,state)
	state.cursor.load_source("builtin:CURS:0",input.builtins.CURS.payload,input.builtins.CURS.flags)
	emit(observer,"cursor-source",1,state)
	emit(observer,"cursor-activation",0,state)
	state.cursor.activate()
	emit(observer,"cursor-activation",1,state)
	state.saved = Saved.new(m,input.savedRectangle,input.pixelsPerByte)
	var file_handle: int = input.get("firstFileHandle",5)
	var archive: Dictionary = input.archives[0]
	emit(observer,"catalog",0,state)
	var th_handle = state.catalogs.open(archive.archive,archive.filename,input.volume,file_handle)
	file_handle += 1
	emit(observer,"catalog",1,state)
	var th: Dictionary = state.catalogs.catalogs[th_handle]
	state.cursor.loader = th.loader
	emit(observer,"cursor-source",0,state)
	state.cursor.source = state.catalogs.load_source(th_handle,"CURS",1)
	emit(observer,"cursor-source",1,state)
	emit(observer,"cursor-activation",0,state)
	state.cursor.activate()
	emit(observer,"cursor-activation",1,state)
	state.gameFont = state.catalogs.load_source(th_handle,"FONT",1)
	emit(observer,"font-activation",0,state)
	FontResources.activate(th.loader,state.gameFont)
	emit(observer,"font-activation",1,state)
	state.available = m.available()
	var sound: Dictionary = {}
	for entry in th.records:
		if entry.tag == "" and entry.id == 1: sound = entry; break
	assert(not sound.is_empty(), "Missing sound configuration")
	state.direct = Direct.new(m)
	state.soundConfiguration = state.direct.load_copy(sound.payload,th_handle,sound.handle)
	for remaining in input.archives.slice(1):
		emit(observer,"catalog",0,state)
		state.catalogs.open(remaining.archive,remaining.filename,input.volume,file_handle)
		file_handle += 1
		emit(observer,"catalog",1,state)
	emit(observer,"startup-sound",0,state)
	state.backgroundSound = load_sound(state,0)
	m.retain(state.backgroundSound)
	emit(observer,"startup-sound",1,state)
	return state

static func load_sound(state: Dictionary, id: int) -> int:
	var found = state.catalogs.resolve("SND",id)
	if found.is_empty(): return 0
	var handle = state.catalogs.load_source(found.catalog.handle,"SND",id)
	var sound = Sound.new(state.memory,found.catalog.handle)
	var prepared = sound.prepare(handle,found.entry.payload,state.soundRateLimits)
	return 0 if prepared.action == "missing" else handle

static func select_cursor(state: Dictionary, id: int) -> void:
	var found = state.catalogs.resolve("CURS",id)
	if not found.is_empty():
		state.cursor.loader = found.catalog.loader
		state.cursor.source = state.catalogs.load_source(found.catalog.handle,"CURS",id)
	elif id == 0:
		var asset: Dictionary = state.embeddedAssets.CURS
		state.cursor.loader = state.builtins
		state.cursor.load_source("builtin:CURS:0",asset.payload,asset.flags)
	else:
		assert(false, "Missing cursor resource")
		return
	state.cursor.activate()
