import pygame
import random
import math
import os
import sys
from pathlib import Path

pygame.init()

# ============================================================
# 1. 全螢幕自適應與縮放畫布設定
# ============================================================

info = pygame.display.Info()
SCREEN_WIDTH = info.current_w if info.current_w > 0 else 405
SCREEN_HEIGHT = info.current_h if info.current_h > 0 else 720

# 開啟全螢幕模式
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("單人飛機大戰")

# 虛擬邏輯解析度 (所有遊戲物件基於此座標系繪製)
GAME_WIDTH = 405
GAME_HEIGHT = 720
canvas = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

# 座標縮放比例
SCALE_X = SCREEN_WIDTH / GAME_WIDTH
SCALE_Y = SCREEN_HEIGHT / GAME_HEIGHT

clock = pygame.time.Clock()

# ============================================================
# 顏色
# ============================================================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

RED = (255, 60, 60)
GREEN = (50, 220, 80)
BLUE = (60, 130, 255)
YELLOW = (255, 230, 50)
CYAN = (40, 230, 255)
MAGENTA = (255, 50, 220)
ORANGE = (255, 150, 30)
PURPLE = (150, 70, 230)

DARK_GRAY = (35, 35, 45)
DARK_BLUE = (10, 20, 55)

# ============================================================
# 2. 跨平台中文字型載入 (電腦與 Android 自動相容)
# ============================================================

def get_font(size, bold=True):
    # 1. 優先嘗試電腦端 (Windows / Mac) 常用字型名稱
    desktop_fonts = ["Microsoft JhengHei", "微軟正黑體", "PMingLiU", "新細明體", "PingFang TC", "Arial Unicode MS"]
    for font_name in desktop_fonts:
        try:
            f = pygame.font.SysFont(font_name, size, bold=bold)
            if f.render("測試", True, (0, 0, 0)).get_width() > 0:
                return f
        except Exception:
            pass

    # 2. 若電腦字型找不到，再嘗試 Android 系統實體檔案路徑
    android_fonts = [
        "/system/fonts/NotoSansCJK-Regular.ttc",
        "/system/fonts/NotoSansSC-Regular.otf",
        "/system/fonts/DroidSansFallback.ttf"
    ]
    for font_path in android_fonts:
        if os.path.exists(font_path):
            try:
                f = pygame.font.Font(font_path, size)
                f.set_bold(bold)
                return f
            except Exception:
                pass

    # 3. 保底方案
    return pygame.font.SysFont(None, size, bold=bold)

font = get_font(22, True)
small_font = get_font(16, True)
big_font = get_font(32, True)
huge_font = get_font(48, True)

# ============================================================
# 搖桿與技能按鈕
# ============================================================

