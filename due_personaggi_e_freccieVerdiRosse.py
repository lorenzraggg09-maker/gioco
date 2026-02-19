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
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (50, 150, 255)
PURPLE = (120, 0, 200)

lane_width = WIDTH // 4
hit_line_y = HEIGHT - 120
note_speed = 5
hit_window = 40

font = pygame.font.SysFont("arial", 40)
big_font = pygame.font.SysFont("arial", 50, bold=True)

key_map = {
    pygame.K_LEFT: 0,
    pygame.K_DOWN: 1,
    pygame.K_UP: 2,
    pygame.K_RIGHT: 3
}

arrow_symbols = ["←", "↓", "↑", "→"]

# ------------------------
# SFONDO MENU (NUOVO)
# ------------------------
circles = [[random.randint(0, WIDTH),
            random.randint(0, HEIGHT),
            random.randint(30, 80)] for _ in range(8)]

def draw_menu_background():
    # Gradiente viola/blu
    for y in range(HEIGHT):
        color = (40 + y // 8, 0, 80 + y // 6)
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

    # Cerchi luminosi animati
    for circle in circles:
        pygame.draw.circle(screen, (100, 0, 200), (circle[0], circle[1]), circle[2], 2)
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
# NOTE
# ------------------------
class Note:
    def __init__(self, lane):
        self.lane = lane
        self.x = lane * lane_width + lane_width // 2
        self.y = -50

        rand = random.random()
        if rand < 0.1:
            self.type = 1
        elif rand < 0.2:
            self.type = 2
        else:
            self.type = 0

    def update(self):
        self.y += note_speed

    def draw(self):
        if self.type == 0:
            color = WHITE
        elif self.type == 1:
            color = GREEN
        else:
            color = RED

        text = font.render(arrow_symbols[self.lane], True, color)
        rect = text.get_rect(center=(self.x, self.y))
        screen.blit(text, rect)

# ------------------------
# PERSONAGGIO
# ------------------------
class Character:
    def __init__(self, x, image_path):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (160, 200))
        self.x = x
        self.y = 500
        self.base_y = self.y
        self.anim_timer = 0

    def animate(self):
        self.anim_timer = 10

    def update(self):
        if self.anim_timer > 0:
            self.y = self.base_y - 20
            self.anim_timer -= 1
        else:
            self.y = self.base_y

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
    notes = []
    spawn_timer = 0

    player = Character(200, "goku_GIOCO.png")
    enemy = Character(600, "goku_GIOCO.png")

    running = True
    while running:
        clock.tick(FPS)
        draw_game_background()

        spawn_timer += 1
        if spawn_timer > 20:
            notes.append(Note(random.randint(0, 3)))
            spawn_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in key_map:
                    lane = key_map[event.key]
                    hit = False

                    for note in notes:
                        if note.lane == lane and abs(note.y - hit_line_y) < hit_window:
                            notes.remove(note)
                            player.animate()
                            hit = True

                            if note.type == 0:
                                score += 10
                            elif note.type == 1:
                                health = min(100, health + 10)
                            elif note.type == 2:
                                health -= 10
                            break

                    if not hit:
                        health -= 5

        for note in notes[:]:
            note.update()
            if note.y > HEIGHT:
                notes.remove(note)
                health -= 5

        player.update()
        enemy.update()

        for i in range(4):
            x = i * lane_width + lane_width // 2
            text = font.render(arrow_symbols[i], True, (100, 255, 100))
            rect = text.get_rect(center=(x, hit_line_y))
            screen.blit(text, rect)

        for note in notes:
            note.draw()

        player.draw()
        enemy.draw()

        score_text = font.render(f"Score: {score}", True, WHITE)
        health_text = font.render(f"Health: {health}", True, WHITE)

        screen.blit(score_text, (10, 10))
        screen.blit(health_text, (10, 60))

        if health <= 0:
            game_over = big_font.render("GAME OVER", True, RED)
            screen.blit(game_over, (WIDTH//2 - game_over.get_width()//2, HEIGHT//2))
            pygame.display.flip()
            pygame.time.wait(3000)
            return

        pygame.display.flip()

# ------------------------
# AVVIO PROGRAMMA
# ------------------------
while True:
    menu()
    game()
