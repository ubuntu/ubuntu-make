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

"""Tests for android frameworks in container"""

from . import ContainerTests
import os
from ..large import test_android


class AndroidStudioInContainer(ContainerTests, test_android.AndroidStudioTests):
    """This will install Android Studio inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["developer.android.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "android", "android-studio")


class AndroidSDKContainer(ContainerTests, test_android.AndroidSDKTests):
    """This will install Android SDK inside a container"""

    def setUp(self):
        self.hosts = {443: ["developer.android.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "android", "android-sdk")


class AndroidNDKContainer(ContainerTests, test_android.AndroidNDKTests):
    """This will install Android NDK inside a container"""

    def setUp(self):
        self.hosts = {443: ["developer.android.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "android", "android-ndk")
