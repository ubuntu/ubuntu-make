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


"""Dartlang module"""

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import platform
import re
import umake.frameworks.baseinstaller
from umake.tools import create_launcher, get_application_desktop_file

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class DartCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Dart", description=_("Dartlang Development Environment"), logo_path=None)


class DartLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Dart Editor", description=_("Dart SDK with editor (default)"), is_category_default=True,
                         category=category, only_on_archs=_supported_archs, expect_license=False,
                         packages_requirements=["openjdk-7-jdk"],
                         download_page="https://www.dartlang.org/tools/download-editor.html",
                         dir_to_decompress_in_tarball="dart",
                         desktop_filename="dart-editor.desktop")

    def parse_download_link(self, line, in_download):
        """Parse Dart Lang download link, expect to find a url"""

        if 'data-os="linux"' in line and 'data-tool="editor"' in line:
            arch = platform.machine()
            tag_machine = '64'
            if arch == 'i686':
                tag_machine = '32'
            if 'data-bits="{}"'.format(tag_machine) in line:
                p = re.search(r'href="(.*)"', line)
                with suppress(AttributeError):
                    url = p.group(1)
                    return ((url, None), True)
        return ((None, None), False)

    def post_install(self):
        """Create the Dart Editor launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Dart Editor"),
                        icon_path=os.path.join(self.install_path, "icon.xpm"),
                        exec=os.path.join(self.install_path, "DartEditor"),
                        comment=_("Dart Editor for the dart language"),
                        categories="Development;IDE;"))

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not os.path.isfile(os.path.join(self.install_path, "DartEditor")):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True
