
# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
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

"""Tests for the Web category"""
import logging
import platform
import subprocess
import os
from os.path import join
import pexpect
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE

logger = logging.getLogger(__name__)


class FirefoxDevTests(LargeFrameworkTests):
    """Tests for Firefox Developer Edition"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/web/firefox-dev")
        self.desktop_filename = "firefox-developer.desktop"
        self.icon_filename = "mozicon128.png"

    @property
    def full_icon_path(self):
        return join(self.installed_path, "browser", "icons", self.icon_filename)

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "firefox")

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def test_default__install(self):
        """Install firefox dev from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} web firefox-dev'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.exec_path))
        self.assertTrue(self.path_exists(self.full_icon_path))

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["firefox-dev", self.installed_path],
                                    wait_before=self.TIMEOUT_START, send_sigkill=True)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} web firefox-dev'.format(UMAKE)))
        self.expect_and_no_warn("Firefox Dev is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()
