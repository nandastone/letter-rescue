extends RefCounted
## Original four views, replay bounds and interruptible robot speech tail.
const ScrAnimation = preload("res://scripts/animation.gd")
var host
var store
var view: int = 0
var actor
var tail_wait: bool = false
var sound_due: int = 0
var busy: bool:
	get:
		return actor!=null and (not actor.done or tail_wait)

func _init(game) -> void:
	host = game
	store = game.store

func enter() -> void:
	view = host.rewards.next_view()
	replay()

func replay() -> void:
	tail_wait = false
	if view<3:
		var id = [800,820,840][view]
		actor = host.animation("th",id,id)
	else:
		actor = ScrAnimation.new(store,"modules",3610,3600,host.tick)
		actor.origin = Vector2i(181,93)
		actor.sound_requested.connect(speak)
		sound_due = host.tick
		while actor.frame_updates==0 and not actor.done:
			actor.step(host.tick)
		tail_wait = host.rewards.shelf.any(func(value): return value)
		actor.done = not tail_wait

func speak(id: int) -> void:
	sound_due = host.tick+host.play_sound(id)

func interrupt() -> bool:
	if not busy:
		return false
	if actor.done and tail_wait:
		tail_wait = false
		host.audio.stop()
	return true

func update(tick: int) -> void:
	if actor==null:
		return
	if not actor.done:
		actor.update(tick)
		if actor.done and view<3:
			host.audio.stop()
	if actor.done and tail_wait and tick>=sound_due:
		tail_wait = false
		host.audio.stop()

func click(point: Vector2i) -> void:
	if interrupt():
		return
	var r = store.data.telescope.rectangles[view]
	if point.x<r[1] or point.x>=r[3] or point.y<r[0] or point.y>=r[2]:
		host.navigate_scene("inside")
	else:
		replay()

func draw(surface) -> void:
	surface.image.fill(Color.BLACK)
	var id = 781+2*view
	var shape = store.shape("th",id)
	surface.draw(store,"th",id,id-1,160-int(shape[0]/2),100-int(shape[1]/2),2,[34,77,168,243] if view==3 else [])
	if view==3:
		host.rewards.draw_shelf(surface)
	if actor!=null and (view==3 or not actor.done):
		actor.draw(surface)
	surface.draw(store,"th",8,6,304,1)

func dispose() -> void:
	actor = null
