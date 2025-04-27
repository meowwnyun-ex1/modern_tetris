#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Game Constants
-----------------------------
This file stores various constants used in the game
"""

import os
from pathlib import Path

# Import pygame key constants (fixed circular import issue)
try:
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
except ImportError:
    try:
        import pygame_ce as pygame
        from pygame_ce.locals import (
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
    except ImportError:
        # Define fallback key values if pygame not available
        # These match pygame's key constants
        K_LEFT, K_RIGHT, K_DOWN, K_SPACE = 276, 275, 274, 32
        K_UP, K_x, K_z, K_LCTRL = 273, 120, 122, 306
        K_c, K_LSHIFT, K_p, K_ESCAPE = 99, 304, 112, 27
        K_a, K_d, K_s = 97, 100, 115

# Screen basics - Optimized for 14" notebook in windowed mode
SCREEN_WIDTH = 720
SCREEN_HEIGHT = 680
TITLE = "DENSO Tetris"

# Grid size - slightly smaller for better fit on notebook screens
GRID_SIZE = 28
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# Board position (center of screen)
BOARD_X = (SCREEN_WIDTH - BOARD_WIDTH * GRID_SIZE) // 2
BOARD_Y = (SCREEN_HEIGHT - BOARD_HEIGHT * GRID_SIZE) // 2

# Colors (elegant, minimal palette)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)
BG_COLOR = (18, 18, 24)  # Dark blue-gray background

# DENSO Main Red Color
DENSO_RED = (220, 0, 50)  # DC0032 in RGB
DENSO_DARK_RED = (160, 0, 35)
DENSO_LIGHT_RED = (255, 60, 90)

# UI Colors (elegant minimal palette)
UI_BG = (24, 24, 32)  # Dark blue-gray background
UI_ACCENT = (230, 230, 230)  # Almost white accent
UI_HIGHLIGHT = DENSO_RED  # Highlight color
UI_TEXT = (245, 245, 245)  # Off-white text
UI_SUBTEXT = (180, 180, 190)  # Light gray for secondary text
UI_BORDER = (60, 60, 70)  # Dark border
UI_BUTTON = (45, 45, 60)  # Button background
UI_BUTTON_HOVER = (55, 55, 70)  # Button hover state
UI_DISABLED = (100, 100, 110)  # Disabled elements

# Tetromino colors (elegant palette with distinct colors)
TETROMINO_COLORS = {
    "I": (0, 190, 218),  # Cyan (I piece)
    "J": (0, 80, 200),  # Blue (J piece)
    "L": (235, 138, 5),  # Orange (L piece)
    "O": (235, 210, 0),  # Yellow (O piece)
    "S": (0, 190, 80),  # Green (S piece)
    "T": DENSO_RED,  # DENSO Red (T piece)
    "Z": (235, 50, 50),  # Red (Z piece)
    "ghost": (70, 70, 85),  # Ghost piece - visible but subtle
}

# Tetromino glow colors (for subtle glow effects)
TETROMINO_GLOW_COLORS = {
    "I": (100, 210, 235),  # Cyan glow
    "J": (100, 130, 235),  # Blue glow
    "L": (245, 170, 100),  # Orange glow
    "O": (245, 220, 100),  # Yellow glow
    "S": (100, 210, 130),  # Green glow
    "T": (235, 100, 130),  # DENSO Red glow
    "Z": (245, 100, 100),  # Red glow
}

# Tetromino shapes
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

# Frames per level (falling speed)
GRAVITY_LEVELS = {
    1: 60,  # 1 cell per 60 frames
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
    20: 1,  # 1 cell per frame (fastest)
}

# Scoring points
SCORE_SINGLE = 100  # 1 line
SCORE_DOUBLE = 300  # 2 lines
SCORE_TRIPLE = 500  # 3 lines
SCORE_TETRIS = 800  # 4 lines
SCORE_SOFT_DROP = 1  # Soft drop (points per block)
SCORE_HARD_DROP = 2  # Hard drop (points per block)
SCORE_T_SPIN = 400  # T-Spin bonus

# Scoring multipliers
BACK_TO_BACK_MULTIPLIER = 1.5  # Multiplier for back-to-back line clears
COMBO_MULTIPLIER = 1.2  # Additional multiplier for combos
COMBO_BONUS = 50  # Bonus points per combo chain

# Keyboard control (DAS = Delayed Auto Shift)
DAS_DELAY = 170  # milliseconds - time before repeat starts
ARR_DELAY = 50  # milliseconds - time between repeats

# Directions
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
DIR_DOWN = (0, 1)

# Controls (default - will be loaded from config)
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

# Assets paths with improved path handling
ASSETS_DIR = (
    Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "assets"
)
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"
FONTS_DIR = ASSETS_DIR / "fonts"
SHADERS_DIR = ASSETS_DIR / "shaders"

# Create directories if not exist
for directory in [ASSETS_DIR, IMAGES_DIR, SOUNDS_DIR, FONTS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# Sound files
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
    "button_hover": "button_hover.wav",
    "button_click": "button_click.wav",
}

# Music files
MUSIC_FILES = {
    "menu": "menu_theme.mp3",
    "game": "game_theme.mp3",
    "high_level": "high_level.mp3",
    "game_over": "game_over.mp3",
}

# UI dimensions
BUTTON_WIDTH = 220
BUTTON_HEIGHT = 50
BUTTON_PADDING = 15
BUTTON_CORNER_RADIUS = 5
MENU_SPACING = 70  # Space between menu items
TOOLTIP_DELAY = 500  # milliseconds before showing tooltip

# Font sizes optimized for 14" notebook
FONT_SIZE_TITLE = 56
FONT_SIZE_LARGE = 28
FONT_SIZE_MEDIUM = 22
FONT_SIZE_SMALL = 16
FONT_SIZE_TINY = 12

# Line clear effect time (milliseconds)
LINE_CLEAR_DELAY = 200

# Leaderboard depth (number of results to show)
LEADERBOARD_DEPTH = 10

# Particle effects - reduced for clean look
PARTICLE_COUNT = {
    "line_clear": 30,  # particles per line cleared
    "tetris": 100,  # particles for a 4-line clear
    "t_spin": 80,  # particles for T-spin
    "level_up": 50,  # particles for level up
    "game_over": 150,  # particles for game over
}

# Game States
STATE_MENU = 0  # in menu
STATE_PLAYING = 1  # playing
STATE_PAUSED = 2  # paused
STATE_GAME_OVER = 3  # game over
STATE_LINE_CLEAR = 4  # clearing lines
STATE_LEADERBOARD = 5  # showing leaderboard
STATE_REGISTER = 6  # registration screen
STATE_PROFILE = 7  # user profile screen
STATE_VICTORY = 8  # victory screen

# Achievement IDs
ACHIEVEMENT_IDS = {
    "first_game": "first_game",
    "reach_level_10": "reach_level_10",
    "reach_level_20": "reach_level_20",
    "score_10k": "score_10k",
    "score_50k": "score_50k",
    "score_100k": "score_100k",
    "clear_100_lines": "clear_100_lines",
    "tetris": "tetris",
    "t_spin": "t_spin",
    "back_to_back": "back_to_back",
}

# Game mode constants
MODE_ENDLESS = 0  # Play until game over
MODE_VICTORY = 1  # Play until reaching level 20

# Victory requirements
VICTORY_LEVEL = 20  # Level needed to win the game
