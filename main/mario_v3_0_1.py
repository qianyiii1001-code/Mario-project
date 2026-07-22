# 在v3_0版本基础上增加了
# -3-2-1倒计时：按空格准备后在屏幕中间显示倒计时，结束后进入MI阶段
# 在v2版本基础上增加了
# -横向：改为马里奥横向跑，冲撞goomba
# -进度条，trial之间的说明，跳过键
import pygame

# ==========================================
# 并行口 (LPT) TTL Trigger 发送模块
# ==========================================
# 使用 ctypes 直接调用 inpout32.dll / inpoutx64.dll 操作并口
# 无需安装任何第三方 Python 包（pyparallel / psychopy 等）
#
# 驱动安装:
#   1. 下载 InpOutBinaries: http://www.highrez.co.uk/downloads/inpout32/
#   2. 解压后将 inpout32.dll (32位) 或 inpoutx64.dll (64位) 放到 C:\Windows\System32\
#   3. 以管理员权限运行本程序
#
# 如果环境不具备并口，程序仍可运行（仅打印日志，不发送硬件信号）

import ctypes as _ctypes

# ── 并口初始化 ──────────────────────────────────────────────────
# 常见地址: LPT1=0x0378, LPT2=0x0278, LPT3=0x03BC
# 在设备管理器 > 端口(COM和LPT) > LPT端口 > 资源 中查看正确地址
_PARALLEL_PORT_ADDRESS = 0x3FF8  # ← 根据实际硬件修改此地址
_inpout = None
_PARALLEL_OK = False

try:
    # 尝试加载 64 位驱动
    _inpout = _ctypes.WinDLL("inpoutx64.dll")
    print("[并口] 加载 inpoutx64.dll (64位驱动)")
except OSError:
    pass

if _inpout is None:
    try:
        # 尝试加载 32 位驱动
        _inpout = _ctypes.WinDLL("inpout32.dll")
        print("[并口] 加载 inpout32.dll (32位驱动)")
    except OSError:
        pass

if _inpout is None:
    print("[并口] 驱动未找到: 请将 inpout32.dll 或 inpoutx64.dll 放到 C:\\Windows\\System32\\")
else:
    try:
        # 验证并口可访问: 先读取数据寄存器
        _inpout.Inp32(_PARALLEL_PORT_ADDRESS)
        _PARALLEL_OK = True
        print(f"[并口] 初始化成功: 地址 0x{_PARALLEL_PORT_ADDRESS:04X}")
    except Exception as _e:
        print(f"[并口] 初始化失败: {_e}")
        print("[并口] 请确认: 1) 地址正确  2) 以管理员运行")

if not _PARALLEL_OK:
    print("[并口] 将以纯日志模式运行（不发送硬件 TTL 信号）")

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
    coin_font = pygame.font.Font(FONT_PATH, 9)         # 虚拟画布尺寸，不随SCALE放大
else:
    font = safe_sysfont("SimHei", int(24 * FONT_SCALE))
    small_font = safe_sysfont("SimHei", int(18 * FONT_SCALE))
    coin_font = safe_sysfont("SimHei", 12)             # 虚拟画布尺寸，不随SCALE放大

UI_TEXT_Y = SCREEN_H // 2 - OFFSET_Y              # 屏幕长一半（相对游戏区顶部偏移）
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
# Trigger 编码表 & 发送函数
# ==========================================
# 将原来的字符串 Marker 映射为整数 Trigger code (1~255)
# 每个事件类型一个固定 code，block/trial/class 信息由打印日志记录
TRIGGER = {
    # ★ MI 阶段（运动想象）—— 核心 Marker，横竖分开编码
    "MI_START_HENG":   1,   # 横向想象开始
    "MI_END_HENG":    11,   # 横向想象结束
    "MI_START_SHU":    2,   # 竖向想象开始
    "MI_END_SHU":     12,   # 竖向想象结束
    # 实验控制
    "BLOCK_START":   100,   # Block 开始
    "BLOCK_END":     101,   # Block 结束
    "EXPERIMENT_END": 255,  # 实验结束
}


