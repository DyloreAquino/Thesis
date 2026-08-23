import asyncio, json, websockets

async def handler(websocket):
    print("Godot connected")
    tick = 0
    try:
        while True:
            tick += 1
            # Test agent for now
            agents = [{
              "id": 0, 
              "x": 1.0 + tick * 0.01, 
              "y": 2.0, 
              "vx": 0.5, 
              "vy": 0.0
            }]
            await websocket.send(json.dumps({"t": tick, "agents": agents}))
            await asyncio.sleep(0.05)  # 20Hz snapshot rate
    except websockets.exceptions.ConnectionClosed:
        print("Godot disconnected")

async def main():
    async with websockets.serve(handler, "127.0.0.1", 8765):
        print("Listening on ws://127.0.0.1:8765")
        await asyncio.Future()

asyncio.run(main())