extends CanvasLayer
## Explicit file controls outside the original game, opened with F9.
var host
var panel: PanelContainer
var message: Label
var dialog: FileDialog
var action: String = ""
var callback
var browser
var active: bool = false
var print_image: Image
var title: Label
var tip: Label
var buttons: Dictionary = {}

func _init(game) -> void:
	host = game
	layer = 10

func _ready() -> void:
	panel = PanelContainer.new()
	panel.position = Vector2(16,18)
	panel.size = Vector2(288,164)
	var style = StyleBoxFlat.new()
	style.bg_color = Color8(24,31,39)
	style.border_color = Color8(111,126,143)
	style.set_border_width_all(1)
	style.set_corner_radius_all(3)
	panel.add_theme_stylebox_override("panel",style)
	panel.add_theme_font_size_override("font_size",11)
	var box = VBoxContainer.new()
	box.add_theme_constant_override("separation",5)
	var margin = MarginContainer.new()
	for edge in ["left","right","top","bottom"]:
		margin.add_theme_constant_override("margin_"+edge,8)
	panel.add_child(margin)
	margin.add_child(box)
	title = Label.new()
	title.text = "Save files"
	title.add_theme_font_size_override("font_size",14)
	box.add_child(title)
	tip = Label.new()
	tip.text = "Keep both files to save your game and songbooks."
	tip.add_theme_font_size_override("font_size",10)
	box.add_child(tip)
	var grid = GridContainer.new()
	grid.columns = 2
	box.add_child(grid)
	for item in [["Load game","load-status"],["Save game","save-status"],["Load songbooks","load-songs"],["Save songbooks","save-songs"],["Save picture","save-picture"],["Print picture","print-picture"]]:
		var button = Button.new()
		button.text = item[0]
		button.add_theme_font_size_override("font_size",11)
		button.custom_minimum_size = Vector2(130,23)
		button.pressed.connect(request.bind(item[1]))
		grid.add_child(button)
		buttons[item[1]] = button
	message = Label.new()
	message.add_theme_font_size_override("font_size",10)
	message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	message.custom_minimum_size = Vector2(260,30)
	box.add_child(message)
	var close_button = Button.new()
	close_button.text = "Back to game"
	close_button.add_theme_font_size_override("font_size",11)
	close_button.pressed.connect(close)
	box.add_child(close_button)
	add_child(panel)
	panel.hide()
	if OS.has_feature("web"):
		callback = JavaScriptBridge.create_callback(web_selected)
		browser = JavaScriptBridge.get_interface("window")
		browser.treehouseFileSelected = callback
		JavaScriptBridge.eval("""
window.treehouseChooseFile = function(kind) {
 const input = document.createElement('input');
 input.type = 'file'; input.accept = '.dat'; input.style.display = 'none';
 document.body.appendChild(input);
 input.addEventListener('cancel', () => { input.remove(); window.treehouseFileSelected('cancel', '', ''); });
 input.addEventListener('change', () => {
  const file = input.files[0]; input.remove();
  if (!file) { window.treehouseFileSelected('cancel', '', ''); return; }
  const reader = new FileReader();
  reader.onload = () => window.treehouseFileSelected(kind, file.name, reader.result.split(',')[1]);
  reader.onerror = () => window.treehouseFileSelected('error', '', '');
  reader.readAsDataURL(file);
 });
 input.click();
};
const filesDialog = document.createElement('dialog');
filesDialog.id = 'treehouse-files';
filesDialog.setAttribute('aria-label', 'Save files');
filesDialog.style.cssText = 'color:#fff;background:#181f27;border:1px solid #6f7e8f;border-radius:8px;padding:24px;width:min(420px,calc(100vw - 64px));font:16px/1.4 sans-serif;';
filesDialog.innerHTML = '<h2 style="margin:0 0 8px">Save files</h2><p>Keep both files to save your game and songbooks.</p><div id="treehouse-file-actions" style="display:grid;grid-template-columns:1fr 1fr;gap:12px"></div><p id="treehouse-file-message" role="status" style="min-height:3em"></p>';
for (const [label, action] of [['Load game','load-status'],['Save game','save-status'],['Load songbooks','load-songs'],['Save songbooks','save-songs'],['Save picture','save-picture'],['Print picture','print-picture'],['Back to game','close']]) {
 const button = document.createElement('button'); button.textContent = label;
 button.dataset.action = action;
 button.style.cssText = 'padding:12px;font:inherit;color:#fff;background:#303f50;border:1px solid #6f7e8f;border-radius:4px;cursor:pointer;';
 button.onclick = () => {
  if (action === 'print-picture') { window.print(); return; }
  if (action.startsWith('load-')) window.treehouseChooseFile(action);
  else window.treehouseFileSelected(action,'','');
 };
 filesDialog.querySelector('#treehouse-file-actions').appendChild(button);
}
filesDialog.addEventListener('cancel', event => { event.preventDefault(); window.treehouseFileSelected('close','',''); });
filesDialog.addEventListener('keydown', event => {
 if (event.key === 'F9') { event.preventDefault(); event.stopPropagation(); window.treehouseFileSelected('close','',''); }
});
document.body.appendChild(filesDialog);
const printPage = document.createElement('section');
printPage.id = 'treehouse-print-page'; printPage.style.display = 'none';
const printImage = document.createElement('img'); printImage.alt = 'Treehouse picture';
printPage.appendChild(printImage); document.body.appendChild(printPage);
const printStyle = document.createElement('style');
printStyle.textContent = '@media print { @page { size: A4 landscape; margin: 15mm; } body.treehouse-printing { margin:0!important; background:white!important; overflow:visible!important; height:auto!important; } body.treehouse-printing > * { display:none!important; } body.treehouse-printing > #treehouse-print-page { display:block!important; position:static!important; } #treehouse-print-page img { display:block; width:240mm; max-width:100%; height:auto; image-rendering:pixelated; } }';
document.head.appendChild(printStyle);
window.treehouseFilesOpen = (png) => {
 const printing = !!png;
 filesDialog.setAttribute('aria-label', printing ? 'Print picture' : 'Save files');
 filesDialog.querySelector('h2').textContent = printing ? 'Print picture' : 'Save files';
 filesDialog.querySelector('p').textContent = printing ? 'Save the original picture or send it to your printer.' : 'Keep both files to save your game and songbooks.';
 for (const button of filesDialog.querySelectorAll('button')) {
  const action = button.dataset.action;
  button.hidden = action !== 'close' && action.endsWith('picture') !== printing;
 }
 const printButton = filesDialog.querySelector('[data-action="print-picture"]');
 printButton.disabled = true;
 printImage.onload = () => { printButton.disabled = false; };
 if (printing) printImage.src = 'data:image/png;base64,' + png;
 else printImage.removeAttribute('src');
 document.body.classList.toggle('treehouse-printing', printing);
 if (!filesDialog.open) filesDialog.showModal();
};
window.treehouseFilesClose = () => { filesDialog.close(); document.body.classList.remove('treehouse-printing'); document.getElementById('canvas').focus(); };
window.treehouseFileMessage = text => { filesDialog.querySelector('#treehouse-file-message').textContent = text; };
window.treehouseFilesDispose = () => { filesDialog.remove(); printPage.remove(); printStyle.remove(); document.body.classList.remove('treehouse-printing'); };
""",true)

