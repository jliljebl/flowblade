# FLOWBLADE ROADMAP






# FIRST





## Application
- **Automatic Timeline Rendering** The only way to provide smooth playback in all circumstances is to do some form of timeline rendering. There are some ideas here that will be attempted, but cannot be quaranteed to work beforehand.
* **Rotomask**
* fully Configurable Keyboard Shortcuts
* some key parts need expanded code comments.
* multiscript tool



## MLT + Frei0r
- **New display MLT service or method**. SDL1.2 is eventually going away. SDL2 or some GStremer sink as base for a new consumer, also Issues #309 #329 
- add to all *alpha filters* compositing methods **union, intersection, difference and exclusion.**  Requires MLT and Frei0r contribution.
- **Animated Image to Alpha**, combines two images sources using luma information from a third source, probably a frame sequence
* Image producer that doesn't lose data before affine transform is applied.
* Porter-Duff MLT transition
* full affine transform filter with user settable anchor point.

## Stability
  * update and test GDB trace creation instructions document
* collect more data with GDB from affected systems
* bisect if reproduces, try to get some hypothesis if not reproducable

## Communications
####Flowblade contributing documentation

  * contributing code document 
  * code overview doc

#### Forum
GitHub project Issue tab functionality modifed to work as a forum, Google+ is going away.

* Labels used to create subject categories
* copy some data from Google+ forum


# LATER

- Gimp, Inkscape, Audacity, Krita examined as **Timeline Container Clip** media creator programs
- **GPU Rendering** MLT already contains support for GPU rendering for certain filters
- subbuses or virtual channels to help with mixing.
- jack integration
- a 5.1 surround audio track mixing
- **Audio scratching** on timeline. #95
- **Track filters stack** for both video and audio tracks.
- **Selective Filter Application**, this function allows user to apply any filter only inside an area defined by alpha filters. This can currently be simulated with two clips. Requires MLT contribution.
- Contribute **filters for MLT**. Spotligt, affine transform filter seem most interesting. Frei0r is not an adequate platform for some of these. may require using Cairo.

# 2.x SERIES AND PYTHON3

There will be 4-7 releases to essitially complete feature list here, then on to Python 3 port which will be Flowblade 3. 
