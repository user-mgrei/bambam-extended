#!/bin/bash
# Build Pi 5 Standalone Package
# Creates a complete standalone package ready to deploy to Pi 5

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGE_DIR="$REPO_ROOT/pi5-standalone"

echo "=========================================="
echo "Building Pi 5 Standalone Package"
echo "=========================================="
echo "Source: $REPO_ROOT"
echo "Target: $PACKAGE_DIR"
echo ""

# Create package directory structure
echo "Creating directory structure..."
mkdir -p "$PACKAGE_DIR"/{scripts,config,docs,data,extensions,backgrounds}

# Copy main Python files
echo "Copying Python files..."
cp -v "$REPO_ROOT/bambam.py" "$PACKAGE_DIR/"

# Copy TUI if it exists
if [[ -f "$REPO_ROOT/bambam_tui.py" ]]; then
    cp -v "$REPO_ROOT/bambam_tui.py" "$PACKAGE_DIR/"
fi

# Copy requirements
echo "Copying requirements..."
cp -v "$REPO_ROOT/requirements.txt" "$PACKAGE_DIR/"

# Copy data directory
echo "Copying data assets..."
if [[ -d "$REPO_ROOT/data" ]]; then
    cp -rv "$REPO_ROOT/data/"* "$PACKAGE_DIR/data/"
fi

# Copy extensions
echo "Copying extensions..."
if [[ -d "$REPO_ROOT/extensions" ]]; then
    cp -rv "$REPO_ROOT/extensions/"* "$PACKAGE_DIR/extensions/"
fi

# Copy icon
if [[ -f "$REPO_ROOT/icon.gif" ]]; then
    cp -v "$REPO_ROOT/icon.gif" "$PACKAGE_DIR/"
fi

# Copy documentation
echo "Copying documentation..."
for doc in PI5_COMPATIBILITY.md CODEBASE_REFERENCE.md TUI_IMPLEMENTATION_GUIDE.md NEW_FEATURES_GUIDE.md; do
    if [[ -f "$REPO_ROOT/docs/$doc" ]]; then
        cp -v "$REPO_ROOT/docs/$doc" "$PACKAGE_DIR/docs/"
    fi
done

# Copy fact check script
echo "Copying scripts..."
if [[ -f "$REPO_ROOT/scripts/fact_check.py" ]]; then
    cp -v "$REPO_ROOT/scripts/fact_check.py" "$PACKAGE_DIR/scripts/"
fi

# Make scripts executable
echo "Setting permissions..."
chmod +x "$PACKAGE_DIR"/*.sh 2>/dev/null || true
chmod +x "$PACKAGE_DIR"/*.py 2>/dev/null || true
chmod +x "$PACKAGE_DIR/scripts"/*.sh 2>/dev/null || true
chmod +x "$PACKAGE_DIR/scripts"/*.py 2>/dev/null || true

# Run fact check on package
echo ""
echo "Running fact check on package..."
if [[ -f "$PACKAGE_DIR/scripts/fact_check.py" ]]; then
    cd "$PACKAGE_DIR"
    python3 scripts/fact_check.py --root . || echo "Fact check completed with warnings"
fi

# Calculate package size
PACKAGE_SIZE=$(du -sh "$PACKAGE_DIR" | cut -f1)

echo ""
echo "=========================================="
echo "Package Build Complete!"
echo "=========================================="
echo ""
echo "Package location: $PACKAGE_DIR"
echo "Package size: $PACKAGE_SIZE"
echo ""
echo "Contents:"
find "$PACKAGE_DIR" -type f | head -30
TOTAL_FILES=$(find "$PACKAGE_DIR" -type f | wc -l)
echo "... ($TOTAL_FILES files total)"
echo ""
echo "To deploy to Pi 5:"
echo "  scp -r $PACKAGE_DIR pi@<your-pi-ip>:~/bambam-test/"
echo ""
echo "Or create a tarball:"
echo "  tar -czvf bambam-pi5-test.tar.gz -C $(dirname $PACKAGE_DIR) $(basename $PACKAGE_DIR)"
