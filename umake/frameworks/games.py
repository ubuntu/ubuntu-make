# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Canonical
#
# Authors:
#  Didier Roche
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA


"""Game IDEs module"""

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import re
import umake.frameworks.baseinstaller
from umake.tools import create_launcher, get_application_desktop_file, get_current_arch

logger = logging.getLogger(__name__)


class GamesCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Games", description=_("Games Development Environment"), logo_path=None)


class Stencyl(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Stencyl", description=_("Stencyl game developer IDE"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page="http://www.stencyl.com/download/",
                         desktop_filename="stencyl.desktop",
                         packages_requirements=["libxtst6:i386", "libxext6:i386", "libxi6:i386", "libncurses5:i386",
                                                "libxt6:i386", "libxpm4:i386", "libxmu6:i386", "libxp6:i386",
                                                "libgtk2.0-0:i386", "libatk1.0-0:i386", "libc6:i386", "libcairo2:i386",
                                                "libexpat1:i386", "libfontconfig1:i386", "libfreetype6:i386",
                                                "libglib2.0-0:i386", "libice6:i386", "libpango1.0-0:i386",
                                                "libpng12-0:i386", "libsm6:i386", "libxau6:i386", "libxcursor1:i386",
                                                "libxdmcp6:i386", "libxfixes3:i386", "libx11-6:i386",
                                                "libxinerama1:i386", "libxrandr2:i386", "libxrender1:i386",
                                                "zlib1g:i386", "libnss3-1d:i386", "libnspr4-0d:i386", "libcurl3:i386",
                                                "libasound2:i386"])

    def parse_download_link(self, line, in_download):
        """Parse Stencyl download links"""
        url, md5sum = (None, None)
        if ">Linux <" in line:
            in_download = True
        if in_download:
            regexp = r'href="(.*)"><.*64-'
            if get_current_arch() == "i386":
                regexp = r'href="(.*)"><.*32-'
            p = re.search(regexp, line)
            with suppress(AttributeError):
                url = p.group(1)
            if '<div class="spacer"><br/><br/>' in line:
                in_download = False

        if url is None:
            return (None, in_download)
        return ((url, None), in_download)

    def post_install(self):
        """Create the Stencyl launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Stencyl"),
                        icon_path=os.path.join(self.install_path, "data", "other", "icon-30x30.png"),
                        exec='"{}" %f'.format(os.path.join(self.install_path, "Stencyl")),
                        comment=_("Stencyl Game developer environment"),
                        categories="Development;IDE;",
                        extra="Path={}\nStartupWMClass=stencyl-sw-Launcher".format(self.install_path)))

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not os.path.isfile(os.path.join(self.install_path, "Stencyl")):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True
