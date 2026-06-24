import pygame

# ==========================================
# 自动路径配置（由fix_paths.py生成）
# ==========================================
import os as _os
_BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_FONT_DIR = _os.path.join(_BASE_DIR, "assets", "fonts")
_IMG_DIR  = _os.path.join(_BASE_DIR, "assets", "images")

def _p(folder, name):
    return _os.path.join(folder, name)
import sys
import random
import os
import math

pygame.init()

GAME_WIDTH, GAME_HEIGHT = 256, 192
SCALE = 3
screen = pygame.display.set_mode((GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE))
pygame.display.set_caption("Super Mario Bros. - 图像重制版脑机接口实验")

COLOR_SKY = (92, 148, 252)       
COLOR_BRICK_MAIN = (200, 76, 12)  
COLOR_BRICK_SHADOW = (0, 0, 0)    
COLOR_BRICK_LIGHT = (252, 188, 176) 
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_GOLD = (252, 228, 160) 
COLOR_CLOUD_BLUE = (148, 212, 252) 

virtual_screen = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

FONT_PATH = _p(_FONT_DIR, "zpix.ttf") if os.path.exists(_p(_FONT_DIR, "zpix.ttf")) else None
if FONT_PATH:
    font = pygame.font.Font(FONT_PATH, 25)
    small_font = pygame.font.Font(FONT_PATH, 14)
else:
    font = pygame.font.SysFont("SimHei", 24)
    small_font = pygame.font.SysFont("SimHei", 18)

UI_TEXT_Y = 200
UI_HINT_Y = 20
UI_TEXT_COLOR = COLOR_TEXT_GOLD
UI_HINT_COLOR = COLOR_WHITE
BAR_X_OFFSET = 150
BAR_Y = 25
BAR_W = 140
BAR_H = 14

MARIO_X, MARIO_Y = 55, 116
GOOMBA_X, GOOMBA_Y = 180, 140
coin_count = 0

def load_and_scale_sprite(img_path, target_size):
    if os.path.exists(img_path):
        img = pygame.image.load(img_path).convert_alpha()
        return pygame.transform.scale(img, target_size)
    else:
        print(f"[警告] 未找到 {img_path}，已生成替代色块。")
        surf = pygame.Surface(target_size, pygame.SRCALPHA)
        surf.fill((255, 0, 0) if "mario" in img_path else (165, 66, 0))
        return surf

mario_stand = load_and_scale_sprite(_p(_IMG_DIR, "mario.png"), (36, 48))
goomba_normal = load_and_scale_sprite(_p(_IMG_DIR, "goomba.png"), (18, 18))
mario_cap = load_and_scale_sprite(_p(_IMG_DIR, "cap.png"), (14, 10))
ui_coin_img = load_and_scale_sprite(_p(_IMG_DIR, "coin.png"), (16, 16))
stage_coin_img = load_and_scale_sprite(_p(_IMG_DIR, "coin.png"), (20, 20))
goomba_flat = pygame.transform.scale(goomba_normal, (18, 6))

def draw_pixel_cloud(surface, x, y):
    cloud_surf = pygame.Surface((40, 24), pygame.SRCALPHA)
    pygame.draw.circle(cloud_surf, COLOR_BRICK_SHADOW, (12, 14), 10)
    pygame.draw.circle(cloud_surf, COLOR_BRICK_SHADOW, (24, 10), 11)
    pygame.draw.circle(cloud_surf, COLOR_BRICK_SHADOW, (32, 14), 8)
    pygame.draw.rect(cloud_surf, COLOR_BRICK_SHADOW, (8, 12, 28, 11))
    pygame.draw.circle(cloud_surf, COLOR_WHITE, (12, 14), 9)
    pygame.draw.circle(cloud_surf, COLOR_WHITE, (24, 10), 10)
    pygame.draw.circle(cloud_surf, COLOR_WHITE, (32, 14), 7)
    pygame.draw.rect(cloud_surf, COLOR_WHITE, (8, 12, 28, 10))
    pygame.draw.rect(cloud_surf, COLOR_CLOUD_BLUE, (12, 18, 20, 3))
    surface.blit(cloud_surf, (x, y))

