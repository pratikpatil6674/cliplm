#!/usr/bin/env bash

set -euo pipefail

source "$(dirname "$0")/packaging_common.sh"
load_dotenv

# Build a Debian package from the current source tree.
# The script intentionally uses a lightweight package-root layout rather than a
# full debhelper workflow so it stays easy to reason about in this repo.

PROJECT_VERSION="$(project_version)"
DEB_BUILD_DIR="$BUILD_DIR/deb"
PACKAGE_ROOT="$DEB_BUILD_DIR/package-root"

PACKAGE_NAME="${APP_NAME}_${PROJECT_VERSION}_${ARCH}"
PACKAGE_PATH="$DIST_DIR/${PACKAGE_NAME}.deb"
CONTROL_FILE="$PACKAGE_ROOT/DEBIAN/control"
DESKTOP_FILE="$PACKAGE_ROOT/usr/share/applications/${APP_NAME}.desktop"
ICON_TARGET="$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps/${APP_NAME}.svg"
BIN_TARGET="$PACKAGE_ROOT/usr/bin/${APP_NAME}"

echo "Cleaning previous Debian build output..."
rm -rf "$DEB_BUILD_DIR" "$PACKAGE_PATH"
mkdir -p \
    "$PACKAGE_ROOT/DEBIAN" \
    "$(dirname "$BIN_TARGET")" \
    "$(dirname "$DESKTOP_FILE")" \
    "$(dirname "$ICON_TARGET")" \
    "$DIST_DIR"

if [[ "${REBUILD_NUITKA_BINARY:-1}" == "1" ]]; then
    build_nuitka_binary
fi

echo "Staging package files..."
install -Dm755 "$NUITKA_BINARY_PATH" "$BIN_TARGET"
install -Dm644 "$ICON_SOURCE" "$ICON_TARGET"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_DISPLAY_NAME}
Exec=/usr/bin/${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Categories=Utility;
EOF

cat > "$CONTROL_FILE" <<EOF
Package: ${APP_NAME}
Version: ${PROJECT_VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Pratik Patil
Depends: libc6, libegl1, libfontconfig1, libfreetype6, libgl1, libstdc++6, libwayland-client0, libx11-6, libxcb-cursor0, libxcb1, libxkbcommon0
Description: AI-powered clipboard manager with custom prompts
 ClipLM is a desktop clipboard history manager with AI and translation tools.
EOF

chmod 0755 "$PACKAGE_ROOT/DEBIAN"
chmod 0644 "$CONTROL_FILE" "$DESKTOP_FILE" "$ICON_TARGET"
chmod 0755 "$BIN_TARGET"

echo "Building Debian package..."
dpkg-deb --build "$PACKAGE_ROOT" "$PACKAGE_PATH"

echo "Built package: $PACKAGE_PATH"
echo "Install with: sudo apt install \"$PACKAGE_PATH\""
