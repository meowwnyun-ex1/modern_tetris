#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Fixed Game Class
------------------------------
Complete implementation with all missing methods and proper error handling
"""

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame
        print("Using pygame-ce instead of pygame")
    except ImportError:
        print("Please install pygame or pygame-ce")
        import sys
        sys.exit(1)

import random
import time
import logging
import math
import traceback
from pygame.locals import *
import sys

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
    from utils.logger import get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# Fallback database functions
try:
    from db.queries import save_game_score, unlock_achievement
except ImportError:
    def save_game_score(*args, **kwargs):
        print("Database not available - score not saved")
        return True
    def unlock_achievement(*args, **kwargs):
        print("Database not available - achievement not saved")
        return True


class Game:
    """Complete Tetris game implementation"""

    def __init__(self, screen, config, username=None, game_mode=MODE_ENDLESS):
        self.screen = screen
        self.config = config
        self.username = username if username else "Guest"
        self.game_mode = game_mode
        self.logger = get_logger("tetris.game")
        
        try:
            # Initialize components
            self.board = Board(config=config)
            self.renderer = Renderer(screen, config)
            self.ui = GameUI(screen, config)
            self.sound_manager = SoundManager(config)
            self.particle_system = ParticleSystem()

            # Setup controls and reset game
            self.setup_controls()
            self.reset_game()
            
        except Exception as e:
            self.logger.error(f"Error initializing game: {e}")
            self._create_fallback_components()

    def _create_fallback_components(self):
        """Create minimal components to prevent crashes"""
        try:
            if not hasattr(self, 'board'):
                self.board = Board()
            if not hasattr(self, 'renderer'):
                self.renderer = Renderer(self.screen, self.config)
            if not hasattr(self, 'ui'):
                self.ui = GameUI(self.screen, self.config)
            if not hasattr(self, 'particle_system'):
                self.particle_system = ParticleSystem()
        except:
            pass
            
        # Dummy sound manager
        class DummySoundManager:
            def play_sound(self, *args, **kwargs): pass
            def play_music(self, *args, **kwargs): pass
            def stop_music(self, *args, **kwargs): pass
        
        if not hasattr(self, 'sound_manager'):
            self.sound_manager = DummySoundManager()

        # Initialize basic state
        self.state = STATE_PLAYING
        self.level = 1
        self.score = 0
        self.lines_cleared = 0
        self.combo = 0
        self.back_to_back = 0
        self.start_time = time.time()
        self.game_over = False
        self.victory = False

    def setup_controls(self):
        """Setup controls with fallback"""
        try:
            controls = self.config.get("controls", {}).get("keyboard", {})
            self.keys = {}
            
            for action, key_names in controls.items():
                self.keys[action] = []
                for key_name in key_names:
                    if isinstance(key_name, str) and key_name.startswith("K_"):
                        try:
                            key_value = getattr(pygame, key_name)
                            self.keys[action].append(key_value)
                        except AttributeError:
                            continue
                    else:
                        self.keys[action].append(key_name)
        except:
            # Fallback controls
            self.keys = {
                "move_left": [pygame.K_LEFT, pygame.K_a],
                "move_right": [pygame.K_RIGHT, pygame.K_d],
                "soft_drop": [pygame.K_DOWN, pygame.K_s],
                "hard_drop": [pygame.K_SPACE],
                "rotate_cw": [pygame.K_UP, pygame.K_x],
                "rotate_ccw": [pygame.K_z, pygame.K_LCTRL],
                "hold": [pygame.K_c, pygame.K_LSHIFT],
                "pause": [pygame.K_p, pygame.K_ESCAPE],
            }

        # Key states for continuous input
        self.key_states = {action: False for action in self.keys}

    def reset_game(self):
        """Reset game to initial state"""
        self.state = STATE_PLAYING
        self.level = 1
        self.score = 0
        self.lines_cleared = 0
        self.combo = 0
        self.back_to_back = 0
        self.start_time = time.time()
        self.pause_time = 0
        self.game_over = False
        self.victory = False

        # Movement state
        self.das_timer = 0
        self.arr_timer = 0
        self.drop_timer = 0
        self.lock_timer = 0
        self.lock_delay = 0.5
        self.lock_pending = False

        # Tetromino system
        self.tetromino_bag = []
        self.next_tetrominos = []
        self.hold_tetromino = None
        self.can_hold = True

        # Achievement tracking
        self.achievement_data = {
            "max_score": 0,
            "max_level": 1,
            "tetris_count": 0,
            "t_spin_count": 0,
            "back_to_back_count": 0,
            "unlocked": set(),
        }

        # Reset board and create initial pieces
        self.board.reset_grid()
        self.current_tetromino = self.get_next_tetromino()
        for _ in range(5):
            self.next_tetrominos.append(self.get_next_tetromino())

        # Start music
        try:
            self.sound_manager.play_music("game")
        except:
            pass

    def get_next_tetromino(self):
        """Get next tetromino using 7-bag system"""
        if not self.tetromino_bag:
            self.tetromino_bag = ['I', 'J', 'L', 'O', 'S', 'T', 'Z']
            random.shuffle(self.tetromino_bag)

        piece_type = self.tetromino_bag.pop()
        return Tetromino(piece_type, x=(BOARD_WIDTH // 2) - 1, y=0)

    def handle_event(self, event):
        """Handle input events"""
        try:
            if self.state in [STATE_GAME_OVER, STATE_VICTORY]:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE]:
                        return True
                return False

            if self.state == STATE_PAUSED:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_p, pygame.K_ESCAPE]:
                        self.state = STATE_PLAYING
                        self.sound_manager.play_sound("menu_select")
                        return True
                return False

            if event.type == pygame.KEYDOWN:
                for action, keys in self.keys.items():
                    if event.key in keys:
                        self.key_states[action] = True
                        return self._handle_key_action(action)

            elif event.type == pygame.KEYUP:
                for action, keys in self.keys.items():
                    if event.key in keys:
                        self.key_states[action] = False
                        if action in ["move_left", "move_right"]:
                            self.das_timer = 0
                            self.arr_timer = 0
                        return True

            return False
        except Exception as e:
            self.logger.error(f"Error handling event: {e}")
            return False

    def _handle_key_action(self, action):
        """Handle immediate key actions"""
        if action == "pause":
            if self.state == STATE_PLAYING:
                self.state = STATE_PAUSED
                self.sound_manager.play_sound("menu_select")
        elif action == "hard_drop" and self.state == STATE_PLAYING:
            self.hard_drop()
        elif action == "rotate_cw" and self.state == STATE_PLAYING:
            self.rotate_tetromino(1)
        elif action == "rotate_ccw" and self.state == STATE_PLAYING:
            self.rotate_tetromino(-1)
        elif action == "hold" and self.state == STATE_PLAYING:
            self.hold_piece()
        elif action in ["move_left", "move_right"]:
            self.das_timer = 0
            direction = -1 if action == "move_left" else 1
            self.move_tetromino(direction, 0)
        return True

    def update(self, dt):
        """Update game state"""
        try:
            if self.state == STATE_PAUSED:
                return None

            # Update board (line clearing)
            board_update = self.board.update(dt)

            if board_update.get("clearing_complete", False):
                self.state = STATE_PLAYING
                lines_cleared = board_update.get("lines_cleared", 0)
                if lines_cleared > 0:
                    self._handle_line_clear(lines_cleared, board_update)

            # Update particles
            if self.config.get("graphics", {}).get("particles", True):
                self.particle_system.update(dt)

            # Update game logic
            if self.state == STATE_PLAYING:
                self._update_gameplay(dt)
            elif self.state == STATE_GAME_OVER and not self.game_over:
                self._handle_game_over()
            elif self.state == STATE_VICTORY and not self.victory:
                self._handle_victory()

            return None
        except Exception as e:
            self.logger.error(f"Error updating game: {e}")
            return None

    def _handle_line_clear(self, lines_cleared, board_update):
        """Handle line clearing and scoring"""
        self.lines_cleared += lines_cleared
        base_score = board_update.get("score", 0)
        level_multiplier = self.level
        is_tetris = board_update.get("tetris", False)
        is_t_spin = board_update.get("t_spin", False)

        # Back-to-back bonus
        if is_tetris or is_t_spin:
            if self.back_to_back > 0:
                base_score = int(base_score * BACK_TO_BACK_MULTIPLIER)
            self.back_to_back += 1
        else:
            self.back_to_back = 0

        # Combo bonus
        if lines_cleared > 0:
            self.combo += 1
            if self.combo > 1:
                combo_bonus = COMBO_BONUS * self.combo * level_multiplier
                base_score += combo_bonus
        else:
            self.combo = 0

        # Add final score
        self.score += base_score * level_multiplier

        # Level up check
        level_up_lines = self.config.get("game", {}).get("level_up_lines", 10)
        if (self.lines_cleared >= level_up_lines * self.level and 
            self.level < self.config.get("game", {}).get("max_level", 20)):
            self.level += 1
            self.sound_manager.play_sound("level_up")
            
            # Victory check
            if self.game_mode == MODE_VICTORY and self.level >= VICTORY_LEVEL:
                self._handle_victory()

        # Play sounds
        if lines_cleared == 4:
            self.sound_manager.play_sound("tetris")
            self.create_particles("tetris", 2)
        elif lines_cleared > 0:
            self.sound_manager.play_sound("clear")
            self.create_particles("line_clear", lines_cleared)

    def _update_gameplay(self, dt):
        """Update gameplay mechanics"""
        # Handle horizontal movement
        self._handle_horizontal_movement(dt)

        # Handle gravity
        gravity = self._get_gravity_delay()
        if self.key_states.get("soft_drop", False):
            gravity /= 20

        self.drop_timer += dt
        if self.drop_timer >= gravity:
            self.drop_timer = 0
            if self.move_tetromino(0, 1):
                if self.key_states.get("soft_drop", False):
                    self.score += SCORE_SOFT_DROP
            else:
                self.lock_pending = True

        # Handle piece locking
        if self.lock_pending:
            self.lock_timer += dt
            if self.lock_timer >= self.lock_delay:
                self._lock_tetromino()

    def _handle_horizontal_movement(self, dt):
        """Handle DAS/ARR movement"""
        if self.key_states.get("move_left", False) and not self.key_states.get("move_right", False):
            direction = -1
        elif self.key_states.get("move_right", False) and not self.key_states.get("move_left", False):
            direction = 1
        else:
            return

        self.das_timer += dt * 1000
        if self.das_timer >= DAS_DELAY:
            self.arr_timer += dt * 1000
            if self.arr_timer >= ARR_DELAY:
                self.arr_timer = 0
                self.move_tetromino(direction, 0)

    def _get_gravity_delay(self):
        """Calculate gravity delay"""
        level_capped = min(self.level, 20)
        frames_per_drop = GRAVITY_LEVELS.get(level_capped, 1)
        return frames_per_drop / 60.0

    def move_tetromino(self, dx, dy):
        """Move current tetromino"""
        try:
            if self.current_tetromino.move(dx, dy, self.board):
                if dx != 0 and dy == 0:
                    self.sound_manager.play_sound("move")
                if self.lock_pending and (dx != 0 or dy < 0):
                    self.lock_timer = 0
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error moving tetromino: {e}")
            return False

    def rotate_tetromino(self, direction):
        """Rotate current tetromino"""
        try:
            if self.current_tetromino.rotate(direction, self.board):
                self.sound_manager.play_sound("rotate")
                if self.lock_pending:
                    self.lock_timer = 0
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error rotating tetromino: {e}")
            return False

    def hard_drop(self):
        """Drop piece immediately"""
        try:
            if self.state != STATE_PLAYING or not self.current_tetromino:
                return

            drop_distance = self.current_tetromino.hard_drop(self.board)
            self.score += drop_distance * SCORE_HARD_DROP
            self.sound_manager.play_sound("drop")
            self._lock_tetromino()
        except Exception as e:
            self.logger.error(f"Error performing hard drop: {e}")

    def hold_piece(self):
        """Hold current piece"""
        try:
            if not self.config.get("tetromino", {}).get("enable_hold", True):
                return
            if not self.can_hold:
                return

            self.sound_manager.play_sound("hold")

            if self.hold_tetromino is None:
                self.hold_tetromino = Tetromino(self.current_tetromino.shape_name)
                self.current_tetromino = self.next_tetrominos.pop(0)
                self.next_tetrominos.append(self.get_next_tetromino())
            else:
                temp = self.current_tetromino.shape_name
                self.current_tetromino = Tetromino(
                    self.hold_tetromino.shape_name, 
                    x=(BOARD_WIDTH // 2) - 1, 
                    y=0
                )
                self.hold_tetromino = Tetromino(temp)

            self.can_hold = False
            self.lock_pending = False
            self.lock_timer = 0
        except Exception as e:
            self.logger.error(f"Error holding piece: {e}")

    def _lock_tetromino(self):
        """Lock tetromino to board"""
        try:
            if not self.board.lock_tetromino(self.current_tetromino):
                self.state = STATE_GAME_OVER
                return

            if self.board.clearing_lines:
                self.state = STATE_LINE_CLEAR

            # Prepare next piece
            self.current_tetromino = self.next_tetrominos.pop(0)
            self.next_tetrominos.append(self.get_next_tetromino())

            # Reset states
            self.lock_pending = False
            self.lock_timer = 0
            self.can_hold = True

        except Exception as e:
            self.logger.error(f"Error locking tetromino: {e}")
            # Recovery
            self.current_tetromino = self.get_next_tetromino()
            self.next_tetrominos = [self.get_next_tetromino() for _ in range(5)]

    def _handle_game_over(self):
        """Handle game over state"""
        if not self.game_over:
            self.game_over = True
            self.sound_manager.stop_music()
            self.sound_manager.play_sound("game_over")
            
            # Create game over particles
            self.create_particles("game_over", 2)
            
            # Save score
            try:
                save_game_score(
                    self.username, 
                    self.score, 
                    self.level, 
                    self.lines_cleared, 
                    time.time() - self.start_time, 
                    False
                )
                self.logger.info(f"Game over score saved: {self.score}")
            except Exception as e:
                self.logger.error(f"Error saving score: {e}")

    def _handle_victory(self):
        """Handle victory state"""
        if not self.victory:
            self.victory = True
            self.state = STATE_VICTORY
            self.sound_manager.stop_music()
            self.sound_manager.play_sound("level_up")
            
            # Create victory particles
            self.create_particles("victory", 3)
            
            # Save victory score
            try:
                save_game_score(
                    self.username, 
                    self.score, 
                    self.level, 
                    self.lines_cleared, 
                    time.time() - self.start_time, 
                    True
                )
                self.logger.info(f"Victory score saved: {self.score}")
            except Exception as e:
                self.logger.error(f"Error saving victory score: {e}")

    def create_particles(self, effect_type, multiplier=1):
        """Create particle effects"""
        try:
            count = PARTICLE_COUNT.get(effect_type, 50) * multiplier

            if effect_type == "line_clear":
                for line in self.board.clearing_lines:
                    y = self.board.y + line * GRID_SIZE + GRID_SIZE // 2
                    for i in range(count // len(self.board.clearing_lines)):
                        x = self.board.x + random.randint(0, self.board.width * GRID_SIZE)
                        color = (255, 255, 255)
                        self.particle_system.create_particle(x, y, color)

            elif effect_type == "tetris":
                for _ in range(count):
                    x = self.board.x + random.randint(0, self.board.width * GRID_SIZE)
                    y = self.board.y + random.randint(0, self.board.height * GRID_SIZE)
                    color = (random.randint(100, 255), random.randint(100, 255), 255)
                    self.particle_system.create_particle(x, y, color)

            elif effect_type == "level_up":
                for _ in range(count):
                    x = random.randint(0, SCREEN_WIDTH)
                    y = random.randint(0, SCREEN_HEIGHT)
                    color = (255, 215, 0)  # Gold
                    self.particle_system.create_particle(x, y, color, life_span=2.0)

            elif effect_type == "game_over":
                for _ in range(count):
                    x = self.board.x + random.randint(0, self.board.width * GRID_SIZE)
                    y = self.board.y - random.randint(0, GRID_SIZE * 5)
                    color = (255, 0, 0)
                    self.particle_system.create_particle(x, y, color, life_span=3.0, gravity=200)

            elif effect_type == "victory":
                for _ in range(count):
                    center_x = random.randint(0, SCREEN_WIDTH)
                    center_y = random.randint(0, SCREEN_HEIGHT)
                    
                    r = random.randint(100, 255)
                    g = random.randint(100, 255)
                    b = random.randint(100, 255)
                    color = (r, g, b)
                    
                    for i in range(20):
                        angle = random.uniform(0, 6.28)
                        speed = random.uniform(50, 200)
                        distance = random.uniform(0, 5)
                        
                        x = center_x + distance * math.cos(angle)
                        y = center_y + distance * math.sin(angle)
                        
                        vx = math.cos(angle) * speed
                        vy = math.sin(angle) * speed
                        
                        self.particle_system.create_particle(
                            x, y, color,
                            velocity=(vx, vy),
                            life_span=random.uniform(1.0, 3.0),
                            size=random.uniform(2, 5),
                            fade=True
                        )

        except Exception as e:
            self.logger.error(f"Error creating particles: {e}")

    def render(self):
        """Render the complete game"""
        try:
            # Draw background
            self.renderer.render_background(self.level)

            # Draw board
            self.board.render(self.screen)

            # Draw current tetromino
            if self.state in [STATE_PLAYING, STATE_PAUSED] and self.current_tetromino:
                # Draw ghost piece
                if self.config.get("tetromino", {}).get("ghost_piece", True):
                    ghost_y = self.current_tetromino.get_ghost_position(self.board)
                    self.board.render_ghost(self.screen, self.current_tetromino, ghost_y)

                # Draw current piece
                self.board.render_tetromino(self.screen, self.current_tetromino)

            # Draw particles
            if self.config.get("graphics", {}).get("particles", True):
                self.particle_system.render(self.screen)

            # Draw UI
            ui_data = {
                "score": self.score,
                "level": self.level,
                "lines": self.lines_cleared,
                "next_tetrominos": self.next_tetrominos,
                "hold_tetromino": self.hold_tetromino,
                "can_hold": self.can_hold,
                "state": self.state,
                "username": self.username,
                "time": time.time() - self.start_time,
                "game_mode": self.game_mode,
            }
            self.ui.render(ui_data)

            # Render state overlays
            if self.state == STATE_PAUSED:
                self.renderer.render_pause_overlay()
            elif self.state == STATE_GAME_OVER:
                self.renderer.render_game_over(self.score, self.level, self.lines_cleared)
            elif self.state == STATE_VICTORY:
                self.renderer.render_victory(self.score, self.level, self.lines_cleared)

            # Apply bloom effect
            if self.config.get("graphics", {}).get("bloom_effect", True):
                self.renderer.apply_bloom(self.screen)

            pygame.display.flip()

        except Exception as e:
            self.logger.error(f"Error rendering game: {e}")
            # Fallback rendering
            self.screen.fill((0, 0, 0))
            font = pygame.font.SysFont("Arial", 24)
            error_text = font.render("Rendering Error", True, (255, 0, 0))
            self.screen.blit(error_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
            pygame.display.flip()