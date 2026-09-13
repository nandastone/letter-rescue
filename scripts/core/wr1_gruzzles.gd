extends RefCounted
## WR1.EXE 50e8..585c (actions/movement), ba38..bf50 (render updates).
## Coordinates are raw 8px cells. Rendering deliberately mutates animation state.

const HEIGHTS := [3, 3, 4, 3]
const WALK := [0, 0, 1, 1, 2, 2, 3, 3, 2, 2, 1, 1]
const SLIME := [0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 6, 6, 6, 6]
var actors: Array = []
var inactive_actors: Array = [] # Native actor slots persist when difficulty hides them.
# DOS compacts every actor array except this one: cadence belongs to the slot.
var timers: Array[int] = []
var rng: int = 1
var demo_mode: bool = false
var difficulty: int = 14
var cadence: int = 6
var entity_timer: int = 0
var slime_used: int = 0
var slime_ever_used: bool = false
var action_busy: bool = false
var death: bool = false
var slime_request: bool = false
var draws: Array = []
var render_page: int = 0
var miss_timer: int = 0
var miss_grid := Vector2i.ZERO
var last_reward_grid := Vector2i.ZERO

func random_word() -> int:
	rng = (rng * 0x015a4e35 + 1) & 0xffffffff
	return (rng >> 16) & 0x7fff

