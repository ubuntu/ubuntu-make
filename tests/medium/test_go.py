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

"""Tests for go"""

from . import ContainerTests
import os
from ..large import test_go
from umake import settings


class GoInContainer(ContainerTests, test_go.GoTests):
    """This will test the Go integration inside a container"""

    def setUp(self):
        self.hostname = "golang.org"
        self.port = "443"
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/go/go-lang".format(settings.DOCKER_USER))
