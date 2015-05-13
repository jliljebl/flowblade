![Flowblade](flowblade-trunk/Flowblade/res/img/header_text.png "Flowblade")

**Contents:**
  1. [Introduction](https://github.com/jliljebl/flowblade#introduction)
  1. [Features](https://github.com/jliljebl/flowblade#features)
  1. [Releases](https://github.com/jliljebl/flowblade#releases)
  1. [Installing Flowblade](https://github.com/jliljebl/flowblade#installing-flowblade)
  1. [Docs](https://github.com/jliljebl/flowblade#docs)
  1. [Screenshot](https://github.com/jliljebl/flowblade#screenshot)
  1. [Contact](https://github.com/jliljebl/flowblade#contact)

# Introduction

Flowblade Movie Editor is a **multitrack non-linear video editor** for Linux released under **GPL 3 license**.

Flowblade is designed to provide a fast, precise and robust editing experience. Flowblade  employs film-style insert editing model for workflow. In insert editing clips are generally placed tightly after other clips when they are inserted on the timeline. Edits are fine tuned by trimming in and out points of clips or by cutting and deleting parts of clips.

Flowblade provides powerful tools to mix and filter video and audio.

# Features

Editing:

  * 3 move tools
  * 3 trim tools
  * 4 methods to insert / overwrite / append clips on the Timeline
  * Drag'n'Drop clips on the Timeline
  * Clip and compositor parenting with other clips
  * Max. 9 combined video and audio tracks available

Image compositing:

  * 7 compositors. Mix, zoom, move and rotate source video with keyframed animation tools
  * 19 blends. Stardand image blend modes like Add, Hardlight and Overlay are available
  * 40+ pattern wipes. 

Image and audio filtering:

  * 50+ image filters. Color correction, image effects, distorts, alpha manipulation, blur, edge detection, motion effects, freeze frame, etc.
  * 30+ audio filters. Keyframed volume mixing. Echo, reverb, distort, etc.

Supported editable media types:

  * Most common video and audio formats, depends on installed MLT/FFMPEG codecs
  * JPEG, PNG, TGA, TIFF graphics file types
  * SVG vector graphics
  * Numbered frame sequences 

Output encoding:

  * Most common video and audio formats, depends on installed MLT/FFMPEG codecs
  * User can define rendering by setting FFMpeg args individually
        
# Releases

**Latest release:** Flowblade Movie Editor 0.18 was released on March 19, 2015.

**Next release:** Flowblade Movie Editor 1.0 will be out on May/June 2015.

# Installing Flowblade

The latest release is **Flowblade 0.18**, released on March 19, 2015

### Installing from your OS repository

The easiest way to install Flowblade is using the version in your OS repository. The downside is that the version available may not be the current latest release. Contact your OS to get Flowblade included in repositories if not already available.

### Installing using .deb package

**First download .deb file** for Flowblade 0.18 from <a href="https://www.dropbox.com/s/v71v4e6y23dse2u/flowblade-0.18.0-1_all.deb?dl=0">here.</a>  

<ul>
    <li>Double Click on the downloaded .deb file to install.</li>
</ul>

Release has been tested on: <b>Ubuntu 15.05, Linux Mint 17, Debian jessie/sid.</b>
Other recent Debian based systems should work too.

*Please note: The .deb file is in a Dropbox Public folder and may go over download limit, please contact Project Owner if this happens.*


### Installing Using Source Code Archive

Flowblade is currently a 100% script application, and all the dependencies should be available in popular distributions, so in most cases it should be possible to install and run Flowblade without compiling anything.

**First download 0.18 .tar.gz** source archive file from <a href="https://www.dropbox.com/s/qcw3gcyd6uioill/flowblade-0.18.0.tar.gz?dl=0">here.</a> 

  * Extract archive into a folder of your choosing
  * Install dependencies. See [Dependencies](./flowblade-trunk/docs/DEPENDENCIES.md) doc for more information.
  * Launch by running script .../flowblade-0.18.0/flowblade that was created in the folder where archive was unpacked.

*Please note: .tar.gz file is in a Dropbox Public folder and may go over download limit, please contact Project Owner if this happens.*

### Installing Using Development Repository Version

Flowblade is currently a 100% script application, and all the dependencies should be available in popular distributions, so in most cases it should be possible to install and run Flowblade without compiling anything.

Developer version may however be unstable or have new dependencies. If you fail to install developer version, please file a bug in Issues -tab.
  * Install Git in your system (Ubuntu command):
```bash
sudo apt-get install git
```
  * Use Git to download Flowblade into a folder of your choosing by using the git clone command in your terminal:
```bash
git clone https://github.com/jliljebl/flowblade.git
```
  * Install dependencies. See   [Dependencies](./flowblade-trunk/docs/DEPENDENCIES.md) doc for more information.
  * Launch by running script ``.../flowblade-trunk/flowblade`` that was created in the folder where clone command was done.

*Please note: Using the available setup.py script will NOT result in a successful installation, even if dependencies are installed, and may actually break the .deb install if attempted. It is only there to help .deb packaging.* 

# Docs

[FAQ](./flowblade-trunk/docs/FAQ.md)

[Roadmap](./flowblade-trunk/docs/ROADMAP.md)

[Release notes](./flowblade-trunk/docs/RELEASE_NOTES.md)

[Creating a translation](./flowblade-trunk/docs/CREATING_TRANSLATION.md)

[Dependencies](./flowblade-trunk/docs/DEPENDENCIES.md)



# Screenshot

[Screenshot](./flowblade-trunk/docs/Screenshot-0-18.png) for version is 0.18 is available in the */docs* folder.

# Contact

Use the **Issues** tab on the right to give bug reports or to make feature requests.

If needed, you can contact project lead for additional information: janne.liljeblad@gmail.com
