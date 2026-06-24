#!/usr/bin/env python3

import sys
from pathlib import Path

import gi

gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: probe-gdk-pixbuf.py PNG_FILE', file=sys.stderr)
        return 2

    png_file = Path(sys.argv[1])
    header = png_file.read_bytes()[:16].hex()
    print(f'  PNG file: {png_file} size={png_file.stat().st_size} header={header}')

    formats = GdkPixbuf.Pixbuf.get_formats()
    png_format = next((fmt for fmt in formats if fmt.get_name() == 'png'), None)
    if png_format is not None:
        print(
            '  GdkPixbuf png format: '
            f'disabled={png_format.is_disabled()} '
            f'extensions={",".join(png_format.get_extensions())} '
            f'mimes={",".join(png_format.get_mime_types())}'
        )

    format_names = ','.join(fmt.get_name() for fmt in formats)
    print(f'  GdkPixbuf formats: {format_names}')

    GdkPixbuf.Pixbuf.new_from_file(str(png_file))
    print('  GdkPixbuf PNG probe: ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
