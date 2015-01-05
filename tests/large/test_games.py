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

"""Tests for android"""

from . import LargeFrameworkTests
import os
import pexpect
import subprocess
from ..tools import UMAKE


class StencylTests(LargeFrameworkTests):
    """This will test the Stencyl installation"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/games/stencyl")
        self.desktop_filename = "stencyl.desktop"

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "Stencyl")

    def test_default_stencyl_install(self):
        """Install stencyl from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} games stencyl'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.exec_path))
        # launch it, send SIGTERM and check that it exits fine
        use_cwd = self.installed_path
        if self.in_container:
            use_cwd = None
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, cwd=use_cwd)
        self.check_and_kill_process(["./runtimes/jre-linux/bin/java"], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} games stencyl'.format(UMAKE)))
        self.expect_and_no_warn("Stencyl is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()
