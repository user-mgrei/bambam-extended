# TUI Implementation Guide for BamBam

## Overview

This guide provides specifications for implementing a TUI (Terminal User Interface) configuration menu for BamBam, optimized for Raspberry Pi 5 Lite running with the Cage Wayland compositor.

## Recommended TUI Libraries

### For Pi 5 Lite (apt installable):

| Library | apt Package | Use Case |
|---------|-------------|----------|
| **urwid** | `python3-urwid` | Full-featured TUI toolkit |
| **npyscreen** | via pip | ncurses-based forms |
| **dialog** | `dialog` | Simple menu dialogs |
| **whiptail** | `whiptail` | Simple menu dialogs (lighter) |

### Recommended: urwid
```bash
sudo apt install python3-urwid
```

```python
import urwid
# Full TUI toolkit with widgets
```

### Alternative: Pure Python with curses
```python
import curses
# Built-in to Python, no extra packages
```

## TUI Architecture

### File Structure
```
bambam/
├── bambam.py          # Main game (unchanged)
├── bambam_tui.py      # TUI launcher/config menu
├── config/
│   └── bambam.yaml    # User configuration
└── scripts/
    └── bambam-launcher  # Shell wrapper for cage
```

### Configuration Schema
```yaml
# ~/.config/bambam/config.yaml
version: 1

# Display settings
display:
  dark_mode: false
  uppercase: false

# Audio settings
audio:
  start_muted: false
  
# Extension settings
extension:
  name: null  # or "alphanumeric-en_US"
  
# Mode settings (for Agent 3 features)
modes:
  active: []  # List of active mode names
  all_modes: false  # Run all modes at once
  
# Background settings (for Agent 3 features)
background:
  image: null  # Path to background image
  change_interval: null  # Keypresses before random change
  
# Mode rotation (for Agent 3 features)
mode_rotation:
  enabled: false
  keypress_range: [10, 20]  # Min/max keypresses before mode change
```

## TUI Menu Structure

```
┌─────────────────────────────────────────┐
│           BamBam Configuration          │
├─────────────────────────────────────────┤
│  ► Start BamBam                         │
│    ─────────────────────────            │
│    Display Settings                     │
│    Audio Settings                       │
│    Extension Settings                   │
│    Mode Settings                        │
│    Background Settings                  │
│    ─────────────────────────            │
│    Save & Exit                          │
│    Exit Without Saving                  │
└─────────────────────────────────────────┘
```

## Implementation Example (urwid)

```python
#!/usr/bin/env python3
"""BamBam TUI Configuration Menu"""

import os
import subprocess
import sys
from pathlib import Path

try:
    import urwid
except ImportError:
    print("Error: urwid not installed. Run: sudo apt install python3-urwid")
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None


class BambamTUI:
    """TUI configuration menu for BamBam."""
    
    CONFIG_DIR = Path.home() / '.config' / 'bambam'
    CONFIG_FILE = CONFIG_DIR / 'config.yaml'
    
    DEFAULT_CONFIG = {
        'version': 1,
        'display': {'dark_mode': False, 'uppercase': False},
        'audio': {'start_muted': False},
        'extension': {'name': None},
    }
    
    def __init__(self):
        self.config = self.load_config()
        self.palette = [
            ('reversed', 'standout', ''),
            ('header', 'white', 'dark blue'),
            ('footer', 'white', 'dark gray'),
            ('button', 'white', 'dark green'),
            ('button_focus', 'white', 'dark red'),
        ]
        
    def load_config(self) -> dict:
        """Load configuration from file or return defaults."""
        if yaml and self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE) as f:
                return yaml.safe_load(f) or self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save configuration to file."""
        if yaml:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False)
    
    def build_menu(self):
        """Build the main menu widget."""
        menu_items = [
            urwid.Button('Start BamBam', on_press=self.start_bambam),
            urwid.Divider(),
            urwid.Button('Display Settings', on_press=self.display_settings),
            urwid.Button('Audio Settings', on_press=self.audio_settings),
            urwid.Button('Extension Settings', on_press=self.extension_settings),
            urwid.Divider(),
            urwid.Button('Save & Exit', on_press=self.save_and_exit),
            urwid.Button('Exit', on_press=self.exit_app),
        ]
        
        body = urwid.ListBox(urwid.SimpleFocusListWalker(menu_items))
        header = urwid.AttrMap(urwid.Text('BamBam Configuration', align='center'), 'header')
        footer = urwid.AttrMap(urwid.Text('Arrow keys to navigate, Enter to select'), 'footer')
        
        return urwid.Frame(body, header=header, footer=footer)
    
    def start_bambam(self, button):
        """Start BamBam with current configuration."""
        raise urwid.ExitMainLoop()
    
    def display_settings(self, button):
        """Show display settings submenu."""
        # Implementation here
        pass
    
    def audio_settings(self, button):
        """Show audio settings submenu."""
        # Implementation here
        pass
    
    def extension_settings(self, button):
        """Show extension settings submenu."""
        # Implementation here
        pass
    
    def save_and_exit(self, button):
        """Save configuration and exit."""
        self.save_config()
        raise urwid.ExitMainLoop()
    
    def exit_app(self, button):
        """Exit without saving."""
        raise urwid.ExitMainLoop()
    
    def run(self):
        """Run the TUI."""
        main_widget = self.build_menu()
        loop = urwid.MainLoop(main_widget, palette=self.palette)
        loop.run()
        
    def build_bambam_args(self) -> list:
        """Build command line arguments from config."""
        args = []
        if self.config.get('display', {}).get('dark_mode'):
            args.append('--dark')
        if self.config.get('display', {}).get('uppercase'):
            args.append('--uppercase')
        if self.config.get('audio', {}).get('start_muted'):
            args.append('--mute')
        ext = self.config.get('extension', {}).get('name')
        if ext:
            args.extend(['--extension', ext])
        return args


def main():
    tui = BambamTUI()
    tui.run()
    
    # After TUI exits, start BamBam
    bambam_path = Path(__file__).parent / 'bambam.py'
    args = tui.build_bambam_args()
    
    # Run with cage if available
    if os.environ.get('WAYLAND_DISPLAY') is None:
        # Not in Wayland, try cage
        try:
            subprocess.run(['cage', str(bambam_path)] + args)
        except FileNotFoundError:
            # Cage not available, run directly
            subprocess.run([sys.executable, str(bambam_path)] + args)
    else:
        # Already in Wayland, run directly
        subprocess.run([sys.executable, str(bambam_path)] + args)


if __name__ == '__main__':
    main()
```

