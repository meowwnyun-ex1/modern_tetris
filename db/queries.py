#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Queries (Updated for Neon PostgreSQL)
-----------------------------------------------------------
Optimized SQL queries for Neon database with enhanced error handling
"""

import logging
import datetime
import traceback
import json
from typing import List, Optional, Dict, Any, Tuple

try:
    import bcrypt

    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logging.getLogger("tetris.db").error(
        "bcrypt not available. Password hashing will not work properly."
    )

try:
    from sqlalchemy import desc, func, and_, or_, text
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError
    from sqlalchemy.orm import joinedload

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logging.getLogger("tetris.db").error(
        "SQLAlchemy not available. Database queries will not work."
    )

# Import local modules with error handling
try:
    from db.session import get_session, close_session, session_scope
    from db.models import User, GameScore, GameSettings, Achievement, GameSession
except ImportError as e:
    logging.getLogger("tetris.db").error(f"Error importing database modules: {e}")

    # Create dummy classes to prevent errors
    class User:
        pass

    class GameScore:
        pass

    class GameSettings:
        pass

    class Achievement:
        pass

    class GameSession:
        pass

    def session_scope():
        yield None


logger = logging.getLogger("tetris.db")


def _hash_password(password: str) -> Optional[str]:
    """
    Hash password securely with enhanced error handling

    Args:
        password: Plain text password

    Returns:
        Hashed password or None if hashing fails
    """
    if not BCRYPT_AVAILABLE:
        logger.warning("bcrypt not available, using fallback hash (NOT SECURE)")
        import hashlib

        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    try:
        # Use higher rounds for better security
        rounds = 12
        return bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)
        ).decode("utf-8")
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        return None


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against stored hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    if not BCRYPT_AVAILABLE:
        logger.warning("bcrypt not available, using fallback verification (NOT SECURE)")
        import hashlib

        return (
            hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
            == hashed_password
        )

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def register_user(username: str, password: str, email: str = None) -> bool:
    """
    Register a new user with enhanced validation and error handling

    Args:
        username: Username (3-50 characters, alphanumeric + underscore)
        password: Password (minimum 6 characters)
        email: Optional email address

    Returns:
        True if registration successful, False otherwise
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

    # Validate inputs
    if not username or not password:
        logger.warning("Registration failed: empty username or password")
        return False

    if len(username) < 3 or len(username) > 50:
        logger.warning("Registration failed: invalid username length")
        return False

    if len(password) < 6:
        logger.warning("Registration failed: password too short")
        return False

    # Validate email format if provided
    if email:
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            logger.warning("Registration failed: invalid email format")
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

            # Check if email already exists (if provided)
            if email:
                existing_email = session.query(User).filter_by(email=email).first()
                if existing_email:
                    logger.warning(f"Email {email} already registered")
                    return False

            # Hash password
            password_hash = _hash_password(password)
            if not password_hash:
                logger.error("Failed to hash password")
                return False

            # Create new user
            new_user = User(
                username=username,
                password_hash=password_hash,
                email=email,
                is_active=True,
                is_verified=False,
                created_at=func.now(),
                preferences={
                    "theme": "denso",
                    "notifications": True,
                    "privacy_public_scores": True,
                },
            )
            session.add(new_user)
            session.flush()  # Get the user ID

            # Create default settings for the user
            default_settings = GameSettings(
                user_id=new_user.id,
                username=username,
                theme="denso",
                show_ghost=True,
                show_grid=True,
                show_next_pieces=True,
                animations_enabled=True,
                particles_enabled=True,
                music_volume=0.7,
                sfx_volume=0.8,
                music_enabled=True,
                sfx_enabled=True,
                difficulty="medium",
                das_delay=170,
                arr_delay=50,
                controls={},
                advanced_settings={},
            )
            session.add(default_settings)

            # Create welcome achievement
            welcome_achievement = Achievement(
                user_id=new_user.id,
                username=username,
                achievement_id="welcome",
                achievement_name="Welcome to DENSO Tetris!",
                description="Registered your first account",
                category="milestone",
                rarity="common",
                points=10,
                progress_current=1,
                progress_required=1,
                is_completed=True,
                unlocked_at=func.now(),
            )
            session.add(welcome_achievement)

            logger.info(f"User {username} registered successfully")
            return True

        except IntegrityError as e:
            logger.warning(f"Registration failed due to constraint violation: {e}")
            return False
        except Exception as e:
            logger.error(f"Database error during user registration: {e}")
            logger.debug(traceback.format_exc())
            return False


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate user with enhanced security and logging

    Args:
        username: Username
        password: Password

    Returns:
        True if authentication successful, False otherwise
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
            # Find user with additional checks
            user = (
                session.query(User)
                .filter(and_(User.username == username, User.is_active == True))
                .first()
            )

            if not user:
                logger.warning(
                    f"Authentication failed: user {username} not found or inactive"
                )
                return False

            # Check password
            is_valid = _verify_password(password, user.password_hash)

            if is_valid:
                # Update last login time
                user.last_login_at = func.now()
                session.commit()
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


