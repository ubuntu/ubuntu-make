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


"""Nodejs module"""

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import re
import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.interactions import DisplayMessage
from umake.tools import get_current_arch, add_env_to_user, ChecksumType
from umake.ui import UI

logger = logging.getLogger(__name__)


class NodejsCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Nodejs", description=_("Nodejs stable"),
                         logo_path=None)


class NodejsLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Nodejs Lang", description=_("Nodejs stable"), is_category_default=True,
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://nodejs.org/en/download/current",
                         checksum_type=ChecksumType.sha256,
                         dir_to_decompress_in_tarball="node*",
                         required_files_path=[os.path.join("bin", "node")],
                         **kwargs)
    arch_trans = {
        "amd64": "x64",
        "i386": "x86"
    }

    def download_provider_page(self):
        logger.debug("Download application provider page")
        DownloadCenter([DownloadItem(self.download_page)], self.parse_shasum_page, download=False)

    def parse_shasum_page(self, result):
        """Parse the download page and get the SHASUMS256.txt page"""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        for line in result[self.download_page].buffer:
            line_content = line.decode()
            with suppress(AttributeError):
                shasum_url = re.search(r'a href="(.*SHASUMS\d\d\d\.txt\.asc)"', line_content).group(1)

        if not result:
            logger.error("Download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

        self.download_page = shasum_url
        DownloadCenter([DownloadItem(self.download_page)], self.get_metadata_and_check_license, download=False)

    def parse_download_link(self, line, in_download):
        """Parse Nodejs download link, expect to find a sha1 and a url"""
        url, shasum = (None, None)
        arch = get_current_arch()
        if "linux-{}.tar.xz".format(self.arch_trans[arch]) in line:
            in_download = True
        if in_download:
            url = self.download_page.strip("SHASUMS256.txt.asc") + line.split()[1].rstrip()
            shasum = line.split()[0]

        if url is None and shasum is None:
            return (None, in_download)
        return ((url, shasum), in_download)

    def prefix_set(self):
        with suppress(IOError):
            with open(os.path.join(os.environ['HOME'], '.npmrc'), 'r') as file:
                for line in file.readlines():
                    if line.startswith("prefix ="):
                        return True
        return False

    def post_install(self):
        """Add nodejs necessary env variables and move module folder"""
        if not self.prefix_set():
            with open(os.path.join(os.environ['HOME'], '.npmrc'), 'a+') as file:
                file.write("prefix = ${HOME}/.npm_modules\n")

        add_env_to_user(self.name, {"PATH": {"value": "{}:{}".format(os.path.join(self.install_path, "bin"),
                                                                     os.path.join(os.path.expanduser('~'),
                                                                                  ".npm_modules", "bin"))}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))

    def install_framework_parser(self, parser):
        this_framework_parser = super().install_framework_parser(parser)
        this_framework_parser.add_argument('--lts', action="store_true",
                                           help=_("Install lts version"))
        return this_framework_parser

    def run_for(self, args):
        if args.lts:
            self.download_page = "https://nodejs.org/en/download/"
        if not args.remove:
            print('Download from {}'.format(self.download_page))
        super().run_for(args)
