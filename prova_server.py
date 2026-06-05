import asyncio
import json
import random
import time

import websockets

HOST = '0.0.0.0'
PORT = 8765
MAX_PLAYERS = 2
BPM = 130
MS_PER_BEAT = 60000 / BPM
HIT_WINDOW = 120
PERFECT_WINDOW = 50
GOOD_WINDOW = 90
BAD_WINDOW = 120
START_DELAY_MS = 2500
MAX_HEALTH = 100

pattern = [
    {"beat": i, "lane": lane}
    for i, lane in enumerate([
        0, 1, 2, 3, 1, 2, 0, 3,
        2, 1, 0, 1, 2, 3, 0, 2,
        1, 0, 3, 2, 1, 0, 2, 3,
        0, 1, 2, 3, 1, 0, 3, 2,
    ])
]

clients = []
player_by_ws = {}
player_names = {}
scores = {1: 0, 2: 0}
health = {1: MAX_HEALTH, 2: MAX_HEALTH}
combo = {1: 0, 2: 0}
hit_notes = {1: set(), 2: set()}
missed_notes = {1: set(), 2: set()}
start_time_ms = None
match_started = False

async def send(ws, message):
    try:
        await ws.send(json.dumps(message))
    except websockets.ConnectionClosed:
        pass

async def broadcast(message):
    data = json.dumps(message)
    for ws in list(clients):
        try:
            await ws.send(data)
        except websockets.ConnectionClosed:
            pass

async def broadcast_update():
    await broadcast({
        "type": "update",
        "scores": scores,
        "health": health,
        "combo": combo,
    })

async def evaluate_hit(player_id, lane):
    now_ms = int(time.time() * 1000)
    best_index = None
    best_dt = None

    for idx, note in enumerate(pattern):
        if note["lane"] != lane:
            continue
        if idx in hit_notes[player_id] or idx in missed_notes[player_id]:
            continue

        note_time = start_time_ms + note["beat"] * MS_PER_BEAT
        dt = now_ms - note_time
        if abs(dt) <= BAD_WINDOW:
            if best_dt is None or abs(dt) < abs(best_dt):
                best_dt = dt
                best_index = idx

    if best_index is None:
        combo[player_id] = 0
        health[player_id] = max(0, health[player_id] - 5)
        return {
            "type": "result",
            "player_id": player_id,
            "result": "TRASH",
            "lane": lane,
            "note_index": None,
            "score": scores[player_id],
            "health": health[player_id],
            "combo": combo[player_id],
        }

    hit_notes[player_id].add(best_index)
    dt = best_dt
    if abs(dt) <= PERFECT_WINDOW:
        result = "PERFECT"
        score = 15
        health[player_id] = min(MAX_HEALTH, health[player_id] + 5)
        combo[player_id] += 1
    elif abs(dt) <= GOOD_WINDOW:
        result = "GOOD"
        score = 10
        health[player_id] = min(MAX_HEALTH, health[player_id] + 3)
        combo[player_id] += 1
    else:
        result = "BAD"
        score = 2
        combo[player_id] = 0

    scores[player_id] += score

    return {
        "type": "result",
        "player_id": player_id,
        "result": result,
        "lane": lane,
        "note_index": best_index,
        "score": scores[player_id],
        "health": health[player_id],
        "combo": combo[player_id],
    }

async def process_misses():
    global match_started
    while True:
        if match_started:
            now_ms = int(time.time() * 1000)
            changed = False
            for player_id in [1, 2]:
                for idx, note in enumerate(pattern):
                    if idx in hit_notes[player_id] or idx in missed_notes[player_id]:
                        continue
                    note_time = start_time_ms + note["beat"] * MS_PER_BEAT
                    if now_ms > note_time + BAD_WINDOW:
                        missed_notes[player_id].add(idx)
                        combo[player_id] = 0
                        health[player_id] = max(0, health[player_id] - 5)
                        changed = True
                        await broadcast({
                            "type": "result",
                            "player_id": player_id,
                            "result": "MISS",
                            "lane": note["lane"],
                            "note_index": idx,
                            "score": scores[player_id],
                            "health": health[player_id],
                            "combo": combo[player_id],
                        })
            if changed:
                await broadcast_update()
                await check_game_over()
        await asyncio.sleep(0.05)

async def check_game_over():
    global match_started
    if health[1] <= 0 or health[2] <= 0:
        winner = 1 if health[1] > health[2] else 2 if health[2] > health[1] else 0
        await broadcast({"type": "game_over", "winner": winner, "scores": scores, "health": health})
        match_started = False
        return True

    finished = all(
        idx in hit_notes[1] or idx in missed_notes[1]
        for idx in range(len(pattern))
    ) and all(
        idx in hit_notes[2] or idx in missed_notes[2]
        for idx in range(len(pattern))
    )
    if finished:
        winner = 1 if scores[1] > scores[2] else 2 if scores[2] > scores[1] else 0
        await broadcast({"type": "game_over", "winner": winner, "scores": scores, "health": health})
        match_started = False
        return True
    return False

async def start_match():
    global start_time_ms, match_started
    start_time_ms = int(time.time() * 1000 + START_DELAY_MS)
    match_started = True
    await broadcast({
        "type": "start",
        "delay": START_DELAY_MS,
        "bpm": BPM,
        "ms_per_beat": MS_PER_BEAT,
        "hit_window": HIT_WINDOW,
        "pattern": pattern,
    })
    await broadcast_update()

async def register_player(ws):
    player_id = len(clients) + 1
    clients.append(ws)
    player_by_ws[ws] = player_id
    player_names[player_id] = f"Player {player_id}"
    scores[player_id] = 0
    health[player_id] = MAX_HEALTH
    combo[player_id] = 0
    hit_notes[player_id] = set()
    missed_notes[player_id] = set()
    await send(ws, {"type": "welcome", "player_id": player_id})
    await broadcast({"type": "waiting", "players": len(clients)})
    print(f"Player {player_id} connected.")
    return player_id

async def unregister_player(ws):
    global match_started
    if ws in player_by_ws:
        player_id = player_by_ws.pop(ws)
        clients.remove(ws)
        print(f"Player {player_id} disconnected.")
        await broadcast({"type": "disconnect", "player_id": player_id})
        if len(clients) < MAX_PLAYERS:
            match_started = False

async def handle_connection(ws, path=None):
    if len(clients) >= MAX_PLAYERS:
        await send(ws, {"type": "error", "message": "Match is full."})
        return

    player_id = await register_player(ws)

    try:
        async for message in ws:
            data = json.loads(message)
            if data.get("type") == "join":
                player_names[player_id] = data.get("name", player_names[player_id])
                await broadcast({"type": "waiting", "players": len(clients)})
            elif data.get("type") == "input":
                result = await evaluate_hit(player_id, data.get("lane"))
                await broadcast(result)
                await broadcast_update()
                await check_game_over()
            elif data.get("type") == "ping":
                await send(ws, {"type": "pong", "time": int(time.time() * 1000)})
    except websockets.ConnectionClosed:
        pass
    finally:
        await unregister_player(ws)

async def main():
    print(f"Server starting on ws://{HOST}:{PORT}")
    async with websockets.serve(handle_connection, HOST, PORT):
        asyncio.create_task(process_misses())
        while True:
            if len(clients) == MAX_PLAYERS and not match_started:
                await asyncio.sleep(0.3)
                if len(clients) == MAX_PLAYERS and not match_started:
                    await start_match()
            await asyncio.sleep(0.1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped.")
