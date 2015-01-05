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
from umake import settings


class StencylInContainer(ContainerTests, test_games.StencylTests):
    """This will test the basic cli command class inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.stencyl.com"
        self.port = "80"
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'stencyl')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/games/stencyl".format(settings.DOCKER_USER))
