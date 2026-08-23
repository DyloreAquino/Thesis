"""Websocket server: connection lifecycle + message routing. Knows nothing about JuPedSim itself."""
import asyncio
import json
import websockets
from geometry import SceneGeometry
from simulation import CrowdSimulation

scene_geometry = SceneGeometry()
SNAPSHOT_EVERY_N_ITERATIONS = 5

async def handler(websocket) -> None:
    """Handles messages received from Godot"""
    print("Godot connected")
    try:
        async for raw_message in websocket:
            await _route_message(raw_message, websocket)
    except websockets.exceptions.ConnectionClosed:
        print("Godot disconnected")

async def start_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Only main calls this. Starts the server upon starting main.py"""
    async with websockets.serve(handler, host, port):
        print(f"Listening on ws://{host}:{port}")
        await asyncio.Future()

async def _run_simulation(websocket) -> None:
    """Starts the simulation"""
    crowd = CrowdSimulation(scene_geometry)
    tick = 0
    while crowd.agent_count() > 0:
        crowd.step()
        tick += 1
        if tick % SNAPSHOT_EVERY_N_ITERATIONS == 0:
            await websocket.send(json.dumps({"cmd": "tick", "t": tick, "agents": crowd.snapshot()}))
            await asyncio.sleep(crowd.delta_time() * SNAPSHOT_EVERY_N_ITERATIONS)
    print("All agents exited")

async def _route_message(raw_message: str, websocket) -> None:
    """Routes the needed command to whatever it needs to do"""
    data = json.loads(raw_message)
    cmd = data.get("cmd")

    if cmd == "setup_geometry":
        scene_geometry.set_from_message(data)
        print(f"Geometry received: {len(scene_geometry.entry_areas)} entry areas, "
              f"{len(scene_geometry.exit_areas)} exit areas, and "
              f"a walking area with these points: {list(scene_geometry.walkable_area.exterior.coords)}")
        
    elif cmd == "start_simulation":
        if not scene_geometry.is_ready():
            print("Cannot start: geometry not fully received yet")
            return
        asyncio.create_task(_run_simulation(websocket))
        
    else:
        print(f"Unknown command: {cmd}")