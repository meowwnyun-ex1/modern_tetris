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
import re

from db.queries import authenticate_user, register_user
from utils.logger import get_logger


logger = get_logger("tetris.auth")


def hash_password(password):
    try:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        return None


def verify_password(password, hashed_password):
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def validate_username(username):
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
    if not password:
        return False, "Password cannot be empty"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""


def validate_email(email):
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format"
    return True, ""


def login_user(username, password):
    try:
        user = authenticate_user(username, password)
        if user:
            logger.info(f"User {username} logged in successfully")
            return True
        return False
    except Exception as e:
        logger.error(f"Error logging in user {username}: {e}")
        return False


def create_user(username, password, email=None):
    try:
        valid_username, username_error = validate_username(username)
        valid_password, password_error = validate_password(password)
        valid_email, email_error = validate_email(email) if email else (True, "")

        if not (valid_username and valid_password and valid_email):
            return False, username_error or password_error or email_error

        if register_user(username, password):
            logger.info(f"User {username} created successfully")
            return True, ""
        return False, "Failed to create user"
    except Exception as e:
        logger.error(f"Error creating user {username}: {e}")
        return False, "An error occurred"
