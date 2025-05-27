import pygame
import random
import sys
import os

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Screen setup
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Garrett - Space Shooter by Garrett")

# Colors
WHITE = (255, 255, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
BLUE = (50, 150, 255)
GREEN = (50, 255, 50)
BLACK = (0, 0, 0)

FPS = 60
clock = pygame.time.Clock()

# High score file
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

font = pygame.font.SysFont(None, 36)

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.width, self.height = 50, 40
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Draw a simple spaceship shape
        pygame.draw.polygon(self.image, BLUE, [(0,self.height), (self.width/2, 0), (self.width, self.height)])
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20))
        self.speed = 7

    def update(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
            if self.rect.left < 0:
                self.rect.left = 0
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = 12

    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

# Enemy class with multiple types/colors
class Enemy(pygame.sprite.Sprite):
    COLORS = [RED, GREEN, WHITE]
    def __init__(self, x, y, enemy_type, speed):
        super().__init__()
        self.width, self.height = 40, 30
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        color = Enemy.COLORS[enemy_type % len(Enemy.COLORS)]
        pygame.draw.rect(self.image, color, (0, 0, self.width, self.height))
        # Add a little decoration shape
        pygame.draw.circle(self.image, BLACK, (self.width//2, self.height//2), 7)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.type = enemy_type

    def update(self, direction):
        self.rect.x += self.speed * direction

    def drop_down(self):
        self.rect.y += 40

def create_enemies(level, enemy_speed):
    enemies = pygame.sprite.Group()
    enemy_rows = 5
    enemy_cols = 8
    enemy_spacing_x = 60
    enemy_spacing_y = 50
    start_x = (WIDTH - (enemy_cols - 1) * enemy_spacing_x) // 2
    for row in range(enemy_rows):
        for col in range(enemy_cols):
            x = start_x + col * enemy_spacing_x
            y = 50 + row * enemy_spacing_y
            enemy_type = row % 3  # Three enemy types/colors
            enemy = Enemy(x, y, enemy_type, enemy_speed)
            enemies.add(enemy)
    return enemies

# Initialize game variables
player = Player()
player_group = pygame.sprite.Group(player)
bullet_group = pygame.sprite.Group()
level = 1
enemy_speed = 2
enemy_group = create_enemies(level, enemy_speed)
enemy_direction = 1
score = 0
highscore = load_highscore()

running = True
while running:
    clock.tick(FPS)
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bullet = Bullet(player.rect.centerx, player.rect.top)
                bullet_group.add(bullet)

    # Update sprites
    player_group.update(keys)
    bullet_group.update()

    # Move enemies and check edges
    edge_reached = False
    for enemy in enemy_group:
        enemy.update(enemy_direction)
        if enemy.rect.right >= WIDTH or enemy.rect.left <= 0:
            edge_reached = True

    if edge_reached:
        enemy_direction *= -1
        for enemy in enemy_group:
            enemy.drop_down()

    # Check collisions bullet-enemy
    hits = pygame.sprite.groupcollide(enemy_group, bullet_group, True, True)
    if hits:
        score += 10 * len(hits)

    # Check enemy-player collision or enemies reach bottom
    for enemy in enemy_group:
        if enemy.rect.bottom >= HEIGHT - 50 or pygame.sprite.spritecollideany(player, enemy_group):
            running = False

    # Level up when all enemies destroyed
    if len(enemy_group) == 0:
        level += 1
        enemy_speed += 0.5
        enemy_group = create_enemies(level, enemy_speed)
        enemy_direction = 1

    # Draw everything
    screen.fill(BLACK)
    player_group.draw(screen)
    bullet_group.draw(screen)
    enemy_group.draw(screen)

    # Draw HUD
    score_text = font.render(f"Score: {score}", True, WHITE)
    level_text = font.render(f"Level: {level}", True, WHITE)
    highscore_text = font.render(f"High Score: {highscore}", True, WHITE)

    screen.blit(score_text, (10, 10))
    screen.blit(level_text, (10, 40))
    screen.blit(highscore_text, (WIDTH - highscore_text.get_width() - 10, 10))

    pygame.display.flip()

# Save highscore if beaten
save_highscore(score)

# Game over screen
screen.fill(BLACK)
game_over_text = font.render("GAME OVER", True, RED)
final_score_text = font.render(f"Final Score: {score}", True, WHITE)
screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 + 10))
pygame.display.flip()

pygame.time.wait(4000)
pygame.quit()
sys.exit()

