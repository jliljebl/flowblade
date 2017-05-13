# FLOWBLADE ROADMAP

Last updated: May. 2017


## Tracks
- **Track filters stack** for both video and audio tracks.

## Filters
- Contribute **filters for MLT**. Spotligt, affine transform filter seem most interesting. Frei0r is not an adequate platform for some of these. may require using Cairo.
- **Selective Filter Application**, this function allows user to apply any filter only inside an area defined by alpha filters. This can currently be simulated with two clips. Requires MLT contribution.

## Compositing

- **Animated Image to Alpha**, combines two images sources using luma information from a third source, probably a frame sequence
- animated line/curve masks, this may also be best done using **Cairo**.  Requires MLT contribution.
- add to all alpha filters composing methods union, intersection, difference and exclusion.  Requires MLT and Frei0r contribution.

## Tools development
- dedicated masking/keying tool
- FFMPEG copy rendering tool

## Tool integration
- **Timeline Container Clips** with data on original media, tool program data, rendered media and rendered media offset known and saved. Combine with polling for automatic prompts for update on render completion.
- **Media Item creation** from ready made programs for e.g. text animations with Natron
- Gimp, Inkscape, Audacity, Krita examined as **Timeline Container Clip** media creator programs

## Audio
- audio scratching on playback
- subbuses or virtual channels to help with mixing.
- a 5.1 surround audio track mixing
- synching audio with audio
- jack integration

## Editor functionality

- Configurable Keyboard Shortcuts.


## Packaging

- Appimage, Snap, Flatpack. Appimage is done first, Snap second and Flatpack is assessed last.

## Communications

- translations workflow update. 
- website update
- 5 - 10 tutorial videos on some important workflow issues
- forum with threads


## Technical development
- **GPU Rendering** MLT already contains support for GPU rendering for certain filters
- The **Wayland** transition using SDL2 or OpenGL consumer. SDL2 consumer does not exist and would need to be contributed.
	


*Changelog*
- *13-5-17 Remove undoable items related to animating property values in in MLT, require too large MLt controinutions for the time being*
- *13-5-17 Remove completed items and items that will be in 1.14*
- *13-5-17 Add change log*
	
