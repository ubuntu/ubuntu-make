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

"""Tests for the Dart category"""
import logging
import os
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE, spawn_process

logger = logging.getLogger(__name__)


class DartTests(LargeFrameworkTests):
    """Tests for Dart Editor with SDK"""

    TIMEOUT_INSTALL_PROGRESS = 120

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "dart", "dart-sdk")

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "bin", "dart")

    def test_default_dart_install(self):
        """Install dart editor from scratch test case"""
        self.child = spawn_process(self.command('{} dart'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher and an icon file
        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} dart'.format(UMAKE)))
        self.expect_and_no_warn(r"Dart SDK is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class FlutterTests(LargeFrameworkTests):
    """Tests for Dart Editor with SDK"""

    TIMEOUT_INSTALL_PROGRESS = 120

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "dart", "flutter-sdk")

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "bin", "flutter")

    def test_default_dart_install(self):
        """Install dart editor from scratch test case"""
        self.child = spawn_process(self.command('{} dart flutter-sdk'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher and an icon file
        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} dart flutter-sdk'.format(UMAKE)))
        self.expect_and_no_warn(r"Flutter SDK is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()
