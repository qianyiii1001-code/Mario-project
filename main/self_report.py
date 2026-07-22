# -*- coding: utf-8 -*-
"""
Block间自评量表模块
三个维度，7点量表，数字键1-7直接选择，选完自动跳到下一维度。
"""

import pygame

DIMENSIONS = [
    {
        "key": "cognitive_fatigue",
        "question": "刚才这个Block里，完成想象任务感觉有多费力？",
        "anchor_low": "1 = 完全不费力",
        "anchor_high": "7 = 非常费力",
        "marker_name": "COGFATIGUE",
    },
    {
        "key": "physical_fatigue",
        "question": "刚才这个Block里，你感觉自己有多清醒/困倦？",
        "anchor_low": "1 = 非常困倦",
        "anchor_high": "7 = 非常清醒",
        "marker_name": "PHYSFATIGUE",
    },
]

COLOR_BG = (20, 20, 40)
COLOR_TEXT = (255, 255, 255)
COLOR_ANCHOR = (200, 200, 200)
COLOR_HIGHLIGHT = (255, 215, 0)
COLOR_PROGRESS = (120, 120, 160)


class SelfReportScreen:
    def __init__(self, screen, font_large, font_small, outlet=None, clock=None):
        self.screen = screen
        self.font_large = font_large
        self.font_small = font_small
        self.outlet = outlet
        self.clock = clock or pygame.time.Clock()

    def _render_dimension(self, dim, block_index, dim_index, total_dims):
        self.screen.fill(COLOR_BG)
        progress_text = self.font_small.render(
            f"Block {block_index} 评价  {dim_index + 1} / {total_dims}",
            True, COLOR_PROGRESS
        )
        self.screen.blit(progress_text,
            (self.screen.get_width() // 2 - progress_text.get_width() // 2, 60))

        question_text = self.font_large.render(dim["question"], True, COLOR_TEXT)
        self.screen.blit(question_text,
            (self.screen.get_width() // 2 - question_text.get_width() // 2, 200))

        num_options = 7
        spacing = 90
        start_x = self.screen.get_width() // 2 - (spacing * (num_options - 1)) // 2
        y = 350

        for i in range(1, num_options + 1):
            x = start_x + (i - 1) * spacing
            pygame.draw.circle(self.screen, (60, 60, 90), (x, y), 35, width=2)
            num_text = self.font_large.render(str(i), True, COLOR_TEXT)
            self.screen.blit(num_text, (x - num_text.get_width() // 2, y - num_text.get_height() // 2))

        low_text = self.font_small.render(dim["anchor_low"], True, COLOR_ANCHOR)
        high_text = self.font_small.render(dim["anchor_high"], True, COLOR_ANCHOR)
        self.screen.blit(low_text, (start_x - low_text.get_width() // 2, y + 60))
        self.screen.blit(high_text,
            (start_x + spacing * (num_options - 1) - high_text.get_width() // 2, y + 60))

        hint_text = self.font_small.render("按数字键 1-7 作答", True, COLOR_PROGRESS)
        self.screen.blit(hint_text,
            (self.screen.get_width() // 2 - hint_text.get_width() // 2, y + 140))

        pygame.display.flip()

    def run(self, block_index):
        scores = {}
        total_dims = len(DIMENSIONS)

        for dim_index, dim in enumerate(DIMENSIONS):
            answer = None
            while answer is None:
                self._render_dimension(dim, block_index, dim_index, total_dims)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        raise SystemExit
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return None  # ESC 跳过问卷
                        key_to_num = {
                            pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4,
                            pygame.K_5: 5, pygame.K_6: 6, pygame.K_7: 7,
                            pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3, pygame.K_KP4: 4,
                            pygame.K_KP5: 5, pygame.K_KP6: 6, pygame.K_KP7: 7,
                        }
                        if event.key in key_to_num:
                            answer = key_to_num[event.key]
                self.clock.tick(60)

            scores[dim["key"]] = answer
            # 选中反馈 — 高亮 200ms
            self._render_dimension_selected(dim, block_index, dim_index, total_dims, answer)
            pygame.time.wait(200)

        print(f"[SelfReport] Block {block_index} 自评: {scores}")
        return scores

    def _render_dimension_selected(self, dim, block_index, dim_index, total_dims, selected):
        self.screen.fill(COLOR_BG)
        progress_text = self.font_small.render(
            f"Block {block_index} 评价  {dim_index + 1} / {total_dims}",
            True, COLOR_PROGRESS
        )
        self.screen.blit(progress_text,
            (self.screen.get_width() // 2 - progress_text.get_width() // 2, 60))

        question_text = self.font_large.render(dim["question"], True, COLOR_TEXT)
        self.screen.blit(question_text,
            (self.screen.get_width() // 2 - question_text.get_width() // 2, 200))

        num_options = 7
        spacing = 90
        start_x = self.screen.get_width() // 2 - (spacing * (num_options - 1)) // 2
        y = 350

        for i in range(1, num_options + 1):
            x = start_x + (i - 1) * spacing
            is_sel = (i == selected)
            circle_color = COLOR_HIGHLIGHT if is_sel else (60, 60, 90)
            pygame.draw.circle(self.screen, circle_color, (x, y), 35,
                               width=0 if is_sel else 2)
            num_col = (20, 20, 40) if is_sel else COLOR_TEXT
            num_text = self.font_large.render(str(i), True, num_col)
            self.screen.blit(num_text, (x - num_text.get_width() // 2, y - num_text.get_height() // 2))

        pygame.display.flip()
