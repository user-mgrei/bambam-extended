# BamBam Plus - Raspberry Pi 5 Installation Guide

This guide covers installation and setup of BamBam Plus on Raspberry Pi 5 with Raspberry Pi OS Lite (64-bit).

## System Requirements

- Raspberry Pi 5 (4GB or 8GB recommended)
- Raspberry Pi OS Lite (64-bit) or Raspberry Pi OS Desktop
- Display connected via HDMI
- Keyboard and optionally mouse
- SD Card (16GB minimum, 32GB recommended)

## Quick Installation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install core dependencies
sudo apt install -y \
    python3 \
    python3-pip \
    python3-pygame \
    python3-yaml

# Install cage compositor for secure kiosk mode
sudo apt install -y cage swaylock

# Clone or download BamBam Plus
git clone https://github.com/YOUR_FORK/bambam.git
cd bambam

# Test the installation
python3 bambam.py --help
```

## Detailed Installation

### Step 1: System Preparation

```bash
# Update package lists
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y

# Install essential build tools (optional, for building from source)
sudo apt install -y build-essential git
```

### Step 2: Install Python Dependencies

```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install pygame via apt (recommended for ARM optimization)
sudo apt install -y python3-pygame

# Install PyYAML via apt
sudo apt install -y python3-yaml
```

**Why apt over pip?**
- Apt packages are pre-compiled for ARM64 architecture
- Better integration with system libraries
- Automatic security updates
- Lower resource usage during installation

### Step 3: Install Wayland Compositor (for Kiosk Mode)

```bash
# Install cage - minimal Wayland compositor for kiosk mode
sudo apt install -y cage

# Install swaylock for screen locking
sudo apt install -y swaylock

# Optional: Install wlr-randr for display configuration
sudo apt install -y wlr-randr
```

### Step 4: SDL2 Libraries (if not installed with pygame)

```bash
# These should be installed as dependencies of python3-pygame
# Install manually if needed:
sudo apt install -y \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0
```

### Step 5: Audio Setup

```bash
# Ensure audio is working
sudo apt install -y pulseaudio alsa-utils

# Start PulseAudio (if not running)
pulseaudio --start

# Test audio
speaker-test -t wav -c 2 -l 1
```

### Step 6: Download BamBam Plus

```bash
# Option 1: Clone from GitHub
git clone https://github.com/YOUR_FORK/bambam.git
cd bambam

# Option 2: Download release
wget https://github.com/YOUR_FORK/bambam/archive/refs/heads/main.zip
unzip main.zip
cd bambam-main
```

### Step 7: Verify Installation

```bash
# Test Python syntax
python3 -m py_compile bambam.py bambam_tui.py

# Check dependencies
python3 bambam_tui.py --check

# Run TUI (if display is available)
python3 bambam_tui.py
```

## Running BamBam Plus

### Option 1: Direct Run (Development/Testing)

```bash
# Run with default settings
python3 bambam.py

# Run with extension
python3 bambam.py --extension alphanumeric-en_US

# Run with dark mode
python3 bambam.py --dark
```

### Option 2: Using TUI

```bash
# Launch configuration TUI
python3 bambam_tui.py

# Run directly with saved config
python3 bambam_tui.py --run
```

### Option 3: Secure Kiosk Mode (Recommended)

```bash
# Run in cage compositor
cage ./bambam_launcher.sh

# Or via TUI
python3 bambam_tui.py --cage
```

## Auto-Start Configuration

### Method 1: Systemd Service (Headless)

Create `/etc/systemd/system/bambam.service`:

```ini
[Unit]
Description=BamBam Children's Game
After=multi-user.target

[Service]
Type=simple
User=pi
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=WLR_LIBINPUT_NO_DEVICES=1
ExecStart=/usr/bin/cage /home/pi/bambam/bambam_launcher.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bambam.service
sudo systemctl start bambam.service
```

### Method 2: Auto-Login + Profile Script

Edit `/home/pi/.profile` and add at the end:

```bash
# Auto-start BamBam in cage on login
if [ -z "$WAYLAND_DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec cage /home/pi/bambam/bambam_launcher.sh
fi
```

Configure auto-login:

```bash
sudo raspi-config
# Navigate to: System Options > Boot / Auto Login > Console Autologin
```

### Method 3: Display Manager Session

Copy session file:

```bash
sudo cp bambam-session.desktop /usr/share/wayland-sessions/
```

## Performance Optimization

### GPU Memory Split

```bash
sudo raspi-config
# Advanced Options > GPU Memory
# Set to 256MB for better graphics performance
```

### Disable Unnecessary Services

```bash
# Disable Bluetooth if not needed
sudo systemctl disable bluetooth

# Disable hciuart
sudo systemctl disable hciuart
```

### Overclock (Optional, with adequate cooling)

Add to `/boot/config.txt`:

```
# Conservative overclock for Pi 5
arm_freq=2800
gpu_freq=900
```

## Troubleshooting

### No Sound

```bash
# Check if PulseAudio is running
pulseaudio --check && echo "Running" || echo "Not running"

# Start PulseAudio
pulseaudio --start

# List audio devices
pactl list sinks short

# Set default sink
pactl set-default-sink <sink_name>
```

### Display Issues

```bash
# Check current display configuration
wlr-randr

# Force specific resolution in cage
cage -d -- ./bambam_launcher.sh
```

### Permission Errors

```bash
# Add user to required groups
sudo usermod -aG video,audio,input,render pi

# Reboot for changes to take effect
sudo reboot
```

### Game Won't Start

```bash
# Check for Python errors
python3 bambam.py --trace

# Verify dependencies
python3 -c "import pygame; print(pygame.version.ver)"
python3 -c "import yaml; print(yaml.__version__)"
```

## Memory Usage

| Component | Approximate Memory |
|-----------|-------------------|
| Base system (Lite) | ~150MB |
| Cage compositor | ~30MB |
| Python + pygame | ~80MB |
| BamBam loaded | ~100-200MB |
| **Total** | ~400-500MB |

Pi 5 with 4GB RAM has ample headroom for this application.

## Security Considerations

1. **Use cage compositor**: Prevents child from accessing desktop
2. **Enable swaylock**: Locks screen if child somehow quits
3. **Disable virtual terminal switching**: Add to `/etc/X11/xorg.conf.d/`:

```
Section "ServerFlags"
    Option "DontVTSwitch" "true"
EndSection
```

Or copy the included configuration:

```bash
sudo cp 50-dont-vt-switch.conf /etc/X11/xorg.conf.d/
```

4. **Create dedicated user**: Run as non-privileged user
5. **Disable network**: If not needed, disable WiFi/Ethernet

## Updating BamBam Plus

```bash
cd ~/bambam
git pull origin main

# Or for clean update
cd ~
rm -rf bambam
git clone https://github.com/YOUR_FORK/bambam.git
```

## Uninstalling

```bash
# Remove systemd service
sudo systemctl stop bambam.service
sudo systemctl disable bambam.service
sudo rm /etc/systemd/system/bambam.service

# Remove BamBam directory
rm -rf ~/bambam

# Optional: Remove dependencies
sudo apt remove python3-pygame python3-yaml cage swaylock
```

---

*Last Updated: 2026-01-05*
