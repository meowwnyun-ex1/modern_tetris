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
from pathlib import Path
from contextlib import contextmanager

try:
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy.pool import QueuePool
    from sqlalchemy.exc import SQLAlchemyError

    # Check if SQLAlchemy is properly installed
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    from db.models import Base
except ImportError:
    # This may fail if models.py doesn't exist yet
    Base = None

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
        # Look for config file in both the current directory and one level up
        config_paths = [Path("config.yaml"), Path("../config.yaml")]
        config_file = None

        for path in config_paths:
            if path.exists():
                config_file = path
                break

        if config_file:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("database", {})
        else:
            logger.warning("config.yaml not found, using default database settings")
    except Exception as e:
        logger.error(f"Could not load database configuration: {e}")

    # Default config if loading fails
    return {"engine": "sqlite", "sqlite": {"path": "./tetris.db"}}


def init_db():
    """Initialize database connection and create tables with error handling"""
    global engine, Session

    if not SQLALCHEMY_AVAILABLE:
        logger.error("SQLAlchemy is not installed. Database functionality is disabled.")
        return False

    if Base is None:
        logger.error(
            "Database models could not be imported. Database functionality is disabled."
        )
        return False

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
                # Use context manager for proper cleanup
                with sqlite3.connect(db_path) as temp_conn:
                    pass
                db_uri = f"sqlite:///{db_path}"
                logger.info(f"Using SQLite database at {db_path}")
            except Exception as e:
                logger.error(f"Cannot access SQLite at {db_path}: {e}")
                db_uri = "sqlite:///:memory:"
                logger.warning("Using in-memory SQLite as fallback")
        else:
            logger.warning(
                f"Unsupported database engine '{db_engine}', using SQLite instead"
            )
            db_uri = "sqlite:///:memory:"

        # Create engine with connection pool
        engine = create_engine(
            db_uri,
            connect_args={"check_same_thread": False} if db_engine == "sqlite" else {},
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            echo=False,
        )

        # Add SQLite optimizations
        if db_engine == "sqlite":

            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                """Set SQLite pragmas for better performance"""
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        # Create tables
        try:
            Base.metadata.create_all(engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

        # Create session factory
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
        logger.info("Database session factory initialized")

        return True

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Try in-memory SQLite as last resort
        try:
            engine = create_engine("sqlite:///:memory:")
            if Base is not None:
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
    Check if database connection is working

    Returns:
        bool: True if connection is working
    """
    if not SQLALCHEMY_AVAILABLE:
        return False

    if not Session:
        return False

    session = None
    try:
        session = get_session()
        # Try a simple query
        session.execute("SELECT 1")
        logger.info("Database connection successful")
        return True

    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False
    finally:
        if session:
            try:
                close_session(session)
            except:
                pass


def get_session():
    """
    Get a database session with improved error handling

    Returns:
        sqlalchemy.orm.Session: Database session or None if initialization fails
    """
    global engine, Session

    if not SQLALCHEMY_AVAILABLE:
        logger.error("SQLAlchemy is not installed. Cannot create database session.")
        return None

    if Session is None:
        if not init_db():
            return None

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
        if init_db():
            try:
                return Session()
            except Exception as e2:
                logger.critical(
                    f"Could not recreate session after reinitialization: {e2}"
                )
                return None
        return None


def close_session(session):
    """
    Safely close a database session

    Args:
        session: SQLAlchemy session to close
    """
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
            except:
                pass


@contextmanager
def session_scope():
    """
    Context manager for database sessions with automatic commit/rollback

    Usage:
        with session_scope() as session:
            # Do database operations
            session.add(some_object)
            # No need to commit or handle errors

    Yields:
        sqlalchemy.orm.Session: Database session
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("SQLAlchemy is not installed. Cannot create session scope.")
        yield None
        return

    session = None
    try:
        session = get_session()
        if session is None:
            logger.error("Failed to get database session")
            yield None
            return

        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Error in database session: {e}")
        if session:
            try:
                session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error rolling back session: {rollback_error}")
        raise
    finally:
        if session:
            try:
                session.close()
            except Exception as close_error:
                logger.error(f"Error closing session: {close_error}")
