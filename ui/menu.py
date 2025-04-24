#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DENSO Tetris - Menu UI
---------------------
Classes for main menu and submenus
"""

import pygame
import logging
import math
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
from db.queries import (
    get_top_scores,
    authenticate_user,
    register_user,
    get_user_settings,
)
from utils.logger import get_logger


class Button:
    """Class for interactive buttons"""

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

        # Pre-render text
        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def update(self, events):
        """
        Update button state based on events

        Args:
            events: List of pygame events

        Returns:
            bool: True if button was clicked
        """
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)

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
        Draw the button

        Args:
            surface: Surface to draw on
        """
        # Draw button background
        color = self.hover_color if self.hovered else self.bg_color

        if self.corner_radius > 0:
            # Draw rounded rectangle
            pygame.draw.rect(
                surface, color, self.rect, border_radius=self.corner_radius
            )
        else:
            # Draw regular rectangle
            pygame.draw.rect(surface, color, self.rect)

        # Draw border if specified
        if self.border_color:
            pygame.draw.rect(
                surface,
                self.border_color,
                self.rect,
                width=2,
                border_radius=self.corner_radius,
            )

        # Draw text
        surface.blit(self.text_surf, self.text_rect)


class InputField:
    """Class for text input fields"""

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
        border_color=(128, 128, 128),  # Define GRAY as a medium gray color
        active_border_color=UI_HIGHLIGHT,
        corner_radius=BUTTON_CORNER_RADIUS,
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
        self.password_mode = False

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
                    return True

        return False

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

    def draw(self, surface):
        """
        Draw the input field

        Args:
            surface: Surface to draw on
        """
        # Draw field background
        pygame.draw.rect(
            surface, self.bg_color, self.rect, border_radius=self.corner_radius
        )

        # Draw border
        border_color = self.active_border_color if self.active else self.border_color
        pygame.draw.rect(
            surface, border_color, self.rect, width=2, border_radius=self.corner_radius
        )

        # Prepare text to display
        display_text = self.text
        if self.password_mode:
            display_text = "*" * len(self.text)

        # Render text or placeholder
        if display_text:
            text_surf = self.font.render(display_text, True, self.text_color)
        else:
            text_surf = self.font.render(self.placeholder, True, (100, 100, 110))

        # Calculate text position (left-aligned with padding)
        text_x = self.rect.x + 10
        text_y = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (text_x, text_y))

        # Draw cursor when field is active
        if self.active and self.cursor_visible:
            cursor_x = text_x + text_surf.get_width()
            pygame.draw.line(
                surface,
                self.text_color,
                (cursor_x, text_y + 2),
                (cursor_x, text_y + text_surf.get_height() - 2),
                2,
            )


