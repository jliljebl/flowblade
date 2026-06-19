#!/usr/bin/env bash

set -euo pipefail

APP_ID="io.github.jliljebl.Flowblade"
APP_NAME="Flowblade"
ARCH="${ARCH:-x86_64}"
BUILD_APPIMAGE=1

usage() {
    cat <<'USAGE'
Usage: packaging/appimage/build-appimage.sh [--appdir-only]

Build a Flowblade AppImage from an Ubuntu/Debian system with Flowblade runtime
packages installed. Use --appdir-only to validate staging without running
linuxdeploy.
USAGE
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --appdir-only)
            BUILD_APPIMAGE=0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

log() {
    printf '==> %s\n' "$*"
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Required command not found: $1" >&2
        exit 1
    fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
FLOWBLADE_DIR="$ROOT_DIR/flowblade-trunk"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build/appimage}"
APPDIR="${APPDIR:-$BUILD_DIR/${APP_NAME}.AppDir}"
DIST_DIR="${DIST_DIR:-$ROOT_DIR/dist}"
TOOLS_DIR="$BUILD_DIR/tools"
DESKTOP_FILE="$APPDIR/$APP_ID.desktop"
ICON_FILE="$APPDIR/$APP_ID.png"

detect_version() {
    python3 - "$FLOWBLADE_DIR/setup.py" <<'PY'
import ast
import pathlib
import sys

setup_py = pathlib.Path(sys.argv[1])
tree = ast.parse(setup_py.read_text())
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "setup":
        for keyword in node.keywords:
            if keyword.arg == "version":
                print(ast.literal_eval(keyword.value))
                raise SystemExit(0)
raise SystemExit("Could not find setup(version=...)")
PY
}

VERSION="${VERSION:-$(detect_version)}"
APPIMAGE_NAME="${APPIMAGE_NAME:-${APP_NAME}-${VERSION}-${ARCH}.AppImage}"

# These package payloads contain resources that linuxdeploy cannot infer from
# ELF dependencies alone: Python modules, GI typelibs, MLT plugins/data,
# GDK-Pixbuf loaders, icon theme data, and external tools used by Flowblade.
RUNTIME_PACKAGES=(
    adwaita-icon-theme
    ffmpeg
    frei0r-plugins
    gmic
    gir1.2-atk-1.0
    gir1.2-gdkpixbuf-2.0
    gir1.2-freedesktop
    gir1.2-glib-2.0
    gir1.2-harfbuzz-0.0
    gir1.2-gtk-3.0
    gir1.2-pango-1.0
    hicolor-icon-theme
    libcairo-gobject2
    libcairo2
    libdatrie1
    libfontconfig1
    libfreetype6
    libfribidi0
    libgdk-pixbuf-2.0-0
    libgdk-pixbuf2.0-bin
    libglib2.0-bin
    libgraphite2-3
    libgtk-3-0
    libgtk-3-bin
    libharfbuzz0b
    libjbig0
    libjpeg-turbo8
    libmlt++7
    libmlt-data
    libmlt7
    libpango-1.0-0
    libpangocairo-1.0-0
    libpangoft2-1.0-0
    libpng16-16
    librsvg2-common
    libthai0
    libtiff5
    libwayland-client0
    libwayland-cursor0
    libwayland-egl1
    libwebp7
    libwebpdemux2
    libwebpmux3
    libxkbcommon0
    melt
    python3
    python3-gi
    python3-gi-cairo
    python3-mlt
    python3-numpy
    python3-pil
    python3-usb1
    shared-mime-info
    swh-plugins
    zlib1g
)

