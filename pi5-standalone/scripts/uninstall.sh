#!/bin/bash
# BamBam Test Installation Uninstaller
# Removes the standalone test installation without affecting system bambam

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/bambam-test"
CONFIG_DIR="${HOME}/.config/bambam-test"
SYMLINK="${HOME}/.local/bin/bambam-test"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}BamBam Test Installation Uninstaller${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Confirm uninstallation
echo -e "${YELLOW}This will remove:${NC}"
echo "  - $INSTALL_DIR"
echo "  - $CONFIG_DIR"
echo "  - $SYMLINK"
echo ""
echo -e "${GREEN}Your system BamBam installation (if any) will NOT be affected.${NC}"
echo ""

read -p "Are you sure you want to uninstall? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove installation directory
if [[ -d "$INSTALL_DIR" ]]; then
    echo -e "\n${BLUE}Removing installation directory...${NC}"
    sudo rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}✓ Removed $INSTALL_DIR${NC}"
else
    echo -e "${YELLOW}⚠ Installation directory not found${NC}"
fi

# Remove config directory (ask first)
if [[ -d "$CONFIG_DIR" ]]; then
    echo ""
    read -p "Remove configuration files too? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        echo -e "${GREEN}✓ Removed $CONFIG_DIR${NC}"
    else
        echo -e "${YELLOW}Configuration preserved at $CONFIG_DIR${NC}"
    fi
fi

# Remove symlink
if [[ -L "$SYMLINK" ]]; then
    rm -f "$SYMLINK"
    echo -e "${GREEN}✓ Removed symlink $SYMLINK${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "The test installation has been removed."
echo "Your system BamBam installation (if any) is unchanged."