def send_trigger(code, duration_ms=15):
    """发送 TTL Trigger: 设置数据线 → 保持 duration_ms → 清零

    Args:
        code: 整数 trigger code (1~255)
        duration_ms: 脉冲宽度（毫秒），默认 15ms（BP 建议 ≥10ms）
    """
    if _PARALLEL_OK and _inpout is not None:
        try:
            # 优先使用 8 位写（避免 Out32 写入多余字节干扰 BP 读取）
            _write_port = getattr(_inpout, "DlPortWritePortUchar", None)
            if _write_port is not None:
                _write_port(_PARALLEL_PORT_ADDRESS, code)
            else:
                _inpout.Out32(_PARALLEL_PORT_ADDRESS, code)
            pygame.time.wait(duration_ms)
            if _write_port is not None:
                _write_port(_PARALLEL_PORT_ADDRESS, 0)
            else:
                _inpout.Out32(_PARALLEL_PORT_ADDRESS, 0)
        except Exception as _e:
            print(f"[TRIGGER] 并口发送失败: {_e}")
    else:
        # 无并口时模拟延迟，保持时间节奏一致
        pygame.time.wait(duration_ms)
    print(f"[TRIGGER] code={code:3d}")


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


def _generate_stage_clear_sound():
    """合成一段简短上行琶音作为 Block 完成音效（类似马里奥通关旋律）"""
    sample_rate = 22050
    # 四个上行音符: C5 → E5 → G5 → C6，每个 120ms
    notes = [
        (523.25, 0.12),   # C5
        (659.25, 0.12),   # E5
        (783.99, 0.12),   # G5
        (1046.50, 0.24),  # C6 (稍长)
    ]
    total_samples = sum(int(sample_rate * dur) for _, dur in notes)
    # 结尾多给 50ms 防止截断
    total_samples += int(sample_rate * 0.05)

    import struct
    from io import BytesIO

    buf = BytesIO()
    # WAV header
    data_size = total_samples * 2  # 16-bit mono
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate,
                          sample_rate * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))

    for freq, duration in notes:
        n = int(sample_rate * duration)
        for i in range(n):
            t = i / sample_rate
            # 包络：快速起音 + 缓慢衰减
            envelope = max(0.0, 1.0 - t / duration) * 0.8
            val = int(32767 * envelope * math.sin(2 * math.pi * freq * t))
            buf.write(struct.pack("<h", val))

    # 5ms 静音收尾
    silence_samples = int(sample_rate * 0.05)
    for _ in range(silence_samples):
        buf.write(struct.pack("<h", 0))

    buf.seek(0)
    try:
        return pygame.mixer.Sound(buf)
    except Exception:
        return None


stage_clear_sound = _generate_stage_clear_sound()
if stage_clear_sound:
    stage_clear_sound.set_volume(0.5)
    print("[音效] Block完成音效已合成")
else:
    print("[警告] 无法合成Block完成音效")


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
    # 垂直居中对齐金币图标（图标高度16px）
    coin_txt_y = 4 + (16 - coin_txt.get_height()) // 2
    surface.blit(coin_txt, (22, coin_txt_y))


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
    label = small_font.render(f"Block{block_idx + 1}", True, COLOR_WHITE)
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


