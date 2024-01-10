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
import logging
import os
import re
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import get_current_arch, add_env_to_user
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
                         version_regex=r'rust-(\d+(\.\d+)+)',
                         **kwargs)
    arch_trans = {
        "amd64": "x86_64",
        "i386": "i686"
    }

    def parse_download_link(self, line, in_download):
        """Parse Rust download link, expect to find a url"""
        url = None
        if '{}-unknown-linux-gnu.tar.gz">'.format(self.arch_trans[get_current_arch()]) in line:
            p = re.search(r'href="(\S+)">', line)
            with suppress(AttributeError):
                url = p.group(1)
                logger.debug("Found link: {}".format(url))
        return ((url, None), in_download)

    def post_install(self):
        """Add rust necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": "{}:{}:{}".format(os.path.join(self.install_path, "rustc", "bin"),
                                                                        os.path.join(self.install_path, "cargo", "bin"),
                                                                        "$HOME/.cargo/bin")}})

        # adjust for rust: some symlinks magic to have stdlib craft available
        arch_lib_folder = '{}-unknown-linux-gnu'.format(self.arch_trans[get_current_arch()])
        lib_folder = os.path.join(self.install_path, 'rust-std-{}'.format(arch_lib_folder),
                                  'lib', 'rustlib', arch_lib_folder, 'lib')
        arch_dest_lib_folder = os.path.join(self.install_path, 'rustc', 'lib', 'rustlib', arch_lib_folder, 'lib')
        os.mkdir(arch_dest_lib_folder)
        for f in os.listdir(lib_folder):
            os.symlink(os.path.join(lib_folder, f),
                       os.path.join(arch_dest_lib_folder, f))

        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'version'), 'r') as file:
                return re.search(r'(\d+(\.\d+)+)', next(file)).group(1) if file else None
        except FileNotFoundError:
            return
