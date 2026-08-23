extends Node
class_name SimClient

var socket := WebSocketPeer.new()

func _ready():
	socket.connect_to_url("ws://127.0.0.1:8765")

func _process(_delta):
	socket.poll()
	match socket.get_ready_state():
		WebSocketPeer.STATE_OPEN:
			while socket.get_available_packet_count() > 0:
				var text := socket.get_packet().get_string_from_utf8()
				var data = JSON.parse_string(text)
				_apply_snapshot(data)
		WebSocketPeer.STATE_CLOSED:
			print("Closed, code: %d" % socket.get_close_code())
			set_process(false)

func _apply_snapshot(data: Dictionary) -> void:
	for agent in data["agents"]:
		print(agent["id"], " ", agent["x"], ",", agent["y"])
		# later: look up agent Node3D by id, set position/velocityextends Node

## Send message to the server in string format.
func send_message(text: String) -> void:
	if socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		socket.send_text(text)
	else:
		push_warning("Tried to send before the socket was open")
