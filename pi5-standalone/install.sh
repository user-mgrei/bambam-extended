#!/bin/bash
# BamBam Pi 5 Standalone Test Installation Script
# This installs to /opt/bambam-test/ - isolated from any system bambam

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths (isolated from system)
INSTALL_DIR="/opt/bambam-test"
CONFIG_DIR="${HOME}/.config/bambam-test"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
REINSTALL_DEPS=false
UPDATE_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --reinstall-deps) REINSTALL_DEPS=true; shift ;;
        --update) UPDATE_ONLY=true; shift ;;
        --help) 
            echo "Usage: $0 [--reinstall-deps] [--update]"
            echo "  --reinstall-deps  Force reinstall of apt dependencies"
            echo "  --update          Update files only, skip dependency check"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}BamBam Pi 5 Standalone Test Installation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Install directory: ${GREEN}${INSTALL_DIR}${NC}"
echo -e "Config directory:  ${GREEN}${CONFIG_DIR}${NC}"
echo ""

# Check if running on Pi
check_pi() {
    if [[ -f /proc/device-tree/model ]]; then
        model=$(cat /proc/device-tree/model)
        echo -e "${GREEN}Detected: ${model}${NC}"
        if [[ "$model" == *"Raspberry Pi 5"* ]]; then
            echo -e "${GREEN}✓ Raspberry Pi 5 detected${NC}"
            return 0
        fi
    fi
    echo -e "${YELLOW}⚠ Not running on Raspberry Pi 5 (proceeding anyway)${NC}"
    return 0
}

