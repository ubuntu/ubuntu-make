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

"""Tests for large base installer framework"""

from . import LargeFrameworkTests
import os
import platform
import shutil
import subprocess

from ..tools import UMAKE, spawn_process, get_data_dir
from ..tools.local_server import LocalHttp


class BaseInstallerTests(LargeFrameworkTests):
    """This will test the base installer framework via a fake one"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 1
    TIMEOUT_STOP = 1

    server = None
    JAVAEXEC = "java-fake64"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        server_dir = os.path.join(get_data_dir(), "server-content", "localhost")
        cls.server = LocalHttp(server_dir, port=8765)
        cls.testframework = os.path.expanduser(os.path.join('~', '.umake', 'frameworks', 'baseinstallerfake.py'))
        shutil.copy(os.path.join(get_data_dir(), "testframeworks", "baseinstallerfake.py"), cls.testframework)
        if platform.machine() != "x86_64":
            cls.JAVAEXEC = "java-fake32"

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        os.remove(cls.testframework)
        cls.server.stop()

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "base", "base-framework")
        self.desktop_filename = "base-framework.desktop"

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def test_default_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.check_and_kill_process([self.JAVAEXEC, self.installed_path], wait_before=self.TIMEOUT_START)
        self.assertEqual(proc.wait(self.TIMEOUT_STOP), 143)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
        self.expect_and_no_warn("Base Framework is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()
