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
WHITE   = (245, 245, 245)
BLACK   = (10, 10, 14)
CYAN    = (0, 255, 255)
MAGENTA = (255, 0, 200)
YELLOW  = (255, 230, 0)
LIME    = (0, 255, 150)
RED     = (255, 60, 90)
BLUE    = (50, 170, 255)
GRAY    = (40, 40, 50)
ORANGE  = (255, 160, 0)
PURPLE  = (170, 80, 255)

font       = pygame.font.SysFont("consolas", 24)
font_small = pygame.font.SysFont("consolas", 18)
font_big   = pygame.font.SysFont("consolas", 48)

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
    for i in range(HEIGHT):
        t = i / HEIGHT
        r = int(10 + 20 * (1 - t))
        g = int(10 + 20 * (1 - t))
        b = int(14 + 60 * t)
        pygame.draw.line(surf, (r, g, b), (0, i), (WIDTH, i))

def draw_scanlines(surf):
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(surf, (0, 0, 0, 30), (0, y), (WIDTH, y), 1)

def draw_hud_panel(surf, rect, border_color):
    x, y, w, h = rect
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
        pygame.draw.polygon(self.image, BLUE, [(0,self.height), (self.width/2, 0), (self.width, self.height)])
        pygame.draw.polygon(self.image, (100, 240, 255, 80), [(-3,self.height+2), (self.width/2, -4), (self.width+3, self.height+2)], 2)
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 30))
        self.speed = 7
        self.cooldown = 220  # ms
        self.last_shot = 0
        # Power-ups
        self.repeater_active = False
        self.buckshot_active = False
        self.repeater_ends_at = 0
        self.buckshot_ends_at = 0

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
            if self.rect.left < 0:
                self.rect.left = 0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH
        # Expire powerups
        now = pygame.time.get_ticks()
        if self.repeater_active and now >= self.repeater_ends_at:
            self.repeater_active = False
        if self.buckshot_active and now >= self.buckshot_ends_at:
            self.buckshot_active = False

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= self.cooldown

    def shoot(self, group):
        if not self.can_shoot():
            return
        if self.buckshot_active:
            for angle_deg in (-15, -7.5, 0, 7.5, 15):
                group.add(Bullet(self.rect.centerx, self.rect.top, angle_deg))
        else:
            group.add(Bullet(self.rect.centerx, self.rect.top, 0))
        self.last_shot = pygame.time.get_ticks()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle_deg=0.0):
        super().__init__()
        self.image = pygame.Surface((4, 14), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, 4, 14))
        self.rect = self.image.get_rect(midbottom=(x, y))
        speed = 12
        rad = math.radians(angle_deg)
        self.vx = speed * math.sin(rad)
        self.vy = -speed * math.cos(rad)
    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    PALETTE = [MAGENTA, LIME, CYAN]
    def __init__(self, x, y, enemy_type, speed):
        super().__init__()
        self.w, self.h = 36, 26
        self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        color = Enemy.PALETTE[enemy_type % len(Enemy.PALETTE)]
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
# Suicide Bomber (Octopus)
# =========================
class SuicideBomber(pygame.sprite.Sprite):
    """
    Red octopus that seeks the player. Spawns 2 per round starting at level 3.
    Speed scales up each level > 3.
    """
    def __init__(self, x, y, base_speed):
        super().__init__()
        self.image = self._make_octopus()
        self.rect = self.image.get_rect(center=(x, y))
        self.base_speed = base_speed
        # lateral sway for a bit of unpredictability
        self.sway_phase = random.uniform(0, math.tau)

    def _make_octopus(self):
        surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        # Head
        pygame.draw.circle(surf, RED, (18, 14), 12)
        pygame.draw.circle(surf, (255, 120, 140), (18, 14), 12, 2)
        # Eyes
        pygame.draw.circle(surf, WHITE, (13, 12), 3)
        pygame.draw.circle(surf, WHITE, (23, 12), 3)
        pygame.draw.circle(surf, BLACK, (13, 12), 1)
        pygame.draw.circle(surf, BLACK, (23, 12), 1)
        # Tentacles
        for i, dx in enumerate((-12,-6,0,6,12)):
            y = 24 + (i%2)*3
            pygame.draw.line(surf, RED, (18+dx//2, 20), (18+dx, y+10), 4)
        # Danger outline
        pygame.draw.circle(surf, (255, 0, 0, 70), (18, 14), 16, 2)
        return surf

    def update(self, player_rect, level, dt):
        # speed increases gradually past level 3
        speed = self.base_speed + 0.35 * max(0, level - 3)
        # vector toward player
        px, py = player_rect.centerx, player_rect.centery
        dx = px - self.rect.centerx
        dy = py - self.rect.centery
        dist = math.hypot(dx, dy) + 1e-6
        vx = (dx / dist) * speed
        vy = (dy / dist) * speed
        # slight sinusoidal sway on x to make dodging spicy
        sway = math.sin((pygame.time.get_ticks()/220.0) + self.sway_phase) * 0.9
        self.rect.x += int(vx + sway)
        self.rect.y += int(vy)
        # cull if far off screen
        if self.rect.top > HEIGHT + 40 or self.rect.right < -60 or self.rect.left > WIDTH + 60:
            self.kill()

# =========================
# Power-Ups
# =========================
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, ptype, x, y, fall_speed):
        super().__init__()
        self.type = ptype
        self.fall_speed = fall_speed
        self.image = self.make_icon(ptype)
        self.rect = self.image.get_rect(midtop=(x, y))
    def make_icon(self, ptype):
        surf = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255,255,255,40), (14,14), 14)
        pygame.draw.circle(surf, (255,255,255,90), (14,14), 14, 2)
        if ptype == "repeater":
            pygame.draw.polygon(surf, CYAN, [(6,9),(12,14),(6,19)], 0)
            pygame.draw.polygon(surf, CYAN, [(14,9),(20,14),(14,19)], 0)
        else:
            for px, py in [(9,18),(14,16),(19,18),(11,12),(17,12)]:
                pygame.draw.circle(surf, ORANGE, (px,py), 3)
        return surf
    def update(self):
        self.rect.y += int(self.fall_speed)
        if self.rect.top > HEIGHT:
            self.kill()

