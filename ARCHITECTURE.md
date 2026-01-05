# BamBam Plus Architecture Documentation

This document provides comprehensive documentation of the BamBam Plus codebase for persistent context across development sessions and multi-agent collaboration.

## Table of Contents

1. [Overview](#overview)
2. [Core Components](#core-components)
3. [Class Hierarchy](#class-hierarchy)
4. [Configuration System](#configuration-system)
5. [Extension System](#extension-system)
6. [TUI Launcher System](#tui-launcher-system)
7. [Event Flow](#event-flow)
8. [File Structure](#file-structure)
9. [Dependencies](#dependencies)
10. [Raspberry Pi 5 Deployment](#raspberry-pi-5-deployment)

---

## Overview

BamBam Plus is a keyboard/mouse mashing game for babies and toddlers. It displays colorful images and plays sounds in response to keyboard, mouse, and gamepad input. The application locks input devices to prevent children from accidentally causing system damage.

### Fork Goals (Phases)

1. **Stage 1**: Simple extensions (animal sounds, instruments, drums, vehicles, silly sounds)
2. **Stage 2**: Terminal keybind with cage compositor + swaylock protection
3. **Stage 3**: Educational extensions with word-sight-sound associations

---

## Core Components

### Main Application (`bambam.py`)

The entry point is `main()` which:
1. Initializes gettext for internationalization
2. Creates a `Bambam` instance
3. Calls `bambam.run()`

### Bambam Class

The main application class containing:

#### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `data_dirs` | list | Directories containing default data (images/sounds) |
| `extensions_dirs` | list | Directories containing extensions |
| `screen` | pygame.Surface | Main display surface |
| `display_width` | int | Screen width in pixels |
| `display_height` | int | Screen height in pixels |
| `sequence` | str | Buffer for tracking typed command sequences |
| `_sound_policies` | dict | Sound selection policies |
| `_image_policies` | dict | Image selection policies |
| `_event_count` | int | Counter for color cycling (0 to 719) |
| `sound_muted` | bool | Whether sound is muted |
| `_sticky_mouse` | bool | Whether mouse buttons stay pressed |
| `_sound_enabled` | bool | Whether sound system is available |
| `background` | pygame.Surface | Background surface |
| `background_color` | tuple | RGB tuple for background |

#### Key Methods

| Method | Description |
|--------|-------------|
| `run()` | Main entry point, sets up directories, parses args, runs main loop |
| `load_image(fullname)` | Static method to load and scale images |
| `load_sound(name)` | Static method to load sound files |
| `load_items(lst, blacklist, load_function, failure_message)` | Generic resource loader |
| `get_color()` | Returns HSV-cycling color based on event count |
| `draw_dot()` | Draws colored circle at mouse position |
| `process_keypress(event)` | Main event handler for keyboard/joystick |
| `_maybe_process_command(last_keypress)` | Checks for command sequences (quit, mute, etc) |
| `_select_response(event)` | Returns (sound, image) tuple for event |
| `_display_image(img)` | Blits image at random screen position |
| `glob_data(suffixes)` | Finds files in data directories |
| `glob_extension(suffixes, extension_name)` | Finds files in extension directories |
| `_prepare_screen(args)` | Sets up display with background and caption |
| `_prepare_welcome_message(dedicated_session)` | Shows startup information screen |
| `_load_resources(args)` | Loads all images and sounds |
| `_get_extension_mappers(extension_name)` | Parses extension YAML and returns mappers |

#### Command Strings (Translatable)

| Command | Default | Description |
|---------|---------|-------------|
| `QUIT_STRING` | "quit" | Exits the application |
| `SOUND_TOGGLE_STRING` | "sound" | Toggles sound on/off |
| `MOUSE_TOGGLE_STRING` | "mouse" | Toggles sticky mouse |
| `MUTE_STRING` | "mute" | Mutes sound |
| `UNMUTE_STRING` | "unmute" | Unmutes sound |

---

## Class Hierarchy

### Exception Classes

```
BambamException (base)
└── ResourceLoadException (file loading failures)
```

### Policy Classes (Selection Strategies)

```
CollectionPolicyBase (abstract base)
├── DeterministicPolicy - selects based on event.key modulo count
├── NamedFilePolicy - selects by exact filename match
└── RandomPolicy - random selection from collection

FontImagePolicy (standalone) - renders characters as images
```

#### Policy Interface

All policies implement:
```python
def select(self, event, *args) -> resource
```

### Mapper Classes (Event to Policy Routing)

```
LegacySoundMapper - default sound mapping
LegacyImageMapper - default image mapping (font for alphanumeric, random otherwise)
DeclarativeMapper - YAML-configured mapping for extensions
```

#### Mapper Interface

All mappers implement:
```python
def map(self, event) -> tuple[str, list|None]
# Returns (policy_name, optional_args)
```

---

## Configuration System

### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `-e, --extension` | str | None | Extension name to use |
| `-u, --uppercase` | flag | False | Show uppercase letters |
| `--sound_blacklist` | list | [] | Patterns for sounds to skip |
| `--image_blacklist` | list | [] | Patterns for images to skip |
| `-d, --deterministic-sounds` | flag | False | Same key = same sound |
| `-D, --dark` | flag | False | Dark background |
| `-m, --mute` | flag | False | Start muted |
| `--sticky-mouse` | flag | False | Sticky mouse buttons |
| `--wayland-ok` | flag | False | Allow Wayland (unsafe) |
| `--in-dedicated-session` | flag | False | Running in bambam session |
| `--trace` | flag | False | Debug logging |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `BAMBAM_RANDOM_SEED` | Seed for reproducible randomness |
| `XDG_DATA_HOME` | Override for user data location |
| `WAYLAND_DISPLAY` | Detected to warn about Wayland |
| `XDG_SESSION_TYPE` | Alternative Wayland detection |

---

## Extension System

### Directory Structure

```
extensions/
└── extension-name/
    ├── event_map.yaml    (required)
    └── sounds/           (optional)
        ├── file1.ogg
        └── file2.wav
```

### Event Map YAML Schema (apiVersion: 0)

```yaml
apiVersion: 0  # Required, only "0" supported

image:  # Optional image mapping rules
  - check:  # Optional list of conditions
      - type: KEYDOWN
      - unicode:
          isalpha: True  # or isdigit, or value: "x"
    policy: font  # or "random", "named_file"
    args: ["optional.png"]  # Optional arguments

sound:  # Optional sound mapping rules
  - check:
      - unicode:
          value: "a"
    policy: named_file
    args: ["a.ogg"]
  - policy: random  # Fallback (no check = always matches)
```

### Available Policies

| Policy | Scope | Description | Args |
|--------|-------|-------------|------|
| `font` | image | Render character glyph | None |
| `random` | both | Random from data directory | None |
| `deterministic` | sound | Key-based selection | None |
| `named_file` | sound | Specific file from extension | [filename] |

### Check Types

| Check | Subcheck | Description |
|-------|----------|-------------|
| `type` | - | Event type (only "KEYDOWN") |
| `unicode` | `value` | Exact character match |
| `unicode` | `isalpha` | True/False for alphabetic |
| `unicode` | `isdigit` | True/False for numeric |

---

## TUI Launcher System

### Overview (NEW)

The TUI launcher (`bambam_tui.py`) provides:
- Interactive configuration menu
- Cage compositor integration for secure execution
- Mode selection and combination
- Background image management
- Random mode/background switching settings

### Components

```
bambam_tui.py          - Main TUI application
bambam_config.yaml     - User configuration file
bambam_launcher.sh     - Shell wrapper for cage execution
```

### Configuration File Schema

```yaml
# bambam_config.yaml
general:
  dark_mode: false
  uppercase: false
  mute: false
  sticky_mouse: false
  deterministic_sounds: false

modes:
  enabled: []  # List of enabled extensions
  all_modes: false  # Run all modes simultaneously
  random_mode_change:
    enabled: false
    min_keypresses: 10
    max_keypresses: 50

background:
  image_path: null  # Custom background image
  random_change:
    enabled: false
    min_keypresses: 20
    max_keypresses: 100
  images_directory: null  # Directory for random backgrounds

cage:
  enabled: true
  use_swaylock: true
```

---

## Event Flow

### Startup Sequence

```
main()
├── gettext.install('bambam')
├── Bambam()
│   ├── Initialize random generator
│   └── Initialize empty collections
└── bambam.run()
    ├── _add_base_dir() for each search path
    ├── argparse.parse_args()
    ├── pygame.init()
    ├── pygame.display.set_mode(FULLSCREEN)
    ├── _load_resources(args)
    │   ├── _try_init_sound()
    │   ├── load sounds from data dirs
    │   ├── load images from data dirs
    │   ├── If extension:
    │   │   ├── load extension sounds
    │   │   └── _get_extension_mappers()
    │   └── Else: use legacy mappers
    ├── _prepare_screen(args)
    ├── pygame.event.set_grab(True)
    ├── _prepare_welcome_message()
    ├── poll_for_any_key_press()
    └── Main event loop
```

### Event Processing

```
Event received
├── QUIT → sys.exit(0)
├── KEYDOWN / JOYBUTTONDOWN
│   ├── _bump_event_count()
│   └── process_keypress(event)
│       ├── _maybe_process_command() [if alpha key]
│       ├── 10% chance: clear screen
│       ├── _select_response(event)
│       │   ├── _map_and_select(sound_mapper, sound_policies)
│       │   └── _map_and_select(image_mapper, image_policies)
│       ├── sound.play() [if not muted]
│       └── _display_image(img)
├── MOUSEMOTION
│   ├── _bump_event_count()
│   └── If mouse_pressed: draw_dot()
├── MOUSEBUTTONDOWN
│   ├── _bump_event_count()
│   ├── draw_dot()
│   └── Toggle/set mouse_pressed
└── MOUSEBUTTONUP
    ├── _bump_event_count()
    └── Clear mouse_pressed [if not sticky]
```

---

## File Structure

```
bambam/
├── bambam.py              # Main application (with new background/mode features)
├── bambam_tui.py          # TUI launcher and configuration menu (NEW)
├── bambam_config.yaml     # Default configuration file (NEW)
├── bambam_launcher.sh     # Cage compositor wrapper script (NEW)
├── ARCHITECTURE.md        # This document (technical documentation)
├── PI5_INSTALLATION.md    # Raspberry Pi 5 setup guide (NEW)
├── README.md              # User documentation (updated)
├── EXTENSIONS.md          # Extension creation guide
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Development dependencies
├── setup.cfg              # Flake8 configuration
├── Makefile               # Build automation
├── 50-dont-vt-switch.conf # X11 VT switching disable config
├── data/                  # Default media files
│   ├── *.gif              # Animal/object images (12 files)
│   └── *.wav              # Sound effects (12 files)
├── extensions/            # Extension directory
│   └── alphanumeric-en_US/
│       ├── event_map.yaml # Declarative event mapping
│       └── sounds/        # 36 OGG files (0-9, a-z)
│           ├── [0-9].ogg
│           └── [a-z].ogg
├── po/                    # Translation files (17 languages)
│   └── *.po
├── test/                  # Test resources
│   └── *.png              # Test images (34 files)
├── docs/                  # Documentation images
│   └── bambam.png
└── .github/               # CI configuration
    └── workflows/
        └── python-app.yml
```

### New Files Added

| File | Purpose |
|------|---------|
| `bambam_tui.py` | Terminal user interface for configuration and launching |
| `bambam_config.yaml` | Default YAML configuration file |
| `bambam_launcher.sh` | Shell wrapper for cage compositor integration |
| `PI5_INSTALLATION.md` | Comprehensive Raspberry Pi 5 installation guide |
| `ARCHITECTURE.md` | This technical documentation file |

---

## Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pygame | >=2.6.1 | Graphics, sound, input handling |
| pyyaml | >=6.0.3 | Extension configuration parsing |

### System Dependencies (Raspberry Pi 5)

| Package | Purpose |
|---------|---------|
| python3 | Python interpreter |
| python3-pygame | Pygame library |
| python3-yaml | PyYAML library |
| cage | Wayland compositor for kiosk mode |
| swaylock | Screen locker for security |
| libsdl2-2.0-0 | SDL2 library (pygame backend) |
| libsdl2-mixer-2.0-0 | SDL2 audio mixer |
| libsdl2-image-2.0-0 | SDL2 image loading |

### Installation Commands (Debian/Ubuntu/Raspberry Pi OS)

```bash
# Core dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-pygame python3-yaml

# Cage compositor for secure kiosk mode
sudo apt install -y cage swaylock

# Optional: Build from pip for latest versions
pip3 install pygame pyyaml
```

---

## Raspberry Pi 5 Deployment

### Recommended Setup

1. **Use Raspberry Pi OS Lite (64-bit)** - Minimal overhead
2. **Install via apt** - Better ARM optimization
3. **Run in cage** - Secure Wayland kiosk environment

### Performance Optimizations

- Images auto-scaled to max 700px (configurable via `IMAGE_MAX_WIDTH`)
- 60 FPS cap via pygame clock
- OGG format preferred over WAV (smaller, hardware-decoded)
- Lazy resource loading

### Auto-Start Configuration

Create `/etc/systemd/system/bambam.service`:

```ini
[Unit]
Description=BamBam Children's Game
After=graphical.target

[Service]
Type=simple
User=pi
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStart=/usr/bin/cage /path/to/bambam_launcher.sh
Restart=always

[Install]
WantedBy=graphical.target
```

### Memory Considerations

| Resource | Approx. Memory |
|----------|----------------|
| Pygame init | ~50MB |
| Each image | ~1-5MB (after scaling) |
| Each sound | ~0.1-1MB |
| Total typical | ~100-200MB |

Pi 5 (4GB minimum recommended) handles this easily.

---

## Adding New Features Checklist

When adding new features, update:

1. [ ] `bambam.py` - Core implementation
2. [ ] `bambam_tui.py` - TUI configuration options
3. [ ] `bambam_config.yaml` - Default configuration
4. [ ] `ARCHITECTURE.md` - This documentation
5. [ ] `README.md` - User-facing documentation
6. [ ] Command-line arguments (if applicable)
7. [ ] Translation strings (wrap in `_()` or `N_()`)

---

## Agent Collaboration Notes

### Current Active Developments

- **TUI System**: Configuration menu and cage integration
- **Mode System**: All-modes button, random mode switching
- **Background System**: Custom backgrounds, random background switching
- **Extension Enhancements**: Audio+image matching modes

### Shared State

The configuration system uses `bambam_config.yaml` as the single source of truth. All agents should:
1. Read current config before making changes
2. Preserve existing settings when adding new ones
3. Use YAML anchors for shared values if needed

### Testing Protocol

```bash
# Syntax check
python3 -m py_compile bambam.py bambam_tui.py

# Lint check
flake8 bambam.py bambam_tui.py

# Run TUI (development)
python3 bambam_tui.py

# Run game directly
python3 bambam.py --extension alphanumeric-en_US
```

---

*Last Updated: 2026-01-05*
*Document Version: 1.0.0*
