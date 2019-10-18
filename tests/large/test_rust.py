# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Canonical
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

    def test_default_rust_install(self):
        """Install Rust from scratch test case"""
        if not self.in_container:
            self.example_prog_dir = tempfile.mkdtemp()
            self.additional_dirs.append(self.example_prog_dir)
            example_file = os.path.join(self.example_prog_dir, "hello.rs")
            open(example_file, "w").write(self.EXAMPLE_PROJECT)
            # rust compile in pwd by default, do not pollute ubuntu make source code
            compile_command = ["bash", "-l", "-c", "rustc --out-dir {} {}".format(self.example_prog_dir, example_file)]
        else:  # our mock expects getting that path
            self.example_prog_dir = "/tmp"
            example_file = os.path.join(self.example_prog_dir, "hello.rs")
            # rust compile in pwd by default, do not pollute ubuntu make source code
            compile_command = ["bash", "-l", "rustc --out-dir {} {}".format(self.example_prog_dir, example_file)]
        resulting_binary = os.path.join(self.example_prog_dir, "hello")

        self.child = spawn_process(self.command('{} rust'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))
        self.assertTrue(self.is_in_path(os.path.join(self.installed_path, "cargo", "bin", "cargo")))
        cmd_list = ["echo $LD_LIBRARY_PATH"]
        if not self.in_container:
            relogging_command = ["bash", "-l", "-c"]
            relogging_command.extend(cmd_list)
            cmd_list = relogging_command
        self.assertIn(os.path.join(self.installed_path, "rustc", "lib"),
                      subprocess.check_output(self.command_as_list(cmd_list)).decode("utf-8").strip().split(":"))

        # compile a small project
        subprocess.check_call(self.command_as_list(compile_command))

        # run the compiled result
        output = subprocess.check_output(self.command_as_list(resulting_binary)).decode()\
            .replace('\r', '').replace('\n', '')

        self.assertEqual(output, "hello, world")
