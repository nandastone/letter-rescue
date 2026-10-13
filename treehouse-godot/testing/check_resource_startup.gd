extends SceneTree
const Assets = preload("res://scripts/resource_startup_assets.gd")
const Startup = preload("res://scripts/resource_startup.gd")
const FontResources = preload("res://scripts/resource_font.gd")
var boundaries: Dictionary = {}

func snapshot(state: Dictionary) -> Dictionary:
	var arena = Startup.arena_snapshot(state.memory)
	for block in arena.heap.blocks:
		if block.has("handle") and state.memory.resource_payloads.has(block.handle):
			var hash = HashingContext.new()
			hash.start(HashingContext.HASH_SHA256)
			hash.update(state.memory.resource_payloads[block.handle])
			block.payload = hash.finish().hex_encode()
	var catalogs: Array = []
	for file in state.catalogs.files: catalogs.append(state.catalogs.snapshot(file.handle))
	return {"arena":arena,"near":state.memory.near.snapshot(),"dos":state.dos.snapshot(),"files":state.catalogs.files.duplicate(true),"catalogs":catalogs}

func observe(stage: String, _phase: int, state: Dictionary) -> void:
	if not boundaries.has(stage): boundaries[stage] = []
	if stage == "catalog" or boundaries[stage].size() < 2: boundaries[stage].append(snapshot(state))

func _initialize() -> void:
	var output = OS.get_cmdline_user_args()[0]
	var input = JSON.parse_string(FileAccess.get_file_as_string(output+"/fixture.json"))
	var state = Assets.from_data(input,observe)
	var before = snapshot(state)
	FontResources.activate(state.builtins,state.font)
	var stable = snapshot(state) == before
	var m = state.memory
	var discarded: int = state.builtins.sources["builtin:CURS:0"]
	var locked: int = state.cursor.image
	var locked_address = m.address(locked)
	m.discardable(discarded)
	m.discardable(locked)
	var available = m.available()
	var checks = [
		{"name":"active font is not converted twice","passed":stable},
		{"name":"cursor background derives from pixel packing","passed":state.cursor.stride==16 and m.heap.at(state.cursor.background-6).size-6==256},
		{"name":"maximal query discards eligible payload and retains handle","passed":m.handle(discarded).segment==0 and not m.resource_payloads.has(discarded) and available>0},
		{"name":"maximal query preserves locked resource address and bytes","passed":m.address(locked)==locked_address and m.resource_payloads.has(locked)},
		{"name":"oversized searches clamp to conventional extent","passed":m.heap.search_size(0xffffff)==0xfffff and m.heap.search_size(0xffffffff)==0xfffff}]
	var file = FileAccess.open(output+"/godot.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"boundaries":boundaries,"checks":checks}))
	file.close()
	quit()
