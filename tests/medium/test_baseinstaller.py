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

"""Tests for base installer framework in container"""

from . import ContainerTests
import os
from ..large import test_baseinstaller


class BaseInstallerInContainer(ContainerTests, test_baseinstaller.BaseInstallerTests):
    """This will install the Base Framework inside a container"""

    TIMEOUT_START = 10
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {8765: ["localhost"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        self.additional_local_frameworks = [os.path.join("tests", "data", "testframeworks", "baseinstallerfake.py")]
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "base", "base-framework")
