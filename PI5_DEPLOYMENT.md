# BamBam Plus - Raspberry Pi 5 Lite Deployment Guide

This guide covers installation and configuration of BamBam Plus on Raspberry Pi 5 running Raspberry Pi OS Lite (no desktop).

## Prerequisites

- Raspberry Pi 5 (4GB or 8GB recommended)
- Raspberry Pi OS Lite (64-bit) - Bookworm or later
- MicroSD card (16GB minimum, Class 10 or better)
- Audio output (HDMI, USB audio adapter, or headphone jack)
- Display connected via HDMI

## Quick Install

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install core dependencies
sudo apt install -y \
    python3 \
    python3-pygame \
    python3-yaml \
    cage \
    pulseaudio \
    alsa-utils

# Clone BamBam Plus (or copy files)
git clone https://github.com/YOUR_FORK/bambam.git
cd bambam

# Test run (will fail without display, just checking dependencies)
python3 -c "import pygame; import yaml; print('Dependencies OK')"

# Make TUI launcher executable
chmod +x bambam_tui.py bambam_config.py
```

## Package Verification

All dependencies are available via apt on Raspberry Pi OS:

| Package | apt Package | Version |
|---------|-------------|---------|
| Python 3 | `python3` | 3.11+ |
| pygame | `python3-pygame` | 2.x |
| PyYAML | `python3-yaml` | 6.x |
| cage | `cage` | 0.1.x |

### Alternative: pip Installation

If apt packages are too old:

```bash
sudo apt install -y python3-pip python3-venv
python3 -m venv ~/.venv/bambam
source ~/.venv/bambam/bin/activate
pip install pygame pyyaml
```

## Display Setup

### DRM/KMS (Recommended for Pi 5)

Pi 5 uses KMS/DRM for graphics. Ensure:

```bash
# Check KMS is enabled
sudo raspi-config
# Advanced Options → GL Driver → G2 GL (Fake KMS) or G1 GL (Full KMS)
```

### Cage Compositor Setup

Cage is a single-application Wayland compositor, perfect for kiosk mode:

```bash
# Test cage with a simple app
cage -- foot  # (if foot terminal is installed)

# Run BamBam in cage
cage -- python3 /path/to/bambam.py
```

## Auto-Start Configuration

### Method 1: systemd Service (Recommended)

Create `/etc/systemd/system/bambam.service`:

```ini
[Unit]
Description=BamBam Plus Kids Game
After=multi-user.target
Wants=pulseaudio.service

[Service]
Type=simple
User=pi
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=HOME=/home/pi
WorkingDirectory=/home/pi/bambam
ExecStart=/usr/bin/cage -- /usr/bin/python3 /home/pi/bambam/bambam.py
Restart=on-failure
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

### Method 2: /etc/rc.local

Add before `exit 0`:

```bash
su - pi -c 'cage -- python3 /home/pi/bambam/bambam.py' &
```

### Method 3: User .profile

Add to `/home/pi/.profile`:

```bash
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec cage -- python3 /home/pi/bambam/bambam.py
fi
```

## Audio Configuration

### PulseAudio (Recommended)

```bash
# Install PulseAudio
sudo apt install -y pulseaudio pulseaudio-utils

# Start PulseAudio for user
pulseaudio --start

# Test audio
paplay /usr/share/sounds/alsa/Front_Center.wav
```

### ALSA Only (Lower latency)

```bash
# Check sound cards
aplay -l

# Set default card in /etc/asound.conf or ~/.asoundrc
defaults.pcm.card 0
defaults.ctl.card 0

# Test
aplay /usr/share/sounds/alsa/Front_Center.wav
```

### HDMI Audio

```bash
# Force HDMI audio output
sudo raspi-config
# System Options → Audio → HDMI

# Or via config.txt
echo "hdmi_drive=2" | sudo tee -a /boot/firmware/config.txt
```

## Performance Optimizations

### Memory Allocation

Edit `/boot/firmware/config.txt`:

```ini
# Increase GPU memory for pygame
gpu_mem=128

# Enable hardware acceleration
dtoverlay=vc4-kms-v3d
```

### Reduce CPU Usage

The TUI launcher and config system are lightweight. For the main game:

1. Use `--deterministic-sounds` for faster sound selection
2. Pre-load sounds (already implemented in bambam.py)
3. Use compressed images (PNG over TIFF)

### Swap Configuration

```bash
# Increase swap for Pi 5 (4GB models)
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## TUI Launcher Usage

The TUI launcher provides an easy configuration interface:

```bash
# Interactive menu
./bambam_tui.py

# Run with saved config
./bambam_tui.py --run

# Run in cage compositor
./bambam_tui.py --run-cage

# List extensions
./bambam_tui.py --list-ext
```

### Configuration File

Settings are stored in `~/.config/bambam/config.yaml`:

```yaml
display:
  dark_mode: false
  background_image: null
  uppercase: false
audio:
  start_muted: false
  deterministic_sounds: false
mode:
  active_extension: alphanumeric-en_US
  all_modes_enabled: false
auto_switch:
  enabled: false
  mode_change_range: [10, 50]
  background_change_range: [20, 100]
launcher:
  use_cage: true
  sticky_mouse: false
```

## Troubleshooting

### No Display Output

```bash
# Check KMS driver
ls /dev/dri/card*

# Check cage logs
journalctl -u bambam.service -f

# Test with Xvfb (for debugging)
sudo apt install xvfb
xvfb-run python3 bambam.py
```

### No Sound

```bash
# Check PulseAudio
pulseaudio --check && echo "Running" || echo "Not running"
pulseaudio --start

# Check ALSA
amixer sset Master unmute
amixer sset Master 80%

# Check pygame mixer
python3 -c "import pygame; pygame.mixer.init(); print('Mixer OK')"
```

### pygame Import Error

```bash
# Install SDL dependencies
sudo apt install -y libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0

# Reinstall pygame
sudo apt install --reinstall python3-pygame
```

### High CPU Usage

```bash
# Check with htop
htop

# Reduce frame rate (edit bambam.py)
# Change clock.tick(60) to clock.tick(30)
```

## Security Considerations

### Dedicated User

```bash
# Create dedicated bambam user
sudo useradd -m -s /bin/bash bambam
sudo usermod -a -G video,audio,input bambam

# Set ownership
sudo chown -R bambam:bambam /home/bambam/bambam
```

### Disable VT Switching

Copy `50-dont-vt-switch.conf` to prevent Ctrl+Alt+Fx:

```bash
sudo cp 50-dont-vt-switch.conf /etc/X11/xorg.conf.d/
```

### Auto-Login (for kiosk mode)

```bash
sudo raspi-config
# System Options → Boot / Auto Login → Console Autologin
```

## Extension Installation

Place custom extensions in:
- `/home/pi/.local/share/bambam/extensions/`
- `/home/pi/bambam/extensions/`

Each extension needs:
```
extension-name/
├── event_map.yaml
└── sounds/
    └── *.ogg
```

## Verification Checklist

- [ ] Python 3.9+ installed
- [ ] pygame imports without error
- [ ] PyYAML imports without error  
- [ ] cage starts correctly
- [ ] Audio plays through correct device
- [ ] Display resolution detected properly
- [ ] Auto-start works on boot
- [ ] VT switching disabled (optional)
- [ ] TUI launcher shows menu
- [ ] Configuration saves correctly

## Support

- GitHub Issues: [repository issues page]
- BamBam Users Forum: https://groups.google.com/forum/#!forum/bambam-users
