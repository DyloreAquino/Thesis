extends Node
class_name ParametersManager

@export var sim_client: SimClient
@onready var agent_count_input = $"../CanvasLayer/VBoxContainer/HBoxContainer/AgentCountInput"
@onready var entry_rate_input = $"../CanvasLayer/VBoxContainer/HBoxContainer2/EntryRateInput"

func update_parameters() -> void:
	var message := {
		"cmd": "update_sim_parameters",
		"agent_count": agent_count_input.value,
		"entry_rate": entry_rate_input.value
	}
	sim_client.send_message(JSON.stringify(message))
	print(message)

func _on_agent_count_input_value_changed(value: int) -> void:
	update_parameters()


func _on_entry_rate_input_value_changed(value: float) -> void:
	update_parameters()
