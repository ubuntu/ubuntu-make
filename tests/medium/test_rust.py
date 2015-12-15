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
        self.hosts = {443: ["www.rust-lang.org"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "rust", "rust-lang")

    def test_install_with_changed_download_reference_page(self):
        """Installing Rust should fail if download reference page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.rust-lang.org", "downloads.html")
        umake_command = self.command('{} rust'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.path_exists(self.exec_path))

    def test_install_with_wrong_sha(self):
        """Installing Rust should fail if checksum is wrong"""
        # we only modify the amd64 sha as docker only run on it
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.rust-lang.org",
                                               "rust-fake-x86_64-unknown-linux-gnu.tar.gz.sha256")
        with swap_file_and_restore(download_page_file_path) as content:
            with open(download_page_file_path, "w") as newfile:
                newfile.write(content.replace(self.TEST_CHECKSUM_RUST_DATA, "abcdef"))
            self.child = spawn_process(self.command('{} rust'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn([pexpect.EOF, "Corrupted download? Aborting."],
                                    timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
            self.wait_and_close(exit_status=1)

            # we have nothing installed
            self.assertFalse(self.path_exists(self.exec_path))
