#!/usr/bin/env python3
"""
BamBam Multi-Sensory Themes System

Provides themed experiences (farm, ocean, space, etc.) with cohesive
audio/visual combinations and random mode swapping capabilities.
"""

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


@dataclass
class Theme:
    """Represents a multi-sensory theme."""
    name: str
    display_name: str
    description: str
    background_color: tuple = (250, 250, 250)  # RGB
    background_image: Optional[str] = None
    color_palette: list = field(default_factory=list)
    extensions: list = field(default_factory=list)  # Compatible extensions
    enabled: bool = True


# Built-in themes
BUILTIN_THEMES = {
    'default': Theme(
        name='default',
        display_name='Default',
        description='Classic BamBam experience',
        background_color=(250, 250, 250),
        color_palette=[
            (0, 0, 255), (255, 0, 0), (255, 255, 0),
            (255, 0, 128), (0, 0, 128), (0, 255, 0),
            (255, 128, 0), (255, 0, 255), (0, 255, 255)
        ],
    ),
    'dark': Theme(
        name='dark',
        display_name='Dark Mode',
        description='Easy on the eyes, dark background',
        background_color=(0, 0, 0),
        color_palette=[
            (100, 100, 255), (255, 100, 100), (255, 255, 100),
            (255, 100, 200), (100, 100, 200), (100, 255, 100),
            (255, 180, 100), (255, 100, 255), (100, 255, 255)
        ],
    ),
    'farm': Theme(
        name='farm',
        display_name='Farm Friends',
        description='Barn animals and farm sounds',
        background_color=(200, 230, 200),  # Light green
        color_palette=[
            (139, 69, 19), (34, 139, 34), (255, 215, 0),  # Brown, green, gold
            (255, 99, 71), (255, 182, 193), (144, 238, 144),
        ],
        extensions=['animals', 'farm'],
    ),
    'ocean': Theme(
        name='ocean',
        display_name='Ocean Adventure',
        description='Sea creatures and wave sounds',
        background_color=(200, 220, 255),  # Light blue
        color_palette=[
            (0, 105, 148), (64, 224, 208), (0, 191, 255),  # Ocean blues
            (255, 127, 80), (255, 218, 185), (147, 112, 219),
        ],
        extensions=['ocean', 'sea-animals'],
    ),
    'space': Theme(
        name='space',
        display_name='Space Explorer',
        description='Planets, rockets, and cosmic sounds',
        background_color=(10, 10, 30),  # Deep space
        color_palette=[
            (255, 255, 255), (255, 215, 0), (192, 192, 192),  # Stars
            (255, 100, 100), (100, 200, 255), (200, 100, 255),
        ],
        extensions=['space', 'sci-fi'],
    ),
    'music': Theme(
        name='music',
        display_name='Music Class',
        description='Musical instruments and notes',
        background_color=(255, 250, 240),  # Warm white
        color_palette=[
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211),
        ],
        extensions=['instruments', 'music'],
    ),
    'nature': Theme(
        name='nature',
        display_name='Nature Walk',
        description='Birds, insects, and outdoor sounds',
        background_color=(230, 245, 220),  # Soft green
        color_palette=[
            (34, 139, 34), (107, 142, 35), (85, 107, 47),
            (255, 228, 181), (210, 180, 140), (139, 90, 43),
        ],
        extensions=['nature', 'animals'],
    ),
}


