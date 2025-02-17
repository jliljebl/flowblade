#!/usr/bin/python3
"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

import glob, os
from setuptools import setup
    
# FLOWBLADE distutils setup.py script.

install_data = [('share/applications', ['installdata/io.github.jliljebl.Flowblade.desktop']),
                ('share/metainfo', ['installdata/io.github.jliljebl.Flowblade.appdata.xml']),
                ('share/icons/hicolor/128x128/apps', ['installdata/io.github.jliljebl.Flowblade.png']),
                ('share/mime/packages',['installdata/io.github.jliljebl.Flowblade.xml']),
                ('lib/mime/packages',['installdata/flowblade']),
                ('share/man/man1',['installdata/flowblade.1'])]

flowblade_package_data = ['res/filters/*.xml','res/filters/wipes/*','res/img/*',
                          'res/profiles/*','res/render/renderencoding.xml',
                          'res/patternproducer/*','res/help/*','res/help/*/*','locale/Flowblade/*',
                          'res/proxyprofiles/*','res/darktheme/*','launch/*','res/gmic/*',
                          'res/shortcuts/*','res/css/*','res/css/assets/*','res/css/sass/*',
                          'res/css2/*','res/css2/assets/*','res/css2/sass/*',
                          'res/css3/*','res/css3/assets/*','res/css3/sass/*',
                          'res/mediaplugins/*', 'res/mediaplugins/animations_1/*',
                          'res/mediaplugins/animations_2/*', 'res/mediaplugins/text_1/*',
                          'res/mediaplugins/text_2/*', 'res/mediaplugins/transitions_1/*',
                          'res/mediaplugins/transitions_2/*','res/gpu-test/*','res/scripttool/*',
                          'res/usbhid/*', 'res/mediaplugins/text_3/*']

locale_files = []
for filepath in glob.glob("Flowblade/locale/*/LC_MESSAGES/*"):
    filepath = filepath.replace('Flowblade/', '')
    locale_files.append(filepath)

setup(  name='flowblade',
        version='2.18.1',
        author='Janne Liljeblad',
        author_email='janne.liljeblad at gmail dot com',
        description='Non-linear video editor',
        url='https://github.com/jliljebl/flowblade',
        license='GNU GPL3',
        scripts=['flowblade'],
        packages=['Flowblade','Flowblade/tools','Flowblade/vieweditor'],
        package_data={'Flowblade':flowblade_package_data + locale_files},
        data_files=install_data)

