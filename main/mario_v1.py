# 初版 想象完按空格执行动作
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

pygame.font.init()


def safe_sysfont(name, size):
    try:
        return pygame.font.SysFont(name, size)
    except:
        return pygame.font.Font(None, size)

# NES原版比例微型画布，最后统一放大3倍，完美保留硬核像素风
GAME_WIDTH, GAME_HEIGHT = 256, 192
SCALE = 3
screen = pygame.display.set_mode((GAME_WIDTH * SCALE, GAME_HEIGHT * SCALE))
pygame.display.set_caption("Super Mario Bros. - 图像重制版脑机接口实验")

# NES经典怀旧色彩
COLOR_SKY = (92, 148, 252)       
COLOR_BRICK_MAIN = (200, 76, 12)  
COLOR_BRICK_SHADOW = (0, 0, 0)    
COLOR_BRICK_LIGHT = (252, 188, 176) 
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_GOLD = (252, 228, 160) 
COLOR_CLOUD_BLUE = (148, 212, 252) 

virtual_screen = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))

# 初始化中文字体
# 检查当前文件夹下有没有 zpix.ttf 像素字体，有就用它，没有就用系统字体保底
FONT_PATH = _p(_FONT_DIR, "zpix.ttf") if os.path.exists(_p(_FONT_DIR, "zpix.ttf")) else None

if FONT_PATH:
    # Font(字体路径, 字体大小) -> 变圆润可爱的像素字
    font = pygame.font.Font(FONT_PATH, 30)
    small_font = pygame.font.Font(FONT_PATH, 14)
else:
    # 保底机制，防止你还没下载字体时程序报错
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)
    

# 实验逻辑变量
trials = ['横'] * 15 + ['竖'] * 15 + ['空白'] * 10
random.shuffle(trials)

# 配合无损放大，我们在微型画布上的基础坐标
MARIO_X, MARIO_Y = 30, 116
GOOMBA_X, GOOMBA_Y = 180, 140
coin_count = 0

# ==========================================
# 2. 载入并处理外部像素图片
# ==========================================
def load_and_scale_sprite(img_path, target_size):
    """安全载入图片并缩放到适应微型画布的像素尺寸"""
    if os.path.exists(img_path):
        # convert_alpha() 保证透明背景不裁剪
        img = pygame.image.load(img_path).convert_alpha()
        return pygame.transform.scale(img, target_size)
    else:
        # 保底逻辑：如果找不到图片，生成一个纯色块代替，防止程序崩溃
        print(f"[警告] 未找到 {img_path}，已生成替代色块。")
        surf = pygame.Surface(target_size, pygame.SRCALPHA)
        surf.fill((255, 0, 0) if "mario" in img_path else (165, 66, 0))
        return surf

# 缩放到适合 256x192 虚拟画幅的大小（马里奥宽16高20左右，板栗仔16x16）
mario_stand = load_and_scale_sprite(_p(_IMG_DIR, "mario.png"), (36, 48))
goomba_normal = load_and_scale_sprite(_p(_IMG_DIR, "goomba.png"), (18, 18))
mario_cap = load_and_scale_sprite(_p(_IMG_DIR, "cap.png"), (14, 10))
ui_coin_img = load_and_scale_sprite(_p(_IMG_DIR, "coin.png"), (16, 16))
stage_coin_img = load_and_scale_sprite(_p(_IMG_DIR, "coin.png"), (20, 20))



# 制作被踩扁的板栗仔（纵向压扁）
goomba_flat = pygame.transform.scale(goomba_normal, (18, 6))

