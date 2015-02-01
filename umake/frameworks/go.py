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

    def __init__(self, category):
        super().__init__(name="Go Lang", description=_("Google compiler (default)"), is_category_default=True,
                         category=category, only_on_archs=['i386', 'amd64'], expect_license=False,
                         download_page="https://golang.org/dl/",
                         checksum_type=ChecksumType.sha1,
                         dir_to_decompress_in_tarball="go")

    def parse_download_link(self, line, in_download):
        """Parse Go download link, expect to find a sha1 and a url"""
        url, sha1 = (None, None)
        if "linux-{}".format(get_current_arch().replace("i386", "386")) in line:
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

    def post_install(self):
        """Add go necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")},
                                    "GOROOT": {"value": self.install_path}})
        UI.delayed_display(DisplayMessage(_("You need to restart a shell session for your installation to work")))

    @property
    def is_installed(self):
        """Checks path and requirements for installation"""
        if not super().is_installed:
            return False
        if not os.path.isfile(os.path.join(self.install_path, "bin", "go")):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True
