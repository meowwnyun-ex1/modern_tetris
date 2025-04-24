#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Game Class
-------------------------
คลาสหลักสำหรับการจัดการเกม Tetris
"""

import pygame
import random
import time
import logging
import math  # เพิ่มบรรทัดนี้
from pygame.locals import *  # เพิ่มบรรทัดนี้

from core.constants import (
    BOARD_WIDTH,
    BOARD_HEIGHT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GRAVITY_LEVELS,
    STATE_PLAYING,
    STATE_PAUSED,
    STATE_GAME_OVER,
    STATE_LINE_CLEAR,
    SCORE_SOFT_DROP,
    SCORE_HARD_DROP,
    SCORE_T_SPIN,
    DAS_DELAY,
    ARR_DELAY,
    PARTICLE_COUNT,
    GRID_SIZE,  # เพิ่ม GRID_SIZE ตรงนี้
)
from core.board import Board
from core.tetromino import Tetromino
from graphics.effects import ParticleSystem
from graphics.renderer import Renderer
from audio.sound_manager import SoundManager
from ui.game_ui import GameUI
from db.queries import save_game_score
from utils.logger import get_logger


class Game:
    """คลาสหลักสำหรับเกม Tetris"""

    def __init__(self, screen, config, username=None):
        """
        สร้างเกมใหม่

        Args:
            screen (pygame.Surface): พื้นผิวหลักสำหรับการแสดงผล
            config (dict): การตั้งค่าเกม
            username (str, optional): ชื่อผู้เล่น
        """
        self.screen = screen
        self.config = config
        self.username = username if username else "Guest"
        self.logger = get_logger()

        # สร้างบอร์ดเกม
        self.board = Board()

        # สร้างระบบแสดงผล
        self.renderer = Renderer(screen, config)

        # สร้างส่วนติดต่อผู้ใช้
        self.ui = GameUI(screen, config)

        # สร้างระบบเสียง
        self.sound_manager = SoundManager(config)

        # สร้างระบบอนุภาค
        self.particle_system = ParticleSystem()

        # ตั้งค่าการควบคุม
        self.setup_controls()

        # เริ่มต้นเกมใหม่
        self.reset_game()

    def setup_controls(self):
        """ตั้งค่าการควบคุมจากไฟล์ config"""
        controls = self.config["controls"]["keyboard"]

        # แปลงชื่อคีย์เป็นค่า pygame
        self.keys = {}
        for action, key_names in controls.items():
            self.keys[action] = []
            for key_name in key_names:
                # แปลงสตริงเป็นค่า pygame.K_*
                if isinstance(key_name, str) and key_name.startswith("K_"):
                    key_value = getattr(pygame, key_name)
                    self.keys[action].append(key_value)
                else:
                    self.keys[action].append(key_name)

    def reset_game(self):
        """รีเซ็ตเกมใหม่"""
        # ตั้งค่าสถานะเกม
        self.state = STATE_PLAYING
        self.level = self.config["game"]["start_level"]
        self.score = 0
        self.lines_cleared = 0
        self.combo = 0
        self.back_to_back = 0

        # เริ่มต้นเวลา
        self.start_time = time.time()
        self.pause_time = 0

        # รีเซ็ตบอร์ด
        self.board.reset_grid()

        # สร้างถุงเตโตรมิโน
        self.tetromino_bag = []
        self.refill_bag()

        # สร้างเตโตรมิโนปัจจุบันและถัดไป
        self.current_tetromino = self.get_next_tetromino()
        self.next_tetrominos = [
            self.get_next_tetromino()
            for _ in range(self.config["tetromino"]["preview_count"])
        ]
        self.hold_tetromino = None
        self.can_hold = True

        # ตั้งค่าตัวจับเวลา
        self.drop_timer = 0
        self.lock_delay = 0.5  # 500 มิลลิวินาที
        self.lock_timer = 0
        self.das_timer = 0
        self.arr_timer = 0
        self.move_direction = 0

        # บันทึกสถานะปุ่ม
        self.key_states = {
            "MOVE_LEFT": False,
            "MOVE_RIGHT": False,
            "SOFT_DROP": False,
            "HARD_DROP": False,
            "ROTATE_CW": False,
            "ROTATE_CCW": False,
            "HOLD": False,
            "PAUSE": False,
        }

        # ฟลาก
        self.lock_pending = False
        self.game_over = False

        # เริ่มเพลงเกม
        self.sound_manager.play_music("game")

        self.logger.info(f"เริ่มเกมใหม่: ผู้เล่น {self.username}, ระดับ {self.level}")

    def refill_bag(self):
        """เติมถุงเตโตรมิโนแบบสุ่ม (ใช้ระบบถุง 7 ชิ้น)"""
        if len(self.tetromino_bag) <= 7:
            # สร้างชุดใหม่ของทุกชิ้นและสับ
            new_bag = list("IJLOSTZ")
            random.shuffle(new_bag)
            self.tetromino_bag.extend(new_bag)

    def get_next_tetromino(self):
        """
        รับเตโตรมิโนถัดไปจากถุง

        Returns:
            Tetromino: เตโตรมิโนถัดไป
        """
        # เติมถุงถ้าจำเป็น
        self.refill_bag()

        # รับและลบชิ้นแรกจากถุง
        shape_name = self.tetromino_bag.pop(0)

        # สร้างเตโตรมิโนใหม่ที่กึ่งกลางด้านบนของบอร์ด
        return Tetromino(shape_name, x=(BOARD_WIDTH // 2) - 1, y=0)

    def handle_event(self, event):
        """
        จัดการกับเหตุการณ์อินพุต

        Args:
            event (pygame.event.Event): เหตุการณ์ที่จะจัดการ

        Returns:
            bool: True ถ้าจัดการเหตุการณ์, False ถ้าไม่ได้จัดการ
        """
        if self.state == STATE_GAME_OVER:
            # จัดการการกดปุ่มในสถานะเกมจบ
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    # กลับไปที่เมนูหลัก
                    return True
            return False

        if self.state == STATE_PAUSED:
            # จัดการการกดปุ่มในสถานะหยุดชั่วคราว
            if event.type == KEYDOWN:
                if event.key == K_p or event.key == K_ESCAPE:
                    # กลับไปเล่นต่อ
                    self.state = STATE_PLAYING
                    self.sound_manager.play_sound("menu_select")
                    return True
            return False

        if event.type == KEYDOWN:
            # ตรวจสอบการกดปุ่ม
            for action, keys in self.keys.items():
                if event.key in keys:
                    self.key_states[action] = True

                    # จัดการกับการกดปุ่มทันที
                    if action == "PAUSE":
                        if self.state == STATE_PLAYING:
                            self.state = STATE_PAUSED
                            self.sound_manager.play_sound("menu_select")
                    elif action == "HARD_DROP" and self.state == STATE_PLAYING:
                        self.hard_drop()
                    elif action == "ROTATE_CW" and self.state == STATE_PLAYING:
                        self.rotate_tetromino(1)
                    elif action == "ROTATE_CCW" and self.state == STATE_PLAYING:
                        self.rotate_tetromino(-1)
                    elif action == "HOLD" and self.state == STATE_PLAYING:
                        self.hold_piece()
                    elif action in ["MOVE_LEFT", "MOVE_RIGHT"]:
                        # เริ่มต้น DAS timer
                        self.das_timer = 0

                        # เคลื่อนที่ทันที
                        direction = -1 if action == "MOVE_LEFT" else 1
                        self.move_tetromino(direction, 0)

                    return True

        elif event.type == KEYUP:
            # ตรวจสอบการปล่อยปุ่ม
            for action, keys in self.keys.items():
                if event.key in keys:
                    self.key_states[action] = False

                    # รีเซ็ต DAS/ARR เมื่อปล่อยปุ่มเคลื่อนที่
                    if action in ["MOVE_LEFT", "MOVE_RIGHT"]:
                        self.das_timer = 0
                        self.arr_timer = 0
                        self.move_direction = 0

                    return True

        return False

    def update(self, dt):
        """
        อัปเดตสถานะเกม

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)

        Returns:
            object: ซีนถัดไป (ถ้ามีการเปลี่ยนซีน) หรือ None
        """
        # ไม่อัปเดตหากเกมอยู่ในสถานะหยุดชั่วคราวหรือเกมจบ
        if self.state == STATE_PAUSED:
            return None

        # อัปเดตบอร์ด
        board_update = self.board.update(dt)

        # ถ้ามีการล้างแถวเสร็จสิ้น
        if board_update["clearing_complete"]:
            self.state = STATE_PLAYING
            lines_cleared = board_update["lines_cleared"]

            # อัปเดตสถิติ
            self.lines_cleared += lines_cleared
            self.score += board_update["score"] * self.level

            # ตรวจสอบคอมโบ
            if lines_cleared > 0:
                self.combo += 1
                # โบนัสคอมโบ (50 * combo * level)
                if self.combo > 1:
                    self.score += 50 * self.combo * self.level
            else:
                self.combo = 0

            # ตรวจสอบ back-to-back (คือ tetris หรือ t-spin ติดต่อกัน)
            if board_update["tetris"] or board_update["t_spin"]:
                self.back_to_back += 1
                if self.back_to_back > 1:
                    # โบนัส back-to-back
                    self.score += int(board_update["score"] * 0.5)
            else:
                self.back_to_back = 0

            # ตรวจสอบการเลเวลอัพ
            level_up_lines = self.config["game"]["level_up_lines"]
            if (
                self.lines_cleared >= level_up_lines * self.level
                and self.level < self.config["game"]["max_level"]
            ):
                self.level += 1
                self.sound_manager.play_sound("level_up")

                # สร้างอนุภาคเลเวลอัพ
                if self.config["graphics"]["particles"]:
                    self.create_particles("level_up")

                # เปลี่ยนเพลงที่ระดับสูง
                if (
                    self.level >= 15
                    and self.sound_manager.current_music != "high_level"
                ):
                    self.sound_manager.play_music("high_level")

            # เล่นเสียงตามจำนวนแถว
            if lines_cleared == 4:
                self.sound_manager.play_sound("tetris")
                # สร้างอนุภาค tetris
                if self.config["graphics"]["particles"]:
                    self.create_particles("tetris")
            elif lines_cleared > 0:
                self.sound_manager.play_sound("clear")
                # สร้างอนุภาคล้างแถว
                if self.config["graphics"]["particles"]:
                    self.create_particles("line_clear", lines_cleared)

        # อัปเดตอนุภาค
        if self.config["graphics"]["particles"]:
            self.particle_system.update(dt)

        # อัปเดตเกม
        if self.state == STATE_PLAYING:
            self._update_game(dt)
        elif self.state == STATE_LINE_CLEAR:
            # ในสถานะล้างแถว ไม่ต้องทำอะไรเพิ่มเติม รอให้บอร์ดอัปเดตเสร็จ
            pass
        elif self.state == STATE_GAME_OVER:
            # บันทึกคะแนน
            if not self.game_over:
                self._handle_game_over()

        return None

    def _update_game(self, dt):
        """
        อัปเดตสถานะของเกมในโหมดเล่น

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)
        """
        # จัดการกับการเคลื่อนที่ซ้ายขวา (DAS/ARR)
        self._handle_horizontal_movement(dt)

        # จัดการกับการตกแบบอัตโนมัติและการทำ soft drop
        gravity = self._get_gravity_delay()

        # ถ้ากดปุ่ม soft drop ใช้ความเร็วสูงกว่า
        if self.key_states["SOFT_DROP"]:
            gravity /= 20  # กดลงเร็วกว่าปกติ 20 เท่า

        # เพิ่มตัวจับเวลาการตก
        self.drop_timer += dt

        # ถ้าถึงเวลาตก
        if self.drop_timer >= gravity:
            self.drop_timer = 0

            # ลองเคลื่อนที่ลง
            if self.move_tetromino(0, 1):
                # ถ้ากำลังทำ soft drop ให้เพิ่มคะแนน
                if self.key_states["SOFT_DROP"]:
                    self.score += SCORE_SOFT_DROP
            else:
                # ถ้าเคลื่อนที่ลงไม่ได้ ให้เริ่มตัวจับเวลาล็อค
                self.lock_pending = True

        # จัดการกับการล็อคบล็อก
        if self.lock_pending:
            self.lock_timer += dt

            if self.lock_timer >= self.lock_delay:
                self._lock_tetromino()

    def _handle_horizontal_movement(self, dt):
        """
        จัดการกับการเคลื่อนที่ซ้ายขวาแบบ DAS/ARR

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)
        """
        # ตรวจสอบว่ากำลังกดปุ่มซ้ายหรือขวา
        if self.key_states["MOVE_LEFT"] and not self.key_states["MOVE_RIGHT"]:
            direction = -1
        elif self.key_states["MOVE_RIGHT"] and not self.key_states["MOVE_LEFT"]:
            direction = 1
        else:
            # ไม่มีการกดหรือกดทั้งสองปุ่ม
            self.move_direction = 0
            return

        # เพิ่ม DAS timer
        self.das_timer += dt * 1000  # แปลงเป็นมิลลิวินาที

        # ถ้าผ่าน DAS delay แล้ว
        if self.das_timer >= DAS_DELAY:
            # เพิ่ม ARR timer
            self.arr_timer += dt * 1000

            # เคลื่อนที่ตาม ARR
            if self.arr_timer >= ARR_DELAY:
                self.arr_timer = 0
                self.move_tetromino(direction, 0)

    def _get_gravity_delay(self):
        """
        คำนวณเวลาที่ใช้ในการตกหนึ่งช่อง

        Returns:
            float: เวลาล่าช้าในวินาที
        """
        # รับค่าความเร็วจากตาราง
        level_capped = min(self.level, 20)  # จำกัดที่ระดับ 20
        frames_per_drop = GRAVITY_LEVELS.get(level_capped, 1)

        # แปลงเฟรมเป็นวินาที (ที่ 60 fps)
        return frames_per_drop / 60.0

    def rotate_tetromino(self, direction):
        """
        หมุนบล็อกเตโตรมิโนปัจจุบัน

        Args:
            direction (int): 1 สำหรับหมุนตามเข็มนาฬิกา, -1 สำหรับหมุนทวนเข็มนาฬิกา

        Returns:
            bool: True ถ้าหมุนสำเร็จ, False ถ้าไม่สามารถหมุนได้
        """
        if self.current_tetromino.rotate(direction, self.board):
            # เล่นเสียงหมุน
            self.sound_manager.play_sound("rotate")

            # ถ้ากำลังจะล็อค ให้รีเซ็ตตัวจับเวลาล็อค (ให้โอกาสเคลื่อนย้าย)
            if self.lock_pending:
                self.lock_timer = 0

            return True
        return False

    def move_tetromino(self, dx, dy):
        """
        เคลื่อนที่บล็อกเตโตรมิโนปัจจุบัน

        Args:
            dx (int): การเปลี่ยนแปลงในแกน x
            dy (int): การเปลี่ยนแปลงในแกน y

        Returns:
            bool: True ถ้าเคลื่อนที่สำเร็จ, False ถ้าไม่สามารถเคลื่อนที่ได้
        """
        if self.current_tetromino.move(dx, dy, self.board):
            # เล่นเสียงเคลื่อนที่ (เฉพาะการเคลื่อนที่ซ้ายขวา)
            if dx != 0 and dy == 0:
                self.sound_manager.play_sound("move")

            # ถ้ากำลังจะล็อคและมีการเคลื่อนที่ ให้รีเซ็ตตัวจับเวลาล็อค
            if self.lock_pending and (dx != 0 or dy < 0):
                self.lock_timer = 0

            return True
        return False

    def hard_drop(self):
        """ปล่อยบล็อกลงด้านล่างทันที"""
        if self.state != STATE_PLAYING:
            return

        # คำนวณระยะทางที่จะตก
        drop_distance = self.current_tetromino.hard_drop(self.board)

        # เพิ่มคะแนน
        self.score += drop_distance * SCORE_HARD_DROP

        # เล่นเสียง
        self.sound_manager.play_sound("drop")

        # ล็อคบล็อกทันที
        self._lock_tetromino()

    def hold_piece(self):
        """เก็บบล็อกปัจจุบันและสลับกับบล็อกที่เก็บไว้"""
        # ตรวจสอบว่าเปิดใช้งานการเก็บบล็อกหรือไม่
        if not self.config["tetromino"]["enable_hold"]:
            return

        # ตรวจสอบว่าสามารถเก็บได้หรือไม่
        if not self.can_hold:
            return

        # เล่นเสียง
        self.sound_manager.play_sound("hold")

        # สลับบล็อก
        if self.hold_tetromino is None:
            # เก็บบล็อกปัจจุบันและรับบล็อกใหม่
            self.hold_tetromino = Tetromino(self.current_tetromino.shape_name)
            self.current_tetromino = self.get_next_tetromino()
            self.next_tetrominos.append(self.get_next_tetromino())
            self.next_tetrominos.pop(0)
        else:
            # สลับระหว่างบล็อกปัจจุบันและบล็อกที่เก็บไว้
            temp = self.current_tetromino.shape_name
            self.current_tetromino = Tetromino(
                self.hold_tetromino.shape_name, x=(BOARD_WIDTH // 2) - 1, y=0
            )
            self.hold_tetromino = Tetromino(temp)

        # ไม่สามารถเก็บอีกจนกว่าจะล็อคบล็อกถัดไป
        self.can_hold = False

        # รีเซ็ตสถานะล็อค
        self.lock_pending = False
        self.lock_timer = 0

    def _lock_tetromino(self):
        """ล็อคบล็อกปัจจุบันลงบนบอร์ด"""
        # ตรวจสอบ T-spin
        t_spin = self.current_tetromino.t_spin

        # ล็อคบล็อกลงบนบอร์ด
        if not self.board.lock_tetromino(self.current_tetromino):
            # เกมจบ (บล็อกอยู่เหนือบอร์ด)
            self.state = STATE_GAME_OVER
            return

        # เพิ่มคะแนน T-spin
        if t_spin:
            self.score += SCORE_T_SPIN * self.level
            self.sound_manager.play_sound("t_spin")

            # สร้างอนุภาค T-spin
            if self.config["graphics"]["particles"]:
                self.create_particles("t_spin")

        # ตรวจสอบการล้างแถว
        if self.board.clearing_lines:
            self.state = STATE_LINE_CLEAR

        # เตรียมบล็อกถัดไป
        self.current_tetromino = self.next_tetrominos.pop(0)
        self.next_tetrominos.append(self.get_next_tetromino())

        # รีเซ็ตสถานะ
        self.lock_pending = False
        self.lock_timer = 0
        self.can_hold = True  # อนุญาตให้เก็บบล็อกอีกครั้ง

    def _handle_game_over(self):
        """จัดการกับสถานะเกมจบ"""
        self.game_over = True

        # หยุดเพลงเกม
        self.sound_manager.stop_music()

        # เล่นเสียงเกมจบ
        self.sound_manager.play_sound("game_over")

        # เล่นเพลงเกมจบ
        self.sound_manager.play_music("game_over")

        # สร้างอนุภาคเกมจบ
        if self.config["graphics"]["particles"]:
            self.create_particles("game_over")

        # คำนวณเวลาที่เล่น
        elapsed_time = time.time() - self.start_time - self.pause_time

        # บันทึกคะแนนลงฐานข้อมูล
        try:
            save_game_score(
                username=self.username,
                score=self.score,
                level=self.level,
                lines=self.lines_cleared,
                time_played=elapsed_time,
            )
            self.logger.info(
                f"บันทึกคะแนน: {self.username}, {self.score}, ระดับ {self.level}"
            )
        except Exception as e:
            self.logger.error(f"ไม่สามารถบันทึกคะแนนได้: {e}")

    def create_particles(self, effect_type, multiplier=1):
        """
        สร้างอนุภาคสำหรับเอฟเฟกต์พิเศษ

        Args:
            effect_type (str): ประเภทของเอฟเฟกต์
            multiplier (int): ตัวคูณจำนวนอนุภาค
        """
        # รับจำนวนอนุภาคจากค่าคงที่
        count = PARTICLE_COUNT.get(effect_type, 50) * multiplier

        # กำหนดตำแหน่งและสีตามประเภทเอฟเฟกต์
        if effect_type == "line_clear":
            # สร้างอนุภาคสำหรับแต่ละแถวที่ล้าง
            for line in self.board.clearing_lines:
                y = self.board.y + line * GRID_SIZE + GRID_SIZE // 2
                for i in range(count // len(self.board.clearing_lines)):
                    x = self.board.x + random.randint(0, self.board.width * GRID_SIZE)
                    color = (255, 255, 255)
                    self.particle_system.create_particle(x, y, color)

        elif effect_type == "tetris":
            # อนุภาคจำนวนมากที่กระจายทั่วบอร์ด
            for _ in range(count):
                x = self.board.x + random.randint(0, self.board.width * GRID_SIZE)
                y = self.board.y + random.randint(0, self.board.height * GRID_SIZE)
                color = (random.randint(100, 255), random.randint(100, 255), 255)
                self.particle_system.create_particle(x, y, color)

        elif effect_type == "t_spin":
            # อนุภาคสีม่วงรอบบล็อก T
            center_x = self.board.x + (self.current_tetromino.x + 1) * GRID_SIZE
            center_y = self.board.y + (self.current_tetromino.y + 1) * GRID_SIZE
            for _ in range(count):
                angle = random.uniform(0, 6.28)
                distance = random.uniform(0, GRID_SIZE * 3)
                x = center_x + distance * math.cos(angle)
                y = center_y + distance * math.sin(angle)
                color = (128, 0, 128)  # สีม่วง
                self.particle_system.create_particle(x, y, color)

        elif effect_type == "level_up":
            # อนุภาคทั่วหน้าจอ
            for _ in range(count):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                color = (255, 215, 0)  # สีทอง
                self.particle_system.create_particle(x, y, color, life_span=2.0)

        elif effect_type == "game_over":
            # อนุภาคตกจากด้านบนของบอร์ด
            for _ in range(count):
                x = self.board.x + random.randint(0, self.board.width * GRID_SIZE)
                y = self.board.y - random.randint(0, GRID_SIZE * 5)
                color = (255, 0, 0)  # สีแดง
                self.particle_system.create_particle(
                    x, y, color, life_span=3.0, gravity=200
                )

    def render(self):
        """วาดเกมทั้งหมด"""
        # วาดพื้นหลัง
        self.renderer.render_background()

        # วาดบอร์ด
        self.board.render(self.screen)

        # วาดเตโตรมิโนปัจจุบัน
        if self.state in [STATE_PLAYING, STATE_PAUSED]:
            # วาดเงา (ghost piece)
            if self.config["tetromino"]["ghost_piece"]:
                ghost_y = self.current_tetromino.get_ghost_position(self.board)
                self.board.render_ghost(self.screen, self.current_tetromino, ghost_y)

            # วาดบล็อกปัจจุบัน
            self.board.render_tetromino(self.screen, self.current_tetromino)

        # วาดอนุภาค
        if self.config["graphics"]["particles"]:
            self.particle_system.render(self.screen)

        # วาดส่วนติดต่อผู้ใช้ (แสดงคะแนน, ระดับ, ฯลฯ)
        ui_data = {
            "score": self.score,
            "level": self.level,
            "lines": self.lines_cleared,
            "next_tetrominos": self.next_tetrominos,
            "hold_tetromino": self.hold_tetromino,
            "can_hold": self.can_hold,
            "state": self.state,
            "username": self.username,
            "time": time.time() - self.start_time - self.pause_time,
        }
        self.ui.render(ui_data)

        # เอฟเฟกต์ซ้อนทับ (โดยเฉพาะเมื่อหยุดเกมหรือเกมจบ)
        if self.state == STATE_PAUSED:
            self.renderer.render_pause_overlay()
        elif self.state == STATE_GAME_OVER:
            self.renderer.render_game_over(self.score, self.level, self.lines_cleared)

        # ทำเอฟเฟกต์ Bloom เมื่อเปิดใช้งาน
        if self.config["graphics"]["bloom_effect"]:
            self.renderer.apply_bloom(self.screen)

        # อัปเดตหน้าจอ
        pygame.display.flip()
