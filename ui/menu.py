#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modern Tetris - Menu UI
---------------------
คลาสสำหรับเมนูหลักและเมนูย่อยต่างๆ
"""

import pygame
import logging
import math  # เพิ่มบรรทัดนี้
from pygame.locals import *  # เพิ่มบรรทัดนี้

from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE
from core.game import Game
from audio.sound_manager import SoundManager
from db.queries import (
    get_top_scores,
    authenticate_user,
    register_user,
    get_user_settings,
)
from utils.logger import get_logger


class MainMenu:
    """คลาสสำหรับเมนูหลัก"""

    def __init__(self, screen, config):
        """
        สร้างเมนูหลักใหม่

        Args:
            screen (pygame.Surface): พื้นผิวหลักสำหรับการแสดงผล
            config (dict): การตั้งค่าเกม
        """
        self.screen = screen
        self.config = config
        self.logger = get_logger()

        # สร้างระบบเสียง
        self.sound_manager = SoundManager(config)

        # เริ่มเล่นเพลงเมนู
        self.sound_manager.play_music("menu")

        # สร้างพื้นผิวพื้นหลัง
        self.background = self._create_background()

        # นำเข้าฟอนต์
        pygame.font.init()
        try:
            self.title_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 72
            )
            self.large_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 36
            )
            self.medium_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 24
            )
            self.small_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', 18
            )
        except:
            # ใช้ฟอนต์ระบบถ้าโหลดไม่ได้
            self.title_font = pygame.font.SysFont("Arial", 72)
            self.large_font = pygame.font.SysFont("Arial", 36)
            self.medium_font = pygame.font.SysFont("Arial", 24)
            self.small_font = pygame.font.SysFont("Arial", 18)

        # รายการเมนู
        self.menu_items = ["เล่นเกม", "วิธีเล่น", "ตั้งค่า", "อันดับ", "ออกจากเกม"]
        self.selected_item = 0
        self.username = "Guest"  # ชื่อผู้เล่นเริ่มต้น

        # เอฟเฟกต์ animation
        self.animation_timer = 0
        self.animation_speed = 0.5  # รอบต่อวินาที

        # สถานะ
        self.current_menu = "main"  # main, play, howto, settings, leaderboard
        self.login_input = ""
        self.password_input = ""
        self.login_message = ""
        self.input_focus = "username"  # username, password
        self.leaderboard_data = []

        # โหลดข้อมูลผู้เล่นที่มีอันดับสูงสุด
        self._load_leaderboard()

    def _create_background(self):
        """
        สร้างพื้นหลังเมนู

        Returns:
            pygame.Surface: พื้นหลังที่สร้างขึ้น
        """
        # สร้างพื้นผิวใหม่
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # ไล่สีพื้นหลัง
        for y in range(SCREEN_HEIGHT):
            # ไล่สีจากด้านบนลงล่าง
            color = (
                int(20 + (y / SCREEN_HEIGHT) * 30),
                int(0 + (y / SCREEN_HEIGHT) * 20),
                int(50 + (y / SCREEN_HEIGHT) * 40),
            )
            pygame.draw.line(bg, color, (0, y), (SCREEN_WIDTH, y))

        # วาดลายแบบ grid
        grid_color = (50, 20, 80, 50)
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(bg, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)

        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(bg, grid_color, (0, y), (SCREEN_WIDTH, y), 1)

        return bg

    def _load_leaderboard(self):
        """โหลดข้อมูลตารางคะแนน"""
        try:
            self.leaderboard_data = get_top_scores(10)
        except Exception as e:
            self.logger.error(f"ไม่สามารถโหลดตารางคะแนนได้: {e}")
            self.leaderboard_data = []

    def handle_event(self, event):
        """
        จัดการกับเหตุการณ์อินพุต

        Args:
            event (pygame.event.Event): เหตุการณ์ที่จะจัดการ

        Returns:
            bool: True ถ้าจัดการเหตุการณ์, False ถ้าไม่ได้จัดการ
        """
        if self.current_menu == "main":
            return self._handle_main_menu_event(event)
        elif self.current_menu == "play":
            return self._handle_play_menu_event(event)
        elif self.current_menu == "howto":
            return self._handle_howto_menu_event(event)
        elif self.current_menu == "settings":
            return self._handle_settings_menu_event(event)
        elif self.current_menu == "leaderboard":
            return self._handle_leaderboard_menu_event(event)

        return False

    def _handle_main_menu_event(self, event):
        """จัดการกับเหตุการณ์ในเมนูหลัก"""
        if event.type == KEYDOWN:
            if event.key == K_UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
                self.sound_manager.play_sound("menu_change")
            elif event.key == K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
                self.sound_manager.play_sound("menu_change")
            elif event.key == K_RETURN:
                self.sound_manager.play_sound("menu_select")

                if self.menu_items[self.selected_item] == "เล่นเกม":
                    self.current_menu = "play"
                elif self.menu_items[self.selected_item] == "วิธีเล่น":
                    self.current_menu = "howto"
                elif self.menu_items[self.selected_item] == "ตั้งค่า":
                    self.current_menu = "settings"
                elif self.menu_items[self.selected_item] == "อันดับ":
                    self._load_leaderboard()
                    self.current_menu = "leaderboard"
                elif self.menu_items[self.selected_item] == "ออกจากเกม":
                    return pygame.event.post(pygame.event.Event(QUIT))

        return False

    def _handle_play_menu_event(self, event):
        """จัดการกับเหตุการณ์ในเมนูเริ่มเล่น"""
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self.current_menu = "main"
                self.sound_manager.play_sound("menu_change")
            elif event.key == K_RETURN:
                self.sound_manager.play_sound("menu_select")

                # สร้างเกมใหม่และเริ่มเล่น
                return Game(self.screen, self.config, self.username)
            elif event.key == K_BACKSPACE:
                if self.input_focus == "username":
                    self.login_input = self.login_input[:-1]
                else:
                    self.password_input = self.password_input[:-1]
            elif event.key == K_TAB:
                # สลับระหว่างช่องชื่อผู้ใช้และรหัสผ่าน
                self.input_focus = (
                    "password" if self.input_focus == "username" else "username"
                )
            elif event.unicode and ord(event.unicode) >= 32:
                # รับอินพุตตัวอักษร
                if self.input_focus == "username":
                    self.login_input += event.unicode
                else:
                    self.password_input += event.unicode

        # ตรวจสอบคลิกเมาส์
        if event.type == MOUSEBUTTONDOWN and event.button == 1:  # คลิกซ้าย
            # ตรวจสอบการคลิกปุ่มล็อกอิน
            login_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 400, 200, 50)
            if login_rect.collidepoint(event.pos):
                self._handle_login()

            # ตรวจสอบการคลิกปุ่มเล่นเลย
            play_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 470, 200, 50)
            if play_rect.collidepoint(event.pos):
                return Game(self.screen, self.config, self.username)

            # ตรวจสอบการคลิกปุ่มกลับ
            back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 540, 200, 50)
            if back_rect.collidepoint(event.pos):
                self.current_menu = "main"
                self.sound_manager.play_sound("menu_change")

            # ตรวจสอบการคลิกช่องชื่อผู้ใช้
            username_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 300, 300, 30)
            if username_rect.collidepoint(event.pos):
                self.input_focus = "username"

            # ตรวจสอบการคลิกช่องรหัสผ่าน
            password_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 350, 300, 30)
            if password_rect.collidepoint(event.pos):
                self.input_focus = "password"

        return False

    def _handle_howto_menu_event(self, event):
        """จัดการกับเหตุการณ์ในเมนูวิธีเล่น"""
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE or event.key == K_RETURN:
                self.current_menu = "main"
                self.sound_manager.play_sound("menu_change")

        return False

    def _handle_settings_menu_event(self, event):
        """จัดการกับเหตุการณ์ในเมนูตั้งค่า"""
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self.current_menu = "main"
                self.sound_manager.play_sound("menu_change")

        return False

    def _handle_leaderboard_menu_event(self, event):
        """จัดการกับเหตุการณ์ในเมนูตารางคะแนน"""
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE or event.key == K_RETURN:
                self.current_menu = "main"
                self.sound_manager.play_sound("menu_change")

        return False

    def _handle_login(self):
        """จัดการกับการล็อกอิน"""
        if not self.login_input or not self.password_input:
            self.login_message = "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"
            return

        try:
            # ตรวจสอบสิทธิ์
            if authenticate_user(self.login_input, self.password_input):
                self.username = self.login_input
                self.login_message = f"ล็อกอินสำเร็จ! ยินดีต้อนรับ {self.username}"

                # โหลดการตั้งค่าของผู้ใช้
                settings = get_user_settings(self.username)
                if settings:
                    # ใช้การตั้งค่าของผู้ใช้
                    # (ในตัวอย่างนี้ไม่ได้ใช้งานจริง)
                    pass
            else:
                self.login_message = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
        except Exception as e:
            self.logger.error(f"เกิดข้อผิดพลาดในการล็อกอิน: {e}")
            self.login_message = "เกิดข้อผิดพลาดในการล็อกอิน"

    def update(self, dt):
        """
        อัปเดตสถานะของเมนู

        Args:
            dt (float): เวลาที่ผ่านไปตั้งแต่การอัปเดตล่าสุด (วินาที)

        Returns:
            object: ซีนถัดไป (ถ้ามีการเปลี่ยนซีน) หรือ None
        """
        # อัปเดตตัวจับเวลาแอนิเมชัน
        self.animation_timer += dt * self.animation_speed

        # รักษาให้ animation_timer อยู่ระหว่าง 0-1
        self.animation_timer %= 1.0

        return None

    def render(self):
        """วาดเมนู"""
        # วาดพื้นหลัง
        self.screen.blit(self.background, (0, 0))

        if self.current_menu == "main":
            self._render_main_menu()
        elif self.current_menu == "play":
            self._render_play_menu()
        elif self.current_menu == "howto":
            self._render_howto_menu()
        elif self.current_menu == "settings":
            self._render_settings_menu()
        elif self.current_menu == "leaderboard":
            self._render_leaderboard_menu()

    def _render_main_menu(self):
        """วาดเมนูหลัก"""
        # วาดชื่อเกม
        title = self.title_font.render("MODERN TETRIS", True, (0, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # เอฟเฟกต์เรืองแสงสำหรับชื่อ
        glow_color = (
            0,
            200,
            200,
            int(100 + 100 * math.sin(self.animation_timer * 2 * math.pi)),
        )
        glow_title = self.title_font.render("MODERN TETRIS", True, glow_color)
        glow_rect = glow_title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(glow_title, glow_rect)

        # วาดรายการเมนู
        for i, item in enumerate(self.menu_items):
            if i == self.selected_item:
                # รายการที่เลือก
                color = (255, 255, 0)

                # เพิ่มสัญลักษณ์ > < รอบรายการที่เลือก
                selected_text = f"< {item} >"
                text = self.large_font.render(selected_text, True, color)

                # ทำเอฟเฟกต์เคลื่อนไหว
                offset = math.sin(self.animation_timer * 2 * math.pi) * 5
            else:
                # รายการอื่น ๆ
                color = (200, 200, 200)
                text = self.medium_font.render(item, True, color)
                offset = 0

            # ตำแหน่งของรายการเมนู
            y_position = 300 + i * 60
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2 + offset, y_position))
            self.screen.blit(text, text_rect)

        # วาดข้อความด้านล่าง
        version_text = self.small_font.render("เวอร์ชัน 1.0", True, (150, 150, 150))
        version_rect = version_text.get_rect(
            bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20)
        )
        self.screen.blit(version_text, version_rect)

        # วาดชื่อผู้เล่นปัจจุบัน
        user_text = self.small_font.render(
            f"ผู้เล่น: {self.username}", True, (150, 150, 150)
        )
        user_rect = user_text.get_rect(bottomleft=(20, SCREEN_HEIGHT - 20))
        self.screen.blit(user_text, user_rect)

    def _render_play_menu(self):
        """วาดเมนูเริ่มเล่น"""
        # วาดหัวข้อ
        title = self.large_font.render("เข้าสู่ระบบ", True, (0, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # วาดช่องชื่อผู้ใช้
        username_label = self.medium_font.render("ชื่อผู้ใช้:", True, WHITE)
        self.screen.blit(username_label, (SCREEN_WIDTH // 2 - 200, 300))

        # กรอบช่องชื่อผู้ใช้
        username_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 300, 300, 30)
        pygame.draw.rect(self.screen, (30, 30, 50), username_rect)
        pygame.draw.rect(
            self.screen,
            (200, 200, 200) if self.input_focus == "username" else (100, 100, 100),
            username_rect,
            2,
        )

        # ข้อความชื่อผู้ใช้
        username_text = self.medium_font.render(self.login_input, True, WHITE)
        self.screen.blit(username_text, (SCREEN_WIDTH // 2 - 145, 300))

        # เคอร์เซอร์
        if (
            self.input_focus == "username"
            and int(pygame.time.get_ticks() / 500) % 2 == 0
        ):
            cursor_x = SCREEN_WIDTH // 2 - 145 + username_text.get_width()
            pygame.draw.line(self.screen, WHITE, (cursor_x, 300), (cursor_x, 325), 2)

        # วาดช่องรหัสผ่าน
        password_label = self.medium_font.render("รหัสผ่าน:", True, WHITE)
        self.screen.blit(password_label, (SCREEN_WIDTH // 2 - 200, 350))

        # กรอบช่องรหัสผ่าน
        password_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 350, 300, 30)
        pygame.draw.rect(self.screen, (30, 30, 50), password_rect)
        pygame.draw.rect(
            self.screen,
            (200, 200, 200) if self.input_focus == "password" else (100, 100, 100),
            password_rect,
            2,
        )

        # ข้อความรหัสผ่าน (แสดงเป็น *)
        password_display = "*" * len(self.password_input)
        password_text = self.medium_font.render(password_display, True, WHITE)
        self.screen.blit(password_text, (SCREEN_WIDTH // 2 - 145, 350))

        # เคอร์เซอร์
        if (
            self.input_focus == "password"
            and int(pygame.time.get_ticks() / 500) % 2 == 0
        ):
            cursor_x = SCREEN_WIDTH // 2 - 145 + password_text.get_width()
            pygame.draw.line(self.screen, WHITE, (cursor_x, 350), (cursor_x, 375), 2)

        # ข้อความล็อกอิน
        if self.login_message:
            login_msg = self.small_font.render(self.login_message, True, (255, 200, 0))
            login_msg_rect = login_msg.get_rect(center=(SCREEN_WIDTH // 2, 385))
            self.screen.blit(login_msg, login_msg_rect)

        # ปุ่มล็อกอิน
        login_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 400, 200, 50)
        pygame.draw.rect(self.screen, (0, 100, 200), login_rect)
        pygame.draw.rect(self.screen, WHITE, login_rect, 2)
        login_text = self.medium_font.render("ล็อกอิน", True, WHITE)
        login_text_rect = login_text.get_rect(center=login_rect.center)
        self.screen.blit(login_text, login_text_rect)

        # ปุ่มเล่นเลย
        play_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 470, 200, 50)
        pygame.draw.rect(self.screen, (0, 150, 0), play_rect)
        pygame.draw.rect(self.screen, WHITE, play_rect, 2)
        play_text = self.medium_font.render("เล่นเลย", True, WHITE)
        play_text_rect = play_text.get_rect(center=play_rect.center)
        self.screen.blit(play_text, play_text_rect)

        # ปุ่มกลับ
        back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 540, 200, 50)
        pygame.draw.rect(self.screen, (150, 0, 0), back_rect)
        pygame.draw.rect(self.screen, WHITE, back_rect, 2)
        back_text = self.medium_font.render("กลับ", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.screen.blit(back_text, back_text_rect)

    def _render_howto_menu(self):
        """วาดเมนูวิธีเล่น"""
        # วาดหัวข้อ
        title = self.large_font.render("วิธีเล่น", True, (0, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # วาดเนื้อหา
        help_texts = [
            "การควบคุม:",
            "- ปุ่มลูกศรซ้าย/ขวา: เคลื่อนย้ายบล็อก",
            "- ปุ่มลูกศรลง: ทำให้บล็อกตกเร็วขึ้น",
            "- ปุ่มลูกศรขึ้น: หมุนบล็อกตามเข็มนาฬิกา",
            "- Z: หมุนบล็อกทวนเข็มนาฬิกา",
            "- Space: ทำให้บล็อกตกทันที",
            "- C: เก็บบล็อก",
            "- ESC/P: หยุดเกมชั่วคราว",
            "",
            "กฎเกม:",
            "- ล้างบล็อกเพื่อทำคะแนน",
            "- ยิ่งล้างมากแถวพร้อมกัน ยิ่งได้คะแนนมาก",
            "- ทำ T-Spin เพื่อรับคะแนนโบนัส",
            "- เกมจะจบเมื่อบล็อกสูงถึงด้านบนของบอร์ด",
            "",
            "กดปุ่ม ESC หรือ Enter เพื่อกลับไปยังเมนูหลัก",
        ]

        y_pos = 180
        for text in help_texts:
            if text.startswith("-"):
                # รายการย่อย
                rendered_text = self.small_font.render(text, True, (200, 200, 200))
                self.screen.blit(rendered_text, (SCREEN_WIDTH // 2 - 200, y_pos))
            elif text.startswith("การควบคุม") or text.startswith("กฎเกม"):
                # หัวข้อย่อย
                rendered_text = self.medium_font.render(text, True, (255, 255, 0))
                self.screen.blit(rendered_text, (SCREEN_WIDTH // 2 - 250, y_pos))
            elif text == "":
                # บรรทัดว่าง
                pass
            else:
                # ข้อความปกติ
                rendered_text = self.medium_font.render(text, True, WHITE)
                self.screen.blit(rendered_text, (SCREEN_WIDTH // 2 - 250, y_pos))

            y_pos += 30

    def _render_settings_menu(self):
        """วาดเมนูตั้งค่า"""
        # วาดหัวข้อ
        title = self.large_font.render("ตั้งค่า", True, (0, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # รายการตั้งค่า
        settings_list = [
            "ธีม: " + self.config["graphics"]["theme"],
            "เอฟเฟกต์อนุภาค: "
            + ("เปิด" if self.config["graphics"]["particles"] else "ปิด"),
            "แอนิเมชัน: " + ("เปิด" if self.config["graphics"]["animations"] else "ปิด"),
            "เอฟเฟกต์เรืองแสง: "
            + ("เปิด" if self.config["graphics"]["bloom_effect"] else "ปิด"),
            "แสดงเงาบล็อก: "
            + ("เปิด" if self.config["tetromino"]["ghost_piece"] else "ปิด"),
            "ระดับเสียงเพลง: "
            + str(int(self.config["audio"]["music_volume"] * 100))
            + "%",
            "ระดับเสียงเอฟเฟกต์: "
            + str(int(self.config["audio"]["sfx_volume"] * 100))
            + "%",
            "",
            "กดปุ่ม ESC เพื่อกลับไปยังเมนูหลัก",
        ]

        y_pos = 180
        for text in settings_list:
            if text == "":
                # บรรทัดว่าง
                y_pos += 20
                continue

            rendered_text = self.medium_font.render(text, True, WHITE)
            self.screen.blit(rendered_text, (SCREEN_WIDTH // 2 - 200, y_pos))
            y_pos += 40

        # หมายเหตุ: ในตัวอย่างนี้ไม่ได้เพิ่มการทำงานจริงของการตั้งค่า
        note = self.small_font.render(
            "* การแก้ไขการตั้งค่าจะมีผลในการเริ่มเกมครั้งถัดไป", True, (200, 200, 100)
        )
        self.screen.blit(note, (SCREEN_WIDTH // 2 - 200, y_pos + 20))

    def _render_leaderboard_menu(self):
        """วาดเมนูตารางคะแนน"""
        # วาดหัวข้อ
        title = self.large_font.render("อันดับคะแนนสูงสุด", True, (0, 255, 255))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # วาดหัวตาราง
        header_y = 170
        pygame.draw.line(
            self.screen,
            WHITE,
            (SCREEN_WIDTH // 2 - 300, header_y),
            (SCREEN_WIDTH // 2 + 300, header_y),
            2,
        )

        # หัวข้อคอลัมน์
        rank_text = self.medium_font.render("อันดับ", True, (255, 255, 0))
        self.screen.blit(rank_text, (SCREEN_WIDTH // 2 - 280, header_y - 30))

        name_text = self.medium_font.render("ชื่อผู้เล่น", True, (255, 255, 0))
        self.screen.blit(name_text, (SCREEN_WIDTH // 2 - 180, header_y - 30))

        score_text = self.medium_font.render("คะแนน", True, (255, 255, 0))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 + 50, header_y - 30))

        level_text = self.medium_font.render("ระดับ", True, (255, 255, 0))
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 + 180, header_y - 30))

        # วาดข้อมูล
        if not self.leaderboard_data:
            no_data = self.medium_font.render("ไม่มีข้อมูลคะแนน", True, WHITE)
            no_data_rect = no_data.get_rect(center=(SCREEN_WIDTH // 2, 300))
            self.screen.blit(no_data, no_data_rect)
        else:
            y_pos = header_y + 20
            for i, score in enumerate(self.leaderboard_data):
                # สีพื้นหลังของแถว
                row_color = (30, 30, 50) if i % 2 == 0 else (40, 40, 60)
                pygame.draw.rect(
                    self.screen,
                    row_color,
                    (SCREEN_WIDTH // 2 - 300, y_pos - 5, 600, 40),
                )

                # อันดับ
                rank = self.medium_font.render(f"{i+1}", True, WHITE)
                self.screen.blit(rank, (SCREEN_WIDTH // 2 - 280, y_pos))

                # ชื่อผู้เล่น
                name = self.medium_font.render(score.username, True, WHITE)
                self.screen.blit(name, (SCREEN_WIDTH // 2 - 180, y_pos))

                # คะแนน
                score_value = self.medium_font.render(f"{score.score:,}", True, WHITE)
                self.screen.blit(score_value, (SCREEN_WIDTH // 2 + 50, y_pos))

                # ระดับ
                level = self.medium_font.render(f"{score.level}", True, WHITE)
                self.screen.blit(level, (SCREEN_WIDTH // 2 + 180, y_pos))

                y_pos += 40

        # ข้อความด้านล่าง
        hint = self.small_font.render(
            "กดปุ่ม ESC หรือ Enter เพื่อกลับไปยังเมนูหลัก", True, (200, 200, 200)
        )
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)
