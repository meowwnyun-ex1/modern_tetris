#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Main Application
-------------------------------
A modern Tetris game with DENSO branding
Copyright (c) 2025 Thammaphon Chittasuwanna (SDM)
"""

import os
import sys
import yaml
import logging
import traceback
import time
from pathlib import Path


# Set up exception handling before imports
def global_exception_handler(exctype, value, tb):
    """Global exception handler to log unhandled exceptions"""
    logger = logging.getLogger("tetris")
    logger.critical(f"Unhandled exception: {value}")
    logger.critical("".join(traceback.format_exception(exctype, value, tb)))
    sys.__excepthook__(exctype, value, tb)

    # Show error message to user if pygame is initialized
    try:
        if pygame.display.get_init():
            show_crash_screen(f"Error: {str(value)}")
    except:
        pass


# Install global exception handler
sys.__excepthook__ = global_exception_handler

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame

        print("Using pygame-ce instead of pygame")
    except ImportError:
        print("Please install pygame or pygame-ce")
        sys.exit(1)

# Try to import internal modules after pygame is loaded
try:
    from core.constants import (
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        DENSO_RED,
        TITLE,
        UI_BG,
    )
    from core.game import Game
    from ui.menu import MainMenu
    from utils.logger import setup_logger
    from db.session import init_db
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)


def ensure_assets_directory():
    """Ensure all required directories exist with improved asset creation"""
    # Create required directory structure
    required_dirs = [
        "assets",
        "assets/images",
        "assets/images/backgrounds",
        "assets/sounds",
        "assets/fonts",
        "logs",
    ]

    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)

    # Create minimal required assets
    create_important_assets()


def create_important_assets():
    """Create minimal required assets to prevent errors"""
    # Create small icon
    icon_path = "assets/images/icon.png"
    if not os.path.exists(icon_path):
        try:
            icon_surface = pygame.Surface((32, 32))
            icon_surface.fill(DENSO_RED)
            pygame.draw.rect(icon_surface, (255, 255, 255), (8, 8, 16, 16))
            pygame.image.save(icon_surface, icon_path)
            logger.info(f"Created icon: {icon_path}")
        except Exception as e:
            logger.error(f"Could not create icon: {e}")

    # Create dummy files for essential sounds
    for sound_name in [
        "menu_select.wav",
        "game_over.wav",
        "menu_theme.mp3",
        "game_theme.mp3",
        "move.wav",
        "rotate.wav",
        "drop.wav",
        "clear.wav",
        "tetris.wav",
        "level_up.wav",
        "menu_change.wav",
    ]:
        create_empty_sound(f"assets/sounds/{sound_name}")


def create_empty_sound(filename):
    """Create an empty sound file to prevent errors"""
    if os.path.exists(filename):
        return

    try:
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok=True)

        # Create empty file with simple header
        with open(filename, "wb") as f:
            # Write minimal header based on file type
            if filename.endswith(".wav"):
                # Simple WAV header
                f.write(
                    b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
                )
            else:
                # Empty file for other types
                f.write(b"\x00" * 32)

        logger.info(f"Created dummy sound file: {filename}")
    except Exception as e:
        logger.error(f"Failed to create dummy sound file: {e}")


def load_config():
    """Load configuration from config.yaml with error handling"""
    default_config = {
        "screen": {
            "width": SCREEN_WIDTH,
            "height": SCREEN_HEIGHT,
            "fullscreen": False,
            "vsync": True,
            "target_fps": 60,
        },
        "game": {
            "difficulty": "medium",
            "start_level": 1,
            "max_level": 20,
            "level_up_lines": 10,
            "das_delay": 170,
            "arr_delay": 30,
        },
        "graphics": {
            "theme": "denso",
            "particles": True,
            "animations": True,
            "bloom_effect": True,
        },
        "audio": {
            "music_volume": 0.6,
            "sfx_volume": 0.7,
            "enable_music": True,
            "enable_sfx": True,
        },
        "tetromino": {
            "ghost_piece": True,
            "enable_hold": True,
            "enable_preview": True,
            "preview_count": 3,
        },
        "ui": {
            "font": "arial",
            "language": "en",
            "show_fps": True,
            "show_ghost_piece": True,
            "show_grid": True,
        },
        "database": {"engine": "sqlite", "sqlite": {"path": "./tetris.db"}},
    }

    try:
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f)

            # Deep merge configs
            for key, value in loaded_config.items():
                if (
                    key in default_config
                    and isinstance(default_config[key], dict)
                    and isinstance(value, dict)
                ):
                    default_config[key].update(value)
                else:
                    default_config[key] = value

            logging.info("Configuration loaded successfully")
        else:
            logging.warning("config.yaml not found, using default configuration")
            # Save default config for future use
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False)

    except Exception as e:
        logging.error(f"Could not load config file: {e}")

    return default_config


def show_crash_screen(error_message):
    """Display a crash screen when fatal errors occur"""
    try:
        # Setup minimal display if not already initialized
        if not pygame.display.get_init():
            pygame.init()
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("DENSO Tetris - Error")
        else:
            screen = pygame.display.get_surface()

        # Clear screen
        screen.fill((20, 20, 30))

        # Create fonts
        title_font = pygame.font.SysFont("Arial", 32, bold=True)
        text_font = pygame.font.SysFont("Arial", 18)

        # Render error title
        title = title_font.render("DENSO Tetris - Critical Error", True, (255, 50, 50))
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 100))

        # Render error message
        y_pos = 200
        wrapped_text = wrap_text(error_message, text_font, screen.get_width() - 100)
        for line in wrapped_text:
            text = text_font.render(line, True, (255, 255, 255))
            screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, y_pos))
            y_pos += 30

        # Render help text
        help_text = text_font.render("Press any key to exit", True, (200, 200, 200))
        screen.blit(
            help_text,
            (screen.get_width() // 2 - help_text.get_width() // 2, y_pos + 40),
        )

        # Update display
        pygame.display.flip()

        # Wait for key press
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False
            pygame.time.wait(100)

    except Exception as e:
        print(f"Failed to show crash screen: {e}")
    finally:
        try:
            pygame.quit()
        except:
            pass


def wrap_text(text, font, max_width):
    """Wrap text to fit within a given width"""
    words = text.split(" ")
    lines = []
    current_line = []

    for word in words:
        # Test width
        test_line = " ".join(current_line + [word])
        width = font.size(test_line)[0]

        if width <= max_width:
            current_line.append(word)
        else:
            # Start a new line
            lines.append(" ".join(current_line))
            current_line = [word]

    # Add the last line
    if current_line:
        lines.append(" ".join(current_line))

    return lines


def fallback_menu(screen):
    """Fallback simple menu if main menu fails to load"""
    font_large = pygame.font.SysFont("Arial", 32)
    font_medium = pygame.font.SysFont("Arial", 24)

    title = font_large.render("DENSO Tetris - Error Loading UI", True, (255, 255, 255))
    error_text = font_medium.render(
        "The game menu could not be initialized", True, (255, 50, 50)
    )
    help_text = font_medium.render(
        "Press ENTER to start game or ESC to exit", True, (200, 200, 200)
    )
    copyright = font_medium.render(
        "© 2025 Thammaphon Chittasuwanna (SDM)", True, (150, 150, 150)
    )

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                return None  # Exit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                try:
                    # Try to start game directly
                    config = load_config()
                    return Game(screen, config, "Guest")
                except Exception as e:
                    logging.error(f"Cannot start game: {e}")

        # Render
        screen.fill((20, 20, 30))

        # Draw DENSO logo
        pygame.draw.rect(screen, DENSO_RED, (SCREEN_WIDTH // 2 - 100, 80, 200, 50))
        logo_text = font_large.render("DENSO", True, (255, 255, 255))
        screen.blit(logo_text, (SCREEN_WIDTH // 2 - logo_text.get_width() // 2, 90))

        # Draw error info
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 250))
        screen.blit(help_text, (SCREEN_WIDTH // 2 - help_text.get_width() // 2, 350))

        # Draw copyright
        screen.blit(
            copyright,
            (SCREEN_WIDTH // 2 - copyright.get_width() // 2, SCREEN_HEIGHT - 50),
        )

        pygame.display.flip()
        pygame.time.wait(100)

    return None


def main():
    """Main function of the application with improved error handling and performance"""
    # Initialize logger
    global logger
    logger = setup_logger()
    logger.info("DENSO Tetris starting...")

    try:
        # Load configuration
        config = load_config()

        # Initialize pygame
        pygame.init()

        # Set better exception handling
        sys.excepthook = global_exception_handler

        # Create display window
        screen = pygame.display.set_mode(
            (config["screen"]["width"], config["screen"]["height"]),
            pygame.FULLSCREEN if config["screen"]["fullscreen"] else 0,
        )
        pygame.display.set_caption(TITLE)

        # Try to set window icon
        try:
            icon_path = "assets/images/icon.png"
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path)
                pygame.display.set_icon(icon)
        except Exception as e:
            logger.warning(f"Could not load window icon: {e}")

        # Create required assets directory structure
        ensure_assets_directory()

        # Initialize database connection
        try:
            init_db()
        except Exception as e:
            logger.error(f"Could not initialize database: {e}")

        # Create first scene
        try:
            current_scene = MainMenu(screen, config)
            logger.info("Main menu initialized successfully")
        except Exception as e:
            logger.error(
                f"Could not initialize main menu: {e}\n{traceback.format_exc()}"
            )
            current_scene = fallback_menu(screen)
            if current_scene is None:
                pygame.quit()
                sys.exit(1)

        # Main game loop
        clock = pygame.time.Clock()
        running = True
        last_time = time.time()
        accumulated_time = 0
        fixed_time_step = 1.0 / config["screen"].get("target_fps", 60)

        while running:
            # Custom time measurement
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            # Limit processing frame rate (prevent CPU throttling)
            delta_time = min(delta_time, 0.25)  # Max 250 ms
            accumulated_time += delta_time

            # Process input
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_F4
                    and (event.mod & pygame.KMOD_ALT)
                ):
                    running = False

                if current_scene:
                    current_scene.handle_event(event)

            # Prepare variable for fixed update tracking
            update_count = 0

            # Fixed update steps for consistent physics (limit updates)
            while (
                accumulated_time >= fixed_time_step and update_count < 5
            ):  # Limit to 5 updates per frame
                # Update state
                if current_scene:
                    next_scene = current_scene.update(fixed_time_step)
                    if next_scene:
                        # Change scene if requested
                        current_scene = next_scene
                        # Reset events to prevent carry-over
                        events.clear()

                accumulated_time -= fixed_time_step
                update_count += 1

            # If too much accumulated time remains but update limit reached
            # Drop the excess time to prevent death spiral
            if update_count >= 5 and accumulated_time > fixed_time_step:
                logger.warning(
                    f"Dropping {accumulated_time:.4f}s of accumulated time to prevent lag spiral"
                )
                accumulated_time = 0

            # Fill background with base color before rendering
            screen.fill(UI_BG)

            # Render graphics
            if current_scene:
                current_scene.render()

            # Update display
            pygame.display.flip()

            # Limit frame rate
            try:
                clock.tick(config["screen"].get("target_fps", 60))
            except Exception as e:
                logger.error(f"Error in clock.tick(): {e}")

            # Give CPU a break if processing is too fast
            if delta_time < fixed_time_step * 0.5:
                time.sleep(0.001)  # Sleep 1ms if processing too fast

    except KeyboardInterrupt:
        logger.info("Game terminated by user (KeyboardInterrupt)")
    except Exception as e:
        logger.critical(f"Critical error in main loop: {e}\n{traceback.format_exc()}")
        show_crash_screen(str(e))
    finally:
        # Clean up and exit
        logger.info("Closing application")
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
