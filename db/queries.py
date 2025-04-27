#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Queries
------------------------------
SQL commands for retrieving and saving data with improved error handling
"""

import logging
import datetime
import traceback

try:
    import bcrypt

    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logging.getLogger("tetris.db").error(
        "bcrypt not available. Password hashing will not work properly."
    )

try:
    from sqlalchemy import desc
    from sqlalchemy.exc import SQLAlchemyError

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logging.getLogger("tetris.db").error(
        "SQLAlchemy not available. Database queries will not work."
    )

# Import local modules with error handling
try:
    from db.session import get_session, close_session, session_scope
    from db.models import User, GameScore, GameSettings, Achievement
except ImportError as e:
    logging.getLogger("tetris.db").error(f"Error importing database modules: {e}")
    # Create dummy objects to prevent errors if imports fail
    if "User" not in locals():

        class User:
            pass

    if "GameScore" not in locals():

        class GameScore:
            pass

    if "GameSettings" not in locals():

        class GameSettings:
            pass

    if "Achievement" not in locals():

        class Achievement:
            pass

    def session_scope():
        yield None


logger = logging.getLogger("tetris.db")


def _hash_password(password):
    """
    Hash password securely

    Args:
        password (str): Plain text password

    Returns:
        str: Hashed password or None if hashing fails
    """
    if not BCRYPT_AVAILABLE:
        logger.warning(
            "bcrypt not available, storing password in plain text (NOT SECURE)"
        )
        return f"INSECURE:{password}"

    try:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        return None


def _verify_password(plain_password, hashed_password):
    """
    Verify password against stored hash

    Args:
        plain_password (str): Plain text password to verify
        hashed_password (str): Stored password hash

    Returns:
        bool: True if password matches, False otherwise
    """
    if not BCRYPT_AVAILABLE:
        logger.warning(
            "bcrypt not available, checking password in plain text (NOT SECURE)"
        )
        return hashed_password == f"INSECURE:{plain_password}"

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def register_user(username, password):
    """
    Register a new user with better validation

    Args:
        username (str): Username
        password (str): Password

    Returns:
        bool: True if registration was successful
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

    if not username or not password:
        logger.warning("Registration failed: empty username or password")
        return False

    if len(password) < 6:
        logger.warning("Registration failed: password too short")
        return False

    with session_scope() as session:
        if session is None:
            return False

        try:
            # Check if username already exists
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                logger.warning(f"Username {username} already exists")
                return False

            # Hash password
            password_hash = _hash_password(password)
            if not password_hash:
                return False

            # Create new user
            new_user = User(username=username, password_hash=password_hash)
            session.add(new_user)

            logger.info(f"User {username} registered successfully")
            return True

        except Exception as e:
            logger.error(f"Database error during user registration: {e}")
            logger.debug(traceback.format_exc())
            return False


def authenticate_user(username, password):
    """
    Authenticate user with better error handling

    Args:
        username (str): Username
        password (str): Password

    Returns:
        bool: True if authentication was successful
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

    if not username or not password:
        return False

    with session_scope() as session:
        if session is None:
            return False

        try:
            # Find user
            user = session.query(User).filter_by(username=username).first()
            if not user:
                logger.warning(f"Authentication failed: user {username} not found")
                return False

            # Check password
            is_valid = _verify_password(password, user.password_hash)

            if is_valid:
                logger.info(f"User {username} authenticated successfully")
            else:
                logger.warning(
                    f"Authentication failed: incorrect password for {username}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"Database error during authentication: {e}")
            logger.debug(traceback.format_exc())
            return False


def save_game_score(username, score, level, lines, time_played, victory=False):
    """
    Save game score with validation

    Args:
        username (str): Username
        score (int): Score
        level (int): Level
        lines (int): Number of lines cleared
        time_played (float): Time played (seconds)
        victory (bool): Whether the game ended in victory

    Returns:
        bool: True if score was saved successfully
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

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

    with session_scope() as session:
        if session is None:
            return False

        try:
            # Create new score entry
            new_score = GameScore(
                username=username,
                score=score,
                level=level,
                lines_cleared=lines,
                time_played=time_played,
                victory=bool(victory),
                timestamp=datetime.datetime.now(),
            )
            session.add(new_score)

            logger.info(f"Score {score} for user {username} saved successfully")
            return True

        except Exception as e:
            logger.error(f"Database error saving score: {e}")
            logger.debug(traceback.format_exc())
            return False


