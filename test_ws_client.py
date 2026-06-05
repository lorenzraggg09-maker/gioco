import asyncio
import json
import time
import websockets

async def main():
    uri = 'ws://localhost:8765'
    try:
        async with websockets.connect(uri) as ws:
            print('Connected to', uri)
            await ws.send(json.dumps({'type':'join','name':'TestClient'}))
            start = time.time()
            while time.time() - start < 5.0:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    print('RECV:', msg)
                except asyncio.TimeoutError:
                    pass
            print('Test finished, closing')
    except Exception as e:
        print('Connection failed:', e)

if __name__ == '__main__':
    asyncio.run(main())
