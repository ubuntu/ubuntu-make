# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
#
# Authors:
#  Tin Tvrtković
#  Jared Ravetch
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


"""Rust module"""

from contextlib import suppress
from gettext import gettext as _
from glob import glob
import logging
import os
import re
from bs4 import BeautifulSoup
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.network.download_center import DownloadItem, DownloadCenter
from umake.tools import get_current_arch, add_env_to_user, ChecksumType, \
    MainLoop, Checksum
from umake.ui import UI

logger = logging.getLogger(__name__)


class RustCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Rust", description=_("Rust language"),
                         logo_path=None)


class RustLang(umake.frameworks.baseinstaller.BaseInstaller):
    # Button labels on the download page.
    arch_trans = {
        "amd64": "64-bit",
        "i386": "32-bit"
    }

    def __init__(self, category):
        super().__init__(name="Rust Lang",
                         description=_("The official Rust distribution"),
                         is_category_default=True,
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page="https://www.rust-lang.org/downloads.html",
                         checksum_type=ChecksumType.sha256,
                         dir_to_decompress_in_tarball="rust-*")

    def parse_download_link(self, line, in_download):
        """Parse Rust download link, expect to find a url"""
        url, sha1 = (None, None)
        arch = get_current_arch()
        if "{}-unknown-linux-gnu.tar.gz".format(self.arch_trans[arch]) in line:
            in_download = True
        if in_download:
            p = re.search(r'href="(.*)">', line)
            with suppress(AttributeError):
                url = p.group(1)
            p = re.search(r'<td><tt>(\w+)</tt></td>', line)
            with suppress(AttributeError):
                sha1 = p.group(1)
            if "</tr>" in line:
                in_download = False

        if url is None and sha1 is None:
            return (None, in_download)
        return ((url, sha1), in_download)

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Override this so we can use BS and fetch the checksum separately."""
        logger.debug("Fetched download page, parsing.")

        page = result[self.download_page]

        error_msg = page.error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page_url, error_msg))
            UI.return_main_screen(status_code=1)

        soup = BeautifulSoup(page.buffer, 'html.parser')

        link = (soup.find('div', class_="install")
                .find('td', class_="inst-type", text="Linux (.tar.gz)")
                .parent
                .find(text=self.arch_trans[get_current_arch()])
                .parent
                .parent)

        if link is None:
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)

        download_url = link.attrs['href']
        checksum_url = download_url + '.sha256'
        logger.debug("Found download URL: " + download_url)
        logger.debug("Downloading checksum first, from " + checksum_url)

        def checksum_downloaded(results):
            checksum_result = next(iter(results.values()))  # Just get the first.
            if checksum_result.error:
                logger.error(checksum_result.error)
                UI.return_main_screen(status_code=1)

            checksum = checksum_result.buffer.getvalue().decode('utf-8').split()[0]
            logger.info('Obtained SHA256 checksum: ' + checksum)

            self.download_requests.append(DownloadItem(download_url,
                                                       checksum=Checksum(ChecksumType.sha256, checksum),
                                                       ignore_encoding=True))
            self.start_download_and_install()

        DownloadCenter([DownloadItem(checksum_url)], on_done=checksum_downloaded, download=False)

    def post_install(self):
        """Add rust necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": "{}:{}".format(os.path.join(self.install_path, "rustc", "bin"),
                                                                     os.path.join(self.install_path, "cargo", "bin"))},
                                    "LD_LIBRARY_PATH": {"value": os.path.join(self.install_path, "rustc", "lib")}})

        # adjust for rust 1.5 some symlinks magic to have stdlib craft available
        os.chdir(os.path.join(self.install_path, "rustc", "lib"))
        os.rename("rustlib", "rustlib.init")
        os.symlink(glob(os.path.join('..', '..', 'rust-std-*', 'lib', 'rustlib'))[0], 'rustlib')
        os.symlink(os.path.join('..', 'rustlib.init', 'etc'), os.path.join('rustlib', 'etc'))

        UI.delayed_display(DisplayMessage(_("You need to restart your current shell session for your {} installation "
                                            "to work properly").format(self.name)))