def run_dash_preview(surface, virtual_screen, trial_type, stage_coin_x, stage_coin_y, duration_ms=1300):
    """CUE结束后、READY前的虚线预览阶段：笔头从马里奥出发匀速划到金币，身后留下白色虚线轨迹"""
    start_pos = (MARIO_X + 18, MARIO_Y + 11)
    end_pos = (stage_coin_x + 10, stage_coin_y + 10)

    anim_start = pygame.time.get_ticks()
    hold_start = None

    while True:
        now = pygame.time.get_ticks()
        elapsed = now - anim_start

        if hold_start is not None:
            # 停留阶段：完整虚线 + 笔头静止 300ms
            if now - hold_start >= 300:
                break
            progress = 1.0
            dot_x, dot_y = end_pos
        else:
            if elapsed >= duration_ms:
                hold_start = now
                progress = 1.0
                dot_x, dot_y = end_pos
            else:
                progress = elapsed / duration_ms
                dot_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * progress)
                dot_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * progress)

        draw_retro_scenery(virtual_screen)

        # 白色虚线轨迹（每隔8px画一段4px短线）
        if progress > 0:
            draw_growing_dashed_line(virtual_screen, start_pos, end_pos,
                                     progress, COLOR_WHITE, dash_len=4, gap_len=4)

        # 笔头小圆点
        pygame.draw.circle(virtual_screen, COLOR_WHITE, (dot_x, dot_y), 3)

        surface.fill((0, 0, 0))
        surface.blit(pygame.transform.scale(virtual_screen,
                     (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        pygame.display.flip()

        key = handle_events()
        if key == "skip_block":
            return "skip_block"
        if key == "end":
            return "end"

    return None


def run_countdown(surface, virtual_screen, trial_idx, block_idx, total_ms=3000):
    """
    在屏幕中央显示 3 → 2 → 1 倒计时。
    total_ms: 倒计时总时长（毫秒），默认3000ms，每个数字显示约1秒。
    """
    numbers = [3, 2, 1]
    interval = total_ms // len(numbers)  # 每个数字分配的时间

    # 创建大号倒计数字体（比普通字体更大）
    countdown_size = int(font.get_height() * 2.5)
    if FONT_PATH:
        countdown_font = pygame.font.Font(FONT_PATH, countdown_size)
    else:
        countdown_font = safe_sysfont("SimHei", countdown_size)

    start = pygame.time.get_ticks()

    for i, num in enumerate(numbers):
        num_start = start + i * interval
        while pygame.time.get_ticks() - num_start < interval:
            now = pygame.time.get_ticks()
            elapsed_in_num = now - num_start

            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen,
                         (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            # 倒计时数字在屏幕居中（Y方向用游戏区正中间偏上一点）
            num_surf = countdown_font.render(str(num), True, COLOR_TEXT_GOLD)
            num_x = GAME_RECT.centerx - num_surf.get_width() // 2
            num_y = GAME_RECT.centery - num_surf.get_height() // 2 - int(10 * FONT_SCALE)
            screen.blit(num_surf, (num_x, num_y))

            draw_progress_bar(screen, trial_idx, 20, block_idx, NUM_BLOCKS)
            pygame.display.flip()

            key = handle_events()
            if key == "skip_block":
                return "skip_block"
            if key == "end":
                return "end"

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
        draw_progress_bar(surface, trial_idx, 20, block_idx, NUM_BLOCKS)
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            return "skip_block"
        if key == "end":
            return "end"
    return None


def run_block_complete_screen(surface, virtual_screen, block_idx, total_blocks):
    if stage_clear_sound:
        stage_clear_sound.play()
    duration_ms = 3000
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration_ms:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        surface.fill((0, 0, 0))
        surface.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        draw_centered_text(surface, f"Block {block_idx + 1} 完成！", UI_TEXT_Y - 20, COLOR_TEXT_GOLD)
        if block_idx < total_blocks - 1:
            draw_centered_text(surface, "准备进入休息", UI_TEXT_Y + 100, UI_HINT_COLOR)
        else:
            draw_centered_text(surface, "实验完成，感谢参与！", UI_TEXT_Y + 100, UI_HINT_COLOR)
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
        draw_centered_text(surface, "【休息放空中，请稍放松】", UI_TEXT_Y + 100, UI_HINT_COLOR)
        remaining = (duration_ms - (pygame.time.get_ticks() - start)) // 1000 + 1
        draw_centered_text(surface, f"{remaining}", UI_TEXT_Y + 50, COLOR_TEXT_GOLD)
        pygame.display.flip()
        key = handle_events(allow_space=True)
        if key in ("skip_block", "space"):
            break
        if key == "end":
            return "end"
    return None


def run_instruction_screen(surface, virtual_screen):
    """显示实验指导语，两屏，空格翻页，第二屏空格进入实验"""
    title_size = int(SCREEN_H * 0.055)
    body_size = int(SCREEN_H * 0.035)
    hint_size = int(SCREEN_H * 0.022)

    if FONT_PATH:
        title_font = pygame.font.Font(FONT_PATH, title_size)
        body_font = pygame.font.Font(FONT_PATH, body_size)
        hint_font = pygame.font.Font(FONT_PATH, hint_size)
    else:
        title_font = safe_sysfont("SimHei", title_size)
        body_font = safe_sysfont("SimHei", body_size)
        hint_font = safe_sysfont("SimHei", hint_size)

    page1 = [
        (title_font, "欢迎参加本次实验", COLOR_TEXT_GOLD),
        (body_font, "", COLOR_WHITE),
        (body_font, "", COLOR_WHITE),
        (body_font, "", COLOR_WHITE),
        (body_font, "", COLOR_WHITE),
        (body_font, "【你的任务】", COLOR_TEXT_GOLD),
        (body_font, "想象用右手握笔，在空中画出笔画：", COLOR_WHITE),
        (body_font, "  * 横  ->  手腕从左向右水平划过", COLOR_WHITE),
        (body_font, "  * 竖  ->  手腕从下向上垂直划过", COLOR_WHITE),
    ]

    page2 = [
        (title_font, "想象期间请保持身体静止", COLOR_TEXT_GOLD),
        (body_font, "", COLOR_WHITE),
        (body_font, "/ 尽量减少眨眼和吞咽", COLOR_WHITE),
        (body_font, "/ 放松面部、肩膀", COLOR_WHITE),
    ]

    pages = [page1, page2]
    page_idx = 0
    clock = pygame.time.Clock()

    while page_idx < len(pages):
        surface.fill((0, 0, 0))

        lines = pages[page_idx]
        line_heights = [f.get_height() for f, _, _ in lines]
        gap = int(SCREEN_H * 0.018)
        total_h = sum(line_heights) + gap * (len(lines) - 1)
        start_y = (SCREEN_H - total_h) // 2

        y = start_y
        for font_obj, text, color in lines:
            if text:
                surf = font_obj.render(text, True, color)
                surface.blit(surf, ((SCREEN_W - surf.get_width()) // 2, y))
            y += font_obj.get_height() + gap

        hint_text = "按 [空格键] 继续" if page_idx == 0 else "按 [空格键] 开始实验"
        hint_surf = hint_font.render(hint_text, True, COLOR_WHITE)
        surface.blit(hint_surf, ((SCREEN_W - hint_surf.get_width()) // 2,
                                 SCREEN_H - int(SCREEN_H * 0.1)))

        pygame.display.flip()
        clock.tick(60)

        key = handle_events(allow_space=True)
        if key == "space":
            page_idx += 1
        elif key == "end":
            return "end"
        elif key == "skip_block":
            page_idx += 1  # P键也翻页，保持一致

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
        bg_img = pygame.Surface((SCREEN_W, SCREEN_H))
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

# ── 指导语 ──────────────────────────────────────────────────
key = run_instruction_screen(screen, virtual_screen)
if key == "end":
    send_trigger(TRIGGER["EXPERIMENT_END"])
    pygame.quit()
    sys.exit()

TOTAL_TRIALS = 20
FEEDBACK_DUR = 2000
end_experiment = False

for block_idx in range(NUM_BLOCKS):
    if end_experiment:
        break

    # ── BLOCK 开始 ──────────────────────────────────────────────
    send_trigger(TRIGGER["BLOCK_START"])
    print(f"[TRIGGER] BLOCK_START Block {block_idx + 1}")

    trials = ["横"] * 10 + ["竖"] * 10
    random.shuffle(trials)
    skip_current_block = False

    for trial_idx, trial_type in enumerate(trials):
        if skip_current_block or end_experiment:
            break

        # 用数字编码方便后续分析：横=1，竖=2
        class_id = 1 if trial_type == "横" else 2

        # ── 1. REST ─────────────────────────────────────────────
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 2000:
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
        if skip_current_block or end_experiment:
            break

        # 金币初始化
        if trial_type == "竖":
            stage_coin_x = MARIO_X + 7
            stage_coin_y = MARIO_Y - 80
        elif trial_type == "横":
            stage_coin_x = GOOMBA_X + 1
            stage_coin_y = GOOMBA_Y - 22
        else:
            stage_coin_x, stage_coin_y = -100, -100

        # ── 2. CUE ──────────────────────────────────────────────
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < 2000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            draw_centered_text(screen, f"【当前任务：{trial_type}向想象】", UI_TEXT_Y + 100, UI_TEXT_COLOR)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events()
            if key == "skip_block":
                skip_current_block = True; break
            if key == "end":
                end_experiment = True; break
        if skip_current_block or end_experiment:
            break

        # ── 2.5. 虚线预览（Block1前十次, Block2前五次, Block3无） ──
        DASH_PREVIEW_COUNTS = [10, 5, 0]
        if trial_idx < DASH_PREVIEW_COUNTS[block_idx]:
            result = run_dash_preview(screen, virtual_screen, trial_type, stage_coin_x, stage_coin_y)
            if result == "skip_block":
                skip_current_block = True
                continue
            if result == "end":
                end_experiment = True
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

            if block_idx == 0:
                draw_centered_text(screen, "回忆笔画轨迹，准备好后按空格开始想象", UI_TEXT_Y + 100, UI_HINT_COLOR)
            else:
                draw_centered_text(screen, "准备好后按空格开始想象", UI_TEXT_Y + 100, UI_HINT_COLOR)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events(allow_space=True)
            if key == "space":
                waiting_for_space = False
            elif key == "skip_block":
                skip_current_block = True; waiting_for_space = False
            elif key == "end":
                end_experiment = True; waiting_for_space = False

        if skip_current_block or end_experiment:
            break

        # ── 3.5. 倒计时 3-2-1 ─────────────────────────────────────
        key = run_countdown(screen, virtual_screen, trial_idx, block_idx, total_ms=3000)
        if key == "skip_block":
            skip_current_block = True
        elif key == "end":
            end_experiment = True

        if skip_current_block or end_experiment:
            break

        # ── 4. MI ────────────────────────────────────────────────
        mi_key_start = "MI_START_HENG" if trial_type == "横" else "MI_START_SHU"
        mi_key_end = "MI_END_HENG" if trial_type == "横" else "MI_END_SHU"
        send_trigger(TRIGGER[mi_key_start])
        print(f"[TRIGGER] {mi_key_start} B{block_idx+1} T{trial_idx+1}")
        mi_start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - mi_start < 4000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))

            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events()
            if key == "skip_block":
                skip_current_block = True; break
            if key == "end":
                end_experiment = True; break
        send_trigger(TRIGGER[mi_key_end])
        print(f"[TRIGGER] {mi_key_end} B{block_idx+1} T{trial_idx+1}")

        if skip_current_block or end_experiment:
            break

        # ── 5. FEEDBACK ──────────────────────────────────────────
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
                jump_offset = int(80 * (4 * progress * (1 - progress)))
                jump_y = MARIO_Y - jump_offset
                virtual_screen.blit(mario_stand, (MARIO_X, jump_y))
                if not coin_eaten:
                    virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
                if jump_offset > 40 and not coin_eaten:
                    coin_eaten = True
                    coin_count += 1
                    if coin_sound:
                        coin_sound.play()
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
    send_trigger(TRIGGER["BLOCK_END"])
    print(f"[TRIGGER] BLOCK_END Block {block_idx + 1}")

    if end_experiment:
        break

    key = run_block_complete_screen(screen, virtual_screen, block_idx, NUM_BLOCKS)
    if key == "end":
        break

    if block_idx < NUM_BLOCKS - 1:
        key = run_rest_block(screen, virtual_screen, duration_ms=15000)
        if key == "end":
            break

send_trigger(TRIGGER["EXPERIMENT_END"])
pygame.quit()
