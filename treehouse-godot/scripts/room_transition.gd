extends RefCounted
## Original ring/bubble SCR sequence and displayed backing callbacks.
var host
var variant: int
var returning: bool
var phase: String = "opening"
var child_visible: bool
var display_child: bool
var open_inlet: bool
var actor
var due: int
var sound_due: int
var done: bool = false
var hide_pointer: bool:
	get: return phase!="entry-pause"

func _init(game, which: int, reverse: bool) -> void:
	host = game
	variant = which
	returning = reverse
	child_visible = not returning
	display_child = child_visible
	open_inlet = returning and variant==3
	sound_due = host.tick
	host.play_sound(1015)
	play(980,980)

func play(id: int, palette: int) -> void:
	actor = host.ScrAnimation.new(host.store,"th",id,palette,host.tick)
	actor.sound_requested.connect(func(sound): sound_due=host.tick+host.play_sound(sound))
	actor.callback_requested.connect(func(slot,arg):
		if slot==0:
			child_visible = bool(arg))
	actor.displayed.connect(func(): display_child=child_visible)
	actor.update(host.tick)

func interrupt() -> void:
	if phase in ["sound-tail","board-pause","entry-pause"]:
		host.audio.stop()
		sound_due = host.tick
		due = host.tick

func update(tick: int) -> void:
	if phase=="entry-pause":
		done = tick>=due
		return
	if phase=="board-pause":
		if tick>=due:
			open_inlet = false
			if returning:
				done = true
			else:
				phase = "entry-pause"
				due = tick+60
		return
	if phase=="sound-tail":
		if tick>=sound_due:
			end_transfer()
		return
	actor.update(tick)
	if not actor.done:
		return
	if phase=="opening":
		if returning:
			host.audio.stop()
		if variant==3:
			open_inlet = true
		phase = "transfer"
		play(1100+variant+4*int(returning),1100)
	elif phase=="transfer":
		phase = "sound-tail"
		if tick>=sound_due:
			end_transfer()
	elif phase=="closing":
		actor = null
		phase = "board-pause"
		due = tick+(60 if variant==3 else 0)
		if variant!=3:
			done = true

func end_transfer() -> void:
	host.audio.stop()
	actor = null
	if returning:
		phase = "closing"
		play(981,980)
	else:
		phase = "board-pause" if variant==3 else "entry-pause"
		due = host.tick+60

func draw(surface) -> void:
	var transferring = phase in ["transfer","sound-tail"]
	host.draw_inside(false,not (transferring and variant==2))
	if open_inlet:
		surface.draw(host.store,"th",927,900,160,184)
	if phase in ["opening","closing"]:
		actor.draw(surface)
	elif phase!="board-pause" or not returning:
		surface.draw(host.store,"th",986,980,150,162)
	if display_child if actor!=null else child_visible:
		host.resident.draw(surface)
	if transferring:
		actor.draw(surface)
	var bounds = actor.script_data.bounds if transferring else [162,150,174,197]
	host.resident.draw_objects(surface,true,false,bounds,168 if transferring else 0)

func dispose() -> void:
	actor = null