def apply_powerup(player, ptype, duration_ms=8000):
    now = pygame.time.get_ticks()
    if ptype == "repeater":
        player.repeater_active = True
        player.repeater_ends_at = now + duration_ms
    elif ptype == "buckshot":
        player.buckshot_active = True
        player.buckshot_ends_at = now + duration_ms

# =========================
# Level / Difficulty
# =========================
def enemy_params_for_level(level):
    speed = 1.8 + 0.25 * max(0, level - 1)
    speed = min(speed, 4.0)
    drop_dist = min(32, 24 + int(0.75 * (level - 1)))
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

def spawn_powerups_for_level(group):
    fast1 = random.uniform(5.0, 7.0)
    fast2 = random.uniform(5.0, 7.0)
    x1 = random.randint(30, WIDTH-30)
    x2 = random.randint(30, WIDTH-30)
    group.add(PowerUp("repeater", x1, -40, fast1))
    group.add(PowerUp("buckshot", x2, -100, fast2))

def spawn_bombers_for_level(level, bomber_group):
    """Spawn 2 red octopus bombers starting level 3."""
    if level < 3:
        return
    # Spawn near top with random x; base speed tuned for fairness at L3
    base_speed = 2.4
    for i in range(2):
        x = random.randint(40, WIDTH - 40)
        y = random.randint(-160, -40)
        bomber_group.add(SuicideBomber(x, y, base_speed))

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

powerup_group = pygame.sprite.Group()
powerups_spawned = False

bomber_group = pygame.sprite.Group()
bombers_spawned = False

score = 0
highscore = load_highscore()

edge_cooldown_ms = 300
last_edge_flip = 0

