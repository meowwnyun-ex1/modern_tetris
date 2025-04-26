#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Logger
--------------------
Functions for setting up and using the logging system
"""

import os
import logging
import datetime


def setup_logger(console_level=logging.INFO):
    """
    Setup logging system with detailed configuration

    Args:
        console_level: Logging level for console output
    """
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Set filename with current date and time
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"tetris_{current_time}.log")

    # Configure log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    try:
        # Add file handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)

        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(console_handler)
    except Exception as e:
        # If log setup fails, create a basic console logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(console_handler)

        root_logger.error(f"Error setting up logger: {e}")

    # Create game logger
    game_logger = logging.getLogger("tetris")
    game_logger.info(f"Started logging system at {current_time}")


def get_logger(name="tetris"):
    """
    Get a logger object

    Args:
        name (str, optional): Logger name

    Returns:
        logging.Logger: Logger object
    """
    logger = logging.getLogger(name)

    # Ensure there's at least a console handler if no handlers
    if not logger.handlers and not logging.getLogger().handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    return logger
