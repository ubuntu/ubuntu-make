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
CONFIG_FILENAME = "udtc"
LSB_RELEASE_FILE = "/etc/lsb-release"
UDTC_FRAMEWORKS_ENVIRON_VARIABLE = "UDTC_FRAMEWORKS"

# Those are for the tests
DOCKER_USER = "user"
DOCKER_PASSWORD = "user"
DOCKER_TESTIMAGE = "didrocks/docker-udtc"
UDTC_IN_CONTAINER = "/udtc"
TEST_MD5_ANDROID_STUDIO_FAKE_DATA = "f55cc96c8ffda42ee151e71e313b6bf9"
TEST_MD5_ECLIPSE_ADT_32_FAKE_DATA = "edfec4e37d62e410a284bfa190a41802"
TEST_MD5_ECLIPSE_ADT_64_FAKE_DATA = "8e3e67b68250e6bedc202d492b76e4cd"
APT_FAKE_REPO_PATH = "/apt-fake-repo"
