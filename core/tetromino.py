#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Tetromino Class
------------------------------
This class handles individual tetromino blocks
"""

import random
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
    TETROMINO_SHAPES,
    TETROMINO_COLORS,
    TETROMINO_GLOW_COLORS,
    GRID_SIZE,
)


class Tetromino:
    """Class for tetromino blocks"""

    def __init__(self, shape_name=None, x=0, y=0):
        """
        Create a new tetromino

        Args:
            shape_name (str, optional): Shape name (I, J, L, O, S, T, Z). Random if None.
            x (int, optional): Initial X position
            y (int, optional): Initial Y position
        """
        self.logger = get_logger("tetris.tetromino")

        # If no shape specified, choose a random one
        if shape_name is None:
            shape_name = random.choice(list(TETROMINO_SHAPES.keys()))

        self.shape_name = shape_name
        self.shape = TETROMINO_SHAPES[shape_name]
        self.color = TETROMINO_COLORS[shape_name]
        self.glow_color = TETROMINO_GLOW_COLORS[shape_name]
        self.rotation = 0
        self.x = x
        self.y = y

        # For T-spin detection
        self.last_rotation = False
        self.t_spin = False

        # Create surfaces for rendering
        self._create_surfaces()

    def _create_surfaces(self):
        """Create pre-rendered surfaces for performance optimization"""
        try:
            # Maximum tetromino size (4x4)
            max_size = 4 * GRID_SIZE

            # Main block surface
            self.surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)

            # Glow effect surface (for bloom)
            self.glow_surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)

            # Ghost piece surface
            self.ghost_surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)

            # Draw blocks on surfaces
            self._update_surfaces()
        except Exception as e:
            self.logger.error(f"Error creating tetromino surfaces: {e}")

    def _update_surfaces(self):
        """Update surfaces based on current block state"""
        try:
            # Clear surfaces
            self.surface.fill((0, 0, 0, 0))
            self.glow_surface.fill((0, 0, 0, 0))
            self.ghost_surface.fill((0, 0, 0, 0))

            # Draw each block
            current_shape = self.shape[self.rotation]
            for x, y in current_shape:
                # Main block
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self.surface, self.color, rect)
                pygame.draw.rect(self.surface, (255, 255, 255), rect, 1)  # White border

                # Glow effect
                center = (
                    x * GRID_SIZE + GRID_SIZE // 2,
                    y * GRID_SIZE + GRID_SIZE // 2,
                )
                pygame.draw.circle(
                    self.glow_surface, (*self.glow_color, 128), center, GRID_SIZE - 5
                )

                # Ghost piece
                ghost_rect = rect.copy()
                ghost_color = TETROMINO_COLORS["ghost"]
                pygame.draw.rect(self.ghost_surface, ghost_color, ghost_rect)
                pygame.draw.rect(
                    self.ghost_surface, (100, 100, 100), ghost_rect, 1
                )  # Gray border
        except Exception as e:
            self.logger.error(f"Error updating tetromino surfaces: {e}")

    def get_positions(self):
        """
        Get current block positions on the board

        Returns:
            list: List of (x, y) positions for each block
        """
        positions = []
        for block_x, block_y in self.shape[self.rotation]:
            positions.append((self.x + block_x, self.y + block_y))
        return positions

    def rotate(self, direction=1, board=None):
        """
        Rotate the tetromino

        Args:
            direction (int): 1 for clockwise, -1 for counter-clockwise
            board (Board, optional): Board for collision checking

        Returns:
            bool: True if rotation successful, False if blocked
        """
        # Save current rotation
        old_rotation = self.rotation

        # Calculate new rotation (0-3)
        new_rotation = (self.rotation + direction) % 4
        self.rotation = new_rotation

        # If board specified, check collisions
        if board is not None:
            # Use Super Rotation System (SRS) to try different positions
            kicks = self._get_wall_kicks(old_rotation, new_rotation)

            for kick_x, kick_y in kicks:
                test_x = self.x + kick_x
                test_y = self.y + kick_y

                if not board.check_collision(self, test_x, test_y):
                    # Rotation successful
                    self.x = test_x
                    self.y = test_y
                    self.last_rotation = True

                    # Check for T-spin (T block only)
                    if self.shape_name == "T":
                        self.check_tspin(board)

                    # Update rendering surfaces
                    self._update_surfaces()
                    return True

            # If no valid position found, revert rotation
            self.rotation = old_rotation
            return False

        # Update surfaces
        self._update_surfaces()
        return True

    def _get_wall_kicks(self, old_rot, new_rot):
        """
        Get wall kick offsets for Super Rotation System (SRS)

        Args:
            old_rot (int): Current rotation (0-3)
            new_rot (int): New rotation (0-3)

        Returns:
            list: List of (dx, dy) offsets to try
        """
        # Wall kick data for I tetromino
        if self.shape_name == "I":
            kicks = {
                (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
                (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
                (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
                (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
                (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
                (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
                (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
                (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
            }
        # Wall kick data for other tetrominos (J, L, S, T, Z)
        else:
            kicks = {
                (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
                (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
                (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
                (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
                (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
                (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
                (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
                (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
            }

        # O tetromino doesn't need kicks (symmetrical)
        if self.shape_name == "O":
            return [(0, 0)]

        # Get appropriate kicks
        key = (old_rot, new_rot)
        return kicks.get(key, [(0, 0)])

    def move(self, dx, dy, board=None):
        """
        Move the tetromino

        Args:
            dx (int): X movement (-1 for left, 1 for right)
            dy (int): Y movement (1 for down)
            board (Board, optional): Board for collision checking

        Returns:
            bool: True if movement successful, False if blocked
        """
        # Calculate new position
        new_x = self.x + dx
        new_y = self.y + dy

        # Check for collisions if board provided
        if board is not None:
            if board.check_collision(self, new_x, new_y):
                return False

        # Update position
        self.x = new_x
        self.y = new_y

        # Reset last rotation state (for T-spin detection)
        self.last_rotation = False

        return True

    def hard_drop(self, board):
        """
        Drop block to bottom immediately

        Args:
            board (Board): Game board

        Returns:
            int: Number of cells dropped (for scoring)
        """
        drop_distance = 0

        # Move down until collision
        while not board.check_collision(self, self.x, self.y + 1):
            self.y += 1
            drop_distance += 1

        return drop_distance

    def get_ghost_position(self, board):
        """
        Calculate ghost piece position (shadow at bottom)

        Args:
            board (Board): Game board

        Returns:
            int: Y position where block would land
        """
        ghost_y = self.y

        # Move down until collision
        while not board.check_collision(self, self.x, ghost_y + 1):
            ghost_y += 1

        return ghost_y

    def check_tspin(self, board):
        """
        Check if current position is a T-spin
        (T block with 3+ corners blocked)

        Args:
            board (Board): Game board

        Returns:
            bool: True if T-spin detected
        """
        # Only check T blocks that were just rotated
        if self.shape_name != "T" or not self.last_rotation:
            self.t_spin = False
            return False

        # Check all 4 corners around the T block
        corners = [
            (self.x, self.y),  # Top-left
            (self.x + 2, self.y),  # Top-right
            (self.x, self.y + 2),  # Bottom-left
            (self.x + 2, self.y + 2),  # Bottom-right
        ]

        # Count blocked corners
        blocked_corners = 0
        for corner_x, corner_y in corners:
            if (
                corner_x < 0
                or corner_x >= board.width
                or corner_y < 0
                or corner_y >= board.height
                or board.grid[corner_y][corner_x] is not None
            ):
                blocked_corners += 1

        # T-spin requires at least 3 corners blocked
        self.t_spin = blocked_corners >= 3
        return self.t_spin

    def render(self, surface, x, y):
        """
        Render the tetromino on the surface

        Args:
            surface (pygame.Surface): Surface to render on
            x (int): X position on screen
            y (int): Y position on screen
        """
        try:
            surface.blit(self.surface, (x, y))
        except Exception as e:
            self.logger.error(f"Error rendering tetromino: {e}")

    def render_ghost(self, surface, x, y):
        """
        Render ghost (shadow) tetromino on the surface

        Args:
            surface (pygame.Surface): Surface to render on
            x (int): X position on screen
            y (int): Y position on screen
        """
        try:
            surface.blit(self.ghost_surface, (x, y))
        except Exception as e:
            self.logger.error(f"Error rendering tetromino ghost: {e}")

    def render_glow(self, surface, x, y):
        """
        Render glow effect for tetromino (for bloom effect)

        Args:
            surface (pygame.Surface): Surface to render on
            x (int): X position on screen
            y (int): Y position on screen
        """
        try:
            surface.blit(self.glow_surface, (x, y))
        except Exception as e:
            self.logger.error(f"Error rendering tetromino glow: {e}")
