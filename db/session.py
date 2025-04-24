#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Database Session
-----------------------------
จัดการเซสชันและการเชื่อมต่อกับฐานข้อมูล
"""

import os
import yaml
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

from db.models import Base

# ตัวแปรส่วนกลางสำหรับเซสชันฐานข้อมูล
engine = None
Session = None
logger = logging.getLogger("tetris.db")


def load_db_config():
    """โหลดการตั้งค่าฐานข้อมูลจากไฟล์ config"""
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config["database"]
    except Exception as e:
        logger.error(f"ไม่สามารถโหลดการตั้งค่าฐานข้อมูลได้: {e}")
        # ใช้ค่าเริ่มต้น
        return {"engine": "sqlite", "sqlite": {"path": "./tetris.db"}}


def init_db():
    """เริ่มต้นการเชื่อมต่อกับฐานข้อมูลและสร้างตาราง"""
    global engine, Session

    # โหลดการตั้งค่า
    db_config = load_db_config()
    db_engine = db_config.get("engine", "sqlite")

    # สร้าง URI สำหรับเชื่อมต่อฐานข้อมูล
    if db_engine == "sqlite":
        db_path = db_config["sqlite"]["path"]
        # สร้างโฟลเดอร์หากไม่มี
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        db_uri = f"sqlite:///{db_path}"

    elif db_engine == "mysql":
        config = db_config["mysql"]
        db_uri = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

    elif db_engine == "postgresql":
        config = db_config["postgresql"]
        db_uri = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"

    else:
        # ใช้ SQLite เป็นค่าเริ่มต้น
        db_uri = "sqlite:///tetris.db"

    # สร้าง Engine
    try:
        engine = create_engine(
            db_uri,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False,
        )

        # สร้างตาราง
        Base.metadata.create_all(engine)

        # สร้างเซสชันแฟคทอรี
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)

        logger.info(f"เชื่อมต่อกับฐานข้อมูล {db_engine} สำเร็จ")

    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับฐานข้อมูล: {e}")
        # ใช้ SQLite ในหน่วยความจำเป็นแผนสำรอง
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)


def get_session():
    """รับอ็อบเจกต์เซสชัน"""
    if Session is None:
        init_db()
    return Session()


def close_session(session):
    """ปิดเซสชัน"""
    try:
        session.close()
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการปิดเซสชัน: {e}")
