# BamBam Plus Architecture Documentation

## Overview

BamBam Plus is an enhanced fork of BamBam - a keyboard mashing and doodling game for babies and toddlers. This document provides persistent context for all development agents and contributors.

## Core Files Structure

```
/workspace/
├── bambam.py              # Main application (805 lines)
├── bambam_tui.py          # TUI configuration interface (NEW)
├── bambam_config.py       # Configuration management (NEW)
├── requirements.txt       # Runtime dependencies (pygame, pyyaml)
├── requirements-dev.txt   # Development dependencies
├── data/                  # Built-in media files
│   ├── *.gif             # Animal/character images
│   └── *.wav             # Sound effects
├── extensions/            # Extension modules
│   └── alphanumeric-en_US/
│       ├── event_map.yaml # Event routing configuration
│       └── sounds/        # Phonetic pronunciations (a-z, 0-9.ogg)
└── test/                  # E2E tests and golden files
```

## Core Classes (bambam.py)

### Main Application Classes

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `Bambam` | Main game controller | `run()`, `process_keypress()`, `_select_response()` |
| `BambamException` | Base exception class | - |
| `ResourceLoadException` | Media loading errors | `__str__()` |

### Policy Classes (Sound/Image Selection)

| Class | Purpose | Selection Strategy |
|-------|---------|-------------------|
| `CollectionPolicyBase` | Abstract base for policies | Stores named media items |
| `DeterministicPolicy` | Key-based selection | `key % len(items)` |
| `RandomPolicy` | Random selection | `random.choice()` |
| `NamedFilePolicy` | File name lookup | Direct dictionary lookup |
| `FontImagePolicy` | Text rendering | Renders unicode chars with random colors |

### Mapper Classes (Event → Policy Routing)

| Class | Purpose | Configuration |
|-------|---------|---------------|
| `LegacySoundMapper` | Default sound routing | Deterministic or random |
| `LegacyImageMapper` | Default image routing | Font for alphanumeric, random otherwise |
| `DeclarativeMapper` | YAML-based routing | `event_map.yaml` spec |

## Event Flow Diagram

```
User Input (Keyboard/Mouse/Joystick)
         │
         ▼
    pygame.event.get()
         │
         ▼
    Event Type Check
    ├── KEYDOWN / JOYBUTTONDOWN → process_keypress()
    │         │
    │         ▼
    │   _maybe_process_command() ← Check for quit/mute/sound commands
    │         │
    │         ▼
    │   _select_response()
    │   ├── Sound: _map_and_select(sound_mapper, sound_policies)
    │   └── Image: _map_and_select(image_mapper, image_policies)
    │         │
    │         ▼
    │   Display image + Play sound
    │
    ├── MOUSEMOTION → draw_dot() (if mouse pressed)
    └── MOUSEBUTTONDOWN/UP → draw_dot() + toggle mouse state
```

## Extension System (API v0)

### event_map.yaml Structure
```yaml
apiVersion: 0          # Required, only "0" supported
image:                 # Optional image routing
  - check:             # Condition list (all must match)
      - type: KEYDOWN
      - unicode:
          isalpha: True
    policy: font       # Policy name
    args: []          # Optional policy arguments
  - policy: random    # Fallback (no check = always match)

sound:                # Optional sound routing
  - check:
      - unicode:
          value: "a"
    policy: named_file
    args: ["a.ogg"]
  - policy: random    # Fallback
```

### Available Policies
- `font` - Render key's unicode character (image only)
- `random` - Pick random media from data/ directory
- `named_file` - Use specific file from extension (sound only currently)
- `deterministic` - Deterministic selection based on key code

### Check Types
- `type: KEYDOWN` - Match keyboard events
- `unicode.value: "x"` - Exact character match
- `unicode.isalpha: True/False` - Is alphabetic
- `unicode.isdigit: True/False` - Is numeric

## Command Strings (Typed During Game)

| Command | Action | Translatable |
|---------|--------|--------------|
| `quit` | Exit game | Yes |
| `sound` | Toggle sound | Yes |
| `mute` | Mute sounds | Yes |
| `unmute` | Unmute sounds | Yes |
| `mouse` | Toggle sticky mouse | Yes |

## Configuration Options (CLI)

| Flag | Description |
|------|-------------|
| `-e, --extension NAME` | Load extension |
| `-u, --uppercase` | Show uppercase letters |
| `-d, --deterministic-sounds` | Same sounds for same keys |
| `-D, --dark` | Dark background mode |
| `-m, --mute` | Start muted |
| `--sticky-mouse` | Sticky mouse buttons |
| `--wayland-ok` | Allow Wayland (unsafe) |
| `--sound_blacklist PATTERN` | Skip matching sounds |
| `--image_blacklist PATTERN` | Skip matching images |

## Data Directories Search Order

