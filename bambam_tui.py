#!/usr/bin/env python3
"""
BamBam Plus TUI - Terminal User Interface for configuration and launching.

This TUI provides:
- Easy configuration of BamBam settings
- Mode/extension selection
- Background image management
- Cage compositor integration for secure kiosk mode
- Random mode/background switching settings

Usage:
    python3 bambam_tui.py           # Launch TUI
    python3 bambam_tui.py --run     # Run BamBam with current config
    python3 bambam_tui.py --cage    # Run BamBam in cage compositor
"""

import argparse
import curses
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Configuration paths
CONFIG_FILE = Path(__file__).parent / "bambam_config.yaml"
DEFAULT_CONFIG_FILE = Path(__file__).parent / "bambam_config.yaml"
USER_CONFIG_DIR = Path.home() / ".config" / "bambam"
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.yaml"

# Color pairs
COLOR_NORMAL = 1
COLOR_HIGHLIGHT = 2
COLOR_HEADER = 3
COLOR_SUCCESS = 4
COLOR_WARNING = 5
COLOR_ERROR = 6


def load_config() -> dict:
    """Load configuration from file."""
    config_path = USER_CONFIG_FILE if USER_CONFIG_FILE.exists() else CONFIG_FILE

    if not YAML_AVAILABLE:
        return get_default_config()

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
            return merge_with_defaults(config)
    except Exception as e:
        print(f"Warning: Could not load config: {e}", file=sys.stderr)
        return get_default_config()


def save_config(config: dict) -> bool:
    """Save configuration to user config file."""
    if not YAML_AVAILABLE:
        return False

    try:
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(USER_CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}", file=sys.stderr)
        return False


def get_default_config() -> dict:
    """Return default configuration."""
    return {
        'general': {
            'dark_mode': False,
            'uppercase': False,
            'mute': False,
            'sticky_mouse': False,
            'deterministic_sounds': False,
        },
        'modes': {
            'active_extension': None,
            'available_extensions': ['alphanumeric-en_US'],
            'all_modes_enabled': False,
            'random_mode_change': {
                'enabled': False,
                'min_keypresses': 10,
                'max_keypresses': 50,
            },
        },
        'background': {
            'image_path': None,
            'images_directory': None,
            'random_change': {
                'enabled': False,
                'min_keypresses': 20,
                'max_keypresses': 100,
            },
        },
        'cage': {
            'enabled': True,
            'use_swaylock': True,
            'swaylock_config': '',
        },
        'audio': {
            'volume': 1.0,
            'prefer_ogg': True,
        },
        'display': {
            'max_image_width': 700,
            'target_fps': 60,
        },
        'advanced': {
            'random_seed': None,
            'trace': False,
            'sound_blacklist': [],
            'image_blacklist': [],
        },
    }


def merge_with_defaults(config: dict) -> dict:
    """Merge loaded config with defaults to ensure all keys exist."""
    defaults = get_default_config()

    def deep_merge(base: dict, override: dict) -> dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    return deep_merge(defaults, config)


def detect_extensions() -> list:
    """Detect available extensions in extension directories."""
    extensions = []
    search_paths = [
        Path(__file__).parent / "extensions",
        Path.home() / ".local" / "share" / "bambam" / "extensions",
        Path("/usr/share/bambam/extensions"),
    ]

    for path in search_paths:
        if path.exists() and path.is_dir():
            for item in path.iterdir():
                if item.is_dir() and (item / "event_map.yaml").exists():
                    if item.name not in extensions:
                        extensions.append(item.name)

    return sorted(extensions)


def detect_background_images(directory: Optional[str]) -> list:
    """Detect background images in a directory."""
    if not directory:
        return []

    path = Path(directory)
    if not path.exists():
        return []

    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
    images = []

    for item in path.iterdir():
        if item.is_file() and item.suffix.lower() in image_extensions:
            images.append(str(item))

    return sorted(images)


def check_dependencies() -> dict:
    """Check if required system dependencies are available."""
    deps = {
        'python3': shutil.which('python3') is not None,
        'cage': shutil.which('cage') is not None,
        'swaylock': shutil.which('swaylock') is not None,
        'pygame': False,
        'yaml': YAML_AVAILABLE,
    }

    try:
        import pygame  # noqa: F401
        deps['pygame'] = True
    except ImportError:
        pass

    return deps


