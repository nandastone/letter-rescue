extends Node

var slime_count: int = 5
var max_slime: int = 10

signal slime_used(remaining: int)
signal slime_collected(remaining: int)
signal slime_empty

func reset(starting_slime: int = 5) -> void:
	slime_count = starting_slime

func has_slime() -> bool:
	return slime_count > 0

func use_slime() -> bool:
	if slime_count <= 0:
		slime_empty.emit()
		return false
	slime_count -= 1
	slime_used.emit(slime_count)
	return true

func add_slime(amount: int = -1) -> void:
	# -1 means use difficulty-based refill.
	if amount < 0:
		amount = GameManager.get_slime_refill()
	slime_count = min(slime_count + amount, max_slime)
	slime_collected.emit(slime_count)

func refill() -> void:
	slime_count = max_slime
	slime_collected.emit(slime_count)
