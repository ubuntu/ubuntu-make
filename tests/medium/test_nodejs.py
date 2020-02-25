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
import subprocess
from ..large import test_nodejs
from ..tools import UMAKE, spawn_process


class NodejsInContainer(ContainerTests, test_nodejs.NodejsTests):
    """This will test the Nodejs integration inside a container"""

    def setUp(self):
        self.hosts = {443: ["nodejs.org"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "nodejs", "nodejs-lang")

    def test_existing_prefix(self):
        subprocess.call(self.command_as_list(['echo', '''"prefix = test" > ~/.npmrc''']))
        self.child = spawn_process(self.command('{} nodejs'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        result = subprocess.check_output(self.command_as_list(['cat', '''~/.npmrc''']))
        self.assertEqual(result.rstrip().decode(), 'prefix = test')

    def test_existing_npmrc(self):
        subprocess.call(self.command_as_list(['echo', '''"test = 123" > ~/.npmrc''']))
        self.child = spawn_process(self.command('{} nodejs'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        result = subprocess.check_output(self.command_as_list(["cat", "~/.npmrc"]))
        self.assertEqual(result.rstrip().decode(), 'test = 123\r\nprefix = ${HOME}/.npm_modules')
