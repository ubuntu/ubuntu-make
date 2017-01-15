# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Canonical
#
# Authors:
#  Didier Roche
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

"""Tests for rust"""

from . import ContainerTests
import os
import pexpect

from ..large import test_rust
from ..tools import get_data_dir, UMAKE, swap_file_and_restore, spawn_process


class RustInContainer(ContainerTests, test_rust.RustTests):
    """This will test the Rust integration inside a container"""

    TEST_CHECKSUM_RUST_DATA = "2a0db6efe370a900491d9e9db13e53ffd00b01dcd8458486f9f3fc3177f96af3"

    def setUp(self):
        self.hosts = {443: ["www.rust-lang.org", "static.rust-lang.org"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "rust", "rust-lang")

    def test_install_with_changed_download_reference_page(self):
        """Installing Rust should fail if download reference page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.rust-lang.org",
                                               "en-US", "other-installers.html")
        umake_command = self.command('{} rust'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.path_exists(self.exec_path))
