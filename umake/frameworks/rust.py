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
    def __init__(self, **kwargs):
        super().__init__(name="Rust Lang",
                         description=_("The official Rust distribution"),
                         is_category_default=True,
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://www.rust-lang.org/en-US/other-installers.html",
                         dir_to_decompress_in_tarball="rust-*",
                         **kwargs)
    arch_trans = {
        "amd64": "x86_64",
        "i386": "i686"
    }

    def parse_download_link(self, line, in_download):
        """Parse Rust download link, expect to find a url"""
        url = None
        if '{}-unknown-linux-gnu.tar.gz">'.format(self.arch_trans[get_current_arch()]) in line:
            p = re.search(r'href="(.*)">', line)
            with suppress(AttributeError):
                url = p.group(1)
                logger.debug("Found link: {}".format(url))
        return ((url, None), in_download)

    def post_install(self):
        """Add rust necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": "{}:{}".format(os.path.join(self.install_path, "rustc", "bin"),
                                                                     os.path.join(self.install_path, "cargo", "bin"))},
                                    "LD_LIBRARY_PATH": {"value": os.path.join(self.install_path, "rustc", "lib")}})

        # adjust for rust: some symlinks magic to have stdlib craft available
        arch_lib_folder = '{}-unknown-linux-gnu'.format(self.arch_trans[get_current_arch()])
        os.symlink(os.path.join(self.install_path, 'rust-std-{}'.format(arch_lib_folder), 'lib', 'rustlib',
                                arch_lib_folder, 'lib'),
                   os.path.join(self.install_path, 'rustc', 'lib', 'rustlib', arch_lib_folder, 'lib'))

        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
