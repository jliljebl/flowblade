# Known Issues

This is list of bugs and defectes that are known to exist, but will probably not be fixed anytime soon.

#### 1. Selecting clip in timeline often blocks ability to drag / move / select tracks in awesomeWM

In awesomeWM there are often problems dragging clips. Instead of moving the clip, a file icon appears and is moved. 

The problem causing the bug is that awesome fires 'leave-notify-event' signals even when mouse has not left the timeline area.

**Status:** Problem is in another program, cannot be fixed in Flowblade

#### 2. Audio may be corrupted when first clip is not at complete beginning with H.264/mp4

Audio output (especially when using H.264 /mp4-codec and mp3 for audio) may be unusable when there is a (small) gap at the very beginning of video. The sound comes out distorted. After moving the first files to the first frame the audio plays correctly.

**Status:** No work is planned on this. This is almost guaranteed to be MLT or codec issue and as such cannot be fixed within Flowblade.


