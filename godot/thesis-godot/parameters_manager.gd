extends Node
class_name ParametersManager

@export var sim_client: SimClient
@onready var agent_count_input = $"../CanvasLayer/HBoxContainer/AgentCountInput"

func update_parameters() -> void:
	var message := {
		"cmd": "update_sim_parameters",
		"agent_count": agent_count_input.value
	}
	sim_client.send_message(JSON.stringify(message))
	print(message)

func _on_agent_count_input_value_changed(value):
	update_parameters()
