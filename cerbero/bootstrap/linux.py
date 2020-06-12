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

from cerbero.bootstrap import BootstrapperBase
from cerbero.bootstrap.bootstrapper import register_bootstrapper
from cerbero.enums import Platform, Architecture, Distro, DistroVersion
from cerbero.errors import ConfigurationError
from cerbero.utils import shell
from cerbero.utils import messages as m

import shlex
import subprocess

class UnixBootstrapper (BootstrapperBase):

    tool = []
    command = []
    yes_arg = []
    checks = []
    packages = []

    def __init__(self, config, offline, assume_yes):
        BootstrapperBase.__init__(self, config, offline)
        self.assume_yes = assume_yes

    def start(self, jobs=0):
        for c in self.checks:
            c()

        if self.config.distro_packages_install:
            extra_packages = self.config.extra_bootstrap_packages.get(
                self.config.platform, None)
            if extra_packages:
                self.packages += extra_packages.get(self.config.distro, [])
                self.packages += extra_packages.get(self.config.distro_version, [])
            tool = self.tool
            if self.assume_yes:
                tool += self.yes_arg;
            tool += self.command;
            cmd = tool + self.packages
            m.message("Running command '%s'" % ' '.join(cmd))
            shell.new_call(cmd)


class DebianBootstrapper (UnixBootstrapper):

    tool = ['sudo', 'apt-get']
    command = ['install']
    yes_arg = ['-y']
    packages = ['autotools-dev', 'automake', 'autoconf', 'libtool', 'g++',
                'autopoint', 'make', 'cmake', 'bison', 'flex', 'nasm',
                'pkg-config', 'gtk-doc-tools', 'libxv-dev',
                'libx11-dev', 'libx11-xcb-dev',
                'libpulse-dev', 'python3-dev', 'texinfo', 'gettext',
                'build-essential', 'pkg-config', 'doxygen', 'curl',
                'libxext-dev', 'libxi-dev', 'x11proto-record-dev',
                'libxrender-dev', 'libgl1-mesa-dev', 'libxfixes-dev',
                'libxdamage-dev', 'libxcomposite-dev', 'libasound2-dev',
                'libxml-simple-perl', 'dpkg-dev', 'debhelper',
                'build-essential', 'devscripts', 'fakeroot', 'transfig',
                'gperf', 'libdbus-glib-1-dev', 'wget', 'glib-networking',
                'libxtst-dev', 'libxrandr-dev', 'libglu1-mesa-dev',
                'libegl1-mesa-dev', 'git', 'subversion', 'xutils-dev',
                'intltool', 'ccache', 'python3-setuptools', 'libssl-dev']

    def __init__(self, config, offline, assume_yes):
        UnixBootstrapper.__init__(self, config, offline, assume_yes)
        if self.config.target_platform == Platform.WINDOWS:
            if self.config.arch == Architecture.X86_64:
                self.packages.append('libc6:i386')
                self.checks.append(self.create_debian_arch_check('i386'))
        if self.config.target_platform == Platform.LINUX:
            self.packages.append('chrpath')
            self.packages.append('libfuse-dev')
        if self.config.distro_version == DistroVersion.DEBIAN_SQUEEZE:
            self.packages.remove('glib-networking')

    def create_debian_arch_check(self, arch):
        def check_arch():
            native_arch = shell.check_output(['dpkg', '--print-architecture'])
            if native_arch == arch:
                return
            foreign_archs = shell.check_output(['dpkg', '--print-foreign-architectures'])
            if arch in foreign_archs.split():
                return
            raise ConfigurationError(('Architecture %s is missing from your setup. ' + \
                                      'You can add it with: "dpkg --add-architecture %s",' + \
                                      ' then run "apt-get update."') \
                                      % (arch, arch))

        return check_arch

class RedHatBootstrapper (UnixBootstrapper):

    tool = ['dnf']
    command = ['install']
    yes_arg = ['-y']
    packages = ['gcc', 'gcc-c++', 'automake', 'autoconf', 'libtool',
                'gettext-devel', 'make', 'cmake', 'bison', 'flex', 'nasm',
                'pkgconfig', 'gtk-doc', 'curl', 'doxygen', 'texinfo',
                'texinfo-tex', 'texlive-dvips', 'docbook-style-xsl',
                'transfig', 'intltool', 'rpm-build', 'redhat-rpm-config',
                'python3-devel', 'libXrender-devel', 'pulseaudio-libs-devel',
                'libXv-devel', 'mesa-libGL-devel', 'libXcomposite-devel',
                'alsa-lib-devel', 'perl-ExtUtils-MakeMaker', 'libXi-devel',
                'perl-XML-Simple', 'gperf', 'gdk-pixbuf2-devel', 'wget',
                'docbook-utils-pdf', 'glib-networking', 'help2man',
                'dbus-devel', 'glib2-devel', 'libXrandr-devel',
                'libXtst-devel', 'git', 'subversion', 'xorg-x11-util-macros',
                'mesa-libEGL-devel', 'ccache', 'openssl-devel']

    def __init__(self, config, offline, assume_yes):
        UnixBootstrapper.__init__(self, config, offline, assume_yes)

        if self.config.distro_version < DistroVersion.FEDORA_23:
            self.tool = ['yum']
        elif self.config.distro_version in [DistroVersion.REDHAT_6, DistroVersion.REDHAT_7]:
            self.tool = ['yum']
        elif self.config.distro_version == DistroVersion.REDHAT_8:
            self.tool = ['yum', '--enablerepo=PowerTools']
            # See https://bugzilla.redhat.com/show_bug.cgi?id=1757002
            self.packages.remove('docbook-utils-pdf')

        if self.config.target_platform == Platform.WINDOWS:
            if self.config.arch == Architecture.X86_64:
                self.packages.append('glibc.i686')
            if self.config.distro_version in [DistroVersion.FEDORA_24, DistroVersion.FEDORA_25]:
                self.packages.append('libncurses-compat-libs.i686')
        if self.config.target_platform == Platform.LINUX:
            self.packages.append('chrpath')
            self.packages.append('fuse-devel')
        # Use sudo to gain root access on everything except RHEL
        if self.config.distro_version == DistroVersion.REDHAT_6:
            self.tool = ['su', '-c', shlex.join(self.tool)]
        else:
            self.tool = ['sudo'] + self.tool