# ==========================================
# 3. 经典 NES 场景绘制
# ==========================================
def draw_pixel_cloud(surface, x, y):
    """手工拼出一朵原汁原味的 NES 像素黑边复古云"""
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
    """绘制带有点阵花纹的 100% 原版地面、和白云"""
    surface.fill(COLOR_SKY)
    
    # 1. 绘制浮空的原版像素白云
    draw_pixel_cloud(surface, 8, 25)   
    draw_pixel_cloud(surface, 165, 30)  
    draw_pixel_cloud(surface, 195, 15)  
    
    # 2. 绘制多层像素草地泥土砖块（156px往下是地面）
    for bx in range(0, GAME_WIDTH, 16):
        for by in range(156, GAME_HEIGHT, 16):
            pygame.draw.rect(surface, COLOR_BRICK_MAIN, (bx, by, 16, 16))
            pygame.draw.rect(surface, COLOR_BRICK_SHADOW, (bx, by, 16, 16), 1)
            pygame.draw.line(surface, COLOR_BRICK_LIGHT, (bx+1, by+1), (bx+14, by+1), 1)
            pygame.draw.line(surface, COLOR_BRICK_LIGHT, (bx+1, by+1), (bx+1, by+14), 1)



    # 1. 用纯代码画一个精致闪亮的 8-bit 像素金币椭圆图标
    # === 替换为完美的真实 8-bit 像素金币贴图 ===
    surface.blit(ui_coin_img, (7, 4))  # 完美的像素金币挂在左上角
    
    # 2. 渲染带有可爱像素字体的金币文本（例如：x05）
    # 由于这里是在 256x192 的微型画布上绘制，我们用自带的较小字体渲染
    coin_txt = small_font.render(f"x{coin_count:02d}", True, (255, 255, 255))
    surface.blit(coin_txt, (22, 4))
    

            
def run_game_start_menu(surface, game_width, game_height, scale):
    """
    一个复古的 8-bit 像素风游戏开始菜单界面。
    它会持续循环直到被试按下键盘上的【空格键】。
    """
    in_menu = True
    clock = pygame.time.Clock()
    
    # 局部变量定义，用于绘制菜单和文字
    FONT_PATH = _p(_FONT_DIR, "zpix.ttf") if os.path.exists(_p(_FONT_DIR, "zpix.ttf")) else None
    if FONT_PATH:
        HD_FONT_TITLE = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), 50)
        HD_FONT_TEXT = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), 35)
        PIXEL_FONT_SMALL = pygame.font.Font(FONT_PATH, 12)
    else:
        HD_FONT_TITLE = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), 50)
        HD_FONT_TEXT = pygame.font.Font(_p(_FONT_DIR, "SuperMario256.ttf"), 35)
        PIXEL_FONT_SMALL = pygame.font.Font(FONT_PATH, 12)

    bg_img = pygame.image.load(_p(_IMG_DIR, "background.png")).convert()
    bg_img = pygame.transform.scale(bg_img, (game_width * scale, game_height * scale))
        
    PIXEL_FONT_SMALL = pygame.font.Font(FONT_PATH, 12)
##    COLOR_MENU_BG = (92, 148, 252)      # 复古暗色菜单背景
    COLOR_BRICK_MAIN = (200, 76, 12)  # 砖块/板栗仔主色（红棕）
    COLOR_TEXT_GOLD = (252, 216, 40) # 怀旧金色文字
    COLOR_WHITE = (255, 255, 255)
    COLOR_BRICK_SHADOW = (15, 15, 35)
    
    # 建立一个局部的微型渲染画布，用于处理拉伸
    virtual_surf = pygame.Surface((game_width, game_height))
    
    while in_menu:
##        virtual_surf.fill(COLOR_MENU_BG)
        surface.blit(bg_img, (0, 0))
        
        
        # 将微型画布放大渲染到主屏幕上，确保硬边缘
