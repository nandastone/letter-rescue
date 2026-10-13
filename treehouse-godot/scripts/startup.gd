extends RefCounted
## Overlay 5 logo: three sequential SCR70 sparkles, cue-e reveal, sound + 60 ticks.
var host
var data: Dictionary
var start_tick: int
var phase: String = "sparkles"
var index: int = 0
var sparkle
var wipe_start: int = -1
var reveal: Image
var player: AudioStreamPlayer

func _init(game) -> void:
	host = game
	data = host.store.data.startup
	start_tick = host.tick
	var backing = host.Surface.new()
	draw_background(backing)
	backing.draw(host.store,"th64",62,60,int(data.wipe_bounds[1])+2,int(data.wipe_bounds[0]))
	reveal = backing.image
	player = AudioStreamPlayer.new()
	host.add_child(player)
	player.stream = load("res://data/title.wav")
	if host.audio_output_enabled and host.preferences.settings.sound:
		player.play()
	update(host.tick)

func irq_tick(irq: int) -> int:
	return start_tick+int(ceil(irq*float(data.pit_divisor)/float(data.pit_hz)*host.TICK_HZ))

func cue_tick(value: int) -> int:
	for cue in data.cues:
		if int(cue.value)==value:
			return irq_tick(int(cue.irq))
	assert(false,"Missing original title cue")
	return start_tick

func update(tick: int) -> void:
	if phase=="done":
		return
	if sparkle!=null:
		sparkle.update(tick)
		if sparkle.done:
			sparkle = null
			index += 1
	if phase=="sparkles" and sparkle==null:
		if index<3 and tick>=cue_tick(97+index):
			sparkle = host.animation("th",70,70)
			var bounds = sparkle.script_data.bounds
			# Original wrapper receives bottom/center, not a top-left position.
			sparkle.origin = Vector2i(int(data.sparkles[index][0])-int((bounds[3]-bounds[1])/2),int(data.sparkles[index][1])-int(bounds[2]-bounds[0]))
		elif index==3:
			phase = "cue"
	if phase=="cue" and tick>=cue_tick(101):
		phase = "wipe"
		wipe_start = tick
	if phase=="wipe":
		var columns = int(data.wipe_bounds[3])-int(data.wipe_bounds[1])
		if (tick-wipe_start+1)*2>=columns:
			phase = "wait"
	if phase=="wait" and tick>=irq_tick(int(data.end_irq))+60:
		finish()

func finish() -> void:
	if phase=="done":
		return
	phase = "done"
	dispose()
	host.select_screen()

func draw_background(surface) -> void:
	surface.image.fill(Color.BLACK)
	surface.draw(host.store,"th64",61,60,int(data.origin[0]),int(data.origin[1]),0)

func draw(surface) -> void:
	draw_background(surface)
	if sparkle!=null:
		sparkle.draw(surface)
	if wipe_start>=0:
		var bounds = data.wipe_bounds
		var width = mini(int(bounds[3])-int(bounds[1]),(host.tick-wipe_start+1)*2)
		var region = Rect2i(int(bounds[1]),int(bounds[0]),width,int(bounds[2])-int(bounds[0]))
		surface.image.blit_rect(reveal,region,region.position)

func dispose() -> void:
	if sparkle!=null:
		sparkle = null
	if is_instance_valid(player):
		player.stop()
		player.stream = null
		player.queue_free()
		player = null
