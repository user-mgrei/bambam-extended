# BamBam Plus Architecture Documentation

> **Persistent Context Document** - Updated as codebase evolves
> Last updated: 2026-01-05

## Table of Contents
1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Core Architecture](#core-architecture)
4. [Class Hierarchy](#class-hierarchy)
5. [Extension System](#extension-system)
6. [Event Flow](#event-flow)
7. [Configuration](#configuration)
8. [TUI Launcher](#tui-launcher)
9. [Pi 5 Lite Deployment](#pi-5-lite-deployment)
10. [Development Guide](#development-guide)

---

## Overview

BamBam Plus is a keyboard mashing and doodling game designed for babies and toddlers. It displays bright colors, pictures, and sounds when keys are pressed or mouse is moved. The application locks keyboard/mouse focus to prevent children from accidentally exiting or causing system damage.

### Key Features
- Full-screen interactive display with pygame
- Keyboard/mouse/joystick input handling
- Sound playback with mute/unmute controls
- Extension system for customizable behaviors
- Dark/light mode support
- Deterministic or random sound modes
- Session-based execution for safety

### Target Platforms
- Desktop Linux (X11/Wayland with limitations)
- Raspberry Pi 5 Lite (via apt package manager)
- Cage Wayland compositor for kiosk mode

---

## File Structure

```
/workspace/
├── bambam.py              # Main application entry point (803 lines)
├── bambam_tui.py          # TUI launcher for cage/configuration (NEW)
├── bambam_config.py       # Configuration management system (NEW)
├── ARCHITECTURE.md        # This documentation file
├── EXTENSIONS.md          # Extension creation guide
├── README.md              # User-facing documentation
│
├── data/                  # Default media assets
│   ├── *.gif              # Image files (alien1, bear, chimp, dog, etc.)
│   └── *.wav              # Sound files (boom, hen2, horse1a, etc.)
│
├── extensions/            # Extension directories
│   └── alphanumeric-en_US/
│       ├── event_map.yaml # Extension configuration
│       └── sounds/        # Extension-specific sounds (a-z, 0-9.ogg)
│
├── test/                  # Test infrastructure
│   ├── golden/            # Golden file screenshots by Python version
│   └── find-freetype.sh   # Font detection utility
│
├── test_e2e.py            # End-to-end test script
├── test_e2e_test.py       # Unit tests for e2e module
├── run_e2e_test.sh        # E2E test runner with xvfb
│
├── po/                    # Translations (ar, ca, cs, de, es, fr, etc.)
├── *.pot                  # Translation templates
├── *.6                    # Man pages (bambam.6, localized versions)
│
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Development dependencies
├── Makefile               # Build automation for translations
├── setup.cfg              # Python package configuration
│
├── .github/workflows/     # CI/CD
│   └── python-app.yml     # GitHub Actions workflow
│
├── bambam.desktop         # Desktop entry file
├── bambam-session.desktop # Session entry for display managers
├── 50-dont-vt-switch.conf # X11 config to prevent VT switching
└── icon.gif               # Application icon
```

---

## Core Architecture

### Main Module: `bambam.py`

#### Entry Point
```python
def main():
    gettext.install('bambam')
    try:
        bambam = Bambam()
        bambam.run()
    except BambamException as e:
        print(e, file=sys.stderr)
        sys.exit(1)
```

#### Bambam Class (Main Application)

**Constants:**
- `IMAGE_MAX_WIDTH = 700` - Maximum image dimension before scaling
- `_HUE_SPACE = 360` - Color hue cycle range

**Key Attributes:**
- `data_dirs: List[str]` - Directories containing media files
- `extensions_dirs: List[str]` - Directories containing extensions
- `screen: pygame.Surface` - Main display surface
- `display_width/height: int` - Screen dimensions
- `sequence: str` - Buffer for command detection (quit, sound, mouse, etc.)
- `_sound_policies: Dict` - Sound selection policies
- `_image_policies: Dict` - Image selection policies
- `_event_count: int` - Counter for color cycling
- `_random: random.Random` - Seeded random generator (via BAMBAM_RANDOM_SEED env)
- `sound_muted: bool` - Current mute state
- `_sticky_mouse: bool` - Sticky mouse button mode

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `run()` | Main entry, sets up pygame, loads resources, runs event loop |
| `_load_resources(args)` | Loads images, sounds, policies based on CLI args |
| `_prepare_screen(args)` | Initializes display, background, caption |
| `_prepare_welcome_message(dedicated_session)` | Shows initial instructions |
| `process_keypress(event)` | Handles keyboard/joystick events |
| `_maybe_process_command(last_keypress)` | Detects typed commands |
| `_select_response(event)` | Chooses sound/image for event |
| `_display_image(img)` | Renders image at random position |
| `draw_dot()` | Draws circle at mouse position |
| `glob_data(suffixes)` | Searches for media files |
| `glob_extension(suffixes, extension_name)` | Searches extension media |
| `load_image(fullname)` | Static: loads and scales image |
| `load_sound(name)` | Static: loads sound file |
| `get_color()` | Returns time-varying HSV color |

---

## Class Hierarchy

### Exception Classes
```
Exception
└── BambamException
    └── ResourceLoadException(resource, message)
```

### Policy Classes (Strategy Pattern)
```
CollectionPolicyBase
├── DeterministicPolicy    # Sound based on key code modulo
├── RandomPolicy           # Random selection from collection
└── NamedFilePolicy        # Select by explicit filename

FontImagePolicy            # Renders typed characters as images
```

### Mapper Classes (Event Routing)
```
LegacySoundMapper          # Default: random or deterministic
LegacyImageMapper          # Default: font for alphanumeric, random otherwise
DeclarativeMapper          # YAML-driven event mapping for extensions
```

### Policy Selection Flow
```
Event → Mapper.map(event) → (policy_name, args)
                               ↓
                        policies[policy_name].select(event, *args)
                               ↓
                        Sound/Image to play/display
```

---

## Extension System

### Extension Structure
```
extensions/{extension-name}/
├── event_map.yaml         # Required: event mapping configuration
└── sounds/                # Optional: sound files (.wav, .ogg)
    ├── a.ogg
    ├── b.ogg
    └── ...
```

### event_map.yaml Schema
```yaml
apiVersion: 0              # Only version 0 supported

image:                     # Image event mapping (optional)
  - check:                 # Conditions (optional, [] = always match)
      - type: KEYDOWN      # Event type check
      - unicode:           # Unicode character checks
          isalpha: True    # Check isalpha()
          isdigit: True    # Check isdigit()
          value: "a"       # Exact character match
    policy: font           # Policy: font, random, named_file
    args: ["file.ogg"]     # Arguments for named_file policy

sound:                     # Sound event mapping (optional)
  - check: [...]
    policy: named_file
    args: ["sound.ogg"]
```

### Available Policies
| Policy | Type | Description |
|--------|------|-------------|
| `font` | Image | Renders key character as colored glyph |
| `random` | Both | Random selection from data/ directory |
| `deterministic` | Sound | Consistent sound per key code |
| `named_file` | Sound | Play specific file from extension |

### DeclarativeMapper._match_check() Logic
```python
# Supported checks:
- type: KEYDOWN           # event.type == pygame.KEYDOWN
- unicode.value: "x"      # event.unicode == "x"
- unicode.isalpha: True   # event.unicode.isalpha() == True
- unicode.isdigit: True   # event.unicode.isdigit() == True
```

---

## Event Flow

### Startup Sequence
```
1. main() → Bambam().run()
2. _add_base_dir() for program dir, /usr/share/bambam, ~/.local/share/bambam
3. argparse: --extension, --dark, --mute, --deterministic-sounds, etc.
4. pygame.init(), pygame.display.set_mode(FULLSCREEN)
5. _load_resources() → load sounds, images, create policies
6. _prepare_screen() → render background, command caption
7. pygame.event.set_grab(True), set_keyboard_grab(True)
8. _prepare_welcome_message() → show safety instructions
9. poll_for_any_key_press() → wait for user
10. Main event loop
```

### Main Event Loop
```
while True:
    clock.tick(60)
    for event in pygame.event.get():
        QUIT → sys.exit(0)
        KEYDOWN/JOYBUTTONDOWN → _bump_event_count(), process_keypress()
        MOUSEMOTION → if mouse_pressed: draw_dot()
        MOUSEBUTTONDOWN → draw_dot(), toggle mouse_pressed
        MOUSEBUTTONUP → if not sticky: mouse_pressed = False
```

### Command Detection
```
sequence += keypress.lower()
if "quit" in sequence → sys.exit(0)
if "mouse" in sequence → toggle _sticky_mouse
if "sound" in sequence → toggle sound_muted
if "mute" in sequence → sound_muted = True
if "unmute" in sequence → sound_muted = False
```

---

## Configuration

### Command Line Arguments
| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `-e, --extension` | str | None | Use specified extension |
| `-u, --uppercase` | flag | False | Show uppercase letters |
| `-d, --deterministic-sounds` | flag | False | Same sound per key |
| `-D, --dark` | flag | False | Dark background |
| `-m, --mute` | flag | False | Start muted |
| `--sticky-mouse` | flag | False | Toggle mouse drawing mode |
| `--sound_blacklist` | list | [] | Patterns to skip |
| `--image_blacklist` | list | [] | Patterns to skip |
| `--wayland-ok` | flag | False | Allow Wayland (unsafe) |
| `--in-dedicated-session` | flag | False | Internal: session mode |
| `--trace` | flag | False | Enable debug logging |

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `BAMBAM_RANDOM_SEED` | Seed for deterministic testing |
| `XDG_DATA_HOME` | User data directory base |
| `WAYLAND_DISPLAY` | Wayland detection |
| `XDG_SESSION_TYPE` | Session type detection |

### Future Configuration System (bambam_config.py)
```yaml
# ~/.config/bambam/config.yaml
display:
  dark_mode: false
  background_image: null     # Path to custom background
  
audio:
  start_muted: false
  deterministic: false
  
modes:
  active_extension: null     # Or "alphanumeric-en_US"
  all_modes_enabled: false   # Run all modes simultaneously
  
auto_switch:
  enabled: false
  mode_change_range: [10, 50]      # Keypresses for random mode change
  background_change_range: [20, 100]  # Keypresses for background change
```

---

## TUI Launcher

### bambam_tui.py (NEW)

A terminal user interface launcher for:
- Running BamBam in Cage Wayland compositor
- Configuration menu for all settings
- Mode selection (extensions)
- All-modes toggle
- Background image selection
- Auto-switch settings

### Cage Integration
```bash
# Launch in cage (kiosk mode)
cage -- python3 bambam.py [args]

# Or via TUI launcher
bambam_tui.py --run-in-cage
```

### TUI Menu Structure
```
╔═══════════════════════════════════════╗
║         BamBam Plus Launcher          ║
╠═══════════════════════════════════════╣
║  [1] Start Game                       ║
║  [2] Select Mode/Extension            ║
║  [3] Display Settings                 ║
║  [4] Audio Settings                   ║
║  [5] Auto-Switch Settings             ║
║  [6] Run in Cage (Kiosk Mode)         ║
║  [7] Run All Modes                    ║
║  [Q] Quit                             ║
╚═══════════════════════════════════════╝
```

---

## Pi 5 Lite Deployment

### Required Packages (apt)
```bash
# Core dependencies
sudo apt install python3 python3-pygame python3-yaml

# For cage/kiosk mode
sudo apt install cage

# For audio
sudo apt install pulseaudio alsa-utils

# Optional: for TUI
sudo apt install python3-pip
pip3 install textual  # If using rich TUI
```

### Optimizations for Pi 5
1. **Memory**: Use pygame's convert() for faster blitting
2. **Audio**: Pre-load sounds, use mixer channels efficiently
3. **Display**: Hardware-accelerated fullscreen via DRM/KMS
4. **Boot**: Auto-start via systemd service or /etc/xdg/autostart

### systemd Service Example
```ini
[Unit]
Description=BamBam Kids Game
After=graphical.target

[Service]
Type=simple
User=bambam
ExecStart=/usr/bin/cage -- /usr/games/bambam
Restart=on-failure

[Install]
WantedBy=graphical.target
```

---

## Development Guide

### Running Tests
```bash
# Unit tests
python -m unittest *_test.py

# Lint
flake8 . --show-source --statistics
autopep8 -d *.py

# E2E tests (requires xvfb, imagemagick, xdotool, sox)
./run_e2e_test.sh regular -- 
./run_e2e_test.sh dark --no-expect-light-mode -- --dark
```

### Adding New Extension
1. Create directory in `extensions/{name}/`
2. Add `event_map.yaml` with apiVersion: 0
3. Add sound files to `sounds/` subdirectory
4. Define image and sound mappings

### Adding New Policy
1. Inherit from `CollectionPolicyBase` or create new class
2. Implement `select(event, *args)` method
3. Register in `_load_resources()` with `_add_*_policy()`

### Code Style
- Python 3.9+ compatible
- PEP 8 compliant (enforced by flake8)
- Type hints encouraged
- Docstrings for public methods

---

## Changelog (New Additions)

### Fork Enhancements (Implemented)
- [x] TUI launcher with cage support (`bambam_tui.py`)
- [x] Configuration file system (`bambam_config.py`)
- [x] Background image customization (`--background-image`)
- [x] Auto-switch by keypress count (`--auto-switch`)
- [x] Pi 5 Lite deployment guide (`PI5_DEPLOYMENT.md`)
- [x] Comprehensive architecture documentation (`ARCHITECTURE.md`)

### New Files
| File | Purpose |
|------|---------|
| `bambam_tui.py` | TUI launcher with curses-based menu for configuration and cage execution |
| `bambam_config.py` | YAML-based configuration management with dataclasses |
| `PI5_DEPLOYMENT.md` | Raspberry Pi 5 Lite installation and deployment guide |
| `ARCHITECTURE.md` | This comprehensive codebase documentation |

### New CLI Arguments in bambam.py
| Argument | Description |
|----------|-------------|
| `--background-image PATH` | Use a custom background image |
| `--auto-switch` | Enable auto-switching of modes/backgrounds |

### Configuration System
Configuration is stored at `~/.config/bambam/config.yaml` and includes:
- Display settings (dark mode, background, uppercase)
- Audio settings (muted, deterministic)
- Mode settings (extension, all-modes)
- Auto-switch settings (enabled, ranges for mode/background changes)
- Launcher settings (cage, sticky mouse, wayland-ok)

---

## References

- [pygame Documentation](https://www.pygame.org/docs/)
- [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [Cage Compositor](https://github.com/cage-kiosk/cage)
- [Original BamBam](https://github.com/porridge/bambam)
