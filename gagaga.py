import pygame
import random
import sys
import os
import math

# =========================
# Init
# =========================
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Garrett - Space Shooter")

FPS = 60
clock = pygame.time.Clock()

# =========================
# Colors / Fonts
# =========================
# Neon-ish palette
WHITE   = (245, 245, 245)
BLACK   = (10, 10, 14)
CYAN    = (0, 255, 255)
MAGENTA = (255, 0, 200)
YELLOW  = (255, 230, 0)
LIME    = (0, 255, 150)
RED     = (255, 60, 90)
BLUE    = (50, 170, 255)
GRAY    = (40, 40, 50)

font      = pygame.font.SysFont("consolas", 24)
font_small= pygame.font.SysFont("consolas", 18)
font_big  = pygame.font.SysFont("consolas", 48)

HIGHSCORE_FILE = "highscore.txt"

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            try:
                return int(f.read())
            except:
                return 0
    return 0

def save_highscore(score):
    current = load_highscore()
    if score > current:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))

# =========================
# Background FX
# =========================
class Star:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.randrange(0, WIDTH)
        self.y = random.randrange(0, HEIGHT)
        self.speed = random.uniform(0.5, 2.2)
        self.size = random.randint(1, 2)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.x = random.randrange(0, WIDTH)
            self.y = 0
            self.speed = random.uniform(0.5, 2.2)
            self.size = random.randint(1, 2)

    def draw(self, surf):
        pygame.draw.rect(surf, (180, 220, 255), (self.x, int(self.y), self.size, self.size))

stars = [Star() for _ in range(140)]

def draw_gradient_bg(surf):
    # Vertical gradient
    for i in range(HEIGHT):
        t = i / HEIGHT
        # Dark to subtle purple/blue
        r = int(10 + 20 * (1 - t))
        g = int(10 + 20 * (1 - t))
        b = int(14 + 60 * t)
        pygame.draw.line(surf, (r, g, b), (0, i), (WIDTH, i))

def draw_scanlines(surf):
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(surf, (0, 0, 0, 30), (0, y), (WIDTH, y), 1)

def draw_hud_panel(surf, rect, border_color):
    x, y, w, h = rect
    # Fill (transparent look by blending with gradient underneath)
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((20, 20, 28, 150))
    surf.blit(panel, (x, y))
    pygame.draw.rect(surf, border_color, rect, 2)

