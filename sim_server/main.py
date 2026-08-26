import asyncio
from network import start_server

if __name__ == "__main__":
    asyncio.run(start_server())
    # asyncio.run(stop_server)