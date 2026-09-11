extends Node
## Records where the player is drawn on each rendered frame. Runs after every
## other _process callback, so it sees the final drawn position of the frame.
signal done(rows: Array)

var rows: Array = []
var frames: int

func _process(_delta: float) -> void:
	var game := get_parent()
	if game.player.original_sprite == null:
		return
	# Deaths, rescues, recaps and the exit walk run their own sequences, which
	# the smoothing leaves alone; flag them so the gate can skip those frames.
	var player := game.player
	var sequence: bool = player.is_dead or player.original_rescue != null or player.original_recap != null or player.original_exit != null
	rows.append([game.player.original_state.ticks,
		game.player.position.x + game.player.original_sprite.offset.x,
		game.player.position.y + game.player.original_sprite.offset.y, sequence])
	if rows.size() >= frames:
		done.emit(rows)
