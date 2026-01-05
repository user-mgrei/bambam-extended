# New Features Implementation Guide

## Overview

This guide provides specifications for implementing new features in BamBam:
1. Mode-button to run all modes at once
2. Background image customization
3. Keypress-triggered random mode/background changes

## Feature 1: All Modes Button

### Concept
Allow running multiple extensions/modes simultaneously so different keypresses can trigger different sound/image sets.

### Implementation Approach

#### Option A: Mode Multiplexing (Recommended)
Run multiple mappers in parallel, selecting randomly which one responds.

```python
class MultiModeMapper:
    """Combines multiple mappers into one."""
    
    def __init__(self, mappers: list, random_gen):
        self._mappers = mappers
        self._random = random_gen
    
    def map(self, event):
        """Randomly select a mapper to handle the event."""
        mapper = self._random.choice(self._mappers)
        return mapper.map(event)
```

#### Option B: Mode Layering
Let each mode process the event, combining responses.

```python
class LayeredModeMapper:
    """Processes event through all mappers."""
    
    def __init__(self, mappers: list):
        self._mappers = mappers
    
    def map(self, event):
        """Return first successful mapping."""
        for mapper in self._mappers:
            try:
                result = mapper.map(event)
                if result[0]:  # Has policy
                    return result
            except Exception:
                continue
        return "random", None  # Fallback
```

### Command Line Addition
```python
parser.add_argument('--all-modes', action='store_true',
                    help=_('Run all available extensions simultaneously.'))
```

### Loading Multiple Extensions
```python
def _load_all_extensions(self):
    """Load all extensions from extension directories."""
    extensions = []
    for ext_dir in self.extensions_dirs:
        for subdir in os.listdir(ext_dir):
            ext_path = os.path.join(ext_dir, subdir)
            if os.path.isdir(ext_path) and os.path.exists(
                    os.path.join(ext_path, 'event_map.yaml')):
                extensions.append(subdir)
    return extensions
```

## Feature 2: Background Image

### Concept
Allow customizable background images instead of solid colors.

### Implementation

#### Add Command Line Argument
```python
parser.add_argument('--background-image', type=str, metavar='PATH',
                    help=_('Use custom background image.'))
```

#### Modify `_prepare_screen()` Method
```python
def _prepare_screen(self, args):
    # ... existing code ...
    
    if args.background_image:
        try:
            bg_image = pygame.image.load(args.background_image)
            # Scale to screen size
            bg_image = pygame.transform.scale(
                bg_image, 
                (self.display_width, self.display_height)
            )
            self.background = bg_image.convert()
        except pygame.error as e:
            print(_('Warning: Could not load background image: %s') % e,
                  file=sys.stderr)
            # Fall back to solid color
            self.background = pygame.Surface(self.screen.get_size()).convert()
            self.background.fill(self.background_color)
    else:
        # Existing solid color background
        self.background = pygame.Surface(self.screen.get_size()).convert()
        self.background.fill(self.background_color)
```

#### Background Image Validation
```python
SUPPORTED_BG_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

def validate_background_image(path: str) -> bool:
    """Validate background image file."""
    if not os.path.exists(path):
        return False
    ext = os.path.splitext(path)[1].lower()
    return ext in SUPPORTED_BG_FORMATS
```

## Feature 3: Keypress-Triggered Changes

### Concept
After N keypresses (within a configurable range), randomly change:
- The active mode/extension
- The background image

### Implementation

#### Configuration Parameters
```python
parser.add_argument('--mode-change-range', type=str, metavar='MIN-MAX',
                    help=_('Keypresses before random mode change (e.g., "10-20").'))
parser.add_argument('--background-change-range', type=str, metavar='MIN-MAX',
                    help=_('Keypresses before random background change (e.g., "15-30").'))
```

#### Range Parser
```python
def parse_range(range_str: str) -> tuple:
    """Parse 'MIN-MAX' string to (min, max) tuple."""
    if not range_str:
        return None
    parts = range_str.split('-')
    if len(parts) != 2:
        raise ValueError(f"Invalid range format: {range_str}")
    return (int(parts[0]), int(parts[1]))
```

#### Keypress Counter Class
```python
class KeypressCounter:
    """Counts keypresses and triggers changes at random intervals."""
    
    def __init__(self, min_count: int, max_count: int, random_gen):
        self._min = min_count
        self._max = max_count
        self._random = random_gen
        self._current_count = 0
        self._trigger_at = self._random.randint(min_count, max_count)
    
    def increment(self) -> bool:
        """Increment counter, return True if trigger reached."""
        self._current_count += 1
        if self._current_count >= self._trigger_at:
            self._current_count = 0
            self._trigger_at = self._random.randint(self._min, self._max)
            return True
        return False
```

