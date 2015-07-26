# Road map
This document gives a broad overview what's happening next in Flowblade development. For more information see open Issues on the Issues tab.

*Last updated: July 27, 2015*

## Next release (1.2)
*Estimated release date is September - November 2015.*

**GTK3+ port** This release cycle will focus solely on porting the application to GTK3.

### Coming features in the next few releases

**Keyframe editing on the timeline** This is mainly provided for the purpose of audio mixing that can be done more naturally on the timeline. Other parameters may later be also made editable on the timeline.

**Rendered fade/transition delete update** Make fades and transitions automatically cover the gap left with material from source clip(s) if possible.

**Audio Levels display enhancement** This still needs to be improved.

**Audio Scrubbing** This will make editing audio on the timeline easier.

**Compositioning and masking tool** A dedicated tool for masking and simple compositioning will be provided instead of making the timeline editing more complex by adding these features as part of the main workflow.

**Single filter resizing** This is a frequently asked feature.

**Trimming with arrow keys** In many cases this will be more a precise and relaxed way of choosing in and out frames for trims.

**Slowmotion forward playback for JKL scrubbing** This needs special casing to work for technical reasons, and because of that has not been added so far.

**EDL Export** We need some subset of this feature, mainly to work with Blender.

### Long term developments

**GPU Rendering** MLT already contains support for GPU rendering and it has been used by Shotcut for a while, but my experience has been that it is quite unstable. It may work well with some combinations of Qt version, graphics card and drivers but other combinations may be unusably crashy. 

The Wayland transition should probably be completed too before this is attempted. Currently the earliest date that this will be looked at looks to be early 2017.

**Webpage** The content for this mostly already exists. 
