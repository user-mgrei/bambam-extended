#!/usr/bin/env python3
# Copyright (C) 2026 BamBam Plus Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
BamBam Plus TUI Launcher

A terminal user interface for configuring and launching BamBam.
Supports running in cage compositor for kiosk mode on Raspberry Pi.

Usage:
    ./bambam_tui.py              # Interactive TUI menu
    ./bambam_tui.py --run        # Run with saved config
    ./bambam_tui.py --run-cage   # Run in cage compositor
    ./bambam_tui.py --list-ext   # List available extensions
"""

import argparse
import curses
import os
import shutil
import subprocess
import sys
from typing import List, Optional, Callable, Any

from bambam_config import (
    load_config, save_config,
    list_available_extensions, list_background_images,
    ensure_directories, get_backgrounds_dir
)


# Box drawing characters
BOX_CHARS = {
    'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝',
    'h': '═', 'v': '║',
    'lt': '╠', 'rt': '╣', 'tt': '╦', 'bt': '╩', 'x': '╬'
}


class TUIMenu:
    """Base class for TUI menus using curses."""

    def __init__(self, stdscr, title: str):
        self.stdscr = stdscr
        self.title = title
        self.selected = 0
        self.items: List[tuple] = []  # (label, action, value_getter)

        # Setup curses
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)      # Title
        curses.init_pair(2, curses.COLOR_GREEN, -1)     # Selected
        curses.init_pair(3, curses.COLOR_YELLOW, -1)    # Value
        curses.init_pair(4, curses.COLOR_RED, -1)       # Warning
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Highlight

    def add_item(self, label: str, action: Callable, value_getter: Callable = None):
        """Add a menu item."""
        self.items.append((label, action, value_getter))

    def draw_box(self, y: int, x: int, height: int, width: int):
        """Draw a box at the specified position."""
        # Top border
        self.stdscr.addstr(y, x, BOX_CHARS['tl'] + BOX_CHARS['h'] * (width - 2) + BOX_CHARS['tr'])
        # Sides
        for i in range(1, height - 1):
            self.stdscr.addstr(y + i, x, BOX_CHARS['v'])
            self.stdscr.addstr(y + i, x + width - 1, BOX_CHARS['v'])
        # Bottom border
        self.stdscr.addstr(y + height - 1, x, BOX_CHARS['bl'] + BOX_CHARS['h'] * (width - 2) + BOX_CHARS['br'])

    def draw(self):
        """Draw the menu."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Calculate menu dimensions
        menu_width = min(60, width - 4)
        menu_height = len(self.items) + 6
        start_y = max(0, (height - menu_height) // 2)
        start_x = max(0, (width - menu_width) // 2)

        # Draw box
        try:
            self.draw_box(start_y, start_x, menu_height, menu_width)
        except curses.error:
            pass

        # Draw title
        title_x = start_x + (menu_width - len(self.title)) // 2
        try:
            self.stdscr.addstr(start_y + 1, title_x, self.title, curses.color_pair(1) | curses.A_BOLD)
            # Separator line
            sep_line = BOX_CHARS['lt'] + BOX_CHARS['h'] * (menu_width - 2) + BOX_CHARS['rt']
            self.stdscr.addstr(start_y + 2, start_x, sep_line)
        except curses.error:
            pass

        # Draw items
        for idx, (label, _, value_getter) in enumerate(self.items):
            y = start_y + 3 + idx
            x = start_x + 2

            # Prepare the display string
            if value_getter:
                value = value_getter()
                display = f"  {label}: "
                value_str = str(value) if value is not None else "None"
            else:
                display = f"  {label}"
                value_str = ""

            # Highlight selected item
            if idx == self.selected:
                attr = curses.color_pair(5) | curses.A_BOLD
                prefix = "▶ "
            else:
                attr = curses.A_NORMAL
                prefix = "  "

            try:
                # Draw prefix and label
                self.stdscr.addstr(y, x, prefix, attr)
                self.stdscr.addstr(y, x + 2, display.strip(), attr)

                # Draw value in different color
                if value_str:
                    val_x = x + 2 + len(display.strip()) + 1
                    val_attr = curses.color_pair(3) if idx != self.selected else attr
                    self.stdscr.addstr(y, val_x, value_str, val_attr)
            except curses.error:
                pass

        # Draw help text
        help_y = start_y + menu_height
        help_text = "↑↓:Navigate  Enter:Select  Q:Back/Quit"
        help_x = start_x + (menu_width - len(help_text)) // 2
        try:
            self.stdscr.addstr(help_y, help_x, help_text, curses.A_DIM)
        except curses.error:
            pass

        self.stdscr.refresh()

    def run(self) -> Any:
        """Run the menu loop."""
        while True:
            self.draw()
            key = self.stdscr.getch()

            if key == curses.KEY_UP:
                self.selected = (self.selected - 1) % len(self.items)
            elif key == curses.KEY_DOWN:
                self.selected = (self.selected + 1) % len(self.items)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                _, action, _ = self.items[self.selected]
                result = action()
                if result == 'quit' or result == 'back':
                    return result
            elif key in [ord('q'), ord('Q')]:
                return 'back'


class BambamTUI:
    """Main BamBam TUI application."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.config = load_config()
        ensure_directories()

    def show_message(self, title: str, message: str, wait: bool = True):
        """Show a message dialog."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        lines = message.split('\n')
        box_width = min(max(len(line) for line in lines) + 4, width - 4)
        box_height = len(lines) + 4
        start_y = (height - box_height) // 2
        start_x = (width - box_width) // 2

        # Draw box
        menu = TUIMenu(self.stdscr, "")
        menu.draw_box(start_y, start_x, box_height, box_width)

        # Draw title
        title_x = start_x + (box_width - len(title)) // 2
        try:
            self.stdscr.addstr(start_y + 1, title_x, title, curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass

        # Draw message
        for i, line in enumerate(lines):
            try:
                self.stdscr.addstr(start_y + 2 + i, start_x + 2, line)
            except curses.error:
                pass

        if wait:
            try:
                self.stdscr.addstr(start_y + box_height - 1, start_x + 2, "Press any key...")
            except curses.error:
                pass
            self.stdscr.refresh()
            self.stdscr.getch()

    def select_from_list(self, title: str, items: List[str], allow_none: bool = True) -> Optional[str]:
        """Show a selection menu and return the chosen item."""
        menu = TUIMenu(self.stdscr, title)

        result = [None]  # Use list to allow modification in closure

        if allow_none:
            def select_none():
                result[0] = None
                return 'back'
            menu.add_item("(None)", select_none)

        for item in items:
            def make_selector(val):
                def select():
                    result[0] = val
                    return 'back'
                return select
            menu.add_item(item, make_selector(item))

        def go_back():
            return 'back'
        menu.add_item("← Back", go_back)

        menu.run()
        return result[0]

    def toggle_bool(self, getter: Callable, setter: Callable) -> Callable:
        """Create a toggle function for boolean settings."""
        def toggle():
            current = getter()
            setter(not current)
            save_config(self.config)
        return toggle

    def edit_range(self, title: str, current: tuple) -> tuple:
        """Edit a numeric range (min, max)."""
        curses.echo()
        curses.curs_set(1)

        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        y = height // 2 - 2

        try:
            self.stdscr.addstr(y, 2, title, curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(y + 1, 2, f"Current: {current[0]} - {current[1]}")
            self.stdscr.addstr(y + 2, 2, "Enter min value: ")
            self.stdscr.refresh()

            min_str = self.stdscr.getstr(y + 2, 19, 10).decode('utf-8').strip()

            self.stdscr.addstr(y + 3, 2, "Enter max value: ")
            self.stdscr.refresh()

            max_str = self.stdscr.getstr(y + 3, 19, 10).decode('utf-8').strip()
        except curses.error:
            min_str = ""
            max_str = ""

        curses.noecho()
        curses.curs_set(0)

        try:
            min_val = int(min_str) if min_str else current[0]
            max_val = int(max_str) if max_str else current[1]
            if min_val > max_val:
                min_val, max_val = max_val, min_val
            return (max(1, min_val), max(1, max_val))
        except ValueError:
            return current

    def main_menu(self):
        """Show the main menu."""
        menu = TUIMenu(self.stdscr, "BamBam Plus Launcher")

        def start_game():
            self.run_bambam(use_cage=False)
            return None

        def start_in_cage():
            self.run_bambam(use_cage=True)
            return None

        def run_all_modes():
            self.config.mode.all_modes_enabled = True
            self.config.auto_switch.enabled = True  # Enable auto-switch for all modes
            save_config(self.config)
            self.run_bambam(use_cage=self.config.launcher.use_cage)
            return None

        def mode_menu():
            self.show_mode_menu()
            return None

        def display_menu():
            self.show_display_menu()
            return None

        def audio_menu():
            self.show_audio_menu()
            return None

        def autoswitch_menu():
            self.show_autoswitch_menu()
            return None

        def quit_app():
            return 'quit'

        menu.add_item("Start Game", start_game)
        menu.add_item("Start in Cage (Kiosk)", start_in_cage)
        menu.add_item("Run All Modes", run_all_modes)
        menu.add_item("Mode/Extension Settings", mode_menu)
        menu.add_item("Display Settings", display_menu)
        menu.add_item("Audio Settings", audio_menu)
        menu.add_item("Auto-Switch Settings", autoswitch_menu)
        menu.add_item("Quit", quit_app)

        return menu.run()

    def show_mode_menu(self):
        """Show mode/extension settings menu."""
        menu = TUIMenu(self.stdscr, "Mode/Extension Settings")

        def select_extension():
            extensions = list_available_extensions()
            if not extensions:
                self.show_message("No Extensions",
                                  "No extensions found.\n"
                                  "Place extensions in ~/.local/share/bambam/extensions/")
                return None
            selected = self.select_from_list("Select Extension", extensions)
            self.config.mode.active_extension = selected
            save_config(self.config)
            return None

        def get_extension():
            return self.config.mode.active_extension or "(default)"

        def get_all_modes():
            return "ON" if self.config.mode.all_modes_enabled else "OFF"

        menu.add_item("Extension", select_extension, get_extension)
        menu.add_item("All Modes", self.toggle_bool(
            lambda: self.config.mode.all_modes_enabled,
            lambda v: setattr(self.config.mode, 'all_modes_enabled', v)
        ), get_all_modes)

        def go_back():
            return 'back'
        menu.add_item("← Back", go_back)

        menu.run()

    def show_display_menu(self):
        """Show display settings menu."""
        menu = TUIMenu(self.stdscr, "Display Settings")

        def get_dark():
            return "ON" if self.config.display.dark_mode else "OFF"

        def get_uppercase():
            return "ON" if self.config.display.uppercase else "OFF"

        def get_background():
            bg = self.config.display.background_image
            return os.path.basename(bg) if bg else "(default)"

        def select_background():
            images = list_background_images()
            bg_dir = get_backgrounds_dir()
            if not images:
                self.show_message("No Backgrounds",
                                  f"No background images found.\nAdd images to:\n{bg_dir}")
                return None
            selected = self.select_from_list("Select Background", [os.path.basename(i) for i in images])
            if selected:
                # Find full path
                for img in images:
                    if os.path.basename(img) == selected:
                        self.config.display.background_image = img
                        break
            else:
                self.config.display.background_image = None
            save_config(self.config)
            return None

        menu.add_item("Dark Mode", self.toggle_bool(
            lambda: self.config.display.dark_mode,
            lambda v: setattr(self.config.display, 'dark_mode', v)
        ), get_dark)
        menu.add_item("Uppercase", self.toggle_bool(
            lambda: self.config.display.uppercase,
            lambda v: setattr(self.config.display, 'uppercase', v)
        ), get_uppercase)
        menu.add_item("Background", select_background, get_background)

        def go_back():
            return 'back'
        menu.add_item("← Back", go_back)

        menu.run()

    def show_audio_menu(self):
        """Show audio settings menu."""
        menu = TUIMenu(self.stdscr, "Audio Settings")

        def get_muted():
            return "ON" if self.config.audio.start_muted else "OFF"

        def get_deterministic():
            return "ON" if self.config.audio.deterministic_sounds else "OFF"

        menu.add_item("Start Muted", self.toggle_bool(
            lambda: self.config.audio.start_muted,
            lambda v: setattr(self.config.audio, 'start_muted', v)
        ), get_muted)
        menu.add_item("Deterministic", self.toggle_bool(
            lambda: self.config.audio.deterministic_sounds,
            lambda v: setattr(self.config.audio, 'deterministic_sounds', v)
        ), get_deterministic)

        def go_back():
            return 'back'
        menu.add_item("← Back", go_back)

        menu.run()

    def show_autoswitch_menu(self):
        """Show auto-switch settings menu."""
        menu = TUIMenu(self.stdscr, "Auto-Switch Settings")

        def get_enabled():
            return "ON" if self.config.auto_switch.enabled else "OFF"

        def get_mode_range():
            r = self.config.auto_switch.mode_change_range
            return f"{r[0]}-{r[1]} keys"

        def get_bg_range():
            r = self.config.auto_switch.background_change_range
            return f"{r[0]}-{r[1]} keys"

        def edit_mode_range():
            new_range = self.edit_range("Mode Change Range", self.config.auto_switch.mode_change_range)
            self.config.auto_switch.mode_change_range = new_range
            save_config(self.config)
            return None

        def edit_bg_range():
            new_range = self.edit_range("Background Change Range", self.config.auto_switch.background_change_range)
            self.config.auto_switch.background_change_range = new_range
            save_config(self.config)
            return None

        menu.add_item("Enabled", self.toggle_bool(
            lambda: self.config.auto_switch.enabled,
            lambda v: setattr(self.config.auto_switch, 'enabled', v)
        ), get_enabled)
        menu.add_item("Mode Change", edit_mode_range, get_mode_range)
        menu.add_item("Background Change", edit_bg_range, get_bg_range)

        def go_back():
            return 'back'
        menu.add_item("← Back", go_back)

        menu.run()

    def run_bambam(self, use_cage: bool = False):
        """Launch bambam with current configuration."""
        # Build command
        script_dir = os.path.dirname(os.path.realpath(__file__))
        bambam_path = os.path.join(script_dir, 'bambam.py')

        if not os.path.exists(bambam_path):
            # Try system path
            bambam_path = shutil.which('bambam') or '/usr/games/bambam'

        args = self.config.to_cli_args()
        cmd = [sys.executable, bambam_path] + args

        if use_cage:
            # Check if cage is available
            if not shutil.which('cage'):
                self.show_message("Error", "cage compositor not found.\nInstall with: sudo apt install cage")
                return

            cmd = ['cage', '--'] + cmd

        # Exit curses temporarily
        curses.endwin()

        try:
            # Run bambam
            print(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd)
        except Exception as e:
            print(f"Error running bambam: {e}")
            input("Press Enter to continue...")

        # Restore curses
        self.stdscr = curses.initscr()
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

    def run(self):
        """Run the TUI application."""
        while True:
            result = self.main_menu()
            if result == 'quit':
                break


def main_tui(stdscr):
    """Curses wrapper main function."""
    app = BambamTUI(stdscr)
    app.run()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='BamBam Plus TUI Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Interactive TUI menu
  %(prog)s --run        # Run with saved configuration
  %(prog)s --run-cage   # Run in cage compositor
  %(prog)s --list-ext   # List available extensions
        """)
    parser.add_argument('--run', action='store_true',
                        help='Run bambam with saved configuration')
    parser.add_argument('--run-cage', action='store_true',
                        help='Run bambam in cage compositor')
    parser.add_argument('--list-ext', action='store_true',
                        help='List available extensions')
    parser.add_argument('--show-config', action='store_true',
                        help='Show current configuration')
    args = parser.parse_args()

    ensure_directories()

    if args.list_ext:
        extensions = list_available_extensions()
        if extensions:
            print("Available extensions:")
            for ext in extensions:
                print(f"  - {ext}")
        else:
            print("No extensions found.")
        return

    if args.show_config:
        config = load_config()
        cli_args = config.to_cli_args()
        print("Current configuration CLI args:", ' '.join(cli_args) if cli_args else "(defaults)")
        return

    if args.run or args.run_cage:
        config = load_config()
        script_dir = os.path.dirname(os.path.realpath(__file__))
        bambam_path = os.path.join(script_dir, 'bambam.py')

        if not os.path.exists(bambam_path):
            bambam_path = shutil.which('bambam') or '/usr/games/bambam'

        cli_args = config.to_cli_args()
        cmd = [sys.executable, bambam_path] + cli_args

        if args.run_cage:
            if not shutil.which('cage'):
                print("Error: cage compositor not found. Install with: sudo apt install cage",
                      file=sys.stderr)
                sys.exit(1)
            cmd = ['cage', '--'] + cmd

        print(f"Running: {' '.join(cmd)}")
        os.execvp(cmd[0], cmd)
        return

    # Run interactive TUI
    curses.wrapper(main_tui)


if __name__ == '__main__':
    main()
