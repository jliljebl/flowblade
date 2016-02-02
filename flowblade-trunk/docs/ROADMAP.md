# Roadmap
This document gives a broad overview what's happening next in Flowblade development. For more information see open Issues on the Issues tab.

*Last updated: Feb 1, 2016*

### Short term 

**Webpage** The content for this mostly already exists.

### Medium term

**Natron Integration** The Natron compositor seems very powerful and has programmable headless rendering which will make it possible to be integrate it with Flowblade to create for example animated text effects.

**Big translations update** Translations have currently some issues that shoud all be fixed in one go, possible adding some net based translation tool to make crating translations easier at the same time.

**Trimming with arrow keys** In many cases this will be more a precise and relaxed way of choosing in and out frames for trims.

**Audio Scrubbing** This will make editing audio on the timeline easier.

**Single filter resizing** This is a frequently asked feature.

**Slowmotion forward playback for JKL scrubbing** This needs special casing to work for technical reasons, and because of that has not been added so far.

 

### Long term

**GPU Rendering** MLT already contains support for GPU rendering and it has been used by Shotcut for a while, but my experience has been that it is quite unstable. It may work well with some combinations of Qt version, graphics card and drivers but other combinations may be unusably crashy. 

The Wayland transition should probably be completed too before this is attempted. Currently the earliest date that this will be looked at looks to be early 2017.


