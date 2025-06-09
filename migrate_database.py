#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Migration Script
----------------------------------------
Script to migrate existing SQLite data to Neon PostgreSQL
"""

import os
import sys
import logging
import traceback
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("python-dotenv not available, using system environment variables only")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
    ],
)

logger = logging.getLogger("tetris.db.migration")


def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = ["sqlalchemy", "psycopg2", "bcrypt"]
    missing_modules = []

    for module in required_modules:
        try:
            if module == "psycopg2":
                import psycopg2
            elif module == "sqlalchemy":
                import sqlalchemy
            elif module == "bcrypt":
                import bcrypt
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        logger.error(f"Missing required modules: {', '.join(missing_modules)}")
        logger.error("Please install them with: pip install -r requirements.txt")
        return False

    return True


def create_sqlite_engine(sqlite_path):
    """Create SQLite engine for source database"""
    try:
        from sqlalchemy import create_engine

        if not os.path.exists(sqlite_path):
            logger.error(f"SQLite database not found: {sqlite_path}")
            return None

        engine = create_engine(f"sqlite:///{sqlite_path}")
        logger.info(f"Connected to SQLite database: {sqlite_path}")
        return engine

    except Exception as e:
        logger.error(f"Failed to connect to SQLite database: {e}")
        return None


def create_postgresql_engine():
    """Create PostgreSQL engine for target database"""
    try:
        from db.session import init_db, engine as pg_engine

        if not init_db():
            logger.error("Failed to initialize PostgreSQL connection")
            return None

        logger.info("Connected to PostgreSQL database")
        return pg_engine

    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        return None


def get_sqlite_schema():
    """Get the schema of the SQLite database"""
    try:
        from sqlalchemy import text

        # This is a simplified schema detection
        # In a real migration, you'd want more sophisticated schema analysis
        tables = {
            "users": ["id", "username", "password_hash", "created_at"],
            "game_scores": [
                "id",
                "username",
                "score",
                "level",
                "lines_cleared",
                "time_played",
                "victory",
                "timestamp",
            ],
            "game_settings": [
                "id",
                "username",
                "theme",
                "music_volume",
                "sfx_volume",
                "show_ghost",
                "controls",
                "timestamp",
            ],
            "achievements": [
                "id",
                "username",
                "achievement_id",
                "achievement_name",
                "description",
                "achieved_at",
            ],
        }

        return tables

    except Exception as e:
        logger.error(f"Failed to get SQLite schema: {e}")
        return {}


def migrate_table_data(sqlite_engine, pg_engine, table_name, columns):
    """Migrate data from one table"""
    try:
        from sqlalchemy import text
        from db.session import session_scope

        logger.info(f"Migrating table: {table_name}")

        # Read data from SQLite
        with sqlite_engine.connect() as sqlite_conn:
            try:
                result = sqlite_conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.fetchall()
                logger.info(f"Found {len(rows)} rows in {table_name}")
            except Exception as e:
                logger.warning(f"Table {table_name} not found in SQLite: {e}")
                return True

        if not rows:
            logger.info(f"No data to migrate for {table_name}")
            return True

        # Migrate data to PostgreSQL
        migrated_count = 0
        error_count = 0

        with session_scope() as session:
            if session is None:
                logger.error("Failed to get PostgreSQL session")
                return False

            for row in rows:
                try:
                    if table_name == "users":
                        migrated_count += migrate_user_row(session, row)
                    elif table_name == "game_scores":
                        migrated_count += migrate_score_row(session, row)
                    elif table_name == "game_settings":
                        migrated_count += migrate_settings_row(session, row)
                    elif table_name == "achievements":
                        migrated_count += migrate_achievement_row(session, row)

                except Exception as e:
                    logger.error(f"Failed to migrate row from {table_name}: {e}")
                    error_count += 1

        logger.info(
            f"Migrated {migrated_count} rows from {table_name}, {error_count} errors"
        )
        return error_count == 0

    except Exception as e:
        logger.error(f"Failed to migrate table {table_name}: {e}")
        logger.debug(traceback.format_exc())
        return False


def migrate_user_row(session, row):
    """Migrate a single user row"""
    try:
        from db.models import User
        from sqlalchemy import func

        # Check if user already exists
        existing_user = session.query(User).filter_by(username=row[1]).first()
        if existing_user:
            logger.debug(f"User {row[1]} already exists, skipping")
            return 0

        # Create new user with enhanced fields
        new_user = User(
            username=row[1],
            password_hash=row[2],
            email=None,  # SQLite version didn't have email
            is_active=True,
            is_verified=False,
            created_at=row[3] if len(row) > 3 else func.now(),
            preferences={},
            total_games_played=0,
            best_score=0,
            best_level=1,
            total_lines_cleared=0,
            total_play_time_seconds=0,
        )

        session.add(new_user)
        session.flush()  # Get the ID

        return 1

    except Exception as e:
        logger.error(f"Failed to migrate user row: {e}")
        return 0


def migrate_score_row(session, row):
    """Migrate a single score row"""
    try:
        from db.models import GameScore, User
        from sqlalchemy import func

        # Get user ID
        user = session.query(User).filter_by(username=row[1]).first()
        if not user:
            logger.warning(f"User {row[1]} not found for score migration")
            return 0

        # Create new score record
        new_score = GameScore(
            user_id=user.id,
            username=row[1],
            score=row[2],
            level=row[3],
            lines_cleared=row[4],
            time_played=row[5] if len(row) > 5 else 0.0,
            victory=row[6] if len(row) > 6 else False,
            game_mode="endless",
            game_stats={},
            created_at=row[7] if len(row) > 7 else func.now(),
        )

        # Calculate metrics
        new_score.calculate_metrics()

        session.add(new_score)

        # Update user stats
        if new_score.score > user.best_score:
            user.best_score = new_score.score
        if new_score.level > user.best_level:
            user.best_level = new_score.level

        user.total_games_played += 1
        user.total_lines_cleared += new_score.lines_cleared
        user.total_play_time_seconds += int(new_score.time_played)

        return 1

    except Exception as e:
        logger.error(f"Failed to migrate score row: {e}")
        return 0


def migrate_settings_row(session, row):
    """Migrate a single settings row"""
    try:
        from db.models import GameSettings, User

        # Get user ID
        user = session.query(User).filter_by(username=row[1]).first()
        if not user:
            logger.warning(f"User {row[1]} not found for settings migration")
            return 0

        # Check if settings already exist
        existing_settings = (
            session.query(GameSettings).filter_by(user_id=user.id).first()
        )
        if existing_settings:
            logger.debug(f"Settings for {row[1]} already exist, skipping")
            return 0

        # Parse controls JSON if it exists
        controls = {}
        if len(row) > 6 and row[6]:
            try:
                controls = json.loads(row[6])
            except:
                controls = {}

        # Create new settings record
        new_settings = GameSettings(
            user_id=user.id,
            username=row[1],
            theme=row[2] if len(row) > 2 else "denso",
            music_volume=row[3] if len(row) > 3 else 0.7,
            sfx_volume=row[4] if len(row) > 4 else 0.8,
            show_ghost=bool(row[5]) if len(row) > 5 else True,
            show_grid=True,
            show_next_pieces=True,
            animations_enabled=True,
            particles_enabled=True,
            music_enabled=True,
            sfx_enabled=True,
            difficulty="medium",
            das_delay=170,
            arr_delay=50,
            controls=controls,
            advanced_settings={},
        )

        session.add(new_settings)
        return 1

    except Exception as e:
        logger.error(f"Failed to migrate settings row: {e}")
        return 0


def migrate_achievement_row(session, row):
    """Migrate a single achievement row"""
    try:
        from db.models import Achievement, User
        from sqlalchemy import func

        # Get user ID
        user = session.query(User).filter_by(username=row[1]).first()
        if not user:
            logger.warning(f"User {row[1]} not found for achievement migration")
            return 0

        # Check if achievement already exists
        existing_achievement = (
            session.query(Achievement)
            .filter_by(user_id=user.id, achievement_id=row[2])
            .first()
        )
        if existing_achievement:
            logger.debug(f"Achievement {row[2]} for {row[1]} already exists, skipping")
            return 0

        # Create new achievement record
        new_achievement = Achievement(
            user_id=user.id,
            username=row[1],
            achievement_id=row[2],
            achievement_name=row[3] if len(row) > 3 else "",
            description=row[4] if len(row) > 4 else "",
            category="general",
            rarity="common",
            points=10,
            progress_current=1,
            progress_required=1,
            is_completed=True,
            unlocked_at=row[5] if len(row) > 5 else func.now(),
        )

        session.add(new_achievement)
        return 1

    except Exception as e:
        logger.error(f"Failed to migrate achievement row: {e}")
        return 0


def verify_migration(sqlite_engine, pg_engine):
    """Verify that the migration was successful"""
    try:
        from sqlalchemy import text
        from db.session import session_scope

        logger.info("Verifying migration...")

        # Count records in both databases
        verification_results = {}

        with sqlite_engine.connect() as sqlite_conn:
            with session_scope() as pg_session:
                if pg_session is None:
                    logger.error("Failed to get PostgreSQL session for verification")
                    return False

                tables = ["users", "game_scores", "game_settings", "achievements"]

                for table in tables:
                    try:
                        # Count SQLite records
                        sqlite_result = sqlite_conn.execute(
                            text(f"SELECT COUNT(*) FROM {table}")
                        )
                        sqlite_count = sqlite_result.scalar()
                    except:
                        sqlite_count = 0

                    try:
                        # Count PostgreSQL records
                        if table == "users":
                            from db.models import User

                            pg_count = pg_session.query(User).count()
                        elif table == "game_scores":
                            from db.models import GameScore

                            pg_count = pg_session.query(GameScore).count()
                        elif table == "game_settings":
                            from db.models import GameSettings

                            pg_count = pg_session.query(GameSettings).count()
                        elif table == "achievements":
                            from db.models import Achievement

                            pg_count = pg_session.query(Achievement).count()
                        else:
                            pg_count = 0
                    except:
                        pg_count = 0

                    verification_results[table] = {
                        "sqlite": sqlite_count,
                        "postgresql": pg_count,
                        "match": sqlite_count == pg_count,
                    }

                    logger.info(
                        f"{table}: SQLite={sqlite_count}, PostgreSQL={pg_count}, Match={sqlite_count == pg_count}"
                    )

        # Check if all tables match
        all_match = all(result["match"] for result in verification_results.values())

        if all_match:
            logger.info(
                "✅ Migration verification successful - all record counts match"
            )
        else:
            logger.warning("⚠️  Migration verification: some record counts don't match")
            for table, result in verification_results.items():
                if not result["match"]:
                    logger.warning(
                        f"  {table}: Expected {result['sqlite']}, got {result['postgresql']}"
                    )

        return all_match

    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        logger.debug(traceback.format_exc())
        return False


def main():
    """Main migration function"""
    logger.info("Starting DENSO Tetris database migration...")

    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed")
        return False

    # Get SQLite database path
    sqlite_path = input(
        "Enter the path to your SQLite database file (default: ./tetris.db): "
    ).strip()
    if not sqlite_path:
        sqlite_path = "./tetris.db"

    if not os.path.exists(sqlite_path):
        logger.error(f"SQLite database not found: {sqlite_path}")
        return False

    # Create backup of SQLite database
    backup_path = f"{sqlite_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil

        shutil.copy2(sqlite_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    except Exception as e:
        logger.warning(f"Failed to create backup: {e}")

    # Connect to databases
    sqlite_engine = create_sqlite_engine(sqlite_path)
    if not sqlite_engine:
        return False

    pg_engine = create_postgresql_engine()
    if not pg_engine:
        return False

    # Get schema and migrate data
    schema = get_sqlite_schema()
    if not schema:
        logger.error("Failed to get SQLite schema")
        return False

    success = True
    for table_name, columns in schema.items():
        if not migrate_table_data(sqlite_engine, pg_engine, table_name, columns):
            logger.error(f"Failed to migrate table: {table_name}")
            success = False

    if success:
        # Verify migration
        if verify_migration(sqlite_engine, pg_engine):
            logger.info("✅ Database migration completed successfully!")
        else:
            logger.warning("⚠️  Migration completed but verification failed")
            success = False

    return success


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎮 Database migration completed successfully!")
            print("Your data has been migrated to the Neon PostgreSQL database.")
            print("You can now run the game with: python main.py")
        else:
            print("\n❌ Database migration failed. Please check the logs for details.")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during migration: {e}")
        logger.debug(traceback.format_exc())
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
