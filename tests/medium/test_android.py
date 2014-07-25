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

"""Tests for basic CLI commands"""

from . import ContainerTests
import os
from ..large.test_android import AndroidStudioTests
from udtc import settings


class AndroidStudioInContainer(ContainerTests, AndroidStudioTests):
    """This will test the basic cli command class inside a container"""

    def setUp(self):
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/android/android-studio".format(settings.DOCKER_USER))
