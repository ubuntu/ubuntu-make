
# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#  Tin Tvrtković
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

"""Tests for the Go category"""
import platform
import subprocess
import os
from os.path import join
import pexpect
import tempfile
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE


class GoTests(LargeFrameworkTests):
    """The default Go google compiler."""

    TIMEOUT_INSTALL_PROGRESS = 300

    EXAMPLE_PROJECT = """package main
                        import "fmt"
                        func main() { fmt.Printf("hello, world") }"""

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/go/go-lang")
        self.framework_name_for_profile = "Go Lang"

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "bin", "go")

    def test_default_go_install(self):
        """Install eclipse from scratch test case"""
        if not self.in_container:
            self.example_prog_dir = tempfile.mkdtemp()
            self.additional_dirs.append(self.example_prog_dir)
            example_file = os.path.join(self.example_prog_dir, "hello.go")
            open(example_file, "w").write(self.EXAMPLE_PROJECT)
            compile_command = ["bash", "-l", "-c", "go run {}".format(example_file)]
        else:  # our mock expects getting that path
            compile_command = ["bash", "-l", "go run /tmp/hello.go"]

        self.child = pexpect.spawnu(self.command('{} go'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        self.assertTrue(self.path_exists(self.exec_path))
        self.assertTrue(self.is_in_path(self.exec_path))

        # compile a small project
        output = subprocess.check_output(self.command_as_list(compile_command)).decode()

        if self.in_container:
            self.assertEqual(output, "hello, world\r\n")
        else:
            self.assertEqual(output, "hello, world")
