# Known Issues

This is list of bugs and defectes that are known to exist, but will probably not be fixed anytime soon.

#### 1. Selecting clip in timeline often blocks ability to drag / move / select tracks in awesomeWM

In awesomeWM there are often problems dragging clips. Instead of moving the clip, a file icon appears and is moved. 

The problem causing the bug is that awesome fires 'leave-notify-event' signals even when mouse has not left the timeline area.

**Status:** Problem is in another program, cannot be fixed in Flowblade

#### 2. Audio may be corrupted when first clip is not at complete beginning with H.264/mp4

Audio output (especially when using H.264 /mp4-codec and mp3 for audio) may be unusable when there is a (small) gap at the very beginning of video. The sound comes out distorted. After moving the first files to the first frame the audio plays correctly.

**Status:** No work is planned on this. This is almost guaranteed to be MLT or codec issue and as such cannot be fixed within Flowblade.

#### 3. Changing profile for rendering changes image scaling / positioning for compositors.

Compositors and filters receive broken image scaling and positioning if project profile is changed for rendering.

The problem is that the relevant data is saved as absolute pixel values, not as 0-1 normalized floats. Changing the render profile does not change the positioning or scaling correctly, e.g 50 px X-position is different image position for HD and SD images.

The current proposed solution is to render using original profile and re-render to desired dimensions.

**Status:** No work is planned on this. An acceptable work around exists, and a fix would require large de-stabilizing changes all over the code base.

#### 4. mov/xdcam422 clips with high bitrate  (50000kb/s) may not work with proxy editing
This has been reported and a single case has been reproduced.

**Status:** No work on a fix is planned.

#### 5. Using Affine filter on .png file may result in image errors 
Image describing issue here: http://i.xomf.com/rfncv.png

**Status:** No work on a fix is planned. *Affine* filter is not part rodamap on improving Flowblade's motion graphics capabilities and will not be worked on.


#### 6. Title causes distortion in mixed aspect ratio project

Problem is described in Issue #258.

**Status:** Some fix may be attempted later.

#### 7. MLT 6.4.0 crashes with terminal output: "ERROR: /usr/lib/python2.7/dist-packages/_mlt.x86_64-linux-gnu.so: undefined symbol: _ZNK3Mlt7Profile8is_validEv"

In systems running MLT 6.4.0 Flowblade does not start, more info on issue here: https://plus.google.com/u/0/102624418925189345577/posts/7ANDDW3hzHB?sfc=true

**Status:** This is fixed upstream, make sure to use MLT 6.4.1 or higher.


#### 8. Lock up when exporting frame from file with size 640x360 with Project Profile being 4K UHD 2160p 30fps

More here: https://github.com/jliljebl/flowblade/issues/517

**Workaround:** Re-encode 640x360 into bigger size.

**Status:** No work on a fix is planned.
