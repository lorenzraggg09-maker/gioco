import pygame
import random
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GIOCO DI MOMO E LORE")
clock = pygame.time.Clock()
FPS = 60

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
BLUE = (50, 150, 255)

lane_width = WIDTH // 4
hit_line_y = HEIGHT - 120
note_speed = 5
hit_window = 40

font = pygame.font.SysFont("arial", 40)
big_font = pygame.font.SysFont("arial", 50, bold=True)
small_font = pygame.font.SysFont("arial", 30)

key_map = {
    pygame.K_LEFT: 0,
    pygame.K_DOWN: 1,
    pygame.K_UP: 2,
    pygame.K_RIGHT: 3
}

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
# SFONDO MENU
# ------------------------
circles = [[random.randint(0, WIDTH),
            random.randint(0, HEIGHT),
            random.randint(30, 80)] for _ in range(8)]

def draw_menu_background():
    for y in range(HEIGHT):
        color = (40 + y // 8, 0, 80 + y // 6)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

    for circle in circles:
        pygame.draw.circle(screen, (100, 0, 200),
                           (circle[0], int(circle[1])), circle[2], 2)
        circle[1] += 0.5
        if circle[1] - circle[2] > HEIGHT:
            circle[0] = random.randint(0, WIDTH)
            circle[1] = -50

# ------------------------
# SFONDO GIOCO (STELLE)
# ------------------------
stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT)] for _ in range(50)]

def draw_game_background():
    for y in range(HEIGHT):
        color = (10, 10, 40 + y // 10)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

    for star in stars:
        pygame.draw.circle(screen, WHITE, star, 2)
        star[1] += 1
        if star[1] > HEIGHT:
            star[0] = random.randint(0, WIDTH)
            star[1] = 0

# ------------------------
# NOTE NORMALI
# ------------------------
class Note:
    def __init__(self, lane):
        self.lane = lane
        self.x = lane * lane_width + lane_width // 2
        self.y = -50

    def update(self):
        self.y += note_speed

    def draw(self):
        img = arrow_images[self.lane]
        rect = img.get_rect(center=(self.x, self.y))
        screen.blit(img, rect)

# ------------------------
# PERSONAGGIO CENTRATO (AGGIORNATO)
# ------------------------
class Character:
    def __init__(self, image_path):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (160, 200))
        self.x = WIDTH // 2
        self.y = 520
        self.base_y = self.y
        self.anim_timer = 0
        
        # Variabili per l'animazione di morte
        self.angle = 0
        self.death_y = self.y

    def animate(self):
        self.anim_timer = 10

    def update(self):
        if self.anim_timer > 0:
            self.y = self.base_y - 20
            self.anim_timer -= 1
        else:
            self.y = self.base_y

    def update_death(self):
        # Ruota il personaggio e lo fa cadere verso il basso
        self.angle += 5
        self.death_y += 4

    def draw_death(self):
        # Ruota l'immagine originale in base all'angolo corrente
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        rect = rotated_image.get_rect(midbottom=(self.x, int(self.death_y)))
        screen.blit(rotated_image, rect)

    def draw(self):
        rect = self.image.get_rect(midbottom=(self.x, self.y))
        screen.blit(self.image, rect)

# ------------------------
# MENU
# ------------------------
def menu():
    while True:
        draw_menu_background()

        title = big_font.render("GIOCO DI MOMO E LORE", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 170))

        button_rect = pygame.Rect(WIDTH//2 - 120, 350, 240, 90)
        pygame.draw.rect(screen, BLUE, button_rect, border_radius=20)

        button_text = font.render("GIOCA", True, WHITE)
        screen.blit(button_text, (
            button_rect.centerx - button_text.get_width()//2,
            button_rect.centery - button_text.get_height()//2
        ))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    return

        pygame.display.flip()
        clock.tick(FPS)

# ------------------------
# GIOCO
# ------------------------
def game():
    score = 0
    health = 100
    max_health = 100
    notes = []
    spawn_timer = 0

    hit_notes = 0
    total_notes_spawned = 0

    player = Character("goku_GIOCO.png")

    game_over_text = big_font.render("GAME OVER", True, RED)
    final_go_x = WIDTH // 2
    final_go_y = HEIGHT // 2
    go_x = WIDTH + game_over_text.get_width() 
    go_target_x = final_go_x
    animation_timer = 0

    running = True
    game_state = "PLAYING"

    while running:
        clock.tick(FPS)
        draw_game_background()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game_state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key in key_map:
                        lane = key_map[event.key]
                        hit = False

                        for note in notes:
                            if note.lane == lane and abs(note.y - hit_line_y) < hit_window:
                                notes.remove(note)
                                player.animate()
                                score += 10
                                hit_notes += 1
                                total_notes_spawned += 1
                                hit = True
                                break

                        if not hit:
                            health -= 5
                            total_notes_spawned += 1
                            if health < 0: health = 0

        if game_state == "PLAYING":
            spawn_timer += 1
            if spawn_timer > 20:
                notes.append(Note(random.randint(0, 3)))
                spawn_timer = 0

            for note in notes[:]:
                note.update()
                if note.y > HEIGHT:
                    notes.remove(note)
                    health -= 5
                    total_notes_spawned += 1
                    if health < 0: health = 0

            player.update()

            if health <= 0:
                game_state = "GAMEOVER"
                # Imposta la posizione iniziale di morte uguale alla posizione corrente
                player.death_y = player.y

        # Gestione aggiornamenti di morte
        if game_state == "GAMEOVER":
            player.update_death()

        # Disegna elementi statici e dinamici
        for i in range(4):
            x = i * lane_width + lane_width // 2
            img = arrow_images[i]
            rect = img.get_rect(center=(x, hit_line_y))
            screen.blit(img, rect)

        for note in notes:
            note.draw()
            
        # Sceglie come disegnare il giocatore in base allo stato
        if game_state == "PLAYING":
            player.draw()
        else:
            player.draw_death()

        # UI di gioco (visibile solo mentre giochi)
        if game_state == "PLAYING":
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))

            bar_width = 200
            bar_height = 25
            bar_x = 10
            bar_y = 65
            pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=5)
            health_color = GREEN if health > 30 else RED
            current_bar_width = int((health / max_health) * bar_width)
            if current_bar_width > 0:
                pygame.draw.rect(screen, health_color, (bar_x, bar_y, current_bar_width, bar_height), border_radius=5)
            health_text = small_font.render(f"HP: {health}%", True, WHITE)
            screen.blit(health_text, (bar_x + 5, bar_y - 25))

            if total_notes_spawned > 0:
                accuracy = (hit_notes / total_notes_spawned) * 100
            else:
                accuracy = 100.0
            accuracy_text = font.render(f"Accuracy: {accuracy:.1f}%", True, WHITE)
            screen.blit(accuracy_text, (WIDTH - accuracy_text.get_width() - 20, 10))

        # Animazione cinematica Game Over
        if game_state == "GAMEOVER":
            if go_x > go_target_x:
                dist_to_target = go_x - go_target_x
                current_speed = max(2, (dist_to_target * 0.1))
                go_x -= current_speed
                if go_x < go_target_x:
                    go_x = go_target_x

            rect = game_over_text.get_rect(center=(int(go_x), final_go_y))
            screen.blit(game_over_text, rect)

            if go_x <= go_target_x:
                animation_timer += 1
                if animation_timer > 180:
                    return

        pygame.display.flip()

# ------------------------
# AVVIO PROGRAMMA
# ------------------------
while True:
    menu()
    game()