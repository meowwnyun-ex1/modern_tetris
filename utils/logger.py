#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Logger
--------------------
ฟังก์ชันสำหรับการตั้งค่าและใช้งานระบบบันทึก log
"""

import os
import logging
import datetime


def setup_logger():
    """ตั้งค่าระบบบันทึก log"""
    # สร้างโฟลเดอร์ logs ถ้ายังไม่มี
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # กำหนดชื่อไฟล์ log ด้วยวันที่และเวลาปัจจุบัน
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"tetris_{current_time}.log")

    # กำหนดรูปแบบข้อความ log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ตั้งค่า root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),  # แสดงใน console ด้วย
        ],
    )

    # สร้าง logger สำหรับเกม
    game_logger = logging.getLogger("tetris")
    game_logger.setLevel(logging.INFO)

    # แจ้งว่าเริ่มต้นระบบ log แล้ว
    game_logger.info(f"เริ่มต้นระบบ logging ที่ {current_time}")


def get_logger(name="tetris"):
    """
    รับอ็อบเจกต์ logger

    Args:
        name (str, optional): ชื่อของ logger

    Returns:
        logging.Logger: อ็อบเจกต์ logger
    """
    return logging.getLogger(name)
