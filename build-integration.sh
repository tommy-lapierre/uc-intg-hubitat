#!/bin/bash
# Build integration package for Unfolded Circle Remote 3
# This creates a compiled aarch64 package suitable for local installation

set -e  # Exit on error

VERSION="0.2.0"
DRIVER_ID="hubitat"
ARTIFACT_NAME="uc-intg-${DRIVER_ID}-${VERSION}-aarch64"

echo "======================================"
echo "Building UC Integration Package"
echo "Driver: ${DRIVER_ID}"
echo "Version: ${VERSION}"
echo "======================================"
echo ""

# Clean previous builds
echo "→ Cleaning previous builds..."
rm -rf dist/ build/ artifacts/
rm -f *.tar.gz *.sha256

# Step 1: Build with PyInstaller using UC's Docker image
echo "→ Building with PyInstaller (aarch64)..."
echo "  This may take a few minutes..."

# Convert Windows path to Docker format if needed
WORK_DIR="$(pwd)"
if [[ "$WORK_DIR" == /c/* ]]; then
  WORK_DIR="$(echo $WORK_DIR | sed 's|^/c|C:|')"
fi

MSYS_NO_PATHCONV=1 docker run --rm --name uc-integration-builder \
  --platform=linux/arm64 \
  -v "${WORK_DIR}:/workspace" \
  -w /workspace \
  docker.io/unfoldedcircle/r2-pyinstaller:3.11.6 \
  bash -c "python -m pip install --quiet --upgrade pip && \
    python -m pip install --quiet -r requirements.txt && \
    pyinstaller --clean --onedir --name driver intg-hubitat/driver.py"

if [ ! -d "dist/driver" ]; then
    echo "✗ PyInstaller build failed - dist/driver not found"
    exit 1
fi

echo "✓ Compilation complete"
echo ""

# Step 2: Prepare artifacts directory
echo "→ Preparing package structure..."
mkdir -p artifacts/bin

# Step 3: Move compiled driver to bin/
cp -r dist/driver/* artifacts/bin/

# Step 4: Copy driver.json to root (REQUIRED at root level)
cp intg-hubitat/driver.json artifacts/

# Step 5: Copy README to root (optional but helpful)
cp README.md artifacts/

# Note: Custom icon would go here if you have one
# cp hubitat.png artifacts/

echo "✓ Package structure prepared"
echo ""

# Step 6: Create tar.gz archive (with root starting at artifacts/)
echo "→ Creating tar.gz archive..."
tar czf "${ARTIFACT_NAME}.tar.gz" -C artifacts .

if [ ! -f "${ARTIFACT_NAME}.tar.gz" ]; then
    echo "✗ Failed to create archive"
    exit 1
fi

# Step 7: Generate SHA256 checksum
echo "→ Generating checksum..."
sha256sum "${ARTIFACT_NAME}.tar.gz" > "${ARTIFACT_NAME}.tar.gz.sha256"

# Display results
SIZE=$(ls -lh "${ARTIFACT_NAME}.tar.gz" | awk '{print $5}')
echo ""
echo "======================================"
echo "✓ Package created successfully!"
echo "======================================"
echo "File: ${ARTIFACT_NAME}.tar.gz"
echo "Size: ${SIZE}"
echo ""
echo "Package contents:"
tar -tzf "${ARTIFACT_NAME}.tar.gz" | head -20
TOTAL=$(tar -tzf "${ARTIFACT_NAME}.tar.gz" | wc -l)
echo "... (${TOTAL} total files)"
echo ""
echo "SHA256: $(cat ${ARTIFACT_NAME}.tar.gz.sha256 | awk '{print $1}')"
echo ""
echo "======================================"
echo "Installation Instructions:"
echo "======================================"
echo "1. Go to http://[REMOTE-IP] in your browser"
echo "2. Navigate to Integrations menu"
echo "3. Click 'Add new / Install custom'"
echo "4. Upload: ${ARTIFACT_NAME}.tar.gz"
echo ""
echo "Or use REST API:"
echo "curl --location 'http://[REMOTE-IP]/api/intg/install' \\"
echo "  --user 'web-configurator:[PIN]' \\"
echo "  --form 'file=@\"${ARTIFACT_NAME}.tar.gz\"'"
echo ""
