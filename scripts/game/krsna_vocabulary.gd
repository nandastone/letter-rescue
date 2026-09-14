extends RefCounted
## First Letter Rescue vocabulary expansion. Source words remain untouched so
## native profiles, seeded starts, demos and Legacy continue to behave as WR1.

const REPLACEMENTS := {
	"toe": "cow",
	"bell": "calf",
	"wine": "milk",
	"sign": "gopi",
	"watch": "flute",
	"money": "radha",
	"clown": "lotus",
	"fence": "krsna",
	"bottle": "butter",
	"nurse": "altar",
	"factory": "peacock",
	"balloon": "garland",
	"gun": "boy",
	"ghost": "conch",
	"scale": "beads",
	"teepee": "tulsi",
	"camera": "kirtan",
}

const PICTURE_WORDS: Array[String] = [
	"cow", "calf", "milk", "gopi", "flute", "radha",
	"lotus", "krsna", "butter", "altar", "peacock", "garland",
	"boy", "conch", "beads", "tulsi",
	"pot", "crown", "kirtan",
]

const PICTURE_SIZE := 24
const FRAME_COUNT := 2
const ANIMATED_WORDS: Array[String] = ["cow", "calf", "altar", "peacock", "garland", "kirtan"]
const ATLAS_PATH := "res://assets/sprites/krsna_words.png"


static func display_word(original_word: String) -> String:
	return REPLACEMENTS.get(original_word.to_lower(), original_word.to_lower())


static func load_picture(word: String, frame: int = 0) -> Texture2D:
	var index := PICTURE_WORDS.find(word.to_lower())
	if index < 0 or not ResourceLoader.exists(ATLAS_PATH):
		return null
	var texture := AtlasTexture.new()
	texture.atlas = load(ATLAS_PATH)
	texture.region = Rect2((index * FRAME_COUNT + posmod(frame, FRAME_COUNT)) * PICTURE_SIZE, 0, PICTURE_SIZE, PICTURE_SIZE)
	return texture