running = True
while running:
    dt = clock.tick(FPS)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            player.shoot(bullet_group)

    # Repeater: hold-to-shoot (respects cooldown)
    if player.repeater_active and keys[pygame.K_SPACE]:
        player.shoot(bullet_group)

    # Spawns per level
    if not powerups_spawned:
        spawn_powerups_for_level(powerup_group)
        powerups_spawned = True
    if not bombers_spawned:
        spawn_bombers_for_level(level, bomber_group)
        bombers_spawned = True

    # Updates
    for s in stars:
        s.update()

    player_group.update(keys)
    bullet_group.update()
    enemy_group.update(enemy_direction)
    powerup_group.update()
    for b in bomber_group:
        b.update(player.rect, level, dt)

    # Edge handling for invaders
    edge_reached = any(
        (e.rect.right >= WIDTH - 6 or e.rect.left <= 6) for e in enemy_group
    )
    now = pygame.time.get_ticks()
    if edge_reached and (now - last_edge_flip) > edge_cooldown_ms:
        enemy_direction *= -1
        for enemy in enemy_group:
            enemy.drop_down(drop_dist)
        last_edge_flip = now

    # Collisions: bullets -> enemies & bombers
    hits1 = pygame.sprite.groupcollide(enemy_group, bullet_group, True, True)
    hits2 = pygame.sprite.groupcollide(bomber_group, bullet_group, True, True)
    if hits1:
        destroyed = sum(len(v) for v in hits1.values())
        score += 10 * destroyed + (destroyed - 1) * 2
    if hits2:
        destroyed = sum(len(v) for v in hits2.values())
        score += 20 * destroyed  # bombers worth more

    # Player gets powerups
    got = pygame.sprite.spritecollide(player, powerup_group, True)
    for p in got:
        apply_powerup(player, p.type, duration_ms=8000)

    # Lose conditions: invader reaches bottom or any bomber/enemy hits player
    player_hit_by_enemy = pygame.sprite.spritecollideany(player, enemy_group)
    player_hit_by_bomber = pygame.sprite.spritecollideany(player, bomber_group)
    bottom_reached = any(e.rect.bottom >= HEIGHT - 60 for e in enemy_group)
    if player_hit_by_enemy or player_hit_by_bomber or bottom_reached:
        running = False

    # Level clear when NO invaders remain (bombers don't block progression)
    if len(enemy_group) == 0:
        level += 1
        enemy_speed, drop_dist = enemy_params_for_level(level)
        enemy_group = create_enemies(level, enemy_speed)
        enemy_direction = 1
        last_edge_flip = 0

        # reset per-level spawns
        powerup_group.empty()
        bomber_group.empty()
        powerups_spawned = False
        bombers_spawned = False

    # =========================
    # Draw
    # =========================
    draw_gradient_bg(screen)
    for s in stars:
        s.draw(screen)
    draw_scanlines(screen)

    # Entities
    player_group.draw(screen)
    bullet_group.draw(screen)
    enemy_group.draw(screen)
    bomber_group.draw(screen)
    powerup_group.draw(screen)

    # HUD
    hud_rect = (10, 10, WIDTH - 20, 108)
    draw_hud_panel(screen, hud_rect, CYAN)

    score_text = font.render(f"SCORE: {score}", True, WHITE)
    level_text = font.render(f"LEVEL: {level}", True, WHITE)
    hi_text    = font.render(f"HI: {highscore}", True, WHITE)
    screen.blit(score_text, (20, 20))
    screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, 20))
    screen.blit(hi_text, (WIDTH - hi_text.get_width() - 20, 20))

    # Power-up timers
    def seconds_left(ms_until):
        return max(0, (ms_until - pygame.time.get_ticks()) // 1000)
    px = 20
    py = 48
    if player.repeater_active:
        t = seconds_left(player.repeater_ends_at)
        screen.blit(font_small.render(f"Repeater: {t}s", True, CYAN), (px, py))
        py += 22
    if player.buckshot_active:
        t = seconds_left(player.buckshot_ends_at)
        screen.blit(font_small.render(f"Buckshot: {t}s", True, ORANGE), (px, py))
        py += 22

    # Bomber hint (from L3+)
    if level >= 3:
        screen.blit(font_small.render("Bombers Active", True, RED), (20, py))

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
