#!/usr/bin/env python
# -*- coding: future_fstrings -*-
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, tools
from conans.errors import ConanException
from conans.model.version import Version


class QtConan(ConanFile):
    """
    Qt interface package to use a system installed Qt.
    """

    name        = 'qt'
    version     = '5.9.6'
    description = 'Use pre-installed Qt'
    url         = 'https://github.com/kheaactua/conan-qt-simple'
    license     = 'MIT'
    options = {
        'qt_path':  'ANY', # e.g. /opt/Qt5.3.2/5.3/gcc_64
    }
    default_options = (
        'qt_path=None',
    )
    requires = (
        'helpers/[>=0.3]@ntc/stable',
    )

    settings    = {
        'os':       ['Linux', 'Windows'],
        'arch':     ['x86_64'],
        'compiler': None
    }

    def source(self):
        pass

    def package_info(self):
        # Attempt to find Qt

        qt_path = None
        if self.options.qt_path and len(str(self.options.qt_path)) and os.path.exists(str(self.options.qt_path)):
            # Good
            qt_path = str(self.options.qt_path)
        else:
            # Attempt to guess
            (major, minor, _) = str(self.version).split('.')
            if tools.os_info.is_linux:
                guesses = [
                    f'/opt/Qt{self.version}/{major}.{minor}/gcc_64',
                    f'/opt/Qt{self.version}/{self.version}/gcc_64',
                    f'%s/Qt{self.version}/{major}.{minor}/gcc_64'%os.environ.get('HOME', '/opt'),
                ]
            else:
                if 'Visual Studio' == self.settings.compiler:
                    v = Version(str(self.settings.compiler.version))
                    if v == '12':
                        year = '2013'
                    elif v == '14':
                        year = '2015'
                    elif v == '15':
                        year = '2017'
                    else:
                        raise ConanException('Cannot auto-detect Qt path, not enough compiler information')

                guesses = [
                    os.path.join(r'C:\\', 'Qt', f'Qt{self.version}', str(self.version), f'msvc{year}_64'),
                ]

            for g in guesses:
                if os.path.exists(g):
                    qt_path = g
                    break

            if qt_path is None:
                raise ConanException('Cannot auto-detect Qt path.  Guesses:\n - %s\nPlease specify the directory with the qt_path option'%'\n - '.join(guesses))

        self.output.info(f'Found Qt at {qt_path}')

        self.cpp_info.libdirs     = [os.path.join(qt_path, 'lib')]
        self.cpp_info.libs        = tools.collect_libs(self)

        self.cpp_info.bindirs     = [os.path.join(qt_path, 'bin')]
        self.cpp_info.includedirs = [os.path.join(qt_path, 'include')]

        self.cpp_info.resdirs     = [os.path.join(qt_path, 'lib', 'cmake')]

        # Put qmake and DLLs in the path
        if tools.os_info.is_windows:
            self.env_info.path.extend(self.cpp_info.bindirs)

        # Make it easier for CMake to find Qt
        self.env_info.CMAKE_PREFIX_PATH.append(self.cpp_info.resdirs[0])

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
