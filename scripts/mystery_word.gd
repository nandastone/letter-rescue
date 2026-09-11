extends Node

# The level's mystery word and how many of its letters have been collected.
# Collection itself runs in wr1_letters.gd at the original logical update.

var word: String = ""
var next_index: int = 0

func setup(mystery: String) -> void:
	word = mystery.to_upper()
	next_index = 0
