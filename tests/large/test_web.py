
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

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def verify_install(self, installed_language):
        # we have an installed launcher, added to the launcher, a dictionary file and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.language_file_exists(installed_language))
        self.assert_exec_exists()
        self.assert_icon_exists()

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

    def test_default_install(self):
        """Install firefox dev from scratch test case"""
        install_language = "en-US"
        self.child = pexpect.spawnu(self.command('{} web firefox-dev'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Choose language:")
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()
        self.verify_install(install_language)

    def test_arg_language_select_install(self):
        """Install firefox dev with language selected by --lang"""
        install_language = "bg"
        self.child = pexpect.spawnu(self.command('{} web firefox-dev --lang={}'.format(UMAKE, install_language)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()
        self.verify_install(install_language)

    def test_interactive_language_select_install(self):
        """Install firefox dev with language selected interactively"""
        install_language = "bg"
        self.child = pexpect.spawnu(self.command('{} web firefox-dev'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Choose language:")
        self.child.sendline(install_language)
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()
        self.verify_install(install_language)

    def language_file_exists(self, language):
        return self.path_exists(os.path.join(self.installed_path, "dictionaries", "{}.aff".format(language)))


class VisualStudioCodeTest(LargeFrameworkTests):
    """Tests for Visual Studio Code"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/web/visual-studio-code")
        self.desktop_filename = "visual-studio-code.desktop"

    def test_default_install(self):
        """Install visual studio from scratch test case"""

        self.child = pexpect.spawnu(self.command('{} web visual-studio-code'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["Code", self.installed_path],
                                    wait_before=self.TIMEOUT_START, send_sigkill=True)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} web visual-studio-code'.format(UMAKE)))
        self.expect_and_no_warn("Visual Studio Code is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()
