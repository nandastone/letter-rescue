extends Node2D

# One of a level's seven word/picture slots. word_manager.gd drives its state
# from the original matching model.

enum State { IDLE, SHOWING_WORD, SHOWING_PICTURE, MATCHED }

var state: State = State.IDLE
var word: String = ""
var picture_texture: Texture2D = null
var block_index: int = 0
var original_word_sprite: Sprite2D
var original_picture_frames: Array[Texture2D] = []

func set_original_picture(picture_word: String) -> void:
	picture_texture = preload("res://scripts/wr1_pictures.gd").load_picture(picture_word)
	original_picture_frames.assign([picture_texture, preload("res://scripts/wr1_pictures.gd").load_picture(picture_word, 1)])
	$PictureSprite.centered = false
	$PictureSprite.position = Vector2.ZERO
	var card := Image.create(72, 18, false, Image.FORMAT_RGBA8)
	card.fill(Color.BLACK)
	card.fill_rect(Rect2i(2, 1, 69, 15), Color.WHITE)
	preload("res://scripts/wr1_text.gd").draw(card, word.to_lower(), Vector2i(32 - 4 * word.length(), 4), Color.BLACK, Color.WHITE)
	if original_word_sprite == null:
		original_word_sprite = Sprite2D.new()
		original_word_sprite.centered = false
		original_word_sprite.z_index = 2
		add_child(original_word_sprite)
	original_word_sprite.texture = ImageTexture.create_from_image(card)
	original_word_sprite.hide()
	preload("res://scripts/wr1_clear_text.gd").sprite_text(original_word_sprite, card, [
		{"erase":Rect2(2,1,69,15), "rect":Rect2(2,1,69,15), "text":word.to_lower(), "background":Color.WHITE, "pixels":12, "baseline_adjustment":0.75}])
	if preload("res://scripts/wr1_clear_text.gd").enabled():
		var question: Image = $Sprite2D.texture.get_image()
		question.convert(Image.FORMAT_RGBA8)
		preload("res://scripts/wr1_clear_text.gd").sprite_text($Sprite2D, question, [
			{"erase":Rect2(6,4,13,15), "rect":Rect2(5,3,15,17), "text":"?", "background":Color.WHITE, "pixels":14}])

func set_original_picture_frame(frame: int) -> void:
	if original_picture_frames.size() == 2:
		picture_texture = original_picture_frames[frame]
		$PictureSprite.texture = picture_texture

func _ready() -> void:
	update_visual()

func setup(word_text: String, index: int) -> void:
	word = word_text
	block_index = index
	state = State.IDLE
	update_visual()

func update_visual() -> void:
	if original_word_sprite != null:
		original_word_sprite.hide()
	$Sprite2D.visible = state == State.IDLE or (state == State.SHOWING_PICTURE and picture_texture == null)
	$PictureSprite.visible = state == State.SHOWING_PICTURE and picture_texture != null
	if $PictureSprite.visible:
		$PictureSprite.texture = picture_texture
	if state == State.IDLE:
		$Sprite2D.modulate = Color.WHITE
	if state == State.SHOWING_WORD and original_word_sprite != null:
		original_word_sprite.show()
	if original_word_sprite != null:
		preload("res://scripts/wr1_clear_text.gd").sync_sprite(original_word_sprite)
	preload("res://scripts/wr1_clear_text.gd").sync_sprite($Sprite2D)
