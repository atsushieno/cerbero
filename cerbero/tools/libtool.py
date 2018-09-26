#!/usr/bin/env python3
# cerbero - a multi-platform build system for Open Source software
# Copyright (C) 2012 Andoni Morales Alastruey <ylatuya@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
from cerbero.config import Platform
from cerbero.errors import FatalError

def get_libtool_versions(version, soversion=0):
    parts = version.split('.')
    if not parts or len(parts) > 3:
        raise FatalError('Version must contain three or fewer parts: {!r}'
                         ''.format(version))
    try:
        major = int(parts[0])
        minor = 0
        micro = 0
        if len(parts) > 1:
            minor = int(parts[1])
            if len(parts) > 2:
                micro = int(parts[2])
    except ValueError:
        raise FatalError('Invalid version: {!r}'.format(version))
    interface_age = 0
    if (minor % 2) == 0:
        interface_age = micro
    binary_age = (100 * minor) + micro
    return (soversion, binary_age - interface_age, interface_age)

class LibtoolLibrary(object):
    '''
    Helper class to create libtool libraries files (.la)
    '''

    LIBTOOL_TPL = '''\
# %(libname)s - a libtool library file
# Generated by libtool (GNU libtool) 2.4.2 Debian-2.4.2-1ubuntu1
#
# Please DO NOT delete this file!
# It is necessary for linking the library.

# The name that we can dlopen(3).
dlname='%(dlname)s'

# Names of this library.
library_names='%(library_names)s'

# The name of the static archive.
old_library='%(old_library)s'

# Linker flags that can not go in dependency_libs.
inherited_linker_flags=''

# Libraries that this one depends upon.
dependency_libs='%(dependency_libs)s'

# Names of additional weak libraries provided by this library
weak_library_names=''

# Version information for libglib-2.0.
current=%(current)s
age=%(age)s
revision=%(revision)s

# Is this an already installed library?
installed=yes

# Should we warn about portability when linking against -modules?
shouldnotlink=no

# Files to dlopen/dlpreopen
dlopen=''
dlpreopen=''

# Directory that this library needs to be installed in:
libdir='%(libdir)s'
'''

    def __init__(self, libname, major, minor, micro, libdir, platform,
            deps=None, static_only=False):
        self.libtool_vars = {
            'libname': '',
            'dlname': '',
            'library_names': '',
            'old_library': '',
            'dependency_libs': '',
            'current': '',
            'age': '',
            'revision': '',
            'libdir': ''}

        if platform == Platform.WINDOWS:
            shared_ext = 'dll.a'
        elif platform in [Platform.DARWIN, Platform.IOS]:
            shared_ext = 'dylib'
        else:
            shared_ext = 'so'

        if not libname.startswith('lib'):
            libname = 'lib%s' % libname
        if deps is None:
            deps = ''
        self.libname = libname
        self.libdir = libdir
        self.laname = '%s.la' % libname
        dlname_base = '%s.%s' % (libname, shared_ext)
        dlname = dlname_base
        dlname_all = dlname_base
        major_str = ''
        minor_str = ''
        micro_str = ''

        if major is not None:
            dlname = '%s.%s' % (dlname_base, major)
            major_str = major
            if minor is not None:
                dlname_all = '%s.%s' % (dlname, minor)
                minor_str = minor
                if micro is not None:
                    dlname_all = '%s.%s' % (dlname_all, micro)
                    micro_str = micro
        old_library = '%s.a' % libname
        self.change_value('libname', self.laname)
        if not static_only:
            self.change_value('dlname', dlname)
            self.change_value('library_names', '%s %s %s' % (dlname_all, dlname,
                dlname_base))
        self.change_value('old_library', old_library)
        self.change_value('current', minor_str)
        self.change_value('age', minor_str)
        self.change_value('revision', micro_str)
        self.change_value('libdir', libdir)
        self.change_value('dependency_libs', self._parse_deps(deps))

    def save(self):
        path = os.path.join(self.libdir, self.laname)
        with open(path, 'w') as f:
            f.write(self.LIBTOOL_TPL % self.libtool_vars)

    def change_value(self, key, val):
        self.libtool_vars[key] = val

    def _parse_deps(self, deps):
        deps_str = ''
        libtool_deps = [x for x in deps if not x.startswith('-l')]
        lib_deps = [x for x in deps if x.startswith('-l')]
        for d in libtool_deps:
            if not d.startswith('lib'):
                d = 'lib' + d
            deps_str += ' %s/%s.la ' % (self.libdir, d)
        deps_str += ' '.join(lib_deps)
        return deps_str
