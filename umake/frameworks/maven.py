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
from umake.tools import add_env_to_user, MainLoop, ChecksumType
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
                         packages_requirements=["openjdk-7-jdk | openjdk-8-jdk | openjdk-11-jdk"],
                         checksum_type=ChecksumType.sha512,
                         match_last_link=True,
                         download_page="https://maven.apache.org/download.cgi",
                         dir_to_decompress_in_tarball="apache-maven-*",
                         required_files_path=[os.path.join("bin", "mvn")],
                         **kwargs)
        self.url = None
        self.new_download_url = None

    def parse_download_link(self, line, in_download):
        """Parse Maven download link, expect to find a url"""
        if '<td><a href="' in line:
            p = re.search(r'href="(.*-bin.tar.gz)"', line)
            with suppress(AttributeError):
                self.url = p.group(1)
                in_download = True
        if in_download and '<td><a class="externalLink"' in line:
            print(line)
            p = re.search(r'href="(.*.sha512)"', line)
            with suppress(AttributeError):
                self.new_download_url = p.group(1)
        return (None, in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        logger.debug("Found download link for {}, checksum: {}".format(self.url, checksum))
        self.check_data_and_start_download(self.url, checksum)

    def post_install(self):
        """Add the necessary Maven environment variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