def save_game_score(
    username: str,
    score: int,
    level: int,
    lines: int,
    time_played: float,
    victory: bool = False,
    game_mode: str = "endless",
    game_stats: Dict = None,
) -> bool:
    """
    Save game score with enhanced analytics and user stat updates

    Args:
        username: Username
        score: Final score
        level: Final level
        lines: Lines cleared
        time_played: Time played in seconds
        victory: Whether game ended in victory
        game_mode: Game mode played
        game_stats: Additional game statistics

    Returns:
        True if score saved successfully, False otherwise
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

    if not username:
        logger.warning("Cannot save score: no username provided")
        return False

    # Validate inputs
    try:
        score = max(0, int(score))
        level = max(1, int(level))
        lines = max(0, int(lines))
        time_played = max(0.0, float(time_played))
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid score data: {e}")
        return False

    with session_scope() as session:
        if session is None:
            return False

        try:
            # Get user
            user = session.query(User).filter_by(username=username).first()
            if not user:
                logger.warning(f"User {username} not found when saving score")
                return False

            # Create new score entry
            new_score = GameScore(
                user_id=user.id,
                username=username,
                score=score,
                level=level,
                lines_cleared=lines,
                time_played=time_played,
                victory=victory,
                game_mode=game_mode,
                game_stats=game_stats or {},
                created_at=func.now(),
            )

            # Calculate performance metrics
            new_score.calculate_metrics()

            session.add(new_score)

            # Update user statistics
            user.update_stats(score, level, lines, time_played)

            # Check and update achievements
            _check_score_achievements(session, user, new_score)

            logger.info(f"Score {score} for user {username} saved successfully")
            return True

        except Exception as e:
            logger.error(f"Database error saving score: {e}")
            logger.debug(traceback.format_exc())
            return False


def _check_score_achievements(session, user: User, score: GameScore):
    """
    Check and update achievements based on game score

    Args:
        session: Database session
        user: User object
        score: GameScore object
    """
    achievements_to_check = [
        # Score achievements
        ("score_1k", "First Thousand", "Score 1,000 points", 1000),
        ("score_10k", "Ten Thousand", "Score 10,000 points", 10000),
        ("score_50k", "Fifty Thousand", "Score 50,000 points", 50000),
        ("score_100k", "One Hundred Thousand", "Score 100,000 points", 100000),
        # Level achievements
        ("level_10", "Level 10", "Reach level 10", None),
        ("level_20", "Level 20", "Reach level 20", None),
        # Lines achievements
        ("lines_100", "Line Clearer", "Clear 100 lines in total", None),
        ("lines_1000", "Line Master", "Clear 1,000 lines in total", None),
        # Special achievements
        ("first_game", "First Game", "Complete your first game", None),
        ("tetris", "Tetris Master", "Get a Tetris (4 lines)", None),
        ("victory", "Victory", "Complete victory mode", None),
    ]

    for achievement_id, name, description, threshold in achievements_to_check:
        # Check if user already has this achievement
        existing = (
            session.query(Achievement)
            .filter_by(user_id=user.id, achievement_id=achievement_id)
            .first()
        )

        if existing and existing.is_completed:
            continue

        # Check achievement criteria
        should_unlock = False

        if achievement_id.startswith("score_") and threshold:
            should_unlock = score.score >= threshold
        elif achievement_id.startswith("level_"):
            target_level = int(achievement_id.split("_")[1])
            should_unlock = score.level >= target_level
        elif achievement_id == "lines_100":
            should_unlock = user.total_lines_cleared >= 100
        elif achievement_id == "lines_1000":
            should_unlock = user.total_lines_cleared >= 1000
        elif achievement_id == "first_game":
            should_unlock = user.total_games_played >= 1
        elif achievement_id == "tetris":
            # Check if game stats indicate a tetris
            tetris_count = score.game_stats.get("tetris_count", 0)
            should_unlock = tetris_count > 0
        elif achievement_id == "victory":
            should_unlock = score.victory

        if should_unlock:
            if existing:
                existing.is_completed = True
                existing.unlocked_at = func.now()
            else:
                new_achievement = Achievement(
                    user_id=user.id,
                    username=user.username,
                    achievement_id=achievement_id,
                    achievement_name=name,
                    description=description,
                    category=(
                        "score" if achievement_id.startswith("score_") else "gameplay"
                    ),
                    rarity="common",
                    points=10,
                    progress_current=1,
                    progress_required=1,
                    is_completed=True,
                    unlocked_at=func.now(),
                )
                session.add(new_achievement)


def get_top_scores(
    limit: int = 10, game_mode: str = None, time_period: str = "all"
) -> List[GameScore]:
    """
    Get top scores with filtering options

    Args:
        limit: Number of scores to retrieve
        game_mode: Filter by game mode (optional)
        time_period: 'all', 'month', 'week', 'day'

    Returns:
        List of top scores
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return []

    with session_scope() as session:
        if session is None:
            return []

        try:
            query = session.query(GameScore)

            # Filter by game mode if specified
            if game_mode:
                query = query.filter(GameScore.game_mode == game_mode)

            # Filter by time period
            if time_period != "all":
                now = datetime.datetime.now(datetime.timezone.utc)
                if time_period == "day":
                    start_time = now - datetime.timedelta(days=1)
                elif time_period == "week":
                    start_time = now - datetime.timedelta(weeks=1)
                elif time_period == "month":
                    start_time = now - datetime.timedelta(days=30)
                else:
                    start_time = None

                if start_time:
                    query = query.filter(GameScore.created_at >= start_time)

            # Order by score and get top results
            scores = (
                query.order_by(desc(GameScore.score), desc(GameScore.created_at))
                .limit(limit)
                .all()
            )

            return scores

        except Exception as e:
            logger.error(f"Database error retrieving top scores: {e}")
            logger.debug(traceback.format_exc())
            return []