# Install apt dependencies
install_deps() {
    echo -e "\n${BLUE}Installing system dependencies...${NC}"
    
    local packages=(
        "python3"
        "python3-pip"
        "python3-pygame"
        "python3-yaml"
        "python3-urwid"
        "cage"
        "alsa-utils"
    )
    
    # Check which packages need installation
    local to_install=()
    for pkg in "${packages[@]}"; do
        if ! dpkg -l "$pkg" &>/dev/null || $REINSTALL_DEPS; then
            to_install+=("$pkg")
        fi
    done
    
    if [[ ${#to_install[@]} -gt 0 ]]; then
        echo "Installing: ${to_install[*]}"
        sudo apt-get update
        sudo apt-get install -y "${to_install[@]}"
    else
        echo -e "${GREEN}✓ All dependencies already installed${NC}"
    fi
}

# Create installation directory
setup_install_dir() {
    echo -e "\n${BLUE}Setting up installation directory...${NC}"
    
    if [[ -d "$INSTALL_DIR" ]]; then
        echo -e "${YELLOW}Existing installation found, updating...${NC}"
    fi
    
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown -R "$USER:$USER" "$INSTALL_DIR"
}

# Copy files
copy_files() {
    echo -e "\n${BLUE}Copying files...${NC}"
    
    # Copy main files
    cp -v "${SCRIPT_DIR}/bambam.py" "$INSTALL_DIR/" 2>/dev/null || echo "bambam.py will be copied from repo"
    cp -v "${SCRIPT_DIR}/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true
    
    # Copy TUI if exists
    if [[ -f "${SCRIPT_DIR}/bambam_tui.py" ]]; then
        cp -v "${SCRIPT_DIR}/bambam_tui.py" "$INSTALL_DIR/"
    fi
    
    # Copy data directory
    if [[ -d "${SCRIPT_DIR}/data" ]]; then
        cp -rv "${SCRIPT_DIR}/data" "$INSTALL_DIR/"
    fi
    
    # Copy extensions
    if [[ -d "${SCRIPT_DIR}/extensions" ]]; then
        cp -rv "${SCRIPT_DIR}/extensions" "$INSTALL_DIR/"
    fi
    
    # Copy backgrounds
    if [[ -d "${SCRIPT_DIR}/backgrounds" ]]; then
        cp -rv "${SCRIPT_DIR}/backgrounds" "$INSTALL_DIR/"
    fi
    
    # Copy scripts
    mkdir -p "$INSTALL_DIR/scripts"
    cp -rv "${SCRIPT_DIR}/scripts/"* "$INSTALL_DIR/scripts/" 2>/dev/null || true
    
    # Copy docs
    mkdir -p "$INSTALL_DIR/docs"
    cp -rv "${SCRIPT_DIR}/docs/"* "$INSTALL_DIR/docs/" 2>/dev/null || true
    
    # Copy launcher scripts
    cp -v "${SCRIPT_DIR}/test-run.sh" "$INSTALL_DIR/" 2>/dev/null || true
    cp -v "${SCRIPT_DIR}/run-cage.sh" "$INSTALL_DIR/" 2>/dev/null || true
    cp -v "${SCRIPT_DIR}/run-tui.sh" "$INSTALL_DIR/" 2>/dev/null || true
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true
    chmod +x "$INSTALL_DIR"/*.py 2>/dev/null || true
    chmod +x "$INSTALL_DIR/scripts"/*.sh 2>/dev/null || true
    chmod +x "$INSTALL_DIR/scripts"/*.py 2>/dev/null || true
}

# Setup config directory
setup_config() {
    echo -e "\n${BLUE}Setting up configuration...${NC}"
    
    mkdir -p "$CONFIG_DIR"
    
    if [[ ! -f "$CONFIG_DIR/config.yaml" ]]; then
        if [[ -f "${SCRIPT_DIR}/config/default.yaml" ]]; then
            cp "${SCRIPT_DIR}/config/default.yaml" "$CONFIG_DIR/config.yaml"
        else
            # Create default config
            cat > "$CONFIG_DIR/config.yaml" << 'EOF'
# BamBam Test Configuration
version: 1

display:
  dark_mode: false
  uppercase: false

audio:
  start_muted: false

extension:
  name: null  # or "alphanumeric-en_US"
EOF
        fi
        echo -e "${GREEN}✓ Created default configuration${NC}"
    else
        echo -e "${GREEN}✓ Existing configuration preserved${NC}"
    fi
}

# Verify installation
verify_install() {
    echo -e "\n${BLUE}Verifying installation...${NC}"
    
    local errors=0
    
    # Check Python
    if python3 -c "import pygame; print(f'pygame {pygame.version.ver}')" 2>/dev/null; then
        echo -e "${GREEN}✓ pygame available${NC}"
    else
        echo -e "${RED}✗ pygame not available${NC}"
        ((errors++))
    fi
    
    # Check PyYAML
    if python3 -c "import yaml; print('PyYAML OK')" 2>/dev/null; then
        echo -e "${GREEN}✓ PyYAML available${NC}"
    else
        echo -e "${YELLOW}⚠ PyYAML not available (extensions disabled)${NC}"
    fi
    
    # Check urwid
    if python3 -c "import urwid; print('urwid OK')" 2>/dev/null; then
        echo -e "${GREEN}✓ urwid available (TUI enabled)${NC}"
    else
        echo -e "${YELLOW}⚠ urwid not available (TUI disabled)${NC}"
    fi
    
    # Check cage
    if command -v cage &>/dev/null; then
        echo -e "${GREEN}✓ cage available${NC}"
    else
        echo -e "${YELLOW}⚠ cage not available (kiosk mode disabled)${NC}"
    fi
    
    # Check bambam.py
    if [[ -f "$INSTALL_DIR/bambam.py" ]]; then
        echo -e "${GREEN}✓ bambam.py installed${NC}"
    else
        echo -e "${RED}✗ bambam.py not found${NC}"
        ((errors++))
    fi
    
    # Check data directory
    if [[ -d "$INSTALL_DIR/data" ]] && [[ -n "$(ls -A "$INSTALL_DIR/data" 2>/dev/null)" ]]; then
        echo -e "${GREEN}✓ data directory populated${NC}"
    else
        echo -e "${RED}✗ data directory empty or missing${NC}"
        ((errors++))
    fi
    
    return $errors
}

# Create convenience symlinks
create_symlinks() {
    echo -e "\n${BLUE}Creating convenience scripts...${NC}"
    
    # Create local bin directory
    mkdir -p "${HOME}/.local/bin"
    
    # Create symlink for easy access
    ln -sf "$INSTALL_DIR/test-run.sh" "${HOME}/.local/bin/bambam-test"
    
    echo -e "${GREEN}✓ Created ~/. local/bin/bambam-test${NC}"
    echo -e "${YELLOW}  (Make sure ~/.local/bin is in your PATH)${NC}"
}

# Main installation
main() {
    check_pi
    
    if ! $UPDATE_ONLY; then
        install_deps
    fi
    
    setup_install_dir
    copy_files
    setup_config
    
    if verify_install; then
        create_symlinks
        
        echo -e "\n${GREEN}========================================${NC}"
        echo -e "${GREEN}Installation Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "To test the installation:"
        echo -e "  ${BLUE}cd $INSTALL_DIR${NC}"
        echo -e "  ${BLUE}./test-run.sh${NC}"
        echo ""
        echo -e "For cage/kiosk mode (run from TTY, not SSH):"
        echo -e "  ${BLUE}./run-cage.sh${NC}"
        echo ""
        echo -e "To uninstall:"
        echo -e "  ${BLUE}$INSTALL_DIR/scripts/uninstall.sh${NC}"
    else
        echo -e "\n${RED}Installation completed with errors.${NC}"
        echo -e "Please check the messages above."
        exit 1
    fi
}

main "$@"
