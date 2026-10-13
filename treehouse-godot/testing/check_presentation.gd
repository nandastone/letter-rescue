extends SceneTree
const Presentation = preload("res://scripts/presentation.gd")
var checks: Array = []

func check(value: bool, name: String) -> void:
	checks.append({"name":name,"passed":value})

func _initialize() -> void:
	var old = Image.create(2,4,false,Image.FORMAT_RGBA8)
	old.fill(Color.RED)
	var next = old.duplicate()
	next.fill(Color.BLUE)
	var p = Presentation.new(1,5,4)
	p.commit(0,old)
	old.fill(Color.GREEN)
	p.commit(2.5,next)
	next.fill(Color.GREEN)
	p.advance_to(4)
	check(p.count==1,"one complete frame after four reads")
	check(p.image.get_pixel(0,0)==Color.RED and p.image.get_pixel(0,1)==Color.RED and p.image.get_pixel(0,2)==Color.BLUE and p.image.get_pixel(0,3)==Color.BLUE,"scanout mixes commit snapshots at band boundaries")
	var retained = p.image
	p.advance_to(9)
	check(p.count==2 and p.image.get_pixel(0,0)==Color.BLUE,"next complete frame uses latest source")
	check(retained.get_pixel(0,0)==Color.RED,"published frames retain their own pixels")
	old.fill(Color.RED)
	next.fill(Color.BLUE)
	p.reset(10,old)
	p.commit(11,next)
	p.advance_to(14)
	check(p.image.get_pixel(0,0)==Color.BLUE,"commit at a read boundary precedes that read")
	check(p.count==1,"reset starts an independent presentation clock")
	var passed = checks.all(func(c): return c.passed)
	var f = FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":passed,"checks":checks,"scope":"Synthetic scanout ownership and clock boundaries, not game or native timing evidence."},"\t"))
	f.close()
	quit(0 if passed else 1)