class MainMenu:
    """Class for main menu and submenus"""

    def __init__(self, screen, config):
        """
        Create a new main menu

        Args:
            screen (pygame.Surface): Main surface for display
            config (dict): Game config
        """
        self.screen = screen
        self.config = config
        self.logger = get_logger()

        # Create sound system
        self.sound_manager = SoundManager(config)

        # Start menu music
        self.sound_manager.play_music("menu")

        # Create background surface
        self.background = self._create_background()

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

        # States
        self.current_menu = "main"  # main, play, howto, settings, leaderboard, register
        self.login_message = ""
        self.register_message = ""

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
        )

        self.password_input = InputField(
            SCREEN_WIDTH // 2 - 150,
            340,
            300,
            40,
            placeholder="Password",
            font=self.medium_font,
        )
        self.password_input.password_mode = True

        self.email_input = InputField(
            SCREEN_WIDTH // 2 - 150,
            400,
            300,
            40,
            placeholder="Email",
            font=self.medium_font,
        )

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
            action=self._play_as_guest,
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

    def _create_main_menu_buttons(self):
        """Create buttons for main menu"""
        self.main_menu_buttons = []

        # Calculate button positions
        center_x = SCREEN_WIDTH // 2
        start_y = 300

        for i, item in enumerate(self.menu_items):
            button = Button(
                center_x - BUTTON_WIDTH // 2,
                start_y + i * MENU_SPACING,
                BUTTON_WIDTH,
                BUTTON_HEIGHT,
                item,
                self.medium_font,
                action=lambda idx=i: self._handle_menu_click(idx),
                bg_color=UI_BUTTON,
                hover_color=UI_BUTTON_HOVER,
                border_color=UI_BORDER,
            )
            self.main_menu_buttons.append(button)

    def _handle_menu_click(self, index):
        """Handle main menu button click"""
        self.selected_item = index
        self.sound_manager.play_sound("menu_select")

        if self.menu_items[index] == "Play Game":
            self.current_menu = "play"
        elif self.menu_items[index] == "How to Play":
            self.current_menu = "howto"
        elif self.menu_items[index] == "Settings":
            self.current_menu = "settings"
        elif self.menu_items[index] == "Leaderboard":
            self._load_leaderboard()
            self.current_menu = "leaderboard"
        elif self.menu_items[index] == "Exit":
            pygame.event.post(pygame.event.Event(QUIT))

    def _play_as_guest(self):
        """Start game as guest"""
        self.username = "Guest"
        return Game(self.screen, self.config, self.username)

    def _back_to_main(self):
        """Go back to main menu"""
        self.current_menu = "main"
        self.sound_manager.play_sound("menu_change")

    def _switch_to_register(self):
        """Switch to registration screen"""
        self.current_menu = "register"
        self.sound_manager.play_sound("menu_change")

    def _create_background(self):
        """
        Create menu background

        Returns:
            pygame.Surface: Created background
        """
        # Create new surface
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Simple gradient background
        for y in range(SCREEN_HEIGHT):
            # Map y position to color intensity
            factor = y / SCREEN_HEIGHT
            color = (
                int(UI_BG[0] + factor * 10),  # Slight gradient
                int(UI_BG[1] + factor * 10),
                int(UI_BG[2] + factor * 8),
            )
            pygame.draw.line(bg, color, (0, y), (SCREEN_WIDTH, y))

        # Subtle grid pattern
        grid_color = (UI_BG[0] + 10, UI_BG[1] + 10, UI_BG[2] + 10, 30)
        grid_spacing = 40

        # Draw vertical grid lines
        for x in range(0, SCREEN_WIDTH, grid_spacing):
            pygame.draw.line(bg, grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)

        # Draw horizontal grid lines
        for y in range(0, SCREEN_HEIGHT, grid_spacing):
            pygame.draw.line(bg, grid_color, (0, y), (SCREEN_WIDTH, y), 1)

        return bg

    def _load_leaderboard(self):
        """Load leaderboard data"""
        try:
            self.leaderboard_data = get_top_scores(10)
        except Exception as e:
            self.logger.error(f"Could not load leaderboard: {e}")
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

        # Check each button
        for button in buttons:
            was_hovered = button.hovered
            is_hovered = button.rect.collidepoint(mouse_pos)

            # Play sound when first hovering over a button
            if not was_hovered and is_hovered:
                self.sound_manager.play_sound("menu_change")

            button.hovered = is_hovered

    def _handle_main_menu_event(self, event):
        """Handle events in main menu"""
        # Check keyboard navigation
        if event.type == KEYDOWN:
            if event.key == K_UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
                self.sound_manager.play_sound("menu_change")
            elif event.key == K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
                self.sound_manager.play_sound("menu_change")
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
            self.current_menu = "play"  # Go back to login screen
            self.sound_manager.play_sound("menu_change")
            return True

        # Keyboard navigation
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                self.current_menu = "play"  # Go back to login screen
                self.sound_manager.play_sound("menu_change")
                return True

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
        """Handle login attempt"""
        username = self.username_input.text
        password = self.password_input.text

        if not username or not password:
            self.login_message = "Please enter username and password"
            return False

        try:
            # Authenticate
            if authenticate_user(username, password):
                self.username = username
                self.login_message = f"Login successful! Welcome {self.username}"
                self.sound_manager.play_sound("menu_select")

                # Load user settings
                settings = get_user_settings(self.username)
                if settings:
                    # Use user settings
                    # (not implemented in this example)
                    pass

                # Start game
                return Game(self.screen, self.config, self.username)
            else:
                self.login_message = "Invalid username or password"
                return False
        except Exception as e:
            self.logger.error(f"Error during login: {e}")
            self.login_message = "Login error occurred"
            return False

    def _handle_register(self):
        """Handle registration attempt"""
        username = self.username_input.text
        password = self.password_input.text
        email = self.email_input.text

        if not username or not password:
            self.register_message = "Username and password are required"
            return False

        if len(password) < 6:
            self.register_message = "Password must be at least 6 characters"
            return False

        try:
            # Register new user
            if register_user(username, password):
                self.username = username
                self.register_message = "Registration successful!"
                self.sound_manager.play_sound("menu_select")

                # Switch back to login screen
                self.current_menu = "play"
                self.login_message = "Account created! You can now log in."
                return True
            else:
                self.register_message = "Username already exists"
                return False
        except Exception as e:
            self.logger.error(f"Error during registration: {e}")
            self.register_message = "Registration error occurred"
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

        # Update input fields
        self.username_input.update(dt)
        self.password_input.update(dt)
        self.email_input.update(dt)

        return None

    def render(self):
        """Draw menu"""
        # Draw background
        self.screen.blit(self.background, (0, 0))

        if self.current_menu == "main":
            self._render_main_menu()
        elif self.current_menu == "play":
            self._render_play_menu()
        elif self.current_menu == "register":
            self._render_register_menu()
        elif self.current_menu == "howto":
            self._render_howto_menu()
        elif self.current_menu == "settings":
            self._render_settings_menu()
        elif self.current_menu == "leaderboard":
            self._render_leaderboard_menu()

    def _render_main_menu(self):
        """Draw main menu"""
        # Draw game title with DENSO in highlight color
        # Split the title to highlight "DENSO"
        title_denso = self.title_font.render("DENSO", True, DENSO_RED)
        title_tetris = self.title_font.render(" TETRIS", True, WHITE)

        # Position both parts
        denso_rect = title_denso.get_rect(
            right=SCREEN_WIDTH // 2 + title_tetris.get_width() // 2, centery=150
        )
        tetris_rect = title_tetris.get_rect(left=denso_rect.right, centery=150)

        # Draw title parts
        self.screen.blit(title_denso, denso_rect)
        self.screen.blit(title_tetris, tetris_rect)

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
        self.screen.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

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
                button.draw(self.screen)

                # Restore original colors
                button.bg_color = orig_bg
                button.hover_color = orig_hover
                button.border_color = orig_border
            else:
                button.draw(self.screen)

        # Draw version text
        version_text = self.tiny_font.render("Version 1.0", True, UI_SUBTEXT)
        version_rect = version_text.get_rect(
            bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 40)
        )
        self.screen.blit(version_text, version_rect)

        # Draw current player name
        user_text = self.small_font.render(f"Player: {self.username}", True, UI_SUBTEXT)
        user_rect = user_text.get_rect(bottomleft=(20, SCREEN_HEIGHT - 40))
        self.screen.blit(user_text, user_rect)

        # Draw copyright
        copyright_text = self.tiny_font.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, UI_SUBTEXT
        )
        copyright_rect = copyright_text.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
        )
        self.screen.blit(copyright_text, copyright_rect)

    def _render_play_menu(self):
        """Draw play/login menu"""
        # Draw title
        title = self.large_font.render("Login", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # Draw subtle separator line
        pygame.draw.line(
            self.screen,
            UI_ACCENT,
            (SCREEN_WIDTH // 2 - 100, 190),
            (SCREEN_WIDTH // 2 + 100, 190),
            2,
        )

        # Draw subtitle
        subtitle = self.medium_font.render(
            "Sign in to save your scores", True, UI_SUBTEXT
        )
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)

        # Draw input field labels
        username_label = self.small_font.render("Username:", True, UI_TEXT)
        self.screen.blit(username_label, (SCREEN_WIDTH // 2 - 150, 260))

        password_label = self.small_font.render("Password:", True, UI_TEXT)
        self.screen.blit(password_label, (SCREEN_WIDTH // 2 - 150, 320))

        # Draw input fields
        self.username_input.draw(self.screen)
        self.password_input.draw(self.screen)

        # Draw login message
        if self.login_message:
            message_color = (
                (0, 200, 0) if "successful" in self.login_message else (255, 100, 100)
            )
            login_msg = self.small_font.render(self.login_message, True, message_color)
            login_msg_rect = login_msg.get_rect(center=(SCREEN_WIDTH // 2, 420))
            self.screen.blit(login_msg, login_msg_rect)

        # Draw buttons
        self.login_button.draw(self.screen)
        self.register_button.draw(self.screen)
        self.play_as_guest_button.draw(self.screen)
        self.back_button.draw(self.screen)

        # Draw copyright
        copyright_text = self.tiny_font.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, UI_SUBTEXT
        )
        copyright_rect = copyright_text.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
        )
        self.screen.blit(copyright_text, copyright_rect)

    def _render_register_menu(self):
        """Draw registration menu"""
        # Draw title
        title = self.large_font.render("Create Account", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # Draw subtle separator line
        pygame.draw.line(
            self.screen,
            UI_ACCENT,
            (SCREEN_WIDTH // 2 - 100, 190),
            (SCREEN_WIDTH // 2 + 100, 190),
            2,
        )

        # Draw subtitle
        subtitle = self.medium_font.render(
            "Register to track your scores", True, UI_SUBTEXT
        )
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)

        # Draw input field labels
        username_label = self.small_font.render("Username:", True, UI_TEXT)
        self.screen.blit(username_label, (SCREEN_WIDTH // 2 - 150, 260))

        password_label = self.small_font.render("Password:", True, UI_TEXT)
        self.screen.blit(password_label, (SCREEN_WIDTH // 2 - 150, 320))

        email_label = self.small_font.render("Email (optional):", True, UI_TEXT)
        self.screen.blit(email_label, (SCREEN_WIDTH // 2 - 150, 380))

        # Draw input fields
        self.username_input.draw(self.screen)
        self.password_input.draw(self.screen)
        self.email_input.draw(self.screen)

        # Draw registration message
        if self.register_message:
            message_color = (
                (0, 200, 0)
                if "successful" in self.register_message
                else (255, 100, 100)
            )
            register_msg = self.small_font.render(
                self.register_message, True, message_color
            )
            register_msg_rect = register_msg.get_rect(center=(SCREEN_WIDTH // 2, 470))
            self.screen.blit(register_msg, register_msg_rect)

        # Draw buttons
        self.create_account_button.draw(self.screen)
        self.back_button.draw(self.screen)

        # Draw copyright
        copyright_text = self.tiny_font.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, UI_SUBTEXT
        )
        copyright_rect = copyright_text.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
        )
        self.screen.blit(copyright_text, copyright_rect)

    def _render_howto_menu(self):
        """Draw how to play menu"""
        # Draw title
        title = self.large_font.render("How to Play", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

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
            ("- More lines cleared at once = more points", UI_TEXT),
            ("- T-Spins give bonus points", UI_TEXT),
            ("- Game ends when blocks reach the top", UI_TEXT),
        ]

        y_pos = 180
        for text, color in help_texts:
            if text.startswith("-"):
                # Sub-item
                rendered_text = self.small_font.render(text, True, color)
                self.screen.blit(rendered_text, (SCREEN_WIDTH // 2 - 200, y_pos))
                y_pos += 30
            elif text.startswith("Controls") or text.startswith("Game Rules"):
                # Sub-header
                rendered_text = self.medium_font.render(text, True, color)
                self.screen.blit(rendered_text, (SCREEN_WIDTH // 2 - 250, y_pos))
                y_pos += 40
            elif text == "":
                # Empty line
                y_pos += 20
            else:
                # Normal text
                rendered_text = self.medium_font.render(text, True, color)
                self.screen.blit(rendered_text, (SCREEN_WIDTH // 2 - 250, y_pos))
                y_pos += 30

        # Draw back button
        self.back_button.rect.center = (SCREEN_WIDTH // 2, y_pos + 50)
        self.back_button.text_rect = self.medium_font.render(
            self.back_button.text, True, UI_TEXT
        ).get_rect(center=self.back_button.rect.center)
        self.back_button.draw(self.screen)

        # Draw copyright
        copyright_text = self.tiny_font.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, UI_SUBTEXT
        )
        copyright_rect = copyright_text.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
        )
        self.screen.blit(copyright_text, copyright_rect)

    def _render_settings_menu(self):
        """Draw settings menu"""
        # Draw title
        title = self.large_font.render("Settings", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

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
        for label, value in settings_list:
            # Draw setting label
            label_text = self.medium_font.render(label, True, UI_TEXT)
            self.screen.blit(label_text, (SCREEN_WIDTH // 2 - 240, y_pos))

            # Draw setting value
            value_text = self.medium_font.render(value, True, UI_HIGHLIGHT)
            value_rect = value_text.get_rect(
                midright=(SCREEN_WIDTH // 2 + 240, y_pos + label_text.get_height() // 2)
            )
            self.screen.blit(value_text, value_rect)

            y_pos += 50

        # Note about settings
        note = self.small_font.render(
            "* Settings changes will take effect in the next game", True, UI_SUBTEXT
        )
        note_rect = note.get_rect(center=(SCREEN_WIDTH // 2, y_pos + 20))
        self.screen.blit(note, note_rect)

        # Draw back button
        self.back_button.rect.center = (SCREEN_WIDTH // 2, y_pos + 80)
        self.back_button.text_rect = self.medium_font.render(
            self.back_button.text, True, UI_TEXT
        ).get_rect(center=self.back_button.rect.center)
        self.back_button.draw(self.screen)

        # Draw copyright
        copyright_text = self.tiny_font.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, UI_SUBTEXT
        )
        copyright_rect = copyright_text.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
        )
        self.screen.blit(copyright_text, copyright_rect)

    def _render_leaderboard_menu(self):
        """Draw leaderboard menu"""
        # Draw title
        title = self.large_font.render("High Scores", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # Draw table header
        header_y = 170
        pygame.draw.rect(
            self.screen,
            UI_BUTTON,
            (SCREEN_WIDTH // 2 - 300, header_y - 10, 600, 50),
            border_radius=5,
        )

        pygame.draw.rect(
            self.screen,
            UI_BORDER,
            (SCREEN_WIDTH // 2 - 300, header_y - 10, 600, 50),
            width=2,
            border_radius=5,
        )

        # Column headers
        rank_text = self.medium_font.render("Rank", True, UI_HIGHLIGHT)
        rank_rect = rank_text.get_rect(center=(SCREEN_WIDTH // 2 - 250, header_y + 15))
        self.screen.blit(rank_text, rank_rect)

        name_text = self.medium_font.render("Player", True, UI_HIGHLIGHT)
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2 - 100, header_y + 15))
        self.screen.blit(name_text, name_rect)

        score_text = self.medium_font.render("Score", True, UI_HIGHLIGHT)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2 + 80, header_y + 15))
        self.screen.blit(score_text, score_rect)

        level_text = self.medium_font.render("Level", True, UI_HIGHLIGHT)
        level_rect = level_text.get_rect(
            center=(SCREEN_WIDTH // 2 + 220, header_y + 15)
        )
        self.screen.blit(level_text, level_rect)

        # Draw data
        if not self.leaderboard_data:
            no_data = self.medium_font.render("No score data available", True, UI_TEXT)
            no_data_rect = no_data.get_rect(center=(SCREEN_WIDTH // 2, 300))
            self.screen.blit(no_data, no_data_rect)
        else:
            y_pos = header_y + 60
            for i, score in enumerate(self.leaderboard_data):
                # Row background color - alternate for readability
                row_color = (
                    UI_BUTTON
                    if i % 2 == 0
                    else (UI_BUTTON[0] - 5, UI_BUTTON[1] - 5, UI_BUTTON[2] - 5)
                )

                # Highlight user's score
                if score.username == self.username:
                    row_color = (UI_BUTTON[0] + 10, UI_BUTTON[1] + 5, UI_BUTTON[2])

                # Draw row background
                pygame.draw.rect(
                    self.screen,
                    row_color,
                    (SCREEN_WIDTH // 2 - 300, y_pos - 5, 600, 40),
                    border_radius=3,
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
                rank_rect = rank.get_rect(
                    centerx=SCREEN_WIDTH // 2 - 250, centery=y_pos + 15
                )
                self.screen.blit(rank, rank_rect)

                # Player name
                name_color = DENSO_RED if score.username == self.username else UI_TEXT
                name = self.medium_font.render(score.username, True, name_color)
                name_rect = name.get_rect(
                    centerx=SCREEN_WIDTH // 2 - 100, centery=y_pos + 15
                )
                self.screen.blit(name, name_rect)

                # Score
                score_value = self.medium_font.render(f"{score.score:,}", True, UI_TEXT)
                score_rect = score_value.get_rect(
                    centerx=SCREEN_WIDTH // 2 + 80, centery=y_pos + 15
                )
                self.screen.blit(score_value, score_rect)

                # Level
                level = self.medium_font.render(f"{score.level}", True, UI_TEXT)
                level_rect = level.get_rect(
                    centerx=SCREEN_WIDTH // 2 + 220, centery=y_pos + 15
                )
                self.screen.blit(level, level_rect)

                y_pos += 50

        # Draw back button
        self.back_button.rect.center = (SCREEN_WIDTH // 2, y_pos + 40)
        self.back_button.text_rect = self.medium_font.render(
            self.back_button.text, True, UI_TEXT
        ).get_rect(center=self.back_button.rect.center)
        self.back_button.draw(self.screen)

        # Draw copyright
        copyright_text = self.tiny_font.render(
            "© 2025 Thammaphon Chittasuwanna (SDM)", True, UI_SUBTEXT
        )
        copyright_rect = copyright_text.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
        )
        self.screen.blit(copyright_text, copyright_rect)  #!/usr/bin/env python


# -*- coding: utf-8 -*-

"""
DENSO Tetris - Menu UI
---------------------
Classes for main menu and submenus
"""

import pygame
import logging
import math
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
from db.queries import (
    get_top_scores,
    authenticate_user,
    register_user,
    get_user_settings,
)
from utils.logger import get_logger


class Button:
    """Class for interactive buttons"""

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

        # Pre-render text
        self.text_surf = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def update(self, events):
        """
        Update button state based on events

        Args:
            events: List of pygame events

        Returns:
            bool: True if button was clicked
        """
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)

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
        Draw the button

        Args:
            surface: Surface to draw on
        """
        # Draw button background
        color = self.hover_color if self.hovered else self.bg_color

        if self.corner_radius > 0:
            # Draw rounded rectangle
            pygame.draw.rect(
                surface, color, self.rect, border_radius=self.corner_radius
            )
        else:
            # Draw regular rectangle
            pygame.draw.rect(surface, color, self.rect)

        # Draw border if specified
        if self.border_color:
            pygame.draw.rect(
                surface,
                self.border_color,
                self.rect,
                width=2,
                border_radius=self.corner_radius,
            )

        # Draw text
        surface.blit(self.text_surf, self.text_rect)


class InputField:
    """Class for text input fields"""

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
        text_color=(255, 255, 255),
        border_color=(128, 128, 128),
        active_border_color=UI_HIGHLIGHT,
        corner_radius=BUTTON_CORNER_RADIUS,
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
        self.password_mode = False

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
                    return True

        return False

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

    def draw(self, surface):
        """
        Draw the input field

        Args:
            surface: Surface to draw on
        """
        # Draw field background
        pygame.draw.rect(
            surface, self.bg_color, self.rect, border_radius=self.corner_radius
        )

        # Draw border
        border_color = self.active_border_color if self.active else self.border_color
        pygame.draw.rect(
            surface, border_color, self.rect, width=2, border_radius=self.corner_radius
        )

        # Prepare text to display
        display_text = self.text
        if self.password_mode:
            display_text = "*" * len(self.text)

        # Render text or placeholder
        if display_text:
            text_surf = self.font.render(display_text, True, self.text_color)
        else:
            text_surf = self.font.render(self.placeholder, True, (100, 100, 110))

        # Calculate text position (left-aligned with padding)
        text_x = self.rect.x + 10
        text_y = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (text_x, text_y))

        # Draw cursor when field is active
        if self.active and self.cursor_visible:
            cursor_x = text_x + text_surf.get_width()
            pygame.draw.line(
                surface,
                self.text_color,
                (cursor_x, text_y + 2),
                (cursor_x, text_y + text_surf.get_height() - 2),
                2,
            )
