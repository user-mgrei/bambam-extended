#!/bin/bash
# BamBam TUI Configuration Menu Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SCRIPT_DIR}"
CONFIG_DIR="${HOME}/.config/bambam-test"

# Export environment
export BAMBAM_CONFIG_DIR="$CONFIG_DIR"
export BAMBAM_TEST_MODE=1

echo "=========================================="
echo "BamBam Configuration Menu"
echo "=========================================="

# Check if TUI exists
if [[ -f "$INSTALL_DIR/bambam_tui.py" ]]; then
    echo "Starting TUI configuration..."
    cd "$INSTALL_DIR"
    exec python3 bambam_tui.py "$@"
else
    echo ""
    echo "TUI configuration menu not yet implemented."
    echo ""
    echo "Manual configuration options:"
    echo ""
    echo "Run with dark mode:"
    echo "  ./test-run.sh --dark"
    echo ""
    echo "Run with extension:"
    echo "  ./test-run.sh --extension alphanumeric-en_US"
    echo ""
    echo "Run muted:"
    echo "  ./test-run.sh --mute"
    echo ""
    echo "Run with uppercase letters:"
    echo "  ./test-run.sh --uppercase"
    echo ""
    echo "Combine options:"
    echo "  ./test-run.sh --dark --extension alphanumeric-en_US --trace"
    echo ""
    echo "Available extensions:"
    if [[ -d "$INSTALL_DIR/extensions" ]]; then
        for ext in "$INSTALL_DIR/extensions"/*/; do
            if [[ -f "${ext}event_map.yaml" ]]; then
                echo "  - $(basename "$ext")"
            fi
        done
    else
        echo "  (none found)"
    fi
    echo ""
    echo "Edit configuration manually:"
    echo "  nano $CONFIG_DIR/config.yaml"
fi
