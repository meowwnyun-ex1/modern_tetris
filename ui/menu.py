#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Menu UI
---------------------
Classes for main menu and submenus with modern design
"""

# Standard library imports
import os
import sys
import math
import time
import random
import logging
from pathlib import Path

try:
    import pygame
except ImportError:
    try:
        import pygame_ce as pygame

        print("Using pygame-ce instead of pygame")
    except ImportError:
        print("Please install pygame or pygame-ce")
        sys.exit(1)

from pygame.locals import (
    KEYDOWN,
    MOUSEBUTTONDOWN,
    QUIT,
    MOUSEMOTION,
    K_UP,
    K_DOWN,
    K_ESCAPE,
    K_RETURN,
    K_BACKSPACE,
    K_TAB,
)

try:
    from core.constants import (
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        BLACK,
        WHITE,
        DENSO_RED,
        DENSO_DARK_RED,
        DENSO_LIGHT_RED,
        UI_BG,
        UI_BUTTON,
        UI_BUTTON_HOVER,
        UI_TEXT,
        UI_SUBTEXT,
        UI_ACCENT,
        UI_HIGHLIGHT,
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
        BUTTON_PADDING,
        BUTTON_CORNER_RADIUS,
        MENU_SPACING,
        FONT_SIZE_TITLE,
        FONT_SIZE_LARGE,
        FONT_SIZE_MEDIUM,
        FONT_SIZE_SMALL,
        FONT_SIZE_TINY,
        UI_BORDER,
    )
    from core.game import Game
    from audio.sound_manager import SoundManager
    from utils.logger import get_logger
except ImportError as e:
    print(f"Error importing required modules: {e}")
    # Set some fallback values to prevent crashes
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    DENSO_RED = (220, 0, 50)
    DENSO_DARK_RED = (160, 0, 35)
    DENSO_LIGHT_RED = (255, 60, 90)
    UI_BG = (24, 24, 32)
    UI_BUTTON = (45, 45, 60)
    UI_BUTTON_HOVER = (55, 55, 70)
    UI_TEXT = (245, 245, 245)
    UI_SUBTEXT = (180, 180, 190)
    UI_ACCENT = (230, 230, 230)
    UI_HIGHLIGHT = DENSO_RED
    UI_BORDER = (60, 60, 70)
    BUTTON_WIDTH = 220
    BUTTON_HEIGHT = 50
    BUTTON_PADDING = 15
    BUTTON_CORNER_RADIUS = 5
    MENU_SPACING = 70
    FONT_SIZE_TITLE = 56
    FONT_SIZE_LARGE = 28
    FONT_SIZE_MEDIUM = 22
    FONT_SIZE_SMALL = 16
    FONT_SIZE_TINY = 12

# Try to import database functions
try:
    from db.queries import (
        get_top_scores,
        authenticate_user,
        register_user,
        get_user_settings,
    )

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("Database functionality not available, using fallback mode")

# Setup logger
logger = logging.getLogger("tetris.menu")


class Button:
    """Class for interactive buttons with modern design"""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        text,
        font,
        action=None,
        bg_color=UI_BUTTON,
        hover_color=UI_BUTTON_HOVER,
        text_color=UI_TEXT,
        border_color=None,
        corner_radius=BUTTON_CORNER_RADIUS,
        icon=None,
    ):
        """
        Create a new button

        Args:
            x, y: Position coordinates
            width, height: Button dimensions
            text: Button label text
            font: Text font
            action: Function to call when clicked
            bg_color, hover_color, text_color: Button colors
            border_color: Border color (None for no border)
            corner_radius: Rounded corner radius (0 for sharp corners)
            icon: Optional icon path to display on button
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color
        self.corner_radius = corner_radius
        self.hovered = False
        self.clicked = False
        self.icon = None
        self.icon_rect = None

        # Load icon if provided
        if icon and os.path.exists(icon):
            try:
                self.icon = pygame.image.load(icon)
                self.icon = pygame.transform.scale(
                    self.icon, (height - 10, height - 10)
                )
                self.icon_rect = self.icon.get_rect(midleft=(x + 10, y + height // 2))
            except Exception as e:
                logger.error(f"Couldn't load icon {icon}: {e}")

        # Pre-render text
        self.update_text(text)

        # Animation properties
        self.animation_state = 0  # 0-1 for hover animation
        self.animation_speed = 8.0  # Animation speed

    def update_text(self, text):
        """Update button text"""
        self.text = text
        self.text_surf = self.font.render(self.text, True, self.text_color)

        # Adjust text position based on icon presence
        if self.icon:
            text_x = self.rect.centerx + 15
        else:
            text_x = self.rect.centerx

        self.text_rect = self.text_surf.get_rect(center=(text_x, self.rect.centery))

    def update(self, events, dt=1 / 60):
        """
        Update button state based on events

        Args:
            events: List of pygame events
            dt: Delta time for animations

        Returns:
            bool: True if button was clicked
        """
        mouse_pos = pygame.mouse.get_pos()
        was_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)

        # Update hover animation
        if self.hovered:
            self.animation_state = min(
                1.0, self.animation_state + dt * self.animation_speed
            )
        else:
            self.animation_state = max(
                0.0, self.animation_state - dt * self.animation_speed
            )

        for event in events:
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered:
                    self.clicked = True
                    if self.action:
                        self.action()
                    return True

        return False

    def draw(self, surface):
        """
        Draw the button with modern effects

        Args:
            surface: Surface to draw on
        """
        # Calculate animated colors
        if self.animation_state > 0:
            # Interpolate between normal and hover colors
            r = int(
                self.bg_color[0]
                + (self.hover_color[0] - self.bg_color[0]) * self.animation_state
            )
            g = int(
                self.bg_color[1]
                + (self.hover_color[1] - self.bg_color[1]) * self.animation_state
            )
            b = int(
                self.bg_color[2]
                + (self.hover_color[2] - self.bg_color[2]) * self.animation_state
            )
            color = (r, g, b)

            # Also animate text position for "press" effect
            text_offset = int(2 * self.animation_state)
            text_pos = (self.text_rect.x, self.text_rect.y + text_offset)
        else:
            color = self.bg_color
            text_pos = (self.text_rect.x, self.text_rect.y)

        # Draw button background with rounded corners
        if self.corner_radius > 0:
            pygame.draw.rect(
                surface, color, self.rect, border_radius=self.corner_radius
            )
        else:
            pygame.draw.rect(surface, color, self.rect)

        # Draw border if specified
        if self.border_color:
            border_color = self.border_color
            if self.hovered:
                # Brighter border on hover
                border_color = (
                    min(255, border_color[0] + 50),
                    min(255, border_color[1] + 50),
                    min(255, border_color[2] + 50),
                )

            pygame.draw.rect(
                surface,
                border_color,
                self.rect,
                width=2,
                border_radius=self.corner_radius,
            )

        # Draw icon if available
        if self.icon:
            surface.blit(self.icon, self.icon_rect)

        # Draw text
        surface.blit(self.text_surf, text_pos)

        # Draw subtle glow effect when hovered
        if self.animation_state > 0:
            glow_surf = pygame.Surface(
                (self.rect.width, self.rect.height), pygame.SRCALPHA
            )
            glow_color = (*DENSO_RED, int(50 * self.animation_state))
            pygame.draw.rect(
                glow_surf,
                glow_color,
                (0, 0, self.rect.width, self.rect.height),
                border_radius=self.corner_radius,
            )
            surface.blit(glow_surf, self.rect, special_flags=pygame.BLEND_RGB_ADD)


class InputField:
    """Class for modern text input fields"""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        placeholder="",
        font=None,
        max_length=20,
        bg_color=(30, 30, 40),
        text_color=WHITE,
        border_color=(60, 60, 70),
        active_border_color=DENSO_RED,
        corner_radius=BUTTON_CORNER_RADIUS,
        icon=None,
        input_type="text",
    ):
        """
        Create a new input field

        Args:
            x, y: Position coordinates
            width, height: Field dimensions
            placeholder: Placeholder text
            font: Text font
            max_length: Maximum text length
            bg_color, text_color: Field colors
            border_color, active_border_color: Border colors
            corner_radius: Rounded corner radius
            icon: Optional icon path to display on field
            input_type: "text", "password", or "email"
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.font = font
        self.max_length = max_length
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color
        self.active_border_color = active_border_color
        self.corner_radius = corner_radius
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.last_key_time = 0
        self.key_repeat_delay = 500  # ms before key starts repeating
        self.key_repeat_interval = 50  # ms between repeats
        self.input_type = input_type
        self.error_message = ""
        self.valid = True
        self.icon = None
        self.icon_rect = None
        self.helper_text = ""

        # Load icon if provided
        if icon and os.path.exists(icon):
            try:
                self.icon = pygame.image.load(icon)
                self.icon = pygame.transform.scale(
                    self.icon, (height - 10, height - 10)
                )
                self.icon_rect = self.icon.get_rect(midleft=(x + 10, y + height // 2))
            except Exception as e:
                logger.error(f"Couldn't load icon {icon}: {e}")

        # Animation properties
        self.animation_state = 0  # 0-1 for hover/active animation
        self.animation_speed = 8.0  # Animation speed
        self.shake_offset = 0
        self.shake_time = 0
        self.shake_duration = 0.3  # seconds

        # Input field properties
        self.padding = 10
        self.icon_padding = 35 if self.icon else 0

    def handle_event(self, event):
        """
        Handle input events

        Args:
            event: Pygame event

        Returns:
            bool: True if the field was interacted with
        """
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            # Toggle active state based on click
            self.active = self.rect.collidepoint(event.pos)
            return self.active

        if not self.active:
            return False

        if event.type == KEYDOWN:
            current_time = pygame.time.get_ticks()

            # Handle different key inputs
            if event.key == K_BACKSPACE:
                self.text = self.text[:-1]
                self.last_key_time = current_time
                self._validate()
                return True

            elif event.key == K_RETURN:
                self.active = False
                return True

            elif event.key == K_TAB:
                self.active = False
                return True

            elif event.unicode and len(self.text) < self.max_length:
                # Only accept printable characters
                if ord(event.unicode) >= 32:
                    self.text += event.unicode
                    self.last_key_time = current_time
                    self._validate()
                    return True

        return False

    def _validate(self):
        """Validate input based on input type"""
        self.valid = True
        self.error_message = ""

        if not self.text:  # Empty fields are considered valid until submission
            return True

        if self.input_type == "email":
            if "@" not in self.text or "." not in self.text or len(self.text) < 5:
                self.valid = False
                self.error_message = "Invalid email format"

        elif self.input_type == "password":
            if len(self.text) < 6:
                self.valid = False
                self.error_message = "Password too short (min 6 chars)"

        return self.valid

    def update(self, dt):
        """
        Update input field state

        Args:
            dt: Time delta in seconds
        """
        # Blink cursor
        self.cursor_timer += dt * 1000  # Convert to ms
        if self.cursor_timer >= 500:  # Blink every 500ms
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        # Handle key repeats for backspace
        if pygame.key.get_pressed()[K_BACKSPACE] and self.active:
            current_time = pygame.time.get_ticks()
            if (
                current_time - self.last_key_time > self.key_repeat_delay
                and current_time % self.key_repeat_interval < 20
            ):
                self.text = self.text[:-1]
                self._validate()

        # Update hover/active animation
        if self.active:
            self.animation_state = min(
                1.0, self.animation_state + dt * self.animation_speed
            )
        else:
            self.animation_state = max(
                0.0, self.animation_state - dt * self.animation_speed
            )

        # Update shake animation if active
        if self.shake_time > 0:
            self.shake_time -= dt
            self.shake_offset = math.sin(self.shake_time * 30) * (
                8 * self.shake_time / self.shake_duration
            )
            if self.shake_time <= 0:
                self.shake_offset = 0

    def set_error(self, message):
        """Set error state with message and shake animation"""
        self.error_message = message
        self.valid = False
        self.shake_time = self.shake_duration

    def clear_error(self):
        """Clear error state"""
        self.error_message = ""
        self.valid = True

    def draw(self, surface):
        """
        Draw the input field with modern design

        Args:
            surface: Surface to draw on
        """
        # Apply shake effect if active
        x_offset = self.shake_offset if self.shake_time > 0 else 0
        rect = self.rect.copy()
        rect.x += x_offset

        # Draw field background
        border_color = self.border_color

        # Determine border color based on state
        if not self.valid and self.error_message:
            # Error state
            border_color = (200, 50, 50)  # Error red
        elif self.active:
            # Active state
            r = int(
                self.border_color[0]
                + (self.active_border_color[0] - self.border_color[0])
                * self.animation_state
            )
            g = int(
                self.border_color[1]
                + (self.active_border_color[1] - self.border_color[1])
                * self.animation_state
            )
            b = int(
                self.border_color[2]
                + (self.active_border_color[2] - self.border_color[2])
                * self.animation_state
            )
            border_color = (r, g, b)

        # Draw with rounded corners
        pygame.draw.rect(surface, self.bg_color, rect, border_radius=self.corner_radius)

        # Draw border
        pygame.draw.rect(
            surface, border_color, rect, width=2, border_radius=self.corner_radius
        )

        # Draw icon if available
        if self.icon:
            icon_rect = self.icon_rect.copy()
            icon_rect.x += x_offset
            surface.blit(self.icon, icon_rect)

        # Prepare text to display
        display_text = self.text
        if self.input_type == "password":
            display_text = "•" * len(self.text)

        # Render text or placeholder
        if display_text:
            text_surf = self.font.render(display_text, True, self.text_color)
        else:
            text_surf = self.font.render(self.placeholder, True, (100, 100, 110))

        # Calculate text position (left-aligned with padding)
        text_x = rect.x + self.padding + self.icon_padding
        text_y = rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (text_x, text_y))

        # Draw cursor when field is active
        if self.active and self.cursor_visible:
            cursor_x = text_x + text_surf.get_width()
            cursor_color = (
                self.active_border_color
                if self.animation_state > 0.5
                else self.text_color
            )
            pygame.draw.line(
                surface,
                cursor_color,
                (cursor_x, text_y + 2),
                (cursor_x, text_y + text_surf.get_height() - 2),
                2,
            )

        # Draw helper text or error message below the input field
        if self.error_message and not self.valid:
            error_text = self.font.render(self.error_message, True, (200, 50, 50))
            error_rect = error_text.get_rect(x=rect.x, y=rect.bottom + 5)
            surface.blit(error_text, error_rect)
        elif self.helper_text:
            helper_text = self.font.render(self.helper_text, True, (150, 150, 150))
            helper_rect = helper_text.get_rect(x=rect.x, y=rect.bottom + 5)
            surface.blit(helper_text, helper_rect)


class MainMenu:
    """Class for main menu and submenus with modern design"""

    def __init__(self, screen, config):
        """
        Create a new main menu

        Args:
            screen (pygame.Surface): Main surface for display
            config (dict): Game config
        """
        self.screen = screen
        self.config = config
        self.logger = get_logger("tetris.menu")

        # Create sound system
        try:
            self.sound_manager = SoundManager(config)
            # Start menu music
            self.sound_manager.play_music("menu")
        except Exception as e:
            self.logger.error(f"Error initializing sound: {e}")
            # Create dummy sound manager to prevent crashes
            self.sound_manager = type(
                "DummySoundManager",
                (),
                {
                    "play_sound": lambda *args, **kwargs: None,
                    "play_music": lambda *args, **kwargs: None,
                    "stop_music": lambda *args, **kwargs: None,
                },
            )()

        # Create background surface
        self.background = self._create_background()

        # Try to load assets
        self.assets = {}
        self._load_assets()

        # Load fonts
        pygame.font.init()
        try:
            self.title_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', FONT_SIZE_TITLE
            )
            self.large_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', FONT_SIZE_LARGE
            )
            self.medium_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', FONT_SIZE_MEDIUM
            )
            self.small_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', FONT_SIZE_SMALL
            )
            self.tiny_font = pygame.font.Font(
                f'assets/fonts/{config["ui"]["font"]}.ttf', FONT_SIZE_TINY
            )
        except:
            # Use system fonts if loading fails
            self.title_font = pygame.font.SysFont("Arial", FONT_SIZE_TITLE)
            self.large_font = pygame.font.SysFont("Arial", FONT_SIZE_LARGE)
            self.medium_font = pygame.font.SysFont("Arial", FONT_SIZE_MEDIUM)
            self.small_font = pygame.font.SysFont("Arial", FONT_SIZE_SMALL)
            self.tiny_font = pygame.font.SysFont("Arial", FONT_SIZE_TINY)

        # Menu items
        self.menu_items = [
            "Play Game",
            "How to Play",
            "Settings",
            "Leaderboard",
            "Exit",
        ]
        self.selected_item = 0
        self.username = "Guest"  # Default player name

        # Animation effects
        self.animation_timer = 0
        self.animation_speed = 0.5  # cycles per second
        self.transition_state = 0  # For menu transitions
        self.transition_target = ""  # Target menu for transition
        self.transition_speed = 4.0  # Transition speed multiplier
        self.transition_direction = 1  # 1 for in, -1 for out
        self.transition_callback = None  # Callback after transition

        # States
        self.current_menu = "main"  # main, play, howto, settings, leaderboard, register
        self.login_message = ""
        self.register_message = ""
        self.notification = {
            "text": "",
            "color": (255, 255, 255),
            "timer": 0,
            "duration": 3.0,  # seconds
        }

        # Create buttons for main menu
        self.main_menu_buttons = []
        self._create_main_menu_buttons()

        # Create input fields for login/register screens
        self.username_input = InputField(
            SCREEN_WIDTH // 2 - 150,
            280,
            300,
            40,
            placeholder="Username",
            font=self.medium_font,
            icon="assets/images/icon_user.png",
        )

        self.password_input = InputField(
            SCREEN_WIDTH // 2 - 150,
            340,
            300,
            40,
            placeholder="Password",
            font=self.medium_font,
            input_type="password",
            icon="assets/images/icon_lock.png",
        )

        self.email_input = InputField(
            SCREEN_WIDTH // 2 - 150,
            400,
            300,
            40,
            placeholder="Email",
            font=self.medium_font,
            input_type="email",
            icon="assets/images/icon_email.png",
        )

        # Set helper text
        self.password_input.helper_text = "At least 6 characters"

        # Input focus
        self.active_input = None

        # Login/register buttons
        self.login_button = Button(
            SCREEN_WIDTH // 2 - 150,
            460,
            140,
            50,
            "Login",
            self.medium_font,
            action=self._handle_login,
            bg_color=UI_BUTTON,
            hover_color=DENSO_RED,
            border_color=UI_BORDER,
        )

        self.register_button = Button(
            SCREEN_WIDTH // 2 + 10,
            460,
            140,
            50,
            "Register",
            self.medium_font,
            action=self._switch_to_register,
            bg_color=UI_BUTTON,
            hover_color=UI_BUTTON_HOVER,
            border_color=UI_BORDER,
        )

        self.play_as_guest_button = Button(
            SCREEN_WIDTH // 2 - 150,
            530,
            300,
            50,
            "Play as Guest",
            self.medium_font,
            action=lambda: self._set_transition("main", self._play_as_guest),
            bg_color=(0, 120, 0),
            hover_color=(0, 150, 0),
            border_color=UI_BORDER,
        )

        self.back_button = Button(
            SCREEN_WIDTH // 2 - 150,
            600,
            300,
            50,
            "Back",
            self.medium_font,
            action=self._back_to_main,
            bg_color=(100, 20, 20),
            hover_color=(150, 30, 30),
            border_color=UI_BORDER,
        )

        self.create_account_button = Button(
            SCREEN_WIDTH // 2 - 150,
            530,
            300,
            50,
            "Create Account",
            self.medium_font,
            action=self._handle_register,
            bg_color=(0, 120, 120),
            hover_color=(0, 150, 150),
            border_color=UI_BORDER,
        )

        # Load high score player data
        self.leaderboard_data = []
        self._load_leaderboard()

        # Collect all input events
        self.current_events = []

        # Tetromino animation for background
        self.bg_tetrominos = []
        self._init_bg_tetrominos()

    def _load_assets(self):
        """Load additional assets for menu"""
        # Try to load icons
        icon_paths = {
            "user": "assets/images/icon_user.png",
            "lock": "assets/images/icon_lock.png",
            "email": "assets/images/icon_email.png",
            "logo": "assets/images/denso_logo.png",
        }

        for name, path in icon_paths.items():
            try:
                if os.path.exists(path):
                    self.assets[name] = pygame.image.load(path)
                else:
                    # Create directory if needed
                    os.makedirs(os.path.dirname(path), exist_ok=True)

                    # Create dummy icons if files don't exist
                    if name == "user":
                        icon = self._create_user_icon()
                    elif name == "lock":
                        icon = self._create_lock_icon()
                    elif name == "email":
                        icon = self._create_email_icon()
                    elif name == "logo":
                        icon = self._create_logo_icon()
                    else:
                        icon = pygame.Surface((32, 32))

                    pygame.image.save(icon, path)
                    self.assets[name] = icon
            except Exception as e:
                self.logger.error(f"Could not load asset {name}: {e}")
                # Create a backup surface
                self.assets[name] = pygame.Surface((32, 32))
                self.assets[name].fill(DENSO_RED)

    def _create_user_icon(self):
        """Create a simple user icon"""
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        # Draw circle for head
        pygame.draw.circle(icon, WHITE, (16, 10), 8)
        # Draw body
        pygame.draw.ellipse(icon, WHITE, (8, 18, 16, 14))
        return icon

    def _create_lock_icon(self):
        """Create a simple lock icon"""
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        # Draw lock body
        pygame.draw.rect(icon, WHITE, (8, 14, 16, 14), border_radius=2)
        # Draw lock top
        pygame.draw.rect(icon, WHITE, (10, 6, 12, 10))
        # Draw keyhole
        pygame.draw.circle(icon, (30, 30, 40), (16, 20), 3)
        return icon

    def _create_email_icon(self):
        """Create a simple email icon"""
        icon = pygame.Surface((32, 32), pygame.SRCALPHA)
        # Draw envelope
        pygame.draw.rect(icon, WHITE, (4, 8, 24, 16), border_radius=2)
        # Draw diagonal lines for envelope flap
        pygame.draw.line(icon, WHITE, (4, 8), (16, 16), 2)
        pygame.draw.line(icon, WHITE, (28, 8), (16, 16), 2)
        return icon

    def _create_logo_icon(self):
        """Create a simple DENSO logo icon"""
        icon = pygame.Surface((120, 40), pygame.SRCALPHA)
        # Draw "DENSO" text
        font = pygame.font.SysFont("Arial", 28, bold=True)
        text = font.render("DENSO", True, DENSO_RED)
        icon.blit(text, (10, 5))
        return icon

    def _init_bg_tetrominos(self):
        """Initialize background tetromino animations"""
        # Create random tetrominos in the background
        tetromino_shapes = [
            [(0, 0), (0, 1), (0, 2), (0, 3)],  # I
            [(0, 0), (0, 1), (0, 2), (1, 2)],  # J
            [(0, 0), (0, 1), (0, 2), (1, 0)],  # L
            [(0, 0), (0, 1), (1, 0), (1, 1)],  # O
            [(1, 0), (2, 0), (0, 1), (1, 1)],  # S
            [(1, 0), (0, 1), (1, 1), (2, 1)],  # T
            [(0, 0), (1, 0), (1, 1), (2, 1)],  # Z
        ]

        tetromino_colors = [
            (0, 190, 218),  # Cyan (I)
            (0, 80, 200),  # Blue (J)
            (235, 138, 5),  # Orange (L)
            (235, 210, 0),  # Yellow (O)
            (0, 190, 80),  # Green (S)
            DENSO_RED,  # Red (T)
            (235, 50, 50),  # Red (Z)
        ]

        # Create 10 random tetrominos
        for _ in range(10):
            shape_idx = random.randint(0, len(tetromino_shapes) - 1)

            tetromino = {
                "shape": tetromino_shapes[shape_idx],
                "color": tetromino_colors[shape_idx],
                "x": random.randint(-100, SCREEN_WIDTH - 50),
                "y": random.randint(-200, -50),
                "rotation": random.randint(0, 3),
                "speed": random.uniform(15, 30),
                "rotation_speed": random.uniform(-0.5, 0.5),
                "scale": random.uniform(0.5, 1.5),
                "alpha": random.randint(30, 100),
            }

            self.bg_tetrominos.append(tetromino)

    def _create_main_menu_buttons(self):
        """Create buttons for main menu with improved look"""
        self.main_menu_buttons = []

        # Calculate button positions
        center_x = SCREEN_WIDTH // 2
        start_y = 300

        # Create buttons with modern style
        for i, item in enumerate(self.menu_items):
            # Different colors for different buttons
            if item == "Play Game":
                bg_color = (0, 120, 80)
                hover_color = (0, 180, 120)
            elif item == "Exit":
                bg_color = (120, 20, 20)
                hover_color = (180, 40, 40)
            else:
                bg_color = UI_BUTTON
                hover_color = UI_BUTTON_HOVER

            button = Button(
                center_x - BUTTON_WIDTH // 2,
                start_y + i * MENU_SPACING,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                item,
                self.medium_font,
                action=lambda idx=i: self._handle_menu_click(idx),
                bg_color=bg_color,
                hover_color=hover_color,
                border_color=UI_BORDER,
            )
            self.main_menu_buttons.append(button)

    def _handle_menu_click(self, index):
        """Handle main menu button click with transition animation"""
        self.selected_item = index
        try:
            self.sound_manager.play_sound("menu_select")
        except:
            pass

        if self.menu_items[index] == "Play Game":
            self._set_transition("play")
        elif self.menu_items[index] == "How to Play":
            self._set_transition("howto")
        elif self.menu_items[index] == "Settings":
            self._set_transition("settings")
        elif self.menu_items[index] == "Leaderboard":
            self._load_leaderboard()
            self._set_transition("leaderboard")
        elif self.menu_items[index] == "Exit":
            pygame.event.post(pygame.event.Event(QUIT))

    def _set_transition(self, target, callback=None):
        """Set up menu transition animation"""
        self.transition_state = 0
        self.transition_target = target
        self.transition_direction = 1  # transition in
        self.transition_callback = callback

    def _show_notification(self, text, color=(255, 255, 255), duration=3.0):
        """Show a notification message"""
        self.notification = {
            "text": text,
            "color": color,
            "timer": duration,
            "duration": duration,
        }

    def _play_as_guest(self):
        """Start game as guest"""
        self.username = "Guest"
        self._show_notification("Playing as Guest", (100, 255, 100))
        return Game(self.screen, self.config, self.username)

    def _back_to_main(self):
        """Go back to main menu with transition"""
        self._set_transition("main")
        try:
            self.sound_manager.play_sound("menu_change")
        except:
            pass

    def _switch_to_register(self):
        """Switch to registration screen with transition"""
        self._set_transition("register")
        try:
            self.sound_manager.play_sound("menu_change")
        except:
            pass

    def _create_background(self):
        """
        Create modern menu background with subtle DENSO branding

        Returns:
            pygame.Surface: Created background
        """
        # Create new surface
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Modern gradient background
        for y in range(SCREEN_HEIGHT):
            # Map y position to color intensity
            factor = 1 - (y / SCREEN_HEIGHT)
            color = (
                int(UI_BG[0] + factor * 15),  # Subtle gradient
                int(UI_BG[1] + factor * 10),
                int(max(5, UI_BG[2] - factor * 10)),
            )
            pygame.draw.line(bg, color, (0, y), (SCREEN_WIDTH, y))

        # Add subtle grid pattern
        grid_color = (30, 30, 40, 15)  # Very subtle grid
        grid_spacing = 30

        # Draw vertical grid lines
        for x in range(0, SCREEN_WIDTH, grid_spacing):
            pygame.draw.line(bg, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)

        # Draw horizontal grid lines
        for y in range(0, SCREEN_HEIGHT, grid_spacing):
            pygame.draw.line(bg, grid_color, (0, y), (SCREEN_WIDTH, y), 1)

        # Add a subtle DENSO branding element in the corner
        logo_surface = pygame.Surface((200, 100), pygame.SRCALPHA)
        font = pygame.font.SysFont("Arial", 14)
        text = font.render("DENSO", True, (*DENSO_RED, 40))  # Semi-transparent
        logo_surface.blit(text, (10, 10))

        # Add to bottom right corner
        bg.blit(logo_surface, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 100))

        return bg

    def _load_leaderboard(self):
        """Load leaderboard data with error handling"""
        try:
            if DB_AVAILABLE:
                self.leaderboard_data = get_top_scores(10)
                if not self.leaderboard_data:
                    self._show_notification(
                        "No scores found in leaderboard", (255, 200, 100)
                    )
            else:
                self.leaderboard_data = []
                self._show_notification(
                    "Database not available - leaderboard disabled", (255, 200, 100)
                )
        except Exception as e:
            self.logger.error(f"Could not load leaderboard: {e}")
            self._show_notification("Error loading leaderboard data", (255, 100, 100))
            self.leaderboard_data = []

    def handle_event(self, event):
        """
        Handle input events

        Args:
            event (pygame.event.Event): Event to handle

        Returns:
            bool: True if event was handled, False if not
        """
        # Store event for button updates
        self.current_events = [event]

        # Handle button hover sound (only once per button)
        if event.type == MOUSEMOTION:
            self._check_button_hover()

        # Skip event handling during transitions
        if self.transition_state > 0 and self.transition_direction > 0:
            # Only allow quit events during transitions
            if event.type == QUIT:
                return True
            return False

        # Handle menu-specific events
        if self.current_menu == "main":
            return self._handle_main_menu_event(event)
        elif self.current_menu == "play":
            return self._handle_play_menu_event(event)
        elif self.current_menu == "register":
            return self._handle_register_menu_event(event)
        elif self.current_menu == "howto":
            return self._handle_howto_menu_event(event)
        elif self.current_menu == "settings":
            return self._handle_settings_menu_event(event)
        elif self.current_menu == "leaderboard":
            return self._handle_leaderboard_menu_event(event)

        return False

    def _check_button_hover(self):
        """Check for button hover to play sound effects"""
        mouse_pos = pygame.mouse.get_pos()

        # Check which set of buttons to use
        buttons = []
        if self.current_menu == "main":
            buttons = self.main_menu_buttons
        elif self.current_menu == "play":
            buttons = [
                self.login_button,
                self.register_button,
                self.play_as_guest_button,
                self.back_button,
            ]
        elif self.current_menu == "register":
            buttons = [self.create_account_button, self.back_button]
        elif self.current_menu in ["howto", "settings", "leaderboard"]:
            buttons = [self.back_button]

        # Check each button
        for button in buttons:
            was_hovered = button.hovered
            is_hovered = button.rect.collidepoint(mouse_pos)

            # Play sound when first hovering over a button
            if not was_hovered and is_hovered:
                try:
                    self.sound_manager.play_sound("menu_change")
                except:
                    pass

    def _handle_main_menu_event(self, event):
        """Handle events in main menu"""
        # Check keyboard navigation
        if event.type == KEYDOWN:
            if event.key == K_UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
                try:
                    self.sound_manager.play_sound("menu_change")
                except:
                    pass
            elif event.key == K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
                try:
                    self.sound_manager.play_sound("menu_change")
                except:
                    pass
            elif event.key == K_RETURN:
                # Same as clicking the selected button
                return self._handle_menu_click(self.selected_item)

        # Check button clicks
        for i, button in enumerate(self.main_menu_buttons):
            if button.update(self.current_events):
                return True

        return False

    def _handle_play_menu_event(self, event):
        """Handle events in play/login menu"""
        # Handle input fields
        input_handled = False
        input_handled |= self.username_input.handle_event(event)
        input_handled |= self.password_input.handle_event(event)

        # Set active input field
        if input_handled:
            if self.username_input.active:
                self.active_input = "username"
            elif self.password_input.active:
                self.active_input = "password"

        # Handle button clicks
        if self.login_button.update(self.current_events):
            return self._handle_login()

        if self.register_button.update(self.current_events):
            self._switch_to_register()
            return True

        if self.play_as_guest_button.update(self.current_events):
            return self._play_as_guest()

        if self.back_button.update(self.current_events):
            self._back_to_main()
            return True

        # Keyboard navigation
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self._back_to_main()
                return True
            elif event.key == K_RETURN and not (
                self.username_input.active or self.password_input.active
            ):
                return self._handle_login()

        return False

    def _handle_register_menu_event(self, event):
        """Handle events in registration menu"""
        # Handle input fields
        input_handled = False
        input_handled |= self.username_input.handle_event(event)
        input_handled |= self.password_input.handle_event(event)
        input_handled |= self.email_input.handle_event(event)

        # Set active input field
        if input_handled:
            if self.username_input.active:
                self.active_input = "username"
            elif self.password_input.active:
                self.active_input = "password"
            elif self.email_input.active:
                self.active_input = "email"

        # Handle button clicks
        if self.create_account_button.update(self.current_events):
            return self._handle_register()

        if self.back_button.update(self.current_events):
            self._set_transition("play")  # Go back to login screen
            try:
                self.sound_manager.play_sound("menu_change")
            except:
                pass
            return True

        # Keyboard navigation
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self._set_transition("play")  # Go back to login screen
                try:
                    self.sound_manager.play_sound("menu_change")
                except:
                    pass
                return True
            elif event.key == K_RETURN and not (
                self.username_input.active
                or self.password_input.active
                or self.email_input.active
            ):
                return self._handle_register()

        return False

    def _handle_howto_menu_event(self, event):
        """Handle events in how to play menu"""
        # Check button clicks
        if self.back_button.update(self.current_events):
            self._back_to_main()
            return True

        # Keyboard navigation
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE or event.key == K_RETURN:
                self._back_to_main()
                return True

        return False

    def _handle_settings_menu_event(self, event):
        """Handle events in settings menu"""
        # Check button clicks
        if self.back_button.update(self.current_events):
            self._back_to_main()
            return True

        # Keyboard navigation
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self._back_to_main()
                return True

        return False

    def _handle_leaderboard_menu_event(self, event):
        """Handle events in leaderboard menu"""
        # Check button clicks
        if self.back_button.update(self.current_events):
            self._back_to_main()
            return True

        # Keyboard navigation
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE or event.key == K_RETURN:
                self._back_to_main()
                return True

        return False

    def _handle_login(self):
        """Handle login attempt with better error handling"""
        username = self.username_input.text
        password = self.password_input.text

        # Validate input
        if not username:
            self.username_input.set_error("Username is required")
            self._show_notification("Please enter a username", (255, 100, 100))
            return False

        if not password:
            self.password_input.set_error("Password is required")
            self._show_notification("Please enter your password", (255, 100, 100))
            return False

        try:
            if DB_AVAILABLE:
                # Authenticate
                if authenticate_user(username, password):
                    self.username = username
                    self._show_notification(
                        f"Login successful! Welcome {self.username}", (100, 255, 100)
                    )
                    try:
                        self.sound_manager.play_sound("menu_select")
                    except:
                        pass

                    # Load user settings
                    try:
                        settings = get_user_settings(self.username)
                    except:
                        settings = None

                    # Start game with transition
                    self._set_transition(
                        "main", lambda: Game(self.screen, self.config, self.username)
                    )
                    return False  # Return False until transition completes
                else:
                    self.password_input.set_error("Invalid credentials")
                    self._show_notification(
                        "Invalid username or password", (255, 100, 100)
                    )
                    return False
            else:
                # In development mode, accept any login
                self.username = username
                self._show_notification(
                    f"Login successful (dev mode)! Welcome {self.username}",
                    (100, 255, 100),
                )
                try:
                    self.sound_manager.play_sound("menu_select")
                except:
                    pass
                self._set_transition(
                    "main", lambda: Game(self.screen, self.config, self.username)
                )
                return False

        except Exception as e:
            self.logger.error(f"Error during login: {e}")
            self._show_notification("Authentication system error", (255, 100, 100))
            return False

    def _handle_register(self):
        """Handle registration attempt with validation"""
        username = self.username_input.text
        password = self.password_input.text
        email = self.email_input.text

        # Validate all inputs
        valid = True

        if not username:
            self.username_input.set_error("Username is required")
            valid = False

        if not password:
            self.password_input.set_error("Password is required")
            valid = False
        elif len(password) < 6:
            self.password_input.set_error("Password must be at least 6 characters")
            valid = False

        if email and "@" not in email:
            self.email_input.set_error("Invalid email format")
            valid = False

        if not valid:
            self._show_notification(
                "Please correct the errors in the form", (255, 100, 100)
            )
            return False

        try:
            if DB_AVAILABLE:
                # Register new user
                if register_user(username, password):
                    self.username = username
                    self._show_notification("Registration successful!", (100, 255, 100))
                    try:
                        self.sound_manager.play_sound("menu_select")
                    except:
                        pass

                    # Reset fields
                    self.username_input.text = username  # Keep username for login
                    self.password_input.text = ""
                    self.email_input.text = ""

                    # Switch back to login screen with transition
                    self._set_transition("play")
                    self.login_message = "Account created! You can now log in."
                    return True
                else:
                    self.username_input.set_error("Username already exists")
                    self._show_notification("Username already exists", (255, 100, 100))
                    return False
            else:
                # In development mode, accept any registration
                self.username = username
                self._show_notification(
                    "Registration successful (dev mode)!", (100, 255, 100)
                )
                try:
                    self.sound_manager.play_sound("menu_select")
                except:
                    pass
                self._set_transition("play")
                self.login_message = "Account created! You can now log in."
                return True

        except Exception as e:
            self.logger.error(f"Error during registration: {e}")
            self._show_notification("Registration system error", (255, 100, 100))
            return False

    def update(self, dt):
        """
        Update menu state

        Args:
            dt (float): Time passed since last update (seconds)

        Returns:
            object: Next scene (if changing scene) or None
        """
        # Update animation timer
        self.animation_timer += dt * self.animation_speed

        # Keep animation_timer between 0-1
        self.animation_timer %= 1.0

        # Update transition state
        if self.transition_state < 1.0 and self.transition_direction > 0:
            # Transitioning in
            self.transition_state += dt * self.transition_speed
            if self.transition_state >= 1.0:
                # Transition complete
                self.transition_state = 1.0
                self.current_menu = self.transition_target

        elif self.transition_state > 0 and self.transition_direction < 0:
            # Transitioning out
            self.transition_state -= dt * self.transition_speed
            if self.transition_state <= 0:
                # Transition complete
                self.transition_state = 0
                self.transition_direction = 1
                self.current_menu = self.transition_target

                # Execute callback if there is one
                if self.transition_callback:
                    result = self.transition_callback()
                    self.transition_callback = None
                    return result

        # Update input fields
        self.username_input.update(dt)
        self.password_input.update(dt)
        self.email_input.update(dt)

        # Update buttons with animation
        if self.current_menu == "main":
            for button in self.main_menu_buttons:
                button.update([], dt)
        elif self.current_menu == "play":
            self.login_button.update([], dt)
            self.register_button.update([], dt)
            self.play_as_guest_button.update([], dt)
            self.back_button.update([], dt)
        elif self.current_menu == "register":
            self.create_account_button.update([], dt)
            self.back_button.update([], dt)
        else:
            self.back_button.update([], dt)

        # Update background tetrominos
        for tetromino in self.bg_tetrominos:
            # Move downward
            tetromino["y"] += tetromino["speed"] * dt

            # Rotate if it has rotation speed
            tetromino["rotation"] += tetromino["rotation_speed"] * dt

            # Reset if it goes off screen
            if tetromino["y"] > SCREEN_HEIGHT + 100:
                tetromino["y"] = random.randint(-200, -50)
                tetromino["x"] = random.randint(-100, SCREEN_WIDTH - 50)
                tetromino["speed"] = random.uniform(15, 30)

        # Update notification timer
        if self.notification["timer"] > 0:
            self.notification["timer"] -= dt
            if self.notification["timer"] <= 0:
                self.notification["text"] = ""

        return None

    def render(self):
        """Draw menu with modern effects"""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        # Draw background tetrominos
        self._render_bg_tetrominos()

        # Apply transition effect if active
        if self.transition_state > 0:
            # Draw current menu with transition effect
            menu_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
            )

            if self.transition_direction > 0:
                # Coming in
                if self.current_menu == self.transition_target:
                    # Fade in
                    alpha = int(255 * self.transition_state)
                    offset_x = int((1.0 - self.transition_state) * SCREEN_WIDTH * 0.1)

                    # Draw the menu on a separate surface
                    self._render_current_menu(menu_surface)

                    # Apply fade and slide effect
                    menu_surface.set_alpha(alpha)
                    self.screen.blit(menu_surface, (offset_x, 0))
                else:
                    # Old menu fading out
                    alpha = int(255 * (1.0 - self.transition_state))
                    offset_x = int(self.transition_state * -SCREEN_WIDTH * 0.1)

                    # Draw the old menu
                    self._render_menu_by_name(self.current_menu, menu_surface)

                    # Apply fade and slide effect
                    menu_surface.set_alpha(alpha)
                    self.screen.blit(menu_surface, (offset_x, 0))
            else:
                # Just draw the current menu
                self._render_current_menu(self.screen)
        else:
            # Normal rendering without transition
            self._render_current_menu(self.screen)

        # Draw notification if active
        if self.notification["text"] and self.notification["timer"] > 0:
            self._render_notification()

    def _render_bg_tetrominos(self):
        """Render background tetromino animations"""
        for tetromino in self.bg_tetrominos:
            cell_size = 20 * tetromino["scale"]

            # Draw each block of the tetromino
            for block_x, block_y in tetromino["shape"]:
                # Apply rotation
                angle = tetromino["rotation"] * math.pi / 2
                rot_x = block_x * math.cos(angle) - block_y * math.sin(angle)
                rot_y = block_x * math.sin(angle) + block_y * math.cos(angle)

                x = tetromino["x"] + rot_x * cell_size
                y = tetromino["y"] + rot_y * cell_size

                color = tetromino["color"] + (tetromino["alpha"],)

                # Draw block
                rect = pygame.Rect(x, y, cell_size, cell_size)
                pygame.draw.rect(self.screen, color, rect, border_radius=2)
                pygame.draw.rect(
                    self.screen,
                    (*color[:3], tetromino["alpha"] // 2),
                    rect,
                    width=1,
                    border_radius=2,
                )

    def _render_notification(self):
        """Render notification message with fade effect"""
        if not self.notification["text"]:
            return

        # Calculate fade effect
        alpha = min(
            255, int(255 * self.notification["timer"] / self.notification["duration"])
        )
        if alpha <= 0:
            return

        # Create notification surface
        font = self.medium_font
        text = font.render(self.notification["text"], True, self.notification["color"])

        # Create background surface
        padding = 20
        width = text.get_width() + padding * 2
        height = text.get_height() + padding * 2

        notify_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        # Semi-transparent dark background
        bg_color = (20, 20, 30, min(200, alpha))
        pygame.draw.rect(
            notify_surface, bg_color, (0, 0, width, height), border_radius=10
        )

        # Add border
        border_color = (*self.notification["color"][:3], alpha)
        pygame.draw.rect(
            notify_surface,
            border_color,
            (0, 0, width, height),
            width=2,
            border_radius=10,
        )

        # Add text with adjusted alpha
        text_alpha = pygame.Surface(text.get_size(), pygame.SRCALPHA)
        text_alpha.fill((255, 255, 255, alpha))
        text.blit(text_alpha, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        notify_surface.blit(text, (padding, padding))

        # Position at bottom of screen
        x = (SCREEN_WIDTH - width) // 2
        y = SCREEN_HEIGHT - height - 20

        # Apply slight bobbing animation
        y_offset = math.sin(time.time() * 3) * 3

        self.screen.blit(notify_surface, (x, y + y_offset))

    def _render_current_menu(self, surface):
        """Render the current menu"""
        self._render_menu_by_name(self.current_menu, surface)

    def _render_menu_by_name(self, menu_name, surface):
        """Render a specific menu by name"""
        if menu_name == "main":
            self._render_main_menu(surface)
        elif menu_name == "play":
            self._render_play_menu(surface)
        elif menu_name == "register":
            self._render_register_menu(surface)
        elif menu_name == "howto":
            self._render_howto_menu(surface)
        elif menu_name == "settings":
            self._render_settings_menu(surface)
        elif menu_name == "leaderboard":
            self._render_leaderboard_menu(surface)

    def _render_main_menu(self, surface):
        """Draw main menu with modern effects"""
        # Draw game logo with animation
        logo_scale = 1.0 + 0.05 * math.sin(self.animation_timer * 2 * math.pi)

        # Draw DENSO TETRIS title with modern styling
        title_denso = self.title_font.render("DENSO", True, DENSO_RED)
        title_tetris = self.title_font.render(" TETRIS", True, WHITE)

        # Position both parts with slight animation
        denso_rect = title_denso.get_rect(
            right=SCREEN_WIDTH // 2 + title_tetris.get_width() // 2,
            centery=150 + math.sin(self.animation_timer * 2 * math.pi) * 5,
        )
        tetris_rect = title_tetris.get_rect(
            left=denso_rect.right,
            centery=150 + math.sin((self.animation_timer + 0.25) * 2 * math.pi) * 5,
        )

        # Draw title parts
        surface.blit(title_denso, denso_rect)
        surface.blit(title_tetris, tetris_rect)

        # Subtle glow effect for title
        glow_intensity = int(80 + 50 * math.sin(self.animation_timer * 2 * math.pi))
        glow_color = (DENSO_RED[0], DENSO_RED[1], DENSO_RED[2], glow_intensity)

        # Create a temporary surface for the glow effect
        glow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        glow_denso = self.title_font.render("DENSO", True, glow_color)
        glow_rect = glow_denso.get_rect(center=(denso_rect.centerx, denso_rect.centery))
        glow_surface.blit(glow_denso, glow_rect)

        # Apply blur effect (simplified)
        for i in range(3):
            offset = i + 1
            blur_rect = glow_rect.copy()
            blur_rect.x += offset
            glow_surface.blit(
                glow_denso, blur_rect, special_flags=pygame.BLEND_RGBA_ADD
            )
            blur_rect = glow_rect.copy()
            blur_rect.x -= offset
            glow_surface.blit(
                glow_denso, blur_rect, special_flags=pygame.BLEND_RGBA_ADD
            )
            blur_rect = glow_rect.copy()
            blur_rect.y += offset
            glow_surface.blit(
                glow_denso, blur_rect, special_flags=pygame.BLEND_RGBA_ADD
            )
            blur_rect = glow_rect.copy()
            blur_rect.y -= offset
            glow_surface.blit(
                glow_denso, blur_rect, special_flags=pygame.BLEND_RGBA_ADD
            )

        # Apply the glow
        surface.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # Draw buttons with selection highlight
        for i, button in enumerate(self.main_menu_buttons):
            # Change button appearance if selected by keyboard
            if i == self.selected_item:
                # Save original colors
                orig_bg = button.bg_color
                orig_hover = button.hover_color
                orig_border = button.border_color

                # Set selected appearance
                button.bg_color = DENSO_RED
                button.hover_color = DENSO_LIGHT_RED
                button.border_color = WHITE

                # Draw button
                button.draw(surface)

                # Restore original colors
                button.bg_color = orig_bg
                button.hover_color = orig_hover
                button.border_color = orig_border
            else:
                button.draw(surface)

        # Draw version and copyright info
        self._render_footer(surface)

    def _render_footer(self, surface):
        """Render the footer with version and copyright info"""
        # Draw version text
        version_text = self.tiny_font.render("Version 1.0", True, UI_SUBTEXT)
        version_rect = version_text.get_rect(
            bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 40)
        )
        surface.blit(version_text, version_rect)

        # Draw current player name
        user_text = self.small_font.render(f"Player: {self.username}", True, UI_SUBTEXT)
        user_rect = user_text.get_rect(bottomleft=(20, SCREEN_HEIGHT - 40))
        surface.blit(user_text, user_rect)

        # Draw copyright with subtle animation
        copyright_text = self.tiny_font.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, UI_SUBTEXT
        )
        copyright_rect = copyright_text.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
        )
        surface.blit(copyright_text, copyright_rect)

    def _render_play_menu(self, surface):
        """Draw play/login menu with modern UI"""
        # Draw title with subtle animation
        y_offset = math.sin(self.animation_timer * 2 * math.pi) * 3
        title = self.large_font.render("Login", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150 + y_offset))
        surface.blit(title, title_rect)

        # Draw animated separator line
        line_width = int(200 + math.sin(self.animation_timer * 2 * math.pi) * 20)
        pygame.draw.line(
            surface,
            DENSO_RED,
            (SCREEN_WIDTH // 2 - line_width // 2, 190),
            (SCREEN_WIDTH // 2 + line_width // 2, 190),
            2,
        )

        # Add glow to the line
        glow_surf = pygame.Surface((line_width + 20, 10), pygame.SRCALPHA)
        for i in range(5):
            glow_alpha = max(0, 100 - i * 20)
            pygame.draw.line(
                glow_surf,
                (*DENSO_RED, glow_alpha),
                (10, 5 + i),
                (line_width + 10, 5 + i),
                1,
            )
            pygame.draw.line(
                glow_surf,
                (*DENSO_RED, glow_alpha),
                (10, 5 - i),
                (line_width + 10, 5 - i),
                1,
            )
        surface.blit(glow_surf, (SCREEN_WIDTH // 2 - line_width // 2 - 10, 185))

        # Draw subtitle
        subtitle = self.medium_font.render(
            "Sign in to save your scores", True, UI_SUBTEXT
        )
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        surface.blit(subtitle, subtitle_rect)

        # Draw input field labels
        username_label = self.small_font.render("Username:", True, UI_TEXT)
        surface.blit(username_label, (SCREEN_WIDTH // 2 - 150, 260))

        password_label = self.small_font.render("Password:", True, UI_TEXT)
        surface.blit(password_label, (SCREEN_WIDTH // 2 - 150, 320))

        # Draw input fields
        self.username_input.draw(surface)
        self.password_input.draw(surface)

        # Draw login message
        if self.login_message:
            message_color = (
                (100, 255, 100)
                if "successful" in self.login_message
                else (255, 100, 100)
            )
            login_msg = self.small_font.render(self.login_message, True, message_color)
            login_msg_rect = login_msg.get_rect(center=(SCREEN_WIDTH // 2, 420))
            surface.blit(login_msg, login_msg_rect)

        # Draw buttons
        self.login_button.draw(surface)
        self.register_button.draw(surface)
        self.play_as_guest_button.draw(surface)
        self.back_button.draw(surface)

        # Draw footer
        self._render_footer(surface)

    def _render_register_menu(self, surface):
        """Draw registration menu with modern UI"""
        # Draw title with subtle animation
        y_offset = math.sin(self.animation_timer * 2 * math.pi) * 3
        title = self.large_font.render("Create Account", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150 + y_offset))
        surface.blit(title, title_rect)

        # Draw animated separator line
        line_width = int(200 + math.sin(self.animation_timer * 2 * math.pi) * 20)
        pygame.draw.line(
            surface,
            DENSO_RED,
            (SCREEN_WIDTH // 2 - line_width // 2, 190),
            (SCREEN_WIDTH // 2 + line_width // 2, 190),
            2,
        )

        # Add glow to the line (same as in play menu)
        glow_surf = pygame.Surface((line_width + 20, 10), pygame.SRCALPHA)
        for i in range(5):
            glow_alpha = max(0, 100 - i * 20)
            pygame.draw.line(
                glow_surf,
                (*DENSO_RED, glow_alpha),
                (10, 5 + i),
                (line_width + 10, 5 + i),
                1,
            )
            pygame.draw.line(
                glow_surf,
                (*DENSO_RED, glow_alpha),
                (10, 5 - i),
                (line_width + 10, 5 - i),
                1,
            )
        surface.blit(glow_surf, (SCREEN_WIDTH // 2 - line_width // 2 - 10, 185))

        # Draw subtitle
        subtitle = self.medium_font.render(
            "Register to track your scores", True, UI_SUBTEXT
        )
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        surface.blit(subtitle, subtitle_rect)

        # Draw input field labels
        username_label = self.small_font.render("Username:", True, UI_TEXT)
        surface.blit(username_label, (SCREEN_WIDTH // 2 - 150, 260))

        password_label = self.small_font.render("Password:", True, UI_TEXT)
        surface.blit(password_label, (SCREEN_WIDTH // 2 - 150, 320))

        email_label = self.small_font.render("Email (optional):", True, UI_TEXT)
        surface.blit(email_label, (SCREEN_WIDTH // 2 - 150, 380))

        # Draw input fields
        self.username_input.draw(surface)
        self.password_input.draw(surface)
        self.email_input.draw(surface)

        # Draw registration message
        if self.register_message:
            message_color = (
                (100, 255, 100)
                if "successful" in self.register_message
                else (255, 100, 100)
            )
            register_msg = self.small_font.render(
                self.register_message, True, message_color
            )
            register_msg_rect = register_msg.get_rect(center=(SCREEN_WIDTH // 2, 470))
            surface.blit(register_msg, register_msg_rect)

        # Draw buttons
        self.create_account_button.draw(surface)
        self.back_button.draw(surface)

        # Draw footer
        self._render_footer(surface)

    def _render_howto_menu(self, surface):
        """Draw how to play menu with modern UI"""
        # Draw title with subtle animation
        y_offset = math.sin(self.animation_timer * 2 * math.pi) * 3
        title = self.large_font.render("How to Play", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100 + y_offset))
        surface.blit(title, title_rect)

        # Draw content
        help_texts = [
            ("Controls:", UI_HIGHLIGHT),
            ("- Left/Right Arrow: Move block", UI_TEXT),
            ("- Down Arrow: Soft drop", UI_TEXT),
            ("- Up Arrow: Rotate clockwise", UI_TEXT),
            ("- Z: Rotate counter-clockwise", UI_TEXT),
            ("- Space: Hard drop", UI_TEXT),
            ("- C: Hold block", UI_TEXT),
            ("- ESC/P: Pause game", UI_TEXT),
            ("", UI_TEXT),  # Blank line
            ("Game Rules:", UI_HIGHLIGHT),
            ("- Clear lines to score points", UI_TEXT),
            ("- More lines = more points", UI_TEXT),
            ("- T-Spins give bonus points", UI_TEXT),
            ("- Game ends when blocks reach the top", UI_TEXT),
        ]

        # Create stylish card background
        card_width = 500
        card_height = 420
        card_x = (SCREEN_WIDTH - card_width) // 2
        card_y = 160

        # Draw card with modern style
        pygame.draw.rect(
            surface,
            (40, 40, 60),
            (card_x, card_y, card_width, card_height),
            border_radius=15,
        )
        pygame.draw.rect(
            surface,
            DENSO_RED,
            (card_x, card_y, card_width, card_height),
            width=2,
            border_radius=15,
        )

        y_pos = 180
        for text, color in help_texts:
            if text.startswith("-"):
                # Sub-item with animation for highlighted items
                if "T-Spin" in text:
                    # Special highlight for T-Spin
                    color = (DENSO_RED[0], DENSO_RED[1], DENSO_RED[2])

                rendered_text = self.small_font.render(text, True, color)
                surface.blit(rendered_text, (SCREEN_WIDTH // 2 - 200, y_pos))
                y_pos += 30

            elif text.startswith("Controls") or text.startswith("Game Rules"):
                # Sub-header with modern styling
                # Draw header background
                header_rect = pygame.Rect(card_x + 20, y_pos - 5, card_width - 40, 36)
                pygame.draw.rect(surface, (50, 50, 70), header_rect, border_radius=5)

                rendered_text = self.medium_font.render(text, True, color)
                surface.blit(rendered_text, (SCREEN_WIDTH // 2 - 220, y_pos))
                y_pos += 40

            elif text == "":
                # Empty line
                y_pos += 20

            else:
                # Normal text
                rendered_text = self.medium_font.render(text, True, color)
                surface.blit(rendered_text, (SCREEN_WIDTH // 2 - 220, y_pos))
                y_pos += 30

        # Draw back button
        self.back_button.rect.center = (SCREEN_WIDTH // 2, y_pos + 50)
        self.back_button.text_rect = self.medium_font.render(
            self.back_button.text, True, UI_TEXT
        ).get_rect(center=self.back_button.rect.center)
        self.back_button.draw(surface)

        # Draw footer
        self._render_footer(surface)

    def _render_settings_menu(self, surface):
        """Draw settings menu with modern UI"""
        # Draw title with subtle animation
        y_offset = math.sin(self.animation_timer * 2 * math.pi) * 3
        title = self.large_font.render("Settings", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100 + y_offset))
        surface.blit(title, title_rect)

        # Create stylish card background
        card_width = 500
        card_height = 420
        card_x = (SCREEN_WIDTH - card_width) // 2
        card_y = 160

        # Draw card with modern style
        pygame.draw.rect(
            surface,
            (40, 40, 60),
            (card_x, card_y, card_width, card_height),
            border_radius=15,
        )
        pygame.draw.rect(
            surface,
            DENSO_RED,
            (card_x, card_y, card_width, card_height),
            width=2,
            border_radius=15,
        )

        # Settings list
        settings_list = [
            ("Theme:", self.config["graphics"]["theme"]),
            (
                "Particle Effects:",
                "On" if self.config["graphics"]["particles"] else "Off",
            ),
            ("Animations:", "On" if self.config["graphics"]["animations"] else "Off"),
            (
                "Bloom Effect:",
                "On" if self.config["graphics"]["bloom_effect"] else "Off",
            ),
            (
                "Ghost Piece:",
                "On" if self.config["tetromino"]["ghost_piece"] else "Off",
            ),
            ("Music Volume:", f"{int(self.config['audio']['music_volume'] * 100)}%"),
            ("Sound Effects:", f"{int(self.config['audio']['sfx_volume'] * 100)}%"),
        ]

        y_pos = 180
        for i, (label, value) in enumerate(settings_list):
            # Draw alternating row backgrounds
            row_rect = pygame.Rect(card_x + 20, y_pos - 5, card_width - 40, 40)
            row_color = (50, 50, 70) if i % 2 == 0 else (45, 45, 65)
            pygame.draw.rect(surface, row_color, row_rect, border_radius=5)

            # Draw setting label
            label_text = self.medium_font.render(label, True, UI_TEXT)
            surface.blit(label_text, (card_x + 30, y_pos))

            # Draw setting value with DENSO red for emphasis
            value_text = self.medium_font.render(value, True, UI_HIGHLIGHT)
            value_rect = value_text.get_rect(
                midright=(
                    card_x + card_width - 30,
                    y_pos + label_text.get_height() // 2,
                )
            )
            surface.blit(value_text, value_rect)

            y_pos += 50

        # Note about settings
        note = self.small_font.render(
            "* Changes will take effect in the next game", True, UI_SUBTEXT
        )
        note_rect = note.get_rect(center=(SCREEN_WIDTH // 2, y_pos + 20))
        surface.blit(note, note_rect)

        # Draw back button
        self.back_button.rect.center = (SCREEN_WIDTH // 2, y_pos + 60)
        self.back_button.text_rect = self.medium_font.render(
            self.back_button.text, True, UI_TEXT
        ).get_rect(center=self.back_button.rect.center)
        self.back_button.draw(surface)

        # Draw footer
        self._render_footer(surface)

    def _render_leaderboard_menu(self, surface):
        """Draw leaderboard menu with modern UI"""
        # Draw title with subtle animation
        y_offset = math.sin(self.animation_timer * 2 * math.pi) * 3
        title = self.large_font.render("High Scores", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100 + y_offset))
        surface.blit(title, title_rect)

        # Create stylish card background
        card_width = 600
        card_height = 420
        card_x = (SCREEN_WIDTH - card_width) // 2
        card_y = 160

        # Draw card with modern style
        pygame.draw.rect(
            surface,
            (40, 40, 60),
            (card_x, card_y, card_width, card_height),
            border_radius=15,
        )
        pygame.draw.rect(
            surface,
            DENSO_RED,
            (card_x, card_y, card_width, card_height),
            width=2,
            border_radius=15,
        )

        # Draw table header
        header_y = 170
        pygame.draw.rect(
            surface,
            (60, 60, 90),
            (card_x + 10, header_y, card_width - 20, 50),
            border_radius=8,
        )

        # Column headers
        rank_text = self.medium_font.render("Rank", True, UI_HIGHLIGHT)
        rank_rect = rank_text.get_rect(center=(card_x + 60, header_y + 25))
        surface.blit(rank_text, rank_rect)

        name_text = self.medium_font.render("Player", True, UI_HIGHLIGHT)
        name_rect = name_text.get_rect(center=(card_x + 200, header_y + 25))  # Fixed
        surface.blit(name_text, name_rect)

        score_text = self.medium_font.render("Score", True, UI_HIGHLIGHT)
        score_rect = score_text.get_rect(center=(card_x + 380, header_y + 25))
        surface.blit(score_text, score_rect)  # Fixed

        level_text = self.medium_font.render("Level", True, UI_HIGHLIGHT)
        level_rect = level_text.get_rect(center=(card_x + 520, header_y + 25))
        surface.blit(level_text, level_rect)

        # Draw data
        if not self.leaderboard_data:
            # Show message when no data
            no_data = self.medium_font.render("No score data available", True, UI_TEXT)
            no_data_rect = no_data.get_rect(
                center=(card_x + card_width // 2, card_y + card_height // 2)
            )
            surface.blit(no_data, no_data_rect)

            # Show hint
            hint = self.small_font.render(
                "Play a game to set your first score!", True, UI_SUBTEXT
            )
            hint_rect = hint.get_rect(
                center=(card_x + card_width // 2, card_y + card_height // 2 + 40)
            )
            surface.blit(hint, hint_rect)

        else:
            y_pos = header_y + 60
            for i, score in enumerate(self.leaderboard_data):
                # Row background color - alternate for readability
                row_color = (50, 50, 70) if i % 2 == 0 else (45, 45, 65)

                # Highlight user's score
                if score.username == self.username:
                    row_color = (70, 40, 50)  # DENSO red tint

                # Draw row background
                pygame.draw.rect(
                    surface,
                    row_color,
                    (card_x + 10, y_pos - 5, card_width - 20, 40),
                    border_radius=5,
                )

                # Rank (with medal icons for top 3)
                rank_color = UI_TEXT
                if i == 0:
                    rank_text = "🥇 1"
                    rank_color = (255, 215, 0)  # Gold
                elif i == 1:
                    rank_text = "🥈 2"
                    rank_color = (192, 192, 192)  # Silver
                elif i == 2:
                    rank_text = "🥉 3"
                    rank_color = (205, 127, 50)  # Bronze
                else:
                    rank_text = f"{i+1}"

                rank = self.medium_font.render(rank_text, True, rank_color)
                rank_rect = rank.get_rect(centerx=card_x + 60, centery=y_pos + 15)
                surface.blit(rank, rank_rect)

                # Player name
                name_color = DENSO_RED if score.username == self.username else UI_TEXT
                name = self.medium_font.render(score.username, True, name_color)
                name_rect = name.get_rect(centerx=card_x + 200, centery=y_pos + 15)
                surface.blit(name, name_rect)

                # Score
                score_value = self.medium_font.render(f"{score.score:,}", True, UI_TEXT)
                score_rect = score_value.get_rect(
                    centerx=card_x + 380, centery=y_pos + 15
                )
                surface.blit(score_value, score_rect)

                # Level
                level = self.medium_font.render(f"{score.level}", True, UI_TEXT)
                level_rect = level.get_rect(centerx=card_x + 520, centery=y_pos + 15)
                surface.blit(level, level_rect)

                y_pos += 40

        # Draw back button
        back_y = card_y + card_height + 30
        self.back_button.rect.center = (SCREEN_WIDTH // 2, back_y)
        self.back_button.text_rect = self.medium_font.render(
            self.back_button.text, True, UI_TEXT
        ).get_rect(center=self.back_button.rect.center)
        self.back_button.draw(surface)

        # Draw footer
        self._render_footer(surface)
