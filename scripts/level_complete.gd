extends Control

signal next_level_requested

func _ready() -> void:
	visible = false
	$VBoxContainer/NextButton.pressed.connect(_on_next)

func show_results(level_num: int, score: int, words_matched: int) -> void:
	visible = true
	$VBoxContainer/LevelLabel.text = "Level %d Complete!" % level_num
	$VBoxContainer/ScoreLabel.text = "Score: %d" % score
	$VBoxContainer/WordsLabel.text = "Words Rescued: %d" % words_matched

func _on_next() -> void:
	visible = false
	next_level_requested.emit()
