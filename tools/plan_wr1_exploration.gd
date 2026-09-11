extends SceneTree
## Offline input planning against recovered collision rules. Outputs only held
## controls; native captures independently determine whether the route succeeds.
const Motion = preload("res://scripts/core/wr1_motion.gd")
const FIELDS = ["width","height","x","y","gx","gy","camera_x","camera_y","phase","frame","facing","idle_ticks","left_index","right_index","background_frame"]
const CONTROLS = [{"left":true},{"right":true},{"up":true,"left":true},
	{"up":true,"right":true},{"up":true},{"down":true},{"down":true,"left":true},{"down":true,"right":true},{}]

func copy(p: RefCounted) -> RefCounted:
	var result = Motion.new()
	result.attributes = p.attributes
	for field in FIELDS:
		result.set(field, p.get(field))
	return result

func key(p: RefCounted) -> String:
	return "%d,%d,%d,%d,%d" % [p.gx,p.gy,p.phase,p.frame,p.facing]

func path_to(p: RefCounted, goal: Vector2i) -> Dictionary:
	var nodes: Array = [{"p":p,"parent":-1,"action":{},"depth":0}]
	var seen := {key(p):true}
	var frontier: Array = [{"id":0,"rank":0.0}]
	var best := 0
	var distance: float = Vector2(p.gx,p.gy).distance_to(Vector2(goal))
	while not frontier.is_empty() and nodes.size() < 45000:
		var cursor: int = frontier.pop_back().id
		var current: RefCounted = nodes[cursor].p
		var d: float = Vector2(current.gx,current.gy).distance_to(Vector2(goal))
		if d < distance:
			distance = d
			best = cursor
		if d <= 2.2:
			break
		for action in CONTROLS:
			var next := copy(current)
			next.step(action.get("up",false),action.get("down",false),action.get("left",false),action.get("right",false))
			next.render_step()
			if next.gy >= next.height or next.gx < 0 or next.gx > next.width-3:
				continue
			var id := key(next)
			if seen.has(id):
				continue
			seen[id] = true
			var depth: int = nodes[cursor].depth + 1
			var rank: float = Vector2(next.gx,next.gy).distance_to(Vector2(goal)) + depth * 0.15
			var entry := {"id":nodes.size(),"rank":rank}
			var low := 0
			var high := frontier.size()
			while low < high:
				var middle := (low + high) / 2
				if frontier[middle].rank > rank:
					low = middle + 1
				else:
					high = middle
			frontier.insert(low,entry)
			nodes.append({"p":next,"parent":cursor,"action":action,"depth":depth})
	var end: RefCounted = nodes[best].p
	var actions: Array = []
	while best > 0:
		actions.push_front(nodes[best].action)
		best = nodes[best].parent
	return {"p":end,"actions":actions,"distance":distance,"searched":nodes.size()}

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var level := int(args[0])
	var p = Motion.new()
	p.configure(JSON.parse_string(FileAccess.get_file_as_string("res://data/wr1/level_%02d.json" % level)))
	# Let camera and standing animation settle, as in the native idle prefix.
	for i in range(20):
		p.step(false,false,false,false)
		p.render_step()
	var goals: Array = [Vector2i(56,36),Vector2i(26,30),Vector2i(6,32),Vector2i(25,17),Vector2i(73,26),Vector2i(75,14),Vector2i(108,30),Vector2i(110,34)] if level == 3 else [Vector2i(4,38),Vector2i(22,33),Vector2i(26,52),Vector2i(38,48),Vector2i(64,48),Vector2i(78,34),Vector2i(110,34),Vector2i(118,40),Vector2i(90,54),Vector2i(48,42)]
	var actions: Array = []
	var waypoints: Array = []
	var outward := goals.duplicate()
	var returning := goals.duplicate()
	returning.reverse()
	goals.append_array(returning)
	goals.append_array(outward)
	for goal in goals:
		var found := path_to(p, goal)
		actions.append_array(found.actions)
		p = found.p
		waypoints.append({"goal":[goal.x,goal.y],"reached":[p.gx,p.gy],"step":actions.size(),"distance":found.distance})
		print("Goal ",goal," reached ",Vector2i(p.gx,p.gy)," actions ",found.actions.size()," search ",found.searched)
	FileAccess.open(args[1],FileAccess.WRITE).store_string(JSON.stringify({"level":level,"scope":"Offline collision-only plan; no future native state input","actions":actions,"waypoints":waypoints},"  ")+"\n")
	quit()
