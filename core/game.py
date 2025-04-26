#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Game Class
-------------------------
Main class for managing the Tetris game with enhanced features
including victory mode
"""

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame

        print("ใช้ pygame-ce แทน pygame")
    except ImportError:
        print("กรุณาติดตั้ง pygame หรือ pygame-ce")
        import sys

        sys.exit(1)
import random
import time
import logging
import math
import traceback
from pygame.locals import *
import sys  # Fix "sys is not defined"

from core.constants import (
    BACK_TO_BACK_MULTIPLIER,
    BOARD_WIDTH,
    BOARD_HEIGHT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GRAVITY_LEVELS,
    STATE_PLAYING,
    STATE_PAUSED,
    STATE_GAME_OVER,
    STATE_VICTORY,
    STATE_LINE_CLEAR,
    SCORE_SINGLE,
    SCORE_DOUBLE,
    SCORE_TRIPLE,
    SCORE_TETRIS,
    SCORE_SOFT_DROP,
    SCORE_HARD_DROP,
    SCORE_T_SPIN,
    COMBO_BONUS,
    DAS_DELAY,
    ARR_DELAY,
    PARTICLE_COUNT,
    GRID_SIZE,
    DENSO_RED,
    VICTORY_LEVEL,
    ACHIEVEMENT_IDS,
    MODE_ENDLESS,
    MODE_VICTORY,
)

try:
    from core.board import Board
    from core.tetromino import Tetromino
    from graphics.effects import ParticleSystem
    from graphics.renderer import Renderer
    from audio.sound_manager import SoundManager
    from ui.game_ui import GameUI
    from db.queries import save_game_score, unlock_achievement
    from utils.logger import get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class Game:
    """Main class for Tetris game"""

    def __init__(self, screen, config, username=None, game_mode=MODE_ENDLESS):
        """
        Create a new game

        Args:
            screen (pygame.Surface): Main surface for display
            config (dict): Game config
            username (str, optional): Player name
            game_mode (int, optional): Game mode (endless or victory)
        """
        self.screen = screen
        self.config = config
        self.username = username if username else "Guest"
        self.game_mode = game_mode
        self.logger = get_logger()
        self.logger.info(
            f"Initializing game for player: {self.username}, Mode: {game_mode}"
        )

        try:
            # Create game components with error handling
            self.board = Board()
            self.renderer = Renderer(screen, config)
            self.ui = GameUI(screen, config)
            self.sound_manager = SoundManager(config)
            self.particle_system = ParticleSystem()

            # Setup controls
            self.setup_controls()

            # Start new game
            self.reset_game()
        except Exception as e:
            self.logger.error(f"Error initializing game: {e}\n{traceback.format_exc()}")
            # Create minimal components to prevent crashes
            if not hasattr(self, "board"):
                self.board = Board()
            if not hasattr(self, "renderer"):
                self.renderer = Renderer(screen, config)
            if not hasattr(self, "ui"):
                self.ui = GameUI(screen, config)
            if not hasattr(self, "sound_manager"):
                self.sound_manager = SoundManager(config)
            if not hasattr(self, "particle_system"):
                self.particle_system = ParticleSystem()

            # Initialize basic game state
            self.state = STATE_PLAYING
            self.level = 1
            self.score = 0
            self.lines_cleared = 0
            self.combo = 0
            self.back_to_back = 0
            self.tetromino_bag = []
            self.current_tetromino = None
            self.next_tetrominos = []
            self.hold_tetromino = None
            self.can_hold = True
            self.start_time = time.time()
            self.pause_time = 0
            self.game_over = False
            self.victory = False

            # Setup fallback controls
            self.keys = {}
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

    def setup_controls(self):
        """Setup controls from config file"""
        try:
            controls = self.config["controls"]["keyboard"]

            # Convert key names to pygame values
            self.keys = {}
            for action, key_names in controls.items():
                self.keys[action] = []
                for key_name in key_names:
                    # Convert string to pygame.K_* value
                    if isinstance(key_name, str) and key_name.startswith("K_"):
                        key_value = getattr(pygame, key_name)
                        self.keys[action].append(key_value)
                    else:
                        self.keys[action].append(key_name)
        except Exception as e:
            self.logger.error(f"Error setting up controls: {e}")
            # Create fallback controls
            self.keys = {
                "MOVE_LEFT": [pygame.K_LEFT, pygame.K_a],
                "MOVE_RIGHT": [pygame.K_RIGHT, pygame.K_d],
                "SOFT_DROP": [pygame.K_DOWN, pygame.K_s],
                "HARD_DROP": [pygame.K_SPACE],
                "ROTATE_CW": [pygame.K_UP, pygame.K_x],
                "ROTATE_CCW": [pygame.K_z, pygame.K_LCTRL],
                "HOLD": [pygame.K_c, pygame.K_LSHIFT],
                "PAUSE": [pygame.K_p, pygame.K_ESCAPE],
            }

    def handle_event(self, event):
        """
        Handle input events

        Args:
            event (pygame.event.Event): Event to handle

        Returns:
            bool: True if event was handled, False otherwise
        """
        try:
            if self.state in [STATE_GAME_OVER, STATE_VICTORY]:
                # Handle button press in game over/victory state
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE]:
                        # Return to main menu
                        return True
                return False

            if self.state == STATE_PAUSED:
                # Handle button press in paused state
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                        # Resume game
                        self.state = STATE_PLAYING
                        try:
                            self.sound_manager.play_sound("menu_select")
                        except:
                            pass
                        return True
                return False

            if event.type == pygame.KEYDOWN:
                # Check button press
                for action, keys in self.keys.items():
                    if event.key in keys:
                        self.key_states[action] = True

                        # Handle immediate button actions
                        if action == "PAUSE":
                            if self.state == STATE_PLAYING:
                                self.state = STATE_PAUSED
                                try:
                                    self.sound_manager.play_sound("menu_select")
                                except:
                                    pass
                        elif action == "HARD_DROP" and self.state == STATE_PLAYING:
                            self.hard_drop()
                        elif action == "ROTATE_CW" and self.state == STATE_PLAYING:
                            self.rotate_tetromino(1)
                        elif action == "ROTATE_CCW" and self.state == STATE_PLAYING:
                            self.rotate_tetromino(-1)
                        elif action == "HOLD" and self.state == STATE_PLAYING:
                            self.hold_piece()
                        elif action in ["MOVE_LEFT", "MOVE_RIGHT"]:
                            # Start DAS timer
                            self.das_timer = 0

                            # Move immediately
                            direction = -1 if action == "MOVE_LEFT" else 1
                            self.move_tetromino(direction, 0)

                        return True

            elif event.type == pygame.KEYUP:
                # Check button release
                for action, keys in self.keys.items():
                    if event.key in keys:
                        self.key_states[action] = False

                        # Reset DAS/ARR when movement key is released
                        if action in ["MOVE_LEFT", "MOVE_RIGHT"]:
                            self.das_timer = 0
                            self.arr_timer = 0
                            self.move_direction = 0

                        return True

            return False
        except Exception as e:
            self.logger.error(f"Error handling event: {e}")
            return False

    def update(self, dt):
        """
        Update game state

        Args:
            dt (float): Time passed since last update (seconds)

        Returns:
            object: Next scene (if changing scene) or None
        """
        try:
            # Don't update if game is paused
            if self.state == STATE_PAUSED:
                return None

            # Update board
            board_update = self.board.update(dt)

            # If line clear is complete
            if board_update.get("clearing_complete", False):
                self.state = STATE_PLAYING
                lines_cleared = board_update.get("lines_cleared", 0)

                # Update statistics
                self.lines_cleared += lines_cleared
                base_score = board_update.get("score", 0)

                # Calculate score multipliers
                level_multiplier = self.level

                # Check if this is a T-spin or Tetris
                is_tetris = board_update.get("tetris", False)
                is_t_spin = board_update.get("t_spin", False)

                # Apply back-to-back bonus if appropriate
                if is_tetris or is_t_spin:
                    if self.back_to_back > 0:
                        # Back-to-back bonus
                        base_score = int(base_score * BACK_TO_BACK_MULTIPLIER)
                    self.back_to_back += 1

                    # Track achievements
                    if is_tetris:
                        self.achievement_data["tetris_count"] += 1
                        if self.achievement_data["tetris_count"] == 1:
                            self._unlock_achievement(
                                ACHIEVEMENT_IDS["tetris"],
                                "First Tetris",
                                "Clear 4 lines at once",
                            )

                    if is_t_spin:
                        self.achievement_data["t_spin_count"] += 1
                        if self.achievement_data["t_spin_count"] == 1:
                            self._unlock_achievement(
                                ACHIEVEMENT_IDS["t_spin"],
                                "T-Spin Master",
                                "Perform your first T-Spin",
                            )

                    if self.back_to_back >= 2:
                        self.achievement_data["back_to_back_count"] += 1
                        if self.achievement_data["back_to_back_count"] == 1:
                            self._unlock_achievement(
                                ACHIEVEMENT_IDS["back_to_back"],
                                "Back-to-Back",
                                "Perform consecutive Tetris or T-Spin clears",
                            )
                else:
                    self.back_to_back = 0

                # Apply combo bonus
                if lines_cleared > 0:
                    self.combo += 1
                    # Combo bonus (50 * combo * level)
                    if self.combo > 1:
                        combo_bonus = COMBO_BONUS * self.combo * level_multiplier
                        base_score += combo_bonus
                else:
                    self.combo = 0

                # Add final score
                self.score += base_score * level_multiplier

                # Update max score achievement tracking
                if self.score > self.achievement_data["max_score"]:
                    self.achievement_data["max_score"] = self.score

                    # Check score achievements
                    if self.score >= 10000 and not self._has_achievement("score_10k"):
                        self._unlock_achievement(
                            ACHIEVEMENT_IDS["score_10k"],
                            "Score 10,000",
                            "Reach a score of 10,000 points",
                        )

                    if self.score >= 50000 and not self._has_achievement("score_50k"):
                        self._unlock_achievement(
                            ACHIEVEMENT_IDS["score_50k"],
                            "Score 50,000",
                            "Reach a score of 50,000 points",
                        )

                    if self.score >= 100000 and not self._has_achievement("score_100k"):
                        self._unlock_achievement(
                            ACHIEVEMENT_IDS["score_100k"],
                            "Score 100,000",
                            "Reach a score of 100,000 points",
                        )

                # Check for level up
                level_up_lines = self.config["game"].get("level_up_lines", 10)
                if (
                    self.lines_cleared >= level_up_lines * self.level
                    and self.level < self.config["game"].get("max_level", 20)
                ):
                    self.level += 1

                    # Update max level for achievement tracking
                    if self.level > self.achievement_data["max_level"]:
                        self.achievement_data["max_level"] = self.level

                        # Check level achievements
                        if self.level >= 10 and not self._has_achievement(
                            "reach_level_10"
                        ):
                            self._unlock_achievement(
                                ACHIEVEMENT_IDS["reach_level_10"],
                                "Level 10",
                                "Reach level 10",
                            )

                        if self.level >= 20 and not self._has_achievement(
                            "reach_level_20"
                        ):
                            self._unlock_achievement(
                                ACHIEVEMENT_IDS["reach_level_20"],
                                "Level 20",
                                "Reach level 20",
                            )

                    try:
                        self.sound_manager.play_sound("level_up")
                    except:
                        pass

                    # Create level up particles
                    if self.config["graphics"].get("particles", True):
                        self.create_particles("level_up")

                    # Change music at high level
                    if (
                        self.level >= 15
                        and self.sound_manager.current_music != "high_level"
                    ):
                        try:
                            self.sound_manager.play_music("high_level")
                        except:
                            pass

                    # Check for victory condition
                    if self.game_mode == MODE_VICTORY and self.level >= VICTORY_LEVEL:
                        self._handle_victory()
                        return None

                # Check lines cleared achievement
                if self.lines_cleared >= 100 and not self._has_achievement(
                    "clear_100_lines"
                ):
                    self._unlock_achievement(
                        ACHIEVEMENT_IDS["clear_100_lines"],
                        "Line Clearer",
                        "Clear 100 lines total",
                    )

                # Play sound based on lines cleared
                try:
                    if lines_cleared == 4:
                        self.sound_manager.play_sound("tetris")
                        # Create tetris particles
                        if self.config["graphics"].get("particles", True):
                            self.create_particles("tetris")
                    elif lines_cleared > 0:
                        self.sound_manager.play_sound("clear")
                        # Create line clear particles
                        if self.config["graphics"].get("particles", True):
                            self.create_particles("line_clear", lines_cleared)
                except Exception as e:
                    self.logger.warning(f"Sound error: {e}")

            # Update particles
            if self.config["graphics"].get("particles", True):
                try:
                    self.particle_system.update(dt)
                except Exception as e:
                    self.logger.warning(f"Particle system error: {e}")

            # Update game state
            if self.state == STATE_PLAYING:
                self._update_game(dt)
            elif self.state == STATE_LINE_CLEAR:
                # In line clear state, just wait for board update to finish
                pass
            elif self.state == STATE_GAME_OVER:
                # Save score
                if not self.game_over:
                    self._handle_game_over()
            elif self.state == STATE_VICTORY:
                # Handle victory state
                if not self.victory:
                    self._handle_victory()

            return None
        except Exception as e:
            self.logger.error(f"Error updating game: {e}")
            return None

    def _update_game(self, dt):
        """
        Update game state in play mode

        Args:
            dt (float): Time passed since last update (seconds)
        """
        try:
            # Handle left/right movement (DAS/ARR)
            self._handle_horizontal_movement(dt)

            # Handle automatic drop and soft drop
            gravity = self._get_gravity_delay()

            # If soft drop button is pressed, use higher speed
            if self.key_states["SOFT_DROP"]:
                gravity /= 20  # 20x faster when pressing down

            # Increase drop timer
            self.drop_timer += dt

            # If it's time to drop
            if self.drop_timer >= gravity:
                self.drop_timer = 0

                # Try to move down
                if self.move_tetromino(0, 1):
                    # If doing soft drop, add score
                    if self.key_states["SOFT_DROP"]:
                        self.score += SCORE_SOFT_DROP
                else:
                    # If can't move down, start lock timer
                    self.lock_pending = True

            # Handle piece locking
            if self.lock_pending:
                self.lock_timer += dt

                if self.lock_timer >= self.lock_delay:
                    self._lock_tetromino()
        except Exception as e:
            self.logger.error(f"Error in game update: {e}")

    def _handle_horizontal_movement(self, dt):
        """
        Handle left/right movement with DAS/ARR

        Args:
            dt (float): Time passed since last update (seconds)
        """
        try:
            # Check if left or right button is pressed
            if self.key_states["MOVE_LEFT"] and not self.key_states["MOVE_RIGHT"]:
                direction = -1
            elif self.key_states["MOVE_RIGHT"] and not self.key_states["MOVE_LEFT"]:
                direction = 1
            else:
                # No button pressed or both pressed
                self.move_direction = 0
                return

            # Increase DAS timer
            self.das_timer += dt * 1000  # Convert to milliseconds

            # If past DAS delay
            if self.das_timer >= DAS_DELAY:
                # Increase ARR timer
                self.arr_timer += dt * 1000

                # Move according to ARR
                if self.arr_timer >= ARR_DELAY:
                    self.arr_timer = 0
                    self.move_tetromino(direction, 0)
        except Exception as e:
            self.logger.error(f"Error handling horizontal movement: {e}")

    def _get_gravity_delay(self):
        """
        Calculate time for one cell drop

        Returns:
            float: Delay in seconds
        """
        try:
            # Get speed from table
            level_capped = min(self.level, 20)  # Cap at level 20
            frames_per_drop = GRAVITY_LEVELS.get(level_capped, 1)

            # Convert frames to seconds (at 60 fps)
            return frames_per_drop / 60.0
        except Exception as e:
            self.logger.error(f"Error calculating gravity delay: {e}")
            return 1.0 / 60.0  # Default to 1 frame

    def rotate_tetromino(self, direction):
        """
        Rotate current tetromino

        Args:
            direction (int): 1 for clockwise, -1 for counter-clockwise

        Returns:
            bool: True if rotation succeeded, False if not possible
        """
        try:
            if self.current_tetromino.rotate(direction, self.board):
                # Play rotation sound
                try:
                    self.sound_manager.play_sound("rotate")
                except:
                    pass

                # If about to lock, reset lock timer (to allow movement)
                if self.lock_pending:
                    self.lock_timer = 0

                return True
            return False
        except Exception as e:
            self.logger.error(f"Error rotating tetromino: {e}")
            return False

    def move_tetromino(self, dx, dy):
        """
        Move current tetromino

        Args:
            dx (int): Change in x axis
            dy (int): Change in y axis

        Returns:
            bool: True if movement succeeded, False if not possible
        """
        try:
            if self.current_tetromino.move(dx, dy, self.board):
                # Play movement sound (only for left/right movement)
                if dx != 0 and dy == 0:
                    try:
                        self.sound_manager.play_sound("move")
                    except:
                        pass

                # If about to lock and has moved, reset lock timer
                if self.lock_pending and (dx != 0 or dy < 0):
                    self.lock_timer = 0

                return True
            return False
        except Exception as e:
            self.logger.error(f"Error moving tetromino: {e}")
            return False

    def hard_drop(self):
        """Drop piece to bottom immediately"""
        try:
            if self.state != STATE_PLAYING or not self.current_tetromino:
                return

            # Calculate drop distance
            drop_distance = self.current_tetromino.hard_drop(self.board)

            # Add score
            self.score += drop_distance * SCORE_HARD_DROP

            # Play sound
            try:
                self.sound_manager.play_sound("drop")
            except:
                pass

            # Lock piece immediately
            self._lock_tetromino()
        except Exception as e:
            self.logger.error(f"Error performing hard drop: {e}")

    def hold_piece(self):
        """Store current piece and swap with held piece"""
        try:
            # Check if hold feature is enabled
            if not self.config["tetromino"].get("enable_hold", True):
                return

            # Check if can hold now
            if not self.can_hold:
                return

            # Play sound
            try:
                self.sound_manager.play_sound("hold")
            except:
                pass

            # Swap pieces
            if self.hold_tetromino is None:
                # Store current piece and get new one
                self.hold_tetromino = Tetromino(self.current_tetromino.shape_name)
                self.current_tetromino = self.get_next_tetromino()
                self.next_tetrominos.append(self.get_next_tetromino())
                self.next_tetrominos.pop(0)
            else:
                # Swap between current and held piece
                temp = self.current_tetromino.shape_name
                self.current_tetromino = Tetromino(
                    self.hold_tetromino.shape_name, x=(BOARD_WIDTH // 2) - 1, y=0
                )
                self.hold_tetromino = Tetromino(temp)

            # Can't hold again until next piece is locked
            self.can_hold = False

            # Reset lock state
            self.lock_pending = False
            self.lock_timer = 0
        except Exception as e:
            self.logger.error(f"Error holding piece: {e}")

    def _lock_tetromino(self):
        """Lock current tetromino to board"""
        try:
            # Check for T-spin
            t_spin = getattr(self.current_tetromino, "t_spin", False)

            # Lock piece to board
            if not self.board.lock_tetromino(self.current_tetromino):
                # Game over (piece above board)
                self.state = STATE_GAME_OVER
                return

            # Add T-spin score
            if t_spin:
                self.score += SCORE_T_SPIN * self.level
                try:
                    self.sound_manager.play_sound("t_spin")
                except:
                    pass

                # Create T-spin particles
                if self.config["graphics"].get("particles", True):
                    self.create_particles("t_spin")

            # Check for line clears
            if self.board.clearing_lines:
                self.state = STATE_LINE_CLEAR

            # Prepare next piece
            self.current_tetromino = self.next_tetrominos.pop(0)
            self.next_tetrominos.append(self.get_next_tetromino())

            # Reset states
            self.lock_pending = False
            self.lock_timer = 0
            self.can_hold = True  # Allow holding again
        except Exception as e:
            self.logger.error(f"Error locking tetromino: {e}")
            # Try to recover
            if self.state != STATE_GAME_OVER:
                self.current_tetromino = self.get_next_tetromino()
                self.next_tetrominos.append(self.get_next_tetromino())
                if len(self.next_tetrominos) > 0:
                    self.next_tetrominos.pop(0)
                self.lock_pending = False
                self.lock_timer = 0
                self.can_hold = True

    def reset_game(self):
        """Reset game state"""
        self.state = STATE_PLAYING
        self.level = 1
        self.score = 0
        self.lines_cleared = 0
        self.combo = 0
        self.back_to_back = 0
        self.tetromino_bag = []
        self.next_tetrominos = []
        self.hold_tetromino = None
        self.can_hold = True
        self.start_time = time.time()
        self.pause_time = 0
        self.game_over = False
        self.victory = False

        # Movement state tracking
        self.das_timer = 0
        self.arr_timer = 0
        self.move_direction = 0
        self.drop_timer = 0
        self.lock_timer = 0
        self.lock_delay = 0.5
        self.lock_pending = False

        # Achievement tracking
        self.achievement_data = {
            "max_score": 0,
            "max_level": 1,
            "tetris_count": 0,
            "t_spin_count": 0,
            "back_to_back_count": 0,
            "unlocked": set(),
        }

        # Initialize board
        self.board.reset_grid()

        # Create initial pieces
        self.current_tetromino = self.get_next_tetromino()
        for _ in range(5):
            self.next_tetrominos.append(self.get_next_tetromino())

        # Start game music
        try:
            self.sound_manager.play_music("game")
        except:
            self.logger.warning("Could not play game music")

    def create_particles(self, effect_type, multiplier=1):
        """
        Create particles for special effects

        Args:
            effect_type (str): Type of effect
            multiplier (int): Particle count multiplier
        """
        try:
            # Get particle count from constants
            count = PARTICLE_COUNT.get(effect_type, 50) * multiplier

            # Set position and color based on effect type
            if effect_type == "line_clear":
                # Create particles for each cleared line
                for line in self.board.clearing_lines:
                    y = self.board.y + line * GRID_SIZE + GRID_SIZE // 2
                    for i in range(count // len(self.board.clearing_lines)):
                        x = self.board.x + random.randint(
                            0, self.board.width * GRID_SIZE
                        )
                        color = (255, 255, 255)
                        self.particle_system.create_particle(x, y, color)

            elif effect_type == "tetris":
                # Many particles spread across board
                for _ in range(count):
                    x = self.board.x + random.randint(0, self.board.width * GRID_SIZE)
                    y = self.board.y + random.randint(0, self.board.height * GRID_SIZE)
                    color = (random.randint(100, 255), random.randint(100, 255), 255)
                    self.particle_system.create_particle(x, y, color)

            elif effect_type == "t_spin":
                # Purple particles around T block
                center_x = self.board.x + (self.current_tetromino.x + 1) * GRID_SIZE
                center_y = self.board.y + (self.current_tetromino.y + 1) * GRID_SIZE
                for _ in range(count):
                    angle = random.uniform(0, 6.28)
                    distance = random.uniform(0, GRID_SIZE * 3)
                    x = center_x + distance * math.cos(angle)
                    y = center_y + distance * math.sin(angle)
                    color = (128, 0, 128)  # Purple
                    self.particle_system.create_particle(x, y, color)

            elif effect_type == "level_up":
                # Particles across screen
                for _ in range(count):
                    x = random.randint(0, SCREEN_WIDTH)
                    y = random.randint(0, SCREEN_HEIGHT)
                    color = (255, 215, 0)  # Gold
                    self.particle_system.create_particle(x, y, color, life_span=2.0)

            elif effect_type == "game_over":
                # Particles falling from top of board
                for _ in range(count):
                    x = self.board.x + random.randint(0, self.board.width * GRID_SIZE)
                    y = self.board.y - random.randint(0, GRID_SIZE * 5)
                    color = (255, 0, 0)  # Red
                    self.particle_system.create_particle(
                        x, y, color, life_span=3.0, gravity=200
                    )

            elif effect_type == "victory":
                # Colorful firework particles
                for _ in range(count):
                    # Create multiple explosion centers
                    center_x = random.randint(0, SCREEN_WIDTH)
                    center_y = random.randint(0, SCREEN_HEIGHT)

                    # Randomize color for this firework
                    r = random.randint(100, 255)
                    g = random.randint(100, 255)
                    b = random.randint(100, 255)
                    color = (r, g, b)

                    # Create explosion particles
                    for i in range(20):  # 20 particles per firework
                        angle = random.uniform(0, 6.28)
                        speed = random.uniform(50, 200)
                        distance = random.uniform(0, 5)  # Initial distance

                        # Calculate position
                        x = center_x + distance * math.cos(angle)
                        y = center_y + distance * math.sin(angle)

                        # Calculate velocity
                        vx = math.cos(angle) * speed
                        vy = math.sin(angle) * speed

                        # Create particle with velocity
                        self.particle_system.create_particle(
                            x,
                            y,
                            color,
                            velocity=(vx, vy),
                            life_span=random.uniform(1.0, 3.0),
                            size=random.uniform(2, 5),
                            fade=True,
                        )

        except Exception as e:
            self.logger.error(f"Error creating particles: {e}")

    def _unlock_achievement(self, achievement_id, name, description):
        """
        Unlock an achievement with error handling

        Args:
            achievement_id (str): Achievement identifier
            name (str): Achievement name
            description (str): Achievement description
        """
        try:
            unlock_achievement(self.username, achievement_id, name, description)
            self.logger.info(f"Achievement unlocked: {name} for {self.username}")
        except Exception as e:
            self.logger.error(f"Error unlocking achievement {achievement_id}: {e}")

    def _has_achievement(self, achievement_id):
        """
        Check if player has the specified achievement

        Args:
            achievement_id (str): Achievement to check

        Returns:
            bool: True if player has achievement
        """
        # This is a stub that could be implemented with the database
        # For now, we'll just use our achievement_data to prevent duplicates
        # in the current session
        return achievement_id in self.achievement_data.get("unlocked", [])

    def render(self):
        """Render the entire game"""
        try:
            # Draw background
            self.renderer.render_background(self.level)

            # Draw board
            self.board.render(self.screen)

            # Draw current tetromino
            if self.state in [STATE_PLAYING, STATE_PAUSED] and self.current_tetromino:
                # Draw ghost piece (shadow)
                if self.config["tetromino"].get("ghost_piece", True):
                    ghost_y = self.current_tetromino.get_ghost_position(self.board)
                    self.board.render_ghost(
                        self.screen, self.current_tetromino, ghost_y
                    )

                # Draw current piece
                self.board.render_tetromino(self.screen, self.current_tetromino)

            # Draw particles
            if self.config["graphics"].get("particles", True):
                try:
                    self.particle_system.render(self.screen)
                except Exception as e:
                    self.logger.warning(f"Error rendering particles: {e}")

            # Draw user interface (score, level, etc.)
            try:
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
                    "game_mode": self.game_mode,
                }
                self.ui.render(ui_data)
            except Exception as e:
                self.logger.error(f"Error rendering UI: {e}")
                # Fallback simple UI
                self._render_fallback_ui()

            # Render specific game state overlays
            if self.state == STATE_PAUSED:
                try:
                    self.renderer.render_pause_overlay()
                except Exception as e:
                    self.logger.warning(f"Error rendering pause overlay: {e}")
                    # Fallback pause message
                    self._draw_simple_text(
                        "PAUSED",
                        (255, 255, 255),
                        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                    )
            elif self.state == STATE_GAME_OVER:
                try:
                    self.renderer.render_game_over(
                        self.score, self.level, self.lines_cleared
                    )
                except Exception as e:
                    self.logger.warning(f"Error rendering game over screen: {e}")
                    # Fallback game over message
                    self._draw_simple_text(
                        "GAME OVER",
                        (255, 0, 0),
                        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                    )
                    self._draw_simple_text(
                        f"Score: {self.score}",
                        (255, 255, 255),
                        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40),
                    )
            elif self.state == STATE_VICTORY:
                try:
                    self.renderer.render_victory(
                        self.score, self.level, self.lines_cleared
                    )
                except Exception as e:
                    self.logger.warning(f"Error rendering victory screen: {e}")
                    # Fallback victory message
                    self._draw_simple_text(
                        "VICTORY!",
                        (255, 215, 0),  # Gold
                        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40),
                    )
                    self._draw_simple_text(
                        f"Score: {self.score}",
                        (255, 255, 255),
                        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                    )
                    self._draw_simple_text(
                        "Press ENTER to continue",
                        (255, 255, 255),
                        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80),
                    )

            # Apply bloom effect if enabled
            if self.config["graphics"].get("bloom_effect", True):
                try:
                    self.renderer.apply_bloom(self.screen)
                except Exception as e:
                    self.logger.warning(f"Error applying bloom effect: {e}")

            # Update screen
            pygame.display.flip()

        except Exception as e:
            self.logger.error(f"Error rendering game: {e}\n{traceback.format_exc()}")
            # Try to render minimal fallback
            try:
                self.screen.fill((0, 0, 0))
                font = pygame.font.SysFont("Arial", 24)
                text = font.render("Rendering Error", True, (255, 0, 0))
                self.screen.blit(
                    text,
                    (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2),
                )
                pygame.display.flip()
            except:
                pass  # Ultimate fallback - just ignore if everything fails

    def _render_fallback_ui(self):
        """Render simple fallback UI if normal UI fails"""
        try:
            # Use system font
            font = pygame.font.SysFont("Arial", 20)

            # Draw score
            score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))

            # Draw level
            level_text = font.render(f"Level: {self.level}", True, (255, 255, 255))
            self.screen.blit(level_text, (20, 50))

            # Draw lines
            lines_text = font.render(
                f"Lines: {self.lines_cleared}", True, (255, 255, 255)
            )
            self.screen.blit(lines_text, (20, 80))

            # Draw player name
            name_text = font.render(f"Player: {self.username}", True, (255, 255, 255))
            self.screen.blit(name_text, (20, 110))

            # Draw game mode
            mode_text = (
                "Mode: Victory" if self.game_mode == MODE_VICTORY else "Mode: Endless"
            )
            mode_render = font.render(mode_text, True, (255, 255, 255))
            self.screen.blit(mode_render, (20, 140))

        except Exception as e:
            self.logger.error(f"Error rendering fallback UI: {e}")

    def _draw_simple_text(self, text, color, position):
        """Draw simple text for fallback messages"""
        try:
            font = pygame.font.SysFont("Arial", 32)
            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect(center=position)
            self.screen.blit(text_surf, text_rect)
        except Exception as e:
            self.logger.error(f"Error drawing simple text: {e}")
