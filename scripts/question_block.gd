extends Area2D

enum State { IDLE, SHOWING_WORD, SHOWING_PICTURE, MATCHED }

var state: State = State.IDLE
var word: String = ""
var picture_texture: Texture2D = null
var block_index: int = 0

signal block_touched(block: Area2D)

func _ready() -> void:
	body_entered.connect(_on_body_entered)
	update_visual()

func setup(word_text: String, index: int) -> void:
	word = word_text
	block_index = index
	state = State.IDLE

	# Load word picture if available.
	var pic_path := "res://assets/pictures/%s.png" % word.to_lower()
	if ResourceLoader.exists(pic_path):
		picture_texture = load(pic_path)

	update_visual()

func _on_body_entered(body: Node2D) -> void:
	if body is CharacterBody2D and body.has_method("die") and state != State.MATCHED:
		block_touched.emit(self)

func show_word() -> void:
	state = State.SHOWING_WORD
	update_visual()

func show_picture() -> void:
	if state == State.MATCHED:
		return
	state = State.SHOWING_PICTURE
	update_visual()

func reset_to_idle() -> void:
	if state == State.MATCHED:
		return
	state = State.IDLE
	update_visual()

func mark_matched() -> void:
	state = State.MATCHED
	update_visual()

func update_visual() -> void:
	match state:
		State.IDLE:
			$Sprite2D.modulate = Color.WHITE
			$Sprite2D.visible = true
			$Label.visible = false
			if has_node("PictureSprite"):
				$PictureSprite.visible = false
		State.SHOWING_WORD:
			$Sprite2D.visible = false
			$Label.text = word.to_upper()
			$Label.visible = true
			$Label.modulate = Color.WHITE
			if has_node("PictureSprite"):
				$PictureSprite.visible = false
		State.SHOWING_PICTURE:
			$Label.visible = false
			$Sprite2D.visible = false
			if picture_texture and has_node("PictureSprite"):
				$PictureSprite.texture = picture_texture
				$PictureSprite.visible = true
			else:
				$Sprite2D.visible = true
				$Label.text = word.to_upper()
				$Label.visible = true
				$Label.modulate = Color.WHITE
		State.MATCHED:
			$Label.visible = false
			$Sprite2D.visible = false
			if has_node("PictureSprite"):
				$PictureSprite.visible = false
