#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Database Queries
------------------------------
คำสั่ง SQL สำหรับการดึงข้อมูลและบันทึกข้อมูล
"""

import logging
import datetime
import bcrypt
from sqlalchemy import desc

from db.session import get_session, close_session
from db.models import User, GameScore, GameSettings, Achievement

logger = logging.getLogger("tetris.db")


def register_user(username, password):
    """
    ลงทะเบียนผู้ใช้ใหม่

    Args:
        username (str): ชื่อผู้ใช้
        password (str): รหัสผ่าน

    Returns:
        bool: True ถ้าลงทะเบียนสำเร็จ
    """
    session = get_session()
    try:
        # ตรวจสอบว่าชื่อผู้ใช้มีอยู่แล้วหรือไม่
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            logger.warning(f"ชื่อผู้ใช้ {username} มีอยู่แล้ว")
            return False

        # เข้ารหัสรหัสผ่าน
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # สร้างผู้ใช้ใหม่
        new_user = User(username=username, password_hash=password_hash)
        session.add(new_user)
        session.commit()

        logger.info(f"ลงทะเบียนผู้ใช้ {username} สำเร็จ")
        return True

    except Exception as e:
        session.rollback()
        logger.error(f"เกิดข้อผิดพลาดในการลงทะเบียนผู้ใช้: {e}")
        return False
    finally:
        close_session(session)


def authenticate_user(username, password):
    """
    ตรวจสอบสิทธิ์ผู้ใช้

    Args:
        username (str): ชื่อผู้ใช้
        password (str): รหัสผ่าน

    Returns:
        bool: True ถ้าตรวจสอบสิทธิ์สำเร็จ
    """
    session = get_session()
    try:
        # ค้นหาผู้ใช้
        user = session.query(User).filter_by(username=username).first()
        if not user:
            logger.warning(f"ไม่พบผู้ใช้ {username}")
            return False

        # ตรวจสอบรหัสผ่าน
        return bcrypt.checkpw(
            password.encode("utf-8"), user.password_hash.encode("utf-8")
        )

    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการตรวจสอบสิทธิ์ผู้ใช้: {e}")
        return False
    finally:
        close_session(session)


def save_game_score(username, score, level, lines, time_played):
    """
    บันทึกคะแนนเกม

    Args:
        username (str): ชื่อผู้ใช้
        score (int): คะแนน
        level (int): ระดับ
        lines (int): จำนวนแถวที่ล้าง
        time_played (float): เวลาที่เล่น (วินาที)

    Returns:
        bool: True ถ้าบันทึกสำเร็จ
    """
    session = get_session()
    try:
        # สร้างรายการคะแนนใหม่
        new_score = GameScore(
            username=username,
            score=score,
            level=level,
            lines_cleared=lines,
            time_played=time_played,
            timestamp=datetime.datetime.now(),
        )
        session.add(new_score)
        session.commit()

        logger.info(f"บันทึกคะแนน {score} สำหรับผู้ใช้ {username} สำเร็จ")
        return True

    except Exception as e:
        session.rollback()
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกคะแนน: {e}")
        return False
    finally:
        close_session(session)


def get_top_scores(limit=10):
    """
    ดึงคะแนนสูงสุด

    Args:
        limit (int): จำนวนรายการที่ต้องการ

    Returns:
        list: รายการคะแนนสูงสุด
    """
    session = get_session()
    try:
        # ดึงคะแนนสูงสุด
        scores = (
            session.query(GameScore).order_by(desc(GameScore.score)).limit(limit).all()
        )
        return scores

    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงคะแนนสูงสุด: {e}")
        return []
    finally:
        close_session(session)


def get_user_best_score(username):
    """
    ดึงคะแนนสูงสุดของผู้ใช้

    Args:
        username (str): ชื่อผู้ใช้

    Returns:
        GameScore: รายการคะแนนสูงสุด
    """
    session = get_session()
    try:
        # ดึงคะแนนสูงสุดของผู้ใช้
        score = (
            session.query(GameScore)
            .filter_by(username=username)
            .order_by(desc(GameScore.score))
            .first()
        )
        return score

    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงคะแนนสูงสุดของผู้ใช้: {e}")
        return None
    finally:
        close_session(session)


def save_user_settings(username, settings):
    """
    บันทึกการตั้งค่าของผู้ใช้

    Args:
        username (str): ชื่อผู้ใช้
        settings (dict): การตั้งค่า

    Returns:
        bool: True ถ้าบันทึกสำเร็จ
    """
    session = get_session()
    try:
        # ตรวจสอบว่ามีการตั้งค่าอยู่แล้วหรือไม่
        user_settings = session.query(GameSettings).filter_by(username=username).first()

        if user_settings:
            # อัปเดตการตั้งค่าที่มีอยู่
            user_settings.theme = settings.get("theme", user_settings.theme)
            user_settings.music_volume = settings.get(
                "music_volume", user_settings.music_volume
            )
            user_settings.sfx_volume = settings.get(
                "sfx_volume", user_settings.sfx_volume
            )
            user_settings.show_ghost = settings.get(
                "show_ghost", user_settings.show_ghost
            )
            user_settings.controls = settings.get("controls", user_settings.controls)
            user_settings.timestamp = datetime.datetime.now()
        else:
            # สร้างการตั้งค่าใหม่
            user_settings = GameSettings(
                username=username,
                theme=settings.get("theme", "neon"),
                music_volume=settings.get("music_volume", 0.7),
                sfx_volume=settings.get("sfx_volume", 0.8),
                show_ghost=settings.get("show_ghost", 1),
                controls=settings.get("controls", "{}"),
            )
            session.add(user_settings)

        session.commit()
        logger.info(f"บันทึกการตั้งค่าสำหรับผู้ใช้ {username} สำเร็จ")
        return True

    except Exception as e:
        session.rollback()
        logger.error(f"เกิดข้อผิดพลาดในการบันทึกการตั้งค่า: {e}")
        return False
    finally:
        close_session(session)


def get_user_settings(username):
    """
    ดึงการตั้งค่าของผู้ใช้

    Args:
        username (str): ชื่อผู้ใช้

    Returns:
        GameSettings: การตั้งค่าของผู้ใช้
    """
    session = get_session()
    try:
        # ดึงการตั้งค่าของผู้ใช้
        settings = session.query(GameSettings).filter_by(username=username).first()
        return settings

    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงการตั้งค่าของผู้ใช้: {e}")
        return None
    finally:
        close_session(session)


def unlock_achievement(username, achievement_id, achievement_name, description):
    """
    ปลดล็อคความสำเร็จ

    Args:
        username (str): ชื่อผู้ใช้
        achievement_id (str): รหัสความสำเร็จ
        achievement_name (str): ชื่อความสำเร็จ
        description (str): คำอธิบายความสำเร็จ

    Returns:
        bool: True ถ้าปลดล็อคสำเร็จ
    """
    session = get_session()
    try:
        # ตรวจสอบว่าปลดล็อคไปแล้วหรือไม่
        existing = (
            session.query(Achievement)
            .filter_by(username=username, achievement_id=achievement_id)
            .first()
        )

        if existing:
            logger.info(f"ความสำเร็จ {achievement_id} ถูกปลดล็อคไปแล้ว")
            return False

        # สร้างความสำเร็จใหม่
        new_achievement = Achievement(
            username=username,
            achievement_id=achievement_id,
            achievement_name=achievement_name,
            description=description,
            achieved_at=datetime.datetime.now(),
        )
        session.add(new_achievement)
        session.commit()

        logger.info(f"ปลดล็อคความสำเร็จ {achievement_name} สำหรับผู้ใช้ {username} สำเร็จ")
        return True

    except Exception as e:
        session.rollback()
        logger.error(f"เกิดข้อผิดพลาดในการปลดล็อคความสำเร็จ: {e}")
        return False
    finally:
        close_session(session)


def get_user_achievements(username):
    """
    ดึงความสำเร็จของผู้ใช้

    Args:
        username (str): ชื่อผู้ใช้

    Returns:
        list: รายการความสำเร็จของผู้ใช้
    """
    session = get_session()
    try:
        # ดึงความสำเร็จของผู้ใช้
        achievements = (
            session.query(Achievement)
            .filter_by(username=username)
            .order_by(Achievement.achieved_at)
            .all()
        )
        return achievements

    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงความสำเร็จของผู้ใช้: {e}")
        return []
    finally:
        close_session(session)
