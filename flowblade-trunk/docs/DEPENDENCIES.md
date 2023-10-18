# Flowblade Package Dependencies #

| **Description** | **Debian package name** | **Ubuntu package name** | **Archlinux packages** |
|:--------------------------------|:----------------|:--------------|:--------------|
| GTK3 Python bindings | [``python3-gi``](https://packages.debian.org/unstable/python3-gi) | [``python3-gi``](https://packages.ubuntu.com/jammy/python3-gi) | [``python-gobject``](https://archlinux.org/packages/extra/x86_64/python-gobject/) |
| MLT python bindings, this pulls in MLT. MLT version 7.0 required, >= 7.12 recommended  | [``python3-mlt``](https://packages.debian.org/unstable/python3-mlt) | [``python3-mlt``](https://packages.ubuntu.com/jammy/python3-mlt) | [``mlt``](https://archlinux.org/packages/extra/x86_64/mlt/) |
| Decoder/Encoder application | [``ffmpeg``](https://packages.debian.org/unstable/ffmpeg) | [``ffmpeg``](https://packages.ubuntu.com/jammy/ffmpeg) | [``ffmpeg``](https://archlinux.org/packages/extra/x86_64/ffmpeg/) |
| DBus python bindings | [``python3-dbus``](https://packages.debian.org/unstable/python3-dbus) | [``python3-dbus``](https://packages.ubuntu.com/jammy/python3-dbus) |  [``dbus-python``](https://archlinux.org/packages/extra/x86_64/dbus-python/) |
| Some image and text resources for MLT | [``libmlt-data``](https://packages.debian.org/unstable/libmlt-data) | [``libmlt-data``](https://packages.ubuntu.com/focal/libmlt-data) | [``mlt``](https://archlinux.org/packages/extra/x86_64/mlt/), sdl_image |
| Language and interpreter | [``python3``](https://packages.debian.org/unstable/python3) | [``python3``](https://packages.ubuntu.com/jammy/python3) | [``python``](https://archlinux.org/packages/core/x86_64/python/) |
| Additional video filters | [``frei0r-plugins``](https://packages.debian.org/unstable/frei0r-plugins) | [``frei0r-plugins``](https://packages.ubuntu.com/jammy/frei0r-plugins) | [``movit``](https://archlinux.org/packages/extra/x86_64/movit/), [``frei0r-plugins``](https://archlinux.org/packages/extra/x86_64/frei0r-plugins/) |
| Additional audio filters | [``swh-plugins``](https://packages.debian.org/unstable/swh-plugins) | [``swh-plugins``](https://packages.ubuntu.com/jammy/swh-plugins) |  [``sox``](https://archlinux.org/packages/extra/x86_64/sox/), [``swh-plugins``](https://archlinux.org/packages/extra/x86_64/swh-plugins/) |
| Gi Cairo bindings | [``python3-gi-cairo``](https://packages.debian.org/unstable/python3-gi-cairo) | [``python3-gi-cairo``](https://packages.ubuntu.com/kinetic/python3-gi-cairo) |  [``python-cairo``](https://archlinux.org/packages/extra/x86_64/python-cairo/) |
| Math and arrays library | [``python3-numpy``](https://packages.debian.org/stable/python3-numpy) | [``python3-numpy``](https://packages.ubuntu.com/jammy/python3-numpy) | [``python-numpy``](https://archlinux.org/packages/extra/x86_64/python-numpy/) |
| PIL image manipulation library | [``python3-pil``](https://packages.debian.org/unstable/python3-pil) | [``python-pil``](https://packages.ubuntu.com/jammy/python3-pil) | [``python-pillow``](https://archlinux.org/packages/extra/x86_64/python-pillow/) |
| svg support | [``librsvg2-common``](https://packages.debian.org/unstable/librsvg2-common) | [``librsvg2-common``](https://packages.ubuntu.com/kinetic/librsvg2-common) | [``librsvg``](https://archlinux.org/packages/extra/x86_64/librsvg/) |
| framework for image processing | [``gmic``](https://packages.debian.org/unstable/gmic) | [``gmic``](https://packages.ubuntu.com/jammy/gmic) | [``gmic``](https://archlinux.org/packages/extra/x86_64/gmic/) |
| Glib |  [``gir1.2-glib-2.0``](https://packages.debian.org/unstable/gir1.2-glib-2.0) |  [``gir1.2-glib-2.0``](https://packages.ubuntu.com/jammy/gir1.2-glib-2.0) | [``dbus-glib``](https://archlinux.org/packages/extra/x86_64/dbus-glib/) ??? |
| Gtk toolkit | [``gir1.2-gtk-3.0``](https://packages.debian.org/unstable/gir1.2-gtk-3.0) | [``gir1.2-gtk-3.0``](https://packages.ubuntu.com/jammy/gir1.2-gtk-3.0) |  [``gtk3``](https://archlinux.org/packages/extra/x86_64/gtk3/) |
| Pango text lib | [``gir1.2-pango-1.0``](https://packages.debian.org/unstable/gir1.2-pango-1.0) | [``gir1.2-pango-1.0``](https://packages.ubuntu.com/jammy/gir1.2-pango-1.0) |  [``pango``](https://archlinux.org/packages/extra/x86_64/pango/) |
| Image support | [``gir1.2-gdkpixbuf-2.0``](https://packages.debian.org/unstable/gir1.2-gdkpixbuf-2.0) | [``gir1.2-gdkpixbuf-2.0``](https://packages.ubuntu.com/jammy/gir1.2-gdkpixbuf-2.0) |  [``gdk-pixbuf2``](https://archlinux.org/packages/extra/x86_64/gdk-pixbuf2/) |

# Dropped  Dependencies #

| **Debian/Ubuntu package name** | **Introduced** | **Dropped** |
|:-------------------------------|:---------------|:------------|
| melt | 0.6  | 0.8 |
| fontconfig | 0.6  | 0.16 |
| python-gtk2 |  0.6   | 1.2 |
| gtk2-engines-pixbuf |  0.6   |  1.2 |
| python-gnome2 |  0.6   |  1.2 |
| python-gobject-2 |  0.6   |  1.2 |
| python-cairo |  0.6   |  1.6 |
