#!/usr/bin/env python3
# Copyright (C) 2026 BamBam Plus Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Configuration management for BamBam Plus.
Handles persistent settings storage and runtime configuration.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional, List

# Default config location following XDG spec
DEFAULT_CONFIG_DIR = os.path.expanduser(
    os.environ.get('XDG_CONFIG_HOME', '~/.config') + '/bambam'
)
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, 'config.json')


@dataclass
class ExtensionConfig:
    """Configuration for a single extension."""
    name: str
    enabled: bool = True
    # Audio + image pairing mode
    distinct_mode: bool = False
    # Custom sound directory within extension
    sounds_dir: str = "sounds"
    # Custom images directory within extension
    images_dir: str = "images"


@dataclass
class KeypressRangeConfig:
    """Configuration for keypress-triggered random changes."""
    # Enable random mode change after N keypresses
    mode_change_enabled: bool = False
    mode_change_min: int = 50
    mode_change_max: int = 150

    # Enable random background change after N keypresses
    background_change_enabled: bool = False
    background_change_min: int = 30
    background_change_max: int = 100


@dataclass
class BackgroundConfig:
    """Background image configuration."""
    # Use custom background image
    use_custom_background: bool = False
    # Path to custom background image
    custom_background_path: str = ""
    # List of background images for rotation
    background_images: List[str] = field(default_factory=list)
    # Cycle through backgrounds
    cycle_backgrounds: bool = False


@dataclass
class DisplayConfig:
    """Display-related configuration."""
    dark_mode: bool = False
    uppercase: bool = False
    fullscreen: bool = True


@dataclass
class AudioConfig:
    """Audio-related configuration."""
    start_muted: bool = False
    sound_enabled: bool = True
    deterministic_sounds: bool = False
    sound_blacklist: List[str] = field(default_factory=list)


@dataclass
class CageConfig:
    """Cage compositor integration configuration."""
    use_cage: bool = True
    cage_command: str = "cage"
    # Additional cage arguments
    cage_args: List[str] = field(default_factory=list)


@dataclass
class BambamConfig:
    """Main configuration container for BamBam Plus."""
    # Display settings
    display: DisplayConfig = field(default_factory=DisplayConfig)

    # Audio settings
    audio: AudioConfig = field(default_factory=AudioConfig)

    # Extension configuration
    current_extension: str = ""
    extensions: List[ExtensionConfig] = field(default_factory=list)

    # Run all modes at once
    all_modes_enabled: bool = False

    # Keypress range triggers
    keypress_triggers: KeypressRangeConfig = field(default_factory=KeypressRangeConfig)

    # Background settings
    background: BackgroundConfig = field(default_factory=BackgroundConfig)

    # Cage compositor settings
    cage: CageConfig = field(default_factory=CageConfig)

    # Sticky mouse setting
    sticky_mouse: bool = False

    # Image blacklist patterns
    image_blacklist: List[str] = field(default_factory=list)

    def to_bambam_args(self) -> List[str]:
        """Convert configuration to bambam.py command line arguments."""
        args = []

        if self.current_extension:
            args.extend(['-e', self.current_extension])

        if self.display.uppercase:
            args.append('-u')

        if self.display.dark_mode:
            args.append('-D')

        if self.audio.start_muted:
            args.append('-m')

        if self.audio.deterministic_sounds:
            args.append('-d')

        if self.sticky_mouse:
            args.append('--sticky-mouse')

        for pattern in self.audio.sound_blacklist:
            args.extend(['--sound_blacklist', pattern])

        for pattern in self.image_blacklist:
            args.extend(['--image_blacklist', pattern])

        return args


