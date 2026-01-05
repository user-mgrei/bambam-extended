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
BamBam Plus Configuration Management

Handles persistent configuration for the BamBam Plus application.
Configuration is stored in YAML format at ~/.config/bambam/config.yaml
"""

import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Tuple

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def get_config_dir() -> str:
    """Get the configuration directory path."""
    xdg_config = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    return os.path.join(xdg_config, 'bambam')


def get_config_path() -> str:
    """Get the full path to the config file."""
    return os.path.join(get_config_dir(), 'config.yaml')


def get_extensions_dir() -> str:
    """Get the user extensions directory."""
    xdg_data = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    return os.path.join(xdg_data, 'bambam', 'extensions')


def get_backgrounds_dir() -> str:
    """Get the backgrounds directory."""
    xdg_data = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    return os.path.join(xdg_data, 'bambam', 'backgrounds')


@dataclass
class DisplayConfig:
    """Display-related configuration."""
    dark_mode: bool = False
    background_image: Optional[str] = None  # Path to custom background image
    uppercase: bool = False


@dataclass
class AudioConfig:
    """Audio-related configuration."""
    start_muted: bool = False
    deterministic_sounds: bool = False
    sound_blacklist: List[str] = field(default_factory=list)


@dataclass
class ModeConfig:
    """Mode/extension configuration."""
    active_extension: Optional[str] = None
    all_modes_enabled: bool = False  # Run all available modes
    image_blacklist: List[str] = field(default_factory=list)


@dataclass
class AutoSwitchConfig:
    """Auto-switch configuration for random mode/background changes."""
    enabled: bool = False
    # Range of keypresses before triggering random mode change
    mode_change_range: Tuple[int, int] = (10, 50)
    # Range of keypresses before triggering random background change
    background_change_range: Tuple[int, int] = (20, 100)


@dataclass
class LauncherConfig:
    """Launcher-specific configuration."""
    use_cage: bool = False  # Launch in cage compositor
    sticky_mouse: bool = False
    wayland_ok: bool = False
    trace_logging: bool = False


@dataclass
class BambamConfig:
    """Main configuration container."""
    display: DisplayConfig = field(default_factory=DisplayConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    mode: ModeConfig = field(default_factory=ModeConfig)
    auto_switch: AutoSwitchConfig = field(default_factory=AutoSwitchConfig)
    launcher: LauncherConfig = field(default_factory=LauncherConfig)

    def to_dict(self) -> dict:
        """Convert config to dictionary for YAML serialization."""
        return {
            'display': asdict(self.display),
            'audio': asdict(self.audio),
            'mode': asdict(self.mode),
            'auto_switch': {
                'enabled': self.auto_switch.enabled,
                'mode_change_range': list(self.auto_switch.mode_change_range),
                'background_change_range': list(self.auto_switch.background_change_range),
            },
            'launcher': asdict(self.launcher),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BambamConfig':
        """Create config from dictionary (loaded from YAML)."""
        config = cls()

        if 'display' in data:
            d = data['display']
            config.display = DisplayConfig(
                dark_mode=d.get('dark_mode', False),
                background_image=d.get('background_image'),
                uppercase=d.get('uppercase', False),
            )

        if 'audio' in data:
            a = data['audio']
            config.audio = AudioConfig(
                start_muted=a.get('start_muted', False),
                deterministic_sounds=a.get('deterministic_sounds', False),
                sound_blacklist=a.get('sound_blacklist', []),
            )

        if 'mode' in data:
            m = data['mode']
            config.mode = ModeConfig(
                active_extension=m.get('active_extension'),
                all_modes_enabled=m.get('all_modes_enabled', False),
                image_blacklist=m.get('image_blacklist', []),
            )

        if 'auto_switch' in data:
            s = data['auto_switch']
            mode_range = s.get('mode_change_range', [10, 50])
            bg_range = s.get('background_change_range', [20, 100])
            config.auto_switch = AutoSwitchConfig(
                enabled=s.get('enabled', False),
                mode_change_range=tuple(mode_range) if isinstance(mode_range, list) else mode_range,
                background_change_range=tuple(bg_range) if isinstance(bg_range, list) else bg_range,
            )

        if 'launcher' in data:
            l_data = data['launcher']
            config.launcher = LauncherConfig(
                use_cage=l_data.get('use_cage', False),
                sticky_mouse=l_data.get('sticky_mouse', False),
                wayland_ok=l_data.get('wayland_ok', False),
                trace_logging=l_data.get('trace_logging', False),
            )

        return config

    def to_cli_args(self) -> List[str]:
        """Convert config to command-line arguments for bambam.py."""
        args = []

        # Display settings
        if self.display.dark_mode:
            args.append('--dark')
        if self.display.uppercase:
            args.append('--uppercase')
        if self.display.background_image:
            args.extend(['--background-image', self.display.background_image])

        # Audio settings
        if self.audio.start_muted:
            args.append('--mute')
        if self.audio.deterministic_sounds:
            args.append('--deterministic-sounds')
        for pattern in self.audio.sound_blacklist:
            args.extend(['--sound_blacklist', pattern])

        # Mode settings
        if self.mode.active_extension:
            args.extend(['--extension', self.mode.active_extension])
        if self.mode.all_modes_enabled:
            args.append('--all-modes')
        for pattern in self.mode.image_blacklist:
            args.extend(['--image_blacklist', pattern])

        # Auto-switch settings
        if self.auto_switch.enabled:
            args.append('--auto-switch')

        # Launcher settings
        if self.launcher.sticky_mouse:
            args.append('--sticky-mouse')
        if self.launcher.wayland_ok:
            args.append('--wayland-ok')
        if self.launcher.trace_logging:
            args.append('--trace')

        return args


def load_config() -> BambamConfig:
    """Load configuration from file, creating defaults if needed."""
    if not _YAML_AVAILABLE:
        print("Warning: PyYAML not available, using default configuration.",
              file=sys.stderr)
        return BambamConfig()

    config_path = get_config_path()

    if not os.path.exists(config_path):
        # Create default config
        config = BambamConfig()
        save_config(config)
        return config

    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        return BambamConfig.from_dict(data)
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}",
              file=sys.stderr)
        return BambamConfig()


def save_config(config: BambamConfig) -> bool:
    """Save configuration to file."""
    if not _YAML_AVAILABLE:
        print("Warning: PyYAML not available, cannot save configuration.",
              file=sys.stderr)
        return False

    config_dir = get_config_dir()
    config_path = get_config_path()

    try:
        os.makedirs(config_dir, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print(f"Warning: Failed to save config to {config_path}: {e}",
              file=sys.stderr)
        return False


def list_available_extensions() -> List[str]:
    """List all available extensions from known directories."""
    extensions = []

    # Check standard extension directories
    program_base = os.path.dirname(os.path.realpath(__file__))
    dirs_to_check = [
        os.path.join(program_base, 'extensions'),
        os.path.join(os.path.dirname(program_base), 'share', 'bambam', 'extensions'),
        get_extensions_dir(),
        '/usr/share/bambam/extensions',
    ]

    for ext_dir in dirs_to_check:
        if os.path.isdir(ext_dir):
            for name in os.listdir(ext_dir):
                ext_path = os.path.join(ext_dir, name)
                event_map = os.path.join(ext_path, 'event_map.yaml')
                if os.path.isdir(ext_path) and os.path.exists(event_map):
                    if name not in extensions:
                        extensions.append(name)

    return sorted(extensions)


def list_background_images() -> List[str]:
    """List available background images."""
    images = []
    bg_dir = get_backgrounds_dir()

    if os.path.isdir(bg_dir):
        for name in os.listdir(bg_dir):
            path = os.path.join(bg_dir, name)
            if os.path.isfile(path):
                ext = os.path.splitext(name)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                    images.append(path)

    return sorted(images)


def ensure_directories():
    """Ensure all necessary directories exist."""
    dirs = [
        get_config_dir(),
        get_extensions_dir(),
        get_backgrounds_dir(),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


if __name__ == '__main__':
    # Test/demo the config system
    ensure_directories()
    config = load_config()
    print("Current configuration:")
    print(yaml.dump(config.to_dict(), default_flow_style=False) if _YAML_AVAILABLE else config.to_dict())
    print("\nAvailable extensions:", list_available_extensions())
    print("CLI args:", config.to_cli_args())
