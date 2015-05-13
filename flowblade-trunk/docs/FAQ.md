#FAQ#

##### "Crop" filter does not work**

Are you trying zoom in a bit and use part of the image instead of the whole image?
If this is the case then you should use filter **Affine** in filter group **Transform** and set properties *Scale X, Scale Y, X, Y*.

If you are trying to crop an image in the sense thatyou want to cut part of the image out, then you must a a Compositor and composite the image you are trying to crop on top of another image or perhaps a black color producer.

  
