#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Auth Utilities
----------------------------
ฟังก์ชันสำหรับตรวจสอบสิทธิ์ผู้ใช้และระบบความปลอดภัย
"""

import bcrypt
import hashlib
import random
import string
import logging

from db.queries import authenticate_user, register_user
from utils.logger import get_logger


logger = get_logger("tetris.auth")


def hash_password(password):
    """
    แฮชรหัสผ่านด้วย bcrypt

    Args:
        password (str): รหัสผ่านที่ต้องการแฮช

    Returns:
        str: รหัสผ่านที่ถูกแฮชแล้ว
    """
    try:
        # แฮชรหัสผ่านด้วย bcrypt
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการแฮชรหัสผ่าน: {e}")
        return None


def verify_password(password, hashed_password):
    """
    ตรวจสอบรหัสผ่านกับรหัสผ่านที่ถูกแฮชไว้

    Args:
        password (str): รหัสผ่านที่ต้องการตรวจสอบ
        hashed_password (str): รหัสผ่านที่ถูกแฮชไว้

    Returns:
        bool: True ถ้ารหัสผ่านถูกต้อง
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการตรวจสอบรหัสผ่าน: {e}")
        return False


def generate_session_id():
    """
    สร้าง Session ID แบบสุ่ม

    Returns:
        str: Session ID
    """
    # สร้างสตริงแบบสุ่ม
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=32))

    # แฮชด้วย SHA-256
    return hashlib.sha256(random_string.encode("utf-8")).hexdigest()


def login_user(username, password):
    """
    ล็อกอินผู้ใช้

    Args:
        username (str): ชื่อผู้ใช้
        password (str): รหัสผ่าน

    Returns:
        dict: ข้อมูลผู้ใช้หรือ None ถ้าล็อกอินไม่สำเร็จ
    """
    try:
        # ตรวจสอบสิทธิ์
        if authenticate_user(username, password):
            # ล็อกอินสำเร็จ
            session_id = generate_session_id()

            # สร้างข้อมูลผู้ใช้
            user_data = {
                "username": username,
                "session_id": session_id,
                "logged_in": True,
            }

            logger.info(f"ผู้ใช้ {username} ล็อกอินสำเร็จ")
            return user_data
        else:
            logger.warning(f"ล็อกอินไม่สำเร็จสำหรับผู้ใช้ {username}")
            return None
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการล็อกอิน: {e}")
        return None


def create_user(username, password):
    """
    สร้างผู้ใช้ใหม่

    Args:
        username (str): ชื่อผู้ใช้
        password (str): รหัสผ่าน

    Returns:
        bool: True ถ้าสร้างผู้ใช้สำเร็จ
    """
    try:
        # ตรวจสอบความถูกต้องของข้อมูล
        if not username or not password:
            logger.warning("ชื่อผู้ใช้หรือรหัสผ่านว่างเปล่า")
            return False

        if len(password) < 6:
            logger.warning("รหัสผ่านสั้นเกินไป (ต้องมีอย่างน้อย 6 ตัวอักษร)")
            return False

        # ลงทะเบียนผู้ใช้
        return register_user(username, password)
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการสร้างผู้ใช้: {e}")
        return False
