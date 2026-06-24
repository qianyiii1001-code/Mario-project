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

# ==========================================
# 1. 初始化与真像素屏幕配置
# ==========================================
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
    font = pygame.font.Font(FONT_PATH, 30)
    small_font = pygame.font.Font(FONT_PATH, 14)
else:
    font = pygame.font.SysFont("SimHei", 24)
    small_font = pygame.font.SysFont("SimHei", 18)

MARIO_X, MARIO_Y = 55, 116
GOOMBA_X, GOOMBA_Y = 180, 140
coin_count = 0

# ==========================================
# 2. 载入并处理外部像素图片
# ==========================================
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

# ==========================================
# 3. 经典 NES 场景绘制
# ==========================================
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
    draw_pixel_cloud(surface, 195, 15)  
    for bx in range(0, GAME_WIDTH, 16):
        for by in range(156, GAME_HEIGHT, 16):
            pygame.draw.rect(surface, COLOR_BRICK_MAIN, (bx, by, 16, 16))
            pygame.draw.rect(surface, COLOR_BRICK_SHADOW, (bx, by, 16, 16), 1)
            pygame.draw.line(surface, COLOR_BRICK_LIGHT, (bx+1, by+1), (bx+14, by+1), 1)
            pygame.draw.line(surface, COLOR_BRICK_LIGHT, (bx+1, by+1), (bx+1, by+14), 1)
    surface.blit(ui_coin_img, (7, 4))
    coin_txt = small_font.render(f"x{coin_count:02d}", True, (255, 255, 255))
    surface.blit(coin_txt, (22, 4))

