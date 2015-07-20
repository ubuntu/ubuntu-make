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
from umake.interactions import DisplayMessage
from umake.tools import add_env_to_user
from umake.ui import UI

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class DartCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Dart", description=_("Dartlang Development Environment"), logo_path=None)


class DartLangEditorRemoval(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Dart Editor", description=_("Dart SDK with editor (not supported upstream anyymore)"),
                         download_page=None, category=category, only_on_archs=_supported_archs, only_for_removal=True)


class DartLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Dart SDK", description=_("Dart SDK (default)"), is_category_default=True,
                         category=category, only_on_archs=_supported_archs,
                         download_page="https://www.dartlang.org/downloads/linux.html",
                         dir_to_decompress_in_tarball="dart-sdk")

    def parse_download_link(self, line, in_download):
        """Parse Dart Lang download link, expect to find a url"""
        tag_machine = '64'
        if platform.machine() == 'i686':
            tag_machine = '32'
        download_re = r'<a data-bits="{}" data-os="linux" data-tool="sdk".*href="(.*)">'.format(tag_machine)

        p = re.search(download_re, line)
        with suppress(AttributeError):
            url = p.group(1)
            return ((url, None), True)
        return ((None, None), False)

    def post_install(self):
        """Add go necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(_("You need to restart a shell session for your installation to work")))

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not os.path.isfile(os.path.join(self.install_path, "bin", "dart")):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True
