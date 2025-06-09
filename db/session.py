#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Session (Updated for Neon PostgreSQL)
-----------------------------------------------------------
Manage database sessions and connections with Neon support
"""

import os
import yaml
import logging
import time
from pathlib import Path
from contextlib import contextmanager

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

try:
    from sqlalchemy import create_engine, event, text
    from sqlalchemy.orm import sessionmaker, scoped_session
    from sqlalchemy.pool import QueuePool, StaticPool
    from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
    from sqlalchemy.engine import Engine
    import sqlite3

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

try:
    from db.models import Base
except ImportError:
    Base = None

# Global variables
engine = None
Session = None
logger = logging.getLogger("tetris.db")


def load_db_config():
    """
    Load database configuration with environment variable support

    Returns:
        dict: Database configuration
    """
    try:
        config_paths = [Path("config.yaml"), Path("../config.yaml")]
        config_file = None

        for path in config_paths:
            if path.exists():
                config_file = path
                break

        if config_file:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                db_config = config.get("database", {})

                # Replace environment variables in config
                if "postgresql" in db_config and "url" in db_config["postgresql"]:
                    url = db_config["postgresql"]["url"]
                    if url.startswith("${") and url.endswith("}"):
                        env_var = url[2:-1]
                        db_config["postgresql"]["url"] = os.getenv(env_var, "")

                return db_config
        else:
            logger.warning("config.yaml not found, using environment variables")
    except Exception as e:
        logger.error(f"Could not load database configuration: {e}")

    # Fallback to environment variables
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return {
            "engine": "postgresql",
            "postgresql": {
                "url": database_url,
                "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
                "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
                "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
                "echo": os.getenv("DB_ECHO", "false").lower() == "true",
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
            },
        }

    # Ultimate fallback to SQLite
    return {"engine": "sqlite", "sqlite": {"path": "./tetris.db"}}


def create_neon_engine(db_config):
    """
    Create PostgreSQL engine for Neon database

    Args:
        db_config (dict): Database configuration

    Returns:
        sqlalchemy.Engine: Database engine
    """
    pg_config = db_config["postgresql"]
    database_url = pg_config["url"]

    if not database_url:
        raise ValueError("DATABASE_URL is required for PostgreSQL connection")

    # Ensure SSL mode is set for Neon
    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url += f"{separator}sslmode=require"

    # Create engine with optimized settings for Neon
    engine_kwargs = {
        "url": database_url,
        "poolclass": QueuePool,
        "pool_size": pg_config.get("pool_size", 10),
        "max_overflow": pg_config.get("max_overflow", 20),
        "pool_timeout": pg_config.get("pool_timeout", 30),
        "pool_recycle": pg_config.get("pool_recycle", 3600),
        "pool_pre_ping": True,  # Important for cloud databases
        "echo": pg_config.get("echo", False),
        "connect_args": {
            "connect_timeout": pg_config.get("connect_timeout", 10),
            "command_timeout": pg_config.get("command_timeout", 30),
            "sslmode": "require",
        },
    }

    engine = create_engine(**engine_kwargs)

    # Add connection event listeners for Neon optimization
    @event.listens_for(engine, "connect")
    def set_postgresql_search_path(dbapi_connection, connection_record):
        """Set PostgreSQL optimizations for Neon"""
        try:
            with dbapi_connection.cursor() as cursor:
                # Set timezone to UTC
                cursor.execute("SET timezone = 'UTC'")
                # Optimize for Neon's architecture
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SET lock_timeout = '10s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
        except Exception as e:
            logger.warning(f"Could not set PostgreSQL optimizations: {e}")

    @event.listens_for(engine, "checkout")
    def ping_connection(dbapi_connection, connection_record, connection_proxy):
        """Ensure connection is alive on checkout"""
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            # Connection is dead, invalidate it
            connection_record.invalidate()
            raise DisconnectionError("Connection is no longer valid")

    return engine


def create_sqlite_engine(db_config):
    """
    Create SQLite engine as fallback

    Args:
        db_config (dict): Database configuration

    Returns:
        sqlalchemy.Engine: Database engine
    """
    sqlite_config = db_config.get("sqlite", {})
    db_path = sqlite_config.get("path", "./tetris.db")

    # Create directory if needed
    db_dir = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(db_dir, exist_ok=True)

    # Test SQLite access
    try:
        with sqlite3.connect(db_path) as temp_conn:
            temp_conn.execute("SELECT 1")
        db_uri = f"sqlite:///{db_path}"
        logger.info(f"Using SQLite database at {db_path}")
    except Exception as e:
        logger.error(f"Cannot access SQLite at {db_path}: {e}")
        db_uri = "sqlite:///:memory:"
        logger.warning("Using in-memory SQLite as fallback")

    engine = create_engine(
        db_uri,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": sqlite_config.get("pool_timeout", 20),
        },
        echo=sqlite_config.get("echo", False),
    )

    # SQLite optimizations
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set SQLite pragmas for better performance"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA temp_store=memory")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        cursor.close()

    return engine


def init_db():
    """Initialize database connection with automatic fallback"""
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
        # Load configuration
        db_config = load_db_config()
        db_engine_type = db_config.get("engine", "sqlite")

        logger.info(f"Attempting to initialize {db_engine_type} database...")

        # Try to create engine based on configuration
        if db_engine_type == "postgresql":
            try:
                engine = create_neon_engine(db_config)
                logger.info("Successfully connected to Neon PostgreSQL database")
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                logger.info("Falling back to SQLite...")
                engine = create_sqlite_engine({"sqlite": {"path": "./tetris.db"}})
        else:
            engine = create_sqlite_engine(db_config)

        # Test connection
        with engine.connect() as conn:
            if db_engine_type == "postgresql":
                conn.execute(text("SELECT version()"))
            else:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")

        # Create tables
        try:
            Base.metadata.create_all(engine)
            logger.info("Database tables created/verified successfully")
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

        # Last resort: in-memory SQLite
        try:
            logger.info("Attempting last resort: in-memory SQLite...")
            engine = create_engine("sqlite:///:memory:")
            if Base is not None:
                Base.metadata.create_all(engine)
            session_factory = sessionmaker(bind=engine)
            Session = scoped_session(session_factory)
            logger.warning("Using in-memory SQLite database (data will not persist)")
            return True
        except Exception as e2:
            logger.critical(f"Could not create fallback database: {e2}")
            return False


def get_session():
    """
    Get a database session with retry logic

    Returns:
        sqlalchemy.orm.Session: Database session or None if failed
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

    max_retries = 3
    for attempt in range(max_retries):
        try:
            session = Session()
            # Test the connection
            session.execute(text("SELECT 1"))
            return session
        except (OperationalError, DisconnectionError) as e:
            logger.warning(
                f"Database connection issue (attempt {attempt + 1}/{max_retries}): {e}"
            )
            if session:
                try:
                    session.close()
                except:
                    pass

            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
                # Try to reinitialize on last retry
                if attempt == max_retries - 2:
                    logger.info("Attempting to reinitialize database connection...")
                    if init_db():
                        continue
            else:
                logger.error("Failed to establish database connection after retries")
                return None
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            if session:
                try:
                    session.close()
                except:
                    pass
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
            session.add(some_object)
            # Automatic commit on success, rollback on error

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


