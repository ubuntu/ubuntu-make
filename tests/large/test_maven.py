# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#  Tin Tvrtković
#  Igor Vuk
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

"""Tests for the Maven category"""
import os
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE, spawn_process


class MavenTests(LargeFrameworkTests):
    """The default Maven compiler."""

    TIMEOUT_INSTALL_PROGRESS = 300

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "maven", "maven-lang")
        self.framework_name_for_profile = "Maven Lang"

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "bin", "mvn")

    def test_default_maven_install(self):
        """Install Maven from scratch test case"""

        self.child = spawn_process(self.command('{} maven'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))