copy_path_from_host() {
    local src="$1"
    local dst="$APPDIR$src"

    case "$src" in
        /|/usr|/usr/bin|/usr/lib|/usr/lib/*|/usr/share|/usr/share/doc|/usr/share/man)
            if [ -d "$src" ] && [ ! -L "$src" ]; then
                mkdir -p "$dst"
                return
            fi
            ;;
    esac

    if [ -d "$src" ] && [ ! -L "$src" ]; then
        mkdir -p "$dst"
    elif [ -e "$src" ] || [ -L "$src" ]; then
        mkdir -p "$(dirname "$dst")"
        cp -a "$src" "$dst"
    fi
}

copy_package_payloads() {
    if ! command -v dpkg-query >/dev/null 2>&1; then
        log "dpkg-query not found; skipping Debian package payload copy"
        return
    fi

    local package path status
    for package in "${RUNTIME_PACKAGES[@]}"; do
        status="$(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || true)"
        if [ "$status" != "install ok installed" ]; then
            log "Skipping package payload not installed: $package"
            continue
        fi

        while IFS= read -r path; do
            case "$path" in
                ""|/|/usr/share/doc/*|/usr/share/man/*|/usr/share/lintian/*|/usr/share/bug/*)
                    continue
                    ;;
            esac
            copy_path_from_host "$path"
        done < <(dpkg-query -L "$package")
    done
}

remove_host_gdk_pixbuf_caches() {
    if [ -d "$APPDIR/usr/lib" ]; then
        find "$APPDIR/usr/lib" -path '*/gdk-pixbuf-2.0/2.10.0/loaders.cache' -type f -delete
    fi
}

copy_binary_to_appdir() {
    local binary="$1"
    local resolved
    resolved="$(command -v "$binary" 2>/dev/null || true)"
    if [ -z "$resolved" ]; then
        return
    fi

    mkdir -p "$APPDIR/usr/bin"
    cp -aL "$resolved" "$APPDIR/usr/bin/$binary"
}

stage_python_runtime() {
    local python_version
    python_version="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    PYTHON_VERSION="$python_version"

    copy_binary_to_appdir python3

    if command -v "python$python_version" >/dev/null 2>&1; then
        copy_binary_to_appdir "python$python_version"
    fi

    mkdir -p "$APPDIR/usr/lib"
    for path in "/usr/lib/python$python_version" "/usr/lib/python3" "/usr/local/lib/python$python_version/dist-packages"; do
        if [ -d "$path" ]; then
            mkdir -p "$APPDIR$(dirname "$path")"
            cp -a "$path" "$APPDIR$(dirname "$path")/"
        fi
    done
}

stage_flowblade() {
    local record_file="$BUILD_DIR/install-record.txt"
    local source_parent="$BUILD_DIR/source"
    local source_dir="$source_parent/flowblade-trunk"

    log "Staging Flowblade into AppDir"
    mkdir -p "$BUILD_DIR" "$APPDIR" "$DIST_DIR"
    rm -rf "$source_parent"
    mkdir -p "$source_parent"
    cp -a "$FLOWBLADE_DIR" "$source_parent/"

    (
        cd "$source_dir"
        PYTHONDONTWRITEBYTECODE=1 python3 setup.py install \
            --root="$APPDIR" \
            --prefix=/usr \
            --install-lib=/usr/share/flowblade \
            --install-scripts=/usr/bin \
            --single-version-externally-managed \
            --record="$record_file" \
            --no-compile
    )

    mkdir -p "$APPDIR/usr/share/flowblade/Flowblade"
    cp -a "$source_dir/Flowblade/res" "$APPDIR/usr/share/flowblade/Flowblade/"
    cp -a "$source_dir/Flowblade/locale" "$APPDIR/usr/share/flowblade/Flowblade/"

    cp "$APPDIR/usr/share/applications/$APP_ID.desktop" "$DESKTOP_FILE"
    cp "$APPDIR/usr/share/icons/hicolor/128x128/apps/$APP_ID.png" "$ICON_FILE"
    sed -i 's|^Exec=.*|Exec=AppRun %f|' "$DESKTOP_FILE"
    ln -sfn "$APP_ID.png" "$APPDIR/.DirIcon"
}