def get_top_scores(limit=10):
    """
    Get top scores with error handling

    Args:
        limit (int): Number of scores to retrieve

    Returns:
        list: List of top scores
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return []

    with session_scope() as session:
        if session is None:
            return []

        try:
            # Get top scores
            scores = (
                session.query(GameScore)
                .order_by(desc(GameScore.score))
                .limit(limit)
                .all()
            )
            return scores

        except Exception as e:
            logger.error(f"Database error retrieving top scores: {e}")
            logger.debug(traceback.format_exc())
            return []


def get_user_best_score(username):
    """
    Get user's best score with error handling

    Args:
        username (str): Username

    Returns:
        GameScore: User's best score entry
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return None

    if not username:
        return None

    with session_scope() as session:
        if session is None:
            return None

        try:
            # Get user's best score
            score = (
                session.query(GameScore)
                .filter_by(username=username)
                .order_by(desc(GameScore.score))
                .first()
            )
            return score

        except Exception as e:
            logger.error(f"Database error retrieving user's best score: {e}")
            logger.debug(traceback.format_exc())
            return None


def save_user_settings(username, settings):
    """
    Save user settings with validation

    Args:
        username (str): Username
        settings (dict): Settings

    Returns:
        bool: True if settings were saved successfully
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

    if not username or not isinstance(settings, dict):
        return False

    with session_scope() as session:
        if session is None:
            return False

        try:
            # Check if settings already exist
            user_settings = (
                session.query(GameSettings).filter_by(username=username).first()
            )

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

                # Handle controls separately to ensure it's valid JSON
                if "controls" in settings:
                    import json

                    try:
                        # Ensure it's valid JSON by encoding and decoding
                        controls_json = json.dumps(settings["controls"])
                        user_settings.controls = controls_json
                    except:
                        # Keep existing controls if new ones are invalid
                        logger.warning(f"Invalid controls JSON for user {username}")

                user_settings.timestamp = datetime.datetime.now()
            else:
                # Create new settings
                import json

                controls_json = "{}"
                try:
                    if "controls" in settings:
                        controls_json = json.dumps(settings["controls"])
                except:
                    logger.warning(f"Invalid controls JSON for user {username}")

                user_settings = GameSettings(
                    username=username,
                    theme=settings.get("theme", "denso"),
                    music_volume=settings.get("music_volume", 0.7),
                    sfx_volume=settings.get("sfx_volume", 0.8),
                    show_ghost=settings.get("show_ghost", 1),
                    controls=controls_json,
                )
                session.add(user_settings)

            logger.info(f"Settings for user {username} saved successfully")
            return True

        except Exception as e:
            logger.error(f"Database error saving settings: {e}")
            logger.debug(traceback.format_exc())
            return False


def get_user_settings(username):
    """
    Get user settings with error handling

    Args:
        username (str): Username

    Returns:
        GameSettings: User settings
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return None

    if not username:
        return None

    with session_scope() as session:
        if session is None:
            return None

        try:
            # Get user settings
            settings = session.query(GameSettings).filter_by(username=username).first()
            return settings

        except Exception as e:
            logger.error(f"Database error retrieving user settings: {e}")
            logger.debug(traceback.format_exc())
            return None


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
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

    if not username or not achievement_id or not achievement_name:
        return False

    with session_scope() as session:
        if session is None:
            return False

        try:
            # Check if achievement already unlocked
            existing = (
                session.query(Achievement)
                .filter_by(username=username, achievement_id=achievement_id)
                .first()
            )

            if existing:
                logger.info(
                    f"Achievement {achievement_id} already unlocked for {username}"
                )
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

            logger.info(f"Achievement {achievement_name} unlocked for user {username}")
            return True

        except Exception as e:
            logger.error(f"Database error unlocking achievement: {e}")
            logger.debug(traceback.format_exc())
            return False


def get_user_achievements(username):
    """
    Get user achievements with error handling

    Args:
        username (str): Username

    Returns:
        list: List of user achievements
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return []

    if not username:
        return []

    with session_scope() as session:
        if session is None:
            return []

        try:
            # Get user achievements
            achievements = (
                session.query(Achievement)
                .filter_by(username=username)
                .order_by(Achievement.achieved_at)
                .all()
            )
            return achievements

        except Exception as e:
            logger.error(f"Database error retrieving user achievements: {e}")
            logger.debug(traceback.format_exc())
            return []


def check_database_connection():
    """
    Check if database connection is working

    Returns:
        bool: True if connection is working
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

    with session_scope() as session:
        if session is None:
            return False

        try:
            # Try a simple query
            session.execute("SELECT 1")
            logger.info("Database connection successful")
            return True

        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return False
