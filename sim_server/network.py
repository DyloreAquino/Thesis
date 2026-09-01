"""Websocket server: connection lifecycle + message routing. Knows nothing about JuPedSim itself."""
import asyncio
import json
import math

import websockets
from geometry import SceneGeometry
from simulation import CrowdSimulation

scene_geometry = SceneGeometry()
SNAPSHOT_EVERY_N_ITERATIONS = 5

sim_parameters = {
    "agent_count": 20,
    "entry_rate": 1.0
}

async def handler(websocket) -> None:
    """Handles messages received from Godot"""
    print("Godot connected")
    simulation_tasks: set[asyncio.Task] = set()
    try:
        async for raw_message in websocket:
            active_simulation = next(
                (task for task in simulation_tasks if not task.done()), None
            )
            simulation_task = await _route_message(
                raw_message, websocket, active_simulation
            )
            if simulation_task is not None:
                simulation_tasks.add(simulation_task)
    except websockets.exceptions.ConnectionClosedOK as closed:
        print(f"Godot closed normally: {closed.code} {closed.reason}")
    except websockets.exceptions.ConnectionClosedError as closed:
        print(f"Godot connection lost: {closed.code} {closed.reason}")
    finally:
        for task in simulation_tasks:
            if not task.done():
                task.cancel()
        if simulation_tasks:
            await asyncio.gather(*simulation_tasks, return_exceptions=True)
        if websocket.close_code is None:
            await websocket.close(code=1000, reason="Server handler shutting down")
        print("Godot disconnected")

async def start_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Only main calls this. Starts the server upon starting main.py"""
    async with websockets.serve(handler, host, port):
        print(f"Listening on ws://{host}:{port}")
        try:
            await asyncio.Future()
        finally:
            print("WebSocket server shutting down")

async def _run_simulation(websocket) -> None:
    """Runs the simulation, then sends info to Godot"""
    crowd = None
    try:
        crowd = CrowdSimulation(scene_geometry, sim_parameters=sim_parameters)
        await _send_simulation_state(websocket, "running")
        tick = 0
        while not crowd.is_finished():
            crowd.step()
            tick += 1
            if tick % SNAPSHOT_EVERY_N_ITERATIONS == 0:
                await websocket.send(json.dumps({
                    "cmd": "tick",
                    "t": tick,
                    "dt": crowd.delta_time() * SNAPSHOT_EVERY_N_ITERATIONS,
                    "agents": crowd.snapshot()}))
                await asyncio.sleep(crowd.delta_time() * SNAPSHOT_EVERY_N_ITERATIONS)
        print("All agents exited")
    except asyncio.CancelledError:
        raise
    except Exception as error:
        print(f"Simulation failed: {error}")
        if websocket.close_code is None:
            await _send_simulation_state(websocket, "error", str(error))
    finally:
        if crowd is not None:
            crowd.close()
        if websocket.close_code is None:
            await _send_simulation_state(websocket, "idle")

async def _send_simulation_state(
    websocket, state: str, message: str | None = None
) -> None:
    """Tell Godot the server-authoritative simulation state."""
    payload = {"cmd": "simulation_state", "state": state}
    if message is not None:
        payload["message"] = message
    await websocket.send(json.dumps(payload))

async def _route_message(
    raw_message: str,
    websocket,
    active_simulation: asyncio.Task | None = None,
) -> asyncio.Task | None:
    """Routes the needed command from Godot to whatever it needs to do"""
    data = json.loads(raw_message)
    cmd = data.get("cmd")

    if cmd == "setup_geometry":
        try:
            scene_geometry.set_from_message(data)
        except (KeyError, TypeError, ValueError) as error:
            print(f"Invalid geometry or routing: {error}")
            await _send_simulation_state(websocket, "error", str(error))
            return
        print(f"Geometry received: {len(scene_geometry.entry_areas)} entry areas, "
              f"{len(scene_geometry.exit_areas)} exit areas, "
              f"{len(scene_geometry.obstacles)} obstacles, and "
              f"{len(scene_geometry.switches)} switches.")
        
    elif cmd == "update_sim_parameters":
        if "agent_count" in data:
            sim_parameters["agent_count"] = data["agent_count"]
            
        if "entry_rate" in data:
            entry_rate = float(data["entry_rate"])
            if math.isfinite(entry_rate) and entry_rate > 0:
                sim_parameters["entry_rate"] = entry_rate
            else:
                print("Ignoring entry_rate: it must be greater than 0 agents/second")
        
    elif cmd == "start_simulation":
        if active_simulation is not None and not active_simulation.done():
            await _send_simulation_state(
                websocket, "running", "A simulation is already running"
            )
            return
        if not scene_geometry.is_ready():
            print("Cannot start: geometry not fully received yet")
            await _send_simulation_state(
                websocket, "error", "Geometry is not ready"
            )
            return
        await _send_simulation_state(websocket, "starting")
        return asyncio.create_task(_run_simulation(websocket))
        
    else:
        print(f"Unknown command: {cmd}")
