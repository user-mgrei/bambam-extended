# Raspberry Pi 5 Lite Compatibility Guide

## Overview
This document provides verified compatibility information for running BamBam on Raspberry Pi 5 with Raspberry Pi OS Lite (Bookworm-based, Debian 12).

## System Requirements

### Hardware
- Raspberry Pi 5 (4GB or 8GB RAM recommended)
- MicroSD card (16GB+ recommended)
- Display with HDMI connection
- USB keyboard/mouse

### Software Base
- Raspberry Pi OS Lite (64-bit, arm64)
- Based on Debian 12 "Bookworm"
- Kernel 6.1+ with KMS/DRM support

## Verified apt Packages

### Core Dependencies
All packages verified available in Raspberry Pi OS Bookworm repos:

```bash
# Python 3 (default is 3.11 on Bookworm)
sudo apt install python3 python3-pip

# Pygame (SDL2-based)
sudo apt install python3-pygame

# PyYAML for extension support
sudo apt install python3-yaml
```

### Display/Graphics Stack (for TUI/Cage setup)
```bash
# Cage - minimal Wayland compositor (CRITICAL for TUI mode)
sudo apt install cage

# Additional display dependencies
sudo apt install libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0
sudo apt install libgl1-mesa-dri
```

### Audio Support
```bash
# ALSA and PulseAudio for sound
sudo apt install alsa-utils pulseaudio
# Or for PipeWire (newer, recommended)
sudo apt install pipewire pipewire-alsa
```

### Development/Testing Dependencies
```bash
# For running tests (optional)
sudo apt install xvfb xauth imagemagick xdotool sox
```

## Complete Installation Script

```bash
#!/bin/bash
# BamBam Pi 5 Lite Installation Script
# Tested on Raspberry Pi OS Lite (Bookworm, 64-bit)

set -e

echo "=== BamBam Pi 5 Lite Installation ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install core dependencies
echo "Installing core dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-pygame \
    python3-yaml \
    git

# Install Cage compositor for TUI mode
echo "Installing Cage Wayland compositor..."
sudo apt install -y cage

# Install audio support
echo "Installing audio support..."
sudo apt install -y alsa-utils

# Optional: PipeWire for better audio handling
# sudo apt install -y pipewire pipewire-alsa

# Clone BamBam (if not already present)
if [ ! -d "bambam" ]; then
    echo "Cloning BamBam repository..."
    git clone https://github.com/porridge/bambam.git
fi

cd bambam

# Verify installation
echo "Verifying installation..."
python3 -c "import pygame; print(f'Pygame version: {pygame.version.ver}')"
python3 -c "import yaml; print('PyYAML: OK')"

echo "=== Installation Complete ==="
echo "To run BamBam:"
echo "  Direct mode: ./bambam.py"
echo "  Cage/TUI mode: cage ./bambam.py"
```

## Running with Cage (Recommended for Kiosk Mode)

### Basic Cage Launch
```bash
# Run BamBam in Cage from TTY (not from desktop)
cage ./bambam.py
```

### Auto-start on Boot (systemd service)
Create `/etc/systemd/system/bambam-kiosk.service`:

```ini
[Unit]
Description=BamBam Kiosk Mode
After=multi-user.target

[Service]
User=pi
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStart=/usr/bin/cage /path/to/bambam/bambam.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable with:
```bash
sudo systemctl enable bambam-kiosk.service
sudo systemctl start bambam-kiosk.service
```

## Package Version Matrix

| Package | Bookworm Version | Minimum Required | Status |
|---------|------------------|------------------|--------|
| python3 | 3.11.2 | 3.9+ | ✅ OK |
| python3-pygame | 2.1.2 | 2.x | ✅ OK |
| python3-yaml | 6.0 | 5.0+ | ✅ OK |
| cage | 0.1.4 | 0.1+ | ✅ OK |
| libsdl2-2.0-0 | 2.26.5 | 2.0+ | ✅ OK |

## Performance Optimizations

### GPU Memory Allocation
Edit `/boot/config.txt`:
```
# Allocate more GPU memory for smooth graphics
gpu_mem=256
```

### Disable Unnecessary Services
```bash
# For kiosk mode, disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
sudo systemctl disable triggerhappy
```

### CPU Governor
```bash
# Set performance governor for consistent frame rates
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## Troubleshooting

### No Display in Cage
- Ensure running from TTY, not from within another compositor
- Check `dmesg` for DRM errors
- Verify `/dev/dri/card0` exists

### No Sound
```bash
# Test audio
aplay -l  # List audio devices
speaker-test -c 2  # Test stereo output

# Check mixer levels
alsamixer
```

### Permission Issues
```bash
# Add user to required groups
sudo usermod -aG video,audio,input,render $USER
```

### PyYAML Import Error
```bash
# If system package conflicts with pip
pip3 install --user pyyaml --force-reinstall
```

## Known Limitations

1. **Wayland vs X11**: BamBam has Wayland detection but recommends dedicated session mode. Cage provides this safely.

2. **Keyboard Grab**: On Pi 5 with Cage, keyboard grab works correctly. VT switching (Ctrl+Alt+Fx) may still be possible.

3. **Screen Resolution**: Auto-detected. For specific resolution, configure in `/boot/config.txt`.

## Verified Extension Compatibility

The `alphanumeric-en_US` extension works correctly on Pi 5 Lite with:
- OGG audio files (libvorbis via SDL2_mixer)
- YAML event mapping
- Font rendering (freetype)

## Contact & Issues

For Pi 5-specific issues, please file a GitHub issue with:
- Output of `cat /etc/os-release`
- Output of `uname -a`
- Output of `dpkg -l | grep -E "pygame|yaml|cage"`
