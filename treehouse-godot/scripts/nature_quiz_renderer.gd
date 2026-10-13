extends "res://scripts/nature_renderer.gd"

func draw(target) -> void:
	surface = target
	var n = owner_ref.get_ref()
	var q = n.quiz
	var shown = q.player if q.display_player==null else q.display_player
	var r = tables.quiz_rectangles
	draw_shape(5402,5400,0,0,2)
	for i in 8:
		center(5651+i,r[1+i],5650,color(5650,2))
	draw_shape(5609,5600,171,3)
	for i in 2:
		if q.phase=="won" and ((q.revealed&(1<<i)) or i==q.other_reveal):
			continue
		var b = tables.reveal_rectangles[i]
		draw_shape(5601,5600,b[1]+1,b[0])
	if q.phase=="won":
		if q.win_stage=="other-shrub":
			q.win_animation.draw(surface)
		if q.win_stage=="shrub":
			q.win_animation.draw(surface)
			waiting_actor(q)
		else:
			var role = 0 if q.winner==0 else q.opponent
			var restore = tables.guess_restore_rectangles[3 if role==0 and n.host.character=="girl" else role]
			var background: Image = surface.image.duplicate()
			var b = tables.reveal_rectangles[q.winner]
			draw_shape(5608,5600,b[1]+1,b[0]+26)
			var region = Rect2i(restore[1],restore[0],restore[3]-restore[1],restore[2]-restore[0])
			surface.image.blit_rect(background,region,region.position)
			var a = tables.animals[q.cards[q.winner][q.secret[q.winner]]]
			var shape = store.shape("modules",a.large)
			draw_shape(a.large,a.palette,int((b[1]+b[3])/2)-int(shape[0]/2),b[0])
	if q.phase=="won" and q.revealed==3:
		var player = 1-q.winner
		var b = tables.reveal_rectangles[player]
		var a = tables.animals[q.cards[player][q.secret[player]]]
		var shape = store.shape("modules",a.large)
		draw_shape(5608,5600,b[1]+1,b[0]+26)
		draw_shape(a.large,a.palette,int((b[1]+b[3])/2)-int(shape[0]/2),b[0])
	draw_shape(5665,5650,284,1)
	draw_shape(5664,5650,265,1)
	draw_shape(8,6,304,1,10,"th")
	if q.phase in ["ready","answered"]:
		draw_shape(5669,5650,137,8,2)
		center(5668 if q.hint_control else 5667,[12,141,29,158],5650,Color.WHITE)
	if q.phase!="ready" and not q.options:
		if q.display_cards!=false:
			for i in 8:
				var a = tables.animals[q.cards[shown][i]]
				center(a.small,r[20+i],a.palette,Color8(255,85,85) if q.hint_card==i else Color.WHITE if q.remaining[shown]&(1<<i) else Color8(170,170,170))
				center(5662 if q.remaining[shown]&(1<<i) else 5663,r[28+i],5650,color(5400,6))
		for i in (q.available if q.visible_questions==null else q.visible_questions):
			if i==q.reminder_hidden:
				continue
			var number = tables.question_shapes[i]
			var b = r[12+i]
			if number:
				fill(b,Color.WHITE)
				draw_shape(5600+number,5600,b[1],b[0])
			var pos = tables.question_positions[i]
			if i!=q.question_hidden:
				draw_shape(5651+i,5650,pos[1],pos[0])
		if q.phase=="question":
			q.draw_turn_actor(surface)
			if not q.busy or q.reminding or q.robot_spoken or q.script_index==8:
				draw_shape(5669,5650,137,82,2)
				center(5666,[86,141,103,158],5650,Color8(255,85,85) if q.guess_hint or q.guessing or q.waiting or q.script_index==8 else Color.WHITE)
		for i in 8:
			if (q.phase=="won" and q.win_stage!="shrub") or q.asked[shown]&(1<<i):
				text(n.strings(5200+i)[q.attributes(q.cards[shown][q.secret[shown]])[i]],30,7+14*i)
		if q.selected>=0:
			var id = q.cards[shown][q.selected]
			var a = tables.animals[id]
			fill(r[38],Color.WHITE)
			var title = n.strings(5208+a.active_time)[a.category]
			heading(title,79-int(width(title,true)/2),7)
			var name = n.animal_name(id)
			text(name,79-int(width(name)/2),21)
			center(a.large,[30,30,77,128],a.palette)
			var sorted = q.available.duplicate()
			sorted.sort()
			for row in sorted.size():
				var index = sorted[row]
				var value = n.strings(5200+index)[q.attributes(id)[index]]
				text(value,79-int(width(value)/2),77+14*row)
		if (q.phase=="answered" or q.answer_display) and not q.answer.is_empty():
			var x = 86-int(width(q.answer)/2)
			text(q.answer,x,126)
			draw_shape(5662,5650,x-12,125)
		if q.phase=="won" and q.win_stage!="shrub":
			if q.win_stage in ["cleanup","done","other-shrub"]:
				draw_shape(5669,5650,137,8,2)
				center(922,[12,141,29,158],900,Color8(255,85,85) if q.hint_control else Color.WHITE,"th")
			if q.selected<0 and q.explanation.is_empty():
				var name = n.animal_name(q.cards[shown][q.secret[shown]])
				text(name,86-int(width(name)/2),126)
			if q.win_stage in ["celebrate","retreat"]:
				if q.win_stage=="retreat":
					fill([42,134,80,167],Color.WHITE)
				q.win_animation.draw(surface)
				if q.win_stage=="retreat":
					draw_shape(5403,5400,166,41)
	if not q.explanation.is_empty() and not q.options:
		fill(r[38],Color.WHITE)
		center(5651+q.selected_attribute,r[1+q.selected_attribute],5650,color(5650,8))
		var title = n.strings(5300)[q.selected_attribute]
		text(title,79-int(width(title)/2),6)
		var line = ""
		var y = 17
		for word in q.explanation.split(" "):
			var trial = word if line.is_empty() else line+" "+word
			if width(trial)>98:
				text(line,30,y,[17,30,116,128])
				y += 10
				line = word
			else:
				line = trial
		text(line,30,y,[17,30,116,128])
	if q.actor_script!=null:
		if q.divider:
			fill([42,134,80,167],Color.WHITE)
		q.actor_script.draw(surface)
		if q.divider:
			draw_shape(5403,5400,166,41)
	if q.waiting and q.actor_script==null and q.phase!="won":
		fill([42,134,80,167],Color.WHITE)
		waiting_actor(q)
	if q.options:
		var o = tables.quiz_options
		var bg = Color8(255,235,195)
		draw_shape(5404,5400,6,3,2)
		draw_shape(5405,5400,34,49,2)
		center(24202 if q.opponent==2 else 22201,o[2],24200 if q.opponent==2 else 22200,bg,"th")
		center(20201,o[7],20200,bg,n.host.character)
		if q.opponent==1:
			draw_shape(5405,5400,34,67,2)
			center(22201,o[8],22200,bg,"th")
		for item in [[q.opponent==1,3],[q.opponent==2,4],[q.help[0],5],[q.opponent==1 and q.help[1],6]]:
			if item[0]:
				mask("th",9,o[item[1]][1],o[item[1]][0],Color8(255,85,85))

func waiting_actor(q) -> void:
	var role = q.role()
	var archive = q.host.character if role==0 else "th"
	var group = 20100+2000*role
	var pos = [238,112 if q.host.character=="girl" else 115] if role==0 else [231,139] if role==1 else [229,137]
	draw_shape(group+(2 if role==2 else 1),group,pos[0],pos[1],10,archive)
