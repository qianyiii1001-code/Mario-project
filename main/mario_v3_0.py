# 在v2版本基础上增加了
# -横向：改为马里奥横向跑，冲撞goomba
# -进度条，trial之间的说明，跳过键
import pygame

from pylsl import StreamInfo, StreamOutlet

# 创建LSL marker流
info = StreamInfo('MarkerStream', 'Markers', 1, 0, 'string', 'mario_bci')
outlet = StreamOutlet(info)

# ==========================================
# 自动路径配置（由fix_paths.py生成）
# ==========================================
import os as _os
_BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_FONT_DIR = _os.path.join(_BASE_DIR, "assets", "fonts")
_IMG_DIR  = _os.path.join(_BASE_DIR, "assets", "images")
_SND_DIR  = _os.path.join(_BASE_DIR, "assets", "sounds")

def _p(folder, name):
    return _os.path.join(folder, name)
import sys
import random
import os
import math

pygame.init()
pygame.font.init()
pygame.mixer.init()


def safe_sysfont(name, size):
    try:
        return pygame.font.SysFont(name, size)
    except Exception:
        return pygame.font.Font(None, size)


GAME_WIDTH, GAME_HEIGHT = 256, 192
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_W, SCREEN_H = screen.get_size()

# SCALE 仍然用整数，保持像素风不模糊
SCALE = min(SCREEN_W // GAME_WIDTH, SCREEN_H // GAME_HEIGHT)

# 算出居中偏移量（黑边放两侧/上下）
OFFSET_X = (SCREEN_W - GAME_WIDTH * SCALE) // 2
OFFSET_Y = (SCREEN_H - GAME_HEIGHT * SCALE) // 2
GAME_RECT = pygame.Rect(OFFSET_X, OFFSET_Y, GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)

COLOR_SKY = (92, 148, 252)
COLOR_BRICK_MAIN = (200, 76, 12)
COLOR_BRICK_SHADOW = (0, 0, 0)
COLOR_BRICK_LIGHT = (252, 188, 176)
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_GOLD = (252, 228, 160)
COLOR_CLOUD_BLUE = (148, 212, 252)

virtual_screen = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

FONT_SCALE = SCALE / 3.0  # 基准 SCALE=3 时字体为设计尺寸

FONT_PATH = _p(_FONT_DIR, "zpix.ttf") if os.path.exists(_p(_FONT_DIR, "zpix.ttf")) else None
if FONT_PATH:
    font = pygame.font.Font(FONT_PATH, int(25 * FONT_SCALE))
    small_font = pygame.font.Font(FONT_PATH, int(14 * FONT_SCALE))
    coin_font = pygame.font.Font(FONT_PATH, int(9 * FONT_SCALE))
else:
    font = safe_sysfont("SimHei", int(24 * FONT_SCALE))
    small_font = safe_sysfont("SimHei", int(18 * FONT_SCALE))
    coin_font = safe_sysfont("SimHei", int(18 * FONT_SCALE))

UI_TEXT_Y = GAME_HEIGHT + int(8 * FONT_SCALE)   # 游戏区下方，随字号缩放
UI_HINT_Y = int(10 * FONT_SCALE)                 # 游戏区内顶部
UI_TEXT_COLOR = COLOR_TEXT_GOLD
UI_HINT_COLOR = COLOR_WHITE
BAR_X_OFFSET = 150
BAR_Y = 25
BAR_W = 140
BAR_H = 14

MARIO_X, MARIO_Y = 55, 116
GOOMBA_X, GOOMBA_Y = 180, 140
coin_count = 0

# ==========================================
# Marker 工具函数
# ==========================================
def send_marker(marker_str):
    """同时发送 LSL marker 和打印日志"""
    outlet.push_sample([marker_str])
    print(f"[MARKER] {marker_str}")


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

coin_sound_path = _p(_SND_DIR, "coin.wav")
if os.path.exists(coin_sound_path):
    coin_sound = pygame.mixer.Sound(coin_sound_path)
    coin_sound.set_volume(0.6)
else:
    coin_sound = None
    print("[警告] 未找到 coin.wav 音效文件")


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
            pygame.draw.line(surface, COLOR_BRICK_LIGHT, (bx + 1, by + 1), (bx + 14, by + 1), 1)
            pygame.draw.line(surface, COLOR_BRICK_LIGHT, (bx + 1, by + 1), (bx + 1, by + 14), 1)
    surface.blit(ui_coin_img, (7, 4))
    coin_txt = coin_font.render(f"x{coin_count:02d}", True, COLOR_WHITE)
    surface.blit(coin_txt, (22, 4))


def draw_growing_dashed_line(surface, start, end, progress, color, dash_len=4, gap_len=4):
    """从 start 向 end 画一条生长的虚线，progress 控制已长出比例 (0~1)"""
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    total_dist = math.sqrt(dx * dx + dy * dy)
    if total_dist == 0:
        return
    ux = dx / total_dist
    uy = dy / total_dist

    target_dist = total_dist * progress
    drawn = 0.0
    drawing = True
    while drawn < target_dist:
        seg_len = min(dash_len if drawing else gap_len, target_dist - drawn)
        if drawing:
            x1 = int(start[0] + ux * drawn)
            y1 = int(start[1] + uy * drawn)
            x2 = int(start[0] + ux * (drawn + seg_len))
            y2 = int(start[1] + uy * (drawn + seg_len))
            pygame.draw.line(surface, color, (x1, y1), (x2, y2), 1)
        drawn += seg_len
        drawing = not drawing


def draw_progress_bar(surface, trial_idx, total_trials, block_idx, total_blocks):
    bar_x = GAME_RECT.right - BAR_X_OFFSET
    pygame.draw.rect(surface, (40, 40, 40), (bar_x, BAR_Y, BAR_W, BAR_H), border_radius=4)
    fill_w = int(BAR_W * (trial_idx + 1) / total_trials)
    if fill_w > 0:
        pygame.draw.rect(surface, COLOR_TEXT_GOLD, (bar_x, BAR_Y, fill_w, BAR_H), border_radius=4)
    pygame.draw.rect(surface, COLOR_WHITE, (bar_x, BAR_Y, BAR_W, BAR_H), 1, border_radius=4)
    label = small_font.render(f"Block{block_idx + 1}  {trial_idx + 1}/{total_trials}", True, COLOR_WHITE)
    surface.blit(label, (bar_x, BAR_Y + BAR_H + 3))


def draw_centered_text(surface, text, y, color):
    """y 为相对于游戏区顶部的偏移（像素），自动跟随画布居中"""
    surf = font.render(text, True, color)
    surface.blit(surf, (GAME_RECT.centerx - surf.get_width() // 2, GAME_RECT.top + y))



def handle_events(allow_space=False):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            print(f"[KEY] {event.key} allow_space={allow_space}")
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == pygame.K_p:
                print("[DEBUG] P key pressed - SKIP CURRENT BLOCK")
                return "skip_block"
            if event.key == pygame.K_e:
                print("[DEBUG] E key pressed - END EXPERIMENT")
                return "end"
            if allow_space and event.key == pygame.K_SPACE:
                return "space"
            
    return None


def run_freeze_frame(surface, virtual_screen, trial_idx, block_idx, duration_ms=1200):
    """Feedback结束后定格期：画面静止，金币数字稳定显示"""
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        surface.fill((0, 0, 0))
        surface.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        draw_progress_bar(surface, trial_idx, 20, block_idx, NUM_BLOCKS)
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            return "skip_block"
        if key == "end":
            return "end"
    return None


def run_blink_rest(surface, virtual_screen, trial_idx, block_idx, duration_ms=1500):
    """定格期结束后眨眼休息提示"""
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
        surface.fill((0, 0, 0))
        surface.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        draw_centered_text(surface, "【可以眨眼放松下一轮即将开始】", UI_HINT_Y, UI_HINT_COLOR)
        draw_progress_bar(surface, trial_idx, 20, block_idx, NUM_BLOCKS)
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            return "skip_block"
        if key == "end":
            return "end"
    return None


def run_block_complete_screen(surface, virtual_screen, block_idx, total_blocks):
    duration_ms = 3000
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        surface.fill((0, 0, 0))
        surface.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        draw_centered_text(surface, f"Block {block_idx + 1} 完成！", UI_TEXT_Y - 20, COLOR_TEXT_GOLD)
        if block_idx < total_blocks - 1:
            draw_centered_text(surface, f"还剩 {total_blocks - block_idx - 1} 个Block", UI_TEXT_Y + 40, UI_HINT_COLOR)
        else:
            draw_centered_text(surface, "实验完成，感谢参与！", UI_TEXT_Y + 40, UI_HINT_COLOR)
        pygame.display.flip()
        key = handle_events(allow_space=True)
        if key in ("skip_block", "space"):
            break
        if key == "end":
            return "end"
    return None


def run_rest_block(surface, virtual_screen, duration_ms=20000):
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        surface.fill((0, 0, 0))
        surface.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        draw_centered_text(surface, "【休息放空中，请稍放松】", UI_HINT_Y, UI_HINT_COLOR)
        remaining = (duration_ms - (pygame.time.get_ticks() - start)) // 1000 + 1
        draw_centered_text(surface, f"{remaining}", UI_TEXT_Y, COLOR_TEXT_GOLD)
        pygame.display.flip()
        key = handle_events(allow_space=True)
        if key in ("skip_block", "space"):
            break
        if key == "end":
            return "end"
    return None


def run_game_start_menu(surface, game_width, game_height, scale):
    in_menu = True
    clock = pygame.time.Clock()
    print(SCREEN_W, SCREEN_H, OFFSET_X, OFFSET_Y)

    # 字体大小按屏幕高度等比缩放
    title_size = int(SCREEN_H * 0.065)
    text_size = int(SCREEN_H * 0.045)
    hint_size = int(SCREEN_H * 0.022)

    if os.path.exists(_p(_FONT_DIR, "SuperMario256.ttf")):
        HD_FONT_TITLE = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), title_size)
        HD_FONT_TEXT = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), text_size)
    else:
        HD_FONT_TITLE = safe_sysfont("Arial", title_size)
        HD_FONT_TEXT = safe_sysfont("Arial", text_size)

    if FONT_PATH:
        PIXEL_FONT_SMALL = pygame.font.Font(FONT_PATH, hint_size)
    else:
        PIXEL_FONT_SMALL = safe_sysfont("SimHei", hint_size)

    if os.path.exists(_p(_IMG_DIR, "scene_2.gif")):
        bg_img = pygame.image.load(_p(_IMG_DIR, "scene_2.gif")).convert()
        print("原始尺寸:", bg_img.get_size())
        bg_img = pygame.transform.scale(bg_img, (SCREEN_W, SCREEN_H))
        print("缩放后尺寸:", bg_img.get_size())
    else:
        bg_img = pygame.Surface((game_width * scale, game_height * scale))
        bg_img.fill(COLOR_SKY)

    C1 = (200, 76, 12)
    C2 = (252, 216, 40)
    C3 = (255, 255, 255)
    C4 = (15, 15, 35)

    # 各元素按屏幕比例定位
    title_y = int(SCREEN_H * 0.20)
    start_y = int(SCREEN_H * 0.48)
    hint_y = int(SCREEN_H * 0.78)

    while in_menu:
        surface.blit(bg_img, (0, 0))
        title_surf = HD_FONT_TITLE.render("SUPER BCI MARIO", True, C1)
        title_shadow = HD_FONT_TITLE.render("SUPER BCI MARIO", True, C4)
        surface.blit(title_shadow, (SCREEN_W // 2 - title_surf.get_width() // 2 + 4, title_y + 4))
        surface.blit(title_surf, (SCREEN_W // 2 - title_surf.get_width() // 2, title_y))
        blink_val = (math.sin(pygame.time.get_ticks() * 0.007) + 1) / 2
        if blink_val > 0.3:
            start_text = HD_FONT_TEXT.render("START GAME", True, C2)
            surface.blit(start_text, (SCREEN_W // 2 - start_text.get_width() // 2, start_y))
        hint_text = PIXEL_FONT_SMALL.render("PRESS [SPACE] TO START", True, C3)
        surface.blit(hint_text, (SCREEN_W // 2 - hint_text.get_width() // 2, hint_y))
        pygame.display.flip()
        clock.tick(60)

        key = handle_events(allow_space=True)
        if key == "space":
            in_menu = False
        elif key == "end":
            pygame.quit()
            sys.exit()


NUM_BLOCKS = 3
run_game_start_menu(screen, GAME_WIDTH, GAME_HEIGHT, SCALE)

TOTAL_TRIALS = 20
FEEDBACK_DUR = 2000
end_experiment = False

for block_idx in range(NUM_BLOCKS):
    if end_experiment:
        break

    # ── BLOCK 开始 ──────────────────────────────────────────────
    send_marker(f"BLOCK_START_{block_idx + 1}")

    trials = ["横"] * 10 + ["竖"] * 10
    random.shuffle(trials)
    skip_current_block = False

    for trial_idx, trial_type in enumerate(trials):
        if skip_current_block or end_experiment:
            break

        # 用数字编码方便后续分析：横=1，竖=2
        class_id = 1 if trial_type == "横" else 2

        # ── 1. REST ─────────────────────────────────────────────
        send_marker(f"REST_START_B{block_idx+1}_T{trial_idx+1}_C{class_id}")
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 3500:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events()
            if key == "skip_block":
                skip_current_block = True; break
            if key == "end":
                end_experiment = True; break
        send_marker(f"REST_END_B{block_idx+1}_T{trial_idx+1}_C{class_id}")

        if skip_current_block or end_experiment:
            break

        # 金币初始化
        if trial_type == "竖":
            stage_coin_x = MARIO_X + 7
            stage_coin_y = MARIO_Y - 60
        elif trial_type == "横":
            stage_coin_x = GOOMBA_X + 1
            stage_coin_y = GOOMBA_Y - 22
        else:
            stage_coin_x, stage_coin_y = -100, -100

        # ── 2. CUE ──────────────────────────────────────────────
        send_marker(f"CUE_START_B{block_idx+1}_T{trial_idx+1}_C{class_id}")
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 2000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            draw_centered_text(screen, f"【当前任务：{trial_type}向想象】", UI_TEXT_Y, UI_TEXT_COLOR)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events()
            if key == "skip_block":
                skip_current_block = True; break
            if key == "end":
                end_experiment = True; break
        send_marker(f"CUE_END_B{block_idx+1}_T{trial_idx+1}_C{class_id}")

        if skip_current_block or end_experiment:
            break

        # ── 3. 按空格准备 ────────────────────────────────────────
        waiting_for_space = True
        while waiting_for_space:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            draw_centered_text(screen, "准备好后按 [空格键] 开始想象", UI_HINT_Y, UI_HINT_COLOR)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events(allow_space=True)
            if key == "space":
                send_marker(f"READY_B{block_idx+1}_T{trial_idx+1}_C{class_id}")
                waiting_for_space = False
            elif key == "skip_block":
                skip_current_block = True; waiting_for_space = False
            elif key == "end":
                end_experiment = True; waiting_for_space = False

        if skip_current_block or end_experiment:
            break

        # ── 4. MI ────────────────────────────────────────────────
        send_marker(f"MI_START_B{block_idx+1}_T{trial_idx+1}_C{class_id}")
        mi_start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - mi_start < 4000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))

            # 从马里奥生长出辅助虚线连至金币
            mi_progress = min((pygame.time.get_ticks() - mi_start) / 4000.0, 1.0)
            mario_center = (MARIO_X + 18, MARIO_Y + 11)
            coin_center = (stage_coin_x + 10, stage_coin_y + 10)
            draw_growing_dashed_line(virtual_screen, mario_center, coin_center,
                                     mi_progress, COLOR_TEXT_GOLD)
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events()
            if key == "skip_block":
                skip_current_block = True; break
            if key == "end":
                end_experiment = True; break
        send_marker(f"MI_END_B{block_idx+1}_T{trial_idx+1}_C{class_id}")

        if skip_current_block or end_experiment:
            break

        # ── 5. FEEDBACK ──────────────────────────────────────────
        send_marker(f"FEEDBACK_START_B{block_idx+1}_T{trial_idx+1}_C{class_id}")
        anim_start = pygame.time.get_ticks()
        coin_eaten = False
        goomba_hit = False

        while pygame.time.get_ticks() - anim_start < FEEDBACK_DUR:
            progress = (pygame.time.get_ticks() - anim_start) / FEEDBACK_DUR
            draw_retro_scenery(virtual_screen)

            if trial_type == "横":
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
                    if coin_sound:
                        coin_sound.play()
                    send_marker(f"COIN_EATEN_B{block_idx+1}_T{trial_idx+1}_C{class_id}")
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
                            pygame.draw.line(virtual_screen, COLOR_TEXT_GOLD, (sx - 1, sy), (sx + 1, sy), 1)
                            pygame.draw.line(virtual_screen, COLOR_TEXT_GOLD, (sx, sy - 1), (sx, sy + 1), 1)
                else:
                    virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))

            elif trial_type == "竖":
                virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
                jump_offset = int(60 * (4 * progress * (1 - progress)))
                jump_y = MARIO_Y - jump_offset
                virtual_screen.blit(mario_stand, (MARIO_X, jump_y))
                if not coin_eaten:
                    virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
                if jump_offset > 40 and not coin_eaten:
                    coin_eaten = True
                    coin_count += 1
                    if coin_sound:
                        coin_sound.play()
                    send_marker(f"COIN_EATEN_B{block_idx+1}_T{trial_idx+1}_C{class_id}")
                bullet_x = GOOMBA_X - int((GOOMBA_X + 20) * progress)
                if bullet_x > -10:
                    pygame.draw.circle(virtual_screen, (16, 16, 24), (bullet_x, GOOMBA_Y + 10), 5)
                    pygame.draw.circle(virtual_screen, (240, 240, 250), (bullet_x - 2, GOOMBA_Y + 8), 1)
            else:
                virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
                virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))

            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events()
            if key == "skip_block":
                skip_current_block = True; break
            if key == "end":
                end_experiment = True; break

        send_marker(f"FEEDBACK_END_B{block_idx+1}_T{trial_idx+1}_C{class_id}")

        if skip_current_block or end_experiment:
            break

        # ── 6. 定格期 1.2秒 ─────────────────────────────────────
        key = run_freeze_frame(screen, virtual_screen, trial_idx, block_idx, duration_ms=1200)
        if key == "skip_block":
            skip_current_block = True
        elif key == "end":
            end_experiment = True

        if skip_current_block or end_experiment:
            break

        # ── 7. 休息期 1.5秒 ─────────────────────────────────────
        key = run_blink_rest(screen, virtual_screen, trial_idx, block_idx, duration_ms=1500)
        if key == "skip_block":
            skip_current_block = True
        elif key == "end":
            end_experiment = True

        if skip_current_block or end_experiment:
            break

    # ── BLOCK 结束 ──────────────────────────────────────────────
    send_marker(f"BLOCK_END_{block_idx + 1}")

    if end_experiment:
        break

    key = run_block_complete_screen(screen, virtual_screen, block_idx, NUM_BLOCKS)
    if key == "end":
        break

    if block_idx < NUM_BLOCKS - 1:
        send_marker(f"REST_BLOCK_START_{block_idx + 1}")
        key = run_rest_block(screen, virtual_screen, duration_ms=15000)
        send_marker(f"REST_BLOCK_END_{block_idx + 1}")
        if key == "end":
            break

send_marker("EXPERIMENT_END")
pygame.quit()
