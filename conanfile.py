#!/usr/bin/env python
# -*- coding: future_fstrings -*-
# -*- coding: utf-8 -*-

import os, shutil, glob
from conans import ConanFile, tools
from conans.tools import cpu_count, os_info, SystemPackageTool
from conans.errors import ConanException
from conans.model.version import Version


class QtConan(ConanFile):
    """
    Qt interface package to use a system installed Qt.
    """

    name        = 'qt'
    version     = '5.9.6'
    description = 'Use pre-installed Qt'
    license     = 'MIT'
    options = {
        'qt_path':  'ANY', # e.g. /opt/Qt5.3.2/5.3/gcc_64
    }
    default_options = (
        'qt_path=None',
    )
    requires = (
        'helpers/0.3@ntc/stable',
    )

    settings    = {
        'os':   ['Linux', 'Windows'],
        'arch': ['x86_64'],
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
            (major, minor, patch) = str(self.version).split('.')
            if tools.os_info.is_linux:
                guesses = [
                    f'/opt/Qt{self.version}/{major}.{minor}/gcc_64',
                    f'/opt/Qt{self.version}/{self.version}/gcc_64',
                ]
            else:
                if 'Visual Studio' == self.compiler:
                    v = Version(str(self.compiler.version))
                    if v == '12':
                        year = '2012'
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
                raise ConanException('Cannot auto-detect Qt path')

        self.output.info(f'Found Qt at {qt_path}')

        self.cpp_info.libdirs     = [os.path.join(qt_path, 'lib')]
        self.cpp_info.libs        = tools.collect_libs(self, folder=self.cpp_info.libdirs[0])

        self.cpp_info.bindirs     = [os.path.join(qt_path, 'bin')]
        self.cpp_info.includedirs = [os.path.join(qt_path, 'include')]

        self.cpp_info.resdirs      = [os.path.join(qt_path, 'lib', 'cmake')]

        # Put qmake and DLLs in the path
        if self.settings.os == "Windows":
            self.env_info.path.extend(self.cpp_info.bindirs)

        # Make it easier for CMake to find Qt
        self.env_info.CMAKE_PREFIX_PATH.append(self.cpp_info.resdirs[0])

        if 'Linux' == self.settings.os:

            # Attempt to fix the uic LD_LIBRARY_PATH issues that I can't seem
            # to address through CMake
            self.env_info.LD_LIBRARY_PATH.append(self.cpp_info.libdirs[0])

            # Qt appears to hard code the font path which leads to run time
            # errors
            self.env_info.QT_QPA_FONTDIR = os.path.join(self.cpp_info.libdirs[0], 'fonts')

            # Populate the pkg-config environment variables.  This is Linux
            # only because on Windows there's a different system (.prl files..
            # *shrugs*)
            with tools.pythonpath(self):
                from platform_helpers import adjustPath, appendPkgConfigPath

                pkg_config_path = os.path.join(self.package_folder, 'lib', 'pkgconfig')
                appendPkgConfigPath(adjustPath(pkg_config_path), self.env_info)

                pc_files = glob.glob(adjustPath(os.path.join(pkg_config_path, '*.pc')))
                for f in pc_files:
                    p_name = re.sub(r'\.pc$', '', os.path.basename(f))
                    p_name = re.sub(r'\W', '_', p_name.upper())
                    setattr(self.env_info, f'PKG_CONFIG_{p_name}_PREFIX', adjustPath(self.package_folder))

                appendPkgConfigPath(adjustPath(pkg_config_path), self.env_info)

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
