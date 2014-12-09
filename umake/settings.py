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

import os

DEFAULT_INSTALL_TOOLS_PATH = os.path.expanduser(os.path.join("~", "tools"))
OLD_CONFIG_FILENAME = "udtc"
CONFIG_FILENAME = "umake"
LSB_RELEASE_FILE = "/etc/lsb-release"
UMAKE_FRAMEWORKS_ENVIRON_VARIABLE = "UMAKE_FRAMEWORKS"

# Those are for the tests
DOCKER_USER = "user"
DOCKER_PASSWORD = "user"
DOCKER_TESTIMAGE = "didrocks/docker-umake-manual"
UMAKE_IN_CONTAINER = "/umake"
TEST_MD5_ANDROID_STUDIO_FAKE_DATA = "490786f827f2578f788e25e423b10cec"
TEST_MD5_ECLIPSE_ADT_32_FAKE_DATA = "3fb4db39926dca2e304b43440e4a25f1"
TEST_MD5_ECLIPSE_ADT_64_FAKE_DATA = "3e26482c619e67b799db0a1d0da02061"
APT_FAKE_REPO_PATH = "/apt-fake-repo"