def draw_retro_scenery(surface):
    surface.fill(COLOR_SKY)
    draw_pixel_cloud(surface, 8, 25)   
    draw_pixel_cloud(surface, 165, 30)  
    draw_pixel_cloud(surface, 195, 22)  
    for bx in range(0, GAME_WIDTH, 16):
        for by in range(156, GAME_HEIGHT, 16):
            pygame.draw.rect(surface, COLOR_BRICK_MAIN, (bx, by, 16, 16))
            pygame.draw.rect(surface, COLOR_BRICK_SHADOW, (bx, by, 16, 16), 1)
            pygame.draw.line(surface, COLOR_BRICK_LIGHT, (bx+1, by+1), (bx+14, by+1), 1)
            pygame.draw.line(surface, COLOR_BRICK_LIGHT, (bx+1, by+1), (bx+1, by+14), 1)
    surface.blit(ui_coin_img, (7, 4))
    coin_txt = small_font.render(f"x{coin_count:02d}", True, COLOR_WHITE)
    surface.blit(coin_txt, (22, 4))

def draw_progress_bar(surface, trial_idx, total_trials, block_idx, total_blocks):
    bar_x = GAME_WIDTH * SCALE - BAR_X_OFFSET
    pygame.draw.rect(surface, (40, 40, 40), (bar_x, BAR_Y, BAR_W, BAR_H), border_radius=4)
    fill_w = int(BAR_W * (trial_idx + 1) / total_trials)
    if fill_w > 0:
        pygame.draw.rect(surface, COLOR_TEXT_GOLD, (bar_x, BAR_Y, fill_w, BAR_H), border_radius=4)
    pygame.draw.rect(surface, COLOR_WHITE, (bar_x, BAR_Y, BAR_W, BAR_H), 1, border_radius=4)
    label = small_font.render(f"Block{block_idx+1}  {trial_idx+1}/{total_trials}", True, COLOR_WHITE)
    surface.blit(label, (bar_x, BAR_Y + BAR_H + 3))

def draw_centered_text(surface, text, y, color):
    surf = font.render(text, True, color)
    surface.blit(surf, (GAME_WIDTH * SCALE // 2 - surf.get_width() // 2, y))

def draw_skip_hint(surface):
    hint = small_font.render("[P] 跳过", True, (160, 160, 160))
    surface.blit(hint, (GAME_WIDTH * SCALE - hint.get_width() - 10,
                         GAME_HEIGHT * SCALE - hint.get_height() - 8))

def handle_events():
    """处理事件，返回 'quit'/'skip'/'space'/None"""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                print("[DEBUG] P key pressed - SKIP")
                return 'skip'
            if event.key == pygame.K_SPACE:
                return 'space'
    return None

def run_block_complete_screen(surface, virtual_screen, block_idx, total_blocks):
    duration_ms = 3000
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), surface)
        draw_centered_text(surface, f"Block {block_idx+1} 完成！", UI_TEXT_Y - 20, COLOR_TEXT_GOLD)
        if block_idx < total_blocks - 1:
            draw_centered_text(surface, f"还剩 {total_blocks - block_idx - 1} 个Block", UI_TEXT_Y + 40, UI_HINT_COLOR)
        else:
            draw_centered_text(surface, "实验完成，感谢参与！", UI_TEXT_Y + 40, UI_HINT_COLOR)
        draw_skip_hint(surface)
        pygame.display.flip()
        if handle_events() == 'skip':
            break

