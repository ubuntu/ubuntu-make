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

"""Tests for the Swift category"""
import subprocess
import os
import tempfile
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE, spawn_process


class SwiftTests(LargeFrameworkTests):
    """The default Swift compiler."""

    TIMEOUT_INSTALL_PROGRESS = 300

    EXAMPLE_PROJECT = """print("Hello, world!")
                         """

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "swift", "swift-lang")
        self.framework_name_for_profile = "Swift Lang"

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "usr", "bin", "swift")

    def test_default_swift_install(self):
        """Install Swift from scratch test case"""
        if not self.in_container:
            self.example_prog_dir = tempfile.mkdtemp()
            self.additional_dirs.append(self.example_prog_dir)
            example_file = os.path.join(self.example_prog_dir, "main.swift")
            open(example_file, "w").write(self.EXAMPLE_PROJECT)
            compile_command = ["bash", "-l", "-c", "swift {}".format(example_file)]
        else:  # our mock expects getting that command parameter
            self.example_prog_dir = "/tmp"
            compile_command = ["bash", "-l", "swift /tmp/main.swift"]

        self.child = spawn_process(self.command('{} swift'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))

        # run the compiled result
        output = subprocess.check_output(self.command_as_list(compile_command)).decode()\
            .replace('\r', '').replace('\n', '')

        self.assertEqual(output, "Hello, world!")
