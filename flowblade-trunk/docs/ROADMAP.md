# Roadmap
This document gives a broad overview what's happening next in Flowblade development. For more information see open Issues on the Issues tab.

*Last updated: Sept. 16, 2016*

### Next

**Increasing Tools Integration** Flowblade's standalone tools and  external tools like Natron will be increasingly integrated with the timeline. There are three levels of integration here, and development will go on to increase integration one level at a time:
  * **Clip and Range export** for. e.g. user can open a timeline clip on G'MIC effects tool
  * **Auto-update on render completion** So after havin applied an effect to a timeline clip it will be automatically updated on timeline
  * **Continuos synchronization** Heve doing changes on timeline clips previously set as clips containing extrenal tool rendering, will cause automatic rerenders to happen.For samo tools this will require additinal IPC interface that is not yet available.

**Compound clips** It should possible to make selected range and other sequences in the project available as compound clips

**Audio Scrubbing** This will make editing audio on the timeline easier.

**Single filter resizing** This is a frequently asked feature.

**Slowmotion forward playback for JKL scrubbing** This needs special casing to work for technical reasons, and because of that has not been added so far.

**Trim edit view** This may be possible with current available APIs and will be attempted.

### Long term

**GPU Rendering** MLT already contains support for GPU rendering and it has been used by Shotcut for a while, but my experience has been that it is quite unstable. It may work well with some combinations of Qt version, graphics card and drivers but other combinations may be unusably crashy.

**Big translations update** Translations have currently some issues that shoud all be fixed in one go, possible adding some net based translation tool to make crating translations easier at the same time.

The Wayland transition should probably be completed too before this is attempted. Currently the earliest date that this will be looked at looks to be early 2017.


