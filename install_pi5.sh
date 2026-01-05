#!/bin/bash
# BamBam Plus Installation Script for Raspberry Pi 5 Lite
# Optimized for apt package manager

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         BamBam Plus - Raspberry Pi 5 Lite Installer        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root for system-wide install
if [ "$EUID" -eq 0 ]; then
    INSTALL_MODE="system"
    INSTALL_DIR="/usr/share/bambam"
    BIN_DIR="/usr/local/bin"
else
    INSTALL_MODE="user"
    INSTALL_DIR="$HOME/.local/share/bambam"
    BIN_DIR="$HOME/.local/bin"
fi

echo "[INFO] Installation mode: $INSTALL_MODE"
echo "[INFO] Install directory: $INSTALL_DIR"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update package lists
echo "[STEP 1/6] Updating package lists..."
if [ "$EUID" -eq 0 ]; then
    apt-get update -qq
else
    echo "[INFO] Skipping apt update (requires root)"
fi

# Install system dependencies
echo "[STEP 2/6] Installing system dependencies..."
DEPS="python3 python3-pygame python3-yaml"

# Optional but recommended for Wayland/cage support
OPTIONAL_DEPS="cage wlr-randr"

if [ "$EUID" -eq 0 ]; then
    apt-get install -y $DEPS

    echo "[INFO] Installing optional dependencies (cage for secure sessions)..."
    apt-get install -y $OPTIONAL_DEPS || echo "[WARN] Some optional deps not available"
else
    echo "[INFO] Please install dependencies manually:"
    echo "       sudo apt install $DEPS"
    echo "       sudo apt install $OPTIONAL_DEPS  # optional"
fi

# Check Python version
echo "[STEP 3/6] Checking Python version..."
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[INFO] Python version: $PYTHON_VERSION"

# Verify pygame is installed
echo "[STEP 4/6] Verifying pygame installation..."
if python3 -c "import pygame" 2>/dev/null; then
    PYGAME_VERSION=$(python3 -c "import pygame; print(pygame.version.ver)")
    echo "[INFO] pygame version: $PYGAME_VERSION"
else
    echo "[ERROR] pygame not installed!"
    echo "        Run: sudo apt install python3-pygame"
    exit 1
fi

# Verify pyyaml is installed
if python3 -c "import yaml" 2>/dev/null; then
    echo "[INFO] PyYAML is available"
else
    echo "[WARN] PyYAML not installed. Extensions will be disabled."
    echo "       Run: sudo apt install python3-yaml"
fi

# Create installation directories
echo "[STEP 5/6] Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/extensions"
mkdir -p "$INSTALL_DIR/backgrounds"
mkdir -p "$BIN_DIR"

# Create config directory
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/bambam"

# Copy files
echo "[STEP 6/6] Installing BamBam Plus..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy main files
cp "$SCRIPT_DIR/bambam.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/bambam_tui.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/bambam_config.py" "$INSTALL_DIR/"

# Copy data files
if [ -d "$SCRIPT_DIR/data" ]; then
    cp -r "$SCRIPT_DIR/data/"* "$INSTALL_DIR/data/"
fi

# Copy extensions
if [ -d "$SCRIPT_DIR/extensions" ]; then
    cp -r "$SCRIPT_DIR/extensions/"* "$INSTALL_DIR/extensions/"
fi

# Create launcher scripts
cat > "$BIN_DIR/bambam" << 'EOF'
#!/bin/bash
# BamBam Plus launcher
BAMBAM_DIR="${BAMBAM_DIR:-/usr/share/bambam}"
if [ ! -d "$BAMBAM_DIR" ]; then
    BAMBAM_DIR="$HOME/.local/share/bambam"
fi
exec python3 "$BAMBAM_DIR/bambam.py" "$@"
EOF
chmod +x "$BIN_DIR/bambam"

cat > "$BIN_DIR/bambam-tui" << 'EOF'
#!/bin/bash
# BamBam Plus TUI launcher
BAMBAM_DIR="${BAMBAM_DIR:-/usr/share/bambam}"
if [ ! -d "$BAMBAM_DIR" ]; then
    BAMBAM_DIR="$HOME/.local/share/bambam"
fi
exec python3 "$BAMBAM_DIR/bambam_tui.py" "$@"
EOF
chmod +x "$BIN_DIR/bambam-tui"

# Create cage launcher for secure sessions
cat > "$BIN_DIR/bambam-cage" << 'EOF'
#!/bin/bash
# BamBam Plus launcher with cage (secure Wayland session)
BAMBAM_DIR="${BAMBAM_DIR:-/usr/share/bambam}"
if [ ! -d "$BAMBAM_DIR" ]; then
    BAMBAM_DIR="$HOME/.local/share/bambam"
fi

if command -v cage >/dev/null 2>&1; then
    exec cage -- python3 "$BAMBAM_DIR/bambam.py" "$@"
else
    echo "Cage not installed. Run: sudo apt install cage"
    echo "Falling back to regular mode..."
    exec python3 "$BAMBAM_DIR/bambam.py" "$@"
fi
EOF
chmod +x "$BIN_DIR/bambam-cage"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                 Installation Complete!                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Usage:"
echo "  bambam          - Start BamBam directly"
echo "  bambam-tui      - Start TUI configuration menu"
echo "  bambam-cage     - Start BamBam in secure cage session"
echo ""
echo "Configuration file: ~/.config/bambam/config.json"
echo "Custom backgrounds: ~/.local/share/bambam/backgrounds/"
echo ""

# Add to PATH reminder for user installs
if [ "$INSTALL_MODE" = "user" ]; then
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "[NOTE] Add $BIN_DIR to your PATH:"
        echo "       echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        echo ""
    fi
fi

echo "Enjoy BamBam Plus! 🎮"