## Cage Integration

### Launcher Script (`bambam-launcher`)
```bash
#!/bin/bash
# BamBam Cage Launcher
# Place in /usr/local/bin/bambam-launcher

BAMBAM_DIR="${BAMBAM_DIR:-/opt/bambam}"
CONFIG_FILE="${HOME}/.config/bambam/config.yaml"

# Check if we need TUI
if [[ "$1" == "--config" ]] || [[ ! -f "$CONFIG_FILE" ]]; then
    # Run TUI for configuration
    python3 "${BAMBAM_DIR}/bambam_tui.py"
fi

# Run BamBam in cage
exec cage "${BAMBAM_DIR}/bambam.py" "$@"
```

### Systemd Service for Auto-start
```ini
# /etc/systemd/system/bambam.service
[Unit]
Description=BamBam Keyboard Game
After=multi-user.target

[Service]
Type=simple
User=pi
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStart=/usr/local/bin/bambam-launcher
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Pi 5 Lite Specific Considerations

### Dependencies (must be apt-installable)
```bash
# Core TUI dependencies
sudo apt install python3-urwid  # or python3-npyscreen

# Cage compositor (required for kiosk mode)
sudo apt install cage

# Optional: for config file support
sudo apt install python3-yaml
```

### Input Handling in Cage
- Cage captures all input by default
- Use `--keyboard-shortcuts` flag if needed
- VT switching still possible with Ctrl+Alt+Fx

### Display Detection
```python
def is_wayland():
    """Check if running under Wayland."""
    return bool(os.environ.get('WAYLAND_DISPLAY'))

def is_cage():
    """Check if running under Cage."""
    return os.environ.get('XDG_CURRENT_DESKTOP') == 'cage'
```

## Testing the TUI

### Manual Testing
```bash
# Test TUI directly
python3 bambam_tui.py

# Test with cage
cage python3 bambam_tui.py
```

### Automated Testing
```python
# TUI testing with pexpect
import pexpect

def test_tui_navigation():
    child = pexpect.spawn('python3 bambam_tui.py')
    child.expect('BamBam Configuration')
    child.send('\x1b[B')  # Down arrow
    child.send('\r')       # Enter
    # ... more assertions
```

## Validation Checklist

Before merging TUI implementation:

- [ ] Python syntax valid (`python3 -m py_compile bambam_tui.py`)
- [ ] Flake8 passes (`flake8 bambam_tui.py`)
- [ ] urwid is optional (graceful fallback or error message)
- [ ] Works without PyYAML (config storage optional)
- [ ] Works in cage (`cage python3 bambam_tui.py`)
- [ ] Works in terminal (`python3 bambam_tui.py`)
- [ ] Config file saved to correct location
- [ ] All Pi 5 apt packages available
- [ ] No pip-only dependencies required