func _reset(mode: int) -> void:
	actors.clear()
	# Initialized data at DS:0f40, including the currently inactive slots.
	timers.assign([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
	difficulty = [14, 6, 2][mode]
	cadence = [6, 2, 1][mode]
	rng = 1
	entity_timer = 0
	slime_used = 0
	slime_ever_used = false
	action_busy = false
	death = false
	slime_request = false
	draws.clear()
	render_page = 0
	miss_timer = 0
	miss_grid = Vector2i.ZERO

func start(positions: Array, mode: int, seed_value: int, select_words: Callable) -> Dictionary:
	_reset(mode)
	rng = seed_value & 0xffff
	# A02B prepares the first level on default Easy before the menu. The
	# difficulty selector calls 8841 afterward, changing count without rerolling
	# mystery/types. Keep all map actors temporarily so Hard can expose them.
	# Hard and Easy consume the same load RNG; only their active counts differ.
	var initial := restart(positions, 2, true, select_words)
	inactive_actors = actors.duplicate(true)
	var count: int = positions.size()
	if mode == 0:
		count = 1
	elif mode == 1:
		count = 2 + random_word() % 2
	actors.resize(mini(count, positions.size()))
	return initial

func configure(positions: Array, mode: int, initial: Dictionary = {}) -> void:
	_reset(mode)
	# Preserve older replay defaults; measured replays restore their checkpoint.
	# Fresh live sessions use start() and the recovered complete load sequence.
	var count: int = 1
	if mode == 1:
		count = 2 + random_word() % 2
	elif mode == 2:
		count = positions.size()
	for i in range(mini(positions.size(), count)):
		actors.append(_actor(int(positions[i][0]), int(positions[i][1]), random_word() % 4, -1))
	if not initial.is_empty():
		rng = int(initial.rng)
		difficulty = int(initial.gruzzle_difficulty)
		cadence = int(initial.gruzzle_cadence)
		entity_timer = int(initial.get("entity_timer", 0))
		slime_used = int(initial.get("slime_used", 0))
		slime_ever_used = bool(initial.get("slime_ever_used", slime_used > 0))
		render_page = int(initial.get("render_page", 0))
		miss_timer = int(initial.get("miss_timer", 0))
		miss_grid = Vector2i(int(initial.get("miss_x", 0)), int(initial.get("miss_y", 0)))
		actors = initial.gruzzles.duplicate(true)
		if initial.has("gruzzle_move_timers"):
			timers.assign(initial.gruzzle_move_timers)
		for i in range(actors.size()):
			timers[i] = int(actors[i].move_timer)
			actors[i].erase("move_timer")

func present_checkpoint(p: RefCounted) -> void:
	# Completed native state stores the animation index for the NEXT render.
	# Drawing this initial frame must not advance the simulation or video page.
	draws.clear()
	for a in actors:
		if a.state == -1 and visible_in(a, p):
			draws.append({"kind":"gruzzle", "type":a.type,
				"frame":WALK[posmod(a.animation_index-1, WALK.size())],
				"position":Vector2i(a.gx*8, a.gy*8-23)})

func _actor(gx: int, gy: int, kind: int, state: int) -> Dictionary:
	return {"gx": gx, "gy": gy, "type": kind, "state": state,
		"animation_index": 0, "jump_phase": -1}

func spawn(grid: Vector2i) -> void:
	if actors.size() == 10:
		actors.pop_back()
	# C4AE..C4C8: demo spawns use the slot and consume no random number.
	var kind: int = actors.size() % 4 if demo_mode else random_word() % 4
	actors.append(_actor(grid.x, grid.y, kind, 64))

func refill(mode: int) -> void:
	slime_used = maxi(0, slime_used - [5, 3, 2][mode])

## Default game's hidden shotgun. The legacy game never calls this, so its
## actor timing, RNG and rendering remain untouched.
func berserker_blast(p: RefCounted, range_cells: int = 34) -> Array[Dictionary]:
	var hits: Array[Dictionary] = []
	var direction: int = -1 if p.facing == 1 else 1
	for i in range(actors.size() - 1, -1, -1):
		var actor: Dictionary = actors[i]
		var forward: int = (int(actor.gx) - p.gx) * direction
		if actor.state != -1 or forward < -1 or forward > range_cells or absi(int(actor.gy) - p.gy) > 7:
			continue
		var at := Vector2(int(actor.gx) * 8, int(actor.gy) * 8 - 23)
		hits.append({"position": at, "type": int(actor.type), "frame": WALK[actor.animation_index]})
		# Remove the cached draw immediately; no ghost waiting for the next tick.
		draws = draws.filter(func(draw: Dictionary) -> bool: return not (draw.kind == "gruzzle" and Vector2(draw.position) == at))
		actors.remove_at(i)
		# Match the engine's actor removal: cadence counters belong to the ten
		# fixed slots and are deliberately not compacted with the actor array.
	# The end-of-level slime-free bonus should not reward a weapon cheat.
	if not hits.is_empty():
		slime_ever_used = true
	return hits

func restart(positions: Array, mode: int, fresh_level: bool = false, select_words: Callable = Callable()) -> Dictionary:
	slime_ever_used = false
	# 4eb5: rotations; 70b1 -> 730a: mystery selection; 5060: all ten
	# actor slots. Inactive slots consume RNG too, but keep their timers.
	var words: int = random_word() % 6 + 1
	var pictures: int = words
	while pictures == words:
		pictures = random_word() % 7
	if fresh_level:
		if select_words.is_valid():
			select_words.call(random_word)
		# 6648..66aa assigns every map spawn a type while decoding a new
		# level. Reset later overwrites those types, but the RNG calls remain.
		for unused in positions:
			random_word()
	var count: int = 1
	if mode == 1:
		count = 2 + random_word() % 2
	elif mode == 2:
		count = positions.size()
	var mystery: int = random_word() % 7
	actors.clear()
	inactive_actors.clear()
	for i in range(10):
		var kind: int = random_word() % 4
		if i < positions.size():
			inactive_actors.append(_actor(int(positions[i][0]), int(positions[i][1]), kind, -1))
		if i < mini(count, positions.size()):
			actors.append(_actor(int(positions[i][0]), int(positions[i][1]), kind, -1))
	slime_used = maxi(0, slime_used - [5, 2, 0][mode])
	death = false
	slime_request = false
	miss_timer = 0
	draws.clear()
	return {"word_offset": words, "picture_offset": pictures, "mystery_index": mystery}

func change_difficulty(mode: int) -> void:
	for i in range(mini(actors.size(),inactive_actors.size())):
		inactive_actors[i] = actors[i].duplicate(true)
	difficulty = [14,6,2][mode]
	cadence = [6,2,1][mode]
	var count: int = 1 if mode == 0 else (2 + random_word() % 2 if mode == 1 else inactive_actors.size())
	actors = inactive_actors.slice(0,mini(count,inactive_actors.size())).duplicate(true)

func visible_in(a: Dictionary, p: RefCounted) -> bool:
	return a.gx > p.camera_x - 2 and a.gx < p.camera_x + 35 and a.gy > p.camera_y - 2 and a.gy <= p.camera_y + 19

func _slime(p: RefCounted) -> void:
	if not slime_request:
		return
	slime_request = false
	if entity_timer < 8 or action_busy:
		return
	entity_timer = 0
	p.frame = 21 if p.facing == 1 else 11
	# Scan columns toward the screen edge, then rows top-to-bottom, then slots.
	# Vertical proximity and line of sight are not conditions in this routine.
	var direction: int = -1 if p.facing == 1 else 1
	var end: int = p.camera_x - 1 if direction == -1 else p.camera_x + 37
	for col in range(p.gx, end, direction):
		for row in range(p.camera_y, p.camera_y + 21):
			for a in actors:
				if a.state == -1 and a.gx == col and a.gy == row:
					if slime_used < 5:
						a.state = 0
						a.animation_index = 0
						slime_used += 1
						slime_ever_used = true
					else:
						miss_timer = 10
						miss_grid = Vector2i(a.gx, a.gy)
					return
	miss_timer = 10
	miss_grid = Vector2i(p.gx - p.facing * 6, p.gy - 2)

func step(p: RefCounted, hazards: Callable = Callable()) -> void:
	entity_timer = _word(entity_timer + 1)
	if demo_mode:
		# 50F4..5105 reseeds on every entity update, after contacts, before slime.
		rng = 200
	_slime(p)
	if hazards.is_valid():
		hazards.call()
	var i := 0
	while i < actors.size():
		var a: Dictionary = actors[i]
		timers[i] = _word(timers[i] + 1)
		if a.state > 34:
			a.state -= 1
			if a.state <= 34:
				a.state = -1
			else:
				i += 1
				continue
		if not visible_in(a, p):
			if a.state == 24:
				actors.remove_at(i)
			else:
				i += 1
			continue
		if timers[i] > cadence:
			if a.state == -1:
				timers[i] = 0
				var old_x: int = a.gx
				var direction: int = -1 if a.gx > p.gx else 1
				# Easy's divisor is negative (-2); remainder zero is still exact.
				if random_word() % (12 - difficulty) == 0:
					direction = random_word() % 3 - 1
				a.gx = clampi(a.gx + direction, 4, p.width - 7)
				for row in range(a.gy - HEIGHTS[a.type], a.gy):
					for col in range(a.gx - 1, a.gx + 5):
						if p.attr(col, row) == 0x73:
							a.gx = old_x
							break
			else:
				a.jump_phase = -1
		if a.jump_phase > -1:
			a.gy -= 1
			a.jump_phase += 1
			if a.jump_phase >= 9:
				a.jump_phase = -1
			for col in range(a.gx - 1, a.gx + 3):
				if p.attr(col, a.gy - HEIGHTS[a.type]) == 0x73:
					a.jump_phase = -1
					a.gy += 1
					break
		else:
			var falling := true
			for col in range(a.gx - 1, a.gx + 3):
				var attr: int = p.attr(col, a.gy)
				var supported := attr == 0x73
				if attr == 0x74:
					# Consume RNG before testing player height/state, as the EXE does.
					supported = random_word() % 4 != 0 or p.gy < a.gy + 3 or a.state != -1
				if supported:
					falling = false
					if a.gy > p.gy and a.state == -1 and random_word() % (difficulty * 8) == 0:
						a.jump_phase = 0
					break
			if falling:
				a.gy += 1
			if a.gy > p.height - 1:
				actors.remove_at(i)
				continue
		if a.state == -1 and a.gx > p.gx - 2 and a.gx <= p.gx + 3 and a.gy <= p.gy + 1 and a.gy > p.gy - 4:
			death = true
		i += 1

func render_step(p: RefCounted) -> int:
	draws.clear()
	render_page = 1 - render_page
	for a in actors:
		if a.state == 24 or not visible_in(a, p):
			continue
		if a.state < 24:
			draws.append({"kind": "gruzzle", "type": a.type, "frame": WALK[a.animation_index],
				"position": Vector2(a.gx * 8, a.gy * 8 - 23)})
		elif render_page == 0:
			# Spawn blink draws only the AND mask on alternate render pages.
			draws.append({"kind": "gruzzle", "type": a.type, "frame": WALK[a.animation_index],
				"position": Vector2(a.gx * 8, a.gy * 8 - 23), "mask": true})
		if a.state == -1:
			a.animation_index = (int(a.animation_index) + 1) % 12
	action_busy = false
	var reward := 0
	for a in actors:
		if a.state < 0 or a.state > 24:
			continue
		if a.state < 24 and not death:
			action_busy = true
			var screen := Vector2(a.gx * 8 + 16 - p.camera_x * 8, a.gy * 8 - 55 - p.camera_y * 8)
			if screen.x >= 0 and screen.x < 288 and screen.y >= 0 and screen.y < 104:
				draws.append({"kind": "slime", "frame": SLIME[a.state], "position": Vector2(a.gx * 8, a.gy * 8 - 87)})
			a.state += 1
			if a.state == 24:
				reward += 10
				last_reward_grid = Vector2i(a.gx, a.gy - 5)
		else:
			draws.append({"kind": "slime", "frame": 7, "position": Vector2(a.gx * 8, a.gy * 8 - 23)})
	if miss_timer > 0:
		miss_timer -= 1
		var screen := Vector2(miss_grid.x * 8 + 16 - p.camera_x * 8, (miss_grid.y - p.camera_y - 8) * 8 + 33)
		if screen.x >= 0 and screen.x < 288 and screen.y >= 0 and screen.y < 104:
			draws.append({"kind": "slime", "frame": 8, "position": Vector2(miss_grid.x * 8, miss_grid.y * 8 - 63)})
	return reward

func snapshot() -> Dictionary:
	var result := actors.duplicate(true)
	for i in range(result.size()):
		result[i]["move_timer"] = timers[i]
	return {"gruzzles": result, "gruzzle_count": actors.size(), "gruzzle_move_timers":timers.duplicate(), "rng": rng,
		"entity_timer": entity_timer, "slime_used": slime_used, "action_busy": int(action_busy), "death": int(death),
		"miss_timer": miss_timer, "miss_x": miss_grid.x, "miss_y": miss_grid.y}

func _word(value: int) -> int:
	return ((value + 32768) & 0xffff) - 32768
