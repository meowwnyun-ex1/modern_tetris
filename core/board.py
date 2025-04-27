#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Board Class
--------------------------
This class handles the game board and interactions with tetrominos
"""

import logging
from utils.logger import get_logger

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

from core.constants import (
    BOARD_WIDTH,
    BOARD_HEIGHT,
    GRID_SIZE,
    BOARD_X,
    BOARD_Y,
    TETROMINO_COLORS,
    BLACK,
    DARK_GRAY,
    WHITE,
    GRAY,
    LINE_CLEAR_DELAY,
    SCORE_SINGLE,
    SCORE_DOUBLE,
    SCORE_TRIPLE,
    SCORE_TETRIS,
    SCORE_T_SPIN,
)


class Board:
    """Class for Tetris game board"""

    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT, config=None):
        """
        Create a new game board

        Args:
            width (int, optional): Board width in cells
            height (int, optional): Board height in cells
            config (dict, optional): Game configuration
        """
        self.width = width
        self.height = height
        self.x = BOARD_X
        self.y = BOARD_Y
        self.config = config or {}
        self.logger = get_logger("tetris.board")

        # Create empty grid
        self.reset_grid()

        # Create surfaces for drawing
        self.create_surfaces()

        # Line clearing effect states
        self.clearing_lines = []
        self.clearing_timer = 0
        self.clearing_effect = 0  # For animation effects

        # Pre-draw grid lines for performance
        self._draw_grid()

        # Create board border
        self._draw_border()

    def create_surfaces(self):
        """Create rendering surfaces with error handling"""
        try:
            # Main board surface
            self.board_surface = pygame.Surface(
                (self.width * GRID_SIZE, self.height * GRID_SIZE), pygame.SRCALPHA
            )

            # Border surface
            self.border_surface = pygame.Surface(
                ((self.width + 2) * GRID_SIZE, (self.height + 2) * GRID_SIZE),
                pygame.SRCALPHA,
            )

            # Grid lines surface
            self.grid_surface = pygame.Surface(
                (self.width * GRID_SIZE, self.height * GRID_SIZE), pygame.SRCALPHA
            )

            # Glow effect surface
            self.glow_surface = pygame.Surface(
                (self.width * GRID_SIZE, self.height * GRID_SIZE), pygame.SRCALPHA
            )

        except pygame.error as e:
            self.logger.error(f"Error creating board surfaces: {e}")
            # Create minimal surfaces to prevent crashes
            self.board_surface = pygame.Surface((1, 1))
            self.border_surface = pygame.Surface((1, 1))
            self.grid_surface = pygame.Surface((1, 1))
            self.glow_surface = pygame.Surface((1, 1))

    def reset_grid(self):
        """Reset the game grid to empty"""
        # Create a 2D grid (height x width) initialized with None
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]

    def _draw_grid(self):
        """Draw grid lines on grid_surface"""
        self.grid_surface.fill((0, 0, 0, 0))  # Transparent

        # Draw horizontal lines
        for y in range(self.height + 1):
            pygame.draw.line(
                self.grid_surface,
                GRAY,
                (0, y * GRID_SIZE),
                (self.width * GRID_SIZE, y * GRID_SIZE),
                1,
            )

        # Draw vertical lines
        for x in range(self.width + 1):
            pygame.draw.line(
                self.grid_surface,
                GRAY,
                (x * GRID_SIZE, 0),
                (x * GRID_SIZE, self.height * GRID_SIZE),
                1,
            )

    def _draw_border(self):
        """Draw board border on border_surface"""
        self.border_surface.fill(DARK_GRAY)

        # Draw inner area (game area)
        inner_rect = pygame.Rect(
            GRID_SIZE, GRID_SIZE, self.width * GRID_SIZE, self.height * GRID_SIZE
        )
        pygame.draw.rect(self.border_surface, BLACK, inner_rect)

        # Draw white border lines
        pygame.draw.rect(self.border_surface, WHITE, inner_rect, 2)

    def update(self, dt):
        """
        Update board state

        Args:
            dt (float): Time delta in seconds

        Returns:
            dict: Update data (score, lines cleared, etc.)
        """
        result = {
            "lines_cleared": 0,
            "score": 0,
            "tetris": False,
            "t_spin": False,
            "level_up": False,
            "clearing_complete": False,
        }

        # If currently clearing lines
        if self.clearing_lines:
            self.clearing_timer += dt * 1000  # Convert to milliseconds
            self.clearing_effect = min(1.0, self.clearing_timer / LINE_CLEAR_DELAY)

            # When effect time is complete, actually clear the lines
            if self.clearing_timer >= LINE_CLEAR_DELAY:
                lines_count = len(self.clearing_lines)

                # Calculate score
                if lines_count == 1:
                    result["score"] = SCORE_SINGLE
                elif lines_count == 2:
                    result["score"] = SCORE_DOUBLE
                elif lines_count == 3:
                    result["score"] = SCORE_TRIPLE
                elif lines_count == 4:
                    result["score"] = SCORE_TETRIS
                    result["tetris"] = True

                # Remove the marked lines
                for line in sorted(self.clearing_lines):
                    # Remove the marked line
                    self.grid.pop(line)
                    # Add empty line at top
                    self.grid.insert(0, [None for _ in range(self.width)])

                # Update return values
                result["lines_cleared"] = lines_count
                result["clearing_complete"] = True

                # Reset line clearing state
                self.clearing_lines = []
                self.clearing_timer = 0
                self.clearing_effect = 0

        return result

    def check_collision(self, tetromino, x, y):
        """
        Check collision between tetromino and board

        Args:
            tetromino (Tetromino): Tetromino to check
            x (int): X position to check
            y (int): Y position to check

        Returns:
            bool: True if collision, False otherwise
        """
        # Check each cell of the tetromino
        for block_x, block_y in tetromino.shape[tetromino.rotation]:
            grid_x = x + block_x
            grid_y = y + block_y

            # Check board boundaries including top
            if grid_x < 0 or grid_x >= self.width or grid_y >= self.height:
                return True

            # Only check collision with other blocks if within board
            if grid_y >= 0:
                if self.grid[grid_y][grid_x] is not None:
                    return True

        return False

    def lock_tetromino(self, tetromino):
        """
        Lock a tetromino onto the board

        Args:
            tetromino (Tetromino): Tetromino to lock

        Returns:
            bool: True if locked successfully, False if game over
        """
        # Place blocks on the grid
        for block_x, block_y in tetromino.shape[tetromino.rotation]:
            grid_x = tetromino.x + block_x
            grid_y = tetromino.y + block_y

            # Check if block is on the board
            if grid_y < 0:
                return False  # Game over (block above board)

            # Store block color in grid
            self.grid[grid_y][grid_x] = tetromino.color

        # Check for complete lines
        self.check_lines()

        return True

    def check_lines(self):
        """
        Check for completed lines and mark them for clearing

        Returns:
            list: List of lines to be cleared
        """
        self.clearing_lines = []

        # Check each row from bottom to top
        for y in range(self.height - 1, -1, -1):
            if all(self.grid[y][x] is not None for x in range(self.width)):
                self.clearing_lines.append(y)

        return self.clearing_lines

    def is_game_over(self):
        """
        Check if game is over (blocks in top rows)

        Returns:
            bool: True if game over, False if game still running
        """
        # Check top rows (first 2 rows - sometimes blocks may extend above top edge)
        for y in range(2):
            for x in range(self.width):
                if self.grid[y][x] is not None:
                    return True
        return False

    def render(self, surface):
        """
        Render the board

        Args:
            surface (pygame.Surface): Surface to render on
        """
        try:
            # Draw border
            surface.blit(self.border_surface, (self.x - GRID_SIZE, self.y - GRID_SIZE))

            # Reset surfaces
            self.board_surface.fill(BLACK)
            self.glow_surface.fill((0, 0, 0, 0))

            # Draw grid
            self.board_surface.blit(self.grid_surface, (0, 0))

            # Draw locked blocks
            for y in range(self.height):
                for x in range(self.width):
                    color = self.grid[y][x]
                    if color:
                        # Draw block
                        rect = pygame.Rect(
                            x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE
                        )
                        pygame.draw.rect(self.board_surface, color, rect)
                        pygame.draw.rect(self.board_surface, WHITE, rect, 1)

                        # Draw glow effect if enabled
                        if self.config.get("graphics", {}).get("bloom_effect", True):
                            glow_color = (*color, 64)  # Add alpha
                            center = (
                                x * GRID_SIZE + GRID_SIZE // 2,
                                y * GRID_SIZE + GRID_SIZE // 2,
                            )
                            pygame.draw.circle(
                                self.glow_surface, glow_color, center, GRID_SIZE - 5
                            )

            # Draw line clear effect
            if self.clearing_lines and self.clearing_effect > 0:
                self._render_line_clear_effect()

            # Blit surfaces
            surface.blit(self.board_surface, (self.x, self.y))
            surface.blit(
                self.glow_surface, (self.x, self.y), special_flags=pygame.BLEND_ADD
            )
        except Exception as e:
            self.logger.error(f"Error rendering board: {e}")

    def _render_line_clear_effect(self):
        """Render line clearing effect animation"""
        try:
            # Draw white flash on cleared lines
            flash_alpha = int(255 * (1.0 - self.clearing_effect))

            for line in self.clearing_lines:
                flash_rect = pygame.Rect(
                    0, line * GRID_SIZE, self.width * GRID_SIZE, GRID_SIZE
                )
                flash_surface = pygame.Surface(
                    (flash_rect.width, flash_rect.height), pygame.SRCALPHA
                )
                flash_surface.fill((255, 255, 255, flash_alpha))
                self.board_surface.blit(flash_surface, flash_rect)

                # Add glow effect
                glow_color = (255, 255, 255, flash_alpha // 2)
                for x in range(self.width):
                    center = (
                        x * GRID_SIZE + GRID_SIZE // 2,
                        line * GRID_SIZE + GRID_SIZE // 2,
                    )
                    pygame.draw.circle(self.glow_surface, glow_color, center, GRID_SIZE)
        except Exception as e:
            self.logger.error(f"Error rendering line clear effect: {e}")

    def render_ghost(self, surface, tetromino, ghost_y):
        """
        Render ghost tetromino (shadow)

        Args:
            surface (pygame.Surface): Surface to render on
            tetromino (Tetromino): Tetromino to render shadow for
            ghost_y (int): Y position of ghost
        """
        try:
            # Calculate screen position
            screen_x = self.x + tetromino.x * GRID_SIZE
            screen_y = self.y + ghost_y * GRID_SIZE

            # Draw ghost blocks
            tetromino.render_ghost(surface, screen_x, screen_y)
        except Exception as e:
            self.logger.error(f"Error rendering ghost: {e}")

    def render_tetromino(self, surface, tetromino):
        """
        Render current tetromino

        Args:
            surface (pygame.Surface): Surface to render on
            tetromino (Tetromino): Tetromino to render
        """
        try:
            # Calculate screen position
            screen_x = self.x + tetromino.x * GRID_SIZE
            screen_y = self.y + tetromino.y * GRID_SIZE

            # Draw block and glow effects
            tetromino.render(surface, screen_x, screen_y)
            tetromino.render_glow(surface, screen_x, screen_y)
        except Exception as e:
            self.logger.error(f"Error rendering tetromino: {e}")
