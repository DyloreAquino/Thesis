extends Node
class_name SimClient

@export var geometry_exporter : GeometryExporter
@export var agent_manager: Node
var socket := WebSocketPeer.new()

func _ready():
	socket.connect_to_url("ws://127.0.0.1:8765")

## Each frame, check if the server sent something
func _process(_delta):
	socket.poll()
	match socket.get_ready_state():
		WebSocketPeer.STATE_OPEN:
			while socket.get_available_packet_count() > 0:
				var text := socket.get_packet().get_string_from_utf8()
				var data = JSON.parse_string(text)
				_parse_coordinates(data)
		WebSocketPeer.STATE_CLOSED:
			print("Closed, code: %d" % socket.get_close_code())
			set_process(false)

## Send message to the server in string format.
func send_message(text: String) -> void:
	if socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		socket.send_text(text)
	else:
		push_warning("Tried to send before the socket was open")

## Parses given coordinates from JuPedSim Coordinates to Godot Coordinates
## Then calls our agent manager to update the snapshot
func _parse_coordinates(data: Dictionary) -> void:
	if data.get("cmd") == "tick":
		var inv_scale := 1.0 / geometry_exporter.world_scale
		agent_manager.apply_snapshot(data["agents"], inv_scale, data["dt"])

func start_simulation() -> void:
	send_message(JSON.stringify({"cmd": "start_simulation"}))

func _on_start_simulation_button_button_up():
	start_simulation()
