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
from umake.network.download_center import DownloadItem
from umake.tools import add_env_to_user, MainLoop
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
                         download_page="https://api.dartlang.org",
                         dir_to_decompress_in_tarball="dart-sdk",
                         required_files_path=[os.path.join("bin", "dart")])

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Get latest version and append files to download"""
        logger.debug("Set download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        version = ''
        version_re = r'Dart SDK ([\d\.]+)'
        for line in result[self.download_page].buffer:
            p = re.search(version_re, line.decode())
            with suppress(AttributeError):
                version = p.group(1)
                break
        else:
            logger.error("Download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

        tag_machine = 'x64'
        if platform.machine() == 'i686':
            tag_machine = 'ia32'

        url = "https://storage.googleapis.com/dart-archive/channels/stable/release/{}/sdk/dartsdk-linux-{}-release.zip"\
            .format(version, tag_machine)
        logger.debug("Found download link for {}".format(url))

        self.download_requests.append(DownloadItem(url, None))
        self.start_download_and_install()

    def post_install(self):
        """Add go necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(_("You need to restart your current shell session for your {} installation "
                                            "to work properly").format(self.name)))
