#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Session
-----------------------------
Manage database sessions and connections with improved error handling
"""

import os
import yaml
import logging
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

from db.models import Base

# Global variables for database session
engine = None
Session = None
logger = logging.getLogger("tetris.db")


def load_db_config():
    """
    Load database configuration from config file with error handling

    Returns:
        dict: Database configuration
    """
    try:
        # Look for config file
        if os.path.exists("config.yaml"):
            with open("config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config["database"]
        else:
            logger.warning("config.yaml not found, using default database settings")
    except Exception as e:
        logger.error(f"Could not load database configuration: {e}")

    # Default config if loading fails
    return {"engine": "sqlite", "sqlite": {"path": "./tetris.db"}}


def init_db():
    """Initialize database connection and create tables with error handling"""
    global engine, Session

    # โหลดการตั้งค่า
    db_config = load_db_config()
    db_engine = db_config.get("engine", "sqlite")

    try:
        # สร้าง database URI
        if db_engine == "sqlite":
            db_path = db_config["sqlite"]["path"]

            # สร้างไดเร็กทอรีถ้าไม่มี
            db_dir = os.path.dirname(os.path.abspath(db_path))
            os.makedirs(db_dir, exist_ok=True)

            db_uri = f"sqlite:///{db_path}"

            # ตรวจสอบว่าสามารถเขียนไปยังตำแหน่งนี้ได้หรือไม่
            try:
                # ทดสอบว่าสามารถเปิดฐานข้อมูล SQLite ได้
                temp_conn = sqlite3.connect(db_path)
                temp_conn.close()
            except Exception as e:
                logger.error(f"ไม่สามารถเข้าถึงฐานข้อมูล SQLite ที่ {db_path}: {e}")
                # ใช้ฐานข้อมูลในหน่วยความจำแทน
                db_uri = "sqlite:///:memory:"
                logger.warning("เปลี่ยนไปใช้ฐานข้อมูล SQLite ในหน่วยความจำแทน")

        # สร้าง Engine พร้อมการจัดการพูลการเชื่อมต่อ
        engine = create_engine(
            db_uri,
            connect_args={"check_same_thread": False} if db_engine == "sqlite" else {},
            echo=False,  # Set to True for SQL debugging
        )

        # สร้างตาราง
        try:
            Base.metadata.create_all(engine)
        except Exception as e:
            logger.error(f"เกิดข้อผิดพลาดในการสร้างตารางฐานข้อมูล: {e}")

        # สร้าง session factory
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)

        logger.info(f"เชื่อมต่อกับฐานข้อมูล: {db_engine}")
        return True
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับฐานข้อมูล: {e}")
        # ใช้ SQLite in-memory เป็น fallback
        try:
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            session_factory = sessionmaker(bind=engine)
            Session = scoped_session(session_factory)
            logger.warning("ใช้ฐานข้อมูล SQLite ในหน่วยความจำเป็น fallback")
            return True
        except:
            logger.critical("ไม่สามารถสร้างฐานข้อมูลสำรองได้")
            return False


def check_database_connection():
    """
    ตรวจสอบว่าการเชื่อมต่อฐานข้อมูลทำงานอยู่หรือไม่

    Returns:
        bool: True ถ้าการเชื่อมต่อทำงาน
    """
    if not Session:
        return False

    session = None
    try:
        session = get_session()
        # ลองคิวรี่อย่างง่าย
        session.execute("SELECT 1")
        logger.info("การเชื่อมต่อฐานข้อมูลทำงานได้ปกติ")
        return True

    except Exception as e:
        logger.error(f"ข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {e}")
        return False
    finally:
        if session:
            try:
                close_session(session)
            except:
                pass


def get_session():
    """Get a database session with improved error handling"""
    global engine, Session

    if Session is None:
        init_db()

    if not engine or not Session:
        logger.error("Database not initialized properly")
        return None

    try:
        session = Session()
        # Verify connection is working
        session.execute("SELECT 1")
        return session
    except Exception as e:
        logger.error(f"Error creating database session: {e}")
        # Try to reinitialize
        init_db()
        try:
            return Session()
        except Exception as e2:
            logger.critical(f"Could not recreate session after reinitialization: {e2}")
            return None


def close_session(session):
    """Close database session safely"""
    if session:
        try:
            session.commit()
        except Exception as e:
            logger.error(f"Error committing session: {e}")
            try:
                session.rollback()
            except:
                pass
        finally:
            try:
                session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")