def run_rest_block(surface, virtual_screen, duration_ms=10000):
    """block间放空休息期"""
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), surface)
        rest_txt = font.render("【休息放空中，请放松】", True, COLOR_WHITE)
        surface.blit(rest_txt, (GAME_WIDTH * SCALE // 2 - rest_txt.get_width() // 2, 20))
        remaining = (duration_ms - (pygame.time.get_ticks() - start)) // 1000 + 1
        count_txt = font.render(f"{remaining}", True, COLOR_TEXT_GOLD)
        surface.blit(count_txt, (GAME_WIDTH * SCALE // 2 - count_txt.get_width() // 2, 280))
        pygame.display.flip()
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

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
        PIXEL_FONT_SMALL = pygame.font.SysFont("SimHei", 12)

    bg_img = pygame.image.load(_p(_IMG_DIR, "background.png")).convert()
    bg_img = pygame.transform.scale(bg_img, (game_width * scale, game_height * scale))
    PIXEL_FONT_SMALL = pygame.font.SysFont("SimHei", 12)
    COLOR_BRICK_MAIN = (200, 76, 12)
    COLOR_TEXT_GOLD = (252, 216, 40)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BRICK_SHADOW = (15, 15, 35)
    virtual_surf = pygame.Surface((game_width, game_height))
    
    while in_menu:
        surface.blit(bg_img, (0, 0))
        title_surf = HD_FONT_TITLE.render("SUPER BCI MARIO", True, COLOR_BRICK_MAIN)
        title_shadow = HD_FONT_TITLE.render("SUPER BCI MARIO", True, COLOR_BRICK_SHADOW)
        surface.blit(title_shadow, (game_width * scale // 2 - title_surf.get_width() // 2 + 4, 104))
        surface.blit(title_surf, (game_width * scale // 2 - title_surf.get_width() // 2, 100))
        blink_val = (math.sin(pygame.time.get_ticks() * 0.007) + 1) / 2
        if blink_val > 0.3:
            start_text = HD_FONT_TEXT.render("START GAME", True, COLOR_TEXT_GOLD)
            surface.blit(start_text, (game_width * scale // 2 - start_text.get_width() // 2, 240))
        hint_text = PIXEL_FONT_SMALL.render("PRESS [SPACE] TO START", True, COLOR_WHITE)
        surface.blit(hint_text, (game_width * scale // 2 - hint_text.get_width() // 2, 450))
        pygame.display.flip()
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    in_menu = False

# ==========================================
# 开始菜单
# ==========================================
run_game_start_menu(screen, GAME_WIDTH, GAME_HEIGHT, SCALE)

# ==========================================
# 4. 实验主循环状态机
# ==========================================
NUM_BLOCKS = 3

for block_idx in range(NUM_BLOCKS):
    print(f"[BLOCK] Block {block_idx+1} 开始")

    trials = ['横'] * 10 + ['竖'] * 10
    random.shuffle(trials)

    for trial_idx, trial_type in enumerate(trials):
        print(f"[MARKER] Trial {trial_idx+1} -> {trial_type}")

        # --- 1. REST 放空期 ---
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 3500:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        # 金币初始化
        if trial_type == '竖':
            stage_coin_x = MARIO_X + 7
            stage_coin_y = MARIO_Y - 60
        elif trial_type == '横':
            stage_coin_x = GOOMBA_X + 1
            stage_coin_y = GOOMBA_Y - 22
        else:
            stage_coin_x, stage_coin_y = -100, -100

        # --- 2. CUE 提示期 ---
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 2000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            txt = font.render(f"【当前任务：{trial_type}】", True, COLOR_TEXT_GOLD)
            screen.blit(txt, (250, 200))
            pygame.display.flip()
            pygame.event.pump()

        # --- 3. MI 运动想象 ---
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 4000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            pygame.display.flip()
            pygame.event.pump()

        # --- waiting_for_space ---
        waiting_for_space = True
        while waiting_for_space:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            hint_txt = font.render("完成后请按 [空格键]", True, COLOR_WHITE)
            screen.blit(hint_txt, (GAME_WIDTH * SCALE // 2 - hint_txt.get_width() // 2, 20))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting_for_space = False

        # --- 4. FEEDBACK ---
        anim_start = pygame.time.get_ticks()
        coin_eaten = False

        while pygame.time.get_ticks() - anim_start < 1000:
            progress = (pygame.time.get_ticks() - anim_start) / 1000.0
            draw_retro_scenery(virtual_screen)

            if not coin_eaten and trial_type in ['横', '竖']:
                virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))

            if trial_type == '横':
                virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
                if progress <= 0.73:
                    hx = MARIO_X + 24 + int((GOOMBA_X - MARIO_X - 20) * (progress / 0.73))
                    rot_y = MARIO_Y + 8 + int(math.sin(progress * math.pi * 4) * 3)
                else:
                    bounce_prog = (progress - 0.73) / 0.27
                    hx = (GOOMBA_X + 4) - int(8 * bounce_prog)
                    rot_y = (MARIO_Y + 8) - int(4 * bounce_prog)
                virtual_screen.blit(mario_cap, (hx, rot_y))
                virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
                if progress > 0.75 and not coin_eaten:
                    coin_eaten = True
                    coin_count += 1
                if progress > 0.7:
                    if progress <= 0.78:
                        pygame.draw.line(virtual_screen, COLOR_WHITE, (GOOMBA_X - 4, GOOMBA_Y + 9), (GOOMBA_X + 22, GOOMBA_Y + 9), 2)
                        pygame.draw.line(virtual_screen, COLOR_WHITE, (GOOMBA_X + 9, GOOMBA_Y - 4), (GOOMBA_X + 9, GOOMBA_Y + 22), 2)
                        pygame.draw.rect(virtual_screen, COLOR_WHITE, (GOOMBA_X + 6, GOOMBA_Y + 6, 6, 6))
                    if progress > 0.75:
                        seed = pygame.time.get_ticks()
                        for i in range(5):
                            angle = i * (2 * math.pi / 5) + seed * 0.01
                            radius = 6 + int((progress - 0.75) * 16) + int(math.sin(seed * 0.02 + i) * 2)
                            star_x = GOOMBA_X + 9 + int(math.cos(angle) * radius)
                            star_y = GOOMBA_Y - 4 + int(math.sin(angle) * radius)
                            if i % 2 == 0:
                                pygame.draw.line(virtual_screen, COLOR_TEXT_GOLD, (star_x - 1, star_y), (star_x + 1, star_y), 1)
                                pygame.draw.line(virtual_screen, COLOR_TEXT_GOLD, (star_x, star_y - 1), (star_x, star_y + 1), 1)
                            else:
                                virtual_screen.set_at((star_x, star_y), COLOR_WHITE)

            elif trial_type == '竖':
                virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
                jump_offset = int(75 * (4 * progress * (1 - progress)))
                jump_y = MARIO_Y - jump_offset
                virtual_screen.blit(mario_stand, (MARIO_X, jump_y))
                if jump_offset > 12 and not coin_eaten:
                    coin_eaten = True
                    coin_count += 1
                bullet_x = GOOMBA_X - int((GOOMBA_X + 20) * progress)
                if bullet_x > -10:
                    pygame.draw.circle(virtual_screen, (16, 16, 24), (bullet_x, GOOMBA_Y + 10), 5)
                    pygame.draw.circle(virtual_screen, (240, 240, 250), (bullet_x - 2, GOOMBA_Y + 8), 1)

            else:
                virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))

            pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
            pygame.display.flip()
            pygame.event.pump()

    # ← for trial_idx 结束后，block间休息，最后一个block不休息
    if block_idx < NUM_BLOCKS - 1:
        run_rest_block(screen, virtual_screen, duration_ms=10000)

pygame.quit()
