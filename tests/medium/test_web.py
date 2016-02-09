# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
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

"""Tests for web category"""

from . import ContainerTests
import os
from ..large import test_web
from ..tools import get_data_dir, UMAKE


class FirefoxDevContainer(ContainerTests, test_web.FirefoxDevTests):
    """This will test the Firefox dev integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["www.mozilla.org"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "web", "firefox-dev")

    def test_install_with_changed_download_page(self):
        """Installing firefox developer should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.mozilla.org", "en-US",
                                               "firefox", "developer", "all")
        umake_command = self.command('{} web firefox-dev'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))


class VisualStudioCodeInContainer(ContainerTests, test_web.VisualStudioCodeTest):
    """This will test the Visual Studio Code integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["code.visualstudio.com"], 80: ["go.microsoft.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'vscode')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "web", "visual-studio-code")
