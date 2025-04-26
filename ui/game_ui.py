#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Game UI
---------------------
Class for in-game user interface
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
import math
import time

from core.constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BOARD_X,
    BOARD_Y,
    BOARD_WIDTH,
    BOARD_HEIGHT,
    GRID_SIZE,
    WHITE,
    BLACK,
    GRAY,
    DENSO_RED,
    DENSO_DARK_RED,
    DENSO_LIGHT_RED,
)


class GameUI:
    """Class for in-game user interface"""

    def __init__(self, screen, config):
        """
        Create a new user interface

        Args:
            screen (pygame.Surface): Main surface for display
            config (dict): Game configuration
        """
        self.screen = screen
        self.config = config

        # Import fonts
        pygame.font.init()
        try:
            self.large_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 36
            )
            self.medium_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 24
            )
            self.small_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 18
            )
        except:
            # Use system fonts if loading fails
            self.large_font = pygame.font.SysFont("Arial", 36)
            self.medium_font = pygame.font.SysFont("Arial", 24)
            self.small_font = pygame.font.SysFont("Arial", 18)

        # UI area positions
        board_right = BOARD_X + BOARD_WIDTH * GRID_SIZE
        self.hold_area = {"x": BOARD_X - 150, "y": BOARD_Y, "width": 120, "height": 120}
        self.next_area = {
            "x": board_right + 30,
            "y": BOARD_Y,
            "width": 120,
            "height": 300,
        }
        self.score_area = {
            "x": BOARD_X - 150,
            "y": BOARD_Y + 150,
            "width": 120,
            "height": 300,
        }

        # Create surface for HUD
        self.hud_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
        )

        # Animation timer
        self.animation_timer = 0

    def render(self, data):
        """
        Draw user interface

        Args:
            data (dict): Game data (score, level, etc.)
        """
        # Clear HUD surface
        self.hud_surface.fill((0, 0, 0, 0))

        # Draw Hold area
        self._render_hold_area(data["hold_tetromino"], data["can_hold"])

        # Draw Next area
        self._render_next_area(data["next_tetrominos"])

        # Draw Score area
        self._render_score_area(data["score"], data["level"], data["lines"])

        # Show FPS if enabled
        if self.config["ui"]["show_fps"]:
            fps = int(1.0 / max(0.001, pygame.time.Clock().get_time() / 1000))
            fps_text = self.small_font.render(f"FPS: {fps}", True, WHITE)
            self.hud_surface.blit(fps_text, (10, 10))

        # Show player name and time
        self._render_player_info(data["username"], data["time"])

        # Draw HUD on main screen
        self.screen.blit(self.hud_surface, (0, 0))

    def _render_hold_area(self, hold_tetromino, can_hold):
        """
        Draw Hold area

        Args:
            hold_tetromino (Tetromino): Held block
            can_hold (bool): Whether holding is available
        """
        area = self.hold_area

        # Draw frame
        pygame.draw.rect(
            self.hud_surface,
            (40, 40, 60),
            (area["x"], area["y"], area["width"], area["height"]),
        )
        pygame.draw.rect(
            self.hud_surface,
            DENSO_RED,
            (area["x"], area["y"], area["width"], area["height"]),
            2,
        )

        # Draw title
        hold_text = self.medium_font.render("HOLD", True, WHITE)
        hold_rect = hold_text.get_rect(
            center=(area["x"] + area["width"] // 2, area["y"] - 20)
        )
        self.hud_surface.blit(hold_text, hold_rect)

        # Draw held block
        if hold_tetromino:
            # Calculate block position (center of area)
            shape = hold_tetromino.shape[0]  # Use default rotation
            width = max(x for x, y in shape) - min(x for x, y in shape) + 1
            height = max(y for x, y in shape) - min(y for x, y in shape) + 1

            cell_size = min(area["width"] / (width + 2), area["height"] / (height + 2))

            # Starting position
            start_x = area["x"] + (area["width"] - width * cell_size) / 2
            start_y = area["y"] + (area["height"] - height * cell_size) / 2

            # Draw each cell of the block
            for block_x, block_y in shape:
                rect = pygame.Rect(
                    start_x + block_x * cell_size,
                    start_y + block_y * cell_size,
                    cell_size,
                    cell_size,
                )

                # If can't hold, show as gray
                color = hold_tetromino.color if can_hold else GRAY

                pygame.draw.rect(self.hud_surface, color, rect)
                pygame.draw.rect(self.hud_surface, WHITE, rect, 1)

    def _render_next_area(self, next_tetrominos):
        """
        Draw Next block area

        Args:
            next_tetrominos (list): List of next tetrominos
        """
        area = self.next_area

        # Draw frame
        pygame.draw.rect(
            self.hud_surface,
            (40, 40, 60),
            (area["x"], area["y"], area["width"], area["height"]),
        )
        pygame.draw.rect(
            self.hud_surface,
            DENSO_RED,
            (area["x"], area["y"], area["width"], area["height"]),
            2,
        )

        # Draw title
        next_text = self.medium_font.render("NEXT", True, WHITE)
        next_rect = next_text.get_rect(
            center=(area["x"] + area["width"] // 2, area["y"] - 20)
        )
        self.hud_surface.blit(next_text, next_rect)

        # Draw next blocks
        preview_count = min(
            len(next_tetrominos), self.config["tetromino"]["preview_count"]
        )

        for i in range(preview_count):
            tetromino = next_tetrominos[i]

            # Calculate block position
            shape = tetromino.shape[0]  # Use default rotation
            width = max(x for x, y in shape) - min(x for x, y in shape) + 1
            height = max(y for x, y in shape) - min(y for x, y in shape) + 1

            cell_size = min(area["width"] / (width + 2), 50)

            # Starting position
            start_x = area["x"] + (area["width"] - width * cell_size) / 2
            start_y = area["y"] + 20 + i * 60

            # Draw each cell of the block
            for block_x, block_y in shape:
                rect = pygame.Rect(
                    start_x + block_x * cell_size,
                    start_y + block_y * cell_size,
                    cell_size,
                    cell_size,
                )

                pygame.draw.rect(self.hud_surface, tetromino.color, rect)
                pygame.draw.rect(self.hud_surface, WHITE, rect, 1)

    def _render_score_area(self, score, level, lines):
        """
        Draw score area

        Args:
            score (int): Current score
            level (int): Current level
            lines (int): Number of lines cleared
        """
        area = self.score_area

        # Draw frame
        pygame.draw.rect(
            self.hud_surface,
            (40, 40, 60),
            (area["x"], area["y"], area["width"], area["height"]),
        )
        pygame.draw.rect(
            self.hud_surface,
            DENSO_RED,
            (area["x"], area["y"], area["width"], area["height"]),
            2,
        )

        # Draw title
        score_text = self.medium_font.render("STATS", True, WHITE)
        score_rect = score_text.get_rect(
            center=(area["x"] + area["width"] // 2, area["y"] - 20)
        )
        self.hud_surface.blit(score_text, score_rect)

        # Draw score
        y_pos = area["y"] + 20

        score_label = self.small_font.render("Score:", True, WHITE)
        self.hud_surface.blit(score_label, (area["x"] + 10, y_pos))

        score_value = self.medium_font.render(f"{score:,}", True, (255, 255, 0))
        self.hud_surface.blit(score_value, (area["x"] + 10, y_pos + 25))

        # Draw level
        y_pos += 70

        level_label = self.small_font.render("Level:", True, WHITE)
        self.hud_surface.blit(level_label, (area["x"] + 10, y_pos))

        level_value = self.medium_font.render(f"{level}", True, (0, 255, 255))
        self.hud_surface.blit(level_value, (area["x"] + 10, y_pos + 25))

        # Draw lines cleared
        y_pos += 70

        lines_label = self.small_font.render("Lines:", True, WHITE)
        self.hud_surface.blit(lines_label, (area["x"] + 10, y_pos))

        lines_value = self.medium_font.render(f"{lines}", True, (0, 255, 0))
        self.hud_surface.blit(lines_value, (area["x"] + 10, y_pos + 25))

        # Draw level progress bar
        y_pos += 70

        progress_label = self.small_font.render("Next Level:", True, WHITE)
        self.hud_surface.blit(progress_label, (area["x"] + 10, y_pos))

        # Calculate progress
        level_up_lines = self.config["game"]["level_up_lines"]
        progress = (lines % level_up_lines) / level_up_lines

        # Draw progress bar
        bar_width = area["width"] - 20
        bar_height = 15
        bar_x = area["x"] + 10
        bar_y = y_pos + 25

        # Border
        pygame.draw.rect(
            self.hud_surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 1
        )

        # Progress
        progress_width = bar_width * progress
        pygame.draw.rect(
            self.hud_surface, DENSO_RED, (bar_x, bar_y, progress_width, bar_height)
        )

    def _render_player_info(self, username, game_time):
        """
        Draw player info and time

        Args:
            username (str): Player name
            game_time (float): Play time (seconds)
        """
        # Draw player name
        player_text = self.small_font.render(f"Player: {username}", True, WHITE)
        self.hud_surface.blit(player_text, (10, SCREEN_HEIGHT - 30))

        # Convert time to mm:ss format
        minutes = int(game_time) // 60
        seconds = int(game_time) % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        # Draw time
        time_text = self.small_font.render(f"Time: {time_str}", True, WHITE)
        time_rect = time_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
        self.hud_surface.blit(time_text, time_rect)

        # Draw copyright
        copyright_text = self.small_font.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, (150, 150, 150)
        )
        copyright_rect = copyright_text.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 5)
        )
        self.hud_surface.blit(copyright_text, copyright_rect)