def get_user_best_score(username: str, game_mode: str = None) -> Optional[GameScore]:
    """
    Get user's best score with optional game mode filtering

    Args:
        username: Username
        game_mode: Filter by game mode (optional)

    Returns:
        User's best score or None if not found
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
            query = session.query(GameScore).filter_by(username=username)

            if game_mode:
                query = query.filter(GameScore.game_mode == game_mode)

            score = query.order_by(desc(GameScore.score)).first()
            return score

        except Exception as e:
            logger.error(f"Database error retrieving user's best score: {e}")
            logger.debug(traceback.format_exc())
            return None


def get_user_stats(username: str) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive user statistics

    Args:
        username: Username

    Returns:
        Dictionary with user statistics or None if not found
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return None

    with session_scope() as session:
        if session is None:
            return None

        try:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                return None

            # Get recent scores
            recent_scores = (
                session.query(GameScore)
                .filter_by(username=username)
                .order_by(desc(GameScore.created_at))
                .limit(10)
                .all()
            )

            # Get achievements
            achievements = (
                session.query(Achievement)
                .filter_by(username=username, is_completed=True)
                .order_by(desc(Achievement.unlocked_at))
                .all()
            )

            # Calculate additional stats
            total_score = (
                session.query(func.sum(GameScore.score))
                .filter_by(username=username)
                .scalar()
                or 0
            )

            avg_score = (
                session.query(func.avg(GameScore.score))
                .filter_by(username=username)
                .scalar()
                or 0
            )

            victories = (
                session.query(func.count(GameScore.id))
                .filter_by(username=username, victory=True)
                .scalar()
                or 0
            )

            stats = {
                "user": user.to_dict(),
                "total_games": user.total_games_played,
                "best_score": user.best_score,
                "best_level": user.best_level,
                "total_lines": user.total_lines_cleared,
                "total_playtime": user.total_play_time_seconds,
                "total_score": int(total_score),
                "average_score": float(avg_score),
                "victories": victories,
                "recent_scores": [score.to_dict() for score in recent_scores],
                "achievements": [achievement.to_dict() for achievement in achievements],
                "achievement_count": len(achievements),
            }

            return stats

        except Exception as e:
            logger.error(f"Database error retrieving user stats: {e}")
            logger.debug(traceback.format_exc())
            return None


def save_user_settings(username: str, settings: Dict[str, Any]) -> bool:
    """
    Save user settings with validation and type conversion

    Args:
        username: Username
        settings: Settings dictionary

    Returns:
        True if settings saved successfully, False otherwise
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
            # Get user
            user = session.query(User).filter_by(username=username).first()
            if not user:
                logger.warning(f"User {username} not found when saving settings")
                return False

            # Get or create settings
            user_settings = (
                session.query(GameSettings).filter_by(username=username).first()
            )

            if user_settings:
                # Update existing settings
                for key, value in settings.items():
                    if hasattr(user_settings, key):
                        # Type validation and conversion
                        if key in ["music_volume", "sfx_volume"]:
                            value = max(0.0, min(1.0, float(value)))
                        elif key in ["das_delay", "arr_delay"]:
                            value = max(0, min(1000, int(value)))
                        elif key in [
                            "show_ghost",
                            "show_grid",
                            "show_next_pieces",
                            "animations_enabled",
                            "particles_enabled",
                            "music_enabled",
                            "sfx_enabled",
                        ]:
                            value = bool(value)
                        elif key in ["controls", "advanced_settings"]:
                            if isinstance(value, dict):
                                # For JSON fields, store as dict (SQLAlchemy will handle serialization)
                                pass
                            else:
                                continue  # Skip invalid JSON data

                        setattr(user_settings, key, value)

                user_settings.updated_at = func.now()
            else:
                # Create new settings with defaults
                user_settings = GameSettings(
                    user_id=user.id,
                    username=username,
                    theme=settings.get("theme", "denso"),
                    show_ghost=settings.get("show_ghost", True),
                    show_grid=settings.get("show_grid", True),
                    show_next_pieces=settings.get("show_next_pieces", True),
                    animations_enabled=settings.get("animations_enabled", True),
                    particles_enabled=settings.get("particles_enabled", True),
                    music_volume=max(0.0, min(1.0, settings.get("music_volume", 0.7))),
                    sfx_volume=max(0.0, min(1.0, settings.get("sfx_volume", 0.8))),
                    music_enabled=settings.get("music_enabled", True),
                    sfx_enabled=settings.get("sfx_enabled", True),
                    difficulty=settings.get("difficulty", "medium"),
                    das_delay=max(0, min(1000, settings.get("das_delay", 170))),
                    arr_delay=max(0, min(1000, settings.get("arr_delay", 50))),
                    controls=settings.get("controls", {}),
                    advanced_settings=settings.get("advanced_settings", {}),
                )
                session.add(user_settings)

            logger.info(f"Settings for user {username} saved successfully")
            return True

        except Exception as e:
            logger.error(f"Database error saving settings: {e}")
            logger.debug(traceback.format_exc())
            return False


