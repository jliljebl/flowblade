#!/usr/bin/env python3

import sys
from pathlib import Path

from PIL import Image


def normalize_pngs(root: Path) -> int:
    '''
    Convert indexed, grayscale, and other non-RGB PNG resources to RGBA.

    The AppImage bundles its own GTK/GdkPixbuf loader stack, and some host
    distributions are less forgiving when loading Flowblade's theme/icon PNGs
    through that stack. Saving resources in a plain RGBA format keeps startup
    smoke tests and runtime icon loading consistent across distributions.
    '''
    converted = 0
    for png_file in sorted(root.rglob('*.png')):
        with Image.open(png_file) as image:
            if image.mode in {'RGB', 'RGBA'}:
                continue

            image.convert('RGBA').save(png_file)
            converted += 1

    return converted


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: normalize-pngs.py PNG_ROOT', file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    converted = normalize_pngs(root)
    print(f'Normalized {converted} PNG files under {root}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
