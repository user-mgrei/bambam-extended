# BamBam Pi 5 Standalone Test Package

## Overview

This is a **standalone test environment** for BamBam that can be deployed to your Raspberry Pi 5 Lite without affecting any existing BamBam installations.

**Installation Path**: `/opt/bambam-test/` (isolated from system bambam)

## New Features

### 🎯 Adaptive Learning Profiles (`bambam_profiles.py`)
- Tracks child engagement and preferences
- Stores favorite letters, sounds, and themes
- Session history and statistics
- Multi-child profile support

### 🎨 Multi-Sensory Themes (`bambam_themes.py`)
- Built-in themes: default, dark, farm, ocean, space, music, nature
- Random theme swapping based on keypress count
- Multi-mode: run all extensions with random swapping
- Custom background image support

### 📱 Remote Parent Control (`bambam_remote.py`)
- Flask web app for remote monitoring/control
- View session timer and keypress count
- Mute/unmute, pause, and stop controls
- **Designed for Tailscale** - you configure the network access

## Quick Start

### 1. Copy to Pi 5
```bash
# From your development machine:
scp -r pi5-standalone/ pi@<your-pi-ip>:~/bambam-test/

# Or use rsync for efficiency:
rsync -avz pi5-standalone/ pi@<your-pi-ip>:~/bambam-test/
```

### 2. Run Installation on Pi 5
```bash
ssh pi@<your-pi-ip>
cd ~/bambam-test
chmod +x install.sh
./install.sh
```

### 3. Test the Installation
```bash
# Run directly (in terminal/SSH with X forwarding)
./test-run.sh

# Run in Cage kiosk mode (from TTY)
./run-cage.sh

# Run TUI configuration menu
./run-tui.sh
```

## Package Contents

```
pi5-standalone/
├── README.md              # This file
├── install.sh             # Main installation script
├── test-run.sh            # Quick test runner
├── run-cage.sh            # Cage kiosk launcher
├── run-tui.sh             # TUI configuration launcher
├── bambam.py              # Main game (copied from repo)
├── bambam_tui.py          # TUI menu (if implemented)
├── requirements.txt       # Python dependencies
├── scripts/
│   ├── fact_check.py      # Validation script
│   └── uninstall.sh       # Clean removal script
├── config/
│   └── default.yaml       # Default configuration
├── data/                  # Game assets (copied)
├── extensions/            # Extensions (copied)
├── backgrounds/           # Background images
└── docs/
    ├── PI5_COMPATIBILITY.md
    ├── TUI_IMPLEMENTATION_GUIDE.md
    └── NEW_FEATURES_GUIDE.md
```

## Isolation from Existing Installation

This package is completely isolated:
- Installs to `/opt/bambam-test/` (not `/usr/games/bambam`)
- Config stored in `~/.config/bambam-test/` (not `~/.config/bambam/`)
- No system-wide desktop entries created
- No systemd services installed by default
- Can be completely removed with `./scripts/uninstall.sh`

## Testing Checklist

After installation, verify:

- [ ] `./test-run.sh` launches game successfully
- [ ] Sound plays on keypress
- [ ] Images display on keypress
- [ ] `quit` command exits game
- [ ] `./run-cage.sh` works from TTY
- [ ] Extensions load correctly
- [ ] TUI menu works (if implemented)

## Troubleshooting

### No display in cage
```bash
# Check if running from TTY (not SSH with X)
tty
# Should show /dev/tty1 or similar

# Check DRM devices
ls -la /dev/dri/
```

### No sound
```bash
# Test audio
aplay -l
speaker-test -c 2 -t wav

# Check mixer
alsamixer
```

### Permission denied
```bash
# Add user to required groups
sudo usermod -aG video,audio,input,render $USER
# Log out and back in
```

### Python import errors
```bash
# Reinstall dependencies
./install.sh --reinstall-deps
```

## Updating

To update with new changes from the fork:
```bash
# On your development machine, regenerate package:
cd /path/to/bambam-fork
./scripts/build-pi5-package.sh

# Copy to Pi:
rsync -avz pi5-standalone/ pi@<your-pi-ip>:~/bambam-test/

# On Pi, reinstall:
cd ~/bambam-test
./install.sh --update
```

## Using New Features

### Adaptive Learning Profiles
```python
# In your code or TUI:
from bambam_profiles import ProfileManager

pm = ProfileManager()
profile = pm.set_active_profile("Emma")
profile.start_session(extension="alphanumeric-en_US")
# ... game runs ...
profile.record_keypress("a", sound_played="a.ogg")
profile.end_session()
print(profile.get_stats_summary())
```

### Multi-Sensory Themes with Random Swapping
```python
from bambam_themes import ThemeManager, MultiModeManager

# Theme management
tm = ThemeManager()
tm.set_current_theme("ocean")
tm.enable_mode_swap(min_keypresses=15, max_keypresses=30)

# On each keypress:
new_theme = tm.on_keypress()
if new_theme:
    print(f"Switched to theme: {new_theme.display_name}")

# Multi-mode (all extensions at once)
mm = MultiModeManager(extensions_dirs=[Path("extensions")])
mm.enable_all_modes()
mm.enable_extension_swap(min_keypresses=10, max_keypresses=25)
```

### Remote Parent Control (Flask)
```bash
# Start the remote control server
python3 bambam_remote.py --port 8080

# Access from browser:
# http://localhost:8080 (local)
# http://<tailscale-ip>:8080 (via Tailscale)
```

**Tailscale Setup** (you handle this):
1. Install Tailscale on Pi 5: `curl -fsSL https://tailscale.com/install.sh | sh`
2. Login: `sudo tailscale up`
3. Access from any device on your Tailscale network

### Configuration File
Edit `~/.config/bambam-test/config.yaml`:
```yaml
profile:
  name: Emma
  track_engagement: true

theme:
  name: ocean

multi_mode:
  enabled: true
  swap_range: [10, 30]

remote_control:
  enabled: true
  port: 8080
```

## Cleanup

To completely remove the test installation:
```bash
./scripts/uninstall.sh
```

This removes:
- `/opt/bambam-test/`
- `~/.config/bambam-test/`
- Any test-specific files

Your existing BamBam installation (if any) remains untouched.
