# Road map
This document gives a broad overview what's happening next in Flowblade development. For more information see open Issues on the Issues tab.

*Last updated: September 13, 2015*

## Next release (1.4)
*Estimated release date is November 2015.*

**All audio levels displayed and rendered on background process** Some users were not happy with the "display levels on request" model that we had before.

**Rendered fade/transition delete update** Make fades and transitions automatically cover the gap left with material from source clip(s) if possible.

**Clip drag-and-drop to do overwrite when clip dopped after the last clip on track** Now user needs to move clips manually to position and often they wish to drop clip into certain position on timeline.

**Trimming with arrow keys** In many cases this will be more a precise and relaxed way of choosing in and out frames for trims.

### Coming features in the next few releases

**Keyframe editing on the timeline** This is mainly provided for the purpose of audio mixing that can be done more naturally on the timeline. Other parameters may later be also made editable on the timeline.

**Audio Scrubbing** This will make editing audio on the timeline easier.

**Compositioning and masking tool** A dedicated tool for masking and simple compositioning will be provided instead of making the timeline editing more complex by adding these features as part of the main workflow.

**Single filter resizing** This is a frequently asked feature.

**Slowmotion forward playback for JKL scrubbing** This needs special casing to work for technical reasons, and because of that has not been added so far.

**EDL Export** We need some subset of this feature, mainly to work with Blender.

### Long term developments

**GPU Rendering** MLT already contains support for GPU rendering and it has been used by Shotcut for a while, but my experience has been that it is quite unstable. It may work well with some combinations of Qt version, graphics card and drivers but other combinations may be unusably crashy. 

The Wayland transition should probably be completed too before this is attempted. Currently the earliest date that this will be looked at looks to be early 2017.

**Webpage** The content for this mostly already exists. 