def get_user_settings(username: str) -> Optional[GameSettings]:
    """
    Get user settings with defaults if not found

    Args:
        username: Username

    Returns:
        User settings or None if user not found
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
            settings = session.query(GameSettings).filter_by(username=username).first()
            return settings

        except Exception as e:
            logger.error(f"Database error retrieving user settings: {e}")
            logger.debug(traceback.format_exc())
            return None


def unlock_achievement(
    username: str,
    achievement_id: str,
    achievement_name: str,
    description: str,
    category: str = "general",
    rarity: str = "common",
    points: int = 10,
) -> bool:
    """
    Unlock achievement for user with enhanced tracking

    Args:
        username: Username
        achievement_id: Unique achievement identifier
        achievement_name: Display name
        description: Achievement description
        category: Achievement category
        rarity: Achievement rarity
        points: Points awarded

    Returns:
        True if achievement unlocked successfully, False if already unlocked or error
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
            # Get user
            user = session.query(User).filter_by(username=username).first()
            if not user:
                logger.warning(f"User {username} not found when unlocking achievement")
                return False

            # Check if achievement already exists
            existing = (
                session.query(Achievement)
                .filter_by(user_id=user.id, achievement_id=achievement_id)
                .first()
            )

            if existing and existing.is_completed:
                logger.info(
                    f"Achievement {achievement_id} already unlocked for {username}"
                )
                return False

            if existing:
                # Update existing achievement
                existing.is_completed = True
                existing.unlocked_at = func.now()
                existing.achievement_name = achievement_name
                existing.description = description
                existing.category = category
                existing.rarity = rarity
                existing.points = points
            else:
                # Create new achievement
                new_achievement = Achievement(
                    user_id=user.id,
                    username=username,
                    achievement_id=achievement_id,
                    achievement_name=achievement_name,
                    description=description,
                    category=category,
                    rarity=rarity,
                    points=points,
                    progress_current=1,
                    progress_required=1,
                    is_completed=True,
                    unlocked_at=func.now(),
                )
                session.add(new_achievement)

            logger.info(f"Achievement {achievement_name} unlocked for user {username}")
            return True

        except Exception as e:
            logger.error(f"Database error unlocking achievement: {e}")
            logger.debug(traceback.format_exc())
            return False


