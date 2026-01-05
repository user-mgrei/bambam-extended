#!/bin/bash
# BamBam Plus Cage Launcher Script
# This script runs BamBam in a secure cage compositor environment
# with optional swaylock protection when the game exits.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAMBAM_PY="$SCRIPT_DIR/bambam.py"
CONFIG_FILE="$HOME/.config/bambam/config.yaml"

# Default settings
USE_SWAYLOCK=true
EXTENSION=""
DARK_MODE=false
UPPERCASE=false
MUTE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-swaylock)
            USE_SWAYLOCK=false
            shift
            ;;
        --extension|-e)
            EXTENSION="$2"
            shift 2
            ;;
        --dark|-D)
            DARK_MODE=true
            shift
            ;;
        --uppercase|-u)
            UPPERCASE=true
            shift
            ;;
        --mute|-m)
            MUTE=true
            shift
            ;;
        --help|-h)
            echo "BamBam Plus Cage Launcher"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-swaylock     Don't run swaylock after game exits"
            echo "  -e, --extension   Use specified extension"
            echo "  -D, --dark        Use dark background"
            echo "  -u, --uppercase   Show uppercase letters"
            echo "  -m, --mute        Start muted"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "This script is designed to be run within cage compositor:"
            echo "  cage $0"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build BamBam command
BAMBAM_CMD="python3 $BAMBAM_PY --wayland-ok"

if [[ -n "$EXTENSION" ]]; then
    BAMBAM_CMD="$BAMBAM_CMD --extension $EXTENSION"
fi

if [[ "$DARK_MODE" == "true" ]]; then
    BAMBAM_CMD="$BAMBAM_CMD --dark"
fi

if [[ "$UPPERCASE" == "true" ]]; then
    BAMBAM_CMD="$BAMBAM_CMD --uppercase"
fi

if [[ "$MUTE" == "true" ]]; then
    BAMBAM_CMD="$BAMBAM_CMD --mute"
fi

# Run BamBam
echo "Starting BamBam Plus..."
$BAMBAM_CMD

# Run swaylock if enabled (to prevent child from accessing desktop after quit)
if [[ "$USE_SWAYLOCK" == "true" ]] && command -v swaylock &> /dev/null; then
    echo "Game exited. Locking screen..."
    swaylock
fi