class VirtualJoystick:
    def __init__(self, x, y, outer_radius=55, inner_radius=22):
        self.base_x = x
        self.base_y = y
        self.handle_x = x
        self.handle_y = y
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.dragging = False
        self.touch_id = None
        self.dx = 0
        self.dy = 0

    def handle_event(self, event, virtual_pos):
        is_down = False
        is_up = False
        is_motion = False

        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                return
            is_down = True
        elif event.type == pygame.FINGERUP:
            if self.touch_id == getattr(event, 'finger_id', None):
                is_up = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.touch_id == "mouse":
                is_up = True
        elif event.type == pygame.FINGERMOTION:
            if self.touch_id == getattr(event, 'finger_id', None):
                is_motion = True
        elif event.type == pygame.MOUSEMOTION:
            if self.touch_id == "mouse":
                is_motion = True

        if is_down and virtual_pos:
            if math.hypot(virtual_pos[0] - self.base_x, virtual_pos[1] - self.base_y) <= self.outer_radius:
                self.dragging = True
                self.touch_id = getattr(event, 'finger_id', 'mouse')
                self._update_position(virtual_pos)

        elif is_up:
            self.reset()

        elif is_motion and virtual_pos:
            self._update_position(virtual_pos)

    def _update_position(self, pos):
        dist = math.hypot(pos[0] - self.base_x, pos[1] - self.base_y)
        angle = math.atan2(pos[1] - self.base_y, pos[0] - self.base_x)

        if dist > self.outer_radius:
            self.handle_x = self.base_x + math.cos(angle) * self.outer_radius
            self.handle_y = self.base_y + math.sin(angle) * self.outer_radius
        else:
            self.handle_x = pos[0]
            self.handle_y = pos[1]

        self.dx = (self.handle_x - self.base_x) / self.outer_radius
        self.dy = (self.handle_y - self.base_y) / self.outer_radius

    def reset(self):
        self.dragging = False
        self.touch_id = None
        self.handle_x = self.base_x
        self.handle_y = self.base_y
        self.dx = 0
        self.dy = 0

    def draw(self, surface):
        base_surface = pygame.Surface((self.outer_radius * 2, self.outer_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(base_surface, (255, 255, 255, 40), (self.outer_radius, self.outer_radius), self.outer_radius)
        pygame.draw.circle(base_surface, (255, 255, 255, 120), (self.outer_radius, self.outer_radius), self.outer_radius, 3)
        surface.blit(base_surface, (self.base_x - self.outer_radius, self.base_y - self.outer_radius))

        pygame.draw.circle(surface, (200, 220, 255), (int(self.handle_x), int(self.handle_y)), self.inner_radius)
        pygame.draw.circle(surface, WHITE, (int(self.handle_x), int(self.handle_y)), self.inner_radius, 2)


class SkillButton:
    def __init__(self, x, y, radius=35):
        self.x = x
        self.y = y
        self.radius = radius

    def handle_event(self, event, virtual_pos, action_func):
        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                return
            if virtual_pos and math.hypot(virtual_pos[0] - self.x, virtual_pos[1] - self.y) <= self.radius:
                action_func()

    def draw(self, surface, energy_pct):
        is_ready = energy_pct >= 100
        btn_color = YELLOW if is_ready else (100, 100, 100)
        
        btn_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(btn_surface, (0, 0, 0, 120), (self.radius, self.radius), self.radius)
        pygame.draw.circle(btn_surface, btn_color, (self.radius, self.radius), self.radius, 4)
        surface.blit(btn_surface, (self.x - self.radius, self.y - self.radius))

        text = small_font.render("大絕", True, btn_color)
        surface.blit(text, text.get_rect(center=(self.x, self.y)))


joystick = VirtualJoystick(80, GAME_HEIGHT - 90)
skill_btn = SkillButton(GAME_WIDTH - 70, GAME_HEIGHT - 90)

# ============================================================
# 遊戲狀態與儲存
# ============================================================

START = 0
PLAYING = 1
PAUSE = 2
GAMEOVER = 3

game_state = START

level = 1
score = 0
level_start_score = 0

def get_safe_save_path():
    try:
        if "ANDROID_ARGUMENT" in os.environ or "PYTHON_SERVICE_ARGUMENT" in os.environ:
            private_dir = os.environ.get("ANDROID_PRIVATE", ".")
            return Path(private_dir) / "highscore.txt"
    except Exception:
        pass
    return Path.home() / ".plane_game_highscore.txt"

SAVE_FILE = get_safe_save_path()

def load_high_score():
    try:
        if SAVE_FILE.exists():
            content = SAVE_FILE.read_text(encoding="utf-8").strip()
            return max(0, int(content))
    except Exception:
        pass
    return 0

def save_high_score(high_score):
    try:
        SAVE_FILE.write_text(str(high_score), encoding="utf-8")
    except Exception:
        pass

high_score = load_high_score()

boss = None
boss_active = False

stars = [[random.randint(0, GAME_WIDTH), random.randint(0, GAME_HEIGHT), random.randint(1, 3)] for _ in range(90)]

# ============================================================
# 遊戲角色與物件類別
# ============================================================

class Player:
    def __init__(self):
        self.width = 45
        self.height = 55
        self.x = GAME_WIDTH // 2 - self.width // 2
        self.y = GAME_HEIGHT - 120
        self.max_hp = 6
        self.hp = 6
        self.speed = 6
        self.double_shot_timer = 0
        self.energy = 0
        self.shield = False
        self.invincible = 0
        self.alive = True
        self.shoot_cooldown = 0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(self, surface):
        if not self.alive or (self.invincible > 0 and (self.invincible // 5) % 2 == 0):
            return

        r = self.rect()
        pygame.draw.polygon(surface, CYAN, [(r.centerx, r.top), (r.left, r.bottom), (r.centerx, r.bottom - 15), (r.right, r.bottom)])
        pygame.draw.line(surface, WHITE, (r.left + 5, r.bottom - 12), (r.right - 5, r.bottom - 12), 3)
        pygame.draw.circle(surface, WHITE, (r.centerx, r.top + 20), 7)

        if self.shield:
            pygame.draw.circle(surface, BLUE, r.center, 35, 3)

player = Player()

class Enemy:
    def __init__(self, enemy_type):
        self.enemy_type = enemy_type
        self.width = 42
        self.height = 45
        self.x = random.randint(10, GAME_WIDTH - 50)
        self.y = random.randint(-500, -50)

        if enemy_type == 1:
            self.speed = 1.5 + level * 0.1
            self.hp = 1 + (level - 1) // 2
            self.color = RED
            self.shoot_rate = 240
        elif enemy_type == 2:
            self.speed = 2.2 + level * 0.1
            self.hp = 2 + (level - 1) // 2
            self.color = ORANGE
            self.shoot_rate = 220
        elif enemy_type == 3:
            self.speed = 1.0 + level * 0.08
            self.hp = 4 + (level - 1) // 2
            self.color = PURPLE
            self.shoot_rate = 280
        else:
            self.speed = 1.8 + level * 0.1
            self.hp = 2 + (level - 1) // 2
            self.color = GREEN
            self.shoot_rate = 260

        self.shoot_rate = max(90, self.shoot_rate - (level - 1) * 8)
        self.shoot_timer = random.randint(min(100, self.shoot_rate), self.shoot_rate)
        self.wave_offset = random.random() * 10

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self):
        if self.enemy_type == 1:
            self.y += self.speed
        elif self.enemy_type == 2:
            self.y += self.speed
            self.x += math.sin(self.y * 0.035 + self.wave_offset) * 1.5
        elif self.enemy_type == 3:
            self.y += self.speed
        elif self.enemy_type == 4:
            self.y += self.speed
            if player.alive:
                self.x += 0.7 if player.x > self.x else -0.7

        self.x = max(0, min(self.x, GAME_WIDTH - self.width))
        self.shoot_timer -= 1

        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_rate
            self.shoot()

    def shoot(self):
        if not player.alive:
            return
        dx = player.x + player.width / 2 - self.x - self.width / 2
        dy = player.y - self.y
        dist = max(1, math.sqrt(dx * dx + dy * dy))
        speed = 3.2 + min(2, (level - 1) * 0.1)
        enemy_bullets.append(EnemyBullet(self.x + self.width / 2, self.y + self.height, dx / dist * speed, dy / dist * speed))

    def draw(self, surface):
        r = self.rect()
        pygame.draw.polygon(surface, self.color, [(r.centerx, r.bottom), (r.left, r.top), (r.centerx, r.top + 12), (r.right, r.top)])
        pygame.draw.circle(surface, WHITE, r.center, 6)

class Boss:
    def __init__(self):
        self.width = 160
        self.height = 80
        self.x = GAME_WIDTH // 2 - 80
        self.y = -120
        self.max_hp = 100 + level * 30 + max(0, level - 3) * 35
        self.hp = self.max_hp
        self.direction = 1
        self.move_speed = 1.2 + min(1.2, (level - 1) * 0.08)
        self.shoot_interval = max(35, 80 - (level - 1) * 4)
        self.shoot_timer = self.shoot_interval
        self.attack_pattern = (level - 1) % 3
        self.bullet_count = min(level, 7)

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self):
        if self.y < 70:
            self.y += 1
        self.x += self.direction * self.move_speed
        if self.x <= 0: self.direction = 1
        if self.x + self.width >= GAME_WIDTH: self.direction = -1

        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_interval
            if player.alive:
                dx = player.x - self.x
                dy = player.y - self.y
                speed = 3.5 + min(2, (level - 1) * 0.12)
                aim_angle = math.atan2(dy, dx)

                if self.attack_pattern == 0:
                    angles = [aim_angle + (i - (self.bullet_count - 1) / 2) * 0.12 for i in range(self.bullet_count)]
                elif self.attack_pattern == 1:
                    angles = [aim_angle + (i - (self.bullet_count - 1) / 2) * 0.30 for i in range(self.bullet_count)]
                else:
                    count = max(5, self.bullet_count)
                    angles = [aim_angle + math.tau * i / count for i in range(count)]

                for angle in angles:
                    enemy_bullets.append(EnemyBullet(self.x + self.width / 2, self.y + self.height, math.cos(angle) * speed, math.sin(angle) * speed))

    def draw(self, surface):
        r = self.rect()
        pygame.draw.rect(surface, PURPLE, r, border_radius=15)
        pygame.draw.circle(surface, YELLOW, r.center, 18)
        pygame.draw.rect(surface, RED, (r.x + 15, r.y + 15, 30, 20))
        pygame.draw.rect(surface, RED, (r.right - 45, r.y + 15, 30, 20))

        bar_width = GAME_WIDTH - 80
        bx, by = 40, 35
        pygame.draw.rect(surface, DARK_GRAY, (bx, by, bar_width, 12))
        pygame.draw.rect(surface, RED, (bx, by, int(bar_width * self.hp / self.max_hp), 12))

class Bullet:
    def __init__(self, x, y, vx, vy, damage):
        self.x, self.y, self.vx, self.vy, self.damage = x, y, vx, vy, damage
    def rect(self): return pygame.Rect(int(self.x), int(self.y), 8, 18)
    def update(self): self.x += self.vx; self.y += self.vy
    def draw(self, surface): pygame.draw.rect(surface, YELLOW, self.rect())

class EnemyBullet:
    def __init__(self, x, y, vx, vy): self.x, self.y, self.vx, self.vy = x, y, vx, vy
    def rect(self): return pygame.Rect(int(self.x - 6), int(self.y - 6), 12, 12)
    def update(self): self.x += self.vx; self.y += self.vy
    def draw(self, surface): pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y)), 6)

