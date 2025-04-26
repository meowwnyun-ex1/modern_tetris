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

    try:
        # Load config
        db_config = load_db_config()
        db_engine = db_config.get("engine", "sqlite")

        # Create database URI
        if db_engine == "sqlite":
            db_path = db_config["sqlite"]["path"]

            # Create directory if needed
            db_dir = os.path.dirname(os.path.abspath(db_path))
            os.makedirs(db_dir, exist_ok=True)

            # Test SQLite access
            try:
                temp_conn = sqlite3.connect(db_path)
                temp_conn.close()
                db_uri = f"sqlite:///{db_path}"
            except Exception as e:
                logger.error(f"Cannot access SQLite at {db_path}: {e}")
                db_uri = "sqlite:///:memory:"
                logger.warning("Using in-memory SQLite as fallback")

        # Create engine with connection pool
        engine = create_engine(
            db_uri,
            connect_args={"check_same_thread": False} if db_engine == "sqlite" else {},
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            echo=False,
        )

        # Create tables
        try:
            Base.metadata.create_all(engine)
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

        # Create session factory
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)

        return True

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Try in-memory SQLite as last resort
        try:
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            session_factory = sessionmaker(bind=engine)
            Session = scoped_session(session_factory)
            logger.warning("Using in-memory SQLite database")
            return True
        except Exception as e2:
            logger.critical(f"Could not create fallback database: {e2}")
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
    if session:
        try:
            session.commit()
        except Exception as e:
            logger.error(f"Error committing session: {e}")
            session.rollback()
        finally:
            session.close()
