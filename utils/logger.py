#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Logger
--------------------
Functions for setting up and using the logging system
"""

import os
import datetime
import logging
import logging.handlers
import traceback
from pathlib import Path


def setup_logger(console_level=logging.INFO):
    """
    Setup logging system with detailed configuration

    Args:
        console_level (int): Logging level for console output

    Returns:
        logging.Logger: Configured root logger
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True, parents=True)

    # Get root logger
    root_logger = logging.getLogger()

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set base level to DEBUG to capture all logs
    root_logger.setLevel(logging.DEBUG)

    # Set filename with current date and time
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"tetris_{current_time}.log"

    # Add file handler
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to set up file handler: {e}")
        # Continue anyway - we'll set up console handler

    # Add console handler
    try:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_format = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_format)
        root_logger.addHandler(console_handler)
    except Exception as e:
        print(f"Failed to set up console handler: {e}")

    # Add rotating file handler for size management
    try:
        rotating_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 5MB
        )
        rotating_handler.setLevel(logging.DEBUG)
        rotating_handler.setFormatter(file_format)
        root_logger.addHandler(rotating_handler)
    except Exception as e:
        print(f"Failed to set up rotating file handler: {e}")

    # Log startup message
    root_logger.info(f"Logging initialized at {datetime.datetime.now().isoformat()}")

    # Log Python version and platform info
    try:
        import sys
        import platform

        root_logger.info(f"Python version: {sys.version}")
        root_logger.info(f"Platform: {platform.platform()}")
    except Exception as e:
        root_logger.error(f"Failed to log system info: {e}")

    return root_logger


def get_logger(name="tetris"):
    """
    Get logger for specific module

    Args:
        name (str): Logger name/category

    Returns:
        logging.Logger: Logger for the specified name
    """
    logger = logging.getLogger(name)

    # If no handlers are configured (root logger not set up yet)
    if not logger.handlers and not logging.getLogger().handlers:
        # Set up a minimal console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # This logger won't propagate to root logger
        logger.propagate = False

    return logger


def log_exception(logger, e, message="An error occurred"):
    """
    Helper function to log exceptions with traceback

    Args:
        logger (logging.Logger): Logger to use
        e (Exception): The exception to log
        message (str): Additional message to prepend
    """
    logger.error(f"{message}: {str(e)}")
    logger.debug("".join(traceback.format_exception(type(e), e, e.__traceback__)))
