extends RefCounted
var host
var returning: bool
var phase: String
var start: int
var frame: int = 0
var actor = null
var done: bool = false
var hide_pointer: bool:
	get: return phase=="bucket"

func _init(game, back: bool) -> void:
	host = game
	returning = back
	phase = "bucket" if back else "cloud"
	begin()

func begin() -> void:
	start = host.tick
	if phase=="cloud":
		frame = 0
		host.play_sound(10034)
	else:
		actor = host.ScrAnimation.new(host.store,host.character,20300+int(returning),20300,host.tick)
		actor.update(host.tick)

func interrupt() -> void:
	pass

func update(tick: int) -> void:
	if phase=="cloud":
		frame = int((tick-start)/8)
		if frame<8:
			return
	else:
		actor.update(tick)
		if not actor.done:
			return
	if phase==("cloud" if returning else "bucket"):
		done = true
		return
	phase = "cloud" if returning else "bucket"
	begin()

func draw(surface) -> void:
	var visible = phase=="cloud" and (frame>=4 if returning else frame<4)
	host.music.draw(surface,visible)
	if phase=="bucket":
		actor.draw(surface)
	else:
		if returning and frame<4:
			actor.draw(surface)
		var point = host.store.data.music.maze_cloud_positions[frame]
		surface.draw(host.store,"modules",2381+frame,2380,int(point[1]),int(point[0]))

func dispose() -> void:
	actor = null
