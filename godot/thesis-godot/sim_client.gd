extends Node
class_name SimClient

signal simulation_state_changed(state: String)

const STATE_IDLE := "idle"
const STATE_STARTING := "starting"
const STATE_RUNNING := "running"

@export var geometry_exporter : GeometryExporter
@export var agent_manager: AgentManager
@export var stats_manager: StatisticsManager

@onready var start_simulation_button: Button = $"../CanvasLayer/StartSimulationButton"

var socket := WebSocketPeer.new()
var simulation_state := STATE_IDLE

func _ready():
	socket.connect_to_url("ws://127.0.0.1:8765")

func _exit_tree() -> void:
	close_socket()

## Each frame, check if the server sent something
func _process(_delta):
	socket.poll()
	match socket.get_ready_state():
		WebSocketPeer.STATE_OPEN:
			while socket.get_available_packet_count() > 0:
				var text := socket.get_packet().get_string_from_utf8()
				var data = JSON.parse_string(text)
				if data is Dictionary:
					_parse_server_message(data)
		WebSocketPeer.STATE_CLOSED:
			_set_simulation_state(STATE_IDLE)
			print("Closed, code: %d" % socket.get_close_code())
			set_process(false)

## Send message to the server in string format.
func send_message(text: String) -> bool:
	if socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		var error := socket.send_text(text)
		if error == OK:
			return true
		push_error("Failed to send WebSocket message: %s" % error_string(error))
	else:
		push_warning("Tried to send before the socket was open")
	return false

## Initiate a normal WebSocket close handshake when this client exits.
func close_socket() -> void:
	_set_simulation_state(STATE_IDLE)
	if socket.get_ready_state() == WebSocketPeer.STATE_OPEN:
		socket.close(1000, "Godot client shutting down")
		socket.poll()

## Parse simulation snapshots and server-authoritative state changes.
func _parse_server_message(data: Dictionary) -> void:
	match data.get("cmd"):
		"tick":
			var inv_scale := 1.0 / geometry_exporter.world_scale
			agent_manager.apply_snapshot(data["agents"], inv_scale, data["dt"])
			stats_manager.apply_snapshot(data["statistics"], data["dt"])
		"simulation_state":
			var state := String(data.get("state", STATE_IDLE))
			if state == "error":
				push_warning(String(data.get("message", "Simulation failed")))
				_set_simulation_state(STATE_IDLE)
			elif state in [STATE_IDLE, STATE_STARTING, STATE_RUNNING]:
				_set_simulation_state(state)

func _set_simulation_state(new_state: String) -> void:
	if simulation_state == new_state:
		return
	simulation_state = new_state
	start_simulation_button.disabled = new_state != STATE_IDLE
	match new_state:
		STATE_STARTING:
			start_simulation_button.text = "Starting..."
		STATE_RUNNING:
			start_simulation_button.text = "Simulation Running"
		_:
			start_simulation_button.text = "Start Simulation"
	simulation_state_changed.emit(new_state)

func is_simulation_running() -> bool:
	return simulation_state == STATE_RUNNING

func is_simulation_active() -> bool:
	return simulation_state in [STATE_STARTING, STATE_RUNNING]

func start_simulation() -> void:
	if is_simulation_active():
		push_warning("A simulation is already starting or running")
		return
	_set_simulation_state(STATE_STARTING)
	if not send_message(JSON.stringify({"cmd": "start_simulation"})):
		_set_simulation_state(STATE_IDLE)

func _on_start_simulation_button_button_up():
	start_simulation()
