Flowblade
=========

[Features](https://github.com/jliljebl/flowblade/blob/master/README.md#features)

# Introduction #

Flowblade Movie Editor is a **multitrack non-linear video editor** for Linux released under GPL 3 license.

Flowblade is designed to provide a fast, precise and robust editing experience. In Flowblade clips are usually automatically placed tightly after or between clips when they are inserted on the timeline. Edits are fine tuned by trimming in and out points of clips, or by cutting and deleting parts of clips.

Flowblade provides powerful tools to mix and filter video and audio.

---

# Features #

Editing

  * 3 move tools
  * 3 trim tools
  * 4 methods to insert/overwrite/append a clip on the Timeline
  * Drag'n'Drop clips on the Timeline
  * Clip and Compositor parenting with other clips
  * Max 9 combined video and audio tracks available

Image compositing:

  * 7 compositors. Mix, zoom, move and rotate source video with keyframed animation tools
  * 19 blends. Stardand image blend modes like Add, Hardlight and Overlay are available
  * 41 pattern wipes. 

Image and audio filtering

  * 50+ image filters. Color correction, image effects, distorts, alpha manipulation, blur, edge detection, motion effects, freeze frame
  * 30+ audio filters. Keyframed volume mixing. Echo, reverb, distort and many other audio effects 

Supported editable media types

  * Most common video and audio formats
  * JPEG and PNG image file types
  * SVG vector graphics
    Numbered frame sequences 

Output encoding

  * depends on installed MLT/FFMPEG codec
  * User can define rendering by setting FFMpeg args 
        
# Releases #
**NEW RELEASE!** Flowblade Movie Editor 0.18 has been released on Mach 19, 2015

**NEXT RELEASE:** Flowblade 1.0 will be out between on May/June 2015.

---

# Installing Flowblade #


### Installing Debian Package ###

  * **Download .deb file** for Flowblade 0.18 from **[here](https://www.dropbox.com/s/v71v4e6y23dse2u/flowblade-0.18.0-1_all.deb?dl=0).**

  * Double Click on downloaded file to install.

*Please note: .deb file is in a Dropbox Public folder and may go over download limit, please contact Project Owner if this happens.*

### Supported OSes ###
  * This release has been tested on **Ubuntu 14.10**, **Ubuntu 14.04**, **Ubuntu 13.10**, **Linux Mint 17** and **Debian Testing (jessie/sid)**
  * May work on earlier Debian based systems

### Currently unsupported OSes ###
  * **Debian 7.2 or earlier**.  On these the application installed, but crashed on start-up, cause unknown. May work on some systems.

### Installing From Source Archive ###
  1. Donwload 0.18 source archive from [here](https://www.dropbox.com/s/qcw3gcyd6uioill/flowblade-0.18.0.tar.gz?dl=0).
  1. Extract archive into a folder of your choosing
  1. Install dependencies. See DependenciesList wiki for more information.
  1. Launch by running script **.../flowblade-0.18.0/flowblade** that was created in the folder where archive was unpacked
Flowblade is currently a 100% script application, and all the dependencies should be available in popular distributions, so in most cases it should be possible to install Flowblade without compiling anything.

*Please note: .tar.gz file is in a Dropbox Public folder and may go over download limit, please contact Project Owner if this happens.*

### Installing Developer Version ###

  1. Install Mercurial in your system.
  1. Use Mercurial to download Flowblade into a folder of your choosing by using the **hg clone** command in your terminal:
```
hg clone https://janne.liljeblad@code.google.com/p/flowblade/
```
  1. Install dependencies. See DependenciesList wiki for more information.
  1. Launch by running script **.../flowblade-trunk/flowblade** that was created in the folder where clone command was done.
Flowblade is currently a 100% script application, and all the dependencies should be available in popular distributions, so in most cases it should be possible to install Flowblade without compiling anything.

Developer version may however be unstable or have new dependencies. If you fail to install developer version, please file a bug in **Issues** -tab.

*NOTE: Using the available _setup.py_ script will NOT result in a successful installation, even if dependencies are installed, and may actually break the .deb install if attempted. It is only there to help .deb packaging.*

---

# Dependencies #

Below is a table of depencies listed in Ubuntu 14.10 tested .deb install package.

| *Debian/Ubuntu package name* | *Description* |
|------------------------------|---------------|
| gtk2-engines-pixbuf | Images handling |
| librsvg2-common | svg support |
| python-gtk2 | GTK+ python bindings |
| python-mlt | MLT python bindings, this pulls in MLT |
| python-dbus | dbus python bindings |
| libmlt-data | Some image and text resources for MLT |
| python 2.7 >= | Language and interpreter |
| frei0r-plugins | Additional video filters |
| swh-plugins | Additional audio filters |
| python-cairo | Cairo bindings |
| python-numpy | Math and arrays library |
| python-gnome2 | Python Gnome bindings |
| python-gobject-2 | GObject library bindings |


## Dropped  Dependencies ##

| *Debian/Ubuntu package name* | *Introduced* | *Dropped* |
|------------------------------|--------------|-----------|
| melt | 0.6  | 0.8 |
| fontconfig | 0.6  | 0.16 |

---

# Contributing a translation #

If you would like to have Flowblade translated into your language you can help by contributing a translation of Flowblade in your language.

### Installing developer version of Flowblade ###

To create a translation you must first install the repository version of Flowblade.

See wiki TestingRepositoryVersion.

### Creating a translation ###

Flowblade uses the standard [http://www.gnu.org/software/gettext/manual/gettext.html  GNU "gettext" utilities] to translate the application. GNU "gettext" is a relatively complex tool, but Flowblade provides a set of scripts that make it easier to create translations without using "gettext" directly.

  * Launch repository version of Flowblade and select *Help -> Environment* from menu to see the two letter locale code for your OS install. For example *fr* for French, *fi* for Finnish etc. Information is under the header *General*.
  * Open terminal in folder */flowblade-trunk/Flowblade/locale* that can be found in the folder you installed repository version of Flowblade in.
  * To create a new translation give a command in the terminal:
{{{
$ ./add_language LANGUAGE_CODE
}}} 
  in which LANGUAGE_CODE is the two letter language code for your locale.
  * A folder named with the LANGUAGE_CODE for your language was created in the */locale* folder
  * Inside that folder is a */LC_MESSAGES* folder in which there is a file called *Flowblade.po*. This is the file used to create the translation.
  * Open the file *Flowblade.po* in a text editor. Translations are given by writing the the translations inside quotes on lines staring with text *msgstr*. To traslate the menu item *Open...* you would need to fill the *msgstr* in example below: 
{{{
#: useraction.py:489
msgid "Open.."
msgstr ""
}}} 
  * To see the translations in the application, you need to compile them into a machine readable *.mo* file. Go to */locale* folder and give command:
{{{
$ ./compile_language LANGUAGE_CODE
}}}
  * Launch repository version of Flowblade to view your translations.

= Updating translation for new version of Flowblade =
 * Go to the */locale* folder and give command:
{{{
$ ./update_language LANGUAGE_CODE
}}}
 * Translate application as described above

### Contributing a translation
Send the created *Flowblade.po* file to janne.liljeblad@gmail.com. Please mention words Flowblade, translation and the LANGUAGE_CODE in the subject line. Translation will be in the next release.
