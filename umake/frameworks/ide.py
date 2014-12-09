# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#  Tin Tvrtković
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


"""Generic IDE module."""

from gettext import gettext as _
import logging
import platform

from os.path import join
import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.tools import create_launcher, get_application_desktop_file, ChecksumType, Checksum
from umake.ui import UI


logger = logging.getLogger(__name__)


class IdeCategory(umake.frameworks.BaseCategory):
    def __init__(self):
        super().__init__(name=_("IDE"), description=_("Generic IDEs"),
                         logo_path=None)


class Eclipse(umake.frameworks.baseinstaller.BaseInstaller):
    """The Eclipse Foundation distribution."""
    DOWNLOAD_URL_PAT = "https://www.eclipse.org/downloads/download.php?" \
                       "file=/technology/epp/downloads/release/luna/R/" \
                       "eclipse-standard-luna-R-linux-gtk{arch}.tar.gz{suf}" \
                       "&r=1"

    def __init__(self, category):
        super().__init__(name=_("Eclipse"),
                         description=_("Pure Eclipse Luna (4.4)"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page=None,
                         dir_to_decompress_in_tarball='eclipse',
                         desktop_filename='eclipse.desktop',
                         packages_requirements=['openjdk-7-jdk'])

    def download_provider_page(self):
        """First, we need to fetch the MD5, then kick off the proceedings.

        This could actually be done in parallel, in a future version.
        """
        logger.debug("Preparing to download MD5.")

        arch = platform.machine()
        if arch == 'i686':
            md5_url = self.DOWNLOAD_URL_PAT.format(arch='', suf='.md5')
        elif arch == 'x86_64':
            md5_url = self.DOWNLOAD_URL_PAT.format(arch='-x86_64', suf='.md5')
        else:
            logger.error("Unsupported architecture: {}".format(arch))
            UI.return_main_screen()

        def done(download_result):
            res = download_result[md5_url]

            if res.error:
                logger.error(res.error)
                UI.return_main_screen()
                return

            # Should be ASCII anyway.
            md5 = res.buffer.getvalue().decode('utf-8').split()[0]
            logger.debug("Downloaded MD5 is {}".format(md5))

            logger.debug("Preparing to download the main archive.")
            if arch == 'i686':
                download_url = self.DOWNLOAD_URL_PAT.format(arch='', suf='')
            elif arch == 'x86_64':
                download_url = self.DOWNLOAD_URL_PAT.format(arch='-x86_64',
                                                            suf='')
            self.download_requests.append(DownloadItem(download_url, Checksum(ChecksumType.md5, md5)))
            self.start_download_and_install()

        DownloadCenter(urls=[DownloadItem(md5_url, None)], on_done=done, download=False)

    def post_install(self):
        """Create the Luna launcher"""
        icon_filename = "icon.xpm"
        icon_path = join(self.install_path, icon_filename)
        exec_path = '"{}" %f'.format(join(self.install_path, "eclipse"))
        comment = _("The Eclipse Luna Integrated Development Environment")
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=_("Eclipse Luna"),
                                                     icon_path=icon_path,
                                                     exec=exec_path,
                                                     comment=comment,
                                                     categories=categories))

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not join(self.install_path, "eclipse"):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True