def run_rest_block(surface, virtual_screen, duration_ms=10000):
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), surface)
        draw_centered_text(surface, "【休息放空中，请放松】", UI_HINT_Y, UI_HINT_COLOR)
        remaining = (duration_ms - (pygame.time.get_ticks() - start)) // 1000 + 1
        draw_centered_text(surface, f"{remaining}", UI_TEXT_Y, COLOR_TEXT_GOLD)
        draw_skip_hint(surface)
        pygame.display.flip()
        if handle_events() == 'skip':
            break

def run_game_start_menu(surface, game_width, game_height, scale):
    in_menu = True
    clock = pygame.time.Clock()
    FONT_PATH = _p(_FONT_DIR, "zpix.ttf") if os.path.exists(_p(_FONT_DIR, "zpix.ttf")) else None
    if FONT_PATH:
        HD_FONT_TITLE = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), 50)
        HD_FONT_TEXT = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), 35)
        PIXEL_FONT_SMALL = pygame.font.Font(FONT_PATH, 12)
    else:
        HD_FONT_TITLE = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), 50)
        HD_FONT_TEXT = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), 35)
        PIXEL_FONT_SMALL = pygame.font.Font(None, 16)

    bg_img = pygame.image.load(_p(_IMG_DIR, "background.png")).convert()
    bg_img = pygame.transform.scale(bg_img, (game_width * scale, game_height * scale))
    PIXEL_FONT_SMALL = pygame.font.Font(None, 16)
    C1 = (200, 76, 12)
    C2 = (252, 216, 40)
    C3 = (255, 255, 255)
    C4 = (15, 15, 35)

    while in_menu:
        surface.blit(bg_img, (0, 0))
        title_surf = HD_FONT_TITLE.render("SUPER BCI MARIO", True, C1)
        title_shadow = HD_FONT_TITLE.render("SUPER BCI MARIO", True, C4)
        surface.blit(title_shadow, (game_width * scale // 2 - title_surf.get_width() // 2 + 4, 104))
        surface.blit(title_surf, (game_width * scale // 2 - title_surf.get_width() // 2, 100))
        blink_val = (math.sin(pygame.time.get_ticks() * 0.007) + 1) / 2
        if blink_val > 0.3:
            start_text = HD_FONT_TEXT.render("START GAME", True, C2)
            surface.blit(start_text, (game_width * scale // 2 - start_text.get_width() // 2, 240))
        hint_text = PIXEL_FONT_SMALL.render("PRESS [SPACE] TO START", True, C3)
        surface.blit(hint_text, (game_width * scale // 2 - hint_text.get_width() // 2, 450))
        pygame.display.flip()
        clock.tick(60)
        key = handle_events()
        if key == 'space':
            in_menu = False

run_game_start_menu(screen, GAME_WIDTH, GAME_HEIGHT, SCALE)

NUM_BLOCKS = 3
TOTAL_TRIALS = 20
FEEDBACK_DUR = 1500

for block_idx in range(NUM_BLOCKS):
    print(f"[BLOCK] Block {block_idx+1} 开始")
    trials = ['横'] * 10 + ['竖'] * 10
    random.shuffle(trials)

    for trial_idx, trial_type in enumerate(trials):
        print(f"[MARKER] Trial {trial_idx+1} -> {trial_type}")

        # --- 1. REST ---
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 3500:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            draw_skip_hint(screen)
            pygame.display.flip()
            if handle_events() == 'skip':
                break

        # 金币初始化
        if trial_type == '竖':
            stage_coin_x = MARIO_X + 7
            stage_coin_y = MARIO_Y - 60
        elif trial_type == '横':
            stage_coin_x = GOOMBA_X + 1
            stage_coin_y = GOOMBA_Y - 22
        else:
            stage_coin_x, stage_coin_y = -100, -100

        # --- 2. CUE ---
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 2000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            draw_centered_text(screen, f"【当前任务：{trial_type}】", UI_TEXT_Y, UI_TEXT_COLOR)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            draw_skip_hint(screen)
            pygame.display.flip()
            if handle_events() == 'skip':
                break

        # --- 3. 按空格准备 ---
        waiting_for_space = True
        while waiting_for_space:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            draw_centered_text(screen, "准备好后按 [空格键] 开始想象", UI_HINT_Y, UI_HINT_COLOR)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            draw_skip_hint(screen)
            pygame.display.flip()
            key = handle_events()
            if key in ('space', 'skip'):
                waiting_for_space = False

        # --- 4. MI ---
        print(f"[MARKER] MI START -> {trial_type}")
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 4000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            draw_skip_hint(screen)
            pygame.display.flip()
            if handle_events() == 'skip':
                break
        print(f"[MARKER] MI END -> {trial_type}")

        # --- 5. FEEDBACK ---
        anim_start = pygame.time.get_ticks()
        coin_eaten = False
        goomba_hit = False

        while pygame.time.get_ticks() - anim_start < FEEDBACK_DUR:
            progress = (pygame.time.get_ticks() - anim_start) / FEEDBACK_DUR
            draw_retro_scenery(virtual_screen)

            if trial_type == '横':
                if progress <= 0.4:
                    t = progress / 0.4
                    mario_x_now = MARIO_X + int((GOOMBA_X - MARIO_X - 20) * t * t)
                elif progress <= 0.55:
                    mario_x_now = GOOMBA_X - 20
                else:
                    t = (progress - 0.55) / 0.45
                    mario_x_now = (GOOMBA_X - 20) + int((MARIO_X - (GOOMBA_X - 20)) * t)
                virtual_screen.blit(mario_stand, (mario_x_now, MARIO_Y))
                if progress > 0.38 and not coin_eaten:
                    coin_eaten = True
                    coin_count += 1
                    goomba_hit = True
                if not coin_eaten:
                    virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
                if goomba_hit:
                    fly_t = progress - 0.38
                    goomba_fly_x = GOOMBA_X + int(120 * fly_t)
                    goomba_fly_y = GOOMBA_Y - int(80 * fly_t) + int(200 * fly_t * fly_t)
                    if goomba_fly_x < GAME_WIDTH:
                        virtual_screen.blit(goomba_flat, (goomba_fly_x, goomba_fly_y))
                    if fly_t < 0.2:
                        seed = pygame.time.get_ticks()
                        for i in range(6):
                            angle = i * (2 * math.pi / 6) + seed * 0.01
                            radius = int(fly_t * 60)
                            sx = GOOMBA_X + 9 + int(math.cos(angle) * radius)
                            sy = GOOMBA_Y + int(math.sin(angle) * radius)
                            pygame.draw.line(virtual_screen, COLOR_TEXT_GOLD, (sx-1, sy), (sx+1, sy), 1)
                            pygame.draw.line(virtual_screen, COLOR_TEXT_GOLD, (sx, sy-1), (sx, sy+1), 1)
                else:
                    virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))

            elif trial_type == '竖':
                virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
                jump_offset = int(75 * (4 * progress * (1 - progress)))
                jump_y = MARIO_Y - jump_offset
                virtual_screen.blit(mario_stand, (MARIO_X, jump_y))
                if not coin_eaten:
                    virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
                if jump_offset > 40 and not coin_eaten:
                    coin_eaten = True
                    coin_count += 1
                bullet_x = GOOMBA_X - int((GOOMBA_X + 20) * progress)
                if bullet_x > -10:
                    pygame.draw.circle(virtual_screen, (16, 16, 24), (bullet_x, GOOMBA_Y + 10), 5)
                    pygame.draw.circle(virtual_screen, (240, 240, 250), (bullet_x - 2, GOOMBA_Y + 8), 1)
            else:
                virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
                virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))

            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            draw_skip_hint(screen)
            pygame.display.flip()
            if handle_events() == 'skip':
                break

    run_block_complete_screen(screen, virtual_screen, block_idx, NUM_BLOCKS)
    if block_idx < NUM_BLOCKS - 1:
        run_rest_block(screen, virtual_screen, duration_ms=10000)

pygame.quit()