write_apprun() {
    log "Writing AppRun"
    cat > "$APPDIR/AppRun" <<EOF
#!/usr/bin/env bash
set -e

APPDIR="\${APPDIR:-\$(dirname "\$(readlink -f "\${BASH_SOURCE[0]}")")}"
PYTHON_VERSION="$PYTHON_VERSION"

export PATH="\$APPDIR/usr/bin:\$PATH"
export PYTHONHOME="\$APPDIR/usr"
export PYTHONNOUSERSITE=1
export PYTHONPATH="\$APPDIR/usr/lib/python3/dist-packages:\$APPDIR/usr/lib/python\$PYTHON_VERSION/dist-packages:\${PYTHONPATH:-}"
export LD_LIBRARY_PATH="\$APPDIR/usr/lib:\$APPDIR/usr/lib/x86_64-linux-gnu:\$APPDIR/lib:\$APPDIR/lib/x86_64-linux-gnu:\${LD_LIBRARY_PATH:-}"
export GI_TYPELIB_PATH="\$APPDIR/usr/lib/girepository-1.0:\$APPDIR/usr/lib/x86_64-linux-gnu/girepository-1.0:\${GI_TYPELIB_PATH:-}"
export GIO_EXTRA_MODULES="\$APPDIR/usr/lib/x86_64-linux-gnu/gio/modules:\${GIO_EXTRA_MODULES:-}"
export XDG_DATA_DIRS="\$APPDIR/usr/share:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

if [ -d "\$APPDIR/usr/lib/x86_64-linux-gnu/mlt-7" ]; then
    export MLT_REPOSITORY="\$APPDIR/usr/lib/x86_64-linux-gnu/mlt-7"
elif [ -d "\$APPDIR/usr/lib/mlt-7" ]; then
    export MLT_REPOSITORY="\$APPDIR/usr/lib/mlt-7"
fi

if [ -d "\$APPDIR/usr/share/mlt-7" ]; then
    export MLT_DATA="\$APPDIR/usr/share/mlt-7"
fi

if [ -d "\$APPDIR/usr/lib/x86_64-linux-gnu/frei0r-1" ]; then
    export FREI0R_PATH="\$APPDIR/usr/lib/x86_64-linux-gnu/frei0r-1"
elif [ -d "\$APPDIR/usr/lib/frei0r-1" ]; then
    export FREI0R_PATH="\$APPDIR/usr/lib/frei0r-1"
fi

if [ -d "\$APPDIR/usr/lib/ladspa" ]; then
    export LADSPA_PATH="\$APPDIR/usr/lib/ladspa"
fi

unset GDK_PIXBUF_MODULEDIR
unset GDK_PIXBUF_MODULE_FILE
GDK_PIXBUF_QUERY_LOADERS=""
for candidate in \
    "\$APPDIR/usr/bin/gdk-pixbuf-query-loaders" \
    "\$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders" \
    "\$APPDIR/usr/lib/gdk-pixbuf-2.0/gdk-pixbuf-query-loaders"; do
    if [ -x "\$candidate" ]; then
        GDK_PIXBUF_QUERY_LOADERS="\$candidate"
        break
    fi
done

GDK_PIXBUF_LOADER_DIR=""
for candidate in \
    "\$APPDIR/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders" \
    "\$APPDIR/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders"; do
    if [ -d "\$candidate" ]; then
        GDK_PIXBUF_LOADER_DIR="\$candidate"
        break
    fi
done

if [ -n "\$GDK_PIXBUF_QUERY_LOADERS" ] && [ -n "\$GDK_PIXBUF_LOADER_DIR" ]; then
    CACHE_BASE="\${XDG_CACHE_HOME:-\${HOME:-/tmp}/.cache}/flowblade-appimage"
    mkdir -p "\$CACHE_BASE"
    if ! GDK_PIXBUF_MODULEDIR="\$GDK_PIXBUF_LOADER_DIR" "\$GDK_PIXBUF_QUERY_LOADERS" > "\$CACHE_BASE/gdk-pixbuf-loaders.cache" 2>"\$CACHE_BASE/gdk-pixbuf-query-loaders.log"; then
        cat "\$CACHE_BASE/gdk-pixbuf-query-loaders.log" >&2 || true
    fi
    if [ -s "\$CACHE_BASE/gdk-pixbuf-loaders.cache" ] && grep -Fq "png" "\$CACHE_BASE/gdk-pixbuf-loaders.cache"; then
        export GDK_PIXBUF_MODULEDIR="\$GDK_PIXBUF_LOADER_DIR"
        export GDK_PIXBUF_MODULE_FILE="\$CACHE_BASE/gdk-pixbuf-loaders.cache"
    fi
fi

exec "\$APPDIR/usr/bin/python3" "\$APPDIR/usr/bin/flowblade" "\$@"
EOF
    chmod +x "$APPDIR/AppRun"
}