1. `{program_dir}/data/` - Alongside bambam.py
2. `{program_dir}/../share/bambam/data/` - System install
3. `$XDG_DATA_HOME/bambam/data/` or `~/.local/share/bambam/data/`

## Dependencies

### Runtime (requirements.txt)
- `pygame==2.6.1` - Graphics, sound, input handling
- `pyyaml==6.0.3` - Extension configuration parsing

### Development (requirements-dev.txt)
- `flake8` - Linting
- `autopep8` - Code formatting
- `pre-commit` - Git hooks

## Testing

### E2E Test Framework
- `test_e2e.py` - Main test script
- `run_e2e_test.sh` - Test runner wrapper
- Uses Xvfb for headless display
- Golden file comparison for screenshots

### Test Scenarios
Located in `test/golden/{python_version}/{extension}/{mode}/`:
- `welcome.png` - Initial welcome screen
- `blank.png` - Cleared screen
- `success.png` - After key presses

---

## NEW FEATURES (Implemented)

### TUI Configuration Interface (`bambam_tui.py`)
- Terminal-based curses configuration menu
- Cage compositor integration for secure Wayland sessions
- Mode selection and settings management
- Easy navigation with arrow keys and Enter

**Launch:** `python3 bambam_tui.py` or `bambam-tui`

### Configuration System (`bambam_config.py`)
- JSON-based persistent settings storage
- Config location: `~/.config/bambam/config.json`
- Dataclass-based configuration with type hints

### Enhanced Extensions
- Audio + Image pairing per extension (named_file policy for images)
- Distinct mode toggle for synchronized audio/image responses
- Supports loading images from extension directories

### Background Image System
- Custom background images support
- Backgrounds directory: `~/.local/share/bambam/backgrounds/`
- Automatic scaling to screen size
- Background rotation on keypress triggers

### Dynamic Mode Features
- **All Modes Button:** Cycles through all available extensions
- **Random Mode Change:** Configurable keypress range (default 50-150)
- **Random Background Change:** Configurable keypress range (default 30-100)

### New CLI Arguments
| Flag | Description | Default |
|------|-------------|---------|
| `--background PATH` | Custom background image | None |
| `--all-modes` | Enable all modes cycling | False |
| `--mode-change-min N` | Min keypresses for mode change | 50 |
| `--mode-change-max N` | Max keypresses for mode change | 150 |
| `--bg-change-min N` | Min keypresses for background change | 30 |
| `--bg-change-max N` | Max keypresses for background change | 100 |

---

## Raspberry Pi 5 Lite Installation

### Quick Install
```bash
./install_pi5.sh
```

### Manual Installation (apt packages)
```bash
# Required packages
sudo apt install python3-pygame python3-yaml

# Optional: Cage compositor for secure sessions
sudo apt install cage wlr-randr
```

### Launch Commands After Installation
```bash
bambam          # Direct launch
bambam-tui      # TUI configuration menu
bambam-cage     # Launch in secure cage session
```

### Performance Considerations for Pi 5
- Uses hardware-accelerated pygame display (FULLSCREEN mode)
- Images scaled on load to max 700px width (configurable)
- Audio: 44.1kHz, 16-bit stereo (pygame defaults)
- Recommended: Use `cage` for dedicated kiosk-style sessions

### File Locations
| Type | System Install | User Install |
|------|----------------|--------------|
| Program | `/usr/share/bambam/` | `~/.local/share/bambam/` |
| Config | `~/.config/bambam/` | `~/.config/bambam/` |
| Backgrounds | `/usr/share/bambam/backgrounds/` | `~/.local/share/bambam/backgrounds/` |
| Extensions | `/usr/share/bambam/extensions/` | `~/.local/share/bambam/extensions/` |

---

## File Inventory

### Core Files
| File | Lines | Purpose |
|------|-------|---------|
| `bambam.py` | ~900 | Main game application |
| `bambam_tui.py` | ~580 | TUI configuration interface |
| `bambam_config.py` | ~220 | Configuration management |
| `install_pi5.sh` | ~150 | Pi 5 installation script |

### Directories
```
/workspace/
├── bambam.py              # Main application
├── bambam_tui.py          # TUI interface
├── bambam_config.py       # Config management
├── install_pi5.sh         # Pi 5 installer
├── ARCHITECTURE.md        # This documentation
├── data/                  # Built-in media
├── extensions/            # Extension modules
│   └── alphanumeric-en_US/
├── backgrounds/           # Background images (NEW)
└── test/                  # E2E tests
```

---

## Agent Coordination Log

| Agent | Task | Status | Notes |
|-------|------|--------|-------|
| 1 | Documentation | ✅ Complete | ARCHITECTURE.md created |
| 2 | TUI Interface | ✅ Complete | bambam_tui.py with cage support |
| 3 | New Features | ✅ Complete | Modes, backgrounds, triggers |
| 4 | Optimization | ✅ Complete | Pi 5 installer, syntax verified |

Last updated: 2026-01-05
