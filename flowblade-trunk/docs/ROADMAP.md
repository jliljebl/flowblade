# FLOWBLADE ROADMAP

Last updated: September. 2017

## The 2.0 FEATURE SET
- **New display MLT service or method**. SDL1.2 will be eventually lost as SDL2 is made default on all distros.This is part of the solution for several issues. #309 #329 
- **Performance review and needed fixes** This needs some investigation and it needs to be made sure that the new display method is as performant as possible.
- **Automatic Timeline Rendering** The only way to provide smooth playback in all circumstances is to do some form of timeline rendering. There are some ideas here that will be attempted, but cannot be quaranteed to work beforehand.
- **Proxy Editing** should have all important improvements. #398 
- **Audio scratching** on timeline. #95
- **Dedicated masking/keying/full affine tool and/or new MLT services** to close related functionality gaps. #372 

- **Animation and compositing updates** This needs to be taken to next level for 2.0.
- **Remove a number of preferences and options** We have so far only added options and preferences, now it is time look carefully what could be removed to simplify and clarify the UX.
- **Translations workflow update** These need the easiest, most moders workflows available.
- **Website update** Some existing features are missing, add *Contributing* text.

### 2.0 Completed items
- **Binary packaging** At least one of Appimage, Snap, Flatpack. #453 **DONE, 1.16, we now have Flatpak, others can be added if we get contributions**
- **Autofollow compositors** Compositors will be made to follow their origin clips automatically if user so chooses.**DONE, 1.16**
- **Context sensitive Timeline tool cursor** This was originally part of non-features list of the design, but it seems that users prefer this, and we will look for a way to incoporate this with current design. #424 **DONE, 1.16**

### Other possible developments
- **Track filters stack** for both video and audio tracks.
- Contribute **filters for MLT**. Spotligt, affine transform filter seem most interesting. Frei0r is not an adequate platform for some of these. may require using Cairo.
- **Selective Filter Application**, this function allows user to apply any filter only inside an area defined by alpha filters. This can currently be simulated with two clips. Requires MLT contribution.
- **Animated Image to Alpha**, combines two images sources using luma information from a third source, probably a frame sequence
- add to all alpha filters composing methods union, intersection, difference and exclusion.  Requires MLT and Frei0r contribution.
- **Configurable Keyboard Shortcuts**
- **Media Item creation** from ready made programs for e.g. text animations with Natron
- Gimp, Inkscape, Audacity, Krita examined as **Timeline Container Clip** media creator programs
- subbuses or virtual channels to help with mixing.
- a 5.1 surround audio track mixing
- synching audio with audio
- jack integration
- 5 - 10 tutorial videos on some important workflow issues
- forum with threads
- **GPU Rendering** MLT already contains support for GPU rendering for certain filters
	


*Changelog*
- *1-4-2018 Mark done items and add animations and prefs dropping for 2.0*
- *14-11-2017 Change document focus to 2.0 feature set*
- *20-9-2017 drop FFMpeg tool, Container clips are done, add Editing section*
- *13-5-17 Remove undoable items related to animating property values in in MLT, require too large MLt controinutions for the time being*
- *13-5-17 Remove completed items and items that will be in 1.14*
- *13-5-17 Add change log*
	
