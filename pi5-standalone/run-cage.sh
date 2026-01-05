#!/bin/bash
# BamBam Cage Kiosk Launcher
# Runs BamBam in Cage Wayland compositor for kiosk mode
#
# IMPORTANT: Run this from a TTY (Ctrl+Alt+F1), not from SSH or desktop!

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"
CONFIG_DIR="${HOME}/.config/bambam-test"

# Export environment
export BAMBAM_CONFIG_DIR="$CONFIG_DIR"
export BAMBAM_TEST_MODE=1
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Check if running from TTY
check_tty() {
    if [[ -n "$DISPLAY" ]] || [[ -n "$WAYLAND_DISPLAY" ]]; then
        echo "=========================================="
        echo "WARNING: Already in a graphical session!"
        echo "=========================================="
        echo ""
        echo "For proper kiosk mode, run this from a TTY:"
        echo "  1. Press Ctrl+Alt+F1 to switch to TTY1"
        echo "  2. Log in"
        echo "  3. Run: $0"
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check cage availability
check_cage() {
    if ! command -v cage &>/dev/null; then
        echo "Error: cage is not installed"
        echo "Install with: sudo apt install cage"
        exit 1
    fi
}

# Check DRM availability
check_drm() {
    if [[ ! -e /dev/dri/card0 ]]; then
        echo "Error: No DRM device found (/dev/dri/card0)"
        echo "Make sure you have proper GPU drivers installed."
        exit 1
    fi
    
    if [[ ! -r /dev/dri/card0 ]]; then
        echo "Error: Cannot read /dev/dri/card0"
        echo "Add user to video group: sudo usermod -aG video $USER"
        exit 1
    fi
}

# Main
main() {
    echo "=========================================="
    echo "BamBam Cage Kiosk Mode"
    echo "=========================================="
    
    check_tty
    check_cage
    check_drm
    
    # Check bambam.py
    if [[ ! -f "$INSTALL_DIR/bambam.py" ]]; then
        echo "Error: bambam.py not found"
        exit 1
    fi
    
    echo ""
    echo "Starting BamBam in Cage..."
    echo "To exit: Type 'quit' in the game"
    echo ""
    
    # Build arguments
    BAMBAM_ARGS=("--wayland-ok")
    
    # Add any passed arguments
    BAMBAM_ARGS+=("$@")
    
    cd "$INSTALL_DIR"
    
    # Run in cage
    # --keyboard-shortcuts allows some control (optional)
    exec cage -- python3 bambam.py "${BAMBAM_ARGS[@]}"
}

main "$@"