def get_user_achievements(
    username: str, completed_only: bool = True
) -> List[Achievement]:
    """
    Get user achievements with filtering options

    Args:
        username: Username
        completed_only: If True, only return completed achievements

    Returns:
        List of user achievements
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
            query = session.query(Achievement).filter_by(username=username)

            if completed_only:
                query = query.filter(Achievement.is_completed == True)

            achievements = query.order_by(
                desc(Achievement.unlocked_at), Achievement.created_at
            ).all()

            return achievements

        except Exception as e:
            logger.error(f"Database error retrieving user achievements: {e}")
            logger.debug(traceback.format_exc())
            return []


def get_leaderboard(
    game_mode: str = None, time_period: str = "all", limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get leaderboard with advanced filtering and ranking

    Args:
        game_mode: Filter by game mode
        time_period: 'all', 'month', 'week', 'day'
        limit: Maximum number of entries

    Returns:
        List of leaderboard entries with rankings
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return []

    with session_scope() as session:
        if session is None:
            return []

        try:
            # Build query for best scores per user
            subquery = session.query(
                GameScore.username,
                func.max(GameScore.score).label("best_score"),
                func.max(GameScore.level).label("best_level"),
                func.sum(GameScore.lines_cleared).label("total_lines"),
                func.count(GameScore.id).label("total_games"),
                func.max(GameScore.created_at).label("latest_game"),
            )

            # Apply filters
            if game_mode:
                subquery = subquery.filter(GameScore.game_mode == game_mode)

            if time_period != "all":
                now = datetime.datetime.now(datetime.timezone.utc)
                if time_period == "day":
                    start_time = now - datetime.timedelta(days=1)
                elif time_period == "week":
                    start_time = now - datetime.timedelta(weeks=1)
                elif time_period == "month":
                    start_time = now - datetime.timedelta(days=30)
                else:
                    start_time = None

                if start_time:
                    subquery = subquery.filter(GameScore.created_at >= start_time)

            # Group by username and order by best score
            results = (
                subquery.group_by(GameScore.username)
                .order_by(desc("best_score"))
                .limit(limit)
                .all()
            )

            # Build leaderboard with rankings
            leaderboard = []
            for rank, result in enumerate(results, 1):
                entry = {
                    "rank": rank,
                    "username": result.username,
                    "best_score": result.best_score,
                    "best_level": result.best_level,
                    "total_lines": result.total_lines,
                    "total_games": result.total_games,
                    "latest_game": (
                        result.latest_game.isoformat() if result.latest_game else None
                    ),
                }
                leaderboard.append(entry)

            return leaderboard

        except Exception as e:
            logger.error(f"Database error retrieving leaderboard: {e}")
            logger.debug(traceback.format_exc())
            return []


def create_game_session(username: str, game_mode: str = "endless") -> Optional[str]:
    """
    Create a new game session for analytics tracking

    Args:
        username: Username
        game_mode: Game mode

    Returns:
        Session ID if created successfully, None otherwise
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return None

    with session_scope() as session:
        if session is None:
            return None

        try:
            user = session.query(User).filter_by(username=username).first()
            if not user:
                return None

            game_session = GameSession(
                user_id=user.id,
                username=username,
                game_mode=game_mode,
                started_at=func.now(),
            )
            session.add(game_session)
            session.flush()  # Get the ID

            return str(game_session.id)

        except Exception as e:
            logger.error(f"Database error creating game session: {e}")
            logger.debug(traceback.format_exc())
            return None


