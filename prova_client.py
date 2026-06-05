import argparse
import asyncio
import json
import sys
import time

import pygame
import websockets


def int_keyed_dict(source):
    if not isinstance(source, dict):
        return source
    return {int(k): v for k, v in source.items()}

WIDTH, HEIGHT = 800, 600
FPS = 60
lane_width = 70
lane_offset_left = 80
lane_offset_right = 500
hit_line_y = HEIGHT - 120
note_speed_per_ms = 0.35

WHITE = (255, 255, 255)
RED = (255, 50, 50)
DARK_RED = (180, 0, 0)
GREEN = (50, 255, 50)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)
BLUE = (50, 150, 255)
GOLD = (255, 215, 0)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (100, 200, 255)
CYAN = (0, 255, 255)

key_map_p1 = {
    pygame.K_a: 0,
    pygame.K_s: 1,
    pygame.K_w: 2,
    pygame.K_d: 3,
}

key_map_p2 = {
    pygame.K_LEFT: 0,
    pygame.K_DOWN: 1,
    pygame.K_UP: 2,
    pygame.K_RIGHT: 3,
}

class Note:
    def __init__(self, lane, base_offset, spawn_time_ms, note_index):
        self.lane = lane
        self.base_offset = base_offset
        self.spawn_time_ms = spawn_time_ms
        self.note_index = note_index
        self.x = base_offset + lane * lane_width + lane_width // 2
        self.hit = False

    def y(self, current_ms):
        return -50 + max(0, current_ms - self.spawn_time_ms) * note_speed_per_ms

    def draw(self, screen, current_ms):
        if self.hit:
            return
        y = self.y(current_ms)
        if y < -80 or y > HEIGHT + 80:
            return
        img = arrow_images[self.lane]
        rect = img.get_rect(center=(self.x, int(y)))
        screen.blit(img, rect)

async def send_message(ws, message):
    await ws.send(json.dumps(message))

async def receive_messages(ws, state):
    while True:
        message = await ws.recv()
        data = json.loads(message)
        msg_type = data.get("type")
        if msg_type == "waiting":
            state["status_text"] = f"Attesa avversario: {data.get('players', 0)}/2"
        elif msg_type == "start":
            state["status_text"] = "Partita in arrivo..."
            state["bpm"] = data.get("bpm", 130)
            state["ms_per_beat"] = data.get("ms_per_beat", 60000 / state["bpm"])
            state["hit_window"] = data.get("hit_window", 120)
            state["pattern"] = data.get("pattern", [])
            state["start_time_ms"] = int(time.time() * 1000 + data.get("delay", 2000))
            state["match_started"] = True
            state["status_text"] = "Gioco in corso"
            state["notes_local"] = [Note(note["lane"], state["my_offset"], state["start_time_ms"] + note["beat"] * state["ms_per_beat"], idx) for idx, note in enumerate(state["pattern"])]
            state["notes_remote"] = [Note(note["lane"], state["remote_offset"], state["start_time_ms"] + note["beat"] * state["ms_per_beat"], idx) for idx, note in enumerate(state["pattern"])]
        elif msg_type == "update":
            state["scores"] = int_keyed_dict(data.get("scores", state["scores"]))
            state["health"] = int_keyed_dict(data.get("health", state["health"]))
            state["combo"] = int_keyed_dict(data.get("combo", state["combo"]))
        elif msg_type == "result":
            idx = data.get("note_index")
            player_id = data.get("player_id")
            if idx is not None:
                notes = state["notes_local"] if player_id == state["player_id"] else state["notes_remote"]
                for note in notes:
                    if note.note_index == idx:
                        note.hit = True
                        break
            state["last_result"] = data
        elif msg_type == "game_over":
            state["match_started"] = False
            winner = data.get("winner")
            if winner == 0:
                state["status_text"] = "Pareggio!"
            elif winner == state["player_id"]:
                state["status_text"] = "Hai vinto!"
            else:
                state["status_text"] = "Hai perso!"
            state["scores"] = int_keyed_dict(data.get("scores", state["scores"]))
            state["health"] = int_keyed_dict(data.get("health", state["health"]))
        elif msg_type == "disconnect":
            state["status_text"] = "Avversario disconnesso"

