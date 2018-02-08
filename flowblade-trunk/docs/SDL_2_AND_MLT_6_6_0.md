# Flowblade, SDL 2 and MLT 6.6.0 and later

**MLT 6.6.0 and later need to be compiled with SDL 1.2 support for Flowblade to work.**

There were some developments with Flowblade, SDL and MLT from autumn 2017 onwards, here are the main points:

1. All releases of MLT up until 6.4.1 used SDL 1.2 in "sdl" module for Flowblade related video display.
2. Autumn 2017 MLT switched to using SDL 2.0 in module "sdl". This broke Flowblade video display.
3. SDL 2.0 dropped YUV overlay API used by Flowblade video display consumer, and SDL 2.0 does not provide similar functionality.
4. For release 6.6.0 MLT switched to having two SDL related modules: "sdl" and "sdl2".
5. The "sdl" module uses SDL 1.2 and this module needs to be compiled into MLT 6.6.0 for Flowblade to work.
6. Both "sdl" and "sdl2" modules can be compiled into MLT 6.6.0

An example of switches for compiling MLT with SDL 1.2 support can be found in this Flatpak definition file: https://github.com/flathub/io.github.jliljebl.Flowblade/blob/master/io.github.jliljebl.Flowblade.json