func input(event: InputEvent) -> bool:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_F9:
			if active: close()
			elif preview()!=null or host.preferences.allowed(false): open()
			return true
		if active and event.keycode==KEY_ESCAPE:
			close()
			return true
	return active

func open() -> void:
	print_image = preview()
	if print_image!=null:
		print_image = print_image.duplicate()
	host.release_inputs()
	host.persistence.save()
	active = true
	if browser!=null:
		browser.treehouseFilesOpen(Marshalls.raw_to_base64(print_image.save_png_to_buffer()) if print_image!=null else "")
	else:
		title.text = "Print picture" if print_image!=null else "Save files"
		tip.text = "Save the picture or open it in your browser to print." if print_image!=null else "Keep both files to save your game and songbooks."
		for kind in buttons:
			buttons[kind].visible = kind.ends_with("picture")== (print_image!=null)
		panel.show()
	tell("Picture: TREEHOUSE.PNG" if print_image!=null else "Game: STATUS.DAT   Songbooks: SONGS.DAT")
	if host.persistence.save_error!=OK:
		tell("This device could not save your game. Download both files to keep it.")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func preview() -> Image:
	if not host.preferences.settings.printing or not host.preferences.kind.is_empty():
		return null
	if host.scene=="music": return host.music.print_view
	if host.scene=="nature": return host.nature.print_view
	return null

func close() -> void:
	if dialog!=null:
		dialog.queue_free()
		dialog = null
	active = false
	print_image = null
	panel.hide()
	if browser!=null:
		browser.treehouseFilesClose()
	host.remainder = 0
	host.dirty = true
	Input.mouse_mode = Input.MOUSE_MODE_HIDDEN

func tell(text: String) -> void:
	message.text = text
	if browser!=null:
		browser.treehouseFileMessage(text)

