extends Node

var word: String = ""
var next_index: int = 0

signal letter_collected(letter: String, index: int)
signal word_completed(word: String)

func setup(mystery: String) -> void:
	word = mystery.to_upper()
	next_index = 0

func try_collect(letter: String) -> bool:
	var upper_letter := letter.to_upper()
	if next_index >= word.length():
		return false
	# Must collect in left-to-right spelling order.
	if upper_letter == word[next_index]:
		letter_collected.emit(upper_letter, next_index)
		next_index += 1
		if next_index >= word.length():
			word_completed.emit(word)
		return true
	return false

func is_complete() -> bool:
	return next_index >= word.length()
