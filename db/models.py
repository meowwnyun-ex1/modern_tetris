#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Models (Updated for Neon PostgreSQL)
----------------------------------------------------------
Database models optimized for Neon PostgreSQL with fallback support
"""

import datetime
import json
import logging
from decimal import Decimal

try:
    from sqlalchemy import (
        Column,
        Integer,
        String,
        Float,
        Boolean,
        DateTime,
        Text,
        JSON,
        BigInteger,
        SmallInteger,
        Index,
        UniqueConstraint,
        CheckConstraint,
        create_engine,
        ForeignKey,
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy.sql import func
    from sqlalchemy.orm import relationship
    import uuid

    # Base class for all models
    Base = declarative_base()
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    # Fallback if SQLAlchemy is not available
    class DummyBase:
        pass

    Base = DummyBase
    SQLALCHEMY_AVAILABLE = False
    logging.getLogger("tetris.db").error(
        "SQLAlchemy not available. Database models will not work."
    )


class BaseModel:
    """Base model with common fields and methods"""

    def to_dict(self):
        """Convert model to dictionary, handling special types"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)

            # Handle special types
            if isinstance(value, datetime.datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, Decimal):
                result[column.name] = float(value)
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value

        return result

    def __repr__(self):
        """Generic repr for all models"""
        class_name = self.__class__.__name__
        attrs = []
        for column in self.__table__.columns:
            if column.primary_key or column.name in ["username", "name", "title"]:
                value = getattr(self, column.name)
                attrs.append(f"{column.name}='{value}'")

        return f"<{class_name}({', '.join(attrs)})>"


class User(Base, BaseModel):
    """Enhanced User model with better indexing and constraints"""

    __tablename__ = "users"

    # Primary key with auto-increment
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Unique username with constraints
    username = Column(
        String(50), unique=True, nullable=False, index=True  # Index for fast lookups
    )

    # Password hash with sufficient length for bcrypt
    password_hash = Column(String(255), nullable=False)

    # Optional email with unique constraint
    email = Column(String(320), unique=True, nullable=True, index=True)

    # User status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps with automatic handling
    created_at = Column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # User preferences as JSON (JSONB for PostgreSQL, TEXT for SQLite)
    preferences = Column(
        JSONB if SQLALCHEMY_AVAILABLE else Text, default=lambda: {}, nullable=False
    )

    # Statistics
    total_games_played = Column(BigInteger, default=0, nullable=False)
    best_score = Column(BigInteger, default=0, nullable=False)
    best_level = Column(SmallInteger, default=1, nullable=False)
    total_lines_cleared = Column(BigInteger, default=0, nullable=False)
    total_play_time_seconds = Column(BigInteger, default=0, nullable=False)

    # Relationships
    game_scores = relationship("GameScore", back_populates="user")
    achievements = relationship("Achievement", back_populates="user")
    settings = relationship("GameSettings", back_populates="user", uselist=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint("LENGTH(username) >= 3", name="username_min_length"),
        CheckConstraint("LENGTH(username) <= 50", name="username_max_length"),
        CheckConstraint("best_score >= 0", name="best_score_positive"),
        CheckConstraint("best_level >= 1", name="best_level_positive"),
        CheckConstraint("total_games_played >= 0", name="total_games_positive"),
        Index("idx_user_username_active", "username", "is_active"),
        Index("idx_user_created", "created_at"),
        Index("idx_user_last_login", "last_login_at"),
    )

    def to_dict(self):
        """Convert to dictionary without sensitive data"""
        data = super().to_dict()
        # Remove password hash from serialization
        data.pop("password_hash", None)
        return data

    def update_stats(self, score, level, lines_cleared, play_time):
        """Update user statistics after a game"""
        self.total_games_played += 1
        if score > self.best_score:
            self.best_score = score
        if level > self.best_level:
            self.best_level = level
        self.total_lines_cleared += lines_cleared
        self.total_play_time_seconds += int(play_time)
        self.updated_at = func.now()


