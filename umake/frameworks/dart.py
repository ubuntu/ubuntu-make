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
from umake.tools import add_env_to_user, MainLoop, get_current_arch, ChecksumType
from umake.ui import UI

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class DartCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Dart", description=_("Dartlang Development Environment"), logo_path=None)


class DartLangEditorRemoval(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Dart Editor", description=_("Dart SDK with editor (not supported upstream anyymore)"),
                         download_page=None, only_on_archs=_supported_archs, only_for_removal=True, **kwargs)


class DartLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Dart SDK", description=_("Dart SDK (default)"), is_category_default=True,
                         only_on_archs=_supported_archs,
                         download_page="https://www.dartlang.org/tools/sdk",
                         dir_to_decompress_in_tarball="dart-sdk",
                         checksum_type=ChecksumType.sha256,
                         required_files_path=[os.path.join("bin", "dart")],
                         **kwargs)

    arch_trans = {
        "amd64": "x64",
        "i386": "ia32"
        # TODO: add arm
    }

    def parse_download_link(self, line, in_download):
        """Parse Dart SDK download links"""
        in_download = False
        if '(stable)' in line:
            p = re.search(r"([\d\.]+)(&nbsp;)*\(stable\)", line)
            if p is not None:
                in_download = True
        if in_download:
            with suppress(AttributeError):
                self.new_download_url = "https://storage.googleapis.com/dart-archive/channels/stable/" +\
                                        "release/{}/sdk/".format(p.group(1)) +\
                                        "dartsdk-linux-{}-release.zip".format(self.arch_trans[get_current_arch()]) +\
                                        ".sha256sum"
        return ((None, None), in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        # you get and store self.download_url
        url = re.sub('.sha256sum', '', self.new_download_url)
        self.check_data_and_start_download(url, checksum)

    def post_install(self):
        """Add go necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))


class FlutterLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Flutter SDK", description=_("Flutter SDK"),
                         only_on_archs=_supported_archs,
                         download_page="https://docs.flutter.io/",
                         dir_to_decompress_in_tarball="flutter",
                         required_files_path=[os.path.join("bin", "flutter")],
                         **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse Flutter SDK download links"""
        url = None
        in_download = False
        if 'Flutter ' in line:
            p = re.search(r"Flutter\s([\d\.]+)", line)
            if p is not None:
                in_download = True
        if in_download:
            with suppress(AttributeError):
                url = "https://storage.googleapis.com/flutter_infra/releases/stable/linux/" +\
                      "flutter_linux_v{}-stable.tar.xz".format(p.group(1))
        return ((url, None), in_download)

    def post_install(self):
        """Add flutter necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
