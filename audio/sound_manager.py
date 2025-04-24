#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Sound Manager
---------------------------
Class for managing game sounds and music
"""

import os
import pygame
import logging

from core.constants import SOUNDS_DIR, SOUND_FILES, MUSIC_FILES
from utils.logger import get_logger


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

        # Check if pygame.mixer is initialized
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception as e:
                self.logger.error(f"Could not initialize pygame.mixer: {e}")
                return

        # Set volume levels
        self.music_volume = config["audio"]["music_volume"]
        self.sfx_volume = config["audio"]["sfx_volume"]

        # Load all sound effects
        self.sounds = {}
        self._load_sounds()

        # Variable for music
        self.current_music = None

    def _load_sounds(self):
        """Load all sound files"""
        try:
            for sound_name, file_name in SOUND_FILES.items():
                file_path = os.path.join(SOUNDS_DIR, file_name)

                if os.path.exists(file_path):
                    self.sounds[sound_name] = pygame.mixer.Sound(file_path)
                    self.sounds[sound_name].set_volume(self.sfx_volume)
                else:
                    self.logger.warning(f"Sound file not found: {file_path}")
        except Exception as e:
            self.logger.error(f"Error loading sound files: {e}")

    def play_sound(self, sound_name):
        """
        Play a sound effect

        Args:
            sound_name (str): Sound name (from SOUND_FILES)
        """
        if not self.config["audio"]["enable_sfx"]:
            return

        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                self.logger.error(f"Error playing sound {sound_name}: {e}")
        else:
            self.logger.warning(f"Sound {sound_name} not found")

    def play_music(self, music_name):
        """
        Play background music

        Args:
            music_name (str): Music name (from MUSIC_FILES)
        """
        if not self.config["audio"]["enable_music"]:
            return

        # Don't replay if it's the same music
        if self.current_music == music_name:
            return

        if music_name in MUSIC_FILES:
            try:
                file_name = MUSIC_FILES[music_name]
                file_path = os.path.join(SOUNDS_DIR, file_name)

                if os.path.exists(file_path):
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.set_volume(self.music_volume)
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                    self.current_music = music_name
                else:
                    self.logger.warning(f"Music file not found: {file_path}")
            except Exception as e:
                self.logger.error(f"Error playing music {music_name}: {e}")
        else:
            self.logger.warning(f"Music {music_name} not found")

    def stop_music(self):
        """Stop current music"""
        try:
            pygame.mixer.music.stop()
            self.current_music = None
        except Exception as e:
            self.logger.error(f"Error stopping music: {e}")

    def pause_music(self):
        """Pause music temporarily"""
        try:
            pygame.mixer.music.pause()
        except Exception as e:
            self.logger.error(f"Error pausing music: {e}")

    def unpause_music(self):
        """Resume music"""
        try:
            pygame.mixer.music.unpause()
        except Exception as e:
            self.logger.error(f"Error resuming music: {e}")

    def set_music_volume(self, volume):
        """
        Set music volume

        Args:
            volume (float): Volume level (0.0 - 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except Exception as e:
            self.logger.error(f"Error setting music volume: {e}")

    def set_sfx_volume(self, volume):
        """
        Set sound effects volume

        Args:
            volume (float): Volume level (0.0 - 1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))

        # Adjust volume for all effects
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
