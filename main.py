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
import pygame
import traceback
import time
from pygame.locals import *

# Import internal modules
from core.game import Game
from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, UI_BG, DENSO_RED
from ui.menu import MainMenu
from utils.logger import setup_logger
from db.session import init_db


def ensure_assets_directory():
    """Ensure all required directories exist with improved asset creation"""
    # สร้างโครงสร้างไดเร็กทอรีที่จำเป็น
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

    # สร้างไฟล์ assets ที่จำเป็นแบบทยอยสร้าง
    create_important_assets()


def create_important_assets():
    """Create minimal required assets to prevent errors"""
    # สร้างไอคอนขนาดเล็ก
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

    # สร้างไฟล์ dummy สำหรับเสียงหลัก
    try:
        create_empty_sound("assets/sounds/menu_select.wav")
        create_empty_sound("assets/sounds/game_over.wav")
        create_empty_sound("assets/sounds/menu_theme.mp3")
    except Exception as e:
        logger.error(f"Could not create dummy sounds: {e}")


def create_empty_sound(filename):
    """Create an empty sound file to prevent errors"""
    if os.path.exists(filename):
        return

    try:
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok=True)

        # สร้างไฟล์เปล่า
        with open(filename, "wb") as f:
            # เขียนข้อมูลเปล่าหรือ header อย่างง่าย
            if filename.endswith(".wav"):
                # สร้าง WAV header อย่างง่าย
                f.write(
                    b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
                )
            else:
                # สร้างไฟล์เปล่าสำหรับไฟล์อื่นๆ
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
        },
        "graphics": {
            "theme": "denso",
            "particles": True,
            "animations": True,
        },
        "audio": {
            "music_volume": 0.6,
            "sfx_volume": 0.7,
            "enable_music": True,
            "enable_sfx": True,
        },
        "ui": {
            "font": "arial",
            "language": "en",
            "show_fps": True,
        },
        "database": {"engine": "sqlite", "sqlite": {"path": "./tetris.db"}},
    }

    try:
        if os.path.exists("config.yaml"):
            with open("config.yaml", "r", encoding="utf-8") as f:
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
            with open("config.yaml", "w", encoding="utf-8") as f:
                yaml.dump(default_config, f, default_flow_style=False)

    except Exception as e:
        logging.error(f"Could not load config file: {e}")

    return default_config


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
    # ส่วนการเตรียมพร้อมและการสร้าง objects ต่างๆ
    # Initialize logger
    global logger
    logger = setup_logger("main")

    # Load configuration
    config = load_config()

    # Initialize pygame and create screen
    pygame.init()
    screen = pygame.display.set_mode(
        (config["screen"]["width"], config["screen"]["height"]),
        pygame.FULLSCREEN if config["screen"]["fullscreen"] else 0,
    )
    pygame.display.set_caption(TITLE)

    # ปรับปรุง main loop
    clock = pygame.time.Clock()  # Initialize clock
    running = True
    last_time = time.time()
    accumulated_time = 0
    fixed_time_step = 1.0 / config["screen"].get("target_fps", 60)

    try:
        while running:
            # วัดเวลาแบบควบคุมเอง แทนการพึ่งพา clock.tick() เพียงอย่างเดียว
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            # จำกัดการประมวลผลตามเฟรมเรต (ป้องกัน CPU throttling)
            delta_time = min(delta_time, 0.25)  # ไม่เกิน 250 ms
            accumulated_time += delta_time

            # ประมวลผลอินพุท
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                current_scene.handle_event(event)

            # เตรียมตัวแปรสำหรับติดตามจำนวนการอัพเดทแบบ fixed
            update_count = 0

            # Fixed update steps for consistent physics (จำกัดจำนวนการอัพเดท)
            while (
                accumulated_time >= fixed_time_step and update_count < 5
            ):  # จำกัดไม่ให้ update มากกว่า 5 ครั้งต่อเฟรม
                # Update state
                next_scene = current_scene.update(fixed_time_step)
                if next_scene:
                    # Change scene if requested
                    current_scene = next_scene
                    # Reset events to prevent carry-over
                    events.clear()

                accumulated_time -= fixed_time_step
                update_count += 1

            # หากยังมี accumulated_time เหลืออยู่มากแต่เกิน update limit แล้ว
            # ให้ยกเลิกส่วนที่เหลือทิ้งเพื่อป้องกันการเกิด spiral of death
            if update_count >= 5 and accumulated_time > fixed_time_step:
                logger.warning(
                    f"Dropping {accumulated_time:.4f}s of accumulated time to prevent lag spiral"
                )
                accumulated_time = 0

            # Fill background with base color before rendering
            screen.fill(UI_BG)

            # Render graphics
            current_scene.render()

            # Update display
            pygame.display.flip()

            # จำกัดเฟรมเรตด้วย clock (แต่ไม่พึ่งพาเพียงอย่างเดียว)
            try:
                clock.tick(config["screen"].get("target_fps", 60))
            except Exception as e:
                logger.error(f"Error in clock.tick(): {e}")

            # ให้ CPU ได้พักบ้าง
            if delta_time < fixed_time_step * 0.5:
                time.sleep(0.001)  # พัก 1 มิลลิวินาที หากการประมวลผลเร็วเกินไป

    except KeyboardInterrupt:
        logger.info("Game terminated by user (KeyboardInterrupt)")
    except Exception as e:
        logger.critical(f"Critical error in main loop: {e}\n{traceback.format_exc()}")
    finally:
        # Clean up and exit
        logger.info("Closing application")
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
