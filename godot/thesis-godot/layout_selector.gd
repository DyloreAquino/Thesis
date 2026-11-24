extends Control

const LAYOUTS := [
	{
		"button_path": "ScrollContainer/GridContainer/MainLayoutButton",
		"scene_path": "res://Tests/main_layout.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T2Button",
		"scene_path": "res://Tests/O1T2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T3Button",
		"scene_path": "res://Tests/O1T3.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T1Button",
		"scene_path": "res://Tests/O2T1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T2Button",
		"scene_path": "res://Tests/O2T2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T3Button",
		"scene_path": "res://Tests/O2T3.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O3T1Button",
		"scene_path": "res://Tests/O3T1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O3T2Button",
		"scene_path": "res://Tests/O3T2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O3T3Button",
		"scene_path": "res://Tests/O3T3.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O4T1Button",
		"scene_path": "res://Tests/O4T1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O4T2Button",
		"scene_path": "res://Tests/O4T2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O4T3Button",
		"scene_path": "res://Tests/O4T3.tscn",
	},
]

func _ready() -> void:
	for layout in LAYOUTS:
		var button := get_node_or_null(layout["button_path"]) as Button
		if button == null:
			push_error("Missing layout selector button: %s" % layout["button_path"])
			continue
		button.pressed.connect(_on_layout_selected.bind(layout["scene_path"]))

func _on_layout_selected(scene_path: String) -> void:
	var error := get_tree().change_scene_to_file(scene_path)
	if error != OK:
		push_error("Failed to load layout '%s': %s" % [scene_path, error_string(error)])
