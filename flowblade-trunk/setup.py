#!/usr/bin/env python

import glob, os 
from distutils.core import setup

# FLOWBLADE distutils setup.py script.
# Running this by itself WILL NOT create a succesful installation.

install_data = [('share/applications', ['installdata/flowblade.desktop']),
                ('share/pixmaps', ['installdata/flowblade.png']),
                ('share/mime/packages',['installdata/flowblade.xml']),
                ('lib/mime/packages',['installdata/flowblade']),
                ('share/man/man1',['installdata/flowblade.1'])]

flowblade_package_data = ['res/filters/*.xml','res/filters/wipes/*','res/img/*',
                          'res/profiles/*','res/render/renderencoding.xml',
                          'res/help/*','locale/Flowblade/*']

locale_files = []
for filepath in glob.glob("Flowblade/locale/*/LC_MESSAGES/*"):
	filepath = filepath.replace('Flowblade/', '')
	locale_files.append(filepath)
	
setup(  name='flowblade',
        version='0.6.0',
        author='Janne Liljeblad',
        author_email='janne.liljeblad at gmail dot com',
        description='Non-linear video editor',
        url='http://code.google.flowblade.com',
        license='GNU GPL3',
        scripts=['flowblade'],
        packages=['Flowblade'],
        package_data={'Flowblade':flowblade_package_data + locale_files},
        data_files=install_data)
