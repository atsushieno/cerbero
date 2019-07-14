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
import shutil

from cerbero.bootstrap import BootstrapperBase
from cerbero.bootstrap.bootstrapper import register_bootstrapper
from cerbero.config import Distro, FatalError
from cerbero.utils import _, shell

NDK_VERSION = 'r20'
NDK_BASE_URL = 'https://dl.google.com/android/repository/android-ndk-%s-%s-%s.zip'
NDK_CHECKSUMS = {
    'android-ndk-r20-linux-x86_64.zip': '57435158f109162f41f2f43d5563d2164e4d5d0364783a9a6fab3ef12cb06ce0',
    'android-ndk-r20-darwin-x86_64.zip': '2ec06c4576c6ad50a727f0a5fbd0f67563aa6e8b348cff904b029622a470f2f1',
    'android-ndk-r20-windows-x86_64.zip': '315cdfdb971ee85a71e267da2cc7d6667ec722c3649aedc45cd42a97b2e8b056',
    'android-ndk-r20-windows-x86.zip': '7541bacd22f5757b9947314ee71111e18fc7db852ac67b23b7dbace229b941cf',
}

class AndroidBootstrapper (BootstrapperBase):

    def __init__(self, config, offline, assume_yes):
        super().__init__(config, offline)
        self.prefix = self.config.toolchain_prefix
        url = NDK_BASE_URL % (NDK_VERSION, self.config.platform, self.config.arch)
        self.fetch_urls.append((url, NDK_CHECKSUMS[os.path.basename(url)]))
        self.extract_steps.append((url, True, self.prefix))

    def start(self):
        if not os.path.exists(self.prefix):
            os.makedirs(self.prefix)
        ndkdir = os.path.join(self.prefix, 'android-ndk-' + NDK_VERSION)
        if not os.path.isdir(ndkdir):
            return
        # Android NDK extracts to android-ndk-$NDK_VERSION, so move its
        # contents to self.prefix
        for d in os.listdir(ndkdir):
            dest = os.path.join(self.prefix, d)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.move(os.path.join(ndkdir, d), self.prefix)
        os.rmdir(ndkdir)


def register_all():
    register_bootstrapper(Distro.ANDROID, AndroidBootstrapper)
