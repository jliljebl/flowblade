# Installing Flowblade #

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
  * If you have Flowblade installed in your system, you probably have the dependencies installed, unless some new ones have been added.
  * Launch by running script .../flowblade-0.18.0/flowblade that was created in the folder where archive was unpacked.
  * Note that if you have Flowblade installed you will need use full path to repository version or navigate to the folder containing launch script and use command "./flowblade" to launch repository version instead of installed version.

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
  * If you have Flowblade installed in your system, you probably have the dependencies installed, unless some new ones have been added.
  * Launch by running script ``.../flowblade-trunk/flowblade`` that was created in the folder where clone command was done.
  * Note that if you have Flowblade installed you will need use full path to repository version or navigate to the folder containing launch script and use command "./flowblade" to launch repository version instead of installed version
 
*Please note: Using the available setup.py script will NOT result in a successful installation, even if dependencies are installed, and may actually break the .deb install if attempted. It is only there to help .deb packaging.* 
