#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Database Setup Script
-----------------------------------
Script to set up and initialize the Neon PostgreSQL database
"""

import os
import sys
import logging
import traceback
from pathlib import Path

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
    handlers=[logging.StreamHandler(), logging.FileHandler("database_setup.log")],
)

logger = logging.getLogger("tetris.db.setup")


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


def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = ["DATABASE_URL"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        logger.error("Please set the following in your .env file or environment:")
        logger.error(
            "DATABASE_URL=postgres://user:password@host:port/database?sslmode=require"
        )
        return False

    database_url = os.getenv("DATABASE_URL")
    if not (
        database_url.startswith("postgres://")
        or database_url.startswith("postgresql://")
    ):
        logger.error("DATABASE_URL must be a valid PostgreSQL connection string")
        return False

    logger.info("Environment variables validated successfully")
    return True


def test_database_connection():
    """Test the database connection"""
    try:
        from db.session import init_db, check_database_health

        logger.info("Testing database connection...")

        if not init_db():
            logger.error("Failed to initialize database connection")
            return False

        health_info = check_database_health()
        if health_info["status"] != "healthy":
            logger.error(f"Database health check failed: {health_info}")
            return False

        logger.info("Database connection test successful")
        logger.info(f"Database engine: {health_info['engine_type']}")
        logger.info(f"Tables exist: {health_info['tables_exist']}")

        return True

    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        logger.debug(traceback.format_exc())
        return False


def create_tables():
    """Create database tables"""
    try:
        from db.models import Base
        from db.session import engine

        if not engine:
            logger.error("Database engine not initialized")
            return False

        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")

        # Verify tables were created
        from sqlalchemy import text

        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                result = conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' ORDER BY table_name"
                    )
                )
            else:
                result = conn.execute(
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    )
                )

            tables = [row[0] for row in result]
            logger.info(f"Created tables: {', '.join(tables)}")

        return True

    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        logger.debug(traceback.format_exc())
        return False


def create_admin_user():
    """Create an admin user for testing"""
    try:
        from db.queries import register_user, authenticate_user

        # Default admin credentials
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@denso-tetris.local")

        logger.info(f"Creating admin user: {admin_username}")

        if register_user(admin_username, admin_password, admin_email):
            logger.info("Admin user created successfully")

            # Test login
            if authenticate_user(admin_username, admin_password):
                logger.info("Admin user authentication test passed")
                return True
            else:
                logger.error("Admin user authentication test failed")
                return False
        else:
            logger.warning("Admin user creation failed (may already exist)")

            # Try to authenticate existing user
            if authenticate_user(admin_username, admin_password):
                logger.info("Existing admin user authenticated successfully")
                return True
            else:
                logger.error("Cannot authenticate admin user")
                return False

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        logger.debug(traceback.format_exc())
        return False


def seed_sample_data():
    """Seed the database with sample data for testing"""
    try:
        from db.queries import register_user, save_game_score, unlock_achievement
        import random

        logger.info("Seeding sample data...")

        # Create sample users
        sample_users = [
            ("player1", "password123", "player1@example.com"),
            ("player2", "password123", "player2@example.com"),
            ("tetris_master", "password123", "master@example.com"),
        ]

        for username, password, email in sample_users:
            if register_user(username, password, email):
                logger.info(f"Created sample user: {username}")

                # Add sample scores
                for i in range(random.randint(3, 8)):
                    score = random.randint(1000, 50000)
                    level = random.randint(1, 15)
                    lines = random.randint(10, 200)
                    time_played = random.uniform(120, 1800)  # 2-30 minutes
                    victory = random.choice([True, False]) if level >= 10 else False

                    save_game_score(username, score, level, lines, time_played, victory)

                # Add sample achievements
                if username == "tetris_master":
                    achievements = [
                        ("score_10k", "Score Master", "Scored over 10,000 points"),
                        ("level_10", "Level 10", "Reached level 10"),
                        ("tetris", "Tetris Master", "Cleared 4 lines at once"),
                    ]

                    for ach_id, name, desc in achievements:
                        unlock_achievement(username, ach_id, name, desc)

        logger.info("Sample data seeded successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to seed sample data: {e}")
        logger.debug(traceback.format_exc())
        return False


def verify_setup():
    """Verify the database setup is working correctly"""
    try:
        from db.queries import get_top_scores, get_user_stats, check_database_connection

        logger.info("Verifying database setup...")

        # Test database connection
        health = check_database_connection()
        if health["status"] != "healthy":
            logger.error(f"Database health check failed: {health}")
            return False

        # Test queries
        top_scores = get_top_scores(5)
        logger.info(f"Found {len(top_scores)} top scores")

        # Test user stats
        stats = get_user_stats("admin")
        if stats:
            logger.info(
                f"Admin user stats retrieved: {stats['total_games']} games played"
            )

        logger.info("Database setup verification completed successfully")
        return True

    except Exception as e:
        logger.error(f"Setup verification failed: {e}")
        logger.debug(traceback.format_exc())
        return False


def main():
    """Main setup function"""
    logger.info("Starting DENSO Tetris database setup...")

    # Step 1: Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed")
        return False

    # Step 2: Check environment variables
    if not check_environment_variables():
        logger.error("Environment variable check failed")
        return False

    # Step 3: Test database connection
    if not test_database_connection():
        logger.error("Database connection test failed")
        return False

    # Step 4: Create tables
    if not create_tables():
        logger.error("Table creation failed")
        return False

    # Step 5: Create admin user
    if not create_admin_user():
        logger.error("Admin user creation failed")
        return False

    # Step 6: Seed sample data (optional)
    create_sample_data = (
        input("Do you want to create sample data for testing? (y/N): ").lower().strip()
    )
    if create_sample_data in ["y", "yes"]:
        if not seed_sample_data():
            logger.warning("Sample data creation failed")

    # Step 7: Verify setup
    if not verify_setup():
        logger.error("Setup verification failed")
        return False

    logger.info("✅ Database setup completed successfully!")
    logger.info("You can now run the DENSO Tetris game with: python main.py")

    # Print connection info
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        # Mask password for logging
        masked_url = database_url
        if "@" in masked_url:
            parts = masked_url.split("@")
            if ":" in parts[0]:
                user_parts = parts[0].split(":")
                if len(user_parts) >= 3:
                    # postgres://user:password@host... -> postgres://user:****@host...
                    user_parts[-1] = "****"
                    parts[0] = ":".join(user_parts)
            masked_url = "@".join(parts)

        logger.info(f"Connected to: {masked_url}")

    return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎮 DENSO Tetris database setup completed successfully!")
            print("You can now start the game with: python main.py")
            sys.exit(0)
        else:
            print("\n❌ Database setup failed. Please check the logs for details.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during setup: {e}")
        logger.debug(traceback.format_exc())
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
