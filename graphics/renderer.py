#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Renderer
----------------------
Class for rendering all graphics with improved error handling
"""

import pygame
import math
import random
import os
import logging
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
    DENSO_RED,
    DENSO_DARK_RED,
    DENSO_LIGHT_RED,
)
from graphics.effects import BloomEffect, ShakeEffect
from utils.logger import get_logger


class Renderer:
    """Class for graphics rendering with improved error handling"""

    def __init__(self, screen, config):
        """
        Create a new renderer

        Args:
            screen (pygame.Surface): Main surface for display
            config (dict): Game config
        """
        self.screen = screen
        self.config = config
        self.logger = get_logger("tetris.renderer")

        # Store screen size
        self.width, self.height = screen.get_size()

        # Load theme
        self.theme = config["graphics"].get("theme", "denso")

        # Create effects
        self.bloom_effect = BloomEffect(
    threshold=100, blur_passes=2, intensity=0.8)
        self.shake_effect = ShakeEffect()

        # Try to load background image
        self.background = self._load_background()

        # High-speed background (for fast movement)
        self.high_speed_bg = self._create_high_speed_background()

        # Surfaces for effects
        self.overlay_surface = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        self.glow_surface = pygame.Surface(
    (self.width, self.height), pygame.SRCALPHA)

        # Load fonts with error handling
        self._load_fonts()

    def _load_background(self):
        """
        Load or create background based on theme

        Returns:
            pygame.Surface: Background surface
        """
        bg = pygame.Surface((self.width, self.height))
        bg.fill(BLACK)  # Default fallback

        try:
            # Try to load from file
            bg_path = os.path.join(
                "assets", "images", "backgrounds", f"{self.theme}_bg.png"
            )
            if os.path.exists(bg_path):
                self.logger.info(f"Loading background: {bg_path}")
                loaded_bg = pygame.image.load(bg_path)
                bg = pygame.transform.scale(
    loaded_bg, (self.width, self.height))
            else:
                self.logger.info(
                    f"Creating background for theme: {self.theme}")
                bg = self._create_background()
        except Exception as e:
            self.logger.error(f"Error loading background: {e}")
            # Use fallback background
            bg = self._create_background()

        return bg

    def _create_background(self):
        """
        Create background based on theme

        Returns:
            pygame.Surface: Created background
        """
        bg = pygame.Surface((self.width, self.height))

        try:
            if self.theme == "denso":
                # Create black background with DENSO red grid and neon dots
                bg.fill((10, 0, 5))  # Very dark red tint

                # Draw horizontal grid lines
                for y in range(0, self.height, 40):
                    line_color = (DENSO_RED[0], DENSO_RED[1], DENSO_RED[2], 30)
                    pygame.draw.line(
    bg, line_color, (0, y), (self.width, y), 1)

                # Draw vertical grid lines
                for x in range(0, self.width, 40):
                    line_color = (DENSO_RED[0], DENSO_RED[1], DENSO_RED[2], 30)
                    pygame.draw.line(
    bg, line_color, (x, 0), (x, self.height), 1)

                # Draw random neon dots
                for _ in range(100):
                    x = random.randint(0, self.width - 1)
                    y = random.randint(0, self.height - 1)
                    radius = random.randint(1, 3)
                    brightness = random.randint(50, 200)
                    color = (brightness, brightness // 4, brightness // 4)
                    pygame.gfxdraw.filled_circle(bg, x, y, radius, color)
                    # Add glow effect
                    pygame.gfxdraw.aacircle(
                        bg,
                        x,
                        y,
                        radius + 1,
                        (brightness // 2, brightness // 8, brightness // 8),
                    )

            elif self.theme == "retro":
                # Create retro background
                bg.fill((0, 0, 50))

                # Draw retro grid
                for y in range(0, self.height, 20):
                    color = (200, 50, 50) if y % 40 == 0 else (100, 50, 50)
                    pygame.draw.line(bg, color, (0, y), (self.width, y), 1)

                for x in range(0, self.width, 20):
                    color = (200, 50, 50) if x % 40 == 0 else (100, 50, 50)
                    pygame.draw.line(bg, color, (x, 0), (x, self.height), 1)

            elif self.theme == "minimalist":
                # Create minimalist background
                bg.fill((240, 240, 240))

                # Draw light random dots
                for _ in range(200):
                    x = random.randint(0, self.width - 1)
                    y = random.randint(0, self.height - 1)
                    radius = random.randint(1, 2)
                    color = (220, 220, 220)
                    pygame.gfxdraw.filled_circle(bg, x, y, radius, color)

            else:
                # Default theme (plain dark background)
                bg.fill((20, 20, 30))

                # Add subtle DENSO branding
                font = pygame.font.SysFont("Arial", 14)
                text = font.render("DENSO TETRIS", True, (40, 40, 50))
                bg.blit(
    text,
    (self.width -
    text.get_width() -
    10,
    self.height -
     30))

        except Exception as e:
            self.logger.error(f"Error creating background: {e}")
            bg.fill((0, 0, 0))  # Plain black as ultimate fallback

        return bg

    def _create_high_speed_background(self):
        """
        Create background effect for high speed (lines rushing down)

        Returns:
            pygame.Surface: High speed effect surface
        """
        try:
            surface = pygame.Surface(
    (self.width, self.height), pygame.SRCALPHA)
            surface.fill((0, 0, 0, 0))  # Transparent

            for _ in range(100):
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                length = random.randint(10, 50)
                color = (
                    DENSO_RED[0],
                    DENSO_RED[1],
                    DENSO_RED[2],
                    random.randint(20, 100),
                )

                pygame.draw.line(surface, color, (x, y), (x, y + length), 1)

            return surface

        except Exception as e:
            self.logger.error(f"Error creating high speed background: {e}")
            # Return an empty transparent surface
            return pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def _load_fonts(self):
        """Load fonts with error handling"""
        try:
            font_name = self.config["ui"].get("font", "arial")
            font_path = os.path.join("assets", "fonts", f"{font_name}.ttf")

            if os.path.exists(font_path):
                self.title_font = pygame.font.Font(font_path, 48)
                self.large_font = pygame.font.Font(font_path, 36)
                self.medium_font = pygame.font.Font(font_path, 24)
                self.small_font = pygame.font.Font(font_path, 18)
            else:
                # Use system font if file doesn't exist
                self.logger.warning(
                    f"Font file not found: {font_path}, using system font"
                )
                self.title_font = pygame.font.SysFont(font_name, 48)
                self.large_font = pygame.font.SysFont(font_name, 36)
                self.medium_font = pygame.font.SysFont(font_name, 24)
                self.small_font = pygame.font.SysFont(font_name, 18)

        except Exception as e:
            self.logger.error(f"Error loading fonts: {e}")
            # Use basic system font as fallback
            self.title_font = pygame.font.SysFont("Arial", 48)
            self.large_font = pygame.font.SysFont("Arial", 36)
            self.medium_font = pygame.font.SysFont("Arial", 24)
            self.small_font = pygame.font.SysFont("Arial", 18)

    def render_background(self, level=1):
            # สร้าง Surface เฉพาะเมื่อจำเป็น
            if not hasattr(self, '_cached_bg') or self._level_cache != level:
                self._level_cache = level
                self._cached_bg = self._create_background_for_level(level)

            # ใช้ Surface ที่แคชไว้
            self.screen.blit(self._cached_bg, (0, 0))
            # Draw high-speed background effect if level is high enough
            if level > 10 and self.config["graphics"].get("animations", True):
                speed_alpha = min(255, (level - 10) * 25)
                high_speed_copy = self.high_speed_bg.copy()

                # Set alpha with error handling
                try:
                    high_speed_copy.set_alpha(speed_alpha)
                except:
                    pass  # Ignore alpha errors

                self.screen.blit(high_speed_copy, (0, 0))

        except Exception as e:
            self.logger.error(f"Error rendering background: {e}")
            # Fallback to plain color
            self.screen.fill((0, 0, 0))

    def render_pause_overlay(self):
        """Draw overlay effect when game is paused"""
        try:
            # Draw transparent black background
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))

            # Draw "PAUSED" text
            text = self.large_font.render("PAUSED", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 40))
            self.screen.blit(text, text_rect)

            # Draw hint
            hint = self.medium_font.render(
                "Press ESC or P to resume", True, (200, 200, 200)
            )
            hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 20))
            self.screen.blit(hint, hint_rect)

        except Exception as e:
            self.logger.error(f"Error rendering pause overlay: {e}")
            # Simplified fallback
            try:
                pygame.draw.rect(
                    self.screen, (0, 0, 0, 128), (0, 0, self.width, self.height)
                )

                text = pygame.font.SysFont("Arial", 36).render(
                    "PAUSED", True, (255, 255, 255)
                )
                self.screen.blit(
                    text, (self.width // 2 - text.get_width() // 2, self.height // 2)
                )
            except:
                pass  # Last resort

    def render_game_over(self, score, level, lines):
        """
        Draw game over screen

        Args:
            score (int): Final score
            level (int): Final level
            lines (int): Number of lines cleared
        """
        try:
            # Draw semi-transparent black background
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))  # More opaque black
            self.screen.blit(overlay, (0, 0))

            # Draw "GAME OVER" text
            text = self.title_font.render("GAME OVER", True, DENSO_RED)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 3 - 40))
            self.screen.blit(text, text_rect)

            # Draw score
            score_text = self.large_font.render(
                f"Score: {score}", True, (255, 255, 255)
            )
            score_rect = score_text.get_rect(
                center=(self.width // 2, self.height // 2 - 40)
            )
            self.screen.blit(score_text, score_rect)

            # Draw level and lines cleared
            level_text = self.medium_font.render(
                f"Level: {level}", True, (200, 200, 200)
            )
            level_rect = level_text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(level_text, level_rect)

            lines_text = self.medium_font.render(
                f"Lines Cleared: {lines}", True, (200, 200, 200)
            )
            lines_rect = lines_text.get_rect(
                center=(self.width // 2, self.height // 2 + 30)
            )
            self.screen.blit(lines_text, lines_rect)

            # Draw hint
            hint = self.medium_font.render(
                "Press Enter to return to main menu", True, (200, 200, 200)
            )
            hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 100))
            self.screen.blit(hint, hint_rect)

        except Exception as e:
            self.logger.error(f"Error rendering game over: {e}")
            # Simplified fallback
            try:
                self.screen.fill((0, 0, 0))
                text = pygame.font.SysFont("Arial", 36).render(
                    "GAME OVER", True, (255, 0, 0)
                )
                self.screen.blit(
                    text,
                    (self.width // 2 - text.get_width() // 2, self.height // 2 - 50),
                )
                score_text = pygame.font.SysFont("Arial", 24).render(
                    f"Score: {score}", True, (255, 255, 255)
                )
                self.screen.blit(
                    score_text,
                    (self.width // 2 - score_text.get_width() // 2, self.height // 2),
                )
            except:
                pass  # Last resort

    def apply_bloom(self, surface):
        """
        Apply Bloom effect to surface if enabled

        Args:
            surface (pygame.Surface): Surface to apply effect to
        """
        if not self.config["graphics"].get("bloom_effect", True):
            return

        try:
            bloomed_surface = self.bloom_effect.apply(surface)
            self.screen.blit(bloomed_surface, (0, 0))
        except Exception as e:
            self.logger.error(f"Error applying bloom effect: {e}")
            # If bloom fails, just keep the original surface

    def apply_shake(self, duration=0.3, intensity=5):
        """
        Start shake effect if enabled

        Args:
            duration (float): Duration of shake
            intensity (float): Intensity of shake
        """
        if not self.config["graphics"].get("shake_effect", True):
            return

        try:
            self.shake_effect.start(intensity, duration)
        except Exception as e:
            self.logger.error(f"Error starting shake effect: {e}")

    def update_effects(self, dt):
        """
        Update all effects

        Args:
            dt (float): Time passed since last update

        Returns:
            tuple: Screen movement offset from effects
        """
        try:
            # Update shake effect
            return self.shake_effect.update(dt)
        except Exception as e:
            self.logger.error(f"Error updating effects: {e}")
            return (0, 0)  # No offset

    def render_loading_screen(self, progress=0):
        """
        Draw loading screen

        Args:
            progress (float): Loading progress (0-1)
        """
        try:
            # Clear screen
            self.screen.fill(BLACK)

            # Draw "LOADING" text
            text = self.large_font.render("LOADING...", True, WHITE)
            text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 50))
            self.screen.blit(text, text_rect)

            # Draw progress bar
            bar_width = self.width * 0.6
            bar_height = 20
            bar_x = (self.width - bar_width) // 2
            bar_y = self.height // 2

            # Border
            pygame.draw.rect(
                self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2
            )

            # Progress
            progress_width = bar_width * progress
            pygame.draw.rect(
                self.screen, DENSO_RED, (bar_x, bar_y, progress_width, bar_height)
            )

            # Update screen
            pygame.display.flip()

        except Exception as e:
            self.logger.error(f"Error rendering loading screen: {e}")
            # Simplified fallback
            try:
                self.screen.fill((0, 0, 0))
                text = pygame.font.SysFont("Arial", 24).render(
                    "LOADING...", True, (255, 255, 255)
                )
                self.screen.blit(
                    text, (self.width // 2 - text.get_width() // 2, self.height // 2)
                )
                pygame.display.flip()
            except:
                pass  # Last resort

    def render_text_with_outline(
        self, text, font, color, outline_color, position, outline_width=2
    ):
        """
        Draw text with outline

        Args:
            text (str): Text to draw
            font (pygame.font.Font): Font
            color (tuple): Text color (RGB)
            outline_color (tuple): Outline color (RGB)
            position (tuple): Position (x, y)
            outline_width (int): Outline thickness
        """
        try:
            # Draw outline
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        outline = font.render(text, True, outline_color)
                        self.screen.blit(outline, (position[0] + dx, position[1] + dy))

            # Draw main text
            main_text = font.render(text, True, color)
            self.screen.blit(main_text, position)

        except Exception as e:
            self.logger.error(f"Error rendering text with outline: {e}")
            # Simplified fallback
            try:
                text_surface = font.render(text, True, color)
                self.screen.blit(text_surface, position)
            except:
                pass  # Last resort

    def render_button(
        self,
        rect,
        text,
        font,
        color=(255, 255, 255),
        bg_color=DENSO_RED,
        highlight=False,
    ):
        """
        Draw a button

        Args:
            rect (pygame.Rect): Button boundaries
            text (str): Button text
            font (pygame.font.Font): Font
            color (tuple): Text color (RGB)
            bg_color (tuple): Background color (RGB)
            highlight (bool): Highlight or not

        Returns:
            pygame.Rect: Button boundaries
        """
        try:
            # Draw button background
            if highlight:
                # Highlight color
                pygame.draw.rect(
                    self.screen,
                    (
                        min(255, bg_color[0] + 50),
                        min(255, bg_color[1] + 50),
                        min(255, bg_color[2] + 50),
                    ),
                    rect,
                )
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
            else:
                pygame.draw.rect(self.screen, bg_color, rect)
                pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)

            # Draw text
            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)

            return rect

        except Exception as e:
            self.logger.error(f"Error rendering button: {e}")
            # Simplified fallback
            try:
                pygame.draw.rect(self.screen, bg_color, rect)
                text_surf = font.render(text, True, color)
                text_rect = text_surf.get_rect(center=rect.center)
                self.screen.blit(text_surf, text_rect)
                return rect
            except:
                return rect  # Last resort
