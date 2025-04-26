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


def setup_logger(console_level=logging.INFO):
    """Setup logging system with detailed configuration"""

    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Set filename with current date and time
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"tetris_{current_time}.log")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add file handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # Add rotating file handler for size management
    rotating_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 5MB
    )
    rotating_handler.setLevel(logging.DEBUG)
    rotating_handler.setFormatter(file_format)
    root_logger.addHandler(rotating_handler)

    return root_logger


def get_logger(name="tetris"):
    """Get logger for specific module"""
    return logging.getLogger(name)
