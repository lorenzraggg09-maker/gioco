import pygame
import random
import sys
import time
import math

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

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GIOCO DI MOMO E LORE")
clock = pygame.time.Clock()
FPS = 60  
fps_options = [30, 60, 120]
fps_index = 1  

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

lane_width = 70
lane_offset_left = 80
lane_offset_right = 500
hit_line_y = HEIGHT - 120
note_speed = 5
hit_window_total = 60 

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

key_map_p1 = {
    pygame.K_a: 0,
    pygame.K_s: 1,
    pygame.K_w: 2,
    pygame.K_d: 3
}

key_map_p2 = key_map

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
menu_arrows = []
for _ in range(12):
    lane = random.randint(0, 3)
    x = lane_offset_right + lane * lane_width + lane_width // 2
    y = random.randint(-600, 0)
    speed = random.uniform(2.5, 4.5)
    menu_arrows.append([lane, x, y, speed])

def draw_menu_background():
    for y in range(HEIGHT):
        color = (15, 15, 30 + y // 12)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    
    for i in range(1, 4):
        x = lane_offset_right + i * lane_width
        for y in range(0, HEIGHT, 30):
            pygame.draw.line(screen, (40, 40, 60), (x, y), (x, y + 15), 2)

    for arrow in menu_arrows:
        img = arrow_images[arrow[0]].copy()
        img.set_alpha(80) 
        rect = img.get_rect(center=(arrow[1], int(arrow[2])))
        screen.blit(img, rect)
        arrow[2] += arrow[3]
        if arrow[2] - 30 > HEIGHT:
            arrow[0] = random.randint(0, 3)
            arrow[1] = lane_offset_right + arrow[0] * lane_width + lane_width // 2
            arrow[2] = random.randint(-150, -50)
            arrow[3] = random.uniform(2.5, 4.5)

# ------------------------
# GENERAZIONE MONTAGNE PIXELATE (VETTORI FISSI)
# ------------------------
mountain_far = []
mountain_near = []

x_pop = 0
while x_pop < WIDTH + 40:
    h = random.randint(280, 380)
    mountain_far.append((x_pop, h))
    x_pop += 40

x_pop = 0
while x_pop < WIDTH + 25:
    h = random.randint(380, 460)
    mountain_near.append((x_pop, h))
    x_pop += 25

# ------------------------
# NUOVO SFONDO GIOCO: TRAMONTO IN MONTAGNA PIXELATA
# ------------------------
def draw_game_background():
    for y in range(HEIGHT):
        if y < 250:
            r = int(30 + (180 - 30) * (y / 250))
            g = int(20 + (50 - 20) * (y / 250))
            b = int(60 + (80 - 60) * (y / 250))
        else:
            factor = (y - 250) / (HEIGHT - 250)
            r = int(180 + (255 - 180) * factor)
            g = int(50 + (170 - 50) * factor)
            b = int(80 + (30 - 80) * factor)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    pygame.draw.circle(screen, (255, 210, 40), (WIDTH // 2, 380), 90)
    for sy in range(300, 470, 12):
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
    def __init__(self, lane, base_offset):
        self.lane = lane
        self.base_offset = base_offset
        self.x = base_offset + lane * lane_width + lane_width // 2
        self.y = -50

    def update(self):
        self.y += note_speed

    def draw(self):
        img = arrow_images[self.lane]
        rect = img.get_rect(center=(self.x, self.y))
        screen.blit(img, rect)

# ------------------------
# PERSONAGGIO A SINISTRA/DESTRA
# ------------------------
class Character:
    def __init__(self, image_path, base_x=120, flip=False):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (160, 200))
        if flip:
            self.image = pygame.transform.flip(self.image, True, False)
        
        self.base_x = base_x
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
                if event.key in key_map:
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

    while True:
        draw_menu_background()
        title = big_font.render("GIOCO DI MOMO E LORE", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))

        play_btn = pygame.Rect(WIDTH//2 - 120, 300, 240, 75)
        exit_btn = pygame.Rect(WIDTH//2 - 120, 400, 240, 75)

        pygame.draw.rect(screen, LIGHT_BLUE if menu_selection == 0 else BLUE, play_btn, border_radius=15)
        play_text = font.render("GIOCA", True, (0, 40, 80) if menu_selection == 0 else WHITE)
        screen.blit(play_text, (play_btn.centerx - play_text.get_width()//2, play_btn.centery - play_text.get_height()//2))

        pygame.draw.rect(screen, (255, 120, 120) if menu_selection == 1 else GRAY, exit_btn, border_radius=15)
        exit_text = font.render("ESCI", True, (80, 0, 0) if menu_selection == 1 else WHITE)
        screen.blit(exit_text, (exit_btn.centerx - exit_text.get_width()//2, exit_btn.centery - exit_text.get_height()//2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    menu_selection = (menu_selection + 1) % 2
                
                if event.key == pygame.K_RETURN:
                    if menu_selection == 0:
                        loading_screen() 
                        return 
                    elif menu_selection == 1:
                        pygame.quit()
                        sys.exit()

        pygame.display.flip()
        clock.tick(60)

# ------------------------
# GIOCO PRINCIPALE
# ------------------------
def game():
    global FPS, music_enabled, fps_index
    
    def reset_level():
        nonlocal score1, score2, health1, health2, notes_left, notes_right, hit_notes1, hit_notes2, total_notes_spawned1, total_notes_spawned2, combo_count1, combo_count2, counts1, counts2, start_time, last_beat_index, total_pause_duration, rating_timer1, rating_timer2, current_rating1, current_rating2, rating_color1, rating_color2
        score1 = 0
        score2 = 0
        health1 = 100
        health2 = 100
        notes_left = []
        notes_right = []
        hit_notes1 = 0
        hit_notes2 = 0
        total_notes_spawned1 = 0
        total_notes_spawned2 = 0
        combo_count1 = 0
        combo_count2 = 0
        counts1.update({"PERFECT": 0, "GOOD": 0, "BAD": 0, "TRASH": 0, "MISS": 0})
        counts2.update({"PERFECT": 0, "GOOD": 0, "BAD": 0, "TRASH": 0, "MISS": 0})
        start_time = pygame.time.get_ticks()
        last_beat_index = 0
        total_pause_duration = 0
        rating_timer1 = 0
        rating_timer2 = 0
        current_rating1 = ""
        current_rating2 = ""
        rating_color1 = WHITE
        rating_color2 = WHITE
        if music_loaded and music_enabled:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.play(-1)
            except: pass

    score1 = 0
    score2 = 0
    health1 = 100
    health2 = 100
    max_health = 100
    notes_left = []
    notes_right = []

    hit_notes1 = 0
    hit_notes2 = 0
    total_notes_spawned1 = 0
    total_notes_spawned2 = 0
    combo_count1 = 0
    combo_count2 = 0

    counts1 = {"PERFECT": 0, "GOOD": 0, "BAD": 0, "TRASH": 0, "MISS": 0}
    counts2 = {"PERFECT": 0, "GOOD": 0, "BAD": 0, "TRASH": 0, "MISS": 0}

    player1 = Character("goku_GIOCO.png", base_x=120, flip=False)
    player2 = Character("goku_GIOCO.png", base_x=WIDTH - 100, flip=True)

    game_over_text = big_font.render("GAME OVER", True, RED)
    final_go_x, final_go_y = WIDTH // 2, HEIGHT // 2
    go_x = WIDTH + game_over_text.get_width() 
    go_target_x = final_go_x
    animation_timer = 0

    current_rating1 = ""
    current_rating2 = ""
    rating_color1 = WHITE
    rating_color2 = WHITE
    rating_timer1 = 0
    rating_timer2 = 0
    max_rating_duration = 25 

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
                if event.key == pygame.K_RETURN:
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

                if game_state in ["PAUSED", "OPTIONS"]:
                    if event.key == pygame.K_UP:
                        if game_state == "PAUSED": pause_selection = (pause_selection - 1) % 4 
                        else: options_selection = (options_selection - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        if game_state == "PAUSED": pause_selection = (pause_selection + 1) % 4 
                        else: options_selection = (options_selection + 1) % 3

                if game_state == "OPTIONS" and options_selection == 1:
                    if event.key == pygame.K_LEFT:
                        fps_index = (fps_index - 1) % len(fps_options)
                        FPS = fps_options[fps_index]
                    elif event.key == pygame.K_RIGHT:
                        fps_index = (fps_index + 1) % len(fps_options)
                        FPS = fps_options[fps_index]

                if game_state == "PLAYING":
                    if event.key in key_map_p1:
                        lane = key_map_p1[event.key]
                        hit = False
                        for note in notes_left:
                            if note.lane == lane:
                                distance = abs(note.y - hit_line_y)
                                if distance <= hit_window_total:
                                    notes_left.remove(note)
                                    player1.dash(lane)
                                    total_notes_spawned1 += 1
                                    hit_notes1 += 1
                                    hit = True

                                    if distance <= 15:
                                        combo_count1 += 1
                                        counts1["PERFECT"] += 1
                                        current_rating1, rating_color1 = "PERFECT", GOLD
                                        score1 += 15
                                        health1 = min(max_health, health1 + 5)
                                    elif distance <= 35:
                                        combo_count1 += 1
                                        counts1["GOOD"] += 1
                                        current_rating1, rating_color1 = "GOOD", GREEN
                                        score1 += 10
                                        health1 = min(max_health, health1 + 3)
                                    else:
                                        combo_count1 = 0 
                                        counts1["BAD"] += 1
                                        current_rating1, rating_color1 = "BAD", ORANGE
                                        score1 += 2

                                    rating_timer1 = max_rating_duration 
                                    break
                        if not hit:
                            health1 -= 5
                            total_notes_spawned1 += 1
                            combo_count1 = 0 
                            counts1["TRASH"] += 1
                            current_rating1, rating_color1 = "TRASH", RED
                            rating_timer1 = max_rating_duration
                            if health1 < 0: health1 = 0

                    elif event.key in key_map_p2:
                        lane = key_map_p2[event.key]
                        hit = False
                        for note in notes_right:
                            if note.lane == lane:
                                distance = abs(note.y - hit_line_y)
                                if distance <= hit_window_total:
                                    notes_right.remove(note)
                                    player2.dash(lane)
                                    total_notes_spawned2 += 1
                                    hit_notes2 += 1
                                    hit = True

                                    if distance <= 15:
                                        combo_count2 += 1
                                        counts2["PERFECT"] += 1
                                        current_rating2, rating_color2 = "PERFECT", GOLD
                                        score2 += 15
                                        health2 = min(max_health, health2 + 5)
                                    elif distance <= 35:
                                        combo_count2 += 1
                                        counts2["GOOD"] += 1
                                        current_rating2, rating_color2 = "GOOD", GREEN
                                        score2 += 10
                                        health2 = min(max_health, health2 + 3)
                                    else:
                                        combo_count2 = 0 
                                        counts2["BAD"] += 1
                                        current_rating2, rating_color2 = "BAD", ORANGE
                                        score2 += 2

                                    rating_timer2 = max_rating_duration 
                                    break
                        if not hit:
                            health2 -= 5
                            total_notes_spawned2 += 1
                            combo_count2 = 0 
                            counts2["TRASH"] += 1
                            current_rating2, rating_color2 = "TRASH", RED
                            rating_timer2 = max_rating_duration
                            if health2 < 0: health2 = 0

        if game_state == "PLAYING":
            current_game_time = pygame.time.get_ticks() - start_time - total_pause_duration
            current_beat_index = int(current_game_time / ms_per_beat)
            
            if current_beat_index > last_beat_index:
                notes_left.append(Note(random.randint(0, 3), lane_offset_left))
                notes_right.append(Note(random.randint(0, 3), lane_offset_right))
                last_beat_index = current_beat_index

            for note in notes_left[:]:
                note.update()
                if note.y > HEIGHT:
                    notes_left.remove(note)
                    health1 -= 5 
                    total_notes_spawned1 += 1
                    combo_count1 = 0 
                    counts1["MISS"] += 1
                    current_rating1, rating_color1 = "MISS", DARK_RED
                    rating_timer1 = max_rating_duration
                    if health1 < 0: health1 = 0

            for note in notes_right[:]:
                note.update()
                if note.y > HEIGHT:
                    notes_right.remove(note)
                    health2 -= 5 
                    total_notes_spawned2 += 1
                    combo_count2 = 0 
                    counts2["MISS"] += 1
                    current_rating2, rating_color2 = "MISS", DARK_RED
                    rating_timer2 = max_rating_duration
                    if health2 < 0: health2 = 0

            player1.update()
            player2.update()
            if health1 <= 0 or health2 <= 0:
                game_state = "GAMEOVER"
                if music_loaded: pygame.mixer.music.stop()
                player1.death_y = player1.y
                player2.death_y = player2.y

        if game_state == "GAMEOVER":
            player1.update_death()
            player2.update_death()

        if game_state != "GAMEOVER":
            player1.draw()
            player2.draw()
        else:
            player1.draw_death()
            player2.draw_death()

        for note in notes_left:
            note.draw()
        for note in notes_right:
            note.draw()

        for i in range(4):
            x_right = lane_offset_right + i * lane_width + lane_width // 2
            screen.blit(arrow_images[i], arrow_images[i].get_rect(center=(x_right, hit_line_y)))
            x_left = lane_offset_left + i * lane_width + lane_width // 2
            screen.blit(arrow_images[i], arrow_images[i].get_rect(center=(x_left, hit_line_y)))

        if game_state in ["PLAYING", "PAUSED", "OPTIONS"]:
            screen.blit(font.render(f"Player 1: {score1}", True, WHITE), (10, 10))
            screen.blit(font.render(f"Player 2: {score2}", True, WHITE), (WIDTH - 220, 10))

            pygame.draw.rect(screen, GRAY, (10, 65, 200, 25), border_radius=5)
            current_bar_width1 = int((health1 / max_health) * 200)
            if current_bar_width1 > 0:
                pygame.draw.rect(screen, GREEN if health1 > 30 else RED, (10, 65, current_bar_width1, 25), border_radius=5)
            screen.blit(small_font.render(f"HP1: {health1}%", True, WHITE), (15, 40))

            pygame.draw.rect(screen, GRAY, (WIDTH - 210, 65, 200, 25), border_radius=5)
            current_bar_width2 = int((health2 / max_health) * 200)
            if current_bar_width2 > 0:
                pygame.draw.rect(screen, GREEN if health2 > 30 else RED, (WIDTH - 210, 65, current_bar_width2, 25), border_radius=5)
            screen.blit(small_font.render(f"HP2: {health2}%", True, WHITE), (WIDTH - 205, 40))

            accuracy1 = (hit_notes1 / total_notes_spawned1) * 100 if total_notes_spawned1 > 0 else 100.0
            accuracy2 = (hit_notes2 / total_notes_spawned2) * 100 if total_notes_spawned2 > 0 else 100.0
            acc_txt1 = font.render(f"A1: {accuracy1:.1f}%", True, WHITE)
            acc_txt2 = font.render(f"A2: {accuracy2:.1f}%", True, WHITE)
            screen.blit(acc_txt1, (lane_offset_left, 10))
            screen.blit(acc_txt2, (WIDTH - acc_txt2.get_width() - 10, 10))
            
            fps_display = stats_font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
            screen.blit(fps_display, (WIDTH - fps_display.get_width() - 20, 55))

            if rating_timer1 > 0:
                if game_state == "PLAYING":
                    progress1 = (max_rating_duration - rating_timer1) / 5.0
                    scale1 = 1.8 - (progress1 * 0.8) if progress1 < 1.0 else 1.0
                else: scale1 = 1.0
                base_rating_surf1 = rating_font.render(current_rating1, True, rating_color1)
                animated_rating_surf1 = pygame.transform.scale(base_rating_surf1, (int(base_rating_surf1.get_width() * scale1), int(base_rating_surf1.get_height() * scale1)))
                rating_rect1 = animated_rating_surf1.get_rect(center=(lane_offset_left + lane_width // 2, hit_line_y - 120))
                screen.blit(animated_rating_surf1, rating_rect1)
                if combo_count1 > 0 and current_rating1 in ["PERFECT", "GOOD"]:
                    base_combo_surf1 = combo_small_font.render(f"({combo_count1})", True, WHITE)
                    animated_combo_surf1 = pygame.transform.scale(base_combo_surf1, (int(base_combo_surf1.get_width() * scale1), int(base_combo_surf1.get_height() * scale1)))
                    screen.blit(animated_combo_surf1, (rating_rect1.right + 3, rating_rect1.top - 8))
                if game_state == "PLAYING": rating_timer1 -= 1

            if rating_timer2 > 0:
                if game_state == "PLAYING":
                    progress2 = (max_rating_duration - rating_timer2) / 5.0
                    scale2 = 1.8 - (progress2 * 0.8) if progress2 < 1.0 else 1.0
                else: scale2 = 1.0
                base_rating_surf2 = rating_font.render(current_rating2, True, rating_color2)
                animated_rating_surf2 = pygame.transform.scale(base_rating_surf2, (int(base_rating_surf2.get_width() * scale2), int(base_rating_surf2.get_height() * scale2)))
                rating_rect2 = animated_rating_surf2.get_rect(center=(lane_offset_right + lane_width // 2, hit_line_y - 120))
                screen.blit(animated_rating_surf2, rating_rect2)
                if combo_count2 > 0 and current_rating2 in ["PERFECT", "GOOD"]:
                    base_combo_surf2 = combo_small_font.render(f"({combo_count2})", True, WHITE)
                    animated_combo_surf2 = pygame.transform.scale(base_combo_surf2, (int(base_combo_surf2.get_width() * scale2), int(base_combo_surf2.get_height() * scale2)))
                    screen.blit(animated_combo_surf2, (rating_rect2.right + 3, rating_rect2.top - 8))
                if game_state == "PLAYING": rating_timer2 -= 1

            perfect_surf1 = stats_font.render(f"PERFECT: {counts1['PERFECT']}", True, GOLD)
            good_surf1 = stats_font.render(f"GOOD: {counts1['GOOD']}", True, GREEN)
            bad_surf1 = stats_font.render(f"BAD: {counts1['BAD']}", True, ORANGE)
            trash_surf1 = stats_font.render(f"TRASH: {counts1['TRASH']}", True, RED)
            miss_surf1 = stats_font.render(f"MISS: {counts1['MISS']}", True, DARK_RED)

            perfect_surf2 = stats_font.render(f"PERFECT: {counts2['PERFECT']}", True, GOLD)
            good_surf2 = stats_font.render(f"GOOD: {counts2['GOOD']}", True, GREEN)
            bad_surf2 = stats_font.render(f"BAD: {counts2['BAD']}", True, ORANGE)
            trash_surf2 = stats_font.render(f"TRASH: {counts2['TRASH']}", True, RED)
            miss_surf2 = stats_font.render(f"MISS: {counts2['MISS']}", True, DARK_RED)

            stats_y = hit_line_y + 38
            stats_x1 = lane_offset_left + 10
            stats_x2 = lane_offset_right + 10

            screen.blit(perfect_surf1, (stats_x1, stats_y))
            screen.blit(good_surf1, (stats_x1 + 180, stats_y))
            screen.blit(bad_surf1, (stats_x1, stats_y + 28))
            screen.blit(trash_surf1, (stats_x1 + 180, stats_y + 28))
            screen.blit(miss_surf1, (stats_x1 + 360, stats_y + 28))

            screen.blit(perfect_surf2, (stats_x2, stats_y))
            screen.blit(good_surf2, (stats_x2 + 180, stats_y))
            screen.blit(bad_surf2, (stats_x2, stats_y + 28))
            screen.blit(trash_surf2, (stats_x2 + 180, stats_y + 28))
            screen.blit(miss_surf2, (stats_x2 + 360, stats_y + 28))

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
                if animation_timer > 180: return

        pygame.display.flip()

# ------------------------
# AVVIO
# ------------------------
while True:
    menu()
    game()
