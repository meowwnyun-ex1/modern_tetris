#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Complete Tetromino Class
------------------------------
Enhanced tetromino handling with full SRS implementation
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
    """Enhanced tetromino class with complete functionality"""

    def __init__(self, shape_name=None, x=0, y=0):
        """Initialize tetromino with full error handling"""
        self.logger = get_logger("tetris.tetromino")

        # Choose random shape if none specified
        if shape_name is None:
            shape_name = random.choice(list(TETROMINO_SHAPES.keys()))

        self.shape_name = shape_name
        self.shape = TETROMINO_SHAPES.get(shape_name, TETROMINO_SHAPES['O'])
        self.color = TETROMINO_COLORS.get(shape_name, (128, 128, 128))
        self.glow_color = TETROMINO_GLOW_COLORS.get(shape_name, (128, 128, 128))
        self.rotation = 0
        self.x = x
        self.y = y

        # T-spin detection
        self.last_rotation = False
        self.t_spin = False

        # Create rendering surfaces
        self._create_surfaces()

    def _create_surfaces(self):
        """Create pre-rendered surfaces for performance"""
        try:
            max_size = 4 * GRID_SIZE
            self.surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)
            self.glow_surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)
            self.ghost_surface = pygame.Surface((max_size, max_size), pygame.SRCALPHA)
            self._update_surfaces()
        except Exception as e:
            self.logger.error(f"Error creating tetromino surfaces: {e}")
            # Create minimal fallback surfaces
            self.surface = pygame.Surface((1, 1))
            self.glow_surface = pygame.Surface((1, 1))
            self.ghost_surface = pygame.Surface((1, 1))

    def _update_surfaces(self):
        """Update surfaces based on current rotation"""
        try:
            # Clear surfaces
            self.surface.fill((0, 0, 0, 0))
            self.glow_surface.fill((0, 0, 0, 0))
            self.ghost_surface.fill((0, 0, 0, 0))

            # Get current shape
            current_shape = self.shape[self.rotation]
            
            for x, y in current_shape:
                # Main block
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                
                # Draw main piece
                pygame.draw.rect(self.surface, self.color, rect)
                pygame.draw.rect(self.surface, (255, 255, 255), rect, 1)

                # Draw glow effect
                center = (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2)
                pygame.draw.circle(
                    self.glow_surface, 
                    (*self.glow_color, 128), 
                    center, 
                    GRID_SIZE - 5
                )

                # Draw ghost piece
                ghost_color = TETROMINO_COLORS["ghost"]
                pygame.draw.rect(self.ghost_surface, ghost_color, rect)
                pygame.draw.rect(self.ghost_surface, (100, 100, 100), rect, 1)

        except Exception as e:
            self.logger.error(f"Error updating tetromino surfaces: {e}")

    def get_positions(self):
        """Get all block positions for collision detection"""
        positions = []
        for block_x, block_y in self.shape[self.rotation]:
            positions.append((self.x + block_x, self.y + block_y))
        return positions

    def rotate(self, direction=1, board=None):
        """Rotate with Super Rotation System (SRS)"""
        old_rotation = self.rotation
        new_rotation = (self.rotation + direction) % 4
        self.rotation = new_rotation

        if board is not None:
            # Try wall kicks
            kicks = self._get_wall_kicks(old_rotation, new_rotation)
            
            for kick_x, kick_y in kicks:
                test_x = self.x + kick_x
                test_y = self.y + kick_y

                if not board.check_collision(self, test_x, test_y):
                    # Success!
                    self.x = test_x
                    self.y = test_y
                    self.last_rotation = True

                    # Check for T-spin
                    if self.shape_name == "T":
                        self.check_tspin(board)

                    self._update_surfaces()
                    return True

            # All kicks failed, revert rotation
            self.rotation = old_rotation
            return False

        # No collision checking, just rotate
        self._update_surfaces()
        return True

    def _get_wall_kicks(self, old_rot, new_rot):
        """Super Rotation System wall kick data"""
        # I-piece has special kick data
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
        # Standard pieces (J, L, S, T, Z)
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

        # O-piece doesn't need kicks (symmetrical)
        if self.shape_name == "O":
            return [(0, 0)]

        return kicks.get((old_rot, new_rot), [(0, 0)])

    def move(self, dx, dy, board=None):
        """Move tetromino with collision detection"""
        new_x = self.x + dx
        new_y = self.y + dy

        if board is not None:
            if board.check_collision(self, new_x, new_y):
                return False

        self.x = new_x
        self.y = new_y
        self.last_rotation = False
        return True

    def hard_drop(self, board):
        """Drop piece to bottom and return distance"""
        drop_distance = 0
        while not board.check_collision(self, self.x, self.y + 1):
            self.y += 1
            drop_distance += 1
        return drop_distance

    def get_ghost_position(self, board):
        """Calculate where piece would land"""
        ghost_y = self.y
        while not board.check_collision(self, self.x, ghost_y + 1):
            ghost_y += 1
        return ghost_y

    def check_tspin(self, board):
        """Check for T-spin conditions"""
        if self.shape_name != "T" or not self.last_rotation:
            self.t_spin = False
            return False

        # Check 4 corners around T-piece
        corners = [
            (self.x, self.y),      # Top-left
            (self.x + 2, self.y),  # Top-right
            (self.x, self.y + 2),  # Bottom-left
            (self.x + 2, self.y + 2),  # Bottom-right
        ]

        blocked_corners = 0
        for corner_x, corner_y in corners:
            if (corner_x < 0 or corner_x >= board.width or 
                corner_y < 0 or corner_y >= board.height or
                (corner_y >= 0 and board.grid[corner_y][corner_x] is not None)):
                blocked_corners += 1

        # T-spin requires 3+ blocked corners
        self.t_spin = blocked_corners >= 3
        return self.t_spin

    def render(self, surface, x, y):
        """Render tetromino on surface"""
        try:
            surface.blit(self.surface, (x, y))
        except Exception as e:
            self.logger.error(f"Error rendering tetromino: {e}")

    def render_ghost(self, surface, x, y):
        """Render ghost piece"""
        try:
            surface.blit(self.ghost_surface, (x, y))
        except Exception as e:
            self.logger.error(f"Error rendering ghost: {e}")

    def render_glow(self, surface, x, y):
        """Render glow effect"""
        try:
            surface.blit(self.glow_surface, (x, y), special_flags=pygame.BLEND_ADD)
        except Exception as e:
            self.logger.error(f"Error rendering glow: {e}")

    def copy(self):
        """Create a copy of this tetromino"""
        new_piece = Tetromino(self.shape_name, self.x, self.y)
        new_piece.rotation = self.rotation
        new_piece.last_rotation = self.last_rotation
        new_piece.t_spin = self.t_spin
        return new_piece