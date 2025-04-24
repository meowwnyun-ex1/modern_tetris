#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Renderer
----------------------
Class for rendering all graphics
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
    DENSO_RED,
    DENSO_DARK_RED,
    DENSO_LIGHT_RED,
)
from graphics.effects import BloomEffect, ShakeEffect


class Renderer:
    """Class for graphics rendering"""

    def __init__(self, screen, config):
        """
        Create a new renderer

        Args:
            screen (pygame.Surface): Main surface for display
            config (dict): Game config
        """
        self.screen = screen
        self.config = config

        # Store screen size
        self.width, self.height = screen.get_size()

        # Load theme
        self.theme = config["graphics"]["theme"]

        # Create effects
        self.bloom_effect = BloomEffect(threshold=100, blur_passes=2, intensity=0.8)
        self.shake_effect = ShakeEffect()

        # Load background image
        try:
            self.background = pygame.image.load(
                f"assets/images/backgrounds/{self.theme}_bg.png"
            )
            self.background = pygame.transform.scale(
                self.background, (self.width, self.height)
            )
        except:
            # Create our own background
            self.background = self._create_background()

        # High-speed background (for fast movement)
        self.high_speed_bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._create_high_speed_background()

        # Surfaces for effects
        self.overlay_surface = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        self.glow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Load fonts
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
            # Use system font if loading fails
            self.title_font = pygame.font.SysFont("Arial", 48)
            self.large_font = pygame.font.SysFont("Arial", 36)
            self.medium_font = pygame.font.SysFont("Arial", 24)
            self.small_font = pygame.font.SysFont("Arial", 18)

    def _create_background(self):
        """
        Create game background based on theme

        Returns:
            pygame.Surface: Created background
        """
        bg = pygame.Surface((self.width, self.height))

        if self.theme == "denso":
            # Create black background with DENSO red grid and neon dots
            bg.fill((10, 0, 5))  # Very dark red tint

            # Draw horizontal grid lines
            for y in range(0, self.height, 40):
                line_color = (DENSO_RED[0], DENSO_RED[1], DENSO_RED[2], 30)
                pygame.draw.line(bg, line_color, (0, y), (self.width, y), 1)

            # Draw vertical grid lines
            for x in range(0, self.width, 40):
                line_color = (DENSO_RED[0], DENSO_RED[1], DENSO_RED[2], 30)
                pygame.draw.line(bg, line_color, (x, 0), (x, self.height), 1)

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
            # Default theme (plain black)
            bg.fill(BLACK)

        return bg

    def _create_high_speed_background(self):
        """Create background for high speed (lines rushing down)"""
        self.high_speed_bg.fill((0, 0, 0, 0))  # Transparent

        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            length = random.randint(10, 50)
            color = (DENSO_RED[0], DENSO_RED[1], DENSO_RED[2], random.randint(20, 100))

            pygame.draw.line(self.high_speed_bg, color, (x, y), (x, y + length), 1)

    def render_background(self, level=1):
        """
        Draw background

        Args:
            level (int, optional): Game speed level
        """
        # Draw main background
        self.screen.blit(self.background, (0, 0))

        # Draw high-speed background effect if level is high enough
        if level > 10:
            speed_alpha = min(255, (level - 10) * 25)
            high_speed_copy = self.high_speed_bg.copy()
            high_speed_copy.set_alpha(speed_alpha)
            self.screen.blit(high_speed_copy, (0, 0))

    def render_pause_overlay(self):
        """Draw overlay effect when game is paused"""
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

    def render_game_over(self, score, level, lines):
        """
        Draw game over screen

        Args:
            score (int): Final score
            level (int): Final level
            lines (int): Number of lines cleared
        """
        # Draw semi-transparent black background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # More opaque black
        self.screen.blit(overlay, (0, 0))

        # Draw "GAME OVER" text
        text = self.title_font.render("GAME OVER", True, DENSO_RED)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(text, text_rect)

        # Draw score
        score_text = self.large_font.render(f"Score: {score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(
            center=(self.width // 2, self.height // 2 - 40)
        )
        self.screen.blit(score_text, score_rect)

        # Draw level and lines cleared
        level_text = self.medium_font.render(f"Level: {level}", True, (200, 200, 200))
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

    def apply_bloom(self, surface):
        """
        Apply Bloom effect to surface

        Args:
            surface (pygame.Surface): Surface to apply effect to
        """
        if self.config["graphics"]["bloom_effect"]:
            bloomed_surface = self.bloom_effect.apply(surface)
            self.screen.blit(bloomed_surface, (0, 0))

    def apply_shake(self, duration=0.3, intensity=5):
        """
        Start shake effect

        Args:
            duration (float): Duration of shake (seconds)
            intensity (float): Intensity of shake (pixels)
        """
        if self.config["graphics"]["shake_effect"]:
            self.shake_effect.start(intensity, duration)

    def update_effects(self, dt):
        """
        Update all effects

        Args:
            dt (float): Time passed since last update (seconds)

        Returns:
            tuple: (offset_x, offset_y) Screen movement from shake effect
        """
        # Update shake effect
        return self.shake_effect.update(dt)

    def render_loading_screen(self, progress=0):
        """
        Draw loading screen

        Args:
            progress (float): Loading progress (0-1)
        """
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
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # Progress
        progress_width = bar_width * progress
        pygame.draw.rect(
            self.screen, DENSO_RED, (bar_x, bar_y, progress_width, bar_height)
        )

        # Update screen
        pygame.display.flip()

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
        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    outline = font.render(text, True, outline_color)
                    self.screen.blit(outline, (position[0] + dx, position[1] + dy))

        # Draw main text
        main_text = font.render(text, True, color)
        self.screen.blit(main_text, position)

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