class ThemeManager:
    """Manages themes and mode swapping."""

    def __init__(self, themes_dir: Optional[Path] = None, random_gen=None):
        self.themes_dir = themes_dir
        self._random = random_gen or random.Random()
        self._themes = dict(BUILTIN_THEMES)
        self._current_theme: Optional[Theme] = None
        self._mode_swap_counter = 0
        self._mode_swap_threshold = None
        self._mode_swap_range = None

        if themes_dir:
            self._load_custom_themes()

    def _load_custom_themes(self):
        """Load custom themes from themes directory."""
        if not self.themes_dir or not self.themes_dir.exists():
            return

        if not _YAML_AVAILABLE:
            return

        for theme_file in self.themes_dir.glob('*.yaml'):
            try:
                with open(theme_file) as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        name = data.get('name', theme_file.stem)
                        theme = Theme(
                            name=name,
                            display_name=data.get('display_name', name.title()),
                            description=data.get('description', ''),
                            background_color=tuple(data.get('background_color', [250, 250, 250])),
                            background_image=data.get('background_image'),
                            color_palette=[tuple(c) for c in data.get('color_palette', [])],
                            extensions=data.get('extensions', []),
                            enabled=data.get('enabled', True),
                        )
                        self._themes[name] = theme
            except (yaml.YAMLError, IOError):
                pass

    def list_themes(self) -> list[str]:
        """List all available theme names."""
        return [name for name, theme in self._themes.items() if theme.enabled]

    def get_theme(self, name: str) -> Optional[Theme]:
        """Get a theme by name."""
        return self._themes.get(name)

    def set_current_theme(self, name: str) -> bool:
        """Set the current active theme."""
        if name in self._themes:
            self._current_theme = self._themes[name]
            return True
        return False

    def get_current_theme(self) -> Optional[Theme]:
        """Get the current active theme."""
        return self._current_theme

    def get_random_theme(self, exclude_current: bool = True) -> Theme:
        """Get a random theme, optionally excluding the current one."""
        available = [
            theme for name, theme in self._themes.items()
            if theme.enabled and (not exclude_current or theme != self._current_theme)
        ]
        if not available:
            available = list(self._themes.values())
        return self._random.choice(available)

    def enable_mode_swap(self, min_keypresses: int, max_keypresses: int):
        """Enable automatic mode/theme swapping after N keypresses."""
        self._mode_swap_range = (min_keypresses, max_keypresses)
        self._reset_swap_threshold()

    def disable_mode_swap(self):
        """Disable automatic mode swapping."""
        self._mode_swap_range = None
        self._mode_swap_threshold = None

    def _reset_swap_threshold(self):
        """Reset the swap threshold to a new random value."""
        if self._mode_swap_range:
            self._mode_swap_threshold = self._random.randint(*self._mode_swap_range)
            self._mode_swap_counter = 0

    def on_keypress(self) -> Optional[Theme]:
        """
        Call on each keypress. Returns a new Theme if swap triggered, else None.
        """
        if self._mode_swap_threshold is None:
            return None

        self._mode_swap_counter += 1
        if self._mode_swap_counter >= self._mode_swap_threshold:
            new_theme = self.get_random_theme(exclude_current=True)
            self._current_theme = new_theme
            self._reset_swap_threshold()
            return new_theme
        return None


class MultiModeManager:
    """Manages running multiple extensions/modes simultaneously with random swapping."""

    def __init__(self, extensions_dirs: list[Path], random_gen=None):
        self.extensions_dirs = extensions_dirs
        self._random = random_gen or random.Random()
        self._available_extensions: list[str] = []
        self._active_extensions: list[str] = []
        self._current_extension_index = 0
        self._swap_counter = 0
        self._swap_range = None
        self._swap_threshold = None
        self._all_modes_enabled = False

        self._discover_extensions()

    def _discover_extensions(self):
        """Discover all available extensions."""
        self._available_extensions = []
        for ext_dir in self.extensions_dirs:
            if ext_dir.exists():
                for subdir in ext_dir.iterdir():
                    if subdir.is_dir():
                        event_map = subdir / 'event_map.yaml'
                        if event_map.exists():
                            self._available_extensions.append(subdir.name)

    def list_extensions(self) -> list[str]:
        """List all available extensions."""
        return self._available_extensions.copy()

    def enable_all_modes(self):
        """Enable all modes to run with random selection."""
        self._all_modes_enabled = True
        self._active_extensions = self._available_extensions.copy()

    def disable_all_modes(self):
        """Disable all-modes, use single extension."""
        self._all_modes_enabled = False
        self._active_extensions = []

    def set_active_extensions(self, extensions: list[str]):
        """Set specific extensions to be active."""
        self._active_extensions = [
            ext for ext in extensions if ext in self._available_extensions
        ]

    def enable_extension_swap(self, min_keypresses: int, max_keypresses: int):
        """Enable automatic extension swapping."""
        self._swap_range = (min_keypresses, max_keypresses)
        self._reset_swap_threshold()

    def disable_extension_swap(self):
        """Disable automatic extension swapping."""
        self._swap_range = None
        self._swap_threshold = None

    def _reset_swap_threshold(self):
        """Reset the swap threshold."""
        if self._swap_range:
            self._swap_threshold = self._random.randint(*self._swap_range)
            self._swap_counter = 0

    def get_current_extension(self) -> Optional[str]:
        """Get the current active extension."""
        if not self._active_extensions:
            return None
        return self._active_extensions[self._current_extension_index % len(self._active_extensions)]

    def on_keypress(self) -> Optional[str]:
        """
        Call on each keypress. Returns new extension name if swap triggered.
        """
        if not self._active_extensions or self._swap_threshold is None:
            return None

        self._swap_counter += 1
        if self._swap_counter >= self._swap_threshold:
            # Pick a random different extension
            if len(self._active_extensions) > 1:
                current = self.get_current_extension()
                others = [e for e in self._active_extensions if e != current]
                new_ext = self._random.choice(others)
                self._current_extension_index = self._active_extensions.index(new_ext)
            self._reset_swap_threshold()
            return self.get_current_extension()
        return None

    def get_random_extension(self) -> Optional[str]:
        """Get a random extension from active set."""
        if not self._active_extensions:
            return None
        return self._random.choice(self._active_extensions)


