#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Sound Manager
---------------------------
คลาสสำหรับจัดการเสียงและเพลงในเกม
"""

import os
import pygame
import logging

from core.constants import SOUNDS_DIR, SOUND_FILES, MUSIC_FILES
from utils.logger import get_logger


class SoundManager:
    """คลาสสำหรับจัดการเสียงและเพลงในเกม"""

    def __init__(self, config):
        """
        สร้างตัวจัดการเสียงใหม่

        Args:
            config (dict): การตั้งค่าเกม
        """
        self.config = config
        self.logger = get_logger()

        # ตรวจสอบว่า pygame.mixer ถูกเริ่มต้นแล้วหรือไม่
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception as e:
                self.logger.error(f"ไม่สามารถเริ่มต้น pygame.mixer ได้: {e}")
                return

        # ตั้งค่าระดับเสียง
        self.music_volume = config["audio"]["music_volume"]
        self.sfx_volume = config["audio"]["sfx_volume"]

        # โหลดเสียงเอฟเฟกต์ทั้งหมด
        self.sounds = {}
        self._load_sounds()

        # ตัวแปรสำหรับเพลง
        self.current_music = None

    def _load_sounds(self):
        """โหลดไฟล์เสียงทั้งหมด"""
        try:
            for sound_name, file_name in SOUND_FILES.items():
                file_path = os.path.join(SOUNDS_DIR, file_name)

                if os.path.exists(file_path):
                    self.sounds[sound_name] = pygame.mixer.Sound(file_path)
                    self.sounds[sound_name].set_volume(self.sfx_volume)
                else:
                    self.logger.warning(f"ไม่พบไฟล์เสียง: {file_path}")
        except Exception as e:
            self.logger.error(f"เกิดข้อผิดพลาดในการโหลดไฟล์เสียง: {e}")

    def play_sound(self, sound_name):
        """
        เล่นเสียงเอฟเฟกต์

        Args:
            sound_name (str): ชื่อเสียง (จาก SOUND_FILES)
        """
        if not self.config["audio"]["enable_sfx"]:
            return

        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                self.logger.error(f"เกิดข้อผิดพลาดในการเล่นเสียง {sound_name}: {e}")
        else:
            self.logger.warning(f"ไม่พบเสียง {sound_name}")

    def play_music(self, music_name):
        """
        เล่นเพลงพื้นหลัง

        Args:
            music_name (str): ชื่อเพลง (จาก MUSIC_FILES)
        """
        if not self.config["audio"]["enable_music"]:
            return

        # ไม่เล่นซ้ำถ้าเป็นเพลงเดียวกัน
        if self.current_music == music_name:
            return

        if music_name in MUSIC_FILES:
            try:
                file_name = MUSIC_FILES[music_name]
                file_path = os.path.join(SOUNDS_DIR, file_name)

                if os.path.exists(file_path):
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.set_volume(self.music_volume)
                    pygame.mixer.music.play(-1)  # วนซ้ำไม่จำกัด
                    self.current_music = music_name
                else:
                    self.logger.warning(f"ไม่พบไฟล์เพลง: {file_path}")
            except Exception as e:
                self.logger.error(f"เกิดข้อผิดพลาดในการเล่นเพลง {music_name}: {e}")
        else:
            self.logger.warning(f"ไม่พบเพลง {music_name}")

    def stop_music(self):
        """หยุดเพลงปัจจุบัน"""
        try:
            pygame.mixer.music.stop()
            self.current_music = None
        except Exception as e:
            self.logger.error(f"เกิดข้อผิดพลาดในการหยุดเพลง: {e}")

    def pause_music(self):
        """หยุดเพลงชั่วคราว"""
        try:
            pygame.mixer.music.pause()
        except Exception as e:
            self.logger.error(f"เกิดข้อผิดพลาดในการหยุดเพลงชั่วคราว: {e}")

    def unpause_music(self):
        """เล่นเพลงต่อ"""
        try:
            pygame.mixer.music.unpause()
        except Exception as e:
            self.logger.error(f"เกิดข้อผิดพลาดในการเล่นเพลงต่อ: {e}")

    def set_music_volume(self, volume):
        """
        ตั้งค่าระดับเสียงเพลง

        Args:
            volume (float): ระดับเสียง (0.0 - 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except Exception as e:
            self.logger.error(f"เกิดข้อผิดพลาดในการตั้งค่าระดับเสียงเพลง: {e}")

    def set_sfx_volume(self, volume):
        """
        ตั้งค่าระดับเสียงเอฟเฟกต์

        Args:
            volume (float): ระดับเสียง (0.0 - 1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))

        # ปรับระดับเสียงของทุกเอฟเฟกต์
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