def build_bambam_command(config: dict) -> list:
    """Build command line arguments for bambam.py based on config."""
    cmd = [sys.executable, str(Path(__file__).parent / "bambam.py")]

    general = config.get('general', {})
    modes = config.get('modes', {})
    advanced = config.get('advanced', {})

    if general.get('dark_mode'):
        cmd.append('--dark')
    if general.get('uppercase'):
        cmd.append('--uppercase')
    if general.get('mute'):
        cmd.append('--mute')
    if general.get('sticky_mouse'):
        cmd.append('--sticky-mouse')
    if general.get('deterministic_sounds'):
        cmd.append('--deterministic-sounds')

    if modes.get('active_extension'):
        cmd.extend(['--extension', modes['active_extension']])

    if advanced.get('trace'):
        cmd.append('--trace')

    for pattern in advanced.get('sound_blacklist', []):
        cmd.extend(['--sound_blacklist', pattern])

    for pattern in advanced.get('image_blacklist', []):
        cmd.extend(['--image_blacklist', pattern])

    return cmd


def run_bambam(config: dict, use_cage: bool = False) -> int:
    """Run BamBam with the given configuration."""
    cmd = build_bambam_command(config)
    cage_config = config.get('cage', {})

    if use_cage and cage_config.get('enabled', True):
        if not shutil.which('cage'):
            print("Error: cage compositor not found. Install with: sudo apt install cage")
            return 1

        # Create a launcher script for cage
        launcher_script = Path(__file__).parent / "bambam_launcher.sh"
        swaylock_cmd = ""

        if cage_config.get('use_swaylock') and shutil.which('swaylock'):
            swaylock_cmd = "\nswaylock"

        script_content = f"""#!/bin/bash
# Auto-generated BamBam launcher script
{' '.join(cmd)}
{swaylock_cmd}
"""
        with open(launcher_script, 'w') as f:
            f.write(script_content)
        os.chmod(launcher_script, 0o755)

        # Run cage with the launcher script
        cage_cmd = ['cage', str(launcher_script)]
        return subprocess.call(cage_cmd)
    else:
        return subprocess.call(cmd)


class MenuItem:
    """Represents a menu item."""

    def __init__(self, label: str, item_type: str = "action",
                 value: Any = None, options: list = None,
                 config_path: list = None, min_val: int = 0, max_val: int = 100):
        self.label = label
        self.item_type = item_type  # action, toggle, select, number, submenu
        self.value = value
        self.options = options or []
        self.config_path = config_path or []
        self.min_val = min_val
        self.max_val = max_val


