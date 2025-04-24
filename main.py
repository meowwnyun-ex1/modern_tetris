#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Main Application
-------------------------------
เกม Tetris สมัยใหม่ที่มีเอฟเฟกต์สวยงามและระบบการเก็บสถิติผู้เล่น
"""

import os
import sys
import yaml
import logging
import pygame
from pygame.locals import *

# Import internal modules
from core.game import Game
from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE
from ui.menu import MainMenu
from utils.logger import setup_logger
from db.session import init_db


def load_config():
    """โหลดไฟล์การตั้งค่าจาก config.yaml"""
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"ไม่สามารถโหลดไฟล์ config: {e}")
        return {}


def main():
    """ฟังก์ชันหลักของโปรแกรม"""
    # ตั้งค่า logging
    setup_logger()
    logger = logging.getLogger("tetris")
    logger.info("เริ่มต้นแอปพลิเคชัน Modern Tetris")

    # โหลดไฟล์การตั้งค่า
    config = load_config()

    # เตรียมฐานข้อมูล
    init_db()

    # เริ่มต้น Pygame
    pygame.init()
    pygame.mixer.init()

    # ตั้งค่าหน้าต่าง
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)

    # ตั้งค่า Clock สำหรับควบคุม FPS
    clock = pygame.time.Clock()

    # สร้าง MainMenu
    main_menu = MainMenu(screen, config)

    # เริ่มต้นลูปหลัก
    running = True
    current_scene = main_menu

    while running:
        dt = clock.tick(60) / 1000.0  # แปลงเป็นวินาทีเพื่อให้ง่ายต่อการคำนวณ

        # ตรวจสอบอินพุต
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            current_scene.handle_event(event)

        # อัปเดตสถานะ
        next_scene = current_scene.update(dt)
        if next_scene:
            # เปลี่ยนซีนถ้ามีการร้องขอ
            current_scene = next_scene

        # วาดกราฟิก
        current_scene.render()

        # อัปเดตหน้าจอ
        pygame.display.flip()

    # ทำความสะอาดและปิดโปรแกรม
    logger.info("กำลังปิดแอปพลิเคชัน")
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
