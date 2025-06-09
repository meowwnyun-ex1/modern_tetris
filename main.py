#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Main Application (Updated for Neon Database)
----------------------------------------------------------
A modern Tetris game with DENSO branding and cloud database support
Copyright (c) 2025 Thammaphon Chittasuwanna (SDM)
"""

import os
import sys
import yaml
import logging
import traceback
import time
from pathlib import Path

# Load environment variables early
try:
    from dotenv import load_dotenv

    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("python-dotenv not available, using system environment variables only")


# Set up exception handling before imports
def global_exception_handler(exctype, value, tb):
    """Global exception handler to log unhandled exceptions"""
    logger = logging.getLogger("tetris")
    logger.critical(f"Unhandled exception: {value}")
    logger.critical("".join(traceback.format_exception(exctype, value, tb)))
    sys.__excepthook__(exctype, value, tb)

    # Show error message to user if pygame is initialized
    try:
        if "pygame" in sys.modules and pygame.display.get_init():
            show_crash_screen(f"Error: {str(value)}")
    except:
        pass


# Install global exception handler
sys.excepthook = global_exception_handler

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame

        print("Using pygame-ce instead of pygame")
    except ImportError:
        print("Please install pygame or pygame-ce")
        print("Run: pip install pygame")
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
    from db.session import init_db, check_database_health
    from db.queries import check_database_connection
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print("\nPlease ensure all required modules are properly installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)


def check_environment():
    """Check and validate environment configuration"""
    logger = logging.getLogger("tetris.env")

    # Check Python version
    if sys.version_info < (3, 8):
        logger.error(f"Python 3.8+ required, but found {sys.version}")
        return False

    # Check required environment variables for database
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        logger.info("Found DATABASE_URL environment variable")
        # Validate URL format
        if not database_url.startswith(("postgres://", "postgresql://")):
            logger.warning("DATABASE_URL doesn't appear to be a PostgreSQL URL")
    else:
        logger.info("DATABASE_URL not found, will use SQLite fallback")

    # Check optional environment variables
    env_vars = {
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
    }

    logger.info(f"Environment: {env_vars['APP_ENV']}")
    logger.info(f"Debug mode: {env_vars['DEBUG']}")
    logger.info(f"Log level: {env_vars['LOG_LEVEL']}")

    return True


def ensure_assets_directory():
    """Ensure all required directories exist with improved asset creation"""
    logger = logging.getLogger("tetris.assets")

    # Create required directory structure
    required_dirs = [
        "assets",
        "assets/images",
        "assets/images/backgrounds",
        "assets/sounds",
        "assets/fonts",
        "logs",
        "temp",
    ]

    for directory in required_dirs:
        try:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")

    # Create minimal required assets
    create_essential_assets()


def create_essential_assets():
    """Create minimal required assets to prevent errors"""
    logger = logging.getLogger("tetris.assets")

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

    # Create dummy sound files to prevent audio errors
    essential_sounds = [
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
        "t_spin.wav",
        "hold.wav",
        "button_hover.wav",
        "button_click.wav",
    ]

    for sound_name in essential_sounds:
        sound_path = f"assets/sounds/{sound_name}"
        if not os.path.exists(sound_path):
            create_dummy_sound(sound_path)


def create_dummy_sound(filename):
    """Create a minimal sound file to prevent audio errors"""
    logger = logging.getLogger("tetris.assets")

    try:
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok=True)

        # Create minimal file based on extension
        with open(filename, "wb") as f:
            if filename.endswith(".wav"):
                # Minimal WAV header (44 bytes) + minimal data
                wav_header = (
                    b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
                    b"\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00"
                    b"\x02\x00\x10\x00data\x00\x00\x00\x00"
                )
                f.write(wav_header)
            elif filename.endswith(".mp3"):
                # Minimal MP3 header
                f.write(b"\xff\xfb\x90\x00" + b"\x00" * 32)
            else:
                # Generic empty file
                f.write(b"\x00" * 64)

        logger.debug(f"Created dummy sound file: {filename}")
    except Exception as e:
        logger.error(f"Failed to create dummy sound file {filename}: {e}")


def load_config():
    """Load configuration with environment variable support and validation"""
    logger = logging.getLogger("tetris.config")

    # Default configuration with environment variable overrides
    default_config = {
        "screen": {
            "width": int(os.getenv("SCREEN_WIDTH", SCREEN_WIDTH)),
            "height": int(os.getenv("SCREEN_HEIGHT", SCREEN_HEIGHT)),
            "fullscreen": os.getenv("FULLSCREEN", "false").lower() == "true",
            "vsync": os.getenv("VSYNC", "true").lower() == "true",
            "target_fps": int(os.getenv("TARGET_FPS", "60")),
        },
        "game": {
            "difficulty": os.getenv("GAME_DIFFICULTY", "medium"),
            "start_level": int(os.getenv("START_LEVEL", "1")),
            "max_level": int(os.getenv("MAX_LEVEL", "20")),
            "level_up_lines": int(os.getenv("LEVEL_UP_LINES", "10")),
            "das_delay": int(os.getenv("DAS_DELAY", "170")),
            "arr_delay": int(os.getenv("ARR_DELAY", "30")),
        },
        "graphics": {
            "theme": os.getenv("GAME_THEME", "denso"),
            "particles": os.getenv("PARTICLES", "true").lower() == "true",
            "animations": os.getenv("ANIMATIONS", "true").lower() == "true",
            "bloom_effect": os.getenv("BLOOM_EFFECT", "true").lower() == "true",
        },
        "audio": {
            "music_volume": float(os.getenv("MUSIC_VOLUME", "0.6")),
            "sfx_volume": float(os.getenv("SFX_VOLUME", "0.7")),
            "enable_music": os.getenv("ENABLE_MUSIC", "true").lower() == "true",
            "enable_sfx": os.getenv("ENABLE_SFX", "true").lower() == "true",
        },
        "tetromino": {
            "ghost_piece": os.getenv("GHOST_PIECE", "true").lower() == "true",
            "enable_hold": os.getenv("ENABLE_HOLD", "true").lower() == "true",
            "enable_preview": os.getenv("ENABLE_PREVIEW", "true").lower() == "true",
            "preview_count": int(os.getenv("PREVIEW_COUNT", "3")),
        },
        "ui": {
            "font": os.getenv("UI_FONT", "arial"),
            "language": os.getenv("UI_LANGUAGE", "en"),
            "show_fps": os.getenv("SHOW_FPS", "true").lower() == "true",
            "show_ghost_piece": os.getenv("SHOW_GHOST_PIECE", "true").lower() == "true",
            "show_grid": os.getenv("SHOW_GRID", "true").lower() == "true",
        },
        "database": {
            "engine": "postgresql" if os.getenv("DATABASE_URL") else "sqlite",
            "postgresql": {
                "url": os.getenv("DATABASE_URL", ""),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
                "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
                "echo": os.getenv("DB_ECHO", "false").lower() == "true",
            },
            "sqlite": {"path": os.getenv("SQLITE_PATH", "./tetris.db")},
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "console_output": os.getenv("LOG_CONSOLE", "true").lower() == "true",
            "file_output": os.getenv("LOG_FILE", "true").lower() == "true",
        },
        "security": {
            "bcrypt_rounds": int(os.getenv("BCRYPT_ROUNDS", "12")),
            "session_timeout": int(os.getenv("SESSION_TIMEOUT", "30")),
        },
    }

    try:
        # Try to load from config.yaml and merge with defaults
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}

            # Deep merge configurations (environment variables take priority)
            for section, values in yaml_config.items():
                if section in default_config and isinstance(values, dict):
                    # Update section but preserve environment overrides
                    yaml_section = yaml_config[section]
                    default_section = default_config[section]

                    # Merge while preserving env var overrides
                    for key, value in yaml_section.items():
                        if key not in default_section:
                            default_section[key] = value
                        # Don't override if env var was set
                else:
                    default_config[section] = values

            logger.info(
                "Configuration loaded from config.yaml and environment variables"
            )
        else:
            logger.info(
                "config.yaml not found, using environment variables and defaults"
            )

            # Save default config for future reference
            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(default_config, f, default_flow_style=False, indent=2)
                logger.info("Created default config.yaml")
            except Exception as e:
                logger.warning(f"Could not create config.yaml: {e}")

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.info("Using default configuration")

    # Validate configuration
    try:
        _validate_config(default_config)
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        # Use safe defaults for critical values
        default_config["screen"]["width"] = max(
            640, min(1920, default_config["screen"]["width"])
        )
        default_config["screen"]["height"] = max(
            480, min(1080, default_config["screen"]["height"])
        )
        default_config["screen"]["target_fps"] = max(
            30, min(120, default_config["screen"]["target_fps"])
        )

    return default_config


def _validate_config(config):
    """Validate configuration values"""
    # Screen validation
    if config["screen"]["width"] < 640 or config["screen"]["width"] > 3840:
        raise ValueError(f"Invalid screen width: {config['screen']['width']}")

    if config["screen"]["height"] < 480 or config["screen"]["height"] > 2160:
        raise ValueError(f"Invalid screen height: {config['screen']['height']}")

    # Audio validation
    config["audio"]["music_volume"] = max(
        0.0, min(1.0, config["audio"]["music_volume"])
    )
    config["audio"]["sfx_volume"] = max(0.0, min(1.0, config["audio"]["sfx_volume"]))

    # Game validation
    config["game"]["start_level"] = max(1, min(20, config["game"]["start_level"]))
    config["game"]["max_level"] = max(
        config["game"]["start_level"], min(99, config["game"]["max_level"])
    )


def show_crash_screen(error_message):
    """Display a crash screen when fatal errors occur"""
    try:
        # Setup minimal display if not already initialized
        if not pygame.display.get_init():
            pygame.init()
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("DENSO Tetris - Critical Error")
        else:
            screen = pygame.display.get_surface()

        # Clear screen with dark background
        screen.fill((20, 20, 30))

        # Create fonts
        try:
            title_font = pygame.font.Font(None, 36)
            text_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 16)
        except:
            title_font = pygame.font.SysFont("Arial", 32, bold=True)
            text_font = pygame.font.SysFont("Arial", 18)
            small_font = pygame.font.SysFont("Arial", 14)

        # Render DENSO branding
        denso_text = title_font.render("DENSO TETRIS", True, DENSO_RED)
        screen.blit(
            denso_text, (screen.get_width() // 2 - denso_text.get_width() // 2, 50)
        )

        # Render error title
        error_title = title_font.render("Critical Error", True, (255, 100, 100))
        screen.blit(
            error_title, (screen.get_width() // 2 - error_title.get_width() // 2, 120)
        )

        # Render error message (wrapped)
        y_pos = 180
        wrapped_lines = wrap_text(error_message, text_font, screen.get_width() - 100)
        for line in wrapped_lines:
            text = text_font.render(line, True, (255, 255, 255))
            screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, y_pos))
            y_pos += 25

        # Render help information
        help_lines = [
            "Please check the following:",
            "• Ensure all dependencies are installed (pip install -r requirements.txt)",
            "• Check your database connection (DATABASE_URL environment variable)",
            "• Verify config.yaml is properly formatted",
            "• Check the logs directory for more details",
            "",
            "Press any key to exit or check the console for more information",
        ]

        y_pos += 30
        for line in help_lines:
            color = (
                (200, 200, 200)
                if line and not line.startswith("•")
                else (150, 150, 150)
            )
            text = small_font.render(line, True, color)
            screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, y_pos))
            y_pos += 20

        # Update display
        pygame.display.flip()

        # Wait for key press with timeout
        start_time = time.time()
        waiting = True
        while waiting and (time.time() - start_time) < 30:  # 30 second timeout
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False
            pygame.time.wait(100)

    except Exception as e:
        print(f"Failed to show crash screen: {e}")
        print(f"Original error: {error_message}")
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
        # Test if adding this word exceeds the width
        test_line = " ".join(current_line + [word])
        width = font.size(test_line)[0]

        if width <= max_width:
            current_line.append(word)
        else:
            # Start a new line
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    # Add the last line
    if current_line:
        lines.append(" ".join(current_line))

    return lines


def initialize_database():
    """Initialize database with comprehensive error handling"""
    logger = logging.getLogger("tetris.db")

    try:
        logger.info("Initializing database...")

        # Initialize database connection
        if not init_db():
            logger.error("Failed to initialize database")
            return False

        # Check database health
        health_check = check_database_connection()
        if health_check["status"] != "healthy":
            logger.warning(f"Database health check failed: {health_check['message']}")
            # Continue anyway - might be using fallback SQLite
        else:
            logger.info("Database connection established successfully")

        return True

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        logger.debug(traceback.format_exc())
        return False


def fallback_menu(screen, config):
    """Fallback simple menu if main menu fails to load"""
    logger = logging.getLogger("tetris.fallback")

    try:
        font_large = pygame.font.SysFont("Arial", 32)
        font_medium = pygame.font.SysFont("Arial", 24)
        font_small = pygame.font.SysFont("Arial", 18)
    except:
        font_large = pygame.font.Font(None, 36)
        font_medium = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 20)

    clock = pygame.time.Clock()

    # Prepare texts
    texts = {
        "title": font_large.render("DENSO Tetris", True, DENSO_RED),
        "error": font_medium.render(
            "Menu system could not be initialized", True, (255, 100, 100)
        ),
        "help1": font_small.render(
            "Press ENTER to start game as Guest", True, (200, 200, 200)
        ),
        "help2": font_small.render("Press ESC to exit", True, (200, 200, 200)),
        "copyright": font_small.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, (150, 150, 150)
        ),
        "status": font_small.render("Fallback Mode", True, (255, 200, 100)),
    }

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_RETURN:
                    try:
                        logger.info("Starting game from fallback menu")
                        return Game(screen, config, "Guest")
                    except Exception as e:
                        logger.error(f"Cannot start game from fallback: {e}")
                        show_crash_screen(f"Game initialization failed: {str(e)}")
                        return None

        # Render fallback menu
        screen.fill((20, 20, 30))

        # Draw DENSO logo area
        logo_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 80, 200, 60)
        pygame.draw.rect(screen, DENSO_RED, logo_rect, border_radius=5)
        pygame.draw.rect(screen, (255, 255, 255), logo_rect, width=2, border_radius=5)

        # Center DENSO text in logo
        title_rect = texts["title"].get_rect(center=logo_rect.center)
        screen.blit(texts["title"], title_rect)

        # Draw error message
        error_rect = texts["error"].get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(texts["error"], error_rect)

        # Draw status
        status_rect = texts["status"].get_rect(center=(SCREEN_WIDTH // 2, 230))
        screen.blit(texts["status"], status_rect)

        # Draw help text
        help1_rect = texts["help1"].get_rect(center=(SCREEN_WIDTH // 2, 300))
        screen.blit(texts["help1"], help1_rect)

        help2_rect = texts["help2"].get_rect(center=(SCREEN_WIDTH // 2, 330))
        screen.blit(texts["help2"], help2_rect)

        # Draw copyright
        copyright_rect = texts["copyright"].get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)
        )
        screen.blit(texts["copyright"], copyright_rect)

        pygame.display.flip()
        clock.tick(60)

    return None


def main():
    """Enhanced main function with comprehensive error handling and environment support"""
    # Initialize basic logging first
    logger = setup_logger(
        console_level=getattr(
            logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO
        )
    )
    logger.info("DENSO Tetris starting...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")

    try:
        # Check environment and dependencies
        if not check_environment():
            logger.error("Environment check failed")
            sys.exit(1)

        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")

        # Initialize pygame
        logger.info("Initializing Pygame...")
        pygame.init()

        # Verify pygame initialization
        if not pygame.get_init():
            raise RuntimeError("Pygame initialization failed")

        # Create display
        display_flags = 0
        if config["screen"]["fullscreen"]:
            display_flags |= pygame.FULLSCREEN
        if config["screen"]["vsync"]:
            display_flags |= pygame.DOUBLEBUF

        screen = pygame.display.set_mode(
            (config["screen"]["width"], config["screen"]["height"]), display_flags
        )
        pygame.display.set_caption(os.getenv("GAME_TITLE", TITLE))
        logger.info(
            f"Display initialized: {config['screen']['width']}x{config['screen']['height']}"
        )

        # Set window icon
        try:
            icon_path = "assets/images/icon.png"
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path)
                pygame.display.set_icon(icon)
                logger.debug("Window icon set successfully")
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")

        # Create assets directory structure
        ensure_assets_directory()

        # Initialize database
        db_initialized = initialize_database()
        if not db_initialized:
            logger.warning(
                "Database initialization failed - some features may be limited"
            )

        # Create main menu or fallback
        current_scene = None
        try:
            current_scene = MainMenu(screen, config)
            logger.info("Main menu initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize main menu: {e}")
            logger.debug(traceback.format_exc())
            current_scene = fallback_menu(screen, config)
            if current_scene is None:
                logger.info("User chose to exit from fallback menu")
                return

        # Main game loop with enhanced error handling
        clock = pygame.time.Clock()
        running = True
        last_time = time.time()
        frame_count = 0
        fps_check_time = time.time()

        # Performance monitoring
        target_fps = config["screen"]["target_fps"]
        performance_warning_threshold = (
            target_fps * 0.8
        )  # Warn if FPS drops below 80% of target

        logger.info("Entering main game loop")

        while running:
            try:
                # Time management
                current_time = time.time()
                delta_time = current_time - last_time
                last_time = current_time

                # Limit delta time to prevent huge jumps
                delta_time = min(delta_time, 1.0 / 20)  # Max 20 FPS minimum

                # Process events
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        running = False
                        logger.info("Quit event received")
                    elif event.type == pygame.KEYDOWN:
                        # Global keyboard shortcuts
                        if event.key == pygame.K_F4 and (event.mod & pygame.KMOD_ALT):
                            running = False
                            logger.info("Alt+F4 pressed")
                        elif event.key == pygame.K_F11:
                            # Toggle fullscreen
                            config["screen"]["fullscreen"] = not config["screen"][
                                "fullscreen"
                            ]
                            if config["screen"]["fullscreen"]:
                                screen = pygame.display.set_mode(
                                    (
                                        config["screen"]["width"],
                                        config["screen"]["height"],
                                    ),
                                    pygame.FULLSCREEN,
                                )
                            else:
                                screen = pygame.display.set_mode(
                                    (
                                        config["screen"]["width"],
                                        config["screen"]["height"],
                                    )
                                )
                            logger.info(
                                f"Fullscreen toggled: {config['screen']['fullscreen']}"
                            )

                    # Pass event to current scene
                    if current_scene and hasattr(current_scene, "handle_event"):
                        try:
                            current_scene.handle_event(event)
                        except Exception as e:
                            logger.error(f"Error handling event in scene: {e}")

                # Update current scene
                if current_scene and hasattr(current_scene, "update"):
                    try:
                        next_scene = current_scene.update(delta_time)
                        if next_scene:
                            current_scene = next_scene
                            logger.debug("Scene transition occurred")
                    except Exception as e:
                        logger.error(f"Error updating scene: {e}")
                        logger.debug(traceback.format_exc())
                        # Try to recover by going to fallback menu
                        current_scene = fallback_menu(screen, config)
                        if current_scene is None:
                            running = False

                # Clear screen
                screen.fill(UI_BG)

                # Render current scene
                if current_scene and hasattr(current_scene, "render"):
                    try:
                        current_scene.render()
                    except Exception as e:
                        logger.error(f"Error rendering scene: {e}")
                        logger.debug(traceback.format_exc())
                        # Draw error message
                        try:
                            font = pygame.font.SysFont("Arial", 24)
                            error_text = font.render(
                                "Rendering Error - Check Logs", True, (255, 100, 100)
                            )
                            screen.blit(error_text, (50, 50))
                        except:
                            pass

                # Update display
                try:
                    pygame.display.flip()
                except Exception as e:
                    logger.error(f"Display update error: {e}")

                # Frame rate control
                try:
                    clock.tick(target_fps)
                except Exception as e:
                    logger.error(f"Clock tick error: {e}")

                # Performance monitoring
                frame_count += 1
                if (
                    frame_count % 300 == 0
                ):  # Check every 300 frames (about 5 seconds at 60 FPS)
                    elapsed = current_time - fps_check_time
                    if elapsed > 0:
                        current_fps = frame_count / elapsed
                        if current_fps < performance_warning_threshold:
                            logger.warning(
                                f"Performance warning: FPS dropped to {current_fps:.1f}"
                            )

                        frame_count = 0
                        fps_check_time = current_time

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                running = False
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                logger.debug(traceback.format_exc())
                # Try to continue for one more iteration
                time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Game terminated by user (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        logger.debug(traceback.format_exc())
        show_crash_screen(str(e))
    finally:
        # Cleanup
        logger.info("Shutting down DENSO Tetris...")
        try:
            pygame.quit()
        except:
            pass
        logger.info("Shutdown complete")


if __name__ == "__main__":
    # Set process title if available
    try:
        import setproctitle

        setproctitle.setproctitle("denso-tetris")
    except ImportError:
        pass

    main()
