#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APPIMAGE="${1:-}"
IMAGES="${APPIMAGE_SMOKE_CONTAINER_IMAGES:-ubuntu:22.04 ubuntu:24.04 debian:12 debian:13 fedora:latest archlinux:latest opensuse/tumbleweed:latest gentoo/stage3:latest}"
CONTAINER_SMOKE_DIR="$ROOT_DIR/build/appimage-smoke-containers"

if [ -z "$APPIMAGE" ]; then
    while IFS= read -r candidate; do
        APPIMAGE="$candidate"
        break
    done < <(find "$ROOT_DIR/dist" -maxdepth 1 -type f -name '*.AppImage' -print | sort)
fi

if [ -z "$APPIMAGE" ] || [ ! -f "$APPIMAGE" ]; then
    echo "No AppImage found to smoke test in containers" >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "Required command not found: docker" >&2
    exit 1
fi

container_install_command() {
    local image="$1"

    case "$image" in
        debian:*|ubuntu:*)
            printf '%s\n' \
                'export DEBIAN_FRONTEND=noninteractive' \
                'apt-get update' \
                'apt-get install -y --no-install-recommends bash ca-certificates coreutils findutils grep xauth xvfb' \
                'rm -rf /var/lib/apt/lists/*'
            ;;
        fedora:*)
            printf '%s\n' \
                'dnf -y --setopt=install_weak_deps=False install bash ca-certificates coreutils findutils grep xorg-x11-server-Xvfb xorg-x11-xauth' \
                'dnf clean all'
            ;;
        archlinux:*)
            printf '%s\n' \
                'pacman -Sy --noconfirm --needed bash ca-certificates coreutils findutils grep xorg-server-xvfb xorg-xauth' \
                'pacman -Scc --noconfirm'
            ;;
        opensuse/*)
            printf '%s\n' \
                'zypper --non-interactive --gpg-auto-import-keys refresh' \
                'zypper --non-interactive --gpg-auto-import-keys install --no-recommends bash ca-certificates coreutils findutils grep xauth xorg-x11-server-extra' \
                'zypper clean --all'
            ;;
        gentoo/*)
            printf '%s\n' \
                'if [ ! -e /var/db/repos/gentoo/profiles/repo_name ]; then emerge-webrsync --quiet; fi' \
                'FEATURES="${FEATURES:-} getbinpkg -news" emerge --getbinpkgonly --usepkg --binpkg-respect-use=y --jobs=1 --quiet app-shells/bash app-misc/ca-certificates sys-apps/coreutils sys-apps/findutils sys-apps/grep x11-apps/xauth '\''x11-base/xorg-server[xvfb]'\'''
            ;;
        *)
            echo "Unsupported AppImage smoke container image: $image" >&2
            return 1
            ;;
    esac
}

appimage_rel="${APPIMAGE#$ROOT_DIR/}"
mkdir -p "$CONTAINER_SMOKE_DIR"

read -r -a images <<< "$IMAGES"
for image in "${images[@]}"; do
    safe_image_name="${image//\//-}"
    safe_image_name="${safe_image_name//:/-}"
    smoke_dir="/work/build/appimage-smoke-containers/$safe_image_name"
    install_command="$(container_install_command "$image")"

    echo "==> Smoke testing AppImage in $image"
    docker run --rm \
        --volume "$ROOT_DIR:/work" \
        --workdir /work \
        --env APPIMAGE_EXTRACT_AND_RUN=1 \
        --env APPIMAGE_SMOKE_TIMEOUT="${APPIMAGE_SMOKE_TIMEOUT:-30s}" \
        --env SMOKE_DIR="$smoke_dir" \
        "$image" \
        bash -lc "$install_command"$'\n'"trap 'chmod -R a+rwX /work/build/appimage-smoke-containers || true' EXIT"$'\n'"packaging/appimage/smoke-test-appimage.sh '$appimage_rel'"
done
