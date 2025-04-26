#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Queries
------------------------------
SQL commands for retrieving and saving data with improved error handling
"""

import logging
import datetime
import bcrypt
import sqlite3
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

from db.session import get_session, close_session
from db.models import User, GameScore, GameSettings, Achievement

logger = logging.getLogger("tetris.db")


def register_user(username, password):
    """
    Register a new user with better validation

    Args:
        username (str): Username
        password (str): Password

    Returns:
        bool: True if registration was successful
    """
    if not username or not password:
        logger.warning("Registration failed: empty username or password")
        return False

    if len(password) < 6:
        logger.warning("Registration failed: password too short")
        return False

    session = get_session()
    try:
        # Check if username already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            logger.warning(f"Username {username} already exists")
            return False

        # Hash password
        try:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            return False

        # Create new user
        new_user = User(username=username, password_hash=password_hash)
        session.add(new_user)
        session.commit()

        logger.info(f"User {username} registered successfully")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error during user registration: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error during user registration: {e}")
        return False
    finally:
        close_session(session)


def authenticate_user(username, password):
    """
    Authenticate user with better error handling

    Args:
        username (str): Username
        password (str): Password

    Returns:
        bool: True if authentication was successful
    """
    if not username or not password:
        return False

    session = get_session()
    try:
        # Find user
        user = session.query(User).filter_by(username=username).first()
        if not user:
            logger.warning(f"Authentication failed: user {username} not found")
            return False

        # Check password
        try:
            is_valid = bcrypt.checkpw(
                password.encode("utf-8"), user.password_hash.encode("utf-8")
            )

            if is_valid:
                logger.info(f"User {username} authenticated successfully")
            else:
                logger.warning(
                    f"Authentication failed: incorrect password for {username}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    except SQLAlchemyError as e:
        logger.error(f"Database error during authentication: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return False
    finally:
        close_session(session)


def save_game_score(username, score, level, lines, time_played):
    """
    Save game score with validation

    Args:
        username (str): Username
        score (int): Score
        level (int): Level
        lines (int): Number of lines cleared
        time_played (float): Time played (seconds)

    Returns:
        bool: True if score was saved successfully
    """
    if not username:
        logger.warning("Cannot save score: no username provided")
        return False

    # Validate inputs
    try:
        score = int(score)
        level = int(level)
        lines = int(lines)
        time_played = float(time_played)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid score data: {e}")
        return False

    session = get_session()
    try:
        # Create new score entry
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

        logger.info(f"Score {score} for user {username} saved successfully")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error saving score: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving score: {e}")
        return False
    finally:
        close_session(session)


def get_top_scores(limit=10):
    """
    Get top scores with error handling

    Args:
        limit (int): Number of scores to retrieve

    Returns:
        list: List of top scores
    """
    session = get_session()
    try:
        # Get top scores
        scores = (
            session.query(GameScore).order_by(desc(GameScore.score)).limit(limit).all()
        )
        return scores

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving top scores: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving top scores: {e}")
        return []
    finally:
        close_session(session)


def get_user_best_score(username):
    """
    Get user's best score with error handling

    Args:
        username (str): Username

    Returns:
        GameScore: User's best score entry
    """
    if not username:
        return None

    session = get_session()
    try:
        # Get user's best score
        score = (
            session.query(GameScore)
            .filter_by(username=username)
            .order_by(desc(GameScore.score))
            .first()
        )
        return score

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving user's best score: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user's best score: {e}")
        return None
    finally:
        close_session(session)


def save_user_settings(username, settings):
    """
    Save user settings with validation

    Args:
        username (str): Username
        settings (dict): Settings

    Returns:
        bool: True if settings were saved successfully
    """
    if not username or not isinstance(settings, dict):
        return False

    session = get_session()
    try:
        # Check if settings already exist
        user_settings = session.query(GameSettings).filter_by(username=username).first()

        if user_settings:
            # Update existing settings
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
            # Create new settings
            user_settings = GameSettings(
                username=username,
                theme=settings.get("theme", "denso"),
                music_volume=settings.get("music_volume", 0.7),
                sfx_volume=settings.get("sfx_volume", 0.8),
                show_ghost=settings.get("show_ghost", 1),
                controls=settings.get("controls", "{}"),
            )
            session.add(user_settings)

        session.commit()
        logger.info(f"Settings for user {username} saved successfully")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error saving settings: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving settings: {e}")
        return False
    finally:
        close_session(session)


def get_user_settings(username):
    """
    Get user settings with error handling

    Args:
        username (str): Username

    Returns:
        GameSettings: User settings
    """
    if not username:
        return None

    session = get_session()
    try:
        # Get user settings
        settings = session.query(GameSettings).filter_by(username=username).first()
        return settings

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving user settings: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user settings: {e}")
        return None
    finally:
        close_session(session)


def unlock_achievement(username, achievement_id, achievement_name, description):
    """
    Unlock achievement with validation

    Args:
        username (str): Username
        achievement_id (str): Achievement ID
        achievement_name (str): Achievement name
        description (str): Achievement description

    Returns:
        bool: True if achievement was unlocked successfully
    """
    if not username or not achievement_id or not achievement_name:
        return False

    session = get_session()
    try:
        # Check if achievement already unlocked
        existing = (
            session.query(Achievement)
            .filter_by(username=username, achievement_id=achievement_id)
            .first()
        )

        if existing:
            logger.info(f"Achievement {achievement_id} already unlocked")
            return False

        # Create new achievement
        new_achievement = Achievement(
            username=username,
            achievement_id=achievement_id,
            achievement_name=achievement_name,
            description=description,
            achieved_at=datetime.datetime.now(),
        )
        session.add(new_achievement)
        session.commit()

        logger.info(f"Achievement {achievement_name} unlocked for user {username}")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error unlocking achievement: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error unlocking achievement: {e}")
        return False
    finally:
        close_session(session)


def get_user_achievements(username):
    """
    Get user achievements with error handling

    Args:
        username (str): Username

    Returns:
        list: List of user achievements
    """
    if not username:
        return []

    session = get_session()
    try:
        # Get user achievements
        achievements = (
            session.query(Achievement)
            .filter_by(username=username)
            .order_by(Achievement.achieved_at)
            .all()
        )
        return achievements

    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving user achievements: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving user achievements: {e}")
        return []
    finally:
        close_session(session)


def check_database_connection():
    """
    Check if database connection is working

    Returns:
        bool: True if connection is working
    """
    session = None
    try:
        session = get_session()
        # Try a simple query
        session.execute("SELECT 1")
        logger.info("Database connection successful")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking database connection: {e}")
        return False
    finally:
        if session:
            close_session(session)
