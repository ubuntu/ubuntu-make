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


"""Go module"""

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import re
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import get_current_arch, add_env_to_user, ChecksumType
from umake.ui import UI

logger = logging.getLogger(__name__)


class GoCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Go", description=_("Go language"),
                         logo_path=None)


class GoLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Go Lang", description=_("Google compiler (default)"), is_category_default=True,
                         only_on_archs=['i386', 'amd64', 'ppc64el', 's390x'],
                         download_page="https://golang.org/dl/",
                         checksum_type=ChecksumType.sha256,
                         dir_to_decompress_in_tarball="go",
                         required_files_path=[os.path.join("bin", "go")],
                         updatable=True, **kwargs)

    update_parse = "go/go(.*).linux-amd64.tar.gz"
    version_parse = {'regex': 'go version go(.*) linux/amd64', 'command': 'go version'}

    arch_trans = {
        "i386": "386",
        "ppc64el": "ppc64le"
    }

    def get_framework_arch(self):
        arch = get_current_arch()
        if arch in self.arch_trans:
            return self.arch_trans[arch]
        return arch

    def parse_download_link(self, line, in_download):
        """Parse Go download link, expect to find a sha and a url"""
        url, sha = (None, None)
        if "linux-{}".format(self.get_framework_arch()) in line:
            in_download = True
        if in_download:
            p = re.search(r'href="(.*)">', line)
            with suppress(AttributeError):
                url = p.group(1)
            p = re.search(r'<td><tt>(\w+)</tt></td>', line)
            with suppress(AttributeError):
                sha = p.group(1)
            if "</tr>" in line:
                in_download = False

        if url is None and sha is None:
            return (None, in_download)
        return ((url, sha), in_download)

    def post_install(self):
        """Add go necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")},
                                    "GOROOT": {"value": self.install_path, "keep": False}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
