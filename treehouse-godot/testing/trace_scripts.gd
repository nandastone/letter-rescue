extends SceneTree
const Resources = preload("res://scripts/resources.gd")
const ScrAnimation = preload("res://scripts/animation.gd")
var events: Array = []
var current_tick: int = 0

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var store = Resources.new()
	var results: Dictionary = {}
	for key in store.data.scripts:
		var pieces = key.split(":")
		var animation = ScrAnimation.new(store,pieces[0],int(pieces[1]),0)
		events = []
		animation.sound_requested.connect(func(id): events.append([current_tick,"sound",id]))
		animation.callback_requested.connect(func(slot,arg): events.append([current_tick,"callback",slot,arg]))
		animation.displayed.connect(func():
			var row = [current_tick,"display"]
			for slot in animation.display:
				for field in ["shape","first","end","flags","x","y","vx","vy","ax","ay","sc","mc"]:
					row.append(slot[field])
			events.append(row))
		for value in 10001:
			current_tick = value
			animation.update(value)
			if animation.done:
				break
		results[key] = {"events":events,"done":animation.done,"tick":current_tick,"pc":animation.pc}
	var file = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	file.store_string(JSON.stringify(results))
	file.close()
	quit()
