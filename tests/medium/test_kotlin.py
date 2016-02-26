# -*- coding: utf-8 -*-
# Copyright (C) 2016 Canonical
#
# Authors:
#  Omer Sheikh
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

"""Tests for kotlin"""

from . import ContainerTests
import os
from ..large import test_kotlin
from ..tools import get_data_dir, UMAKE


class KotlinInContainer(ContainerTests, test_kotlin.KotlinTests):
    """This will test Kotlin integration inside a container"""

    def setUp(self):
        self.hosts = {443: ["api.github.com", "github.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'kotlin')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "kotlin", "kotlin-lang")

    def test_install_with_changed_download_page(self):
        """Installing Kotlin should fail if the download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "api.github.com", "repos",
                                               "Jetbrains", "kotlin", "releases", "latest")
        umake_command = self.command('{} kotlin'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.path_exists(self.exec_path))
