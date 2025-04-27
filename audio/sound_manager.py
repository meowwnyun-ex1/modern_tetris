#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Sound Manager
---------------------------
Class for managing game sounds and music with improved error handling
"""

import os
import logging
import time
from pathlib import Path

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame

        print("Using pygame-ce instead of pygame")
    except ImportError:
        print("Please install pygame or pygame-ce")
        import sys

        sys.exit(1)

# Import constants safely with error handling
try:
    from core.constants import SOUNDS_DIR, SOUND_FILES, MUSIC_FILES
except ImportError:
    # Fallback if import fails
    SOUNDS_DIR = Path("assets/sounds")
    SOUND_FILES = {
        "move": "move.wav",
        "rotate": "rotate.wav",
        "drop": "drop.wav",
        "clear": "clear.wav",
        "tetris": "tetris.wav",
        "level_up": "level_up.wav",
        "game_over": "game_over.wav",
        "menu_select": "menu_select.wav",
        "menu_change": "menu_change.wav",
    }
    MUSIC_FILES = {
        "menu": "menu_theme.mp3",
        "game": "game_theme.mp3",
    }

try:
    from utils.logger import get_logger
except ImportError:
    # Fallback logger if import fails
    def get_logger():
        logger = logging.getLogger("tetris.sound")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


class SoundManager:
    """Class for managing game sounds and music"""

    def __init__(self, config):
        """
        Create a new sound manager

        Args:
            config (dict): Game configuration
        """
        self.config = config
        self.logger = get_logger()

        # Initialize variables
        self.sounds = {}
        self.current_music = None
        self.music_volume = 0.7
        self.sfx_volume = 0.7
        self.initialized = False

        # Try to initialize pygame mixer
        self._initialize_mixer()

        if self.initialized:
            # Set volume levels from config
            self.music_volume = config["audio"]["music_volume"]
            self.sfx_volume = config["audio"]["sfx_volume"]

            # Load sound effects
            self._load_sounds()

    def _initialize_mixer(self):
        """Initialize pygame mixer with error handling"""
        try:
            if pygame.mixer.get_init():
                self.initialized = True
                return

            # Try to initialize mixer
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.initialized = True
            self.logger.info("Sound system initialized successfully")

        except Exception as e:
            self.logger.error(f"Could not initialize pygame.mixer: {e}")
            self.initialized = False

    def _load_sounds(self):
        """Load all sound files with error handling"""
        if not self.initialized:
            return

        try:
            # Check if sounds directory exists
            sound_dir = Path(SOUNDS_DIR)
            if not sound_dir.exists():
                sound_dir.mkdir(exist_ok=True, parents=True)
                self.logger.warning(f"Created sounds directory: {sound_dir}")

            # Load each sound effect
            for sound_name, file_name in SOUND_FILES.items():
                file_path = sound_dir / file_name

                if file_path.exists():
                    try:
                        self.sounds[sound_name] = pygame.mixer.Sound(str(file_path))
                        self.sounds[sound_name].set_volume(self.sfx_volume)
                    except Exception as e:
                        self.logger.error(f"Error loading sound {file_name}: {e}")
                else:
                    self.logger.warning(f"Sound file not found: {file_path}")

                    # Create empty dummy sound to prevent errors
                    try:
                        self.sounds[sound_name] = pygame.mixer.Sound(
                            buffer=bytearray(100)
                        )
                        self.sounds[sound_name].set_volume(0)
                    except Exception as e:
                        self.logger.error(f"Could not create dummy sound: {e}")

        except Exception as e:
            self.logger.error(f"Error loading sound files: {e}")
            # Continue without sound effects rather than crashing

    def play_sound(self, sound_name):
        """
        Play a sound effect

        Args:
            sound_name (str): Name of the sound to play
        """
        if not self.initialized or not self.config["audio"]["enable_sfx"]:
            return

        try:
            if sound_name in self.sounds:
                # Check if it's a valid Sound object
                if hasattr(self.sounds[sound_name], "play"):
                    self.sounds[sound_name].play()
                else:
                    # Create dummy sound if not a Sound object
                    self.sounds[sound_name] = pygame.mixer.Sound(buffer=bytearray(32))
                    self.sounds[sound_name].set_volume(0)
            else:
                self.logger.warning(f"Sound '{sound_name}' not found")
        except Exception as e:
            self.logger.warning(f"Error playing sound {sound_name}: {e}")

    def play_music(self, music_name):
        """
        Play background music with improved error handling

        Args:
            music_name (str): Music name (from MUSIC_FILES)
        """
        # Skip if music is disabled
        if not self.initialized or not self.config["audio"]["enable_music"]:
            return

        # Don't replay if it's the same music
        if self.current_music == music_name:
            return

        # Try to play music
        try:
            if music_name in MUSIC_FILES:
                file_name = MUSIC_FILES[music_name]
                file_path = Path(SOUNDS_DIR) / file_name

                if file_path.exists():
                    # Stop any current music first
                    pygame.mixer.music.stop()

                    # Load and play new music
                    pygame.mixer.music.load(str(file_path))
                    pygame.mixer.music.set_volume(self.music_volume)
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                    self.current_music = music_name
                else:
                    self.logger.warning(f"Music file not found: {file_path}")
            else:
                self.logger.warning(f"Music '{music_name}' not defined")

        except Exception as e:
            self.logger.error(f"Error playing music {music_name}: {e}")
            # Continue without crashing

    def stop_music(self):
        """Stop current music with error handling"""
        if not self.initialized:
            return

        try:
            pygame.mixer.music.stop()
            self.current_music = None
        except Exception as e:
            self.logger.error(f"Error stopping music: {e}")

    def pause_music(self):
        """Pause music temporarily with error handling"""
        if not self.initialized:
            return

        try:
            pygame.mixer.music.pause()
        except Exception as e:
            self.logger.error(f"Error pausing music: {e}")

    def unpause_music(self):
        """Resume music with error handling"""
        if not self.initialized:
            return

        try:
            pygame.mixer.music.unpause()
        except Exception as e:
            self.logger.error(f"Error resuming music: {e}")

    def set_music_volume(self, volume):
        """
        Set music volume with validation

        Args:
            volume (float): Volume level (0.0 - 1.0)
        """
        if not self.initialized:
            return

        # Ensure volume is in valid range
        self.music_volume = max(0.0, min(1.0, volume))

        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except Exception as e:
            self.logger.error(f"Error setting music volume: {e}")

    def set_sfx_volume(self, volume):
        """
        Set sound effects volume with validation

        Args:
            volume (float): Volume level (0.0 - 1.0)
        """
        if not self.initialized:
            return

        # Ensure volume is in valid range
        self.sfx_volume = max(0.0, min(1.0, volume))

        # Adjust volume for all effects
        try:
            for sound in self.sounds.values():
                if hasattr(sound, "set_volume"):
                    sound.set_volume(self.sfx_volume)
        except Exception as e:
            self.logger.error(f"Error setting SFX volume: {e}")
