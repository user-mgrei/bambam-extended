#!/usr/bin/env python3
# Copyright (C) 2026 BamBam Plus Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
TUI (Text User Interface) for BamBam Plus configuration and launching.
Provides an easy-to-use menu system for configuring and running BamBam,
with optional cage compositor integration for Wayland.
"""

import curses
import os
import shutil
import subprocess
import sys
from typing import List, Optional, Callable

from bambam_config import (
    load_config, save_config,
    discover_extensions, discover_backgrounds,
)


class MenuItem:
    """Represents a single menu item."""

    def __init__(self, label: str, action: Optional[Callable] = None,
                 submenu: Optional['Menu'] = None,
                 value_getter: Optional[Callable[[], str]] = None):
        self.label = label
        self.action = action
        self.submenu = submenu
        self.value_getter = value_getter

    def get_display_text(self, width: int = 40) -> str:
        """Get display text with optional value."""
        if self.value_getter:
            value = self.value_getter()
            label_width = width - len(value) - 3
            return f"{self.label:<{label_width}} [{value}]"
        return self.label


class Menu:
    """A menu containing multiple items."""

    def __init__(self, title: str, items: List[MenuItem]):
        self.title = title
        self.items = items
        self.selected = 0

    def add_item(self, item: MenuItem):
        """Add an item to the menu."""
        self.items.append(item)


class BambamTUI:
    """Main TUI application for BamBam Plus."""

    # Color pairs
    COLOR_NORMAL = 1
    COLOR_SELECTED = 2
    COLOR_HEADER = 3
    COLOR_VALUE = 4
    COLOR_ERROR = 5
    COLOR_SUCCESS = 6

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.config = load_config()
        self.running = True
        self.message = ""
        self.message_is_error = False

        # Find bambam.py location
        self.bambam_path = self._find_bambam()

        # Initialize curses
        self._init_curses()

        # Build menu structure
        self.main_menu = self._build_main_menu()
        self.current_menu = self.main_menu
        self.menu_stack: List[Menu] = []

    def _find_bambam(self) -> str:
        """Find the bambam.py script."""
        # Check same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bambam_path = os.path.join(script_dir, 'bambam.py')
        if os.path.exists(bambam_path):
            return bambam_path

        # Check system paths
        for path in ['/usr/games/bambam', '/usr/local/bin/bambam']:
            if os.path.exists(path):
                return path

        return 'bambam.py'

    def _init_curses(self):
        """Initialize curses settings."""
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.use_default_colors()

        # Initialize color pairs
        curses.init_pair(self.COLOR_NORMAL, curses.COLOR_WHITE, -1)
        curses.init_pair(self.COLOR_SELECTED, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(self.COLOR_HEADER, curses.COLOR_YELLOW, -1)
        curses.init_pair(self.COLOR_VALUE, curses.COLOR_GREEN, -1)
        curses.init_pair(self.COLOR_ERROR, curses.COLOR_RED, -1)
        curses.init_pair(self.COLOR_SUCCESS, curses.COLOR_GREEN, -1)

    def _build_main_menu(self) -> Menu:
        """Build the main menu structure."""
        return Menu("BamBam Plus - Configuration", [
            MenuItem("▶  Start BamBam", action=self._start_bambam),
            MenuItem("▶  Start BamBam (with Cage)", action=self._start_bambam_cage),
            MenuItem("▶  Run All Modes", action=self._start_all_modes),
            MenuItem(""),  # Separator
            MenuItem("⚙  Extension Settings", submenu=self._build_extension_menu()),
            MenuItem("⚙  Display Settings", submenu=self._build_display_menu()),
            MenuItem("⚙  Audio Settings", submenu=self._build_audio_menu()),
            MenuItem("⚙  Background Settings", submenu=self._build_background_menu()),
            MenuItem("⚙  Keypress Triggers", submenu=self._build_keypress_menu()),
            MenuItem("⚙  Cage Settings", submenu=self._build_cage_menu()),
            MenuItem(""),  # Separator
            MenuItem("💾  Save Configuration", action=self._save_config),
            MenuItem("🔄  Reload Configuration", action=self._reload_config),
            MenuItem("❌  Exit", action=self._exit),
        ])

    def _build_extension_menu(self) -> Menu:
        """Build extension settings menu."""
        items = [
            MenuItem("← Back", action=self._go_back),
            MenuItem(""),
        ]

        # Add available extensions
        extensions = discover_extensions()
        if extensions:
            items.append(MenuItem("Select Extension:"))
            items.append(MenuItem("  (none)",
                                  action=lambda: self._set_extension(""),
                                  value_getter=lambda: "●" if not self.config.current_extension else ""))
            for ext in extensions:
                items.append(MenuItem(f"  {ext}",
                                      action=lambda e=ext: self._set_extension(e),
                                      value_getter=lambda e=ext: "●" if self.config.current_extension == e else ""))
        else:
            items.append(MenuItem("No extensions found"))

        items.append(MenuItem(""))
        items.append(MenuItem("Distinct Mode (audio+image pairing)",
                              action=self._toggle_distinct_mode,
                              value_getter=lambda: "ON" if (self._get_current_ext_config() and self._get_current_ext_config().distinct_mode) else "OFF"))

        return Menu("Extension Settings", items)

    def _build_display_menu(self) -> Menu:
        """Build display settings menu."""
        return Menu("Display Settings", [
            MenuItem("← Back", action=self._go_back),
            MenuItem(""),
            MenuItem("Dark Mode",
                     action=self._toggle_dark_mode,
                     value_getter=lambda: "ON" if self.config.display.dark_mode else "OFF"),
            MenuItem("Uppercase Letters",
                     action=self._toggle_uppercase,
                     value_getter=lambda: "ON" if self.config.display.uppercase else "OFF"),
            MenuItem("Fullscreen",
                     action=self._toggle_fullscreen,
                     value_getter=lambda: "ON" if self.config.display.fullscreen else "OFF"),
        ])

    def _build_audio_menu(self) -> Menu:
        """Build audio settings menu."""
        return Menu("Audio Settings", [
            MenuItem("← Back", action=self._go_back),
            MenuItem(""),
            MenuItem("Sound Enabled",
                     action=self._toggle_sound,
                     value_getter=lambda: "ON" if self.config.audio.sound_enabled else "OFF"),
            MenuItem("Start Muted",
                     action=self._toggle_start_muted,
                     value_getter=lambda: "ON" if self.config.audio.start_muted else "OFF"),
            MenuItem("Deterministic Sounds",
                     action=self._toggle_deterministic,
                     value_getter=lambda: "ON" if self.config.audio.deterministic_sounds else "OFF"),
        ])

    def _build_background_menu(self) -> Menu:
        """Build background settings menu."""
        items = [
            MenuItem("← Back", action=self._go_back),
            MenuItem(""),
            MenuItem("Use Custom Background",
                     action=self._toggle_custom_bg,
                     value_getter=lambda: "ON" if self.config.background.use_custom_background else "OFF"),
            MenuItem("Cycle Backgrounds",
                     action=self._toggle_cycle_bg,
                     value_getter=lambda: "ON" if self.config.background.cycle_backgrounds else "OFF"),
            MenuItem(""),
        ]

        # Add available backgrounds
        backgrounds = discover_backgrounds()
        if backgrounds:
            items.append(MenuItem("Available Backgrounds:"))
            for bg in backgrounds[:10]:  # Limit to 10
                bg_name = os.path.basename(bg)
                items.append(MenuItem(f"  {bg_name}",
                                      action=lambda b=bg: self._set_background(b),
                                      value_getter=lambda b=bg: "●" if self.config.background.custom_background_path == b else ""))
        else:
            items.append(MenuItem("No backgrounds found"))
            items.append(MenuItem("(Add images to ~/.local/share/bambam/backgrounds/)"))

        return Menu("Background Settings", items)

    def _build_keypress_menu(self) -> Menu:
        """Build keypress trigger settings menu."""
        return Menu("Keypress Trigger Settings", [
            MenuItem("← Back", action=self._go_back),
            MenuItem(""),
            MenuItem("═══ Random Mode Change ═══"),
            MenuItem("Enable Mode Change",
                     action=self._toggle_mode_change,
                     value_getter=lambda: "ON" if self.config.keypress_triggers.mode_change_enabled else "OFF"),
            MenuItem("Min Keypresses",
                     action=lambda: self._adjust_value('mode_min', -10),
                     value_getter=lambda: str(self.config.keypress_triggers.mode_change_min)),
            MenuItem("Max Keypresses",
                     action=lambda: self._adjust_value('mode_max', 10),
                     value_getter=lambda: str(self.config.keypress_triggers.mode_change_max)),
            MenuItem(""),
            MenuItem("═══ Random Background Change ═══"),
            MenuItem("Enable Background Change",
                     action=self._toggle_bg_change,
                     value_getter=lambda: "ON" if self.config.keypress_triggers.background_change_enabled else "OFF"),
            MenuItem("Min Keypresses",
                     action=lambda: self._adjust_value('bg_min', -10),
                     value_getter=lambda: str(self.config.keypress_triggers.background_change_min)),
            MenuItem("Max Keypresses",
                     action=lambda: self._adjust_value('bg_max', 10),
                     value_getter=lambda: str(self.config.keypress_triggers.background_change_max)),
            MenuItem(""),
            MenuItem("(Use ←/→ arrows to adjust values)"),
        ])

    def _build_cage_menu(self) -> Menu:
        """Build cage compositor settings menu."""
        cage_available = shutil.which('cage') is not None
        status = "installed" if cage_available else "NOT FOUND"

        return Menu("Cage Compositor Settings", [
            MenuItem("← Back", action=self._go_back),
            MenuItem(""),
            MenuItem(f"Cage Status: {status}"),
            MenuItem(""),
            MenuItem("Use Cage",
                     action=self._toggle_cage,
                     value_getter=lambda: "ON" if self.config.cage.use_cage else "OFF"),
            MenuItem(""),
            MenuItem("Cage provides a secure Wayland session"),
            MenuItem("that locks keyboard/mouse to BamBam."),
            MenuItem(""),
            MenuItem("Install with: sudo apt install cage"),
        ])

    # Action methods
    def _go_back(self):
        """Return to previous menu."""
        if self.menu_stack:
            self.current_menu = self.menu_stack.pop()

    def _exit(self):
        """Exit the TUI."""
        self.running = False

    def _save_config(self):
        """Save current configuration."""
        if save_config(self.config):
            self.message = "Configuration saved successfully!"
            self.message_is_error = False
        else:
            self.message = "Failed to save configuration!"
            self.message_is_error = True

    def _reload_config(self):
        """Reload configuration from file."""
        self.config = load_config()
        self.message = "Configuration reloaded!"
        self.message_is_error = False

    def _set_extension(self, ext_name: str):
        """Set the current extension."""
        self.config.current_extension = ext_name
        self.message = f"Extension set to: {ext_name or '(none)'}"
        self.message_is_error = False

    def _get_current_ext_config(self):
        """Get config for current extension."""
        if not self.config.current_extension:
            return None
        for ext in self.config.extensions:
            if ext.name == self.config.current_extension:
                return ext
        return None

    def _toggle_distinct_mode(self):
        """Toggle distinct mode for current extension."""
        ext_config = self._get_current_ext_config()
        if ext_config:
            ext_config.distinct_mode = not ext_config.distinct_mode
        else:
            self.message = "Select an extension first"
            self.message_is_error = True

    def _toggle_dark_mode(self):
        self.config.display.dark_mode = not self.config.display.dark_mode

    def _toggle_uppercase(self):
        self.config.display.uppercase = not self.config.display.uppercase

    def _toggle_fullscreen(self):
        self.config.display.fullscreen = not self.config.display.fullscreen

    def _toggle_sound(self):
        self.config.audio.sound_enabled = not self.config.audio.sound_enabled

    def _toggle_start_muted(self):
        self.config.audio.start_muted = not self.config.audio.start_muted

    def _toggle_deterministic(self):
        self.config.audio.deterministic_sounds = not self.config.audio.deterministic_sounds

    def _toggle_custom_bg(self):
        self.config.background.use_custom_background = not self.config.background.use_custom_background

    def _toggle_cycle_bg(self):
        self.config.background.cycle_backgrounds = not self.config.background.cycle_backgrounds

    def _set_background(self, bg_path: str):
        self.config.background.custom_background_path = bg_path
        self.config.background.use_custom_background = True
        self.message = f"Background set to: {os.path.basename(bg_path)}"
        self.message_is_error = False

    def _toggle_mode_change(self):
        self.config.keypress_triggers.mode_change_enabled = not self.config.keypress_triggers.mode_change_enabled

    def _toggle_bg_change(self):
        self.config.keypress_triggers.background_change_enabled = not self.config.keypress_triggers.background_change_enabled

    def _toggle_cage(self):
        self.config.cage.use_cage = not self.config.cage.use_cage

    def _adjust_value(self, which: str, delta: int):
        """Adjust a numeric value. Called by arrow keys."""
        triggers = self.config.keypress_triggers
        if which == 'mode_min':
            triggers.mode_change_min = max(1, triggers.mode_change_min + delta)
        elif which == 'mode_max':
            triggers.mode_change_max = max(triggers.mode_change_min + 1, triggers.mode_change_max + delta)
        elif which == 'bg_min':
            triggers.background_change_min = max(1, triggers.background_change_min + delta)
        elif which == 'bg_max':
            triggers.background_change_max = max(triggers.background_change_min + 1, triggers.background_change_max + delta)

    def _start_bambam(self):
        """Start BamBam without cage."""
        self._launch_bambam(use_cage=False)

    def _start_bambam_cage(self):
        """Start BamBam with cage compositor."""
        if not shutil.which('cage'):
            self.message = "Cage not installed! Run: sudo apt install cage"
            self.message_is_error = True
            return
        self._launch_bambam(use_cage=True)

    def _start_all_modes(self):
        """Start BamBam with all modes cycling."""
        self.config.all_modes_enabled = True
        self._launch_bambam(use_cage=self.config.cage.use_cage)

    def _launch_bambam(self, use_cage: bool = False):
        """Launch BamBam with current configuration."""
        # Build command
        bambam_args = self.config.to_bambam_args()
        cmd = [sys.executable, self.bambam_path] + bambam_args

        if use_cage:
            # Wrap with cage
            cage_cmd = [self.config.cage.cage_command]
            cage_cmd.extend(self.config.cage.cage_args)
            cage_cmd.append('--')
            cage_cmd.extend(cmd)
            cmd = cage_cmd

        # End curses temporarily
        curses.endwin()

        try:
            self.message = "Starting BamBam..."
            print(f"\n[BamBam TUI] Launching: {' '.join(cmd)}\n")
            subprocess.run(cmd)
        except Exception as e:
            self.message = f"Failed to start: {e}"
            self.message_is_error = True
        finally:
            # Restore curses
            self.stdscr = curses.initscr()
            self._init_curses()

    def draw(self):
        """Draw the current screen."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Draw header
        header = "╔" + "═" * (width - 2) + "╗"
        self.stdscr.addstr(0, 0, header[:width-1], curses.color_pair(self.COLOR_HEADER))

        title = f"║ {self.current_menu.title} "
        title = title + " " * (width - len(title) - 1) + "║"
        self.stdscr.addstr(1, 0, title[:width-1], curses.color_pair(self.COLOR_HEADER))

        footer_header = "╚" + "═" * (width - 2) + "╝"
        self.stdscr.addstr(2, 0, footer_header[:width-1], curses.color_pair(self.COLOR_HEADER))

        # Draw menu items
        start_y = 4
        max_items = height - start_y - 4

        # Calculate scroll offset
        scroll_offset = 0
        if self.current_menu.selected >= max_items:
            scroll_offset = self.current_menu.selected - max_items + 1

        visible_items = self.current_menu.items[scroll_offset:scroll_offset + max_items]

        for i, item in enumerate(visible_items):
            y = start_y + i
            if y >= height - 3:
                break

            actual_index = i + scroll_offset
            is_selected = actual_index == self.current_menu.selected

            # Skip separators
            if not item.label:
                continue

            display_text = item.get_display_text(width - 4)

            if is_selected:
                attr = curses.color_pair(self.COLOR_SELECTED) | curses.A_BOLD
                self.stdscr.addstr(y, 2, f" {display_text:<{width-5}} ", attr)
            else:
                attr = curses.color_pair(self.COLOR_NORMAL)
                self.stdscr.addstr(y, 2, f"  {display_text}", attr)

        # Draw message if any
        if self.message:
            msg_y = height - 2
            color = self.COLOR_ERROR if self.message_is_error else self.COLOR_SUCCESS
            self.stdscr.addstr(msg_y, 2, self.message[:width-4], curses.color_pair(color))

        # Draw help bar
        help_text = "↑↓:Navigate  Enter:Select  ←→:Adjust  q:Quit"
        self.stdscr.addstr(height - 1, 2, help_text[:width-4], curses.A_DIM)

        self.stdscr.refresh()

    def handle_input(self):
        """Handle keyboard input."""
        key = self.stdscr.getch()

        # Clear message on any keypress
        self.message = ""

        if key in (ord('q'), ord('Q')):
            if self.menu_stack:
                self._go_back()
            else:
                self.running = False

        elif key == curses.KEY_UP:
            # Move up, skipping empty items
            new_pos = self.current_menu.selected - 1
            while new_pos >= 0 and not self.current_menu.items[new_pos].label:
                new_pos -= 1
            if new_pos >= 0:
                self.current_menu.selected = new_pos

        elif key == curses.KEY_DOWN:
            # Move down, skipping empty items
            new_pos = self.current_menu.selected + 1
            while new_pos < len(self.current_menu.items) and not self.current_menu.items[new_pos].label:
                new_pos += 1
            if new_pos < len(self.current_menu.items):
                self.current_menu.selected = new_pos

        elif key in (curses.KEY_ENTER, ord('\n'), ord(' ')):
            item = self.current_menu.items[self.current_menu.selected]
            if item.submenu:
                self.menu_stack.append(self.current_menu)
                self.current_menu = item.submenu
                self.current_menu.selected = 0
            elif item.action:
                item.action()

        elif key == curses.KEY_LEFT:
            # Decrease value for current item
            item = self.current_menu.items[self.current_menu.selected]
            if 'Min' in item.label or 'Max' in item.label:
                if 'Mode' in self.current_menu.title or 'Keypress' in self.current_menu.title:
                    if 'Mode' in item.label and 'Min' in item.label:
                        self._adjust_value('mode_min', -10)
                    elif 'Mode' in item.label and 'Max' in item.label:
                        self._adjust_value('mode_max', -10)
                    elif 'Background' in item.label or 'bg' in item.label.lower():
                        if 'Min' in item.label:
                            self._adjust_value('bg_min', -10)
                        else:
                            self._adjust_value('bg_max', -10)

        elif key == curses.KEY_RIGHT:
            # Increase value for current item
            item = self.current_menu.items[self.current_menu.selected]
            if 'Min' in item.label or 'Max' in item.label:
                if 'Mode' in self.current_menu.title or 'Keypress' in self.current_menu.title:
                    if 'Mode' in item.label and 'Min' in item.label:
                        self._adjust_value('mode_min', 10)
                    elif 'Mode' in item.label and 'Max' in item.label:
                        self._adjust_value('mode_max', 10)
                    elif 'Background' in item.label or 'bg' in item.label.lower():
                        if 'Min' in item.label:
                            self._adjust_value('bg_min', 10)
                        else:
                            self._adjust_value('bg_max', 10)

        elif key == curses.KEY_BACKSPACE or key == 127:
            self._go_back()

    def run(self):
        """Main TUI event loop."""
        while self.running:
            self.draw()
            self.handle_input()


def main(stdscr):
    """Main entry point for curses application."""
    tui = BambamTUI(stdscr)
    tui.run()


if __name__ == '__main__':
    # Check if running in a terminal
    if not sys.stdout.isatty():
        print("Error: This program requires a terminal.")
        sys.exit(1)

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Make sure terminal is restored on error
        curses.endwin()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
