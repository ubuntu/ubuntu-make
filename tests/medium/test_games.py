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

"""Tests for games framework"""

from . import ContainerTests
import os
from ..large import test_games


class StencylInContainer(ContainerTests, test_games.StencylTests):
    """This will test the Stencyl editor inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {80: ["www.stencyl.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'stencyl')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "games", "stencyl")


class Unity3DInContainer(ContainerTests, test_games.Unity3DTests):
    """This will test the Unity 3D editor inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {80: ["forum.unity3d.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'unity3d')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "games", "unity3d")


class TwineInContainer(ContainerTests, test_games.TwineTests):
    """This will test Twine inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {80: ["twinery.org"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "games", "twine")