class Explosion:
    def __init__(self, x, y): self.x, self.y, self.radius, self.life = x, y, 5, 18
    def update(self): self.radius += 3; self.life -= 1
    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y)), self.radius, 4)
            pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), max(1, self.radius // 2))

class Item:
    def __init__(self, x, y, item_type): self.x, self.y, self.type, self.size = x, y, item_type, 25
    def rect(self): return pygame.Rect(int(self.x), int(self.y), self.size, self.size)
    def update(self): self.y += 2
    def draw(self, surface):
        r = self.rect()
        if self.type == "coin":
            pygame.draw.circle(surface, YELLOW, r.center, 12)
            t = small_font.render("$", True, BLACK)
            surface.blit(t, t.get_rect(center=r.center))
        elif self.type == "heal":
            pygame.draw.rect(surface, GREEN, r)
            pygame.draw.rect(surface, WHITE, (r.x + 9, r.y + 3, 7, 19))
            pygame.draw.rect(surface, WHITE, (r.x + 3, r.y + 9, 19, 7))
        elif self.type == "shield":
            pygame.draw.circle(surface, BLUE, r.center, 12, 3)
        elif self.type == "weapon":
            pygame.draw.rect(surface, BLUE, r, border_radius=4)
            t = small_font.render("2", True, WHITE)
            surface.blit(t, t.get_rect(center=r.center))

# ============================================================
# 邏輯控制函數
# ============================================================

enemies, bullets, enemy_bullets, explosions, items = [], [], [], [], []

def spawn_enemy():
    etype = random.randint(1, 2) if level < 3 else (random.randint(1, 3) if level < 6 else random.randint(1, 4))
    enemies.append(Enemy(etype))

def boss_score_target(): return 300 + (level - 1) * 150
def enemy_count_for_level(): return 5 + (level - 1) * 2

def shoot_player():
    if not player.alive or player.shoot_cooldown > 0: return
    player.shoot_cooldown = 8
    angles = [-0.8, 0.8] if player.double_shot_timer > 0 else [0]
    for angle in angles:
        bullets.append(Bullet(player.x + player.width / 2, player.y, angle * 1.5, -10, 2))

def use_bomb():
    global boss, boss_active, score
    if not player.alive or player.energy < 100: return
    player.energy = 0
    score += len(enemies) * 10
    for enemy in enemies: explosions.append(Explosion(enemy.x + enemy.width / 2, enemy.y + enemy.height / 2))
    enemies.clear()
    enemy_bullets.clear()
    if boss is not None:
        boss.hp -= 40
        explosions.append(Explosion(boss.x + boss.width / 2, boss.y + boss.height / 2))
        if boss.hp <= 0:
            score += 100
            finish_boss()
            items.append(Item(GAME_WIDTH // 2, 180, "weapon"))

def damage_player():
    if not player.alive or player.invincible > 0: return
    if player.shield:
        player.shield = False
        player.invincible = 60
        return
    player.hp -= 1
    player.invincible = 90
    if player.hp <= 0:
        player.hp = 0
        player.alive = False
        explosions.append(Explosion(player.x + player.width / 2, player.y + player.height / 2))

def drop_item(x, y):
    if random.random() <= 0.25:
        items.append(Item(x, y, random.choice(["coin", "coin", "coin", "heal", "shield", "weapon"])))

def collect_item(item):
    global score
    if item.type == "coin": score += 50
    elif item.type == "heal": player.hp = min(player.hp + 2, player.max_hp)
    elif item.type == "shield": player.shield = True
    elif item.type == "weapon": player.double_shot_timer = 15 * 60

def create_boss():
    global boss, boss_active
    enemies.clear(); enemy_bullets.clear()
    boss = Boss(); boss_active = True

def finish_boss():
    global boss, boss_active, level, level_start_score
    boss = None; boss_active = False
    level += 1; level_start_score = score
    enemy_bullets.clear()
    for _ in range(enemy_count_for_level()): spawn_enemy()

def update_background():
    for star in stars:
        star[1] += star[2]
        if star[1] > GAME_HEIGHT:
            star[1] = 0; star[0] = random.randint(0, GAME_WIDTH)

def draw_background(surface):
    bg_color = DARK_BLUE if level <= 2 else ((15, 50, 35) if level <= 4 else ((50, 20, 65) if level <= 6 else (65, 20, 20)))
    surface.fill(bg_color)
    for star in stars:
        pygame.draw.circle(surface, WHITE, (star[0], int(star[1])), max(1, star[2] // 2))

def reset_game():
    global score, level, boss, boss_active, level_start_score, high_score
    high_score = load_high_score()
    score = 0; level = 1; level_start_score = 0; boss = None; boss_active = False
    enemies.clear(); bullets.clear(); enemy_bullets.clear(); explosions.clear(); items.clear()
    player.x = GAME_WIDTH // 2 - 22; player.y = GAME_HEIGHT - 120
    player.max_hp = 6; player.hp = 6; player.double_shot_timer = 0; player.energy = 0
    player.shield = False; player.invincible = 0; player.alive = True; player.shoot_cooldown = 0
    joystick.reset()
    for _ in range(enemy_count_for_level()): spawn_enemy()

# ============================================================
# 主程式迴圈
# ============================================================

reset_game()
running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        virtual_pos = None
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            virtual_pos = (event.pos[0] / SCALE_X, event.pos[1] / SCALE_Y)
        elif event.type in (pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION):
            virtual_pos = (event.x * GAME_WIDTH, event.y * GAME_HEIGHT)

        is_click = (event.type == pygame.FINGERDOWN) or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
        
        if is_click:
            if game_state in (START, GAMEOVER):
                reset_game()
                game_state = PLAYING
                continue

        if game_state == PLAYING:
            joystick.handle_event(event, virtual_pos)
            skill_btn.handle_event(event, virtual_pos, use_bomb)

    if game_state == PLAYING:
        update_background()

        if player.alive:
            player.x += joystick.dx * player.speed
            player.y += joystick.dy * player.speed
            shoot_player()

        player.x = max(0, min(player.x, GAME_WIDTH - player.width))
        player.y = max(0, min(player.y, GAME_HEIGHT - player.height))

        if player.invincible > 0: player.invincible -= 1
        if player.shoot_cooldown > 0: player.shoot_cooldown -= 1
        if player.double_shot_timer > 0: player.double_shot_timer -= 1

        if not boss_active and random.random() < (0.012 + level * 0.001):
            spawn_enemy()

        for enemy in enemies[:]:
            enemy.update()
            if enemy.y > GAME_HEIGHT + 50: enemies.remove(enemy)

        if boss: boss.update()

        for b in bullets[:]:
            b.update()
            if b.y < -40 or b.x < -50 or b.x > GAME_WIDTH + 50: bullets.remove(b)

        for eb in enemy_bullets[:]:
            eb.update()
            if eb.y > GAME_HEIGHT + 50 or eb.x < -50 or eb.x > GAME_WIDTH + 50: enemy_bullets.remove(eb)

        for b in bullets[:]:
            for enemy in enemies[:]:
                if b.rect().colliderect(enemy.rect()):
                    enemy.hp -= b.damage
                    explosions.append(Explosion(enemy.x + enemy.width / 2, enemy.y + enemy.height / 2))
                    if enemy.hp <= 0:
                        enemies.remove(enemy)
                        score += 10
                        player.energy = min(100, player.energy + 10)
                        drop_item(enemy.x, enemy.y)
                    if b in bullets: bullets.remove(b)
                    break

        if boss:
            for b in bullets[:]:
                if b.rect().colliderect(boss.rect()):
                    boss.hp -= b.damage
                    explosions.append(Explosion(b.x, b.y))
                    if b in bullets: bullets.remove(b)
                    if boss.hp <= 0:
                        explosions.append(Explosion(boss.x + boss.width / 2, boss.y + boss.height / 2))
                        score += 100
                        finish_boss()
                        items.append(Item(GAME_WIDTH // 2, 180, "weapon"))
                        break

        for enemy in enemies[:]:
            if enemy.rect().colliderect(player.rect()):
                damage_player()
                enemies.remove(enemy)
                explosions.append(Explosion(enemy.x, enemy.y))

        for eb in enemy_bullets[:]:
            if eb.rect().colliderect(player.rect()):
                damage_player()
                enemy_bullets.remove(eb)

        for item in items[:]:
            item.update()
            if item.rect().colliderect(player.rect()):
                collect_item(item)
                items.remove(item)
            elif item.y > GAME_HEIGHT: items.remove(item)

        for ex in explosions[:]:
            ex.update()
            if ex.life <= 0: explosions.remove(ex)

        if player.alive: player.energy = min(100, player.energy + 0.04)
        if not boss_active and score - level_start_score >= boss_score_target(): create_boss()
        if not player.alive: game_state = GAMEOVER

    if score > high_score:
        high_score = score
        save_high_score(high_score)

    if game_state == START:
        canvas.fill(DARK_BLUE)
        for star in stars: pygame.draw.circle(canvas, WHITE, (star[0], int(star[1])), 2)
    else:
        draw_background(canvas)

    if game_state == PLAYING:
        for enemy in enemies: enemy.draw(canvas)
        if boss: boss.draw(canvas)
        for b in bullets: b.draw(canvas)
        for eb in enemy_bullets: eb.draw(canvas)
        for item in items: item.draw(canvas)
        for ex in explosions: ex.draw(canvas)
        player.draw(canvas)

        joystick.draw(canvas)
        skill_btn.draw(canvas, player.energy)

        canvas.blit(font.render(f"分數：{score}", True, WHITE), (10, 10))
        hs_text = small_font.render(f"最高分：{high_score}", True, YELLOW)
        canvas.blit(hs_text, hs_text.get_rect(top=10, right=GAME_WIDTH - 10))
        canvas.blit(font.render(f"第 {level} 關", True, YELLOW), (GAME_WIDTH // 2 - 35, 10))
        canvas.blit(small_font.render(f"生命：{player.hp}/{player.max_hp}", True, GREEN), (10, 40))

        ds_sec = (player.double_shot_timer + 59) // 60
        canvas.blit(small_font.render(f"雙發射擊：{ds_sec} 秒" if player.double_shot_timer > 0 else "射擊模式：單發", True, WHITE), (10, 60))
        canvas.blit(small_font.render(f"大絕能量：{int(player.energy)}%", True, YELLOW), (10, 80))

        pygame.draw.rect(canvas, DARK_GRAY, (10, 102, 150, 12))
        pygame.draw.rect(canvas, YELLOW, (10, 102, int(150 * player.energy / 100), 12))

    elif game_state == START:
        title = huge_font.render("單人飛機大戰", True, CYAN)
        canvas.blit(title, title.get_rect(center=(GAME_WIDTH // 2, 150)))

        start = big_font.render("點擊螢幕開始遊戲", True, YELLOW)
        canvas.blit(start, start.get_rect(center=(GAME_WIDTH // 2, 260)))

        controls = ["左下角搖桿：控制移動", "右下角按鈕：施放大絕", "自動射擊：無需手動按鍵"]
        y = 360
        for text in controls:
            t = small_font.render(text, True, WHITE)
            canvas.blit(t, t.get_rect(center=(GAME_WIDTH // 2, y)))
            y += 35

    elif game_state == GAMEOVER:
        gameover = huge_font.render("GAME OVER", True, RED)
        canvas.blit(gameover, gameover.get_rect(center=(GAME_WIDTH // 2, 200)))
        canvas.blit(font.render(f"最終分數：{score}", True, WHITE), font.render(f"最終分數：{score}", True, WHITE).get_rect(center=(GAME_WIDTH // 2, 290)))
        canvas.blit(font.render(f"最高分：{high_score}", True, YELLOW), font.render(f"最高分：{high_score}", True, YELLOW).get_rect(center=(GAME_WIDTH // 2, 330)))
        canvas.blit(font.render(f"到達關卡：{level}", True, YELLOW), font.render(f"到達關卡：{level}", True, YELLOW).get_rect(center=(GAME_WIDTH // 2, 370)))
        canvas.blit(font.render("點擊螢幕重新開始", True, CYAN), font.render("點擊螢幕重新開始", True, CYAN).get_rect(center=(GAME_WIDTH // 2, 440)))

    scaled_surface = pygame.transform.scale(canvas, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_surface, (0, 0))

    pygame.display.flip()

save_high_score(high_score)
pygame.quit()