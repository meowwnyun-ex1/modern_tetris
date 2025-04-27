#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Auth Utilities
----------------------------
Functions for user authentication and security systems
"""

import re
import logging
from utils.logger import get_logger

# Try to import bcrypt for password hashing
try:
    import bcrypt

    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False
    logging.warning("bcrypt not available. Password security will be limited.")

# Try to import database functions
try:
    from db.queries import authenticate_user, register_user

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("Database functions not available. Auth will use fallback mode.")

logger = get_logger("tetris.auth")

# If database is not available, we'll keep users in memory (for development/testing)
_memory_users = {}


def hash_password(password):
    """
    Hash password securely

    Args:
        password (str): Plain text password

    Returns:
        str: Hashed password or None if hashing fails
    """
    if not BCRYPT_AVAILABLE:
        logger.warning("bcrypt not available, returning simple hash (NOT SECURE)")
        # Very basic hash - not secure!
        import hashlib

        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    try:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        return None


def verify_password(password, hashed_password):
    """
    Verify password against stored hash

    Args:
        password (str): Plain text password
        hashed_password (str): Stored password hash

    Returns:
        bool: True if password matches, False otherwise
    """
    if not BCRYPT_AVAILABLE:
        logger.warning(
            "bcrypt not available, using simple hash comparison (NOT SECURE)"
        )
        import hashlib

        return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed_password

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def validate_username(username):
    """
    Validate username format

    Args:
        username (str): Username to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 20:
        return False, "Username cannot exceed 20 characters"
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, "Username contains invalid characters"
    return True, ""


def validate_password(password):
    """
    Validate password strength

    Args:
        password (str): Password to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""


def validate_email(email):
    """
    Validate email format

    Args:
        email (str): Email to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not email:
        return True, ""  # Email is optional

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format"
    return True, ""


def login_user(username, password):
    """
    Log in a user

    Args:
        username (str): Username
        password (str): Password

    Returns:
        bool: True if login successful
    """
    if DB_AVAILABLE:
        try:
            # Use database authentication
            result = authenticate_user(username, password)
            if result:
                logger.info(f"User {username} logged in successfully")
            else:
                logger.warning(f"Failed login attempt for user {username}")
            return result
        except Exception as e:
            logger.error(f"Error logging in user {username}: {e}")
            return False
    else:
        # Fallback to memory-based authentication
        logger.warning("Using in-memory authentication (development mode)")
        if username in _memory_users:
            stored_hash = _memory_users[username]["password"]
            if verify_password(password, stored_hash):
                logger.info(f"User {username} logged in successfully (memory mode)")
                return True

        logger.warning(f"Failed login attempt for user {username} (memory mode)")
        return False


def create_user(username, password, email=None):
    """
    Create a new user

    Args:
        username (str): Username
        password (str): Password
        email (str, optional): Email address

    Returns:
        tuple: (success, error_message)
    """
    try:
        # Validate inputs
        valid_username, username_error = validate_username(username)
        valid_password, password_error = validate_password(password)
        valid_email, email_error = validate_email(email) if email else (True, "")

        if not (valid_username and valid_password and valid_email):
            return False, username_error or password_error or email_error

        if DB_AVAILABLE:
            # Use database registration
            if register_user(username, password):
                logger.info(f"User {username} created successfully")
                return True, ""
            return False, "Username already exists or registration failed"
        else:
            # Fallback to memory-based registration
            logger.warning("Using in-memory user registration (development mode)")
            if username in _memory_users:
                return False, "Username already exists"

            # Store user in memory
            hashed_pw = hash_password(password)
            if hashed_pw:
                _memory_users[username] = {"password": hashed_pw, "email": email}
                logger.info(f"User {username} created successfully (memory mode)")
                return True, ""
            return False, "Password hashing failed"

    except Exception as e:
        logger.error(f"Error creating user {username}: {e}")
        return False, f"An error occurred: {str(e)}"


def get_user_count():
    """
    Get the number of registered users

    Returns:
        int: Number of users
    """
    if DB_AVAILABLE:
        try:
            from db.session import session_scope
            from db.models import User

            with session_scope() as session:
                if session:
                    count = session.query(User).count()
                    return count
                return 0
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return 0
    else:
        # In-memory fallback
        return len(_memory_users)


def has_admin_user():
    """
    Check if at least one user exists (for first-run setup)

    Returns:
        bool: True if at least one user exists
    """
    return get_user_count() > 0


def reset_password(username, new_password):
    """
    Reset user password

    Args:
        username (str): Username
        new_password (str): New password

    Returns:
        bool: True if password was reset successfully
    """
    # Validate new password
    valid_password, error = validate_password(new_password)
    if not valid_password:
        logger.warning(f"Invalid new password for {username}: {error}")
        return False

    if DB_AVAILABLE:
        try:
            from db.session import session_scope
            from db.models import User

            with session_scope() as session:
                if not session:
                    return False

                user = session.query(User).filter_by(username=username).first()
                if not user:
                    logger.warning(f"User not found for password reset: {username}")
                    return False

                # Hash and store new password
                hashed_pw = hash_password(new_password)
                if not hashed_pw:
                    return False

                user.password_hash = hashed_pw
                logger.info(f"Password reset successful for {username}")
                return True
        except Exception as e:
            logger.error(f"Error resetting password for {username}: {e}")
            return False
    else:
        # In-memory fallback
        if username not in _memory_users:
            logger.warning(f"User not found for password reset: {username}")
            return False

        hashed_pw = hash_password(new_password)
        if not hashed_pw:
            return False

        _memory_users[username]["password"] = hashed_pw
        logger.info(f"Password reset successful for {username} (memory mode)")
        return True
