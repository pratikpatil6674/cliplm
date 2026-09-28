#!/usr/bin/env bash

set -euo pipefail

source "$(dirname "$0")/packaging_common.sh"
load_dotenv

# Build an AppImage around the Nuitka onefile binary.
# Because the compiled binary is already self-contained, the AppImage wrapper is
# mostly responsible for desktop integration metadata and a stable entrypoint.

PROJECT_VERSION="$(project_version)"
APPIMAGE_BUILD_DIR="$BUILD_DIR/appimage"
APPDIR="$APPIMAGE_BUILD_DIR/AppDir"
APPDIR_USR_BIN="$APPDIR/usr/bin"
DESKTOP_FILE="$APPDIR/${APP_NAME}.desktop"
APP_RUN_FILE="$APPDIR/AppRun"
ICON_TARGET="$APPDIR/${APP_NAME}.svg"
APPIMAGE_PATH="$DIST_DIR/${APP_NAME}-${PROJECT_VERSION}-${ARCH}.AppImage"
TOOLS_DIR="$BUILD_DIR/tools"
APPIMAGETOOL_PATH="$(resolve_project_path "${APPIMAGETOOL_PATH:-$TOOLS_DIR/appimagetool-${ARCH}.AppImage}")"

ensure_appimagetool() {
    if command -v appimagetool >/dev/null 2>&1; then
        APPIMAGETOOL_PATH="$(command -v appimagetool)"
        return
    fi

    if [[ -x "$APPIMAGETOOL_PATH" ]]; then
        return
    fi

    require_command curl

    local appimagekit_arch
    appimagekit_arch="$(appimagekit_arch_name "$ARCH")"
    local download_url="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${appimagekit_arch}.AppImage"

    echo "appimagetool not found on PATH. Downloading from $download_url ..."
    curl -L "$download_url" -o "$APPIMAGETOOL_PATH"
    chmod +x "$APPIMAGETOOL_PATH"
}

appimagekit_arch_name() {
    case "$1" in
        amd64|x86_64)
            printf 'x86_64\n'
            ;;
        arm64|aarch64)
            printf 'aarch64\n'
            ;;
        *)
            printf '%s\n' "$1"
            ;;
    esac
}

echo "Cleaning previous AppImage build output..."
rm -rf "$APPIMAGE_BUILD_DIR" "$APPIMAGE_PATH"
mkdir -p "$APPDIR_USR_BIN" "$DIST_DIR" "$TOOLS_DIR"

if [[ "${REBUILD_NUITKA_BINARY:-1}" == "1" ]]; then
    build_nuitka_binary
fi

ensure_appimagetool

echo "Staging AppDir..."
install -Dm755 "$NUITKA_BINARY_PATH" "$APPDIR_USR_BIN/$APP_NAME"
install -Dm644 "$ICON_SOURCE" "$ICON_TARGET"

cat > "$APP_RUN_FILE" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$HERE/usr/bin/cliplm" "$@"
EOF

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_DISPLAY_NAME}
Exec=${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Categories=Utility;
EOF

chmod 0755 "$APP_RUN_FILE" "$APPDIR_USR_BIN/$APP_NAME"
chmod 0644 "$DESKTOP_FILE" "$ICON_TARGET"

echo "Building AppImage..."
ARCH="$ARCH" "$APPIMAGETOOL_PATH" "$APPDIR" "$APPIMAGE_PATH"

echo "Built AppImage: $APPIMAGE_PATH"