class BackgroundManager:
    """Manages background images with random swapping."""

    def __init__(self, backgrounds_dir: Optional[Path] = None, random_gen=None):
        self.backgrounds_dir = backgrounds_dir
        self._random = random_gen or random.Random()
        self._available_backgrounds: list[Path] = []
        self._current_background: Optional[Path] = None
        self._swap_counter = 0
        self._swap_range = None
        self._swap_threshold = None

        self._discover_backgrounds()

    def _discover_backgrounds(self):
        """Discover available background images."""
        self._available_backgrounds = []
        if self.backgrounds_dir and self.backgrounds_dir.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']:
                self._available_backgrounds.extend(self.backgrounds_dir.glob(ext))

    def list_backgrounds(self) -> list[str]:
        """List available background image names."""
        return [bg.name for bg in self._available_backgrounds]

    def set_current_background(self, name: str) -> bool:
        """Set current background by filename."""
        for bg in self._available_backgrounds:
            if bg.name == name:
                self._current_background = bg
                return True
        return False

    def get_current_background(self) -> Optional[Path]:
        """Get current background image path."""
        return self._current_background

    def enable_background_swap(self, min_keypresses: int, max_keypresses: int):
        """Enable automatic background swapping."""
        self._swap_range = (min_keypresses, max_keypresses)
        self._reset_swap_threshold()

    def disable_background_swap(self):
        """Disable automatic background swapping."""
        self._swap_range = None
        self._swap_threshold = None

    def _reset_swap_threshold(self):
        """Reset the swap threshold."""
        if self._swap_range:
            self._swap_threshold = self._random.randint(*self._swap_range)
            self._swap_counter = 0

    def on_keypress(self) -> Optional[Path]:
        """
        Call on each keypress. Returns new background path if swap triggered.
        """
        if not self._available_backgrounds or self._swap_threshold is None:
            return None

        self._swap_counter += 1
        if self._swap_counter >= self._swap_threshold:
            # Pick a random different background
            if len(self._available_backgrounds) > 1:
                others = [bg for bg in self._available_backgrounds if bg != self._current_background]
                self._current_background = self._random.choice(others)
            elif self._available_backgrounds:
                self._current_background = self._available_backgrounds[0]
            self._reset_swap_threshold()
            return self._current_background
        return None

    def get_random_background(self) -> Optional[Path]:
        """Get a random background image."""
        if not self._available_backgrounds:
            return None
        return self._random.choice(self._available_backgrounds)


if __name__ == '__main__':
    # Demo
    print("Available built-in themes:")
    tm = ThemeManager()
    for name in tm.list_themes():
        theme = tm.get_theme(name)
        print(f"  - {theme.display_name}: {theme.description}")
