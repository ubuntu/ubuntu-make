# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
#
# Authors:
#  Didier Roche
#  Tin Tvrtković
#  Jared Ravetch
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

"""Tests for the Rust category"""
import subprocess
import os
import tempfile
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE, spawn_process


class RustTests(LargeFrameworkTests):
    """The official Rust distribution"""

    TIMEOUT_INSTALL_PROGRESS = 300

    EXAMPLE_PROJECT = """fn main() {println!("hello, world");}"""

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "rust", "rust-lang")
        self.framework_name_for_profile = "Rust"

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "rustc", "bin", "rustc")

    @property
    def cargo_path(self):
        return os.path.join(self.installed_path, "cargo", "bin", "cargo")

    def test_default_rust_install(self):
        """Install Rust from scratch test case"""
        if not self.in_container:
            self.example_prog_dir = tempfile.mkdtemp()
            self.additional_dirs.append(self.example_prog_dir)
            example_file = os.path.join(self.example_prog_dir, "hello.rs")
            open(example_file, "w").write(self.EXAMPLE_PROJECT)
            compile_command = ["bash", "-l", "-c", "rustc {}".format(example_file)]
        else:  # our mock expects getting that path
            compile_command = ["bash", "-l", "rustc /tmp/hello.rs"]

        self.child = spawn_process(self.command('{} rust'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        self.assertTrue(self.is_in_path(self.exec_path))
        self.assertTrue(self.is_in_path(self.cargo_path))
        self.assert_exec_exists()
        cmd_list = ["echo $LD_LIBRARY_PATH"]
        if not self.in_container:
            relogging_command = ["bash", "-l", "-c"]
            relogging_command.extend(cmd_list)
            cmd_list = relogging_command
        self.assertEqual(subprocess.check_output(self.command_as_list(cmd_list)).decode("utf-8").strip(),
                         self.installed_path)

        # compile a small project
        output = subprocess.check_output(self.command_as_list(compile_command)).decode()

        if self.in_container:
            self.assertEqual(output, "hello, world\r\n")
        else:
            self.assertEqual(output, "hello, world\n")