class GameScore(Base, BaseModel):
    """Enhanced GameScore model with better performance and analytics"""

    __tablename__ = "game_scores"

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign key to user with proper indexing
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Username for quick access (denormalized for performance)
    username = Column(String(50), nullable=False, index=True)

    # Game statistics
    score = Column(BigInteger, default=0, nullable=False)
    level = Column(SmallInteger, default=1, nullable=False)
    lines_cleared = Column(Integer, default=0, nullable=False)

    # Time tracking
    time_played = Column(Float, default=0.0, nullable=False)  # seconds

    # Game outcome
    victory = Column(Boolean, default=False, nullable=False)
    game_mode = Column(
        String(20), default="endless", nullable=False
    )  # endless, victory, challenge

    # Additional statistics (stored as JSON for flexibility)
    game_stats = Column(
        JSONB if SQLALCHEMY_AVAILABLE else Text, default=lambda: {}, nullable=False
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )

    # Performance metrics
    score_per_minute = Column(Float, default=0.0, nullable=False)
    lines_per_minute = Column(Float, default=0.0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="game_scores")

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint("score >= 0", name="score_positive"),
        CheckConstraint("level >= 1", name="level_positive"),
        CheckConstraint("lines_cleared >= 0", name="lines_positive"),
        CheckConstraint("time_played >= 0", name="time_positive"),
        Index("idx_score_user_score", "user_id", "score"),
        Index("idx_score_username_score", "username", "score"),
        Index("idx_score_created", "created_at"),
        Index("idx_score_victory", "victory"),
        Index("idx_score_leaderboard", "score", "created_at"),
    )

    def calculate_metrics(self):
        """Calculate performance metrics"""
        if self.time_played > 0:
            minutes = self.time_played / 60.0
            self.score_per_minute = self.score / minutes
            self.lines_per_minute = self.lines_cleared / minutes


class GameSettings(Base, BaseModel):
    """Enhanced GameSettings model with better organization"""

    __tablename__ = "game_settings"

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign key to user
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One setting per user
        index=True,
    )

    # Username for quick access
    username = Column(String(50), nullable=False, unique=True, index=True)

    # Visual settings
    theme = Column(String(20), default="denso", nullable=False)
    show_ghost = Column(Boolean, default=True, nullable=False)
    show_grid = Column(Boolean, default=True, nullable=False)
    show_next_pieces = Column(Boolean, default=True, nullable=False)
    animations_enabled = Column(Boolean, default=True, nullable=False)
    particles_enabled = Column(Boolean, default=True, nullable=False)

    # Audio settings
    music_volume = Column(Float, default=0.7, nullable=False)
    sfx_volume = Column(Float, default=0.8, nullable=False)
    music_enabled = Column(Boolean, default=True, nullable=False)
    sfx_enabled = Column(Boolean, default=True, nullable=False)

    # Game settings
    difficulty = Column(String(20), default="medium", nullable=False)
    das_delay = Column(SmallInteger, default=170, nullable=False)
    arr_delay = Column(SmallInteger, default=50, nullable=False)

    # Controls (stored as JSON)
    controls = Column(
        JSONB if SQLALCHEMY_AVAILABLE else Text, default=lambda: {}, nullable=False
    )

    # Advanced settings
    advanced_settings = Column(
        JSONB if SQLALCHEMY_AVAILABLE else Text, default=lambda: {}, nullable=False
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="settings")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "music_volume >= 0 AND music_volume <= 1", name="music_volume_range"
        ),
        CheckConstraint("sfx_volume >= 0 AND sfx_volume <= 1", name="sfx_volume_range"),
        CheckConstraint("das_delay >= 0 AND das_delay <= 1000", name="das_delay_range"),
        CheckConstraint("arr_delay >= 0 AND arr_delay <= 1000", name="arr_delay_range"),
        Index("idx_settings_user", "user_id"),
        Index("idx_settings_username", "username"),
    )

    def get_controls_dict(self):
        """Get controls as Python dict"""
        if isinstance(self.controls, str):
            try:
                return json.loads(self.controls)
            except:
                return {}
        return self.controls or {}

    def set_controls_dict(self, controls_dict):
        """Set controls from Python dict"""
        if SQLALCHEMY_AVAILABLE:
            self.controls = controls_dict
        else:
            self.controls = json.dumps(controls_dict)


