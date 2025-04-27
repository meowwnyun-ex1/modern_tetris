#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Models
-----------------------------
Database models for storing player statistics and game data
"""

import datetime
import json
import logging

try:
    from sqlalchemy import (
        Column,
        Integer,
        String,
        Float,
        Boolean,
        DateTime,
        create_engine,
    )
    from sqlalchemy.ext.declarative import declarative_base

    # Base class for all models
    Base = declarative_base()
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    # If SQLAlchemy is not available, create a dummy Base class
    class DummyBase:
        pass

    Base = DummyBase
    SQLALCHEMY_AVAILABLE = False

    # Log the import error
    logging.getLogger("tetris.db").error(
        "SQLAlchemy not available. Database models will not work."
    )


class User(Base):
    """User data model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)  # Stored password hash
    created_at = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"<User(username='{self.username}')>"

    def to_dict(self):
        """Convert object to dictionary (without password)"""
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GameScore(Base):
    """Game score data model"""

    __tablename__ = "game_scores"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    score = Column(Integer, default=0)
    level = Column(Integer, default=1)
    lines_cleared = Column(Integer, default=0)
    time_played = Column(Float, default=0.0)  # Time played in seconds
    victory = Column(Boolean, default=False)  # Whether game ended in victory
    timestamp = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        victory_str = "Victory" if self.victory else ""
        return f"<GameScore(username='{self.username}', score={self.score}, level={self.level}{victory_str})>"

    def to_dict(self):
        """Convert object to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "score": self.score,
            "level": self.level,
            "lines_cleared": self.lines_cleared,
            "time_played": self.time_played,
            "victory": self.victory,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class GameSettings(Base):
    """Player settings data model"""

    __tablename__ = "game_settings"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    theme = Column(String(20), default="denso")
    music_volume = Column(Float, default=0.7)
    sfx_volume = Column(Float, default=0.8)
    show_ghost = Column(Integer, default=1)  # 1 = on, 0 = off
    controls = Column(String(500), default="{}")  # Stored as JSON
    timestamp = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"<GameSettings(username='{self.username}', theme='{self.theme}')>"

    def to_dict(self):
        """Convert object to dictionary"""
        # Parse controls from JSON
        try:
            controls = json.loads(self.controls)
        except:
            controls = {}

        return {
            "id": self.id,
            "username": self.username,
            "theme": self.theme,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "show_ghost": bool(self.show_ghost),
            "controls": controls,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class Achievement(Base):
    """Achievement data model"""

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    achievement_id = Column(String(50), nullable=False)
    achievement_name = Column(String(100), nullable=False)
    description = Column(String(200))
    achieved_at = Column(DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return f"<Achievement(username='{self.username}', achievement='{self.achievement_name}')>"

    def to_dict(self):
        """Convert object to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "achievement_id": self.achievement_id,
            "achievement_name": self.achievement_name,
            "description": self.description,
            "achieved_at": self.achieved_at.isoformat() if self.achieved_at else None,
        }
