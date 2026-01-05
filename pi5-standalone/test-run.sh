#!/bin/bash
# BamBam Test Runner
# Quick test script for the standalone installation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"
CONFIG_DIR="${HOME}/.config/bambam-test"

# Export environment for isolated config
export BAMBAM_CONFIG_DIR="$CONFIG_DIR"
export BAMBAM_TEST_MODE=1

echo "=========================================="
echo "BamBam Test Runner"
echo "=========================================="
echo "Install dir: $INSTALL_DIR"
echo "Config dir:  $CONFIG_DIR"
echo ""

# Check if bambam.py exists
if [[ ! -f "$INSTALL_DIR/bambam.py" ]]; then
    echo "Error: bambam.py not found in $INSTALL_DIR"
    echo "Please run install.sh first or copy bambam.py manually."
    exit 1
fi

# Parse arguments
BAMBAM_ARGS=()
TRACE=false
EXTENSION=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --trace) TRACE=true; BAMBAM_ARGS+=("--trace"); shift ;;
        -e|--extension) EXTENSION="$2"; BAMBAM_ARGS+=("--extension" "$2"); shift 2 ;;
        --dark) BAMBAM_ARGS+=("--dark"); shift ;;
        --mute) BAMBAM_ARGS+=("--mute"); shift ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --trace           Enable debug logging"
            echo "  -e, --extension   Use specific extension"
            echo "  --dark            Dark mode"
            echo "  --mute            Start muted"
            echo "  --help            Show this help"
            exit 0
            ;;
        *) BAMBAM_ARGS+=("$1"); shift ;;
    esac
done

# Show what we're running
echo "Running: python3 bambam.py ${BAMBAM_ARGS[*]}"
echo ""
echo "Controls:"
echo "  - Type 'quit' to exit"
echo "  - Type 'sound' to toggle sound"
echo "  - Type 'mute' / 'unmute' for audio control"
echo ""

cd "$INSTALL_DIR"
exec python3 bambam.py "${BAMBAM_ARGS[@]}"
