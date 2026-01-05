# BamBam Pi 5 Standalone Test Package

## Overview

This is a **standalone test environment** for BamBam that can be deployed to your Raspberry Pi 5 Lite without affecting any existing BamBam installations.

**Installation Path**: `/opt/bambam-test/` (isolated from system bambam)

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
