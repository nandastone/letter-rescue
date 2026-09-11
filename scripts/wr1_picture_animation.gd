extends RefCounted
## DS:41a2/41b0; WR1.EXE ab25..ac27. Advances even when pictures are hidden.
var timers: Array[int] = [0,3,5,8,10,13,15]
var frames: Array[int] = [0,0,0,0,0,0,0]
var enabled: bool = true

func configure(initial: Dictionary) -> void:
	if not initial.is_empty():
		timers.assign(initial.picture_timers)
		frames.assign(initial.picture_frames)
		enabled = bool(initial.picture_animation_enabled)

func step() -> Array[int]:
	var changed: Array[int] = []
	if enabled:
		for i in range(7):
			timers[i] += 1
			if timers[i] > 7:
				timers[i] = 0
				frames[i] = 1 - frames[i]
				changed.append(i)
	return changed

func snapshot() -> Dictionary:
	return {"picture_timers":timers.duplicate(),"picture_frames":frames.duplicate(),"picture_animation_enabled":int(enabled)}
