#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Main Application
-------------------------------
A modern Tetris game with minimalist design
Copyright (c) 2025 Thammaphon Chittasuwanna (SDM)
"""

import os
import sys
import yaml
import logging
import pygame
from pygame.locals import *

# Import internal modules
from core.game import Game
from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, UI_BG
from ui.menu import MainMenu
from utils.logger import setup_logger
from db.session import init_db


def load_config():
    """Load configuration from config.yaml"""
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Could not load config file: {e}")
        return {}


def main():
    """Main function of the application"""
    # Setup logging
    setup_logger()
    logger = logging.getLogger("tetris")
    logger.info("Starting DENSO Tetris application")

    # Load configuration
    config = load_config()

    # Initialize database
    init_db()

    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()

    # Setup window - Windowed mode optimized for 14" notebook
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)

    # Set window icon
    try:
        icon = pygame.image.load("assets/images/icon.png")
        pygame.display.set_icon(icon)
    except:
        logger.warning("Could not load game icon")

    # Set custom cursor (simple, elegant)
    try:
        cursor_img = pygame.image.load("assets/images/cursor.png")
        cursor = pygame.cursors.Cursor((0, 0), cursor_img)
        pygame.mouse.set_cursor(cursor)
    except:
        # Default to system cursor if custom one not available
        pass

    # Setup Clock for FPS control
    clock = pygame.time.Clock()

    # Create MainMenu
    main_menu = MainMenu(screen, config)

    # Start main loop
    running = True
    current_scene = main_menu

    # For smooth framerate
    accumulated_time = 0
    fixed_time_step = 1.0 / config["screen"]["target_fps"]

    while running:
        # Calculate delta time with scaling for consistent gameplay
        dt = min(clock.tick(config["screen"]["target_fps"]) / 1000.0, 0.1)
        accumulated_time += dt

        # Process inputs
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            current_scene.handle_event(event)

        # Fixed update steps for consistent physics
        while accumulated_time >= fixed_time_step:
            # Update state
            next_scene = current_scene.update(fixed_time_step)
            if next_scene:
                # Change scene if requested
                current_scene = next_scene
                # Reset events to prevent carry-over
                events.clear()
            accumulated_time -= fixed_time_step

        # Fill background with base color before rendering
        screen.fill(UI_BG)

        # Render graphics
        current_scene.render()

        # Update display
        pygame.display.flip()

    # Clean up and exit
    logger.info("Closing application")
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
