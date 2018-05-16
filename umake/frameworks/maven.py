# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#  Igor Vuk
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


"""Maven module"""

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import re
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.tools import add_env_to_user, MainLoop, ChecksumType, Checksum
from umake.ui import UI

logger = logging.getLogger(__name__)


class MavenCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Maven", description=_("Java software project management and comprehension tool"),
                         logo_path=None)


class MavenLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Maven Lang", description=_("Java software project management and comprehension tool"),
                         is_category_default=True,
                         packages_requirements=["openjdk-7-jdk | openjdk-8-jdk"],
                         checksum_type=ChecksumType.sha1,
                         match_last_link=True,
                         download_page="https://www.apache.org/dist/maven/maven-3",
                         dir_to_decompress_in_tarball="apache-maven-*",
                         required_files_path=[os.path.join("bin", "mvn")],
                         **kwargs)
        self.checksum_url = None

    def parse_download_link(self, line, in_download):
        """Parse Maven download link, expect to find a url"""
        url_found = False
        if 'alt="[DIR]"> <a href="' in line:
            in_download = True
        if in_download:
            p = re.search(r'href="(.*)"', line)
            with suppress(AttributeError):
                url_found = True
                version_url = p.group(1)
                self.checksum_url = os.path.join(self.download_page, os.path.normpath(version_url),
                                                 'binaries',
                                                 'apache-maven-{}-bin.tar.gz.sha1'.format(version_url.strip('/')))
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
            (_url_found, in_download) = self.parse_download_link(line_content, in_download)
            if not url_found:
                url_found = _url_found

        if not url_found:
            logger.error("Download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

        DownloadCenter(urls=[DownloadItem(self.checksum_url, None)],
                       on_done=self.get_sha_and_start_download, download=False)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.checksum_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        # you get and store self.download_url
        url = re.sub('.sha1', '', self.checksum_url)
        if url is None:
            logger.error("Download page changed its syntax or is not parsable (missing url)")
            UI.return_main_screen(status_code=1)
        if checksum is None:
            logger.error("Download page changed its syntax or is not parsable (missing checksum)")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download link for {}, checksum: {}".format(url, checksum))
        self.download_requests.append(DownloadItem(url, Checksum(self.checksum_type, checksum)))
        self.start_download_and_install()

    def post_install(self):
        """Add the necessary Maven environment variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
