
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

"""Tests for the IDE category"""
import logging
import platform
import subprocess
import os
import pexpect
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE

logger = logging.getLogger(__name__)


class EclipseIDETests(LargeFrameworkTests):
    """The Eclipse distribution from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse")
        self.desktop_filename = "eclipse.desktop"

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def test_default_eclipse_ide_install(self):
        """Install eclipse from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        # on 64 bits, there is a java subprocess, we kill that one with SIGKILL (eclipse isn't reliable on SIGTERM)
        if self.arch_option == "x86_64":
            self.check_and_kill_process(["java", self.arch_option, self.installed_path],
                                        wait_before=self.TIMEOUT_START, send_sigkill=True)
        else:
            self.check_and_kill_process([self.exec_path],
                                        wait_before=self.TIMEOUT_START, send_sigkill=True)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UMAKE)))
        self.expect_and_no_warn("Eclipse is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class EclipseMarsIDETests(LargeFrameworkTests):
    """The Eclipse Mars distribution from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-mars")
        self.desktop_filename = "eclipse-mars.desktop"

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def test_default_eclipse_ide_install(self):
        """Install eclipse mars from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide eclipse-mars'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        # on 64 bits, there is a java subprocess, we kill that one with SIGKILL (eclipse isn't reliable on SIGTERM)
        if self.arch_option == "x86_64":
            self.check_and_kill_process(["java", self.arch_option, self.installed_path],
                                        wait_before=self.TIMEOUT_START, send_sigkill=True)
        else:
            self.check_and_kill_process([self.exec_path],
                                        wait_before=self.TIMEOUT_START, send_sigkill=True)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide eclipse-mars'.format(UMAKE)))
        self.expect_and_no_warn("Eclipse-mars is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class IdeaIDETests(LargeFrameworkTests):
    """IntelliJ Idea from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/idea")
        self.desktop_filename = 'jetbrains-idea.desktop'

    def test_default_install(self):
        """Install from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide idea'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide idea'.format(UMAKE)))
        self.expect_and_no_warn("Idea is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class IdeaUltimateIDETests(LargeFrameworkTests):
    """IntelliJ Idea Ultimate from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/idea-ultimate")
        self.desktop_filename = 'jetbrains-idea.desktop'

    def test_default_install(self):
        """Install from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide idea-ultimate'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        logger.info("Installed, running...")

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide idea-ultimate'.format(UMAKE)))
        self.expect_and_no_warn("Idea Ultimate is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class PyCharmIDETests(LargeFrameworkTests):
    """PyCharm from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/pycharm")
        self.desktop_filename = 'jetbrains-pycharm.desktop'

    def test_default_install(self):
        """Install from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide pycharm'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        logger.info("Installed, running...")

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide pycharm'.format(UMAKE)))
        self.expect_and_no_warn("PyCharm is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class PyCharmEducationalIDETests(LargeFrameworkTests):
    """PyCharm Educational from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/pycharm-educational")
        self.desktop_filename = 'jetbrains-pycharm.desktop'

    def test_default_install(self):
        """Install from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide pycharm-educational'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        logger.info("Installed, running...")

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide pycharm-educational'.format(UMAKE)))
        self.expect_and_no_warn("PyCharm Educational is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class PyCharmProfessionalIDETests(LargeFrameworkTests):
    """PyCharm Professional from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/pycharm-professional")
        self.desktop_filename = 'jetbrains-pycharm.desktop'

    def test_default_install(self):
        """Install from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide pycharm-professional'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        logger.info("Installed, running...")

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide pycharm-professional'.format(UMAKE)))
        self.expect_and_no_warn("PyCharm Professional is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class RubyMineIDETests(LargeFrameworkTests):
    """RubyMine from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/rubymine")
        self.desktop_filename = 'jetbrains-rubymine.desktop'

    def test_default_install(self):
        """Install from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide rubymine'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        logger.info("Installed, running...")

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide rubymine'.format(UMAKE)))
        self.expect_and_no_warn("RubyMine is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class WebStormIDETests(LargeFrameworkTests):
    """WebStorm from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/webstorm")
        self.desktop_filename = 'jetbrains-webstorm.desktop'

    def test_default_install(self):
        """Install from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide webstorm'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        logger.info("Installed, running...")

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide webstorm'.format(UMAKE)))
        self.expect_and_no_warn("WebStorm is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class PhpStormIDETests(LargeFrameworkTests):
    """PhpStorm from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/phpstorm")
        self.desktop_filename = 'jetbrains-phpstorm.desktop'

    def test_default_install(self):
        """Install from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide phpstorm'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        logger.info("Installed, running...")

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide phpstorm'.format(UMAKE)))
        self.expect_and_no_warn("PhpStorm is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()


class ArduinoIDETests(LargeFrameworkTests):
    """The Arduino Software distribution from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/arduino")
        self.desktop_filename = "arduino.desktop"

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def test_default_install(self):
        """Install the distribution from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide arduino'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assertTrue(self.is_in_group("dialout"))

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", "processing.app.Base"], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide arduino'.format(UMAKE)))
        self.expect_and_no_warn("Arduino is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()