def check_database_health():
    """
    Comprehensive database health check

    Returns:
        dict: Health check results
    """
    health_info = {
        "status": "unhealthy",
        "engine_type": "unknown",
        "connection_pool": {},
        "tables_exist": False,
        "last_error": None,
    }

    try:
        if not engine:
            health_info["last_error"] = "Database engine not initialized"
            return health_info

        # Get engine info
        health_info["engine_type"] = engine.dialect.name

        # Check connection pool
        pool = engine.pool
        health_info["connection_pool"] = {
            "size": getattr(pool, "size", lambda: 0)(),
            "checked_in": getattr(pool, "checkedin", lambda: 0)(),
            "checked_out": getattr(pool, "checkedout", lambda: 0)(),
            "overflow": getattr(pool, "overflow", lambda: 0)(),
        }

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()

            if test_value != 1:
                health_info["last_error"] = "Connection test failed"
                return health_info

        # Check if tables exist
        if Base:
            try:
                with engine.connect() as conn:
                    # Check if at least one table exists
                    if engine.dialect.name == "postgresql":
                        result = conn.execute(
                            text(
                                "SELECT COUNT(*) FROM information_schema.tables "
                                "WHERE table_schema = 'public'"
                            )
                        )
                    else:  # SQLite
                        result = conn.execute(
                            text(
                                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                            )
                        )

                    table_count = result.scalar()
                    health_info["tables_exist"] = table_count > 0
            except Exception as e:
                health_info["last_error"] = f"Table check failed: {e}"
                return health_info

        health_info["status"] = "healthy"
        logger.info("Database health check passed")

    except Exception as e:
        health_info["last_error"] = str(e)
        logger.error(f"Database health check failed: {e}")

    return health_info
