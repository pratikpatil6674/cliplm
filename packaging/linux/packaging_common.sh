#!/usr/bin/env bash

set -euo pipefail

# Shared packaging helpers for Linux release artifacts.
# The individual scripts source this file so the Nuitka build, version handling,
# and output naming stay consistent across .deb, AppImage, and release metadata.

# Resolve paths from this file rather than from the shell's current directory.
# This keeps every packaging command usable from the repository root, /tmp, or
# a CI runner that invokes the script through an absolute path.
PACKAGING_DIR="$(
    cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1
    pwd
)"
PROJECT_ROOT="$(cd -- "$PACKAGING_DIR/../.." >/dev/null 2>&1 && pwd)"

resolve_project_path() {
    local path="$1"
    if [[ "$path" == /* ]]; then
        printf '%s\n' "$path"
    else
        printf '%s/%s\n' "$PROJECT_ROOT" "$path"
    fi
}

APP_NAME="${APP_NAME:-cliplm}"
APP_DISPLAY_NAME="${APP_DISPLAY_NAME:-ClipLM}"
ARCH="${ARCH:-amd64}"
DIST_DIR="$(resolve_project_path "${DIST_DIR:-dist}")"
BUILD_DIR="$(resolve_project_path "${BUILD_DIR:-build}")"
NUITKA_OUTPUT_DIR="$(resolve_project_path "${NUITKA_OUTPUT_DIR:-$BUILD_DIR/nuitka}")"
NUITKA_BINARY_NAME="${NUITKA_BINARY_NAME:-main.bin}"
NUITKA_BINARY_PATH="$(resolve_project_path "${NUITKA_BINARY_PATH:-$NUITKA_OUTPUT_DIR/$NUITKA_BINARY_NAME}")"
ICON_SOURCE="$(resolve_project_path "${ICON_SOURCE:-icons/app.svg}")"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"
APP_ENTRYPOINT="$PROJECT_ROOT/src/main.py"
DOTENV_FILE="$PROJECT_ROOT/.env"

load_dotenv() {
    local dotenv_path
    dotenv_path="$(resolve_project_path "${1:-$DOTENV_FILE}")"
    if [[ ! -f "$dotenv_path" ]]; then
        return 0
    fi

    # Load simple KEY=VALUE lines from .env into the current shell so packaging
    # scripts can reuse locally stored release credentials without repeating
    # manual export steps.
    set -a
    # shellcheck disable=SC1090
    source "$dotenv_path"
    set +a
}

project_version() {
    local version
    version="$(sed -n 's/^version = "\(.*\)"/\1/p' "$PYPROJECT_FILE" | head -n 1)"
    if [[ -z "$version" ]]; then
        echo "Could not determine project version from $PYPROJECT_FILE" >&2
        return 1
    fi
    printf '%s\n' "$version"
}

require_command() {
    local command_name="$1"
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Required command not found: $command_name" >&2
        return 1
    fi
}

ensure_dist_dir() {
    mkdir -p "$DIST_DIR"
}

build_nuitka_binary() {
    require_command uv
    local build_info_dir="$BUILD_DIR/generated"
    local version
    version="$(project_version)"
    rm -rf "$NUITKA_OUTPUT_DIR"
    mkdir -p "$NUITKA_OUTPUT_DIR" "$build_info_dir"
    printf 'APP_VERSION = "%s"\n' "$version" > "$build_info_dir/AppBuildVersion.py"

    echo "Building standalone binary with Nuitka..."
    PYTHONPATH="$build_info_dir${PYTHONPATH:+:$PYTHONPATH}" \
        uv run --project "$PROJECT_ROOT" python -m nuitka \
        --standalone \
        --onefile \
        --plugin-enable=pyside6 \
        --remove-output \
        --disable-console \
        --output-dir="$NUITKA_OUTPUT_DIR" \
        --output-filename="$NUITKA_BINARY_NAME" \
        --nofollow-import-to=unittest,tkinter,test \
        "$APP_ENTRYPOINT"

    if [[ ! -f "$NUITKA_BINARY_PATH" ]]; then
        echo "Expected Nuitka output not found: $NUITKA_BINARY_PATH" >&2
        return 1
    fi
}
