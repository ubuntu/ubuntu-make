# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
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


"""Swift module"""

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import re
import gnupg

import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import get_current_arch, add_env_to_user, ChecksumType, MainLoop, get_current_ubuntu_version
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.ui import UI

logger = logging.getLogger(__name__)


class SwiftCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Swift", description=_("Swift language"),
                         logo_path=None)


class SwiftLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Swift Lang", description=_("Swift compiler (default)"), is_category_default=True,
                         packages_requirements=["clang"],
                         category=category, only_on_archs=['amd64'],
                         download_page="https://swift.org/download/",
                         dir_to_decompress_in_tarball="swift*",
                         required_files_path=[os.path.join("usr", "bin", "swift")])
        self.release = get_current_ubuntu_version()

    def parse_download_link(self, line, in_download):
        """Parse Swift download link, expect to find a .sig file"""
        url_found = False
        if self.release in line and '.tar.gz.sig' in line:
            in_download = True
        else:
            in_download = False
        if in_download:
            p = re.search(r'href="(.*)" title="PGP Signature"', line)
            with suppress(AttributeError):
                self.sig_url = "https://swift.org" + p.group(1)
                logger.debug(self.sig_url)
                url_found = True
                DownloadCenter(urls=[DownloadItem(self.sig_url, None)],
                               on_done=self.check_gpg_and_start_download, download=False)
        return (url_found, in_download)

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Download files to download + license and check it"""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        in_download = False
        url_found = False
        for line in result[self.download_page].buffer:
            line_content = line.decode()
            if not url_found:
                (_url_found, in_download) = self.parse_download_link(line_content, in_download)
            if not url_found:
                url_found = _url_found

        if not url_found:
            logger.error("Download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

    @MainLoop.in_mainloop_thread
    def check_gpg_and_start_download(self, download_result):
        res = download_result[self.sig_url]
        sig = res.buffer.getvalue().decode('utf-8').split()[0]
        verify = gnupg.GPG().verify(sig)
        if verify is False:
            logger.error("Signature not valid")
            UI.return_main_screen(status_code=1)
        # you get and store self.download_url
        url = re.sub('.sig', '', self.sig_url)
        if url is None:
            logger.error("Download page changed its syntax or is not parsable (missing url)")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download link for {}".format(url))
        self.download_requests.append(DownloadItem(url, None))
        self.start_download_and_install()

    def post_install(self):
        """Add swift necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "usr/bin")}})
        UI.delayed_display(DisplayMessage(_("You need to restart your current shell session for your {} installation "
                                            "to work properly").format(self.name)))