class Achievement(Base, BaseModel):
    """Enhanced Achievement model with categories and progress"""

    __tablename__ = "achievements"

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign key to user
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Username for quick access
    username = Column(String(50), nullable=False, index=True)

    # Achievement details
    achievement_id = Column(String(50), nullable=False, index=True)
    achievement_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(30), default="general", nullable=False)

    # Achievement metadata
    rarity = Column(
        String(20), default="common", nullable=False
    )  # common, rare, epic, legendary
    points = Column(SmallInteger, default=10, nullable=False)
    icon_name = Column(String(50), nullable=True)

    # Progress tracking
    progress_current = Column(Integer, default=0, nullable=False)
    progress_required = Column(Integer, default=1, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Timestamps
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="achievements")

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="unique_user_achievement"),
        CheckConstraint("points >= 0", name="points_positive"),
        CheckConstraint("progress_current >= 0", name="progress_current_positive"),
        CheckConstraint("progress_required >= 1", name="progress_required_positive"),
        Index("idx_achievement_user_category", "user_id", "category"),
        Index("idx_achievement_completed", "is_completed", "unlocked_at"),
        Index("idx_achievement_rarity", "rarity"),
    )

    def update_progress(self, increment=1):
        """Update achievement progress"""
        self.progress_current = min(
            self.progress_current + increment, self.progress_required
        )

        if self.progress_current >= self.progress_required and not self.is_completed:
            self.is_completed = True
            self.unlocked_at = func.now()
            return True  # Achievement unlocked

        return False  # Not yet unlocked

    @property
    def progress_percentage(self):
        """Get progress as percentage"""
        if self.progress_required <= 0:
            return 100.0
        return min(100.0, (self.progress_current / self.progress_required) * 100.0)


class GameSession(Base, BaseModel):
    """Track individual game sessions for analytics"""

    __tablename__ = "game_sessions"

    # Primary key with UUID for better distribution
    id = Column(
        UUID(as_uuid=True) if SQLALCHEMY_AVAILABLE else String(36),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Foreign key to user
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session metadata
    username = Column(String(50), nullable=False, index=True)
    game_mode = Column(String(20), default="endless", nullable=False)

    # Session timing
    started_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Final game state
    final_score = Column(BigInteger, nullable=True)
    final_level = Column(SmallInteger, nullable=True)
    final_lines = Column(Integer, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)

    # Session analytics (stored as JSON)
    analytics_data = Column(
        JSONB if SQLALCHEMY_AVAILABLE else Text, default=lambda: {}, nullable=False
    )

    # Table constraints and indexes
    __table_args__ = (
        Index("idx_session_user_started", "user_id", "started_at"),
        Index("idx_session_completed", "completed", "ended_at"),
        Index("idx_session_mode", "game_mode"),
    )

    def end_session(self, score=None, level=None, lines=None):
        """End the game session"""
        self.ended_at = func.now()
        if self.started_at:
            # Calculate duration if we have start time
            self.duration_seconds = int(
                (self.ended_at - self.started_at).total_seconds()
            )

        self.final_score = score
        self.final_level = level
        self.final_lines = lines
        self.completed = True


# Create indexes after table definition (for better organization)
if SQLALCHEMY_AVAILABLE:
    # Additional composite indexes for complex queries

    # Leaderboard queries
    Index("idx_leaderboard_global", GameScore.score.desc(), GameScore.created_at.desc())
    Index(
        "idx_leaderboard_monthly", GameScore.score.desc(), GameScore.created_at.desc()
    )

    # User analytics
    Index(
        "idx_user_analytics", User.total_games_played, User.best_score, User.created_at
    )

    # Achievement analytics
    Index(
        "idx_achievement_analytics",
        Achievement.category,
        Achievement.rarity,
        Achievement.unlocked_at,
    )
