#FAQ#

**Contents**

  1. [Crop filter does not work](./FAQ.md####crop-filter-does-not-work)
  2. [Will there be Windows or OSX versions](./FAQ.md####will-there-be windows-or-OSX-versions)
  
#### Crop filter does not work

Are you trying zoom in a bit and use part of the image instead of the whole image?
If this is the case then you should use filter **Affine** in filter group **Transform** and set properties *Scale X, Scale Y, X, Y*.

If you are trying to crop an image in the sense that you want to cut part of the image out, then you must use a Compositor and composite the image you are trying to crop on top of another image or perhaps a black color producer.

  
#### Will there be Windows or OSX versions?

These are not currently planned. If in the future the port effort is reasonable, does not have adverse effects on the code base and someone provides quality patches, then those patches can probably be accepted.