async def game_loop(ws, state):
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(FPS)
        current_ms = int(time.time() * 1000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and state["match_started"]:
                if state["player_id"] == 1 and event.key in key_map_p1:
                    lane = key_map_p1[event.key]
                    await send_message(ws, {"type": "input", "lane": lane})
                elif state["player_id"] == 2 and event.key in key_map_p2:
                    lane = key_map_p2[event.key]
                    await send_message(ws, {"type": "input", "lane": lane})

        screen.fill((12, 18, 40))
        draw_background(screen)

        if state["match_started"]:
            for note in state["notes_remote"]:
                note.draw(screen, current_ms)
            for note in state["notes_local"]:
                note.draw(screen, current_ms)

            for i in range(4):
                x_local = state["my_offset"] + i * lane_width + lane_width // 2
                x_remote = state["remote_offset"] + i * lane_width + lane_width // 2
                screen.blit(arrow_images[i], arrow_images[i].get_rect(center=(x_local, hit_line_y)))
                screen.blit(arrow_images[i], arrow_images[i].get_rect(center=(x_remote, hit_line_y)))

        draw_hud(screen, state)
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

def draw_background(screen):
    for y in range(HEIGHT):
        color = (15, 15, 20 + y // 18)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

    for x in [lane_offset_left + i * lane_width for i in range(5)]:
        for y in range(0, HEIGHT, 30):
            pygame.draw.line(screen, (40, 40, 60), (x, y), (x, y + 15), 2)
    for x in [lane_offset_right + i * lane_width for i in range(5)]:
        for y in range(0, HEIGHT, 30):
            pygame.draw.line(screen, (40, 40, 60), (x, y), (x, y + 15), 2)

    pygame.draw.circle(screen, (255, 210, 40), (WIDTH // 2, 380), 90)
    for sy in range(300, 470, 12):
        pygame.draw.line(screen, (210, 70, 60), (0, sy), (WIDTH, sy), 3)

def draw_hud(screen, state):
    info = state["status_text"]
    txt = font.render(info, True, WHITE)
    screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 14))

    player_id = state["player_id"]
    opponent_id = 2 if player_id == 1 else 1
    local_score = state["scores"].get(player_id, 0)
    local_health = state["health"].get(player_id, 0)
    remote_score = state["scores"].get(opponent_id, 0)
    remote_health = state["health"].get(opponent_id, 0)

    screen.blit(small_font.render(f"Score: {local_score}", True, WHITE), (10, 50))
    screen.blit(small_font.render(f"HP: {local_health}", True, WHITE), (10, 80))
    screen.blit(small_font.render(f"Avversario: {remote_score}", True, WHITE), (WIDTH - 260, 50))
    screen.blit(small_font.render(f"HP avv: {remote_health}", True, WHITE), (WIDTH - 260, 80))

    player_label = f"Sei giocatore {player_id}"
    screen.blit(small_font.render(player_label, True, WHITE), (10, 110))

    if state.get("last_result"):
        msg = state["last_result"]
        result = msg.get("result", "")
        screen.blit(small_font.render(f"Ultimo: {result}", True, WHITE), (10, 140))

    if state.get("match_started"):
        controls = "WASD" if player_id == 1 else "Freccia"
        screen.blit(small_font.render(f"Tasti: {controls}", True, WHITE), (10, 170))

async def main():
    parser = argparse.ArgumentParser(description="Client multiplayer online")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    args = parser.parse_args()

    server_uri = f"ws://{args.host}:{args.port}"
    name = input("Inserisci il tuo nome: ").strip() or "Giocatore"

    # INIZIALIZZAZIONE SCHERMO E GRAFICA (Spostata qui prima del caricamento delle immagini)
    pygame.init()
    pygame.font.init()
    global screen, font, small_font, arrow_images
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("GIOCO DI MOMO E LORE - Online")
    
    font = pygame.font.SysFont("arial", 30)
    small_font = pygame.font.SysFont("arial", 24)

    # Caricamento sicuro delle frecce senza convert_alpha precoce
    arrow_images = [
        pygame.image.load("freccia_sinistra.png"),
        pygame.image.load("freccia_sotto.png"),
        pygame.image.load("freccia_sopra.png"),
        pygame.image.load("freccia_destra.png"),
    ]
    for i in range(4):
        arrow_images[i] = pygame.transform.scale(arrow_images[i], (60, 60))

    state = {
        "player_id": None,
        "my_offset": lane_offset_left,
        "remote_offset": lane_offset_right,
        "scores": {1: 0, 2: 0},
        "health": {1: 100, 2: 100},
        "combo": {1: 0, 2: 0},
        "pattern": [],
        "match_started": False,
        "status_text": "Connessione in corso...",
        "notes_local": [],
        "notes_remote": [],
        "last_result": None,
    }

    try:
        async with websockets.connect(server_uri) as ws:
            await send_message(ws, {"type": "join", "name": name})
            while True:
                message = await ws.recv()
                data = json.loads(message)
                if data.get("type") == "welcome":
                    state["player_id"] = data.get("player_id")
                    if state["player_id"] == 1:
                        state["my_offset"] = lane_offset_left
                        state["remote_offset"] = lane_offset_right
                    else:
                        state["my_offset"] = lane_offset_right
                        state["remote_offset"] = lane_offset_left
                    state["status_text"] = "In attesa dell'altro giocatore..."
                    break
            receiver = asyncio.create_task(receive_messages(ws, state))
            await game_loop(ws, state)
            receiver.cancel()
    except Exception as e:
        print("Errore di connessione:", e)
        pygame.quit()
        sys.exit(1)

if __name__ == '__main__':
    async_loop = asyncio.run(main())