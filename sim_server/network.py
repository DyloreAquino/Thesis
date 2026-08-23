"""Websocket server: connection lifecycle + message routing. Knows nothing about JuPedSim itself."""
import asyncio
import json
import websockets
from geometry import SceneGeometry

scene_geometry = SceneGeometry()

async def handler(websocket) -> None:
    print("Godot connected")
    try:
        async for raw_message in websocket:
            await _route_message(raw_message)
    except websockets.exceptions.ConnectionClosed:
        print("Godot disconnected")

async def _route_message(raw_message: str) -> None:
    data = json.loads(raw_message)
    cmd = data.get("cmd")

    if cmd == "setup_geometry":
        scene_geometry.set_from_message(data)
        print(f"Geometry received: {len(scene_geometry.entry_areas)} entry areas, "
              f"{len(scene_geometry.exit_areas)} exit areas, and "
              f"a walking area with these points: {list(scene_geometry.walkable_area.exterior.coords)}")
    else:
        print(f"Unknown command: {cmd}")

async def start_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    async with websockets.serve(handler, host, port):
        print(f"Listening on ws://{host}:{port}")
        await asyncio.Future()