extends Node
class_name AgentManager

@export var agent_scene: PackedScene

var agents: Dictionary[int, Agent] = {}  # agent_id (int) -> Agent instance

## This runs everytime we get a snapshot from the server
func apply_snapshot(agent_data: Array, inverse_scale: float, interval: float) -> void:
	var seen_ids := {}
	for entry in agent_data:
		var id: int = entry["id"]
		var target_pos := Vector2(entry["x"], entry["y"]) * inverse_scale
		seen_ids[id] = true
		_update_or_spawn(id, target_pos, interval)
	_despawn_missing(seen_ids)

## Either we update existing info or we spawn it in
func _update_or_spawn(id: int, target_pos: Vector2, interval: float) -> void:
	if agents.has(id):
		agents[id].set_target_position(target_pos, interval)
	else:
		var agent_node: Node2D = agent_scene.instantiate()
		add_child(agent_node)
		agent_node.global_position = target_pos
		agent_node.set_target_position(target_pos, interval)
		agents[id] = agent_node

## If not there anymore, remove from the dictionary
func _despawn_missing(seen_ids: Dictionary) -> void:
	for id in agents.keys():
		if not seen_ids.has(id):
			agents[id].queue_free()
			agents.erase(id)
