#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APPIMAGE="${1:-}"
APPDIR="${APPDIR:-$ROOT_DIR/build/appimage/Flowblade.AppDir}"
SMOKE_DIR="${SMOKE_DIR:-$ROOT_DIR/build/appimage-smoke}"
SMOKE_TIMEOUT="${APPIMAGE_SMOKE_TIMEOUT:-30s}"
LOG_FILE="$SMOKE_DIR/flowblade-appimage-smoke.log"

if [ -z "$APPIMAGE" ]; then
    while IFS= read -r candidate; do
        APPIMAGE="$candidate"
        break
    done < <(find "$ROOT_DIR/dist" -maxdepth 1 -type f -name '*.AppImage' -print | sort)
fi

if [ -z "$APPIMAGE" ] || [ ! -f "$APPIMAGE" ]; then
    echo "No AppImage found to smoke test" >&2
    exit 1
fi

APPIMAGE="$(readlink -f "$APPIMAGE")"

if ! command -v xvfb-run >/dev/null 2>&1 && ! command -v Xvfb >/dev/null 2>&1; then
    echo "Required command not found: xvfb-run or Xvfb" >&2
    exit 1
fi

run_with_xvfb() {
    local display
    local xvfb_pid
    local xvfb_log
    local ready=0

    display=":$((100 + (RANDOM % 900)))"
    xvfb_log="$SMOKE_DIR/xvfb.log"

    Xvfb "$display" -screen 0 1920x1080x24 >"$xvfb_log" 2>&1 &
    xvfb_pid=$!

    for _ in {1..50}; do
        if [ -S "/tmp/.X11-unix/X${display#:}" ]; then
            ready=1
            break
        fi

        if ! kill -0 "$xvfb_pid" 2>/dev/null; then
            cat "$xvfb_log" >&2
            echo "Xvfb exited before the smoke test could start" >&2
            return 1
        fi

        sleep 0.1
    done

    if [ "$ready" -ne 1 ]; then
        cat "$xvfb_log" >&2
        echo "Xvfb did not create display socket $display" >&2
        kill "$xvfb_pid" 2>/dev/null || true
        wait "$xvfb_pid" 2>/dev/null || true
        return 1
    fi

    DISPLAY="$display" "$@"
    local status=$?

    kill "$xvfb_pid" 2>/dev/null || true
    wait "$xvfb_pid" 2>/dev/null || true

    return "$status"
}

validate_appdir_payload() {
    if [ ! -d "$APPDIR" ]; then
        echo "==> AppDir not found at $APPDIR, skipping AppDir payload validation"
        return
    fi

    local missing=0
    local lib_roots=()
    local library
    local typelib
    local root
    local required_libraries=(
        libasound.so.2
        libcairo-gobject.so.2
        libcairo.so.2
        libcom_err.so.2
        libdatrie.so.1
        libdrm.so.2
        libexpat.so.1
        libfontconfig.so.1
        libfreetype.so.6
        libfribidi.so.0
        libgbm.so.1
        libGLdispatch.so.0
        libgpg-error.so.0
        libgraphite2.so.3
        libharfbuzz.so.0
        libjbig.so.0
        libjack.so.0
        libjpeg.so.8
        libOpenGL.so.0
        libpango-1.0.so.0
        libpangocairo-1.0.so.0
        libpangoft2-1.0.so.0
        libpng16.so.16
        libthai.so.0
        libtiff.so.5
        libusb-1.0.so.0
        libwayland-client.so.0
        libwayland-cursor.so.0
        libwayland-egl.so.1
        libwebp.so.7
        libwebpdemux.so.2
        libwebpmux.so.3
        libxcb.so.1
        libxkbcommon.so.0
        libz.so.1
    )
    local required_typelibs=(
        Atk-1.0
        Gdk-3.0
        GdkPixbuf-2.0
        GdkX11-3.0
        GIRepository-2.0
        Gio-2.0
        GLib-2.0
        GModule-2.0
        GObject-2.0
        Gtk-3.0
        HarfBuzz-0.0
        Pango-1.0
        PangoCairo-1.0
        cairo-1.0
        fontconfig-2.0
        freetype2-2.0
        xlib-2.0
    )

    echo "==> Validating bundled GI typelibs in $APPDIR"
    for typelib in "${required_typelibs[@]}"; do
        if [ -z "$(find "$APPDIR/usr/lib" -path "*/girepository-1.0/$typelib.typelib" -type f -print -quit 2>/dev/null)" ]; then
            echo "Missing bundled GI typelib: $typelib.typelib" >&2
            missing=1
        fi
    done

    echo "==> Validating bundled MIME database in $APPDIR"
    for path in "$APPDIR/usr/share/mime/mime.cache" "$APPDIR/usr/share/mime/magic"; do
        if [ ! -f "$path" ]; then
            echo "Missing bundled MIME database file: ${path#$APPDIR/}" >&2
            missing=1
        fi
    done

    echo "==> Validating bundled Fontconfig data in $APPDIR"
    if [ ! -f "$APPDIR/etc/fonts/fonts.conf" ]; then
        echo 'Missing bundled Fontconfig configuration: etc/fonts/fonts.conf' >&2
        missing=1
    fi
    if [ -z "$(find "$APPDIR/usr/share/fonts" -type f \( -name '*.ttf' -o -name '*.otf' \) -print -quit 2>/dev/null)" ]; then
        echo 'Missing bundled font files under usr/share/fonts' >&2
        missing=1
    fi

    for root in "$APPDIR/usr/lib" "$APPDIR/lib"; do
        if [ -d "$root" ]; then
            lib_roots+=("$root")
        fi
    done

    echo "==> Validating bundled shared libraries in $APPDIR"
    for library in "${required_libraries[@]}"; do
        if [ "${#lib_roots[@]}" -eq 0 ] || [ -z "$(find "${lib_roots[@]}" -name "$library" -print -quit 2>/dev/null)" ]; then
            echo "Missing bundled shared library: $library" >&2
            missing=1
        fi
    done

    if [ "$missing" -ne 0 ]; then
        exit 1
    fi
}

