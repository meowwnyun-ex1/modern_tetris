#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Renderer
----------------------
คลาสสำหรับการแสดงผลกราฟิกทั้งหมด
"""

import pygame
import math
import random
from pygame import gfxdraw

from core.constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLACK,
    WHITE,
    DARK_GRAY,
    BOARD_X,
    BOARD_Y,
    BOARD_WIDTH,
    BOARD_HEIGHT,
    GRID_SIZE,
)
from graphics.effects import BloomEffect, ShakeEffect


class Renderer:
    """คลาสสำหรับการแสดงผลกราฟิก"""

    def __init__(self, screen, config):
        """
        สร้างเรนเดอร์เรอร์ใหม่

        Args:
            screen (pygame.Surface): พื้นผิวหลักสำหรับการแสดงผล
            config (dict): การตั้งค่าเกม
        """
        self.screen = screen
        self.config = config

        # เก็บขนาดหน้าจอ
        self.width, self.height = screen.get_size()

        # โหลดธีม
        self.theme = config["graphics"]["theme"]

        # สร้างเอฟเฟกต์
        self.bloom_effect = BloomEffect(threshold=100, blur_passes=2, intensity=0.8)
        self.shake_effect = ShakeEffect()

        # โหลดรูปภาพพื้นหลัง
        try:
            self.background = pygame.image.load(
                f"assets/images/backgrounds/{self.theme}_bg.png"
            )
            self.background = pygame.transform.scale(
                self.background, (self.width, self.height)
            )
        except:
            # สร้างพื้นหลังเอง
            self.background = self._create_background()

        # พื้นหลังความเร็วสูง (สำหรับการเคลื่อนที่อย่างรวดเร็ว)
        self.high_speed_bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._create_high_speed_background()

        # พื้นผิวสำหรับเอฟเฟกต์
        self.overlay_surface = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        self.glow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # นำเข้าฟอนต์
        pygame.font.init()
        try:
            self.title_font = pygame.font.Font(
                f'assets/fonts/{self.config["ui"]["font"]}.ttf', 48
            )
            self.large_font = pygame.font.Font(
                f'assets/fonts/{self.config["ui"]["font"]}.ttf', 36
            )
            self.medium_font = pygame.font.Font(
                f'assets/fonts/{self.config["ui"]["font"]}.ttf', 24
            )
            self.small_font = pygame.font.Font(
                f'assets/fonts/{self.config["ui"]["font"]}.ttf', 18
            )
        except:
            # ใช้ฟอนต์ระบบถ้าโหลดไม่ได้
            self.title_font = pygame.font.SysFont("Arial", 48)
            self.large_font = pygame.font.SysFont("Arial", 36)
            self.medium_font = pygame.font.SysFont("Arial", 24)
            self.small_font = pygame.font.SysFont("Arial", 18)

    def _create_background(self):
        """
        สร้างพื้นหลังเกมตามธีม

        Returns:
            pygame.Surface: พื้นหลังที่สร้างขึ้น
        """
        bg = pygame.Surface((self.width, self.height))

        if self.theme == "neon":
            # สร้างพื้นหลังสีดำด้วยเส้นกริดและจุดสีนีออน
            bg.fill((0, 0, 0))

            # วาดเส้นกริดในแนวนอน
            for y in range(0, self.height, 40):
                line_color = (0, 50, 80, 50)
                pygame.draw.line(bg, line_color, (0, y), (self.width, y), 1)

            # วาดเส้นกริดในแนวตั้ง
            for x in range(0, self.width, 40):
                line_color = (0, 50, 80, 50)
                pygame.draw.line(bg, line_color, (x, 0), (x, self.height), 1)

            # วาดจุดสีนีออนแบบสุ่ม
            for _ in range(100):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                radius = random.randint(1, 3)
                brightness = random.randint(50, 200)
                color = (0, brightness, brightness)
                pygame.gfxdraw.filled_circle(bg, x, y, radius, color)
                # เพิ่มเอฟเฟกต์เรืองแสง
                pygame.gfxdraw.aacircle(
                    bg, x, y, radius + 1, (0, brightness // 2, brightness // 2)
                )

        elif self.theme == "retro":
            # สร้างพื้นหลังแบบ retro
            bg.fill((0, 0, 50))

            # วาดเส้นกริดแบบ retro
            for y in range(0, self.height, 20):
                color = (200, 50, 50) if y % 40 == 0 else (100, 50, 50)
                pygame.draw.line(bg, color, (0, y), (self.width, y), 1)

            for x in range(0, self.width, 20):
                color = (200, 50, 50) if x % 40 == 0 else (100, 50, 50)
                pygame.draw.line(bg, color, (x, 0), (x, self.height), 1)

        elif self.theme == "minimalist":
            # สร้างพื้นหลังแบบเรียบง่าย
            bg.fill((240, 240, 240))

            # วาดจุดสีอ่อนแบบสุ่ม
            for _ in range(200):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                radius = random.randint(1, 2)
                color = (220, 220, 220)
                pygame.gfxdraw.filled_circle(bg, x, y, radius, color)

        else:
            # ธีมเริ่มต้น (สีดำล้วน)
            bg.fill(BLACK)

        return bg

    def _create_high_speed_background(self):
        """สร้างพื้นหลังสำหรับความเร็วสูง (เส้นพุ่งลงด้านล่าง)"""
        self.high_speed_bg.fill((0, 0, 0, 0))  # โปร่งใส

        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            length = random.randint(10, 50)
            color = (0, 200, 255, random.randint(20, 100))

            pygame.draw.line(self.high_speed_bg, color, (x, y), (x, y + length), 1)

    def render_background(self, level=1):
        """
        วาดพื้นหลัง

        Args:
            level (int, optional): ระดับความเร็วของเกม
        """
        # วาดพื้นหลังหลัก
        self.screen.blit(self.background, (0, 0))

        # วาดเอฟเฟกต์พื้นหลังความเร็วสูงถ้าระดับสูงพอ
        if level > 10:
            speed_alpha = min(255, (level - 10) * 25)
            high_speed_copy = self.high_speed_bg.copy()
            high_speed_copy.set_alpha(speed_alpha)
            self.screen.blit(high_speed_copy, (0, 0))

    def render_pause_overlay(self):
        """วาดเอฟเฟกต์ซ้อนทับเมื่อหยุดเกม"""
        # วาดพื้นหลังโปร่งใสสีดำ
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # สีดำโปร่งแสง
        self.screen.blit(overlay, (0, 0))

        # วาดข้อความ "PAUSED"
        text = self.large_font.render("หยุดชั่วคราว", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 40))
        self.screen.blit(text, text_rect)

        # วาดคำแนะนำ
        hint = self.medium_font.render("กด ESC หรือ P เพื่อเล่นต่อ", True, (200, 200, 200))
        hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 20))
        self.screen.blit(hint, hint_rect)

    def render_game_over(self, score, level, lines):
        """
        วาดหน้าจอเกมจบ

        Args:
            score (int): คะแนนสุดท้าย
            level (int): ระดับสุดท้าย
            lines (int): จำนวนแถวที่ล้างได้
        """
        # วาดพื้นหลังโปร่งใสสีดำ
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # สีดำโปร่งแสงเข้มกว่า
        self.screen.blit(overlay, (0, 0))

        # วาดข้อความ "GAME OVER"
        text = self.title_font.render("เกมจบ", True, (255, 50, 50))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(text, text_rect)

        # วาดคะแนน
        score_text = self.large_font.render(f"คะแนน: {score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(
            center=(self.width // 2, self.height // 2 - 40)
        )
        self.screen.blit(score_text, score_rect)

        # วาดระดับและแถวที่ล้าง
        level_text = self.medium_font.render(f"ระดับ: {level}", True, (200, 200, 200))
        level_rect = level_text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(level_text, level_rect)

        lines_text = self.medium_font.render(f"แถวที่ล้าง: {lines}", True, (200, 200, 200))
        lines_rect = lines_text.get_rect(
            center=(self.width // 2, self.height // 2 + 30)
        )
        self.screen.blit(lines_text, lines_rect)

        # วาดคำแนะนำ
        hint = self.medium_font.render(
            "กด Enter เพื่อกลับไปยังเมนูหลัก", True, (200, 200, 200)
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 100))
        self.screen.blit(hint, hint_rect)

    def apply_bloom(self, surface):
        """
        ใช้เอฟเฟกต์ Bloom กับพื้นผิว

        Args:
            surface (pygame.Surface): พื้นผิวที่จะใช้เอฟเฟกต์
        """
        if self.config["graphics"]["bloom_effect"]:
            bloomed_surface = self.bloom_effect.apply(surface)
            self.screen.blit(bloomed_surface, (0, 0))

    def apply_shake(self, duration=0.3, intensity=5):
        """
        เริ่มเอฟเฟกต์การสั่น

        Args:
            duration (float): ระยะเวลาของการสั่น (วินาที)
            intensity (float): ความแรงของการสั่น (พิกเซล)
        """
        if self.config["graphics"]["shake_effect"]:
            self.shake_effect.start(intensity, duration)

    def update_effects(self, dt):
        """
        อัปเดตเอฟเฟกต์ทั้งหมด

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)

        Returns:
            tuple: (offset_x, offset_y) การเคลื่อนที่ของหน้าจอจากเอฟเฟกต์การสั่น
        """
        # อัปเดตเอฟเฟกต์การสั่น
        return self.shake_effect.update(dt)

    def render_loading_screen(self, progress=0):
        """
        วาดหน้าจอโหลด

        Args:
            progress (float): ความคืบหน้าของการโหลด (0-1)
        """
        # ล้างหน้าจอ
        self.screen.fill(BLACK)

        # วาดข้อความ "LOADING"
        text = self.large_font.render("กำลังโหลด...", True, WHITE)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 50))
        self.screen.blit(text, text_rect)

        # วาดแถบความคืบหน้า
        bar_width = self.width * 0.6
        bar_height = 20
        bar_x = (self.width - bar_width) // 2
        bar_y = self.height // 2

        # กรอบ
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # ความคืบหน้า
        progress_width = bar_width * progress
        pygame.draw.rect(
            self.screen, (0, 200, 255), (bar_x, bar_y, progress_width, bar_height)
        )

        # อัปเดตหน้าจอ
        pygame.display.flip()

    def render_text_with_outline(
        self, text, font, color, outline_color, position, outline_width=2
    ):
        """
        วาดข้อความพร้อมเส้นขอบ

        Args:
            text (str): ข้อความที่จะวาด
            font (pygame.font.Font): ฟอนต์
            color (tuple): สีข้อความ (RGB)
            outline_color (tuple): สีเส้นขอบ (RGB)
            position (tuple): ตำแหน่ง (x, y)
            outline_width (int): ความหนาของเส้นขอบ
        """
        # วาดเส้นขอบ
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    outline = font.render(text, True, outline_color)
                    self.screen.blit(outline, (position[0] + dx, position[1] + dy))

        # วาดข้อความหลัก
        main_text = font.render(text, True, color)
        self.screen.blit(main_text, position)

    def render_button(
        self,
        rect,
        text,
        font,
        color=(255, 255, 255),
        bg_color=(50, 50, 50),
        highlight=False,
    ):
        """
        วาดปุ่มกด

        Args:
            rect (pygame.Rect): ขอบเขตของปุ่ม
            text (str): ข้อความบนปุ่ม
            font (pygame.font.Font): ฟอนต์
            color (tuple): สีข้อความ (RGB)
            bg_color (tuple): สีพื้นหลัง (RGB)
            highlight (bool): ไฮไลท์หรือไม่

        Returns:
            pygame.Rect: ขอบเขตของปุ่ม
        """
        # วาดพื้นหลังปุ่ม
        if highlight:
            # สีไฮไลท์
            pygame.draw.rect(
                self.screen,
                (bg_color[0] + 50, bg_color[1] + 50, bg_color[2] + 50),
                rect,
            )
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
        else:
            pygame.draw.rect(self.screen, bg_color, rect)
            pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)

        # วาดข้อความ
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

        return rect
