#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Game Constants
-----------------------------
ไฟล์นี้เก็บค่าคงที่ต่างๆ ที่ใช้ในเกม
"""

import pygame
from pygame.locals import (
    K_LEFT,
    K_RIGHT,
    K_DOWN,
    K_SPACE,
    K_UP,
    K_x,
    K_z,
    K_LCTRL,
    K_c,
    K_LSHIFT,
    K_p,
    K_ESCAPE,
    K_a,
    K_d,
    K_s,
)
import os

# ค่าพื้นฐานของหน้าจอ
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
TITLE = "Modern Tetris | เกม Tetris สมัยใหม่"

# ขนาดของกริด
GRID_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# ตำแหน่งของบอร์ดเกม (กึ่งกลางหน้าจอ)
BOARD_X = (SCREEN_WIDTH - BOARD_WIDTH * GRID_SIZE) // 2
BOARD_Y = (SCREEN_HEIGHT - BOARD_HEIGHT * GRID_SIZE) // 2

# สีต่างๆ
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)

# สีของเตโตรมิโน (โทนนีออน)
TETROMINO_COLORS = {
    "I": (0, 255, 255),  # สีฟ้า (I piece)
    "J": (0, 0, 255),  # สีน้ำเงิน (J piece)
    "L": (255, 165, 0),  # สีส้ม (L piece)
    "O": (255, 255, 0),  # สีเหลือง (O piece)
    "S": (0, 255, 0),  # สีเขียว (S piece)
    "T": (128, 0, 128),  # สีม่วง (T piece)
    "Z": (255, 0, 0),  # สีแดง (Z piece)
    "ghost": (40, 40, 40),  # สีเทาเข้ม (Ghost piece)
}

# สีเรืองแสงของเตโตรมิโน (สำหรับเอฟเฟกต์แสง)
TETROMINO_GLOW_COLORS = {
    "I": (100, 255, 255),  # สีฟ้าเรืองแสง
    "J": (100, 100, 255),  # สีน้ำเงินเรืองแสง
    "L": (255, 200, 100),  # สีส้มเรืองแสง
    "O": (255, 255, 100),  # สีเหลืองเรืองแสง
    "S": (100, 255, 100),  # สีเขียวเรืองแสง
    "T": (200, 100, 200),  # สีม่วงเรืองแสง
    "Z": (255, 100, 100),  # สีแดงเรืองแสง
}

# รูปร่างของเตโตรมิโน
TETROMINO_SHAPES = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
    ],
    "J": [
        [(0, 0), (0, 1), (0, 2), (1, 2)],
        [(0, 0), (1, 0), (2, 0), (0, 1)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(2, 0), (0, 1), (1, 1), (2, 1)],
    ],
    "L": [
        [(0, 0), (0, 1), (0, 2), (1, 0)],
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (0, 2)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (1, 1), (0, 2)],
        [(0, 0), (1, 0), (2, 0), (1, 1)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
}

# จำนวนเฟรมที่ทำให้บล็อกตกเร็วขึ้นในแต่ละระดับ
GRAVITY_LEVELS = {
    1: 60,  # 1 ช่องต่อ 60 เฟรม
    2: 50,
    3: 40,
    4: 30,
    5: 25,
    6: 20,
    7: 15,
    8: 12,
    9: 10,
    10: 8,
    11: 7,
    12: 6,
    13: 5,
    14: 4,
    15: 3,
    16: 3,
    17: 2,
    18: 2,
    19: 1,
    20: 1,  # 1 ช่องต่อเฟรม (เร็วที่สุด)
}

# คะแนนสำหรับการล้างแถว
SCORE_SINGLE = 100  # 1 แถว
SCORE_DOUBLE = 300  # 2 แถว
SCORE_TRIPLE = 500  # 3 แถว
SCORE_TETRIS = 800  # 4 แถว
SCORE_SOFT_DROP = 1  # Soft drop (คะแนนต่อบล็อก)
SCORE_HARD_DROP = 2  # Hard drop (คะแนนต่อบล็อก)
SCORE_T_SPIN = 400  # T-Spin bonus

# เคอร์เซอร์คีย์บอร์ด (DAS = Delayed Auto Shift)
DAS_DELAY = 170  # มิลลิวินาที - เวลาก่อนที่จะเริ่มเลื่อนซ้ำ
ARR_DELAY = 50  # มิลลิวินาที - เวลาระหว่างแต่ละการเลื่อนซ้ำ

# ทิศทาง
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
DIR_DOWN = (0, 1)

# การควบคุม (ค่าเริ่มต้น - จะถูกโหลดจาก config)
DEFAULT_CONTROLS = {
    "MOVE_LEFT": [K_LEFT, K_a],
    "MOVE_RIGHT": [K_RIGHT, K_d],
    "SOFT_DROP": [K_DOWN, K_s],
    "HARD_DROP": [K_SPACE],
    "ROTATE_CW": [K_UP, K_x],
    "ROTATE_CCW": [K_z, K_LCTRL],
    "HOLD": [K_c, K_LSHIFT],
    "PAUSE": [K_p, K_ESCAPE],
}

# พาธของไฟล์ assets
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SHADERS_DIR = os.path.join(ASSETS_DIR, "shaders")

# ชื่อไฟล์เสียง
SOUND_FILES = {
    "move": "move.wav",
    "rotate": "rotate.wav",
    "drop": "drop.wav",
    "clear": "clear.wav",
    "tetris": "tetris.wav",
    "level_up": "level_up.wav",
    "game_over": "game_over.wav",
    "menu_select": "menu_select.wav",
    "menu_change": "menu_change.wav",
    "t_spin": "t_spin.wav",
    "hold": "hold.wav",
}

# ชื่อไฟล์เพลง
MUSIC_FILES = {
    "menu": "menu_theme.mp3",
    "game": "game_theme.mp3",
    "high_level": "high_level.mp3",
    "game_over": "game_over.mp3",
}

# เวลาในการแสดงเอฟเฟกต์การล้างแถว (มิลลิวินาที)
LINE_CLEAR_DELAY = 200

# ความลึกของรายการระดับ (จำนวนผลลัพธ์ที่แสดงในตาราง)
LEADERBOARD_DEPTH = 10

# เอฟเฟกต์อนุภาค
PARTICLE_COUNT = {
    "line_clear": 50,  # จำนวนอนุภาคต่อแถวที่ล้าง
    "tetris": 200,  # จำนวนอนุภาคเมื่อล้าง 4 แถว
    "t_spin": 150,  # จำนวนอนุภาคเมื่อทำ T-spin
    "level_up": 100,  # จำนวนอนุภาคเมื่อเลเวลอัพ
    "game_over": 300,  # จำนวนอนุภาคเมื่อเกมจบ
}

# Game States
STATE_MENU = 0  # อยู่ในเมนู
STATE_PLAYING = 1  # กำลังเล่น
STATE_PAUSED = 2  # หยุดชั่วคราว
STATE_GAME_OVER = 3  # เกมจบ
STATE_LINE_CLEAR = 4  # กำลังล้างแถว
STATE_LEADERBOARD = 5  # แสดงตารางคะแนน