def end_game_session(
    session_id: str,
    score: int = None,
    level: int = None,
    lines: int = None,
    analytics_data: Dict = None,
) -> bool:
    """
    End a game session with final statistics

    Args:
        session_id: Session ID
        score: Final score
        level: Final level
        lines: Lines cleared
        analytics_data: Additional analytics data

    Returns:
        True if session ended successfully, False otherwise
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("Database functionality not available")
        return False

    with session_scope() as session:
        if session is None:
            return False

        try:
            game_session = session.query(GameSession).filter_by(id=session_id).first()
            if not game_session:
                return False

            game_session.end_session(score, level, lines)
            if analytics_data:
                game_session.analytics_data = analytics_data

            return True

        except Exception as e:
            logger.error(f"Database error ending game session: {e}")
            logger.debug(traceback.format_exc())
            return False


def check_database_connection() -> Dict[str, Any]:
    """
    Comprehensive database connection and health check

    Returns:
        Dictionary with connection status and health information
    """
    if not SQLALCHEMY_AVAILABLE:
        return {"status": "error", "message": "SQLAlchemy not available", "details": {}}

    try:
        # Import health check from session
        from db.session import check_database_health

        health_info = check_database_health()

        with session_scope() as session:
            if session is None:
                return {
                    "status": "error",
                    "message": "Could not create database session",
                    "details": health_info,
                }

            # Test basic operations
            user_count = session.query(func.count(User.id)).scalar()
            score_count = session.query(func.count(GameScore.id)).scalar()

            health_info.update(
                {
                    "user_count": user_count,
                    "score_count": score_count,
                    "message": "Database connection healthy",
                }
            )

            return {
                "status": "healthy",
                "message": "Database connection successful",
                "details": health_info,
            }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "message": f"Database health check failed: {str(e)}",
            "details": {},
        }
