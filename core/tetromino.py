#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Tetromino Class
------------------------------
คลาสนี้จัดการเกี่ยวกับบล็อกเตโตรมิโนแต่ละชิ้น
"""

import random
import pygame
from core.constants import (
    TETROMINO_SHAPES,
    TETROMINO_COLORS,
    TETROMINO_GLOW_COLORS,
    GRID_SIZE,
)


class Tetromino:
    """คลาสสำหรับบล็อกเตโตรมิโน"""

    def __init__(self, shape_name=None, x=0, y=0):
        """
        สร้างบล็อกเตโตรมิโนใหม่

        Args:
            shape_name (str, optional): ชื่อรูปร่าง (I, J, L, O, S, T, Z) หากไม่ระบุจะสุ่ม
            x (int, optional): ตำแหน่ง x เริ่มต้น
            y (int, optional): ตำแหน่ง y เริ่มต้น
        """
        # หากไม่มีการระบุรูปร่าง ให้สุ่มหนึ่งรูปร่าง
        if shape_name is None:
            shape_name = random.choice(list(TETROMINO_SHAPES.keys()))

        self.shape_name = shape_name
        self.shape = TETROMINO_SHAPES[shape_name]
        self.color = TETROMINO_COLORS[shape_name]
        self.glow_color = TETROMINO_GLOW_COLORS[shape_name]
        self.rotation = 0
        self.x = x
        self.y = y

        # สำหรับเช็ค T-spin
        self.last_rotation = False
        self.t_spin = False

        # สร้าง surface สำหรับวาดบล็อกล่วงหน้า
        self._create_surfaces()

    def _create_surfaces(self):
        """สร้าง surface สำหรับวาดบล็อกล่วงหน้า เพื่อเพิ่มประสิทธิภาพ"""
        # กำหนดขนาดสูงสุดของบล็อก (4x4)
        max_size = 4 * GRID_SIZE

        # สร้าง surface หลัก
        self.surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)

        # สร้าง surface สำหรับเอฟเฟกต์เรืองแสง (สำหรับเอฟเฟกต์ bloom)
        self.glow_surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)

        # สร้าง surface สำหรับเงา (ghost piece)
        self.ghost_surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)

        # วาดบล็อกลงบน surface
        self._update_surfaces()

    def _update_surfaces(self):
        """อัปเดต surface ตามสถานะปัจจุบันของบล็อก"""
        # เคลียร์ surface
        self.surface.fill((0, 0, 0, 0))
        self.glow_surface.fill((0, 0, 0, 0))
        self.ghost_surface.fill((0, 0, 0, 0))

        # วาดบล็อกแต่ละช่อง
        current_shape = self.shape[self.rotation]
        for x, y in current_shape:
            # บล็อกหลัก
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self.surface, self.color, rect)
            pygame.draw.rect(self.surface, (255, 255, 255), rect, 1)  # เส้นขอบสีขาว

            # เอฟเฟกต์เรืองแสง
            glow_rect = rect
            # วาดวงกลมเรืองแสงที่จุดกึ่งกลางของบล็อก
            center = (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2)
            pygame.draw.circle(
                self.glow_surface, (*self.glow_color, 128), center, GRID_SIZE - 5
            )

            # บล็อกเงา (ghost piece)
            ghost_rect = rect.copy()
            ghost_color = TETROMINO_COLORS["ghost"]
            pygame.draw.rect(self.ghost_surface, ghost_color, ghost_rect)
            pygame.draw.rect(
                self.ghost_surface, (100, 100, 100), ghost_rect, 1
            )  # เส้นขอบสีเทา

    def get_positions(self):
        """
        รับตำแหน่งปัจจุบันของบล็อกทั้งหมดบนบอร์ด

        Returns:
            list: รายการตำแหน่ง (x, y) ของแต่ละช่องของบล็อก
        """
        positions = []
        for block_x, block_y in self.shape[self.rotation]:
            positions.append((self.x + block_x, self.y + block_y))
        return positions

    def rotate(self, direction=1, board=None):
        """
        หมุนบล็อก

        Args:
            direction (int): 1 สำหรับหมุนตามเข็มนาฬิกา, -1 สำหรับหมุนทวนเข็มนาฬิกา
            board (Board, optional): บอร์ดเกมสำหรับเช็คการชน

        Returns:
            bool: True ถ้าหมุนสำเร็จ, False ถ้าไม่สามารถหมุนได้
        """
        # เก็บการหมุนปัจจุบัน
        old_rotation = self.rotation

        # คำนวณการหมุนใหม่ (0-3)
        new_rotation = (self.rotation + direction) % 4
        self.rotation = new_rotation

        # ถ้ามีการระบุบอร์ด ให้ตรวจสอบการชน
        if board is not None:
            # ใช้ระบบ Super Rotation System (SRS) เพื่อพยายามหมุนโดยไม่ชน
            kicks = self._get_wall_kicks(old_rotation, new_rotation)

            for kick_x, kick_y in kicks:
                test_x = self.x + kick_x
                test_y = self.y + kick_y

                if not board.check_collision(self, test_x, test_y):
                    # หมุนสำเร็จ
                    self.x = test_x
                    self.y = test_y
                    self.last_rotation = True

                    # ตรวจสอบ T-spin (เฉพาะบล็อก T)
                    if self.shape_name == "T":
                        self.check_tspin(board)

                    # อัปเดต surface
                    self._update_surfaces()
                    return True

            # ถ้าไม่สามารถหมุนได้ ให้กลับไปใช้การหมุนเดิม
            self.rotation = old_rotation
            return False

        # อัปเดต surface
        self._update_surfaces()
        return True

    def _get_wall_kicks(self, old_rot, new_rot):
        """
        รับการเปลี่ยนตำแหน่งสำหรับระบบ Super Rotation System (SRS)

        Args:
            old_rot (int): การหมุนเดิม (0-3)
            new_rot (int): การหมุนใหม่ (0-3)

        Returns:
            list: รายการของการเปลี่ยนตำแหน่ง (dx, dy) ที่จะลอง
        """
        # ตารางการเปลี่ยนตำแหน่งสำหรับ Super Rotation System
        # สำหรับบล็อก I
        if self.shape_name == "I":
            kicks = {
                (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
                (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
                (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
                (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
                (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
                (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
                (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
                (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
            }
        # สำหรับบล็อกอื่น ๆ (J, L, S, T, Z)
        else:
            kicks = {
                (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
                (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
                (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
                (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
                (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
                (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
                (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
                (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
            }

        # บล็อก O ไม่มีการเปลี่ยนตำแหน่ง
        if self.shape_name == "O":
            return [(0, 0)]

        # รับการเปลี่ยนตำแหน่งที่เหมาะสม
        key = (old_rot, new_rot)
        return kicks.get(key, [(0, 0)])

    def move(self, dx, dy, board=None):
        """
        เคลื่อนที่บล็อก

        Args:
            dx (int): การเปลี่ยนแปลงในแกน x
            dy (int): การเปลี่ยนแปลงในแกน y
            board (Board, optional): บอร์ดเกมสำหรับเช็คการชน

        Returns:
            bool: True ถ้าเคลื่อนที่สำเร็จ, False ถ้าไม่สามารถเคลื่อนที่ได้
        """
        # คำนวณตำแหน่งใหม่
        new_x = self.x + dx
        new_y = self.y + dy

        # ตรวจสอบการชนถ้ามีการระบุบอร์ด
        if board is not None:
            if board.check_collision(self, new_x, new_y):
                return False

        # อัปเดตตำแหน่ง
        self.x = new_x
        self.y = new_y

        # รีเซ็ตสถานะการหมุนล่าสุด (สำหรับตรวจสอบ T-spin)
        self.last_rotation = False

        return True

    def hard_drop(self, board):
        """
        ปล่อยบล็อกลงด้านล่างทันที

        Args:
            board (Board): บอร์ดเกมสำหรับเช็คการชน

        Returns:
            int: จำนวนแถวที่ตก (สำหรับคำนวณคะแนน)
        """
        drop_distance = 0

        # เคลื่อนที่ลงจนกว่าจะชน
        while not board.check_collision(self, self.x, self.y + 1):
            self.y += 1
            drop_distance += 1

        return drop_distance

    def get_ghost_position(self, board):
        """
        คำนวณตำแหน่งของ ghost piece (เงาด้านล่าง)

        Args:
            board (Board): บอร์ดเกมสำหรับเช็คการชน

        Returns:
            int: ตำแหน่ง y ที่บล็อกจะตกลงไป
        """
        ghost_y = self.y

        # เคลื่อนที่ลงจนกว่าจะชน
        while not board.check_collision(self, self.x, ghost_y + 1):
            ghost_y += 1

        return ghost_y

    def check_tspin(self, board):
        """
        ตรวจสอบว่าเป็น T-spin หรือไม่ (บล็อก T ที่ถูกหมุนและมีช่องรอบๆ 3 ช่องขึ้นไปที่ถูกบล็อก)

        Args:
            board (Board): บอร์ดเกม

        Returns:
            bool: True ถ้าเป็น T-spin
        """
        # ตรวจสอบเฉพาะบล็อก T ที่เพิ่งหมุน
        if self.shape_name != "T" or not self.last_rotation:
            self.t_spin = False
            return False

        # ตรวจสอบมุมทั้ง 4 มุมรอบๆ บล็อก T
        corners = [
            (self.x, self.y),  # บนซ้าย
            (self.x + 2, self.y),  # บนขวา
            (self.x, self.y + 2),  # ล่างซ้าย
            (self.x + 2, self.y + 2),  # ล่างขวา
        ]

        # นับจำนวนมุมที่ถูกบล็อก
        blocked_corners = 0
        for corner_x, corner_y in corners:
            if (
                corner_x < 0
                or corner_x >= board.width
                or corner_y < 0
                or corner_y >= board.height
                or board.grid[corner_y][corner_x] is not None
            ):
                blocked_corners += 1

        # T-spin ต้องมีอย่างน้อย 3 มุมที่ถูกบล็อก
        self.t_spin = blocked_corners >= 3
        return self.t_spin

    def render(self, surface, x, y):
        """
        วาดบล็อกบนพื้นผิวที่กำหนด

        Args:
            surface (pygame.Surface): พื้นผิวที่จะวาด
            x (int): ตำแหน่ง x
            y (int): ตำแหน่ง y
        """
        surface.blit(self.surface, (x, y))

    def render_ghost(self, surface, x, y):
        """
        วาดเงาของบล็อกบนพื้นผิวที่กำหนด

        Args:
            surface (pygame.Surface): พื้นผิวที่จะวาด
            x (int): ตำแหน่ง x
            y (int): ตำแหน่ง y
        """
        surface.blit(self.ghost_surface, (x, y))

    def render_glow(self, surface, x, y):
        """
        วาดเอฟเฟกต์เรืองแสงของบล็อกบนพื้นผิวที่กำหนด

        Args:
            surface (pygame.Surface): พื้นผิวที่จะวาด
            x (int): ตำแหน่ง x
            y (int): ตำแหน่ง y
        """
        surface.blit(self.glow_surface, (x, y))