func request(kind: String) -> void:
	action = kind
	var name = "STATUS.DAT" if kind.ends_with("status") else "SONGS.DAT"
	if kind.ends_with("picture"):
		if print_image==null: return
		name = "TREEHOUSE.PNG"
		if kind=="print-picture":
			var path = "user://treehouse-print.html"
			var file = FileAccess.open(path,FileAccess.WRITE)
			if file==null:
				tell("Could not prepare the picture. Try Save picture instead.")
				return
			file.store_string(print_document(print_image.save_png_to_buffer()))
			var error = file.get_error()
			file.close()
			if error!=OK:
				tell("Could not prepare the picture. Try Save picture instead.")
				return
			var opened = OS.shell_open(ProjectSettings.globalize_path(path))
			tell("Use Print picture in the browser window." if opened==OK else "Could not open a browser. Try Save picture instead.")
			return
	if OS.has_feature("web"):
		if kind.begins_with("save"):
			JavaScriptBridge.download_buffer(export_data(kind),name,"image/png" if kind=="save-picture" else "application/octet-stream")
			tell(name+" downloaded.")
		else:
			browser.treehouseChooseFile(kind)
		return
	dialog = FileDialog.new()
	dialog.access = FileDialog.ACCESS_FILESYSTEM
	dialog.file_mode = FileDialog.FILE_MODE_SAVE_FILE if kind.begins_with("save") else FileDialog.FILE_MODE_OPEN_FILE
	dialog.use_native_dialog = true
	dialog.filters = PackedStringArray(["*.png ; PNG picture"] if kind=="save-picture" else ["*.dat ; Treehouse data files"])
	dialog.current_file = name
	dialog.file_selected.connect(desktop_selected)
	dialog.canceled.connect(func():
		tell("No file selected.")
		dialog.queue_free()
		dialog = null)
	add_child(dialog)
	dialog.popup_centered_ratio(0.8)

func export_data(kind: String) -> PackedByteArray:
	if kind=="save-picture": return print_image.save_png_to_buffer() if print_image!=null else PackedByteArray()
	return host.persistence.export_data() if kind.ends_with("status") else host.music.editor.export_data()

static func print_document(png: PackedByteArray) -> String:
	return '<!doctype html><html lang="en"><meta charset="utf-8"><title>Treehouse picture</title><style>body{margin:24px;font:18px sans-serif;background:white;color:black}img{display:block;width:960px;max-width:100%;height:auto;image-rendering:pixelated}button{font:inherit;padding:12px;margin-bottom:20px}@media print{@page{size:A4 landscape;margin:15mm}body{margin:0}button{display:none}img{width:240mm;max-width:100%}}</style><button onclick="window.print()" disabled>Print picture</button><img alt="Treehouse picture" onload="document.querySelector(\'button\').disabled=false" src="data:image/png;base64,'+Marshalls.raw_to_base64(png)+'"></html>'

func import_data(kind: String, data: PackedByteArray) -> bool:
	var loaded = host.persistence.import_data(data) if kind.ends_with("status") else host.music.editor.import_data(data)
	if loaded:
		if kind.ends_with("status"):
			tell("Game loaded. Choose a friend to begin.")
			if not host.persistence.file.warnings.is_empty():
				tell("Game loaded. Some invalid saved values were repaired for play.")
		else:
			host.music.instrument = int(host.music.song[3])
			tell("Both songbooks loaded.")
		host.dirty = true
	else:
		tell("That file is incomplete or invalid. Your game has not changed.")
	return loaded

func web_selected(args: Array) -> void:
	if args.size()!=3 or not active: return
	if args[0]=="cancel":
		tell("No file selected.")
	elif args[0]=="error":
		tell("Could not read that file. Please try again.")
	elif args[0]=="close":
		close()
	elif args[0] in ["save-status","save-songs","save-picture"]:
		request(str(args[0]))
	elif args[0] in ["load-status","load-songs"]:
		import_data(str(args[0]),Marshalls.base64_to_raw(str(args[2])))

func desktop_selected(path: String) -> void:
	if action.begins_with("save"):
		var file = FileAccess.open(path,FileAccess.WRITE)
		if file==null:
			tell("Could not save that file. Please choose another location.")
		else:
			file.store_buffer(export_data(action))
			tell("File saved." if file.get_error()==OK else "The file could not be saved completely.")
			file.close()
	else:
		import_data(action,FileAccess.get_file_as_bytes(path))
	dialog.queue_free()
	dialog = null

func _exit_tree() -> void:
	if browser!=null:
		browser.treehouseFilesDispose()
		browser.treehouseFileSelected = null
		browser.treehouseChooseFile = null
	callback = null