class TUI:
    """Terminal User Interface for BamBam configuration."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.config = load_config()
        self.current_menu = "main"
        self.menu_stack = []
        self.selected_index = 0
        self.message = ""
        self.message_type = "info"

        # Initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(COLOR_NORMAL, curses.COLOR_WHITE, -1)
        curses.init_pair(COLOR_HIGHLIGHT, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(COLOR_HEADER, curses.COLOR_CYAN, -1)
        curses.init_pair(COLOR_SUCCESS, curses.COLOR_GREEN, -1)
        curses.init_pair(COLOR_WARNING, curses.COLOR_YELLOW, -1)
        curses.init_pair(COLOR_ERROR, curses.COLOR_RED, -1)

        # Hide cursor
        curses.curs_set(0)

        # Detect extensions
        self.extensions = detect_extensions()
        self.config['modes']['available_extensions'] = self.extensions

    def get_config_value(self, path: list) -> Any:
        """Get a value from config using a path list."""
        value = self.config
        for key in path:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def set_config_value(self, path: list, value: Any):
        """Set a value in config using a path list."""
        target = self.config
        for key in path[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[path[-1]] = value

    def get_menu_items(self) -> list:
        """Get menu items for the current menu."""
        if self.current_menu == "main":
            return [
                MenuItem("▶ START GAME", "action", "start"),
                MenuItem("▶ START IN CAGE (Secure)", "action", "start_cage"),
                MenuItem("", "separator"),
                MenuItem("⚙ General Settings", "submenu", "general"),
                MenuItem("🎵 Mode/Extension Settings", "submenu", "modes"),
                MenuItem("🎨 Theme Settings", "submenu", "themes"),
                MenuItem("🖼 Background Settings", "submenu", "background"),
                MenuItem("🔑 Keypress Patterns", "submenu", "patterns"),
                MenuItem("🔊 Audio Settings", "submenu", "audio"),
                MenuItem("📺 Display Settings", "submenu", "display"),
                MenuItem("🔧 Advanced Settings", "submenu", "advanced"),
                MenuItem("", "separator"),
                MenuItem("💾 Save Configuration", "action", "save"),
                MenuItem("🔄 Reload Configuration", "action", "reload"),
                MenuItem("📋 Check Dependencies", "action", "check_deps"),
                MenuItem("❌ Exit", "action", "exit"),
            ]

        elif self.current_menu == "general":
            return [
                MenuItem("← Back to Main Menu", "action", "back"),
                MenuItem("", "separator"),
                MenuItem("Dark Mode", "toggle",
                         self.get_config_value(['general', 'dark_mode']),
                         config_path=['general', 'dark_mode']),
                MenuItem("Uppercase Letters", "toggle",
                         self.get_config_value(['general', 'uppercase']),
                         config_path=['general', 'uppercase']),
                MenuItem("Start Muted", "toggle",
                         self.get_config_value(['general', 'mute']),
                         config_path=['general', 'mute']),
                MenuItem("Sticky Mouse Buttons", "toggle",
                         self.get_config_value(['general', 'sticky_mouse']),
                         config_path=['general', 'sticky_mouse']),
                MenuItem("Deterministic Sounds", "toggle",
                         self.get_config_value(['general', 'deterministic_sounds']),
                         config_path=['general', 'deterministic_sounds']),
            ]

        elif self.current_menu == "modes":
            ext_options = ["None"] + self.extensions
            current_ext = self.get_config_value(['modes', 'active_extension']) or "None"

            return [
                MenuItem("← Back to Main Menu", "action", "back"),
                MenuItem("", "separator"),
                MenuItem("Active Extension", "select", current_ext,
                         options=ext_options,
                         config_path=['modes', 'active_extension']),
                MenuItem("Run All Modes", "toggle",
                         self.get_config_value(['modes', 'all_modes_enabled']),
                         config_path=['modes', 'all_modes_enabled']),
                MenuItem("", "separator"),
                MenuItem("── Random Mode Change ──", "label"),
                MenuItem("Enable Random Mode Change", "toggle",
                         self.get_config_value(['modes', 'random_mode_change', 'enabled']),
                         config_path=['modes', 'random_mode_change', 'enabled']),
                MenuItem("Min Keypresses", "number",
                         self.get_config_value(['modes', 'random_mode_change', 'min_keypresses']),
                         config_path=['modes', 'random_mode_change', 'min_keypresses'],
                         min_val=1, max_val=1000),
                MenuItem("Max Keypresses", "number",
                         self.get_config_value(['modes', 'random_mode_change', 'max_keypresses']),
                         config_path=['modes', 'random_mode_change', 'max_keypresses'],
                         min_val=1, max_val=1000),
            ]

        elif self.current_menu == "background":
            return [
                MenuItem("← Back to Main Menu", "action", "back"),
                MenuItem("", "separator"),
                MenuItem("Background Image Path", "text",
                         self.get_config_value(['background', 'image_path']) or "(none)",
                         config_path=['background', 'image_path']),
                MenuItem("Images Directory", "text",
                         self.get_config_value(['background', 'images_directory']) or "(none)",
                         config_path=['background', 'images_directory']),
                MenuItem("", "separator"),
                MenuItem("── Random Background Change ──", "label"),
                MenuItem("Enable Random Background", "toggle",
                         self.get_config_value(['background', 'random_change', 'enabled']),
                         config_path=['background', 'random_change', 'enabled']),
                MenuItem("Min Keypresses", "number",
                         self.get_config_value(['background', 'random_change', 'min_keypresses']),
                         config_path=['background', 'random_change', 'min_keypresses'],
                         min_val=1, max_val=1000),
                MenuItem("Max Keypresses", "number",
                         self.get_config_value(['background', 'random_change', 'max_keypresses']),
                         config_path=['background', 'random_change', 'max_keypresses'],
                         min_val=1, max_val=1000),
            ]

        elif self.current_menu == "audio":
            return [
                MenuItem("← Back to Main Menu", "action", "back"),
                MenuItem("", "separator"),
                MenuItem("Master Volume", "number",
                         int(self.get_config_value(['audio', 'volume']) * 100),
                         config_path=['audio', 'volume'],
                         min_val=0, max_val=100),
                MenuItem("Prefer OGG Format", "toggle",
                         self.get_config_value(['audio', 'prefer_ogg']),
                         config_path=['audio', 'prefer_ogg']),
            ]

        elif self.current_menu == "themes":
            # Get available themes
            themes_config = self.get_config_value(['themes', 'definitions']) or {}
            theme_names = ["None"] + list(themes_config.keys())
            current_theme = self.get_config_value(['themes', 'active_theme']) or "None"
            
            return [
                MenuItem("← Back to Main Menu", "action", "back"),
                MenuItem("", "separator"),
                MenuItem("Active Theme", "select", current_theme,
                         options=theme_names,
                         config_path=['themes', 'active_theme']),
                MenuItem("", "separator"),
                MenuItem("── Available Themes ──", "label"),
                MenuItem("  rainbow: Cycling rainbow colors", "label"),
                MenuItem("  ocean: Blue and turquoise", "label"),
                MenuItem("  forest: Green forest theme", "label"),
                MenuItem("  sunset: Warm sunset colors", "label"),
                MenuItem("  space: Dark space with bright stars", "label"),
                MenuItem("  pastel: Soft pastel colors", "label"),
            ]
        
        elif self.current_menu == "patterns":
            return [
                MenuItem("← Back to Main Menu", "action", "back"),
                MenuItem("", "separator"),
                MenuItem("Enable Pattern Matching", "toggle",
                         self.get_config_value(['patterns', 'enabled']),
                         config_path=['patterns', 'enabled']),
                MenuItem("", "separator"),
                MenuItem("── Predefined Patterns ──", "label"),
                MenuItem("  abcd: Clear screen", "label"),
                MenuItem("  1234: Change theme", "label"),
                MenuItem("  rainbow: Toggle rainbow mode", "label"),
                MenuItem("", "separator"),
                MenuItem("Note: Pattern actions trigger when", "label"),
                MenuItem("you type the pattern during play", "label"),
            ]

        elif self.current_menu == "display":
            return [
                MenuItem("← Back to Main Menu", "action", "back"),
                MenuItem("", "separator"),
                MenuItem("Max Image Width (px)", "number",
                         self.get_config_value(['display', 'max_image_width']),
                         config_path=['display', 'max_image_width'],
                         min_val=100, max_val=2000),
                MenuItem("Target FPS", "number",
                         self.get_config_value(['display', 'target_fps']),
                         config_path=['display', 'target_fps'],
                         min_val=15, max_val=120),
            ]

        elif self.current_menu == "advanced":
            return [
                MenuItem("← Back to Main Menu", "action", "back"),
                MenuItem("", "separator"),
                MenuItem("Debug Logging", "toggle",
                         self.get_config_value(['advanced', 'trace']),
                         config_path=['advanced', 'trace']),
                MenuItem("Random Seed", "text",
                         str(self.get_config_value(['advanced', 'random_seed']) or "(random)"),
                         config_path=['advanced', 'random_seed']),
                MenuItem("", "separator"),
                MenuItem("── Cage Settings ──", "label"),
                MenuItem("Enable Cage Mode", "toggle",
                         self.get_config_value(['cage', 'enabled']),
                         config_path=['cage', 'enabled']),
                MenuItem("Use Swaylock", "toggle",
                         self.get_config_value(['cage', 'use_swaylock']),
                         config_path=['cage', 'use_swaylock']),
            ]

        return []

    def draw(self):
        """Draw the TUI interface."""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Draw header
        header = "╔══════════════════════════════════════════════════════╗"
        title = "║           🎮 BamBam Plus Configuration 🎮            ║"
        footer = "╚══════════════════════════════════════════════════════╝"

        header_width = len(header)
        start_x = (width - header_width) // 2

        self.stdscr.attron(curses.color_pair(COLOR_HEADER))
        self.stdscr.addstr(0, max(0, start_x), header[:width-1])
        self.stdscr.addstr(1, max(0, start_x), title[:width-1])
        self.stdscr.addstr(2, max(0, start_x), footer[:width-1])
        self.stdscr.attroff(curses.color_pair(COLOR_HEADER))

        # Draw menu items
        items = self.get_menu_items()
        menu_start_y = 4

        for i, item in enumerate(items):
            if menu_start_y + i >= height - 3:
                break

            y = menu_start_y + i

            if item.item_type == "separator":
                self.stdscr.addstr(y, 2, "─" * (width - 4))
                continue

            if item.item_type == "label":
                self.stdscr.attron(curses.color_pair(COLOR_HEADER))
                self.stdscr.addstr(y, 4, item.label[:width-6])
                self.stdscr.attroff(curses.color_pair(COLOR_HEADER))
                continue

            # Build display string
            display_str = f"  {item.label}"

            if item.item_type == "toggle":
                status = "✓ ON" if item.value else "✗ OFF"
                display_str += f": {status}"
            elif item.item_type == "select":
                display_str += f": {item.value}"
            elif item.item_type == "number":
                display_str += f": {item.value}"
            elif item.item_type == "text":
                display_str += f": {item.value}"

            # Highlight selected item
            if i == self.selected_index:
                self.stdscr.attron(curses.color_pair(COLOR_HIGHLIGHT))
                display_str = "▸" + display_str[1:]

            self.stdscr.addstr(y, 2, display_str[:width-4])

            if i == self.selected_index:
                self.stdscr.attroff(curses.color_pair(COLOR_HIGHLIGHT))

        # Draw status bar
        status_y = height - 2
        self.stdscr.addstr(status_y, 0, "─" * width)

        # Draw help text
        help_text = "↑↓:Navigate  ←→:Adjust  Enter:Select  Q:Quit"
        self.stdscr.addstr(status_y + 1, 2, help_text[:width-4])

        # Draw message if any
        if self.message:
            msg_color = COLOR_SUCCESS if self.message_type == "success" else \
                       COLOR_ERROR if self.message_type == "error" else \
                       COLOR_WARNING
            self.stdscr.attron(curses.color_pair(msg_color))
            msg_x = width - len(self.message) - 4
            self.stdscr.addstr(status_y + 1, max(0, msg_x), self.message[:width-4])
            self.stdscr.attroff(curses.color_pair(msg_color))

        self.stdscr.refresh()

    def handle_action(self, action: str):
        """Handle menu action."""
        if action == "exit":
            return False
        elif action == "back":
            if self.menu_stack:
                self.current_menu = self.menu_stack.pop()
                self.selected_index = 0
            else:
                self.current_menu = "main"
                self.selected_index = 0
        elif action == "save":
            if save_config(self.config):
                self.message = "Configuration saved!"
                self.message_type = "success"
            else:
                self.message = "Failed to save!"
                self.message_type = "error"
        elif action == "reload":
            self.config = load_config()
            self.message = "Configuration reloaded!"
            self.message_type = "success"
        elif action == "check_deps":
            deps = check_dependencies()
            missing = [k for k, v in deps.items() if not v]
            if missing:
                self.message = f"Missing: {', '.join(missing)}"
                self.message_type = "warning"
            else:
                self.message = "All dependencies OK!"
                self.message_type = "success"
        elif action == "start":
            curses.endwin()
            run_bambam(self.config, use_cage=False)
            return False
        elif action == "start_cage":
            curses.endwin()
            run_bambam(self.config, use_cage=True)
            return False
        return True

    def handle_input(self, key: int) -> bool:
        """Handle keyboard input. Returns False to exit."""
        items = self.get_menu_items()

        # Filter out non-selectable items
        selectable_indices = [i for i, item in enumerate(items)
                              if item.item_type not in ("separator", "label")]

        if key in (curses.KEY_UP, ord('k')):
            # Move up
            current_pos = selectable_indices.index(self.selected_index) \
                if self.selected_index in selectable_indices else 0
            if current_pos > 0:
                self.selected_index = selectable_indices[current_pos - 1]
            self.message = ""

        elif key in (curses.KEY_DOWN, ord('j')):
            # Move down
            current_pos = selectable_indices.index(self.selected_index) \
                if self.selected_index in selectable_indices else 0
            if current_pos < len(selectable_indices) - 1:
                self.selected_index = selectable_indices[current_pos + 1]
            self.message = ""

        elif key in (curses.KEY_LEFT, ord('h')):
            # Decrease value
            if self.selected_index < len(items):
                item = items[self.selected_index]
                if item.item_type == "number" and item.config_path:
                    new_val = max(item.min_val, item.value - 1)
                    if item.config_path == ['audio', 'volume']:
                        self.set_config_value(item.config_path, new_val / 100.0)
                    else:
                        self.set_config_value(item.config_path, new_val)
                elif item.item_type == "select" and item.options:
                    current_idx = item.options.index(item.value) if item.value in item.options else 0
                    new_idx = (current_idx - 1) % len(item.options)
                    new_val = item.options[new_idx]
                    if new_val == "None":
                        new_val = None
                    self.set_config_value(item.config_path, new_val)

        elif key in (curses.KEY_RIGHT, ord('l')):
            # Increase value
            if self.selected_index < len(items):
                item = items[self.selected_index]
                if item.item_type == "number" and item.config_path:
                    new_val = min(item.max_val, item.value + 1)
                    if item.config_path == ['audio', 'volume']:
                        self.set_config_value(item.config_path, new_val / 100.0)
                    else:
                        self.set_config_value(item.config_path, new_val)
                elif item.item_type == "select" and item.options:
                    current_idx = item.options.index(item.value) if item.value in item.options else 0
                    new_idx = (current_idx + 1) % len(item.options)
                    new_val = item.options[new_idx]
                    if new_val == "None":
                        new_val = None
                    self.set_config_value(item.config_path, new_val)

        elif key in (curses.KEY_ENTER, ord('\n'), ord(' ')):
            # Select/toggle
            if self.selected_index < len(items):
                item = items[self.selected_index]
                if item.item_type == "action":
                    return self.handle_action(item.value)
                elif item.item_type == "toggle" and item.config_path:
                    self.set_config_value(item.config_path, not item.value)
                elif item.item_type == "submenu":
                    self.menu_stack.append(self.current_menu)
                    self.current_menu = item.value
                    self.selected_index = 0

        elif key in (ord('q'), ord('Q')):
            return self.handle_action("exit")

        elif key == ord('s'):
            # Quick save
            self.handle_action("save")

        return True

    def run(self):
        """Main TUI loop."""
        running = True
        while running:
            self.draw()
            try:
                key = self.stdscr.getch()
                running = self.handle_input(key)
            except KeyboardInterrupt:
                running = False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BamBam Plus TUI - Configuration and Launcher")
    parser.add_argument('--run', action='store_true',
                        help='Run BamBam directly with current config')
    parser.add_argument('--cage', action='store_true',
                        help='Run BamBam in cage compositor')
    parser.add_argument('--check', action='store_true',
                        help='Check dependencies and exit')
    args = parser.parse_args()

    if args.check:
        deps = check_dependencies()
        print("Dependency Check:")
        for name, available in deps.items():
            status = "✓" if available else "✗"
            print(f"  {status} {name}")
        missing = [k for k, v in deps.items() if not v]
        if missing:
            print(f"\nMissing dependencies: {', '.join(missing)}")
            print("\nInstall with:")
            print("  sudo apt install python3-pygame python3-yaml cage swaylock")
            sys.exit(1)
        sys.exit(0)

    config = load_config()

    if args.run:
        sys.exit(run_bambam(config, use_cage=False))

    if args.cage:
        sys.exit(run_bambam(config, use_cage=True))

    # Run TUI
    try:
        curses.wrapper(lambda stdscr: TUI(stdscr).run())
    except Exception as e:
        print(f"TUI Error: {e}", file=sys.stderr)
        print("Falling back to command-line mode...")
        print("\nAvailable options:")
        print("  python3 bambam_tui.py --run   # Run BamBam directly")
        print("  python3 bambam_tui.py --cage  # Run in cage compositor")
        print("  python3 bambam_tui.py --check # Check dependencies")
        sys.exit(1)


if __name__ == "__main__":
    main()