class OpenSuseBootstrapper (UnixBootstrapper):

    tool = ['sudo', 'zypper']
    command = ['install']
    yes_arg = ['-y']
    packages = ['gcc', 'automake', 'autoconf', 'gcc-c++', 'libtool',
            'gettext-tools', 'make', 'cmake', 'bison', 'flex', 'nasm',
            'gtk-doc', 'curl', 'doxygen', 'texinfo',
            'texlive', 'docbook-xsl-stylesheets',
            'transfig', 'intltool', 'patterns-openSUSE-devel_rpm_build',
            'python3-devel', 'xorg-x11-libXrender-devel', 'libpulse-devel',
            'xorg-x11-libXv-devel', 'Mesa-libGL-devel', 'libXcomposite-devel',
            'libX11-devel', 'alsa-devel', 'libXi-devel', 'Mesa-devel',
            'Mesa-libGLESv3-devel',
            'perl-XML-Simple', 'gperf', 'gdk-pixbuf-devel', 'wget',
            'docbook-utils', 'glib-networking', 'git', 'subversion', 'ccache',
            'openssl-devel']

class ArchBootstrapper (UnixBootstrapper):

    tool = ['sudo', 'pacman']
    command = ['-S', '--needed']
    yes_arg = ['--noconfirm']
    packages = ['intltool', 'cmake', 'doxygen', 'gtk-doc',
            'libtool', 'bison', 'flex', 'automake', 'autoconf', 'make',
            'curl', 'gettext', 'alsa-lib', 'nasm', 'gperf',
            'docbook-xsl', 'transfig', 'libxrender',
            'libxv', 'mesa', 'python3', 'wget', 'glib-networking', 'git',
            'subversion', 'xorg-util-macros', 'ccache', 'openssl']

    def __init__(self, config, offline, assume_yes):
        UnixBootstrapper.__init__(self, config, offline, assume_yes)

        has_multilib = True
        try:
          shell.check_output (["pacman", "-Sp", "gcc-multilib"])
        except CommandError:
          has_multilib = False

        if self.config.arch == Architecture.X86_64 and has_multilib:
            self.packages.append('gcc-multilib')
        else:
            self.packages.append('gcc')

class GentooBootstrapper (UnixBootstrapper):

    tool = ['sudo', 'emerge']
    command = ['-u']
    yes_arg = [] # Does not seem interactive
    packages = ['dev-util/intltool', 'sys-fs/fuse', 'dev-util/cmake',
            'app-doc/doxygen', 'dev-util/gtk-doc', 'sys-devel/libtool',
            'sys-devel/bison', 'sys-devel/flex', 'sys-devel/automake',
            'sys-devel/autoconf', 'sys-devel/make', 'net-misc/curl',
            'sys-devel/gettext', 'media-libs/alsa-lib', 'media-sound/pulseaudio',
            'dev-lang/nasm', 'dev-util/gperf', 'app-text/docbook-xsl-stylesheets',
            'media-gfx/transfig', 'x11-libs/libXrender', 'x11-libs/libXv',
            'media-libs/mesa', 'net-misc/wget', 'net-libs/glib-networking',
            'dev-libs/openssl']

class NoneBootstrapper (BootstrapperBase):

    def start(self):
        pass


def register_all():
    register_bootstrapper(Distro.DEBIAN, DebianBootstrapper)
    register_bootstrapper(Distro.REDHAT, RedHatBootstrapper)
    register_bootstrapper(Distro.SUSE, OpenSuseBootstrapper)
    register_bootstrapper(Distro.ARCH, ArchBootstrapper, DistroVersion.ARCH_ROLLING)
    register_bootstrapper(Distro.GENTOO, GentooBootstrapper, DistroVersion.GENTOO_VERSION)
    register_bootstrapper(Distro.NONE, NoneBootstrapper)
