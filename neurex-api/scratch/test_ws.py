import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/default?token=neurex-dev-token&user_id=TestUser"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            await websocket.send(json.dumps({"type": "ping"}))
            resp = await websocket.recv()
            print(f"Received: {resp}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