def load_config(config_path: Optional[str] = None) -> BambamConfig:
    """Load configuration from JSON file."""
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE

    if not os.path.exists(config_path):
        return BambamConfig()

    try:
        with open(config_path, 'r') as f:
            data = json.load(f)

        config = BambamConfig()

        # Load display settings
        if 'display' in data:
            config.display = DisplayConfig(**data['display'])

        # Load audio settings
        if 'audio' in data:
            config.audio = AudioConfig(**data['audio'])

        # Load extension settings
        config.current_extension = data.get('current_extension', '')
        if 'extensions' in data:
            config.extensions = [ExtensionConfig(**ext) for ext in data['extensions']]

        config.all_modes_enabled = data.get('all_modes_enabled', False)

        # Load keypress triggers
        if 'keypress_triggers' in data:
            config.keypress_triggers = KeypressRangeConfig(**data['keypress_triggers'])

        # Load background settings
        if 'background' in data:
            config.background = BackgroundConfig(**data['background'])

        # Load cage settings
        if 'cage' in data:
            config.cage = CageConfig(**data['cage'])

        config.sticky_mouse = data.get('sticky_mouse', False)
        config.image_blacklist = data.get('image_blacklist', [])

        return config

    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"Warning: Could not load config from {config_path}: {e}")
        return BambamConfig()


def save_config(config: BambamConfig, config_path: Optional[str] = None) -> bool:
    """Save configuration to JSON file."""
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE

    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # Convert dataclass to dict recursively
        data = _dataclass_to_dict(config)

        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

        return True

    except (OSError, IOError) as e:
        print(f"Error: Could not save config to {config_path}: {e}")
        return False


def _dataclass_to_dict(obj):
    """Recursively convert dataclass instances to dictionaries."""
    if hasattr(obj, '__dataclass_fields__'):
        return {k: _dataclass_to_dict(v) for k, v in asdict(obj).items()}
    elif isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    else:
        return obj


def discover_extensions(base_dirs: Optional[List[str]] = None) -> List[str]:
    """Discover available extensions in extension directories."""
    if base_dirs is None:
        # Default extension directories
        program_dir = os.path.dirname(os.path.abspath(__file__))
        base_dirs = [
            os.path.join(program_dir, 'extensions'),
            os.path.expanduser('~/.local/share/bambam/extensions'),
            '/usr/share/bambam/extensions',
        ]

    extensions = []
    seen = set()

    for base_dir in base_dirs:
        if not os.path.isdir(base_dir):
            continue

        for name in os.listdir(base_dir):
            ext_dir = os.path.join(base_dir, name)
            event_map = os.path.join(ext_dir, 'event_map.yaml')

            if os.path.isdir(ext_dir) and os.path.exists(event_map):
                if name not in seen:
                    extensions.append(name)
                    seen.add(name)

    return sorted(extensions)


def discover_backgrounds(base_dirs: Optional[List[str]] = None) -> List[str]:
    """Discover available background images."""
    if base_dirs is None:
        program_dir = os.path.dirname(os.path.abspath(__file__))
        base_dirs = [
            os.path.join(program_dir, 'backgrounds'),
            os.path.expanduser('~/.local/share/bambam/backgrounds'),
            '/usr/share/bambam/backgrounds',
        ]

    backgrounds = []
    image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')

    for base_dir in base_dirs:
        if not os.path.isdir(base_dir):
            continue

        for name in os.listdir(base_dir):
            if name.lower().endswith(image_exts):
                backgrounds.append(os.path.join(base_dir, name))

    return sorted(backgrounds)


if __name__ == '__main__':
    # Test configuration system
    print("Testing BamBam Config System")
    print("=" * 40)

    # Create default config
    config = BambamConfig()
    config.current_extension = "alphanumeric-en_US"
    config.display.dark_mode = True
    config.keypress_triggers.mode_change_enabled = True
    config.keypress_triggers.mode_change_min = 50
    config.keypress_triggers.mode_change_max = 100

    # Save config
    test_path = "/tmp/bambam_test_config.json"
    if save_config(config, test_path):
        print(f"Saved config to {test_path}")

        # Load config back
        loaded = load_config(test_path)
        print(f"Loaded extension: {loaded.current_extension}")
        print(f"Dark mode: {loaded.display.dark_mode}")
        print(f"Mode change range: {loaded.keypress_triggers.mode_change_min}-{loaded.keypress_triggers.mode_change_max}")

    # Discover extensions
    print("\nDiscovered extensions:")
    for ext in discover_extensions():
        print(f"  - {ext}")

    # Generate args
    print("\nGenerated bambam args:")
    print(" ".join(config.to_bambam_args()))
