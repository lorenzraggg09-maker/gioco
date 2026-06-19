import json
import os
import pygame
import random
import sys
import time
import math
from datetime import datetime

pygame.init()

# Nasconde il cursore del mouse all'interno della finestra del gioco
pygame.mouse.set_visible(False)

# Inizializzazione sicura del mixer audio
music_loaded = False
music_enabled = True  
try:
    pygame.mixer.init()
    pygame.mixer.music.load("musica.mp3")
    music_loaded = True
except Exception as e:
    print("Nota: Musica non trouvata. Il gioco andrà senza audio.")

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
fullscreen = False
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("GIOCO DI MOMO E LORE")
clock = pygame.time.Clock()
FPS = 60  
fps_options = [30, 60, 120]
fps_index = 1  

menu_arrows = []
mountain_far = []
mountain_near = []
leaderboard_cache = []
leaderboard_last_refresh = None
LEADERBOARD_FILE = "leaderboard.json"


def toggle_fullscreen():
    global fullscreen, screen, WIDTH, HEIGHT
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    WIDTH, HEIGHT = screen.get_size()
    update_layout()


def update_layout():
    global WIDTH, HEIGHT, lane_width, lane_spacing, lane_group_width, lane_offset, hit_line_y
    WIDTH, HEIGHT = screen.get_size()
    lane_width = max(56, min(110, int(WIDTH * 0.08)))
    lane_spacing = max(12, int(WIDTH * 0.012))
    lane_group_width = 4 * lane_width + 3 * lane_spacing
    lane_offset = max(0, (WIDTH - lane_group_width) // 2)
    hit_line_y = int(HEIGHT * 0.84)

    menu_arrows.clear()
    for _ in range(18):
        lane = random.randint(0, 3)
        x = lane_offset + lane * (lane_width + lane_spacing) + lane_width // 2
        y = random.randint(-700, 0)
        speed = random.uniform(2.5, 5.1)
        menu_arrows.append([lane, x, y, speed])

    mountain_far.clear()
    mountain_near.clear()
    x_pop = 0
    while x_pop < WIDTH + 60:
        h = random.randint(int(HEIGHT * 0.38), int(HEIGHT * 0.58))
        mountain_far.append((x_pop, h))
        x_pop += max(32, int(WIDTH * 0.03))

    x_pop = 0
    while x_pop < WIDTH + 40:
        h = random.randint(int(HEIGHT * 0.58), int(HEIGHT * 0.78))
        mountain_near.append((x_pop, h))
        x_pop += max(22, int(WIDTH * 0.018))


update_layout()


def load_leaderboard_file():
    global leaderboard_cache
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                leaderboard_cache = sorted(
                    data,
                    key=lambda item: (item.get("score", 0), item.get("accuracy", 0)),
                    reverse=True
                )
            else:
                leaderboard_cache = []
        except Exception:
            leaderboard_cache = []
    else:
        leaderboard_cache = []
    return leaderboard_cache


def get_leaderboard():
    global leaderboard_last_refresh
    now = datetime.now()
    if leaderboard_last_refresh is None or (now - leaderboard_last_refresh).total_seconds() >= 3600:
        load_leaderboard_file()
        leaderboard_last_refresh = now
    return leaderboard_cache


def save_leaderboard_entry(score_value, accuracy_value, grade_value, difficulty_value):
    entry = {
        "score": int(score_value),
        "accuracy": round(float(accuracy_value), 1),
        "grade": grade_value,
        "difficulty": difficulty_value,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data = load_leaderboard_file()
    data.append(entry)
    data = sorted(
        data,
        key=lambda item: (item.get("score", 0), item.get("accuracy", 0)),
        reverse=True
    )[:10]
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data

# COLORI
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

lane_width = max(56, min(110, int(WIDTH * 0.08)))
lane_spacing = max(12, int(WIDTH * 0.012))
lane_group_width = 4 * lane_width + 3 * lane_spacing
lane_offset = max(0, (WIDTH - lane_group_width) // 2)
hit_line_y = int(HEIGHT * 0.84)
note_speed = 5
hit_window_total = 65

font = pygame.font.SysFont("arial", 40)
big_font = pygame.font.SysFont("arial", 50, bold=True)
small_font = pygame.font.SysFont("arial", 30)
stats_font = pygame.font.SysFont("arial", 20, bold=True)
rating_font = pygame.font.SysFont("impact", 35)
combo_small_font = pygame.font.SysFont("impact", 24)

key_map = {
    pygame.K_LEFT: 0,
    pygame.K_DOWN: 1,
    pygame.K_UP: 2,
    pygame.K_RIGHT: 3
}

difficulty_levels = {
    "easy": {"speed": 7.0, "label": "Easy"},
    "medium": {"speed": 9.0, "label": "Medium"},
    "hard": {"speed": 11.0, "label": "Hard"},
    "extreme": {"speed": 13.5, "label": "Extreme"},
    "impossible": {"speed": 16.5, "label": "Impossible"}
}

difficulty_order = list(difficulty_levels.keys())

# ------------------------
# CARICAMENTO IMMAGINI FRECCE
# ------------------------
arrow_images = [
    pygame.image.load("freccia_sinistra.png").convert_alpha(),
    pygame.image.load("freccia_sotto.png").convert_alpha(),
    pygame.image.load("freccia_sopra.png").convert_alpha(),
    pygame.image.load("freccia_destra.png").convert_alpha()
]

for i in range(4):
    arrow_images[i] = pygame.transform.scale(arrow_images[i], (60, 60))

# ------------------------
# SFONDO MENU (LIVELLO DI GAMEPLAY SCORREVOLE)
# ------------------------
def draw_menu_background():
    # Sfondo principale: gradiente pieno schermo
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT - 1)
        r = int(6 + (18 - 6) * t)
        g = int(10 + (32 - 10) * t)
        b = int(24 + (62 - 24) * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Glow centrale molto grande, per evitare il senso di sfondo "ristretto"
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for radius in range(int(min(WIDTH, HEIGHT) * 0.18), int(min(WIDTH, HEIGHT) * 0.06), -20):
        pygame.draw.circle(
            glow,
            (0, 80, 180, 12),
            (WIDTH // 2, int(HEIGHT * 0.68)),
            radius
        )
    screen.blit(glow, (0, 0))

    # Linee guida centrali, ma senza spostarle troppo a destra
    center_x = WIDTH // 2
    guide_left = center_x - int(lane_group_width * 0.5)
    for i in range(5):
        x = guide_left + i * (lane_width + lane_spacing)
        pygame.draw.line(screen, (30, 35, 65), (x, 0), (x, HEIGHT), 1)

    # Frecce animate leggermente sparse sullo sfondo
    for arrow in menu_arrows:
        img = arrow_images[arrow[0]].copy()
        img.set_alpha(50)
        rect = img.get_rect(center=(arrow[1], int(arrow[2])))
        screen.blit(img, rect)
        arrow[2] += arrow[3]
        if arrow[2] - 30 > HEIGHT:
            arrow[0] = random.randint(0, 3)
            arrow[1] = center_x - int(lane_group_width * 0.5) + arrow[0] * (lane_width + lane_spacing) + lane_width // 2
            arrow[2] = random.randint(-140, -30)
            arrow[3] = random.uniform(2.2, 4.2)

# ------------------------
# GENERAZIONE MONTAGNE PIXELATE (VETTORI FISSI)
# ------------------------
# ------------------------
# NUOVO SFONDO GIOCO: TRAMONTO IN MONTAGNA PIXELATA
# ------------------------
def draw_game_background():
    for y in range(HEIGHT):
        if y < HEIGHT * 0.35:
            r = int(30 + (180 - 30) * (y / (HEIGHT * 0.35)))
            g = int(20 + (50 - 20) * (y / (HEIGHT * 0.35)))
            b = int(60 + (80 - 60) * (y / (HEIGHT * 0.35)))
        else:
            factor = (y - HEIGHT * 0.35) / (HEIGHT - HEIGHT * 0.35)
            r = int(180 + (255 - 180) * factor)
            g = int(50 + (170 - 50) * factor)
            b = int(80 + (30 - 80) * factor)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    pygame.draw.circle(screen, (255, 210, 40), (WIDTH // 2, int(HEIGHT * 0.62)), int(min(WIDTH, HEIGHT) * 0.13))
    for sy in range(int(HEIGHT * 0.48), int(HEIGHT * 0.78), max(8, int(HEIGHT * 0.02))):
        pygame.draw.line(screen, (210, 70, 60), (0, sy), (WIDTH, sy), 3)

    for i in range(len(mountain_far) - 1):
        x1, y1 = mountain_far[i]
        x2, y2 = mountain_far[i+1]
        pygame.draw.rect(screen, (65, 30, 65), (x1, y1, x2 - x1, HEIGHT - y1))

    for i in range(len(mountain_near) - 1):
        x1, y1 = mountain_near[i]
        x2, y2 = mountain_near[i+1]
        pygame.draw.rect(screen, (35, 15, 40), (x1, y1, x2 - x1, HEIGHT - y1))

# ------------------------
# NOTE NORMALI
# ------------------------
class Note:
    def __init__(self, lane):
        self.lane = lane
        self.x = lane_offset + lane * (lane_width + lane_spacing) + lane_width // 2
        self.y = -50
        self.image = arrow_images[lane]
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.y += note_speed
        self.rect = self.image.get_rect(center=(self.x, int(self.y)))

    def draw(self):
        screen.blit(self.image, self.rect)

    def is_hit(self, target_y):
        return abs(self.rect.centery - target_y) <= hit_window_total

# ------------------------
# PERSONAGGIO A DESTRA, RIVOLTO VERSO SINISTRA
# ------------------------
class Character:
    def __init__(self, image_path):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (160, 200))
        # Specchia l'immagine orizzontalmente (flip)
        self.image = pygame.transform.flip(self.image, True, False)
        
        # Posizione a sinistra della schermata
        self.base_x = 120  # 120 pixel dal bordo sinistro
        self.base_y = 520
        self.x = self.base_x
        self.y = self.base_y
        
        self.offset_x = 0
        self.offset_y = 0
        self.return_speed = 4  

        self.angle = 0
        self.death_y = self.base_y

    def dash(self, direction):
        if direction == 0:    self.offset_x = -40
        elif direction == 1:  self.offset_y = 40
        elif direction == 2:  self.offset_y = -40
        elif direction == 3:  self.offset_x = 40

    def update(self):
        if self.offset_x > 0: self.offset_x = max(0, self.offset_x - self.return_speed)
        if self.offset_x < 0: self.offset_x = min(0, self.offset_x + self.return_speed)
        if self.offset_y > 0: self.offset_y = max(0, self.offset_y - self.return_speed)
        if self.offset_y < 0: self.offset_y = min(0, self.offset_y + self.return_speed)

        self.x = self.base_x + self.offset_x
        self.y = self.base_y + self.offset_y

    def update_death(self):
        self.angle += 5
        self.death_y += 4

    def draw_death(self):
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        rect = rotated_image.get_rect(midbottom=(self.base_x, int(self.death_y)))
        screen.blit(rotated_image, rect)

    def draw(self):
        rect = self.image.get_rect(midbottom=(int(self.x), int(self.y)))
        screen.blit(self.image, rect)

# ------------------------
# SCHERMATA DI CARICAMENTO INTERATTIVA
# ------------------------
def loading_screen():
    progress = 0
    loading_texts = [
        "Caricamento risorse...",
        "Generazione delle frecce...",
        "Sintonizzazione tracce audio...",
        "Riscaldamento di Goku...",
        "Preparazione del palco...",
        "Riscalda i pollici premendo le frecce!"
    ]
    current_text = loading_texts[0]
    text_timer = 0

    interactive_target_lane = random.randint(0, 3)
    score_mini_game = 0

    while progress < 100:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif event.key in key_map:
                    if key_map[event.key] == interactive_target_lane:
                        score_mini_game += 1
                        interactive_target_lane = random.randint(0, 3)

        progress += random.uniform(0.4, 1.2)
        if progress > 100:
            progress = 100

        text_timer += 1
        if text_timer % 50 == 0 and progress < 90:
            current_text = random.choice(loading_texts)

        for y in range(HEIGHT):
            color = (15, 15, 25 + y // 18)
            pygame.draw.line(screen, color, (0, y), (WIDTH, y))

        hint_text = stats_font.render("MINIGIOCO DI RISCALDAMENTO: premi la freccia corretta!", True, GOLD)
        screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT // 2 - 120))

        arrow_img = arrow_images[interactive_target_lane]
        arrow_rect = arrow_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        screen.blit(arrow_img, arrow_rect)

        mini_score_txt = stats_font.render(f"Frecce colpite: {score_mini_game}", True, GREEN)
        screen.blit(mini_score_txt, (WIDTH // 2 - mini_score_txt.get_width() // 2, HEIGHT // 2 + 30))

        bar_width = 600
        bar_height = 24
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = HEIGHT - 80  

        load_title = stats_font.render("CARICAMENTO IN CORSO...", True, CYAN)
        screen.blit(load_title, (bar_x, bar_y - 28))

        pct_text = stats_font.render(f"{int(progress)}%", True, WHITE)
        screen.blit(pct_text, (bar_x + bar_width - pct_text.get_width(), bar_y - 28))

        pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=6)
        current_bar_width = int((progress / 100) * bar_width)
        if current_bar_width > 0:
            pygame.draw.rect(screen, BLUE, (bar_x, bar_y, current_bar_width, bar_height), border_radius=6)
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=6)

        sub_text = stats_font.render(current_text, True, GRAY)
        screen.blit(sub_text, (WIDTH // 2 - sub_text.get_width() // 2, bar_y + bar_height + 10))

        pygame.display.flip()
        clock.tick(60)
        time.sleep(0.015)

# ------------------------
# MENU PRINCIPALE
# ------------------------
def menu():
    menu_selection = 0
    leaderboard_open = False

    while True:
        draw_menu_background()
        title = big_font.render("GIOCO DI MOMO E LORE", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))

        if leaderboard_open:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            panel = pygame.Rect(WIDTH//2 - 360, HEIGHT//2 - 240, 720, 480)
            pygame.draw.rect(screen, DARK_GRAY, panel, border_radius=18)
            pygame.draw.rect(screen, GOLD, panel, width=3, border_radius=18)

            board_title = big_font.render("CLASSIFICA", True, GOLD)
            screen.blit(board_title, (panel.centerx - board_title.get_width()//2, panel.y + 18))

            entries = get_leaderboard()
            y = panel.y + 90
            for i, entry in enumerate(entries[:8]):
                rank = f"{i+1}."
                rank_surf = stats_font.render(rank, True, WHITE)
                score_surf = stats_font.render(f"{entry.get('score', 0)}", True, WHITE)
                acc_surf = stats_font.render(f"{entry.get('accuracy', 0):.1f}%", True, WHITE)
                grade_surf = stats_font.render(entry.get('grade', '-'), True, GOLD)
                diff_surf = stats_font.render(entry.get('difficulty', '-'), True, CYAN)
                time_surf = stats_font.render(entry.get('timestamp', ''), True, GRAY)

                screen.blit(rank_surf, (panel.x + 30, y))
                screen.blit(score_surf, (panel.x + 90, y))
                screen.blit(acc_surf, (panel.x + 210, y))
                screen.blit(grade_surf, (panel.x + 330, y))
                screen.blit(diff_surf, (panel.x + 400, y))
                screen.blit(time_surf, (panel.x + 520, y))
                y += 48

            if not entries:
                empty_text = font.render("Nessun risultato ancora", True, WHITE)
                screen.blit(empty_text, (panel.centerx - empty_text.get_width()//2, panel.centery))

            exit_hint = stats_font.render("Premi ESC per tornare", True, WHITE)
            screen.blit(exit_hint, (panel.centerx - exit_hint.get_width()//2, panel.bottom - 35))
        else:
            play_btn = pygame.Rect(WIDTH//2 - 120, 300, 240, 75)
            leaderboard_btn = pygame.Rect(WIDTH//2 - 160, 395, 320, 75)
            exit_btn = pygame.Rect(WIDTH//2 - 120, 490, 240, 75)

            pygame.draw.rect(screen, LIGHT_BLUE if menu_selection == 0 else BLUE, play_btn, border_radius=15)
            play_text = font.render("GIOCA", True, (0, 40, 80) if menu_selection == 0 else WHITE)
            screen.blit(play_text, (play_btn.centerx - play_text.get_width()//2, play_btn.centery - play_text.get_height()//2))

            pygame.draw.rect(screen, LIGHT_BLUE if menu_selection == 1 else BLUE, leaderboard_btn, border_radius=15)
            board_text = font.render("CLASSIFICA", True, (0, 40, 80) if menu_selection == 1 else WHITE)
            screen.blit(board_text, (leaderboard_btn.centerx - board_text.get_width()//2, leaderboard_btn.centery - board_text.get_height()//2))

            pygame.draw.rect(screen, (255, 120, 120) if menu_selection == 2 else GRAY, exit_btn, border_radius=15)
            exit_text = font.render("ESCI", True, (80, 0, 0) if menu_selection == 2 else WHITE)
            screen.blit(exit_text, (exit_btn.centerx - exit_text.get_width()//2, exit_btn.centery - exit_text.get_height()//2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif leaderboard_open:
                    if event.key == pygame.K_ESCAPE:
                        leaderboard_open = False
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    menu_selection = (menu_selection + 1) % 3
                elif event.key == pygame.K_RETURN:
                    if menu_selection == 0:
                        loading_screen()
                        return
                    elif menu_selection == 1:
                        leaderboard_open = True
                    elif menu_selection == 2:
                        pygame.quit()
                        sys.exit()

        pygame.display.flip()
        clock.tick(60)

# ------------------------
# GIOCO PRINCIPALE
# ------------------------
def game():
    global FPS, music_enabled, fps_index, note_speed

    difficulty_index = 1
    difficulty = difficulty_order[difficulty_index]
    note_speed = difficulty_levels[difficulty]["speed"]
    
    def reset_level():
        nonlocal score, health, notes, hit_notes, total_notes_spawned, combo_count, counts, start_time, last_beat_index, total_pause_duration, rating_timer, current_rating, game_over_selection, show_game_over_menu, animation_timer, go_x, level_time_expired
        score = 0
        health = 100
        notes = []
        hit_notes = 0
        total_notes_spawned = 0
        combo_count = 0
        counts.update({"PERFECT": 0, "GOOD": 0, "BAD": 0, "TRASH": 0, "MISS": 0})
        start_time = pygame.time.get_ticks()
        last_beat_index = 0
        total_pause_duration = 0
        rating_timer = 0
        current_rating = ""
        game_over_selection = 0
        show_game_over_menu = False
        animation_timer = 0
        go_x = WIDTH + game_over_text.get_width()
        level_time_expired = False
        if music_loaded and music_enabled:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.play(-1)
            except: pass

    # Schermata di selezione difficoltà prima di iniziare
    selecting_difficulty = True
    while selecting_difficulty:
        clock.tick(FPS)
        draw_game_background()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title = big_font.render("SELEZIONA DIFFICOLTÀ", True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 180))

        for i, name in enumerate(difficulty_order):
            y = HEIGHT // 2 - 80 + i * 60
            rect = pygame.Rect(WIDTH // 2 - 140, y, 280, 48)
            selected = i == difficulty_index
            pygame.draw.rect(screen, LIGHT_BLUE if selected else BLUE, rect, border_radius=12)
            label = small_font.render(difficulty_levels[name]["label"], True, (0, 40, 80) if selected else WHITE)
            screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif event.key == pygame.K_UP:
                    difficulty_index = (difficulty_index - 1) % len(difficulty_order)
                elif event.key == pygame.K_DOWN:
                    difficulty_index = (difficulty_index + 1) % len(difficulty_order)
                elif event.key == pygame.K_RETURN:
                    difficulty = difficulty_order[difficulty_index]
                    note_speed = difficulty_levels[difficulty]["speed"]
                    selecting_difficulty = False
                elif event.key == pygame.K_ESCAPE:
                    return

        difficulty = difficulty_order[difficulty_index]
        note_speed = difficulty_levels[difficulty]["speed"]
        pygame.display.flip()

    score = 0
    health = 100
    max_health = 100
    notes = []

    hit_notes = 0
    total_notes_spawned = 0
    combo_count = 0

    counts = {"PERFECT": 0, "GOOD": 0, "BAD": 0, "TRASH": 0, "MISS": 0}

    player = Character("goku_GIOCO.png")

    game_over_text = big_font.render("GAME OVER", True, RED)
    final_go_x, final_go_y = WIDTH // 2, HEIGHT // 2
    go_x = WIDTH + game_over_text.get_width() 
    go_target_x = final_go_x
    animation_timer = 0
    game_over_selection = 0
    show_game_over_menu = False
    leaderboard_saved = False

    current_rating = ""
    rating_color = WHITE
    rating_timer = 0
    max_rating_duration = 25
    level_duration_seconds = 90
    level_time_expired = False

    if music_loaded and music_enabled:
        try: pygame.mixer.music.play(-1)
        except: pass

    BPM = 130  
    ms_per_beat = (60 / BPM) * 1000  
    start_time = pygame.time.get_ticks()
    last_beat_index = 0 
    
    pause_time_start = 0
    total_pause_duration = 0
    
    pause_selection = 0
    options_selection = 0

    btn_1 = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 - 100, 320, 50) 
    btn_2 = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 - 40,  320, 50) 
    btn_3 = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 20,  320, 50) 
    btn_4 = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 80,  320, 50) 

    running = True
    game_state = "PLAYING" 

    while running:
        clock.tick(FPS)
        draw_game_background()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if music_loaded: pygame.mixer.music.stop()
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif event.key == pygame.K_RETURN:
                    if game_state == "PLAYING":
                        game_state = "PAUSED"
                        pause_selection = 0 
                        pause_time_start = pygame.time.get_ticks()
                        if music_loaded: pygame.mixer.music.pause()
                    elif game_state == "PAUSED":
                        if pause_selection == 0: 
                            game_state = "PLAYING"
                            total_pause_duration += pygame.time.get_ticks() - pause_time_start
                            if music_loaded and music_enabled: pygame.mixer.music.unpause()
                        elif pause_selection == 1: 
                            reset_level()
                            game_state = "PLAYING"
                        elif pause_selection == 2: 
                            game_state = "OPTIONS"
                            options_selection = 0
                        elif pause_selection == 3: 
                            if music_loaded: pygame.mixer.music.stop()
                            return 
                    elif game_state == "OPTIONS":
                        if options_selection == 0: 
                            music_enabled = not music_enabled
                            if music_loaded:
                                if not music_enabled: pygame.mixer.music.stop()
                                else: pygame.mixer.music.play(-1)
                        elif options_selection == 2: 
                            game_state = "PAUSED"
                            pause_selection = 2
                    elif game_state in ["GAMEOVER", "LEVEL_FINISHED"] and show_game_over_menu:
                        if game_over_selection == 0:
                            reset_level()
                            game_state = "PLAYING"
                            show_game_over_menu = False
                            if music_loaded and music_enabled:
                                try:
                                    pygame.mixer.music.stop()
                                    pygame.mixer.music.play(-1)
                                except: pass
                        elif game_over_selection == 1:
                            if music_loaded: pygame.mixer.music.stop()
                            return

                if game_state in ["PAUSED", "OPTIONS"]:
                    if event.key == pygame.K_UP:
                        if game_state == "PAUSED": pause_selection = (pause_selection - 1) % 4 
                        else: options_selection = (options_selection - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        if game_state == "PAUSED": pause_selection = (pause_selection + 1) % 4 
                        else: options_selection = (options_selection + 1) % 3
                elif game_state in ["GAMEOVER", "LEVEL_FINISHED"] and show_game_over_menu:
                    if event.key == pygame.K_UP:
                        game_over_selection = (game_over_selection - 1) % 2
                    elif event.key == pygame.K_DOWN:
                        game_over_selection = (game_over_selection + 1) % 2

                if game_state == "OPTIONS" and options_selection == 1:
                    if event.key == pygame.K_LEFT:
                        fps_index = (fps_index - 1) % len(fps_options)
                        FPS = fps_options[fps_index]
                    elif event.key == pygame.K_RIGHT:
                        fps_index = (fps_index + 1) % len(fps_options)
                        FPS = fps_options[fps_index]

                if game_state == "PLAYING" and event.key in key_map:
                    lane = key_map[event.key]
                    hit = False
                    for note in notes:
                        if note.lane == lane and note.is_hit(hit_line_y):
                            distance = abs(note.rect.centery - hit_line_y)
                            notes.remove(note)
                            player.dash(lane)
                            total_notes_spawned += 1
                            hit_notes += 1
                            hit = True

                            if distance <= 15:
                                combo_count += 1
                                counts["PERFECT"] += 1
                                current_rating, rating_color = "PERFECT", GOLD
                                score += 15
                                health = min(max_health, health + 5)
                            elif distance <= 35:
                                combo_count += 1
                                counts["GOOD"] += 1
                                current_rating, rating_color = "GOOD", GREEN
                                score += 10
                                health = min(max_health, health + 3)
                            else:
                                combo_count = 0
                                counts["BAD"] += 1
                                current_rating, rating_color = "BAD", ORANGE
                                score += 2

                            rating_timer = max_rating_duration
                            break
                    if not hit:
                        health -= 5
                        total_notes_spawned += 1
                        combo_count = 0
                        counts["TRASH"] += 1
                        current_rating, rating_color = "TRASH", RED
                        rating_timer = max_rating_duration
                        if health < 0: health = 0

        if game_state == "PLAYING":
            current_game_time = pygame.time.get_ticks() - start_time - total_pause_duration
            if current_game_time >= level_duration_seconds * 1000:
                game_state = "LEVEL_FINISHED"
                if music_loaded: pygame.mixer.music.stop()
            else:
                current_beat_index = int(current_game_time / ms_per_beat)
                
                if current_beat_index > last_beat_index:
                    notes.append(Note(random.randint(0, 3)))
                    last_beat_index = current_beat_index

                for note in notes[:]:
                    note.update()
                    if note.y > HEIGHT:
                        notes.remove(note)
                        health -= 5 
                        total_notes_spawned += 1
                        combo_count = 0 
                        counts["MISS"] += 1
                        current_rating, rating_color = "MISS", DARK_RED
                        rating_timer = max_rating_duration
                        if health < 0: health = 0

                player.update()
                if health <= 0:
                    game_state = "GAMEOVER"
                    if music_loaded: pygame.mixer.music.stop()
                    player.death_y = player.y

        if game_state == "GAMEOVER":
            player.update_death()

        if game_state == "LEVEL_FINISHED":
            if not level_time_expired:
                level_time_expired = True
            show_game_over_menu = True

        for i in range(4):
            x = lane_offset + i * (lane_width + lane_spacing) + lane_width // 2
            screen.blit(arrow_images[i], arrow_images[i].get_rect(center=(x, hit_line_y)))

        for note in notes: note.draw()
        if game_state != "GAMEOVER": player.draw()
        else: player.draw_death()

        if game_state in ["PLAYING", "PAUSED", "OPTIONS"]:
            screen.blit(font.render(f"Score: {score}", True, WHITE), (10, 10))

            if game_state == "PLAYING":
                elapsed_ms = pygame.time.get_ticks() - start_time - total_pause_duration
                remaining_seconds = max(0, level_duration_seconds - int(elapsed_ms / 1000))
                mins = remaining_seconds // 60
                secs = remaining_seconds % 60
                timer_text = f"Tempo: {mins:02d}:{secs:02d}"
                timer_surf = font.render(timer_text, True, WHITE)
                screen.blit(timer_surf, (WIDTH // 2 - timer_surf.get_width() // 2, 10))

            pygame.draw.rect(screen, GRAY, (10, 65, 200, 25), border_radius=5)
            current_bar_width = int((health / max_health) * 200)
            if current_bar_width > 0:
                pygame.draw.rect(screen, GREEN if health > 30 else RED, (10, 65, current_bar_width, 25), border_radius=5)
            screen.blit(small_font.render(f"HP: {health}%", True, WHITE), (15, 40))

            total_judgments = max(1, total_notes_spawned)
            weighted_score = (
                counts["PERFECT"] * 100 +
                counts["GOOD"] * 92 +
                counts["BAD"] * 70 +
                counts["TRASH"] * 35 +
                counts["MISS"] * 0
            )
            accuracy = (weighted_score / (total_judgments * 100)) * 100 if total_judgments > 0 else 100.0
            acc_txt = font.render(f"Accuracy: {accuracy:.1f}%", True, WHITE)
            screen.blit(acc_txt, (WIDTH - acc_txt.get_width() - 20, 10))
            
            fps_display = stats_font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
            screen.blit(fps_display, (WIDTH - fps_display.get_width() - 20, 55))

            if rating_timer > 0:
                if game_state == "PLAYING":
                    progress = (max_rating_duration - rating_timer) / 5.0
                    scale = 1.8 - (progress * 0.8) if progress < 1.0 else 1.0
                else: scale = 1.0
                
                base_rating_surf = rating_font.render(current_rating, True, rating_color)
                animated_rating_surf = pygame.transform.scale(base_rating_surf, (int(base_rating_surf.get_width() * scale), int(base_rating_surf.get_height() * scale)))
                rating_rect = animated_rating_surf.get_rect(center=(lane_offset + lane_width // 2, hit_line_y - 120))
                screen.blit(animated_rating_surf, rating_rect)
                
                if combo_count > 0 and current_rating in ["PERFECT", "GOOD"]:
                    base_combo_surf = combo_small_font.render(f"({combo_count})", True, WHITE)
                    animated_combo_surf = pygame.transform.scale(base_combo_surf, (int(base_combo_surf.get_width() * scale), int(base_combo_surf.get_height() * scale)))
                    screen.blit(animated_combo_surf, (rating_rect.right + 3, rating_rect.top - 8))
                if game_state == "PLAYING": rating_timer -= 1

            perfect_surf = stats_font.render(f"PERFECT: {counts['PERFECT']}", True, GOLD)
            good_surf = stats_font.render(f"GOOD: {counts['GOOD']}", True, GREEN)
            bad_surf = stats_font.render(f"BAD: {counts['BAD']}", True, ORANGE)
            trash_surf = stats_font.render(f"TRASH: {counts['TRASH']}", True, RED)
            miss_surf = stats_font.render(f"MISS: {counts['MISS']}", True, DARK_RED)

            stats_x = lane_offset + 10
            stats_y = hit_line_y + 38
            screen.blit(perfect_surf, (stats_x, stats_y))
            screen.blit(good_surf, (stats_x + 180, stats_y))

            second_row_y = stats_y + 28
            screen.blit(bad_surf, (stats_x, second_row_y))
            screen.blit(trash_surf, (stats_x + 180, second_row_y))
            screen.blit(miss_surf, (stats_x + 360, second_row_y))

        if game_state == "PAUSED":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            
            pause_title = big_font.render("PAUSA", True, CYAN)
            screen.blit(pause_title, (WIDTH//2 - pause_title.get_width()//2, HEIGHT//2 - 160))
            
            pygame.draw.rect(screen, LIGHT_BLUE if pause_selection == 0 else BLUE, btn_1, border_radius=12)
            txt_1 = small_font.render("Riprendi", True, (0, 40, 80) if pause_selection == 0 else WHITE)
            screen.blit(txt_1, (btn_1.centerx - txt_1.get_width()//2, btn_1.centery - txt_1.get_height()//2))
            
            pygame.draw.rect(screen, LIGHT_BLUE if pause_selection == 1 else BLUE, btn_2, border_radius=12)
            txt_2 = small_font.render("Start Over", True, (0, 40, 80) if pause_selection == 1 else WHITE)
            screen.blit(txt_2, (btn_2.centerx - txt_2.get_width()//2, btn_2.centery - txt_2.get_height()//2))
            
            pygame.draw.rect(screen, LIGHT_BLUE if pause_selection == 2 else BLUE, btn_3, border_radius=12)
            txt_3 = small_font.render("Opzioni", True, (0, 40, 80) if pause_selection == 2 else WHITE)
            screen.blit(txt_3, (btn_3.centerx - txt_3.get_width()//2, btn_3.centery - txt_3.get_height()//2))
            
            pygame.draw.rect(screen, (255, 120, 120) if pause_selection == 3 else GRAY, btn_4, border_radius=12)
            txt_4 = small_font.render("Torna alla schermata di titolo", True, (80, 0, 0) if pause_selection == 3 else WHITE)
            screen.blit(txt_4, (btn_4.centerx - txt_4.get_width()//2, btn_4.centery - txt_4.get_height()//2))

        elif game_state == "OPTIONS":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            opt_title = big_font.render("OPZIONI", True, GOLD)
            screen.blit(opt_title, (WIDTH//2 - opt_title.get_width()//2, HEIGHT//2 - 130))
            
            btn_opt1 = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 - 60, 320, 55)
            btn_opt2 = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 10, 320, 55)
            btn_opt3 = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 80, 320, 55)

            pygame.draw.rect(screen, LIGHT_BLUE if options_selection == 0 else BLUE, btn_opt1, border_radius=15)
            status_music = "ON" if music_enabled else "OFF"
            txt_opt1 = small_font.render(f"Musica: {status_music}", True, (0, 40, 80) if options_selection == 0 else WHITE)
            
            pygame.draw.rect(screen, LIGHT_BLUE if options_selection == 1 else BLUE, btn_opt2, border_radius=15)
            txt_opt2 = small_font.render(f"< FPS: {FPS} >", True, (0, 40, 80) if options_selection == 1 else WHITE)
            
            pygame.draw.rect(screen, (255, 200, 100) if options_selection == 2 else GRAY, btn_opt3, border_radius=15)
            txt_opt3 = small_font.render("Indietro", True, (80, 40, 0) if options_selection == 2 else WHITE)
            
            screen.blit(txt_opt1, (btn_opt1.centerx - txt_opt1.get_width()//2, btn_opt1.centery - txt_opt1.get_height()//2))
            screen.blit(txt_opt2, (btn_opt2.centerx - txt_opt2.get_width()//2, btn_opt2.centery - txt_opt2.get_height()//2))
            screen.blit(txt_opt3, (btn_opt3.centerx - txt_opt3.get_width()//2, btn_opt3.centery - txt_opt3.get_height()//2))

        if game_state == "GAMEOVER":
            if go_x > go_target_x:
                go_x -= max(2, ((go_x - go_target_x) * 0.1))
                if go_x < go_target_x: go_x = go_target_x
            rect = game_over_text.get_rect(center=(int(go_x), final_go_y))
            screen.blit(game_over_text, rect)
            if go_x <= go_target_x:
                animation_timer += 1
                if animation_timer > 180:
                    show_game_over_menu = True

        if game_state in ["GAMEOVER", "LEVEL_FINISHED"] and show_game_over_menu:
            if not leaderboard_saved:
                final_accuracy = (hit_notes / total_notes_spawned) * 100 if total_notes_spawned > 0 else 0.0
                if final_accuracy >= 98:
                    grade, grade_color, grade_desc = "Z", (255, 215, 0), "Sei IL Maestro"
                elif final_accuracy >= 95:
                    grade, grade_color, grade_desc = "S", (255, 215, 0), "Sei Spettacolare!"
                elif final_accuracy >= 90:
                    grade, grade_color, grade_desc = "A", (0, 230, 255), "Niente Male"
                elif final_accuracy >= 80:
                    grade, grade_color, grade_desc = "B", (0, 200, 120), "Benino"
                elif final_accuracy >= 70:
                    grade, grade_color, grade_desc = "C", (140, 220, 255), "Non Male Ma Nemmeno Bene"
                elif final_accuracy >= 60:
                    grade, grade_color, grade_desc = "D", (255, 180, 80), "Male"
                else:
                    grade, grade_color, grade_desc = "F", (255, 80, 80), "Terribile"
                save_leaderboard_entry(score, final_accuracy, grade, difficulty_levels[difficulty]["label"])
                leaderboard_saved = True

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            end_title = "TEMPO SCADUTO" if game_state == "LEVEL_FINISHED" else "SEI MORTO"
            menu_title = big_font.render(end_title, True, RED)
            screen.blit(menu_title, (WIDTH // 2 - menu_title.get_width() // 2, HEIGHT // 2 - 180))

            final_accuracy = (hit_notes / total_notes_spawned) * 100 if total_notes_spawned > 0 else 0.0
            if final_accuracy >= 98:
                grade, grade_color, grade_desc = "Z", (255, 215, 0), "Sei IL Maestro"
            elif final_accuracy >= 95:
                grade, grade_color, grade_desc = "S", (255, 215, 0), "Sei Spettacolare!"
            elif final_accuracy >= 90:
                grade, grade_color, grade_desc = "A", (0, 230, 255), "Niente Male"
            elif final_accuracy >= 80:
                grade, grade_color, grade_desc = "B", (0, 200, 120), "Benino"
            elif final_accuracy >= 70:
                grade, grade_color, grade_desc = "C", (140, 220, 255), "Non Male Ma Nemmeno Bene"
            elif final_accuracy >= 60:
                grade, grade_color, grade_desc = "D", (255, 180, 80), "Male"
            else:
                grade, grade_color, grade_desc = "F", (255, 80, 80), "Terribile"

            acc_text = big_font.render(f"Percentuale: {final_accuracy:.1f}%", True, WHITE)
            screen.blit(acc_text, (WIDTH // 2 - acc_text.get_width() // 2, HEIGHT // 2 - 110))

            grade_text = big_font.render(f"Voto: {grade}", True, grade_color)
            screen.blit(grade_text, (WIDTH // 2 - grade_text.get_width() // 2, HEIGHT // 2 - 50))

            grade_desc_text = small_font.render(grade_desc, True, grade_color)
            screen.blit(grade_desc_text, (WIDTH // 2 - grade_desc_text.get_width() // 2, HEIGHT // 2 - 10))

            btn_retry = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 40, 320, 55)
            btn_exit = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 110, 320, 55)

            pygame.draw.rect(screen, LIGHT_BLUE if game_over_selection == 0 else BLUE, btn_retry, border_radius=15)
            retry_text = small_font.render("Rifai il livello", True, (0, 40, 80) if game_over_selection == 0 else WHITE)
            screen.blit(retry_text, (btn_retry.centerx - retry_text.get_width() // 2, btn_retry.centery - retry_text.get_height() // 2))

            pygame.draw.rect(screen, (255, 120, 120) if game_over_selection == 1 else GRAY, btn_exit, border_radius=15)
            exit_text = small_font.render("Esci", True, (80, 0, 0) if game_over_selection == 1 else WHITE)
            screen.blit(exit_text, (btn_exit.centerx - exit_text.get_width() // 2, btn_exit.centery - exit_text.get_height() // 2))

        pygame.display.flip()

# ------------------------
# AVVIO
# ------------------------
while True:
    menu()
    game()
