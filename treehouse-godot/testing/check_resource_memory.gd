extends SceneTree
const Memory = preload("res://scripts/resource_memory.gd")
var checks: Array = []

func integers(value):
	if value is float: return int(value)
	if value is Array: return value.map(integers)
	if value is Dictionary:
		var result = {}
		for key in value: result[key] = integers(value[key])
		return result
	return value

func check(value: bool, name: String) -> void:
	checks.append({"name":name, "passed":value})

func snapshot(memory, static_ids: Array) -> Dictionary:
	var heap = memory.heap.snapshot()
	var active = static_ids.duplicate()
	for block in heap.blocks:
		block.erase("payload")
		if block.flags == 0xc000: active.append(block.handle)
	heap.handles = heap.handles.filter(func(h): return h.id in active)
	return {"heap":heap, "near":memory.near.snapshot()}

func _initialize() -> void:
	var output = OS.get_cmdline_user_args()[0]
	var fixture = integers(JSON.parse_string(FileAccess.get_file_as_string(output + "/fixture.json")))
	var m = Memory.new(fixture.initial)
	var states: Array = []
	var far: Array = []
	var near: Array = []
	var owners: Array = []
	var resizes: Array = []
	var allocations = 0
	var frees = 0
	for e in fixture.stream:
		if e.type == "checkpoint":
			states.append(snapshot(m, fixture.static_ids))
			if e.index % 2 == 0: m.heap.prepare(e.requested)
			continue
		var s: Array = e.stack
		var name: String = "%s at %s" % [e.label, e.milliseconds]
		match e.label:
			"memory.handle.allocate":
				m.near.reset_search()
				owners.append({"kind":"handle"})
			"memory.raw.allocate": owners.append({"kind":"raw"})
			"memory.near.allocate":
				var pointer = m.near.allocate(s[2])
				near.append(pointer)
				if not owners.is_empty() and owners[-1].kind == "handle" and not owners[-1].has("id"): owners[-1].id = pointer
			"memory.near.allocate.return": check(near.pop_back() == e.ax, name)
			"memory.near.free":
				m.near.release(s[2])
				m.heap.handles.erase(s[2])
			"memory.far.allocate":
				var block = m.heap.first_fit(e.ax+65536*e.dx)
				far.append(block)
				if not owners.is_empty(): owners[-1].block = block
				allocations += 1
			"memory.far.allocate.return": check(far.pop_back().address == 16*e.ds+e.si, name)
			"memory.resize": resizes.append({} if not resizes.is_empty() else m.resize(m.heap.at(16*e.ds+e.si), e.ax+65536*e.dx))
			"memory.resize.return": resizes.pop_back()
			"memory.promote.move": m.move_handle_to(e.di, m.heap.at(16*e.ds+e.si))
			"memory.grow.pin": m.handle(e.di).state |= 0x8000
			"memory.grow.unpin": m.unlock(e.di)
			"memory.grow.move": m.move_handle_to(e.di, m.heap.at(16*e.es+e.bx))
			"memory.reallocate": owners.append({"kind":"reallocate", "id":s[4]})
			"memory.reallocate.return":
				var owner: Dictionary = owners.pop_back()
				check(owner.kind == "reallocate", name)
				if e.ax == 0:
					var old: int = m.handle(owner.id).state
					m.claim_handle(owner.block, owner.id)
					m.handle(owner.id).state |= old & 0xfdf0
			"memory.handle.allocate.return":
				var owner: Dictionary = owners.pop_back()
				check(owner.kind == "handle" and owner.id == e.ax, name)
				m.claim_handle(owner.block, owner.id)
			"memory.raw.allocate.return":
				var owner: Dictionary = owners.pop_back()
				check(owner.kind == "raw" and m.claim_raw(owner.block) == 16*e.dx+e.ax, name)
			"memory.raw.free":
				m.free_raw(s[2]+16*s[3])
				frees += 1
			"memory.handle.free": m.unlock(s[2])
			"memory.discard": m.discard(s[2])
			"memory.lock": m.lock(s[2])
			"memory.unlock": m.unlock(s[2])
			"memory.retain": m.retain(s[2])
			"memory.keep.resident": m.keep_resident(s[2])
			"memory.discardable": m.discardable(s[2])
			"memory.flags": m.flags(s[3], s[2])
			"memory.address": m.address(s[2])
			"memory.resource.restore": m.handle(e.bp).state = s[0]
			"memory.resource.cached": m.handle(e.bp).state |= 0x1000
			_:
				if e.label.begins_with("memory.catalog.pin"):
					m.handle(e.bx if e.label.ends_with(".find") else e.bp).state |= 0x8000
				elif e.label.begins_with("memory.catalog.restore"):
					m.handle(e.bx if e.label.ends_with(".outer") or e.label.ends_with(".find") else e.bp).state = s[0]
	# The final native checkpoint is after prepare(), inside a raw allocation.
	# Its far allocation and raw return occur after the fixture window.
	check(far.is_empty() and near.is_empty() and owners == [{"kind":"raw"}] and resizes.is_empty(), "only final raw allocation remains in progress")
	focused_checks()
	var file = FileAccess.open(output + "/godot.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"states":states, "checks":checks, "allocations":allocations, "frees":frees}))
	file.close()
	quit()

func example():
	return Memory.new({"heap":{"search":16, "blocks":[
		{"address":16,"size":16,"flags":0xc000,"padding":0,"handle":102},
		{"address":32,"size":8,"flags":0,"padding":0},
		{"address":40,"size":8,"flags":0x8000,"padding":0},
		{"address":48,"size":6,"flags":0x4000,"padding":0}],
		"handles":[{"id":102,"state":0x7000,"segment":1}]},
		"near":{"start":100,"search":100,"end":202,"blocks":[
		{"address":100,"size":100,"free":true},{"address":202,"size":65534,"free":false}]}})

func focused_checks() -> void:
	var a = example()
	var grown = a.resize(a.heap.at(16), 17)
	check(grown.size == 24 and grown.padding == 1 and grown.flags == 0xc000, "growth recalculates padding")
	var b = example()
	check(b.resize(b.heap.at(16), 19).is_empty() and b.heap.at(16).size == 16 and b.heap.at(32).size == 8 and b.heap.search == 16, "failed growth restores original allocation")
	var c = example()
	c.lock(102)
	check(not c.discard(102), "locked resource cannot be discarded")
	c.unlock(102)
	check(c.discard(102) and c.heap.at(16).flags == 0 and c.handle(102).segment == 0 and c.handle(102).state == 0x5000, "discard preserves ownership flags")
	var d = example()
	d.flags(102, 0x8000)
	d.retain(102)
	d.discardable(102)
	d.keep_resident(102)
	check(d.handle(102).state == 0xf000, "ownership operations preserve independent bits")
	var e = example()
	e.heap.at(16).payload = "preserved bytes"
	var pointer = e.detach_handle(102)
	check(pointer==22 and e.heap.at(16).flags==0x8000 and e.handle(102).segment==0, "detach transfers raw ownership")
	check(e.attach_handle(102,pointer) and e.heap.at(16).payload=="preserved bytes" and e.heap.at(16).handle==102 and e.address(102)==pointer, "adopt preserves payload and handle identity")
	var cache = {"shape":102}
	var entry = {"handle":102}
	e.resource_owners[102] = {"cache":cache,"key":"shape","entry":entry}
	e.resource_payloads[102] = PackedByteArray([1,2,3])
	e.free_handle(102)
	check(not cache.has("shape") and entry.handle==0 and e.resource_owners.is_empty() and e.resource_payloads.is_empty() and not e.heap.handles.has(102), "free removes owned catalog and payload links")