#### Integration in Bambam Class
```python
class Bambam:
    def __init__(self):
        # ... existing code ...
        self._mode_change_counter = None
        self._background_change_counter = None
        self._available_backgrounds = []
        self._available_extensions = []
    
    def _init_change_counters(self, args):
        """Initialize keypress change counters."""
        if args.mode_change_range:
            min_k, max_k = parse_range(args.mode_change_range)
            self._mode_change_counter = KeypressCounter(min_k, max_k, self._random)
            self._available_extensions = self._load_all_extensions()
        
        if args.background_change_range:
            min_k, max_k = parse_range(args.background_change_range)
            self._background_change_counter = KeypressCounter(min_k, max_k, self._random)
            self._available_backgrounds = self._load_background_images()
    
    def _bump_event_count(self):
        """Called on each event."""
        self._event_count = (self._event_count + 1) % (self._HUE_SPACE * 2)
        
        # Check for mode change trigger
        if self._mode_change_counter and self._mode_change_counter.increment():
            self._change_random_mode()
        
        # Check for background change trigger
        if self._background_change_counter and self._background_change_counter.increment():
            self._change_random_background()
    
    def _change_random_mode(self):
        """Switch to a random extension."""
        if self._available_extensions:
            new_ext = self._random.choice(self._available_extensions)
            logging.info('Switching to extension: %s', new_ext)
            self._sound_mapper, self._image_mapper = self._get_extension_mappers(new_ext)
    
    def _change_random_background(self):
        """Switch to a random background image."""
        if self._available_backgrounds:
            bg_path = self._random.choice(self._available_backgrounds)
            logging.info('Switching to background: %s', bg_path)
            try:
                bg_image = pygame.image.load(bg_path)
                bg_image = pygame.transform.scale(
                    bg_image, 
                    (self.display_width, self.display_height)
                )
                self.background = bg_image.convert()
            except pygame.error:
                pass  # Keep current background
    
    def _load_background_images(self) -> list:
        """Load list of available background images."""
        backgrounds = []
        bg_dir = os.path.join(os.path.dirname(__file__), 'backgrounds')
        if os.path.isdir(bg_dir):
            for f in os.listdir(bg_dir):
                if os.path.splitext(f)[1].lower() in SUPPORTED_BG_FORMATS:
                    backgrounds.append(os.path.join(bg_dir, f))
        return backgrounds
```

## Directory Structure for New Features

```
bambam/
├── bambam.py              # Main game (modified)
├── backgrounds/           # NEW: Background images directory
│   ├── nature.jpg
│   ├── space.png
│   └── abstract.jpg
├── extensions/
│   ├── alphanumeric-en_US/
│   ├── animals/           # NEW: Example additional extension
│   │   ├── event_map.yaml
│   │   └── sounds/
│   └── instruments/       # NEW: Example additional extension
│       ├── event_map.yaml
│       └── sounds/
└── config/
    └── default.yaml       # Default configuration
```

## Event Map Extensions

### For new modes with images AND sounds
```yaml
apiVersion: 0

# Animal mode example
image:
- check:
  - type: KEYDOWN
  - unicode:
      value: "a"
  policy: named_file
  args: ["ant.png"]

- check:
  - type: KEYDOWN
  - unicode:
      value: "b"
  policy: named_file
  args: ["bear.png"]

- policy: random

sound:
- check:
  - type: KEYDOWN
  - unicode:
      value: "a"
  policy: named_file
  args: ["ant.ogg"]

- check:
  - type: KEYDOWN
  - unicode:
      value: "b"
  policy: named_file
  args: ["bear.ogg"]

- policy: random
```

## Validation Checklist for New Features

### All Modes Button
- [ ] Can discover all extensions automatically
- [ ] Handles missing extensions gracefully
- [ ] Memory-efficient (doesn't load all sounds at once)
- [ ] Command line argument documented

### Background Images
- [ ] Scales images to screen size
- [ ] Handles missing/invalid images gracefully
- [ ] Works with PNG, JPG, GIF formats
- [ ] Pi 5 GPU can handle image scaling

### Keypress Triggers
- [ ] Range parsing robust (handles edge cases)
- [ ] Counter resets properly after trigger
- [ ] No performance impact on Pi 5
- [ ] Logging shows mode/background changes
- [ ] Works with `--trace` flag

### General
- [ ] All Python 3.9+ compatible
- [ ] No new pip-only dependencies
- [ ] Flake8 passes
- [ ] Unit tests added
- [ ] Documentation updated

## Testing Commands

```bash
# Test all modes
./bambam.py --all-modes --trace

# Test background image
./bambam.py --background-image backgrounds/nature.jpg

# Test mode change trigger
./bambam.py --mode-change-range 5-10 --trace

# Test background change trigger
./bambam.py --background-change-range 10-15 --trace

# Combined
./bambam.py --all-modes --background-change-range 10-15 --mode-change-range 5-10 --trace
```

## Pi 5 Performance Considerations

1. **Image Scaling**: Scale once at load, not on each change
2. **Memory**: Don't preload all extension sounds, load on mode switch
3. **File I/O**: Cache extension list, don't rescan directories
4. **Logging**: Use `--trace` only for debugging, not production
