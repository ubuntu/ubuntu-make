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

"""Tests for nodejs"""

from . import ContainerTests
import os
from ..large import test_nodejs


class NodejsInContainer(ContainerTests, test_nodejs.NodejsTests):
    """This will test the Nodejs integration inside a container"""

    def setUp(self):
        self.hosts = {443: ["nodejs.org"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "nodejs", "nodejs-lang")
