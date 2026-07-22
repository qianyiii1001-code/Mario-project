# v3_0_7 — 三分类版 + 学习试次：
#   基于 v3_0_6 架构
#   正式实验前增加 10 个学习试次（左5 + 右5），含虚线引导
#   6 Block × 25 trial = 150 试次
#   闭眼静息 90s 仅实验前一次，Block 间只有 15s 休息放空
#   指导语改为"抓握动作"想象
#   学习试次不显示"虚线引导路径"文字
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
from self_report import SelfReportScreen
from self_report import SelfReportScreen

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
UI_CENTER_Y = (GAME_HEIGHT * SCALE) // 2 - int(10 * FONT_SCALE)  # 与倒计时321同位（游戏区垂直居中）
UI_HINT_Y = int(10 * FONT_SCALE)                 # 游戏区内顶部
UI_TEXT_COLOR = COLOR_TEXT_GOLD
UI_HINT_COLOR = COLOR_WHITE
BAR_X_OFFSET = 150
BAR_Y = 25
BAR_W = 140
BAR_H = 14

MARIO_X, MARIO_Y = 110, 116
coin_count = 0

# ==========================================
# Trigger 编码表 & 发送函数
# ==========================================
# 将原来的字符串 Marker 映射为整数 Trigger code (1~255)
# 每个事件类型一个固定 code，block/trial/class 信息由打印日志记录
TRIGGER = {
    # ★ MI 阶段（运动想象）—— 核心 Marker，左右手分开编码
    "MI_START_LEFT":   1,   # 左手想象开始
    "MI_END_LEFT":    11,   # 左手想象结束
    "MI_START_RIGHT":  2,   # 右手想象开始
    "MI_END_RIGHT":   12,   # 右手想象结束
    "MI_START_BLANK":  3,   # 空白对照开始
    "MI_END_BLANK":   13,   # 空白对照结束
    # 静息阶段
    "REST_CLOSED_START": 80,   # 闭眼静息开始
    "REST_CLOSED_END":   81,   # 闭眼静息结束
    "REST_OPEN_START":   82,   # 睁眼静息开始
    "REST_OPEN_END":     83,   # 睁眼静息结束
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
peach_stand = load_and_scale_sprite(_p(_IMG_DIR, "peach.png"), (36, 48))
luigi_stand = load_and_scale_sprite(_p(_IMG_DIR, "luigi.png"), (36, 48))
ALL_CHARS = [mario_stand, peach_stand, luigi_stand]
goomba_normal = load_and_scale_sprite(_p(_IMG_DIR, "goomba.png"), (18, 18))
mario_cap = load_and_scale_sprite(_p(_IMG_DIR, "cap.png"), (14, 10))
ui_coin_img = load_and_scale_sprite(_p(_IMG_DIR, "coin.png"), (16, 16))
stage_coin_img = load_and_scale_sprite(_p(_IMG_DIR, "coin.png"), (20, 20))
goomba_flat = pygame.transform.scale(goomba_normal, (18, 6))

# 背景图加载（256×192，与虚拟画布一致）
def _load_bg(name):
    path = _p(_IMG_DIR, name)
    if os.path.exists(path):
        return pygame.transform.scale(pygame.image.load(path).convert(), (GAME_WIDTH, GAME_HEIGHT))
    return None

bg_desert = _load_bg("dessert.png")
if bg_desert:
    # 沙漠背景放大填充全部画面 + 下移 3px
    BIG_W = int(GAME_WIDTH * 1.10)
    BIG_H = int(GAME_HEIGHT * 1.10)
    bg_desert = pygame.transform.scale(
        pygame.image.load(_p(_IMG_DIR, "dessert.png")).convert(),
        (BIG_W, BIG_H))
    shifted = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    shifted.blit(bg_desert, ((GAME_WIDTH - BIG_W) // 2, -6))
    bg_desert = shifted
bg_underwater = _load_bg("bg_underwater.png")
bg_options = [None, bg_desert, bg_underwater]  # None=经典场景
bg_names = ["经典", "沙漠", "海底"]
current_bg = None  # 当前 block 的背景

coin_sound_path = _p(_SND_DIR, "coin.wav")
if os.path.exists(coin_sound_path):
    coin_sound = pygame.mixer.Sound(coin_sound_path)
    coin_sound.set_volume(0.6)
else:
    coin_sound = None
    print("[警告] 未找到 coin.wav 音效文件")


def _generate_stage_clear_sound():
    """合成通关短旋律：五声音阶上行 → 高音定点 → 下行跳音收束"""
    sample_rate = 22050

    import struct
    from io import BytesIO

    # ── 新旋律：简短有力，约 1.2s ───────────────────────────────
    melody = [
        # 上行五声音阶 (0-400ms)
        (523.25, 0.08),   # C5  80ms
        (587.33, 0.08),   # D5  80ms
        (659.25, 0.08),   # E5  80ms
        (783.99, 0.08),   # G5  80ms
        (880.00, 0.08),   # A5  80ms
        # 高音强调 (400-600ms)
        (1046.50, 0.20),  # C6 200ms (站稳高音)
        # 下行跳跃收束 (600-1200ms)
        (1318.51, 0.10),  # E6 100ms
        (783.99, 0.10),   # G5 100ms
        (1046.50, 0.10),  # C6 100ms
        (523.25, 0.30),   # C5 300ms (结尾长音)
    ]

    # 低音声部：简洁的根音支撑
    bass = [
        (0, 0.40),        # 休息，等旋律上行完
        (261.63, 0.20),   # C4 200ms (配合高音C6)
        (0, 0.20),
        (261.63, 0.10),   # C4
        (0, 0.10),
        (261.63, 0.20),   # C4
    ]

    def synth_notes(notes_list, amp=1.0, delay=0.0):
        total_dur = sum(d for _, d in notes_list) + delay
        n_samples = int(sample_rate * total_dur)
        buf = bytearray(n_samples * 2)

        t_offset = delay
        for freq, dur in notes_list:
            if freq == 0:
                t_offset += dur
                continue
            n = int(sample_rate * dur)
            for i in range(n):
                t = i / sample_rate + t_offset
                local_t = i / sample_rate
                attack = min(1.0, local_t / 0.008)         # 8ms 起音
                decay = max(0.25, 1.0 - local_t / dur)      # 线性衰减到25%
                envelope = attack * decay * amp * 0.7
                sample_val = int(32767 * envelope * math.sin(2 * math.pi * freq * t))
                idx = int((t_offset + local_t) * sample_rate) * 2
                if idx + 1 < len(buf):
                    old = int.from_bytes(buf[idx:idx+2], 'little', signed=True)
                    new = max(-32767, min(32767, old + sample_val))
                    buf[idx:idx+2] = struct.pack('<h', new)
            t_offset += dur

        return buf, n_samples

    mel_buf, mel_len = synth_notes(melody, amp=1.0)
    bas_buf, bas_len = synth_notes(bass, amp=0.45)

    max_len = max(mel_len, bas_len)
    final_buf = bytearray(max_len * 2)

    for i in range(0, min(len(mel_buf), max_len * 2), 2):
        v = int.from_bytes(mel_buf[i:i+2], 'little', signed=True)
        final_buf[i:i+2] = struct.pack('<h', v)

    for i in range(0, min(len(bas_buf), max_len * 2), 2):
        old = int.from_bytes(final_buf[i:i+2], 'little', signed=True)
        new_val = int.from_bytes(bas_buf[i:i+2], 'little', signed=True)
        combined = max(-32767, min(32767, old + new_val))
        final_buf[i:i+2] = struct.pack('<h', combined)

    # 40ms 淡出
    fade_samples = int(sample_rate * 0.04)
    fade_start = max(0, max_len - fade_samples)
    for i in range(fade_start, max_len):
        idx = i * 2
        if idx + 1 < len(final_buf):
            v = int.from_bytes(final_buf[idx:idx+2], 'little', signed=True)
            fade = 1.0 - (i - fade_start) / fade_samples
            final_buf[idx:idx+2] = struct.pack('<h', int(v * max(0, fade)))

    buf = BytesIO()
    data_size = len(final_buf)
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate,
                          sample_rate * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(final_buf)

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
    if current_bg is None:
        # 经典场景：蓝天 + 白云 + 砖地
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
    else:
        # 沙漠/海底：直接 blit 预渲染背景
        surface.blit(current_bg, (0, 0))
    # 金币计数器（所有背景都画）
    surface.blit(ui_coin_img, (7, 4))
    coin_txt = coin_font.render(f"x{coin_count:02d}", True, COLOR_WHITE)
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
    label = small_font.render(f"Block {block_idx + 1}", True, COLOR_WHITE)
    surface.blit(label, (bar_x, BAR_Y + BAR_H + 3))


def draw_centered_text(surface, text, y, color):
    """y 为相对于游戏区顶部的偏移（像素），自动跟随画布居中"""
    surf = font.render(text, True, color)
    surface.blit(surf, (GAME_RECT.centerx - surf.get_width() // 2, GAME_RECT.top + y))



def handle_events(allow_space=False, allow_extend=False):
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
            if allow_extend and event.key == pygame.K_r:
                print("[DEBUG] R key pressed - EXTEND REST")
                return "extend"
            if allow_space and event.key == pygame.K_SPACE:
                return "space"

    return None


def run_go(surface, virtual_screen, trial_idx, block_idx, total_ms=1000):
    """屏幕中央显示"开始"，与"准备"相同的时长和位置"""
    go_start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - go_start < total_ms:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(virtual_screen,
                     (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

        draw_centered_text(screen, "开始", UI_CENTER_Y, UI_HINT_COLOR)
        draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
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
        draw_progress_bar(surface, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
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
            draw_centered_text(surface, "现在进入问卷作答", UI_TEXT_Y + 100, UI_HINT_COLOR)
        else:
            draw_centered_text(surface, "请完成最后的问卷", UI_TEXT_Y + 100, UI_HINT_COLOR)
        pygame.display.flip()
        key = handle_events(allow_space=True)
        if key in ("skip_block", "space"):
            break
        if key == "end":
            return "end"
    return None


def run_rest_block(surface, virtual_screen, duration_ms=90000, hint_text="【闭眼静息中】", extend_key=False, _extended_out=None, trigger_start=None, trigger_end=None):
    if trigger_start is not None:
        send_trigger(trigger_start)
    start = pygame.time.get_ticks()
    extended = False
    extend_start = 0
    total_extended_ms = 0
    while True:
        elapsed = pygame.time.get_ticks() - start
        if not extended and elapsed >= duration_ms:
            break

        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        surface.fill((0, 0, 0))
        surface.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

        if extended:
            elapsed_ext = (pygame.time.get_ticks() - extend_start) // 1000
            draw_centered_text(surface, "休息延长中，按 [R] 继续", UI_TEXT_Y + 50, UI_HINT_COLOR)
            draw_centered_text(surface, f"已延长 {elapsed_ext}s", UI_TEXT_Y + 100, COLOR_TEXT_GOLD)
        else:
            draw_centered_text(surface, hint_text, UI_TEXT_Y + 100, UI_HINT_COLOR)
            remaining = (duration_ms - elapsed) // 1000 + 1
            draw_centered_text(surface, f"{remaining}", UI_TEXT_Y + 50, COLOR_TEXT_GOLD)

        pygame.display.flip()
        key = handle_events(allow_space=True, allow_extend=extend_key)
        if key in ("skip_block", "space") and not extended:
            break
        if key == "end":
            if _extended_out is not None:
                _extended_out[0] = total_extended_ms // 1000
            if trigger_end is not None:
                send_trigger(trigger_end)
            return "end"
        if key == "extend":
            if extended:
                total_extended_ms += pygame.time.get_ticks() - extend_start
            extended = not extended
            if extended:
                extend_start = pygame.time.get_ticks()

    if _extended_out is not None:
        _extended_out[0] = total_extended_ms // 1000
    if trigger_end is not None:
        send_trigger(trigger_end)
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
        (body_font, "【任务】", COLOR_TEXT_GOLD),
        (body_font, "通过想象左右手抓握动作，控制角色移动获得金币", COLOR_WHITE),
        (body_font, "", COLOR_WHITE),
        (body_font, "  * 左手抓握  ->  角色向左移动吃金币", COLOR_WHITE),
        (body_font, "  * 右手抓握  ->  角色向右移动吃金币", COLOR_WHITE),
        (body_font, "  * 保持静止  ->  放松，不做运动想象", COLOR_WHITE),
    ]

    page2 = [
        (title_font, "想象时请保持身体静止", COLOR_TEXT_GOLD),
        (body_font, "", COLOR_WHITE),
        (body_font, "/ 减少眨眼和吞咽", COLOR_WHITE),
        (body_font, "/ 放松面部和肩膀", COLOR_WHITE),
        (body_font, "/ 不做实际动作", COLOR_WHITE),
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


NUM_BLOCKS = 6
run_game_start_menu(screen, GAME_WIDTH, GAME_HEIGHT, SCALE)

# ── 指导语 ──────────────────────────────────────────────────
key = run_instruction_screen(screen, virtual_screen)
if key == "end":
    send_trigger(TRIGGER["EXPERIMENT_END"])
    pygame.quit()
    sys.exit()

TOTAL_TRIALS = 25
FEEDBACK_DUR = 4000  # 与 MI 阶段时长一致，想象时间 = 执行时间
end_experiment = False
all_scores = []      # 收集所有 Block 的自评分数，最终导出 CSV

# ── 预生成全部 150 试次（三种任务各 50），分为 6 个 Block ──
_all_trials = ["左"] * 50 + ["右"] * 50 + ["空白"] * 50
random.shuffle(_all_trials)
_block_trials = [_all_trials[i * TOTAL_TRIALS:(i + 1) * TOTAL_TRIALS] for i in range(NUM_BLOCKS)]

# ── 全局角色选择（一次运行全程不变）──────────────────────
char_idx = random.randrange(len(ALL_CHARS))
char_base = ALL_CHARS[char_idx]
char_name = ["Mario", "Peach", "Luigi"][char_idx]
char_y_offsets = [0, -4, 4]
print(f"[CHAR] 本局角色: {char_name}")

# ── 背景序列：5 个 Block 各不同，不连续重复 ──────────────
_block_bgs = []
_pool = list(range(len(bg_options)))
random.shuffle(_pool)
for i in range(NUM_BLOCKS):
    if not _pool:
        # 用完一轮后重新洗牌，避免与上一个重复
        _pool = list(range(len(bg_options)))
        random.shuffle(_pool)
        if _pool[0] == _block_bgs[-1]:
            _pool[0], _pool[-1] = _pool[-1], _pool[0]
    _block_bgs.append(_pool.pop(0))

# ══════════════════════════════════════════════════════════════
# 学习试次（正式实验前，左右各 5 次，共 10 次，含虚线引导）
# ══════════════════════════════════════════════════════════════
print("[LEARN] ===== 学习试次阶段开始 =====")
LEARN_TRIALS_COUNT = 10
_learn_pool = ["左"] * 5 + ["右"] * 5
random.shuffle(_learn_pool)

# 学习试次使用第一个 Block 的背景
current_bg = bg_options[_block_bgs[0]]
print(f"[LEARN] 背景: {bg_names[_block_bgs[0]]}")

for learn_idx, learn_type in enumerate(_learn_pool):
    if end_experiment:
        break

    # 使用已选角色
    mario_stand = char_base
    MARIO_Y = 116 + char_y_offsets[char_idx]

    # 金币位置（学习试次不含空白，只有左/右）
    COIN_Y = 136
    if learn_type == "左":
        stage_coin_x = MARIO_X - 80
        stage_coin_y = COIN_Y
        mario_stand = pygame.transform.flip(char_base, True, False)
    else:  # 右
        stage_coin_x = MARIO_X + 80
        stage_coin_y = COIN_Y
        mario_stand = char_base

    # 虚线端点
    mario_center = (MARIO_X + 18, MARIO_Y + 24)
    coin_center = (stage_coin_x + 10, stage_coin_y + 10)
    learn_hand = "左手" if learn_type == "左" else "右手"

    # ── 1. CUE（2s，含虚线引导）────────────────────────────
    cue_start = pygame.time.get_ticks()
    CUE_DUR = 2000
    while pygame.time.get_ticks() - cue_start < CUE_DUR:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
        draw_growing_dashed_line(virtual_screen, mario_center, coin_center,
                                 1.0, COLOR_WHITE)

        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(virtual_screen,
                     (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

        draw_centered_text(screen, f"【学习试次 {learn_idx+1}/{LEARN_TRIALS_COUNT}：{learn_hand}想象】",
                           UI_CENTER_Y, UI_TEXT_COLOR)
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            break
        if key == "end":
            end_experiment = True
            break

    if end_experiment:
        break

    # ── 2. 准备（1s，保留虚线）────────────────────────────
    ready_start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - ready_start < 1000:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
        draw_growing_dashed_line(virtual_screen, mario_center, coin_center,
                                 1.0, COLOR_WHITE)

        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(virtual_screen,
                     (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

        draw_centered_text(screen, "准备", UI_CENTER_Y, UI_HINT_COLOR)
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            break
        if key == "end":
            end_experiment = True
            break

    if end_experiment:
        break

    # ── 3. 开始（1s，保留虚线）────────────────────────────
    go_start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - go_start < 1000:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
        draw_growing_dashed_line(virtual_screen, mario_center, coin_center,
                                 1.0, COLOR_WHITE)

        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(virtual_screen,
                     (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

        draw_centered_text(screen, "开始", UI_CENTER_Y, UI_HINT_COLOR)
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            break
        if key == "end":
            end_experiment = True
            break

    if end_experiment:
        break

    # ── 4. MI 运动想象（4s，保留虚线）──────────────────────
    mi_start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - mi_start < 4000:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        draw_growing_dashed_line(virtual_screen, mario_center, coin_center,
                                 1.0, COLOR_WHITE)

        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(virtual_screen,
                     (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            break
        if key == "end":
            end_experiment = True
            break

    if end_experiment:
        break

    # ── 5. Feedback（4s，Mario 跑向金币）───────────────────
    anim_start = pygame.time.get_ticks()
    coin_eaten = False
    MARIO_TARGET_LEFT_X = MARIO_X - 80
    MARIO_TARGET_RIGHT_X = MARIO_X + 80

    while pygame.time.get_ticks() - anim_start < FEEDBACK_DUR:
        progress = (pygame.time.get_ticks() - anim_start) / FEEDBACK_DUR
        draw_retro_scenery(virtual_screen)

        if learn_type == "左":
            mario_x_now = MARIO_X - int((MARIO_X - MARIO_TARGET_LEFT_X) * progress)
            virtual_screen.blit(mario_stand, (mario_x_now, MARIO_Y))
            if not coin_eaten:
                virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            else:
                for i in range(6):
                    angle = i * (2 * math.pi / 6)
                    px = stage_coin_x + 10 + int(math.cos(angle) * 12)
                    py = stage_coin_y + 10 + int(math.sin(angle) * 12)
                    pygame.draw.circle(virtual_screen, COLOR_TEXT_GOLD, (px, py), 2)
            if progress > 0.95 and not coin_eaten:
                coin_eaten = True
                coin_count += 1
                if coin_sound:
                    coin_sound.play()
        else:  # 右
            mario_x_now = MARIO_X + int((MARIO_TARGET_RIGHT_X - MARIO_X) * progress)
            virtual_screen.blit(mario_stand, (mario_x_now, MARIO_Y))
            if not coin_eaten:
                virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            else:
                for i in range(6):
                    angle = i * (2 * math.pi / 6)
                    px = stage_coin_x + 10 + int(math.cos(angle) * 12)
                    py = stage_coin_y + 10 + int(math.sin(angle) * 12)
                    pygame.draw.circle(virtual_screen, COLOR_TEXT_GOLD, (px, py), 2)
            if progress > 0.95 and not coin_eaten:
                coin_eaten = True
                coin_count += 1
                if coin_sound:
                    coin_sound.play()

        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(virtual_screen,
                     (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            break
        if key == "end":
            end_experiment = True
            break

    if end_experiment:
        break

    # ── 6. 定格期（1.2s）───────────────────────────────────
    freeze_start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - freeze_start < 1200:
        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.scale(virtual_screen,
                     (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))
        pygame.display.flip()
        key = handle_events()
        if key == "skip_block":
            break
        if key == "end":
            end_experiment = True
            break

print(f"[LEARN] ===== 学习试次阶段结束（获得 {coin_count} 枚金币）=====")

# ── 实验开始前闭眼静息 90s ─────────────────────────────────
key = run_rest_block(screen, virtual_screen, duration_ms=90000, hint_text="【闭眼静息中】", trigger_start=TRIGGER["REST_CLOSED_START"], trigger_end=TRIGGER["REST_CLOSED_END"])
if key == "end":
    send_trigger(TRIGGER["EXPERIMENT_END"])
    pygame.quit()
    sys.exit()

for block_idx in range(NUM_BLOCKS):
    if end_experiment:
        break

    # ── BLOCK 开始 ──────────────────────────────────────────────
    send_trigger(TRIGGER["BLOCK_START"])
    print(f"[TRIGGER] BLOCK_START Block {block_idx + 1}")

    # 使用全局角色
    mario_stand = char_base
    MARIO_Y = 116 + char_y_offsets[char_idx]
    print(f"[CHAR] Block {block_idx + 1} 角色: {char_name} (Y={MARIO_Y})")

    # 使用预分配的背景
    bg_idx = _block_bgs[block_idx]
    current_bg = bg_options[bg_idx]
    print(f"[BG] Block {block_idx + 1} 背景: {bg_names[bg_idx]}")

    trials = _block_trials[block_idx]
    skip_current_block = False

    for trial_idx, trial_type in enumerate(trials):
        if skip_current_block or end_experiment:
            break

        # 用数字编码方便后续分析：左=1，右=2，空白=3
        if trial_type == "左":
            class_id = 1
        elif trial_type == "右":
            class_id = 2
        else:
            class_id = 3

        # 金币初始化：左=金币在Mario左侧，右=金币在Mario右侧，空白不显示金币
        COIN_Y = 136  # 固定金币Y坐标，不随角色浮动
        if trial_type == "左":
            stage_coin_x = MARIO_X - 80
            stage_coin_y = COIN_Y
        elif trial_type == "右":
            stage_coin_x = MARIO_X + 80
            stage_coin_y = COIN_Y
        else:  # 空白对照：金币放画面外不显示
            stage_coin_x, stage_coin_y = -100, -100

        # 角色朝向与运动方向一致：左任务面朝左，右任务/空白面朝右
        if trial_type == "左":
            mario_stand = pygame.transform.flip(char_base, True, False)
        else:
            mario_stand = char_base

        # ── 2. CUE（任务提示 + 金币预览，无虚线）────────────────
        send_marker_cue = f"CUE_START_B{block_idx+1}_T{trial_idx+1}_C{class_id}"
        print(f"[TRIGGER] {send_marker_cue}")
        cue_start = pygame.time.get_ticks()
        CUE_DUR = 2000  # 总时长 2s

        while pygame.time.get_ticks() - cue_start < CUE_DUR:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))

            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            if trial_type == "空白":
                draw_centered_text(screen, "【当前任务：保持静止】", UI_CENTER_Y, UI_TEXT_COLOR)
            else:
                cue_hand = "左手" if trial_type == "左" else "右手"
                draw_centered_text(screen, f"【当前任务：{cue_hand}想象】", UI_CENTER_Y, UI_TEXT_COLOR)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events()
            if key == "skip_block":
                skip_current_block = True; break
            if key == "end":
                end_experiment = True; break

        send_marker_cue_end = f"CUE_END_B{block_idx+1}_T{trial_idx+1}_C{class_id}"
        print(f"[TRIGGER] {send_marker_cue_end}")

        if skip_current_block or end_experiment:
            break

        # ── 3. 准备开始（自动1秒推进）──────────────────────────
        ready_start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - ready_start < 1000:
            draw_retro_scenery(virtual_screen)
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
            screen.fill((0, 0, 0))
            screen.blit(pygame.transform.scale(virtual_screen, (GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE)), (OFFSET_X, OFFSET_Y))

            draw_centered_text(screen, "准备", UI_CENTER_Y, UI_HINT_COLOR)
            draw_progress_bar(screen, trial_idx, TOTAL_TRIALS, block_idx, NUM_BLOCKS)
            pygame.display.flip()
            key = handle_events()
            if key == "skip_block":
                skip_current_block = True; break
            if key == "end":
                end_experiment = True; break

        if skip_current_block or end_experiment:
            break

        # ── 3.5. 开始 ─────────────────────────────────────────
        key = run_go(screen, virtual_screen, trial_idx, block_idx)
        if key == "skip_block":
            skip_current_block = True
        elif key == "end":
            end_experiment = True

        if skip_current_block or end_experiment:
            break

        # ── 4. MI（静态画面，无任何动画）─────────────────────────
        if trial_type == "左":
            mi_key_start = "MI_START_LEFT"
            mi_key_end = "MI_END_LEFT"
        elif trial_type == "右":
            mi_key_start = "MI_START_RIGHT"
            mi_key_end = "MI_END_RIGHT"
        else:
            mi_key_start = "MI_START_BLANK"
            mi_key_end = "MI_END_BLANK"
        send_trigger(TRIGGER[mi_key_start])
        print(f"[TRIGGER] {mi_key_start} B{block_idx+1} T{trial_idx+1}")
        mi_start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - mi_start < 4000:
            draw_retro_scenery(virtual_screen)
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

        # ── 5. FEEDBACK（空白任务跳过，直接进定格）─────
        if trial_type != "空白":
            anim_start = pygame.time.get_ticks()
            coin_eaten = False

            # 预计算 Mario 目标位置（跑到金币处）
            MARIO_TARGET_LEFT_X = MARIO_X - 80   # 左：Mario 跑到左边金币处
            MARIO_TARGET_RIGHT_X = MARIO_X + 80  # 右：Mario 跑到右边金币处

            while pygame.time.get_ticks() - anim_start < FEEDBACK_DUR:
                progress = (pygame.time.get_ticks() - anim_start) / FEEDBACK_DUR

                draw_retro_scenery(virtual_screen)

                if trial_type == "左":
                    # Mario 向左跑（已在 trial 开始时翻面）
                    mario_x_now = MARIO_X - int((MARIO_X - MARIO_TARGET_LEFT_X) * progress)
                    virtual_screen.blit(mario_stand, (mario_x_now, MARIO_Y))
                    if not coin_eaten:
                        virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
                    else:
                        # 吃币后持续显示粒子特效
                        for i in range(6):
                            angle = i * (2 * math.pi / 6)
                            px = stage_coin_x + 10 + int(math.cos(angle) * 12)
                            py = stage_coin_y + 10 + int(math.sin(angle) * 12)
                            pygame.draw.circle(virtual_screen, COLOR_TEXT_GOLD, (px, py), 2)
                    # 到达金币时触发吃币
                    if progress > 0.95 and not coin_eaten:
                        coin_eaten = True
                        coin_count += 1
                        if coin_sound:
                            coin_sound.play()

                elif trial_type == "右":
                    # Mario 向右跑，面朝右（默认方向）
                    mario_x_now = MARIO_X + int((MARIO_TARGET_RIGHT_X - MARIO_X) * progress)
                    virtual_screen.blit(mario_stand, (mario_x_now, MARIO_Y))
                    if not coin_eaten:
                        virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
                    else:
                        # 吃币后持续显示粒子特效
                        for i in range(6):
                            angle = i * (2 * math.pi / 6)
                            px = stage_coin_x + 10 + int(math.cos(angle) * 12)
                            py = stage_coin_y + 10 + int(math.sin(angle) * 12)
                            pygame.draw.circle(virtual_screen, COLOR_TEXT_GOLD, (px, py), 2)
                    # 到达金币时触发吃币
                    if progress > 0.95 and not coin_eaten:
                        coin_eaten = True
                        coin_count += 1
                        if coin_sound:
                            coin_sound.play()

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

    # ── BLOCK 结束 ──────────────────────────────────────────────
    send_trigger(TRIGGER["BLOCK_END"])
    print(f"[TRIGGER] BLOCK_END Block {block_idx + 1}")

    if end_experiment:
        break

    key = run_block_complete_screen(screen, virtual_screen, block_idx, NUM_BLOCKS)
    if key == "end":
        break

    # ── 自评问卷 ─────────────────────────────────────────────
    rpt_size_l = int(SCREEN_H * 0.04)
    rpt_size_s = int(SCREEN_H * 0.028)
    if FONT_PATH:
        rpt_font_l = pygame.font.Font(FONT_PATH, rpt_size_l)
        rpt_font_s = pygame.font.Font(FONT_PATH, rpt_size_s)
    else:
        rpt_font_l = safe_sysfont("SimHei", rpt_size_l)
        rpt_font_s = safe_sysfont("SimHei", rpt_size_s)
    report_screen = SelfReportScreen(screen, rpt_font_l, rpt_font_s)
    scores = report_screen.run(block_idx + 1)
    if scores is not None:
        scores["block"] = block_idx + 1
        scores["total_coins"] = coin_count
        scores["extended_rest_s"] = 0  # 默认值，后续更新
        all_scores.append(scores)
        print(f"[SELFREPORT] Block {block_idx + 1}: {scores}")

    if coin_sound:
        coin_sound.play()
    _ext_s = [0]
    key = run_rest_block(screen, virtual_screen, duration_ms=15000, hint_text="【休息放空中，请稍放松】", extend_key=True, _extended_out=_ext_s)
    if all_scores:
        all_scores[-1]["extended_rest_s"] = _ext_s[0]
    if key == "end":
        break


# ── 导出自评 CSV ─────────────────────────────────────────────
if all_scores:
    import csv
    import datetime
    csv_path = _os.path.join(_BASE_DIR, "logs",
        f"self_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    _os.makedirs(_os.path.dirname(csv_path), exist_ok=True)
    fields = ["block", "cognitive_fatigue", "physical_fatigue", "total_coins", "extended_rest_s"]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_scores)
    print(f"[SELFREPORT] CSV 已导出: {csv_path}")

send_trigger(TRIGGER["EXPERIMENT_END"])
pygame.quit()
