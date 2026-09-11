extends RefCounted
## DS:014c..0150/0160. WR1.EXE bfc0..c10c draws then decrements.
var ticks: int = 0
var grid := Vector2i.ZERO
var amount: int = 0
var bonus: int = 0

func start(value: int, at: Vector2i, bonus_kind: int = 0) -> void:
	ticks = 20
	grid = at
	amount = value
	bonus = bonus_kind

func render_step(p: RefCounted, page: int) -> Dictionary:
	if ticks == 0:
		return {}
	if grid.x < p.camera_x or grid.x > p.camera_x + 36 or grid.y < p.camera_y or grid.y > p.camera_y + 19:
		ticks = 0
		return {}
	var draw := {"text":str(amount),"position":Vector2i(grid.x * 8,grid.y * 8 + ticks),
		"color":Color8(255,85,255) if page == 0 else Color8(255,255,85)}
	if bonus in [1,3] and grid.x - 3 >= p.camera_x and grid.x + 3 <= p.camera_x + 36:
		draw["caption"] = "Bonus #%d" % bonus
	ticks -= 1
	return draw

func snapshot() -> Dictionary:
	return {"reward_timer":ticks,"reward_x":grid.x,"reward_y":grid.y,"reward_bonus":bonus}