validate_appdir_payload

mkdir -p "$SMOKE_DIR/home" "$SMOKE_DIR/runtime" "$SMOKE_DIR/config" "$SMOKE_DIR/data" "$SMOKE_DIR/cache"
chmod 700 "$SMOKE_DIR/runtime"
chmod +x "$APPIMAGE"

RUN_TARGET="$APPIMAGE"
if [ "${APPIMAGE_SMOKE_MANUAL_EXTRACT:-0}" = '1' ]; then
    EXTRACT_DIR="$SMOKE_DIR/appimage-extract"
    rm -rf "$EXTRACT_DIR"
    mkdir -p "$EXTRACT_DIR"
    (
        cd "$EXTRACT_DIR"
        "$APPIMAGE" --appimage-extract >/dev/null
    )
    RUN_TARGET="$EXTRACT_DIR/squashfs-root/AppRun"
    if [ ! -x "$RUN_TARGET" ]; then
        printf 'Extracted AppRun is not executable: %s\n' "$RUN_TARGET" >&2
        exit 1
    fi
fi

printf '==> Smoke testing %s\n' "$RUN_TARGET"
app_command=(
    env
        HOME="$SMOKE_DIR/home"
        XDG_CONFIG_HOME="$SMOKE_DIR/config"
        XDG_DATA_HOME="$SMOKE_DIR/data"
        XDG_CACHE_HOME="$SMOKE_DIR/cache"
        XDG_RUNTIME_DIR="$SMOKE_DIR/runtime"
        PYTHONUNBUFFERED=1
        NO_AT_BRIDGE=1
        SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}"
        "$RUN_TARGET"
)

set +e
if command -v xvfb-run >/dev/null 2>&1; then
    timeout --kill-after=5s "$SMOKE_TIMEOUT" \
        xvfb-run -a -s "-screen 0 1920x1080x24" \
        "${app_command[@]}" >"$LOG_FILE" 2>&1
else
    run_with_xvfb \
        timeout --kill-after=5s "$SMOKE_TIMEOUT" \
        "${app_command[@]}" >"$LOG_FILE" 2>&1
fi
status=$?
set -e

cat "$LOG_FILE"

case "$status" in
    0)
        echo "==> AppImage exited cleanly during smoke test"
        ;;
    124|137)
        # GNU timeout can return 137 when --kill-after escalates to SIGKILL.
        echo "==> AppImage remained running for $SMOKE_TIMEOUT"
        ;;
    *)
        echo "AppImage exited with status $status during smoke test" >&2
        exit "$status"
        ;;
esac

required_markers=(
    "Running from AppImage..."
    "MLT found, version:"
    "Application version:"
    "GTK+ version:"
    "Create SDL1 consumer..."
)

for marker in "${required_markers[@]}"; do
    if ! grep -Fq "$marker" "$LOG_FILE"; then
        echo "Smoke test log is missing expected marker: $marker" >&2
        exit 1
    fi
done

fatal_markers=(
    "MLT not found, exiting"
    "Failed to import module app.py"
    "Traceback (most recent call last)"
    "Fatal Python error"
    "Segmentation fault"
    "error while loading shared libraries"
    "cannot open shared object file"
)

for marker in "${fatal_markers[@]}"; do
    if grep -Fq "$marker" "$LOG_FILE"; then
        echo "Smoke test log contains fatal marker: $marker" >&2
        exit 1
    fi
done

echo "==> AppImage smoke test passed"
