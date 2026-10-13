extends RefCounted
## Original 94x47 backing and two-pixel constrained drawing cursor.
signal changed
signal returned
var bitmap: Image = Image.create(94,47,false,Image.FORMAT_RGBA8)
var colors: Array = []
var tool: int = -1
var previous = null
var returned_color = null

func _init(store) -> void:
	bitmap.fill(Color.BLACK)
	for index in [5,62,37,3,44,11,0]:
		var rgb = store.palette("th64",4).colors[index]
		colors.append(Color8(int(rgb[0]),int(rgb[1]),int(rgb[2])))

func select(value: int) -> void:
	end()
	tool = value
	returned_color = null
	changed.emit()

func begin(point: Vector2i) -> bool:
	if tool < 0:
		return false
	previous = null
	move(point,true)
	return true

func move(point: Vector2i, held: bool = false) -> Vector2i:
	returned_color = null
	if not Rect2i(52,40,105,57).has_point(point):
		end()
		if tool >= 0:
			returned_color = Color.WHITE if tool==6 else colors[tool]
			tool = -1
			returned.emit()
			changed.emit()
		return point
	if tool < 0 or not held:
		previous = null
		return point
	if previous != null and tool < 6:
		point.x = clampi(point.x,previous.x-2,previous.x+2)
		point.y = clampi(point.y,previous.y-2,previous.y+2)
	var eraser = tool==6
	var area = Rect2i(point-Vector2i(60,45)+Vector2i(1,1) if eraser else point-Vector2i(61,46),Vector2i(6,10) if eraser else Vector2i(2,2))
	bitmap.fill_rect(area.intersection(Rect2i(0,0,94,47)),colors[tool])
	previous = point
	return point

func end() -> void:
	previous = null

func clear() -> void:
	end()
	bitmap.fill(Color.BLACK)
	changed.emit()

func draw(surface) -> void:
	surface.blit(bitmap,60,45,false)

func draw_tray(surface) -> void:
	if tool >= 0:
		var x = 63+12*tool
		var width = 14 if tool==6 else 10
		surface.rect(x,92,width,1,Color.BLACK)
		surface.rect(x,93,width,2,Color8(105,105,105))
