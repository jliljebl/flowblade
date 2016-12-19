# FLOWBLADE ROADMAP

Last updated: Dec. 2016

## Timeline Tools

- **Sequence or Box Move Tool** Moves all clips contained in selected range or as defined by box selection as one group from multiple tracks. This will be the only multitrack edit tool available in Flowblade.
- **Ripple mode for trim tool** Moves all clips and compositors after trim point as long as no overwrites happen. This is *mode* for Trim tool and is to be toggled on and off.

## Animation
- MLT keyframe types *bezier* and *step* to be made available in addition to current linear type keyframes for all keyframe editors
- 100% coverage for keyframe editing for float value paramaters. A light weight editor component needs to made for cases where keyframe editing is the secondary 

## Tracks
- **Track filters stack** for both video and audio tracks.

## Filters
- **AVFilters** These are availaBLe in MLT 6.2.0. Color Channels Mixer and 3dLUT are the most interesting filters available
- Contribute **Cairo filters for MLT**. Spotligt, animated producer, animated averlay filter, animated alpha and affine transform filter seem most interesting. Frei0r is not an adequate platform for some of these.
- **Selective Filter Application**, this function allows user to apply any filter only inside an area defined by alpha filters. This can currently be simulated with two clips. Requires MLT contribution.

## Compositing

- **Animated Image to Alpha**, combines two images sources using luma information from a third source, probably a frame sequence
- animated line/curve masks, this may also be best done using **Cairo**.  Requires MLT contribution.
- add to all alpha filters composing methods union, intersection, difference and exclusion.  Requires MLT and Frei0r contribution.

## Multiclip functonality
- create Compound clips from selections and full sequences
- make possible to combinen sequences with insett and append functions

## Tools development

- multispeed reversed clips tool
- Titler tool improvements: drop shadow with blur color outline.
- dedicated masking keying tool

## Tool integration
- **Timeline Contaier Clips** with data on original media, tool program data, rendered media and rendered media offset known and saved. Combine with polling for automatic prompts for update on render completion.
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
- Disk Cache Manager. Data in hidden folder can become quite big eventually, and controlling it from application would be useful

## Project data

- import media data from one project into another project

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
	

	
	
