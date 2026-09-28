#!/usr/bin/env bash

set -euo pipefail

source "$(dirname "$0")/packaging_common.sh"
load_dotenv

# Build the Linux release set:
# - Debian package
# - AppImage
# - release metadata JSON
# - sha256 sums
# - optional Cloudflare R2 upload of the release artifacts

PROJECT_VERSION="$(project_version)"
RELEASE_DIR="$DIST_DIR/release"
DEB_PATH="$DIST_DIR/${APP_NAME}_${PROJECT_VERSION}_${ARCH}.deb"
APPIMAGE_PATH="$DIST_DIR/${APP_NAME}-${PROJECT_VERSION}-${ARCH}.AppImage"
SHA256_FILE="$RELEASE_DIR/sha256sums.txt"
METADATA_FILE="$RELEASE_DIR/release-metadata.json"

echo "Preparing release directories..."
mkdir -p "$DIST_DIR" "$RELEASE_DIR"
rm -f "$SHA256_FILE" "$METADATA_FILE"

# Create actual artifacts
echo "Building standalone binary with Nuitka..."
build_nuitka_binary
echo "Building Debian package..."
REBUILD_NUITKA_BINARY=0 "$PACKAGING_DIR/build_deb.sh"
echo "Building AppImage..."
REBUILD_NUITKA_BINARY=0 "$PACKAGING_DIR/build_appimage.sh"

if [[ ! -f "$DEB_PATH" || ! -f "$APPIMAGE_PATH" ]]; then
    echo "Expected release artifacts were not produced." >&2
    exit 1
fi

echo "Generating checksums..."
sha256sum "$DEB_PATH" "$APPIMAGE_PATH" > "$SHA256_FILE"

DEB_SHA256="$(awk -v file="$DEB_PATH" '$2 == file { print $1 }' "$SHA256_FILE")"
APPIMAGE_SHA256="$(awk -v file="$APPIMAGE_PATH" '$2 == file { print $1 }' "$SHA256_FILE")"
BUILD_TIMESTAMP_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

cat > "$METADATA_FILE" <<EOF
{
  "app_name": "${APP_NAME}",
  "display_name": "${APP_DISPLAY_NAME}",
  "version": "${PROJECT_VERSION}",
  "architecture": "${ARCH}",
  "built_at_utc": "${BUILD_TIMESTAMP_UTC}",
  "artifacts": [
    {
      "type": "deb",
      "path": "${DEB_PATH}",
      "sha256": "${DEB_SHA256}"
    },
    {
      "type": "appimage",
      "path": "${APPIMAGE_PATH}",
      "sha256": "${APPIMAGE_SHA256}"
    }
  ]
}
EOF

echo "Release metadata written to $METADATA_FILE"
echo "Checksums written to $SHA256_FILE"

if [[ "${R2_UPLOAD:-0}" == "1" ]]; then
    "$PACKAGING_DIR/upload_r2_release.sh" "$DEB_PATH" "$APPIMAGE_PATH" "$SHA256_FILE" "$METADATA_FILE"
fi

echo "Release build complete."
