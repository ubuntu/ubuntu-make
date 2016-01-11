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

"""Tests for swift"""

from . import ContainerTests
import os
from ..large import test_swift
from ..tools import get_data_dir, UMAKE


class SwiftInContainer(ContainerTests, test_swift.SwiftTests):
    """This will test the Swift integration inside a container"""

    def setUp(self):
        self.hosts = {443: ["swift.org"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'swift')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "swift", "swift-lang")

    def test_install_with_changed_download_page(self):
        """Installing swift ide should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "swift.org", "download",
                                               "index.html")
        umake_command = self.command('{} swift'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.is_in_path(self.exec_path))
