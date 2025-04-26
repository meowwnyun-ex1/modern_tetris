#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Auth Utilities
----------------------------
Functions for user authentication and security systems
"""

import bcrypt
import hashlib
import random
import string
import logging
import re

from db.queries import authenticate_user, register_user
from utils.logger import get_logger


logger = get_logger("tetris.auth")


def hash_password(password):
    """
    Hash password using bcrypt

    Args:
        password (str): Password to hash

    Returns:
        str: Hashed password
    """
    try:
        # Hash password with bcrypt
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        return None


def verify_password(password, hashed_password):
    """
    Verify password against stored hash

    Args:
        password (str): Password to verify
        hashed_password (str): Stored hashed password

    Returns:
        bool: True if password is correct
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def generate_session_id():
    """
    Generate random session ID

    Returns:
        str: Session ID
    """
    # Generate random string
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=32))

    # Hash with SHA-256
    return hashlib.sha256(random_string.encode("utf-8")).hexdigest()


def validate_username(username):
    """
    Validate username format

    Args:
        username (str): Username to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 20:
        return False, "Username must be at most 20 characters"

    # Check for valid characters (letters, numbers, underscore, hyphen)
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return (
            False,
            "Username can only contain letters, numbers, underscore, and hyphen",
        )

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
        return False, "Password is required"

    if len(password) < 6:
        return False, "Password must be at least 6 characters"

    # Check for minimum complexity (optional)
    # has_upper = any(c.isupper() for c in password)
    # has_lower = any(c.islower() for c in password)
    # has_digit = any(c.isdigit() for c in password)
    # if not (has_upper and has_lower and has_digit):
    #    return False, "Password must include uppercase, lowercase and numbers"

    return True, ""


def validate_email(email):
    """
    Validate email format (basic validation)

    Args:
        email (str): Email to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not email:
        return True, ""  # Email is optional

    if "@" not in email or "." not in email:
        return False, "Invalid email format"

    if len(email) < 5:
        return False, "Invalid email format"

    return True, ""


def login_user(username, password):
    """
    Log in user with better error handling

    Args:
        username (str): Username
        password (str): Password

    Returns:
        dict: User data or None if login failed
    """
    try:
        # Validate inputs
        username_valid, username_error = validate_username(username)
        if not username_valid:
            logger.warning(f"Login failed: {username_error}")
            return None, username_error

        password_valid, password_error = validate_password(password)
        if not password_valid:
            logger.warning(f"Login failed: {password_error}")
            return None, password_error

        # Authenticate
        if authenticate_user(username, password):
            # Login successful
            session_id = generate_session_id()

            # Create user data
            user_data = {
                "username": username,
                "session_id": session_id,
                "logged_in": True,
            }

            logger.info(f"User {username} logged in successfully")
            return user_data, "Login successful"
        else:
            logger.warning(f"Login failed for user {username}")
            return None, "Invalid username or password"
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return None, f"Login system error: {str(e)}"


def create_user(username, password, email=None):
    """
    Create new user with validation

    Args:
        username (str): Username
        password (str): Password
        email (str, optional): Email

    Returns:
        tuple: (success, message)
    """
    try:
        # Validate username
        username_valid, username_error = validate_username(username)
        if not username_valid:
            return False, username_error

        # Validate password
        password_valid, password_error = validate_password(password)
        if not password_valid:
            return False, password_error

        # Validate email if provided
        if email:
            email_valid, email_error = validate_email(email)
            if not email_valid:
                return False, email_error

        # Register user
        success = register_user(username, password)
        if success:
            logger.info(f"User {username} registered successfully")
            return True, "Registration successful"
        else:
            logger.warning(f"Registration failed - username {username} already exists")
            return False, "Username already exists"

    except Exception as e:
        logger.error(f"Error during user creation: {e}")
        return False, f"Registration system error: {str(e)}"