##        pygame.transform.scale(virtual_surf, (game_width*scale, game_height*scale), surface)
        
        # --- 在高清叠加层（surface）上直接渲染精致文字 ---
        # 1. 游戏大标题：SUPER BCI MARIO（带复古阴影）
        title_surf = HD_FONT_TITLE.render("SUPER BCI MARIO", True, COLOR_BRICK_MAIN)
        title_shadow = HD_FONT_TITLE.render("SUPER BCI MARIO", True, COLOR_BRICK_SHADOW)
        surface.blit(title_shadow, (game_width * scale // 2 - title_surf.get_width() // 2 + 4, 104))
        surface.blit(title_surf, (game_width * scale // 2 - title_surf.get_width() // 2, 100))
        
        # 2. 模拟红白机闪烁效果的金色 "▶  START" 文字
        blink_val = (math.sin(pygame.time.get_ticks() * 0.007) + 1) / 2
        if blink_val > 0.3:
            start_text = HD_FONT_TEXT.render("START GAME", True, COLOR_TEXT_GOLD)
            surface.blit(start_text, (game_width * scale // 2 - start_text.get_width() // 2, 240))
            
        # 3. 底部的按键操控提示
        hint_text = PIXEL_FONT_SMALL.render("PRESS [SPACE] TO START", True, COLOR_WHITE)
        surface.blit(hint_text, (game_width * scale // 2 - hint_text.get_width() // 2, 450))
        
        pygame.display.flip()
        clock.tick(60) # 稳定60帧
        
        # 监听按键打破循环
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    in_menu = False
                    

#==============程序在进入 trial 循环前先运行菜单 =======
run_game_start_menu(screen, GAME_WIDTH, GAME_HEIGHT, SCALE)     


# ==========================================
# 4. 实验主循环状态机
# ==========================================
for trial_idx, trial_type in enumerate(trials):
    print(f"[MARKER] Trial {trial_idx+1} -> {trial_type}")
    
    # --- 1. REST 放空期 (1.5秒) ---
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < 3500:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
        
        pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

    # --- 2. CUE 提示期 (1.0秒) ---
  # 金币初始化，在 for 循环第一级
    if trial_type == '竖':
        stage_coin_x = MARIO_X + 6
        stage_coin_y = MARIO_Y - 27
    elif trial_type == '横':
        stage_coin_x = GOOMBA_X + 1
        stage_coin_y = GOOMBA_Y - 22
    else:
        stage_coin_x, stage_coin_y = -100, -100

    # --- CUE 提示期 ---
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < 2000:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
        virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))

##      辅助轨迹
##        if trial_type == '横':
##            for dx in range(MARIO_X+20, GOOMBA_X, 12):
##                virtual_screen.set_at((dx, MARIO_Y+10), COLOR_BRICK_LIGHT)
##        elif trial_type == '竖':
##            for step in range(6):
##                virtual_screen.set_at((MARIO_X+9, MARIO_Y - step*8), COLOR_WHITE)

        if trial_type == '竖':
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
        elif trial_type == '横':
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

        if trial_type == '竖' or trial_type == '横':
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))

        if trial_type == '空白':
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            elapsed_rest = pygame.time.get_ticks() - start
            zzz_offset = (elapsed_rest // 1500) % 3
            mario_zzz_y = MARIO_Y - 12 - (elapsed_rest % 600) // 40
            if zzz_offset >= 0:
                z_txt = small_font.render("z", True, COLOR_WHITE)
                virtual_screen.blit(z_txt, (MARIO_X + 12, mario_zzz_y))
            if zzz_offset >= 1:
                z_txt_2 = font.render("z", True, COLOR_WHITE)
                virtual_screen.blit(z_txt_2, (MARIO_X + 22, mario_zzz_y - 6))
            goomba_zzz_y = GOOMBA_Y - 10 - (elapsed_rest % 500) // 40
            if zzz_offset >= 0:
                z_txt_g1 = small_font.render("z", True, COLOR_WHITE)
                virtual_screen.blit(z_txt_g1, (GOOMBA_X + 6, goomba_zzz_y))
            if zzz_offset >= 1:
                z_txt_g2 = font.render("z", True, COLOR_WHITE)
                virtual_screen.blit(z_txt_g2, (GOOMBA_X + 14, goomba_zzz_y - 4))
        else:
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))

        pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
        pygame.display.flip()
        pygame.event.pump()



        


    # ← 注意：waiting_for_space 在 MI while 循环【外面】，和它平级
    waiting_for_space = True
    while waiting_for_space:
        draw_retro_scenery(virtual_screen)
        virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
        virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))

        # 横竖模式金币持续显示
        if trial_type in ['横', '竖']:
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))

        # 空白模式显示 Zzz
        if trial_type == '空白':
            elapsed_rest = pygame.time.get_ticks() - start
            zzz_offset = (elapsed_rest // 1500) % 3
            mario_zzz_y = MARIO_Y - 12 - (elapsed_rest % 800) // 40
            if zzz_offset >= 0:
                virtual_screen.blit(small_font.render("z", True, COLOR_WHITE), (MARIO_X + 12, mario_zzz_y))
            if zzz_offset >= 1:
                virtual_screen.blit(font.render("z", True, COLOR_WHITE), (MARIO_X + 22, mario_zzz_y - 6))

        # 先scale再贴提示文字，顺序不能反
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





    # --- 4. FEEDBACK 经典动态反馈 (1.0秒) ---

    
    anim_start = pygame.time.get_ticks()
    coin_eaten = False

    while pygame.time.get_ticks() - anim_start < 1000:
        progress = (pygame.time.get_ticks() - anim_start) / 1000.0
        draw_retro_scenery(virtual_screen)
        
        # 并在空中绘制这枚亮晶晶的金币
        if not coin_eaten and trial_type in ['横', '竖']:
            virtual_screen.blit(stage_coin_img, (stage_coin_x, stage_coin_y))
        
        # ------------------ 模式 1：横向任务（飞帽吃金币） ------------------
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
            
            # 帽子弹回时把金币抄走
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
                            
        # ------------------ 模式 2：竖向任务（马里奥跳跃吃金币） ------------------
        elif trial_type == '竖':
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            
            jump_offset = int(40 * (4 * progress * (1 - progress)))
            jump_y = MARIO_Y - jump_offset
            virtual_screen.blit(mario_stand, (MARIO_X, jump_y))
            
            # 跳到高点吃金币判定
            if jump_offset > 12 and not coin_eaten:
                coin_eaten = True
                coin_count += 1
            
            bullet_x = GOOMBA_X - int((GOOMBA_X + 20) * progress)
            if bullet_x > -10:
                pygame.draw.circle(virtual_screen, (16, 16, 24), (bullet_x, GOOMBA_Y + 10), 5)
                pygame.draw.circle(virtual_screen, (240, 240, 250), (bullet_x - 2, GOOMBA_Y + 8), 1)
                
        # ------------------ 模式 3：空白放空模式 ------------------
        else:
            virtual_screen.blit(mario_stand, (MARIO_X, MARIO_Y))
            virtual_screen.blit(goomba_normal, (GOOMBA_X, GOOMBA_Y))
            
        pygame.transform.scale(virtual_screen, (GAME_WIDTH*SCALE, GAME_HEIGHT*SCALE), screen)
        pygame.display.flip()
        pygame.event.pump()
        

    # --- 5. QUESTION 行为校验页 ---
##    if random.random() < 0.3:
##        answered = False
##        while not answered:
##            screen.fill((40, 40, 50))
##            q1 = font.render("【有效性检查】刚才3秒内你脑海在干嘛？", True, COLOR_WHITE)
##            q2 = small_font.render("按键回应：[1] 甩手飞帽(横)   [2] 垂直下砸(竖)   [3] 完全放空", True, COLOR_TEXT_GOLD)
##            screen.blit(q1, (50, 200))
##            screen.blit(q2, (50, 260))
##            pygame.display.flip()
##            
##            for event in pygame.event.get():
##                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
##                if event.type == pygame.KEYDOWN:
##                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3]: answered = True

pygame.quit()
