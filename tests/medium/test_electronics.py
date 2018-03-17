# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#  Tin Tvrtković
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

"""Tests for ides"""

from . import ContainerTests
import os
import pexpect

from ..large import test_electronics
from ..tools import get_data_dir, swap_file_and_restore, UMAKE, spawn_process


class ArduinoIDEInContainer(ContainerTests, test_electronics.ArduinoIDETests):
    """This will test the Arduino IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {80: ["www.arduino.cc"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'arduino')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "electronics", "arduino")

    def test_install_with_changed_download_page(self):
        """Installing arduino ide should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.arduino.cc", "en", "Main",
                                               "Software")
        umake_command = self.command('{} electronics arduino'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))

    def test_install_with_changed_checksum_page(self):
        """Installing arduino ide should fail if checksum link is unparseable"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.arduino.cc",
                                               "checksums.md5sum.txt")
        umake_command = self.command('{} electronics arduino'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))


class EagleTestsInContainer(ContainerTests, test_electronics.EagleTests):
    """This will test the Eagle integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["eagle-updates.circuits.io"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "electronics", "eagle")

    def test_install_with_changed_download_page(self):
        """Installing eagle ide should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "eagle-updates.circuits.io",
                                               "downloads", "latest.html")
        umake_command = self.command('{} electronics eagle'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))
