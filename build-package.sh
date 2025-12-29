#!/bin/bash
# Build integration package for Unfolded Circle Remote

VERSION="0.1.0"
PACKAGE_NAME="uc-intg-hubitat-${VERSION}.tar.gz"

echo "Building ${PACKAGE_NAME}..."

# Create tar.gz package with only necessary files
tar -czf "${PACKAGE_NAME}" \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='venv' \
  --exclude='test_hubitat.py' \
  --exclude='check_thermostat.py' \
  --exclude='config.json' \
  --exclude='*.log' \
  --exclude='.claude' \
  --exclude='CLAUDE.md' \
  --exclude='Dockerfile' \
  --exclude='.dockerignore' \
  --exclude='docker-compose.yml' \
  --exclude='*.tar.gz' \
  --exclude='build-package.sh' \
  intg-hubitat/ requirements.txt README.md

if [ -f "${PACKAGE_NAME}" ]; then
    SIZE=$(ls -lh "${PACKAGE_NAME}" | awk '{print $5}')
    echo "✓ Package created: ${PACKAGE_NAME} (${SIZE})"
    echo ""
    echo "Contents:"
    tar -tzf "${PACKAGE_NAME}"
else
    echo "✗ Failed to create package"
    exit 1
fi
