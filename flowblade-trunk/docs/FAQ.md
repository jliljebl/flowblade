# FAQ

**Contents**

  1. [Alpha Filters do not work](./FAQ.md#alpha-filters-do-not-work)
  1. [Crop filter does not work](./FAQ.md#crop-filter-does-not-work)
  2. [How can I move clips around freely?](./FAQ.md#how-can-i-move-clips-around-freely)
  3. [Will there be Windows or OSX versions?](./FAQ.md#will-there-be-windows-or-osx-versions)
  4. [Rendering with a profile with different framerate changes video playback speed and loses audio sync](./FAQ.md#rendering-with-a-profile-with-different-framerate-changes-video-playback-speed-and-loses-audio-sync)

### Alpha Filters do not work

In Flowblade Alpha filters write into images alpha channel and have no effect unless used in combination with Compositors to combine two images.

Alpha channel in images exits for the sole purpose of compositing two images. If image is not part of a composite, the data in alpha channel has no purpose and does not affect output.

**Select "Add Compositor" -> "Dissolve" from clip popup menu** to composite e.g. clip on track V2 on a clip on track V1 and add Alpha filter into clip on track V2 to see Alpha filters working.

### Crop filter does not work

Are you trying zoom in a bit and use part of the image instead of the whole image?
If this is the case then you should use filter **Affine** in filter group **Transform** and set properties *Scale X, Scale Y, X, Y*.

If you are trying to crop an image in the sense that you want to cut part of the image out, then you must use a Compositor and composite the image you are trying to crop on top of another image or perhaps a black color producer.


### How can I move clips around freely?

Use the **Overwrite** tool.

Click on timeline and press **2** on keyboard or use the **Tool Select Menu** in the middlebar next to the timecode display.

### Will there be Windows or OSX versions?

These are not currently planned. If in the future the port effort is reasonable, does not have adverse effects on the code base and someone provides quality patches, then those patches can probably be accepted.


### Rendering with a profile with different framerate changes video playback speed and loses audio sync

Yes, this will happen. When rendering the video frames are just copied, no complex slowdown/speedup prosessing is done, and audio is **not** resampled.

To maintain sync and playback both Project Profile and Render Profile both need to match the frame rate of original material.  

