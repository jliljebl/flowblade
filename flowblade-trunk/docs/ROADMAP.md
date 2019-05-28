# FLOWBLADE ROADMAP


## Technology updates
* **Python3 port**. This is coming for 2.4
* **Moving video display forward from SDL 1.2** Target is that 2.8 comes with this, late 2019 - early 2020

## Project "Ethel"
We should look for ways to make application more approachable for beginner users.

* **Drag'n'Drop source panel for Filers and Compositors**. We don't need this but many users seem to prefer it.
* **Trakcs auto compositioning** This has been proven to work on MLT and we should make it at least optional, see below.
* **Menus update** We can probably improve discoverability by adding and rearranging some menu items

## Application
- **Automatic Timeline Rendering** The only way to provide smooth playback in all circumstances. 
* multiscript tool, Cairo + GEGL + MLT ( + GMIC?)

## Compositing
See document **[Compositing 2 doc](./COMPOSITING_2.md)**


## Tools
* G'MIC pamater names and descriptions displayed on request, data exists we just need to extract it  somehow
* Rotomask Rotate mode
* Rotomask help-create Box ja Ellipse shapes from menu
* Titler Rotate Mode
* Titler text animations with motion blur

## Communications + code 
  * code overview doc
  * contributing code document 
  * improived code comments

## Possible later developments

* Gimp, Inkscape, Audacity, Krita examined as Timeline Container Clip media creator programs
* GPU Rendering, MLT already contains support for GPU rendering for certain filters
* subbuses or virtual channels to help with mixing.
* jack integration
* a 5.1 surround audio track mixing
- zig-zag layout auto audio splice out with handles
* configurable keyboard shortcuts

