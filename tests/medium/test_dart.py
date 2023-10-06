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

"""Tests for dart"""

from . import ContainerTests
import os
from ..large import test_dart
from ..tools import get_data_dir, UMAKE


class DartInContainer(ContainerTests, test_dart.DartTests):
    """This will test the Dart integration inside a container"""

    def setUp(self):
        self.hosts = {443: ["storage.googleapis.com"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "dart", "dart-sdk")

    def test_install_with_changed_version_page(self):
        """Installing dart sdk should fail if version page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content",
                                               "storage.googleapis.com/dart-archive",
                                               "channels/stable/release/latest/VERSION")
        umake_command = self.command('{} dart'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists(self.desktop_filename))


class FlutterInContainer(ContainerTests, test_dart.FlutterTests):
    """This will test the Flutter integration inside a container"""

    def setUp(self):
        self.hosts = {443: ["storage.googleapis.com"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "dart", "flutter-sdk")

    def test_install_with_changed_version_page(self):
        """Installing dart sdk should fail if version page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content",
                                               "storage.googleapis.com/flutter_infra",
                                               "releases/releases_linux.json")
        umake_command = self.command('{} dart flutter-sdk'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists(self.desktop_filename))
