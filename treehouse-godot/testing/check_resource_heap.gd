extends SceneTree

var checks: Array = []

func integers(value):
	if value is float: return int(value)
	if value is Array: return value.map(integers)
	if value is Dictionary:
		var result = {}
		for key in value: result[key] = integers(value[key])
		return result
	return value

func _initialize() -> void:
	var output = OS.get_cmdline_user_args()[0]
	for path in ["res://scripts/resource_heap.gd", "res://scripts/resource_near_heap.gd"]:
		if not FileAccess.file_exists(path):
			push_error("Missing Godot allocation module: " + path)
			quit(1)
			return
	var heap_script = load("res://scripts/resource_heap.gd")
	var near_script = load("res://scripts/resource_near_heap.gd")
	var fixture = integers(JSON.parse_string(FileAccess.get_file_as_string(output + "/fixture.json")))
	var calls: Array = []
	for c in fixture.calls:
		var heap = heap_script.new(c.initial)
		var available = heap.call(c.operation, c.requested)
		calls.append({"state":heap.snapshot(), "available":available, "moves":heap.moves})
	var near = near_script.new(fixture.near_initial)
	var snapshots: Array = []
	var returns: Array = []
	var allocations = 0
	var frees = 0
	for event in fixture.stream:
		if event.type == "checkpoint":
			snapshots.append(near.snapshot())
		else:
			match event.label:
				"memory.handle.allocate": near.reset_search()
				"memory.near.allocate":
					returns.append(near.allocate(event.stack[2]))
					allocations += 1
				"memory.near.allocate.return":
					checks.append({"name":"near returned pointer %d" % checks.size(), "passed":not returns.is_empty() and returns.pop_back() == event.ax})
				"memory.near.free":
					near.release(event.stack[2])
					frees += 1
	checks.append({"name":"all near allocation calls returned", "passed":returns.is_empty()})
	focused(heap_script, near_script)
	var file = FileAccess.open(output + "/godot.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"calls":calls, "near":snapshots, "checks":checks, "allocations":allocations, "frees":frees}))
	file.close()
	quit()

func focused(heap_script, near_script) -> void:
	var a = heap_script.new({"blocks":[{"address":16,"size":20,"flags":0,"padding":0},{"address":36,"size":6,"flags":0x4000,"padding":0}],"handles":[],"search":16})
	a.reserve(a.at(16), 11, true)
	checks.append({"name":"small remainder is retained as padding", "passed":a.blocks.size()==2 and a.blocks[0].padding==3})
	var b = heap_script.new({"blocks":[{"address":16,"size":40,"flags":0,"padding":1},{"address":56,"size":6,"flags":0x4000,"padding":0}],"handles":[],"search":16})
	b.reserve(b.at(16), 11, true)
	checks.append({"name":"tail split clears free padding", "passed":b.blocks[0].size==22 and b.blocks[0].padding==0 and b.blocks[1].padding==1})
	var c = heap_script.new({"blocks":[{"address":16,"size":8,"flags":0,"padding":1},{"address":24,"size":10,"flags":0,"padding":0},{"address":34,"size":6,"flags":0x4000,"padding":0}],"handles":[],"search":16})
	c.coalesce(c.at(16))
	checks.append({"name":"coalescing preserves first free padding", "passed":c.blocks.size()==2 and c.blocks[0].size==18 and c.blocks[0].padding==1})
	var d = heap_script.new({"blocks":[{"address":16,"size":8,"flags":0xc000,"padding":0,"handle":4,"payload":"kept"},{"address":24,"size":6,"flags":0x4000,"padding":0}],"handles":[{"id":4,"state":0x8000,"segment":1}],"search":16})
	checks.append({"name":"locked handle cannot relocate", "passed":not d.relocate(d.at(16)) and d.moves.is_empty() and d.blocks[0].payload=="kept"})
	var initial = {"start":100,"search":100,"end":110,"blocks":[{"address":100,"size":8,"free":true},{"address":110,"size":65534,"free":false}]}
	var e = near_script.new(initial, {"limit":128,"quantum":16})
	checks.append({"name":"near growth honors explicit platform limit", "passed":e.allocate(13)==102 and e.end==126 and e.at(100).size==14 and e.at(116).size==8})
	var f = near_script.new(initial)
	checks.append({"name":"insufficient near growth leaves state intact", "passed":not f.grow(13,112,16) and f.snapshot()==initial})
