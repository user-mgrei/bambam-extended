# BamBam Codebase Reference Documentation

## Architecture Overview

BamBam is a keyboard-mashing game for babies and toddlers built with Python 3 and Pygame.

### Core Components

```
bambam.py (main application)
├── Bambam class (main game controller)
│   ├── __init__() - Initialize random, data dirs, policies
│   ├── run() - Main entry point and game loop
│   ├── _load_resources() - Load sounds and images
│   ├── _prepare_screen() - Setup display and background
│   ├── process_keypress() - Handle keyboard/joystick events
│   └── _select_response() - Choose sound/image for event
│
├── Policy Classes (select media for events)
│   ├── CollectionPolicyBase - Base class for collections
│   ├── DeterministicPolicy - Same response for same key
│   ├── RandomPolicy - Random selection
│   ├── NamedFilePolicy - Select specific file by name
│   └── FontImagePolicy - Render character as image
│
├── Mapper Classes (map events to policies)
│   ├── LegacySoundMapper - Default sound mapping
│   ├── LegacyImageMapper - Default image mapping
│   └── DeclarativeMapper - YAML-based mapping
│
└── Exception Classes
    ├── BambamException - Base exception
    └── ResourceLoadException - File load failure
```

## Key Functions Reference

### `Bambam.run()` - Main Entry Point
- Parses command line arguments
- Initializes pygame and display
- Loads resources (sounds, images)
- Shows welcome message
- Runs main event loop

### Command Line Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `-e, --extension` | Extension name | None |
| `-u, --uppercase` | Show uppercase letters | False |
| `--sound_blacklist` | Patterns to skip | [] |
| `--image_blacklist` | Patterns to skip | [] |
| `-d, --deterministic-sounds` | Same key = same sound | False |
| `-D, --dark` | Dark background | False |
| `-m, --mute` | Start muted | False |
| `--sticky-mouse` | Sticky mouse buttons | False |
| `--wayland-ok` | Allow Wayland | False |
| `--in-dedicated-session` | Running in session | False |
| `--trace` | Debug logging | False |

### Control Strings (typed to execute)
- `quit` - Exit game
- `sound` - Toggle sound
- `mute` - Mute sounds
- `unmute` - Unmute sounds
- `mouse` - Toggle sticky mouse

## Extension System

### Extension Structure
```
extensions/
└── extension-name/
    ├── event_map.yaml     # Required: event mapping rules
    └── sounds/            # Optional: audio files
        ├── file1.ogg
        └── file2.wav
```

### event_map.yaml Schema (apiVersion: 0)
```yaml
apiVersion: 0  # Required, must be 0

image:         # Optional: image selection rules
  - check:     # Optional: list of conditions
      - type: KEYDOWN  # Event type check
      - unicode:       # Character checks
          isalpha: True/False
          isdigit: True/False
          value: "x"   # Specific character
    policy: font|random|named_file
    args: ["filename.ext"]  # For named_file policy

sound:         # Optional: sound selection rules
  - check: [...]
    policy: random|deterministic|named_file
    args: ["filename.ext"]
```

### Policy Reference
| Policy | Used For | Args | Description |
|--------|----------|------|-------------|
| `font` | image | None | Render character as glyph |
| `random` | both | None | Random from data directory |
| `deterministic` | sound | None | Consistent per key |
| `named_file` | both | [filename] | Specific file from extension |

### Check Conditions
- `type: KEYDOWN` - Matches keyboard events
- `unicode.isalpha: True/False` - Letter check
- `unicode.isdigit: True/False` - Digit check
- `unicode.value: "x"` - Specific character match

## File Format Support

### Images
- GIF (`.gif`)
- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- TIFF (`.tif`, `.tiff`)

### Sounds
- WAV (`.wav`)
- OGG Vorbis (`.ogg`)

### Size Constraints
- `IMAGE_MAX_WIDTH = 700` - Images scaled down if larger

## Data Directory Locations

Searched in order:
1. `<program_dir>/data/`
2. `<program_dir>/../share/bambam/data/`
3. `~/.local/share/bambam/data/`

Extension directories:
1. `<program_dir>/extensions/`
2. `<program_dir>/../share/bambam/extensions/`
3. `~/.local/share/bambam/extensions/`

## Color System

### Background Colors
- Light mode: `(250, 250, 250)`
- Dark mode: `(0, 0, 0)`

### Dynamic Colors
The `get_color()` method cycles through HSV color space based on event count:
- Hue: cycles 0-360° (divided by 2 for gradual change)
- Saturation: 100%
- Value: 100%

## Event Handling

### Supported Event Types
| Event Type | Handler | Description |
|------------|---------|-------------|
| `KEYDOWN` | `process_keypress()` | Keyboard press |
| `JOYBUTTONDOWN` | `process_keypress()` | Gamepad button |
| `MOUSEMOTION` | `draw_dot()` | Mouse movement |
| `MOUSEBUTTONDOWN` | `draw_dot()` | Mouse click |
| `MOUSEBUTTONUP` | - | Mouse release |
| `QUIT` | `sys.exit(0)` | Window close |

### Screen Clear Logic
- 10% chance (`random.randint(0, 10) == 1`) to clear on keypress

## Testing System

### E2E Tests (`test_e2e.py`)
- Uses Xvfb virtual display
- Takes screenshots at key points
- Validates audio output
- Compares against golden files

### Test Scenarios
| Test | Options | Validates |
|------|---------|-----------|
| regular | none | Basic functionality |
| dark | `--dark` | Dark mode |
| deterministic | `--deterministic-sounds` | Sound consistency |
| muted | `--mute` | Muted start |
| start-muted | `--mute` | Unmute command |
| no-audio | invalid driver | No sound support |

## Security Considerations

### Input Grab
- `pygame.event.set_grab(True)` - Grabs pointer
- `pygame.event.set_keyboard_grab(True)` - Grabs keyboard (if available)

### Wayland Safety
- Detects Wayland via `WAYLAND_DISPLAY` or `XDG_SESSION_TYPE`
- Shows warning unless `--wayland-ok` or `--in-dedicated-session`

### Dedicated Session
- Recommended for safety
- Uses display manager session selection
- Logs out on game exit

## Dependencies

### Required
- Python 3.9+
- Pygame 2.x

### Optional
- PyYAML (for extensions)

### System (Linux)
- SDL2 libraries
- Display server (X11 or Wayland with compositor)
- Audio system (ALSA/PulseAudio/PipeWire)
