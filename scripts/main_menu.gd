extends Control

func _ready() -> void:
	if "--original-rules" in LaunchArgs.user_args() and InputReplay.mode != InputReplay.Mode.REPLAYING:
		$Background.hide()
		$VBoxContainer.hide()
		var frontend := preload("res://scripts/wr1_frontend.gd").new()
		add_child(frontend)
		frontend.begin()
		return
	$VBoxContainer/PlayButton.pressed.connect(_on_play)
	$VBoxContainer/DifficultyButton.pressed.connect(_on_cycle_difficulty)
	_update_difficulty_label()
	_update_high_score()

func _on_play() -> void:
	GameManager.restart_game()
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_cycle_difficulty() -> void:
	match GameManager.current_difficulty:
		GameManager.Difficulty.EASY:
			GameManager.current_difficulty = GameManager.Difficulty.MEDIUM
		GameManager.Difficulty.MEDIUM:
			GameManager.current_difficulty = GameManager.Difficulty.HARD
		GameManager.Difficulty.HARD:
			GameManager.current_difficulty = GameManager.Difficulty.EASY
	_update_difficulty_label()

func _update_difficulty_label() -> void:
	var names := {
		GameManager.Difficulty.EASY: "Easy (Ages 4-7)",
		GameManager.Difficulty.MEDIUM: "Medium (Ages 7-10)",
		GameManager.Difficulty.HARD: "Hard (Ages 10+)",
	}
	$VBoxContainer/DifficultyButton.text = "Difficulty: %s" % names[GameManager.current_difficulty]

func _update_high_score() -> void:
	if GameManager.high_score > 0:
		$VBoxContainer/HighScore.text = "High Score: %d" % GameManager.high_score
		$VBoxContainer/HighScore.visible = true
	else:
		$VBoxContainer/HighScore.visible = false

	var completed := GameManager.levels_completed.size()
	if completed > 0:
		$VBoxContainer/Progress.text = "%d/15 Levels Complete" % completed
		$VBoxContainer/Progress.visible = true
	else:
		$VBoxContainer/Progress.visible = false
