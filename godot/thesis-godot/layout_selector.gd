extends Control

const LAYOUTS := [
	{
		"button_path": "ScrollContainer/GridContainer/O1T1E1Button",
		"scene_path": "res://Tests/O1T1E1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T1E2Button",
		"scene_path": "res://Tests/O1T1E2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T1E3Button",
		"scene_path": "res://Tests/O1T1E3.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T2E1Button",
		"scene_path": "res://Tests/O1T2E1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T2E2Button",
		"scene_path": "res://Tests/O1T2E2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T2E3Button",
		"scene_path": "res://Tests/O1T2E3.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T3E1Button",
		"scene_path": "res://Tests/O1T3E1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T3E2Button",
		"scene_path": "res://Tests/O1T3E2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O1T3E3Button",
		"scene_path": "res://Tests/O1T3E3.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T1E1Button",
		"scene_path": "res://Tests/O2T1E1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T1E2Button",
		"scene_path": "res://Tests/O2T1E2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T1E3Button",
		"scene_path": "res://Tests/O2T1E3.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T2E1Button",
		"scene_path": "res://Tests/O2T2E1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T2E2Button",
		"scene_path": "res://Tests/O2T2E2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T2E3Button",
		"scene_path": "res://Tests/O2T2E3.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T3E1Button",
		"scene_path": "res://Tests/O2T3E1.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T3E2Button",
		"scene_path": "res://Tests/O2T3E2.tscn",
	},
	{
		"button_path": "ScrollContainer/GridContainer/O2T3E3Button",
		"scene_path": "res://Tests/O2T3E3.tscn",
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
