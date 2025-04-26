#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Graphics Renderer
------------------------------
Class for handling game rendering with modern effects
"""

import pygame
import math
from core.constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DENSO_RED,
    WHITE,
    BLACK,
    UI_BG,
    UI_TEXT,
    UI_HIGHLIGHT,
)
from graphics.effects import BloomEffect


class Renderer:
    """Handle game rendering and special effects"""

    def __init__(self, screen, config):
        """
        Initialize renderer

        Args:
            screen (pygame.Surface): Main display surface
            config (dict): Game configuration
        """
        self.screen = screen
        self.config = config
        self.bloom = BloomEffect() if config["graphics"]["bloom_effect"] else None

        # Load fonts
        pygame.font.init()
        try:
            self.large_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 48
            )
            self.medium_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 32
            )
        except:
            self.large_font = pygame.font.SysFont("Arial", 48)
            self.medium_font = pygame.font.SysFont("Arial", 32)

    def render_background(self, level):
        """
        Render game background with subtle effects

        Args:
            level (int): Current game level for color effects
        """
        # Create gradient background
        for y in range(SCREEN_HEIGHT):
            # Calculate color based on y position
            factor = 1 - (y / SCREEN_HEIGHT)
            r = int(UI_BG[0] + factor * 15)
            g = int(UI_BG[1] + factor * 10)
            b = int(max(5, UI_BG[2] - factor * 10))
            color = (r, g, b)

            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))

    def render_pause_overlay(self):
        """Render pause screen overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        # Draw "PAUSED" text
        text = self.large_font.render("PAUSED", True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

    def render_game_over(self, score, level, lines):
        """
        Render game over screen

        Args:
            score (int): Final score
            level (int): Final level
            lines (int): Total lines cleared
        """
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Draw game over text
        y_pos = SCREEN_HEIGHT // 2 - 100
        self._render_centered_text("GAME OVER", self.large_font, DENSO_RED, y_pos)

        # Draw stats
        y_pos += 80
        self._render_centered_text(f"Score: {score:,}", self.medium_font, WHITE, y_pos)
        y_pos += 50
        self._render_centered_text(f"Level: {level}", self.medium_font, WHITE, y_pos)
        y_pos += 50
        self._render_centered_text(f"Lines: {lines}", self.medium_font, WHITE, y_pos)

        # Draw continue text
        y_pos += 80
        text = self.medium_font.render("Press ENTER to continue", True, UI_TEXT)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        self.screen.blit(text, text_rect)

    def render_victory(self, score, level, lines):
        """
        Render victory screen

        Args:
            score (int): Final score
            level (int): Final level
            lines (int): Total lines cleared
        """
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Draw victory text with glow effect
        y_pos = SCREEN_HEIGHT // 2 - 100
        text = "VICTORY!"
        glow_surf = self._create_text_glow(text, self.large_font, UI_HIGHLIGHT)
        self.screen.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        self._render_centered_text(text, self.large_font, WHITE, y_pos)

        # Draw stats
        y_pos += 80
        self._render_centered_text(f"Score: {score:,}", self.medium_font, WHITE, y_pos)
        y_pos += 50
        self._render_centered_text(f"Level: {level}", self.medium_font, WHITE, y_pos)
        y_pos += 50
        self._render_centered_text(f"Lines: {lines}", self.medium_font, WHITE, y_pos)

    def apply_bloom(self, surface):
        """
        Apply bloom effect to surface if enabled

        Args:
            surface (pygame.Surface): Surface to apply effect to
        """
        if self.bloom and self.config["graphics"]["bloom_effect"]:
            return self.bloom.apply(surface)
        return surface

    def _render_centered_text(self, text, font, color, y_pos):
        """Helper to render centered text"""
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        self.screen.blit(text_surf, text_rect)

    def _create_text_glow(self, text, font, color):
        """Create glow effect for text"""
        text_surf = font.render(text, True, color)
        glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        for offset in range(1, 10):
            alpha = max(0, 255 - (offset * 25))
            glow_color = (*color, alpha)
            glow_surf = font.render(text, True, glow_color)
            for dx, dy in [(0, offset), (0, -offset), (offset, 0), (-offset, 0)]:
                rect = text_rect.copy()
                rect.x += dx
                rect.y += dy
                glow.blit(glow_surf, rect)

        return glow
