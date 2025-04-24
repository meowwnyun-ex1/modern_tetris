#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Database Models
-----------------------------
โมเดลฐานข้อมูลสำหรับการบันทึกสถิติผู้เล่น
"""

import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """โมเดลข้อมูลผู้ใช้"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)  # เก็บแฮชรหัสผ่าน
    created_at = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"<User(username='{self.username}')>"


class GameScore(Base):
    """โมเดลข้อมูลคะแนนเกม"""

    __tablename__ = "game_scores"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    score = Column(Integer, default=0)
    level = Column(Integer, default=1)
    lines_cleared = Column(Integer, default=0)
    time_played = Column(Float, default=0.0)  # เวลาที่เล่นเป็นวินาที
    timestamp = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"<GameScore(username='{self.username}', score={self.score}, level={self.level})>"


class GameSettings(Base):
    """โมเดลข้อมูลการตั้งค่าของผู้เล่น"""

    __tablename__ = "game_settings"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    theme = Column(String(20), default="neon")
    music_volume = Column(Float, default=0.7)
    sfx_volume = Column(Float, default=0.8)
    show_ghost = Column(Integer, default=1)  # 1 = เปิด, 0 = ปิด
    controls = Column(String(500), default="{}")  # เก็บเป็น JSON
    timestamp = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"<GameSettings(username='{self.username}', theme='{self.theme}')>"


class Achievement(Base):
    """โมเดลข้อมูลความสำเร็จ"""

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    achievement_id = Column(String(50), nullable=False)
    achievement_name = Column(String(100), nullable=False)
    description = Column(String(200))
    achieved_at = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"<Achievement(username='{self.username}', achievement='{self.achievement_name}')>"


# ความสัมพันธ์ m2m ระหว่าง User และ Achievement สามารถทำได้โดยใช้ ForeignKey
# แต่สำหรับตัวอย่างนี้เราเก็บด้วย username เพื่อความเรียบง่าย
