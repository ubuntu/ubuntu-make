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

"""Tests for the Nodejs category"""
import subprocess
import os
import tempfile
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE, spawn_process


class NodejsTests(LargeFrameworkTests):
    """Nodejs stable."""

    TIMEOUT_INSTALL_PROGRESS = 300

    EXAMPLE_PROJECT = """console.log("Hello World");"""

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "nodejs", "nodejs-lang")
        self.framework_name_for_profile = "Nodejs Lang"

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "bin", "node")

    def test_default_nodejs_install(self):
        """Install Nodejs from scratch test case"""
        if not self.in_container:
            self.example_prog_dir = tempfile.mkdtemp()
            self.additional_dirs.append(self.example_prog_dir)
            example_file = os.path.join(self.example_prog_dir, "hello.js")
            open(example_file, "w").write(self.EXAMPLE_PROJECT)
            compile_command = ["bash", "-l", "-c", "node {}".format(example_file)]
            npm_command = ["bash", "-l", "-c", "npm config get prefix"]
        else:  # our mock expects getting that path
            compile_command = ["bash", "-l", "node /tmp/hello.js"]
            npm_command = ["bash", "-l", "npm config get prefix"]

        self.child = spawn_process(self.command('{} nodejs'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))

        npm_path = os.path.join(self.installed_path, "bin", "npm")
        self.assertTrue(self.path_exists(npm_path))
        self.assertTrue(self.is_in_path(npm_path))

        # compile a small project
        output = subprocess.check_output(self.command_as_list(compile_command)).decode()\
            .replace('\r', '').replace('\n', '')

        # set npm prefix
        npm_output = subprocess.check_output(self.command_as_list(npm_command)).decode()\
            .replace('\r', '').replace('\n', '')

        self.assertEqual(output, "Hello World")
        self.assertEqual(npm_output, "{}/.npm_modules".format(os.path.join("/",
                                                              self.installed_path.split('/')[1],
                                                              self.installed_path.split('/')[2])))

    def test_lts_select_install(self):
        """Install nodejs lts"""
        self.child = spawn_process(self.command('{} nodejs --lts').format(UMAKE))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()
