#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Game UI
---------------------
คลาสสำหรับส่วนติดต่อผู้ใช้ในเกม
"""

import pygame
import math
import time

from core.constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BOARD_X,
    BOARD_Y,
    BOARD_WIDTH,
    BOARD_HEIGHT,
    GRID_SIZE,
    WHITE,
    BLACK,
    GRAY,
)


class GameUI:
    """คลาสสำหรับส่วนติดต่อผู้ใช้ในเกม"""

    def __init__(self, screen, config):
        """
        สร้างส่วนติดต่อผู้ใช้ใหม่

        Args:
            screen (pygame.Surface): พื้นผิวหลักสำหรับการแสดงผล
            config (dict): การตั้งค่าเกม
        """
        self.screen = screen
        self.config = config

        # นำเข้าฟอนต์
        pygame.font.init()
        try:
            self.large_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 36
            )
            self.medium_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 24
            )
            self.small_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 18
            )
        except:
            # ใช้ฟอนต์ระบบถ้าโหลดไม่ได้
            self.large_font = pygame.font.SysFont("Arial", 36)
            self.medium_font = pygame.font.SysFont("Arial", 24)
            self.small_font = pygame.font.SysFont("Arial", 18)

        # ตำแหน่งพื้นที่แสดงผล
        board_right = BOARD_X + BOARD_WIDTH * GRID_SIZE
        self.hold_area = {"x": BOARD_X - 150, "y": BOARD_Y, "width": 120, "height": 120}
        self.next_area = {
            "x": board_right + 30,
            "y": BOARD_Y,
            "width": 120,
            "height": 300,
        }
        self.score_area = {
            "x": BOARD_X - 150,
            "y": BOARD_Y + 150,
            "width": 120,
            "height": 300,
        }

        # สร้างพื้นผิวสำหรับ HUD
        self.hud_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )

        # ตัวจับเวลาแอนิเมชัน
        self.animation_timer = 0

    def render(self, data):
        """
        วาดส่วนติดต่อผู้ใช้

        Args:
            data (dict): ข้อมูลเกม (คะแนน, ระดับ, ฯลฯ)
        """
        # ล้างพื้นผิว HUD
        self.hud_surface.fill((0, 0, 0, 0))

        # วาดพื้นที่ Hold
        self._render_hold_area(data["hold_tetromino"], data["can_hold"])

        # วาดพื้นที่ Next
        self._render_next_area(data["next_tetrominos"])

        # วาดพื้นที่คะแนน
        self._render_score_area(data["score"], data["level"], data["lines"])

        # แสดง FPS ถ้าเปิดใช้งาน
        if self.config["ui"]["show_fps"]:
            fps = int(1.0 / max(0.001, pygame.time.Clock().get_time() / 1000))
            fps_text = self.small_font.render(f"FPS: {fps}", True, WHITE)
            self.hud_surface.blit(fps_text, (10, 10))

        # แสดงชื่อผู้เล่นและเวลา
        self._render_player_info(data["username"], data["time"])

        # วาด HUD บนหน้าจอหลัก
        self.screen.blit(self.hud_surface, (0, 0))

    def _render_hold_area(self, hold_tetromino, can_hold):
        """
        วาดพื้นที่เก็บบล็อก (Hold)

        Args:
            hold_tetromino (Tetromino): บล็อกที่เก็บไว้
            can_hold (bool): สามารถเก็บได้หรือไม่
        """
        area = self.hold_area

        # วาดกรอบ
        pygame.draw.rect(
            self.hud_surface,
            (40, 40, 60),
            (area["x"], area["y"], area["width"], area["height"]),
        )
        pygame.draw.rect(
            self.hud_surface,
            GRAY,
            (area["x"], area["y"], area["width"], area["height"]),
            2,
        )

        # วาดหัวข้อ
        hold_text = self.medium_font.render("HOLD", True, WHITE)
        hold_rect = hold_text.get_rect(
            center=(area["x"] + area["width"] // 2, area["y"] - 20)
        )
        self.hud_surface.blit(hold_text, hold_rect)

        # วาดบล็อกที่เก็บไว้
        if hold_tetromino:
            # คำนวณตำแหน่งบล็อก (กึ่งกลางของพื้นที่)
            shape = hold_tetromino.shape[0]  # ใช้การหมุนเริ่มต้น
            width = max(x for x, y in shape) - min(x for x, y in shape) + 1
            height = max(y for x, y in shape) - min(y for x, y in shape) + 1

            cell_size = min(area["width"] / (width + 2), area["height"] / (height + 2))

            # ตำแหน่งเริ่มต้น
            start_x = area["x"] + (area["width"] - width * cell_size) / 2
            start_y = area["y"] + (area["height"] - height * cell_size) / 2

            # วาดแต่ละช่องของบล็อก
            for block_x, block_y in shape:
                rect = pygame.Rect(
                    start_x + block_x * cell_size,
                    start_y + block_y * cell_size,
                    cell_size,
                    cell_size,
                )

                # ถ้าไม่สามารถเก็บได้ ให้แสดงเป็นสีเทา
                color = hold_tetromino.color if can_hold else GRAY

                pygame.draw.rect(self.hud_surface, color, rect)
                pygame.draw.rect(self.hud_surface, WHITE, rect, 1)

    def _render_next_area(self, next_tetrominos):
        """
        วาดพื้นที่บล็อกถัดไป (Next)

        Args:
            next_tetrominos (list): รายการบล็อกถัดไป
        """
        area = self.next_area

        # วาดกรอบ
        pygame.draw.rect(
            self.hud_surface,
            (40, 40, 60),
            (area["x"], area["y"], area["width"], area["height"]),
        )
        pygame.draw.rect(
            self.hud_surface,
            GRAY,
            (area["x"], area["y"], area["width"], area["height"]),
            2,
        )

        # วาดหัวข้อ
        next_text = self.medium_font.render("NEXT", True, WHITE)
        next_rect = next_text.get_rect(
            center=(area["x"] + area["width"] // 2, area["y"] - 20)
        )
        self.hud_surface.blit(next_text, next_rect)

        # วาดบล็อกถัดไป
        preview_count = min(
            len(next_tetrominos), self.config["tetromino"]["preview_count"]
        )

        for i in range(preview_count):
            tetromino = next_tetrominos[i]

            # คำนวณตำแหน่งบล็อก
            shape = tetromino.shape[0]  # ใช้การหมุนเริ่มต้น
            width = max(x for x, y in shape) - min(x for x, y in shape) + 1
            height = max(y for x, y in shape) - min(y for x, y in shape) + 1

            cell_size = min(area["width"] / (width + 2), 50)

            # ตำแหน่งเริ่มต้น
            start_x = area["x"] + (area["width"] - width * cell_size) / 2
            start_y = area["y"] + 20 + i * 60

            # วาดแต่ละช่องของบล็อก
            for block_x, block_y in shape:
                rect = pygame.Rect(
                    start_x + block_x * cell_size,
                    start_y + block_y * cell_size,
                    cell_size,
                    cell_size,
                )

                pygame.draw.rect(self.hud_surface, tetromino.color, rect)
                pygame.draw.rect(self.hud_surface, WHITE, rect, 1)

    def _render_score_area(self, score, level, lines):
        """
        วาดพื้นที่คะแนน

        Args:
            score (int): คะแนนปัจจุบัน
            level (int): ระดับปัจจุบัน
            lines (int): จำนวนแถวที่ล้างได้
        """
        area = self.score_area

        # วาดกรอบ
        pygame.draw.rect(
            self.hud_surface,
            (40, 40, 60),
            (area["x"], area["y"], area["width"], area["height"]),
        )
        pygame.draw.rect(
            self.hud_surface,
            GRAY,
            (area["x"], area["y"], area["width"], area["height"]),
            2,
        )

        # วาดหัวข้อ
        score_text = self.medium_font.render("STATS", True, WHITE)
        score_rect = score_text.get_rect(
            center=(area["x"] + area["width"] // 2, area["y"] - 20)
        )
        self.hud_surface.blit(score_text, score_rect)

        # วาดคะแนน
        y_pos = area["y"] + 20

        score_label = self.small_font.render("คะแนน:", True, WHITE)
        self.hud_surface.blit(score_label, (area["x"] + 10, y_pos))

        score_value = self.medium_font.render(f"{score:,}", True, (255, 255, 0))
        self.hud_surface.blit(score_value, (area["x"] + 10, y_pos + 25))

        # วาดระดับ
        y_pos += 70

        level_label = self.small_font.render("ระดับ:", True, WHITE)
        self.hud_surface.blit(level_label, (area["x"] + 10, y_pos))

        level_value = self.medium_font.render(f"{level}", True, (0, 255, 255))
        self.hud_surface.blit(level_value, (area["x"] + 10, y_pos + 25))

        # วาดจำนวนแถวที่ล้าง
        y_pos += 70

        lines_label = self.small_font.render("แถวที่ล้าง:", True, WHITE)
        self.hud_surface.blit(lines_label, (area["x"] + 10, y_pos))

        lines_value = self.medium_font.render(f"{lines}", True, (0, 255, 0))
        self.hud_surface.blit(lines_value, (area["x"] + 10, y_pos + 25))

        # วาดแถบแสดงความก้าวหน้าระดับ
        y_pos += 70

        progress_label = self.small_font.render("ระดับถัดไป:", True, WHITE)
        self.hud_surface.blit(progress_label, (area["x"] + 10, y_pos))

        # คำนวณความก้าวหน้า
        level_up_lines = self.config["game"]["level_up_lines"]
        progress = (lines % level_up_lines) / level_up_lines

        # วาดแถบความก้าวหน้า
        bar_width = area["width"] - 20
        bar_height = 15
        bar_x = area["x"] + 10
        bar_y = y_pos + 25

        # กรอบ
        pygame.draw.rect(
            self.hud_surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 1
        )

        # ความก้าวหน้า
        progress_width = bar_width * progress
        pygame.draw.rect(
            self.hud_surface, (0, 200, 255), (bar_x, bar_y, progress_width, bar_height)
        )

    def _render_player_info(self, username, game_time):
        """
        วาดข้อมูลผู้เล่นและเวลา

        Args:
            username (str): ชื่อผู้เล่น
            game_time (float): เวลาที่เล่น (วินาที)
        """
        # วาดชื่อผู้เล่น
        player_text = self.small_font.render(f"ผู้เล่น: {username}", True, WHITE)
        self.hud_surface.blit(player_text, (10, SCREEN_HEIGHT - 30))

        # แปลงเวลาเป็นรูปแบบ mm:ss
        minutes = int(game_time) // 60
        seconds = int(game_time) % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        # วาดเวลา
        time_text = self.small_font.render(f"เวลา: {time_str}", True, WHITE)
        time_rect = time_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
        self.hud_surface.blit(time_text, time_rect)
