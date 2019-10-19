
## Building Python 3 bindings to use with repo installation

This is a rough guide on how install and run self created MLT bindinds with Flowblade install from repository.

Please create pull request against this document if you have corrections or additions to improve this guide.

### Install Flowblade from repository
See [here](./INSTALLING.md).

### Install MLT build dependencies
Here is list of Ubuntu depencies. There could be some omissions, please file pull request to update the list if something is found to be missing.

```bash
sudo apt-get install git swig python3-dev python3-numpy libxml2-dev libsdl-dev 
libavdevice-dev libswscale-dev libvorbis-dev libsamplerate-dev 
frei0r-plugins-dev libdv-dev libavformat-dev libquicktime-dev 
libsox-dev libjack-dev ladspa-sdk
```

### Create work directory 

Let's call this directory **\<ROOT_DIR\>**. Open terminal in this directory

### Clone MLT repository
```bash
git clone git://github.com/mltframework/mlt.git
```

### Configure build
```bash
cd mlt
./configure --prefix=<ROOT_DIR>/build --enable-gpl --enable-gpl3 --swig-languages=python
```

### Update bindings file for Python 3

**This is not needed with current MLT repo head anymore.**

Change line in file *\<ROOT_DIR\>/mlt/src/swig/python/build* from:

```bash
export PYTHON_INCLUDE=`python -c "import sys;print(\"{}/include/python{}.{}\".format(sys.prefix,*sys.version_info))"`
```
 to:
 ```bash
export PYTHON_INCLUDE=`python3 -c "import sys;print(\"{}/include/python{}.{}\".format(sys.prefix,*sys.version_info))"`
```

### Build MLT and bindings
 ```bash
make 
make install
```  

### Set up bindings

1. Copy *mlt.py* and *_mlt.so* from  *\<ROOT_DIR\>/mlt/src/swig/python* into  *../flowblade-trunk* where your repository version Flowblade is installed.
1. Create launch script in **\<ROOT_DIR\>** to set up MLT variables correctly on launch.

 ```bash
#!/bin/sh

# Set MLT environment variables to point
# where you have the binaries and libraries
# so MLT finds them runtime.
WORK_DIR=<ROOT_DIR>

INSTALL_DIR=$WORK_DIR/build
export PATH=$WORK_DIR/bin:$PATH

export MLT_REPOSITORY=$INSTALL_DIR/lib/mlt
export MLT_DATA=$INSTALL_DIR/share/mlt
export MLT_PROFILES_PATH=$INSTALL_DIR/share/mlt/profiles
export LD_LIBRARY_PATH=$INSTALL_DIR/lib:$LD_LIBRARY_PATH

# Lauch repository Flowblade
/home/path/to/your/repository/install/flowblade-trunk/flowblade
``` 

Launch Flowblade with the script above.