validate_appdir() {
    log "Validating AppDir metadata"
    test -x "$APPDIR/AppRun"
    test -x "$APPDIR/usr/bin/flowblade"
    test -f "$DESKTOP_FILE"
    test -f "$ICON_FILE"
    test -d "$APPDIR/usr/share/flowblade/Flowblade/res/shortcuts"
    test -f "$APPDIR/usr/share/flowblade/Flowblade/res/filters/filters.xml"
    test -d "$APPDIR/usr/share/flowblade/Flowblade/locale"

    if command -v desktop-file-validate >/dev/null 2>&1; then
        desktop-file-validate "$DESKTOP_FILE"
    fi
}

download_linuxdeploy() {
    require_command curl
    mkdir -p "$TOOLS_DIR"

    LINUXDEPLOY="${LINUXDEPLOY:-$TOOLS_DIR/linuxdeploy-$ARCH.AppImage}"
    if [ ! -x "$LINUXDEPLOY" ]; then
        log "Downloading linuxdeploy"
        curl -L \
            "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-$ARCH.AppImage" \
            -o "$LINUXDEPLOY"
        chmod +x "$LINUXDEPLOY"
    fi
}

run_linuxdeploy() {
    local args=(
        --appdir "$APPDIR"
        --desktop-file "$DESKTOP_FILE"
        --icon-file "$ICON_FILE"
        --executable "$APPDIR/usr/bin/python3"
    )

    for binary in ffmpeg ffprobe gmic melt melt-7; do
        if [ -x "$APPDIR/usr/bin/$binary" ]; then
            args+=(--executable "$APPDIR/usr/bin/$binary")
        fi
    done

    local find_roots=()
    for dir in "$APPDIR/usr/lib" "$APPDIR/lib"; do
        if [ -d "$dir" ]; then
            find_roots+=("$dir")
        fi
    done

    if [ "${#find_roots[@]}" -gt 0 ]; then
        while IFS= read -r -d '' library; do
            args+=(--library "$library")
        done < <(find "${find_roots[@]}" -type f \( -name '*.so' -o -name '*.so.*' \) -print0)
    fi

    mkdir -p "$DIST_DIR"
    export APPIMAGE_EXTRACT_AND_RUN=1
    export ARCH
    export LDAI_OUTPUT="$DIST_DIR/$APPIMAGE_NAME"

    log "Building $LDAI_OUTPUT"
    (
        cd "$BUILD_DIR"
        "$LINUXDEPLOY" "${args[@]}" --output appimage
    )

    if [ ! -f "$LDAI_OUTPUT" ]; then
        local produced=""
        while IFS= read -r candidate; do
            produced="$candidate"
            break
        done < <(find "$BUILD_DIR" "$ROOT_DIR" -maxdepth 1 -type f -name '*.AppImage')

        if [ -z "$produced" ]; then
            echo "linuxdeploy finished but no AppImage was found" >&2
            exit 1
        fi
        mv "$produced" "$LDAI_OUTPUT"
    fi

    chmod +x "$LDAI_OUTPUT"
    log "Created $LDAI_OUTPUT"
}

main() {
    require_command python3

    log "Preparing $APPDIR"
    rm -rf "$APPDIR"
    mkdir -p "$BUILD_DIR" "$DIST_DIR"

    stage_flowblade
    copy_package_payloads
    remove_host_gdk_pixbuf_caches
    stage_python_runtime
    copy_binary_to_appdir ffmpeg
    copy_binary_to_appdir ffprobe
    copy_binary_to_appdir gmic
    copy_binary_to_appdir melt
    copy_binary_to_appdir melt-7
    write_apprun
    validate_appdir

    if [ "$BUILD_APPIMAGE" -eq 0 ]; then
        log "AppDir staged at $APPDIR"
        exit 0
    fi

    download_linuxdeploy
    run_linuxdeploy
}

main "$@"