# =========================
# Entities
# =========================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width, self.height = 40, 34
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Tri-ship with glow
        pygame.draw.polygon(self.image, BLUE, [(0,self.height), (self.width/2, 0), (self.width, self.height)])
        pygame.draw.polygon(self.image, (100, 240, 255, 80), [(-3,self.height+2), (self.width/2, -4), (self.width+3, self.height+2)], 2)
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 30))
        self.speed = 7
        self.cooldown = 220  # ms
        self.last_shot = 0

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
            if self.rect.left < 0:
                self.rect.left = 0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= self.cooldown

    def shoot(self, group):
        if self.can_shoot():
            bullet = Bullet(self.rect.centerx, self.rect.top)
            group.add(bullet)
            self.last_shot = pygame.time.get_ticks()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 14), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, 4, 14))
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = 12

    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    PALETTE = [MAGENTA, LIME, CYAN]
    def __init__(self, x, y, enemy_type, speed):
        super().__init__()
        self.w, self.h = 36, 26
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        color = Enemy.PALETTE[enemy_type % len(Enemy.PALETTE)]
        # Body + core
        pygame.draw.rect(self.image, color, (0, 0, self.w, self.h), border_radius=6)
        pygame.draw.rect(self.image, (20, 20, 30), (8, 8, self.w-16, self.h-16), border_radius=4)
        pygame.draw.circle(self.image, color, (self.w//2, self.h//2), 4)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.type = enemy_type

    def update(self, direction):
        self.rect.x += self.speed * direction

    def drop_down(self, dist):
        self.rect.y += dist

# =========================
# Level / Difficulty
# =========================
def enemy_params_for_level(level):
    """
    Gentle, capped growth:
    - Base speed 1.8; +0.25 per level (starting from level 2), capped at 4.0
    - Drop distance starts at 24px, increases slightly to prevent stalemates, but stays small
    """
    speed = 1.8 + 0.25 * max(0, level - 1)
    speed = min(speed, 4.0)  # cap
    drop_dist = min(32, 24 + int(0.75 * (level - 1)))  # very gradual
    return speed, drop_dist

def create_enemies(level, enemy_speed):
    enemies = pygame.sprite.Group()
    rows, cols = 5, 8
    spacing_x, spacing_y = 60, 50
    start_x = (WIDTH - (cols - 1) * spacing_x) // 2
    top_margin = 70
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * spacing_x
            y = top_margin + r * spacing_y
            e = Enemy(x, y, r % 3, enemy_speed)
            enemies.add(e)
    return enemies

# =========================
# Game State
# =========================
player = Player()
player_group = pygame.sprite.Group(player)
bullet_group = pygame.sprite.Group()

level = 1
enemy_speed, drop_dist = enemy_params_for_level(level)
enemy_group = create_enemies(level, enemy_speed)
enemy_direction = 1

score = 0
highscore = load_highscore()

# A tiny “edge grace” so they don’t chain-drop multiple times in quick succession
edge_cooldown_ms = 300
last_edge_flip = 0

running = True
while running:
    dt = clock.tick(FPS)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot(bullet_group)

    # Updates
    for s in stars:
        s.update()

    player_group.update(keys)
    bullet_group.update()

    # Move enemies + edge handling
    edge_reached = False
    for enemy in enemy_group:
        enemy.update(enemy_direction)
        if enemy.rect.right >= WIDTH - 6 or enemy.rect.left <= 6:
            edge_reached = True

    now = pygame.time.get_ticks()
    if edge_reached and (now - last_edge_flip) > edge_cooldown_ms:
        enemy_direction *= -1
        for enemy in enemy_group:
            enemy.drop_down(drop_dist)
        last_edge_flip = now

    # Collisions: bullets -> enemies
    hits = pygame.sprite.groupcollide(enemy_group, bullet_group, True, True)
    if hits:
        # Slight points bonus if multiple in one frame
        destroyed = sum(len(v) for v in hits.values())
        score += 10 * destroyed + (destroyed - 1) * 2

    # Player collision / lose condition
    # (Give a tiny safety margin above bottom)
    for enemy in list(enemy_group):
        if enemy.rect.bottom >= HEIGHT - 60 or pygame.sprite.spritecollideany(player, enemy_group):
            running = False
            break

    # Level clear
    if len(enemy_group) == 0:
        level += 1
        enemy_speed, drop_dist = enemy_params_for_level(level)
        enemy_group = create_enemies(level, enemy_speed)
        enemy_direction = 1
        last_edge_flip = 0

    # =========================
    # Draw
    # =========================
    draw_gradient_bg(screen)
    for s in stars:
        s.draw(screen)

    # Subtle scanline overlay
    draw_scanlines(screen)

    # Entities
    player_group.draw(screen)
    bullet_group.draw(screen)
    enemy_group.draw(screen)

    # HUD
    hud_rect = (10, 10, WIDTH - 20, 60)
    draw_hud_panel(screen, hud_rect, CYAN)
    score_text = font.render(f"SCORE: {score}", True, WHITE)
    level_text = font.render(f"LEVEL: {level}", True, WHITE)
    hi_text    = font.render(f"HI: {highscore}", True, WHITE)
    screen.blit(score_text, (20, 20))
    screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, 20))
    screen.blit(hi_text, (WIDTH - hi_text.get_width() - 20, 20))

    pygame.display.flip()

# =========================
# Game Over
# =========================
save_highscore(score)

screen.fill(BLACK)
draw_gradient_bg(screen)
for s in stars:
    s.draw(screen)
draw_scanlines(screen)

game_over_text = font_big.render("GAME OVER", True, RED)
final_score_text = font.render(f"Final Score: {score}", True, WHITE)
screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 60))
screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2))

pygame.display.flip()
pygame.time.wait(3000)
pygame.quit()
sys.exit()
