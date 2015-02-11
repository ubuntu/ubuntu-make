# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
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


"""Web module"""

from gettext import gettext as _
import logging
import os
import platform
import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadItem
from umake.tools import create_launcher, get_application_desktop_file, Checksum

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class WebCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Web", description=_("Web Developer Environment"), logo_path=None)


class FirefoxDev(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Firefox Dev", description=_("Firefox Developer Edition"), is_category_default=False,
                         category=category, only_on_archs=_supported_archs, expect_license=False,
                         download_page=None,
                         dir_to_decompress_in_tarball="firefox",
                         desktop_filename="firefox-developer.desktop")

    def download_provider_page(self):
        """Skip download provider page and directly use the download links"""

        arch = platform.machine()
        tag_machine = ''
        if arch == 'x86_64':
            tag_machine = '64'
        self.download_requests.append(DownloadItem(
            "https://download.mozilla.org/?product=firefox-aurora-latest&os=linux{}".format(tag_machine),
            Checksum(None, None)))
        self.start_download_and_install()

    def post_install(self):
        """Create the Firefox Developer launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Firefox Developer Edition"),
                        icon_path=os.path.join(self.install_path, "browser", "icons", "mozicon128.png"),
                        exec=os.path.join(self.install_path, "firefox"),
                        comment=_("Firefox Aurora with Developer tools"),
                        categories="Development;IDE;"))

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not os.path.isfile(os.path.join(self.install_path, "firefox")):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True
