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
TEST_MD5_ANDROID_STUDIO_FAKE_DATA = "b459f70816cf77b3dddc38291bd2f919d5437aef"
APT_FAKE_REPO_PATH = "/apt-fake-repo"
