#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Board Class
--------------------------
คลาสนี้จัดการเกี่ยวกับบอร์ดเกมและการปฏิสัมพันธ์กับเตโตรมิโน
"""

import pygame
import random
from core.constants import (
    BOARD_WIDTH,
    BOARD_HEIGHT,
    GRID_SIZE,
    BOARD_X,
    BOARD_Y,
    TETROMINO_COLORS,
    BLACK,
    DARK_GRAY,
    WHITE,
    GRAY,
    LINE_CLEAR_DELAY,
    SCORE_SINGLE,
    SCORE_DOUBLE,
    SCORE_TRIPLE,
    SCORE_TETRIS,
    SCORE_T_SPIN,
)
from core.tetromino import Tetromino


class Board:
    """คลาสสำหรับบอร์ดเกม Tetris"""

    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT):
        """
        สร้างบอร์ดเกมใหม่

        Args:
            width (int, optional): ความกว้างของบอร์ด
            height (int, optional): ความสูงของบอร์ด
        """
        self.width = width
        self.height = height
        self.x = BOARD_X
        self.y = BOARD_Y

        # สร้างตารางว่าง
        self.reset_grid()

        # สร้าง surface สำหรับวาดบอร์ด
        self.board_surface = pygame.Surface(
            (width * GRID_SIZE, height * GRID_SIZE), pygame.SRCALPHA
        )
        self.border_surface = pygame.Surface(
            ((width + 2) * GRID_SIZE, (height + 2) * GRID_SIZE), pygame.SRCALPHA
        )
        self.grid_surface = pygame.Surface(
            (width * GRID_SIZE, height * GRID_SIZE), pygame.SRCALPHA
        )
        self.glow_surface = pygame.Surface(
            (width * GRID_SIZE, height * GRID_SIZE), pygame.SRCALPHA
        )

        # สำหรับเอฟเฟกต์การล้างแถว
        self.clearing_lines = []
        self.clearing_timer = 0
        self.clearing_effect = 0  # สำหรับเอฟเฟกต์แอนิเมชัน

        # วาดเส้นตารางไว้ล่วงหน้าสำหรับเพิ่มประสิทธิภาพ
        self._draw_grid()

        # สร้างขอบบอร์ด
        self._draw_border()

    def reset_grid(self):
        """รีเซ็ตตารางเกมให้ว่าง"""
        # สร้างตารางแบบ 2 มิติ (height x width) เริ่มต้นเป็น None ทั้งหมด
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]

    def _draw_grid(self):
        """วาดเส้นตารางบนพื้นผิว grid_surface"""
        self.grid_surface.fill((0, 0, 0, 0))  # โปร่งใส

        # วาดเส้นแนวนอน
        for y in range(self.height + 1):
            pygame.draw.line(
                self.grid_surface,
                GRAY,
                (0, y * GRID_SIZE),
                (self.width * GRID_SIZE, y * GRID_SIZE),
                1,
            )

        # วาดเส้นแนวตั้ง
        for x in range(self.width + 1):
            pygame.draw.line(
                self.grid_surface,
                GRAY,
                (x * GRID_SIZE, 0),
                (x * GRID_SIZE, self.height * GRID_SIZE),
                1,
            )

    def _draw_border(self):
        """วาดขอบบอร์ดบนพื้นผิว border_surface"""
        self.border_surface.fill(DARK_GRAY)

        # วาดขอบด้านใน (พื้นที่เกม)
        inner_rect = pygame.Rect(
            GRID_SIZE, GRID_SIZE, self.width * GRID_SIZE, self.height * GRID_SIZE
        )
        pygame.draw.rect(self.border_surface, BLACK, inner_rect)

        # วาดเส้นขอบสีขาว
        pygame.draw.rect(self.border_surface, WHITE, inner_rect, 2)

    def update(self, dt):
        """
        อัปเดตสถานะของบอร์ด

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)

        Returns:
            dict: ข้อมูลการอัปเดต เช่น คะแนน, แถวที่ล้าง, ฯลฯ
        """
        result = {
            "lines_cleared": 0,
            "score": 0,
            "tetris": False,
            "t_spin": False,
            "level_up": False,
            "clearing_complete": False,
        }

        # ถ้ากำลังล้างแถว
        if self.clearing_lines:
            self.clearing_timer += dt * 1000  # แปลงเป็นมิลลิวินาที
            self.clearing_effect = min(1.0, self.clearing_timer / LINE_CLEAR_DELAY)

            # เมื่อหมดเวลาการแสดงเอฟเฟกต์ ให้ล้างแถวจริงๆ
            if self.clearing_timer >= LINE_CLEAR_DELAY:
                lines_count = len(self.clearing_lines)

                # คำนวณคะแนน
                if lines_count == 1:
                    result["score"] = SCORE_SINGLE
                elif lines_count == 2:
                    result["score"] = SCORE_DOUBLE
                elif lines_count == 3:
                    result["score"] = SCORE_TRIPLE
                elif lines_count == 4:
                    result["score"] = SCORE_TETRIS
                    result["tetris"] = True

                # ลบแถวที่ทำเครื่องหมายไว้
                for line in sorted(self.clearing_lines):
                    # ลบแถวที่ทำเครื่องหมาย
                    self.grid.pop(line)
                    # เพิ่มแถวว่างด้านบน
                    self.grid.insert(0, [None for _ in range(self.width)])

                # อัปเดตค่าที่ส่งคืน
                result["lines_cleared"] = lines_count
                result["clearing_complete"] = True

                # รีเซ็ตสถานะการล้างแถว
                self.clearing_lines = []
                self.clearing_timer = 0
                self.clearing_effect = 0

        return result

    def check_collision(self, tetromino, x, y):
        """
        ตรวจสอบการชนระหว่างบล็อกเตโตรมิโนและบอร์ดหรือขอบบอร์ด

        Args:
            tetromino (Tetromino): บล็อกเตโตรมิโนที่ตรวจสอบ
            x (int): ตำแหน่ง x ที่จะตรวจสอบ
            y (int): ตำแหน่ง y ที่จะตรวจสอบ

        Returns:
            bool: True ถ้ามีการชน, False ถ้าไม่มีการชน
        """
        # ตรวจสอบแต่ละช่องของบล็อกเตโตรมิโน
        for block_x, block_y in tetromino.shape[tetromino.rotation]:
            grid_x = x + block_x
            grid_y = y + block_y

            # ตรวจสอบขอบบอร์ด
            if grid_x < 0 or grid_x >= self.width or grid_y >= self.height:
                return True

            # ตรวจสอบการชนกับบล็อกอื่น (ถ้าไม่ใช่ด้านบนบอร์ด)
            if grid_y >= 0 and self.grid[grid_y][grid_x] is not None:
                return True

        return False

    def lock_tetromino(self, tetromino):
        """
        ล็อคบล็อกเตโตรมิโนลงบนบอร์ด

        Args:
            tetromino (Tetromino): บล็อกเตโตรมิโนที่จะล็อค

        Returns:
            bool: True ถ้าล็อคสำเร็จ, False ถ้าล็อคแล้วเกมจบ (บล็อกอยู่เหนือบอร์ด)
        """
        # วางบล็อกลงบนตาราง
        for block_x, block_y in tetromino.shape[tetromino.rotation]:
            grid_x = tetromino.x + block_x
            grid_y = tetromino.y + block_y

            # ตรวจสอบว่าอยู่บนบอร์ดหรือไม่
            if grid_y < 0:
                return False  # เกมจบ (บล็อกอยู่เหนือบอร์ด)

            # เก็บสีของบล็อกลงในตาราง
            self.grid[grid_y][grid_x] = tetromino.color

        # ตรวจสอบแถวที่เต็ม
        self.check_lines()

        return True

    def check_lines(self):
        """
        ตรวจสอบแถวที่เต็มและทำเครื่องหมายเพื่อล้าง

        Returns:
            list: รายการของแถวที่จะถูกล้าง
        """
        self.clearing_lines = []

        # ตรวจสอบแต่ละแถวจากล่างขึ้นบน
        for y in range(self.height - 1, -1, -1):
            if all(self.grid[y][x] is not None for x in range(self.width)):
                self.clearing_lines.append(y)

        return self.clearing_lines

    def is_game_over(self):
        """
        ตรวจสอบว่าเกมจบหรือไม่ (มีบล็อกในแถวบนสุด)

        Returns:
            bool: True ถ้าเกมจบ, False ถ้าเกมยังดำเนินอยู่
        """
        # ตรวจสอบแถวบนสุด (2 แถวแรก - บางครั้งบล็อกอาจจะสูงกว่าขอบบน)
        for y in range(2):
            for x in range(self.width):
                if self.grid[y][x] is not None:
                    return True
        return False

    def render(self, surface):
        """
        วาดบอร์ดทั้งหมดลงบนพื้นผิวที่กำหนด

        Args:
            surface (pygame.Surface): พื้นผิวที่จะวาด
        """
        # วาดขอบบอร์ด
        surface.blit(self.border_surface, (self.x - GRID_SIZE, self.y - GRID_SIZE))

        # รีเซ็ตพื้นผิวบอร์ด
        self.board_surface.fill(BLACK)
        self.glow_surface.fill((0, 0, 0, 0))  # โปร่งใส

        # วาดเส้นตาราง (ถ้าเปิดใช้งาน)
        self.board_surface.blit(self.grid_surface, (0, 0))

        # วาดบล็อกที่ล็อคแล้ว
        for y in range(self.height):
            for x in range(self.width):
                color = self.grid[y][x]
                if color:
                    # วาดบล็อก
                    rect = pygame.Rect(
                        x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE
                    )
                    pygame.draw.rect(self.board_surface, color, rect)
                    pygame.draw.rect(self.board_surface, WHITE, rect, 1)

                    # วาดเอฟเฟกต์เรืองแสง
                    glow_color = (*color, 64)  # เพิ่มค่า alpha
                    center = (
                        x * GRID_SIZE + GRID_SIZE // 2,
                        y * GRID_SIZE + GRID_SIZE // 2,
                    )
                    pygame.draw.circle(
                        self.glow_surface, glow_color, center, GRID_SIZE - 5
                    )

        # วาดเอฟเฟกต์การล้างแถว
        if self.clearing_lines and self.clearing_effect > 0:
            for line in self.clearing_lines:
                # คำนวณเอฟเฟกต์แอนิเมชัน
                effect_width = int(self.width * GRID_SIZE * self.clearing_effect)
                effect_x = (self.width * GRID_SIZE - effect_width) // 2

                # สร้างพื้นผิวสำหรับเอฟเฟกต์
                line_effect = pygame.Surface((effect_width, GRID_SIZE), pygame.SRCALPHA)
                line_effect.fill((255, 255, 255, 200))  # สีขาวโปร่งแสง

                # วาดเอฟเฟกต์เรืองแสง
                glow_effect = pygame.Surface(
                    (self.width * GRID_SIZE, GRID_SIZE), pygame.SRCALPHA
                )
                for i in range(5):
                    # สร้างเส้นเรืองแสงหลาย ๆ เส้นด้วยความโปร่งใสต่างกัน
                    intensity = 150 - (i * 30)
                    if intensity < 0:
                        break
                    glow_y = line * GRID_SIZE + (i - 2) * 2
                    if 0 <= glow_y < self.height * GRID_SIZE:
                        pygame.draw.line(
                            self.glow_surface,
                            (255, 255, 255, intensity),
                            (0, glow_y),
                            (self.width * GRID_SIZE, glow_y),
                            3 - i if i < 3 else 1,
                        )

        # วาดบอร์ดและเอฟเฟกต์เรืองแสงบนพื้นผิวหลัก
        surface.blit(self.board_surface, (self.x, self.y))
        surface.blit(
            self.glow_surface, (self.x, self.y), special_flags=pygame.BLEND_ADD
        )

    def render_ghost(self, surface, tetromino, ghost_y):
        """
        วาดเงาของบล็อกเตโตรมิโนบนบอร์ด

        Args:
            surface (pygame.Surface): พื้นผิวที่จะวาด
            tetromino (Tetromino): บล็อกเตโตรมิโนที่จะแสดงเงา
            ghost_y (int): ตำแหน่ง y ของเงา
        """
        # คำนวณตำแหน่ง x, y บนหน้าจอ
        screen_x = self.x + tetromino.x * GRID_SIZE
        screen_y = self.y + ghost_y * GRID_SIZE

        # วาดเงาบล็อก
        tetromino.render_ghost(surface, screen_x, screen_y)

    def render_tetromino(self, surface, tetromino):
        """
        วาดบล็อกเตโตรมิโนปัจจุบันบนบอร์ด

        Args:
            surface (pygame.Surface): พื้นผิวที่จะวาด
            tetromino (Tetromino): บล็อกเตโตรมิโนที่จะวาด
        """
        # คำนวณตำแหน่ง x, y บนหน้าจอ
        screen_x = self.x + tetromino.x * GRID_SIZE
        screen_y = self.y + tetromino.y * GRID_SIZE

        # วาดบล็อกและเอฟเฟกต์เรืองแสง
        tetromino.render(surface, screen_x, screen_y)
        tetromino.render_glow(surface, screen_x, screen_y)
