
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
import platform
import subprocess
import tempfile
import os
from os.path import join
import pexpect
from tests.large import LargeFrameworkTests
from tests.tools import UDTC


class EclipseIDETests(LargeFrameworkTests):
    """The Eclipse distribution from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse")
        self.desktop_filename = "eclipse-luna.desktop"
        self.icon_filename = "icon.xpm"

    @property
    def full_icon_path(self):
        return join(self.installed_path, self.icon_filename)

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "eclipse")

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def test_default_eclipse_ide_install(self):
        """Install eclipse from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UDTC)))
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

        # FIXME: disable on i386 jenkins for now (doesn't launch the java subprocess). Need kvm investigation
        if not (os.environ["USER"] == "ubuntu" and self.arch_option == "i686"):
            self.check_and_kill_process(["java", self.arch_option, self.installed_path],
                                        wait_before=self.TIMEOUT_START)
        if not self.in_container:
            self.check_and_kill_process([self.installed_path])  # we need to stop the parent as well for eclipse
            # eclipse exits with 143 on SIGTERM, translated to -15
            self.assertEquals(proc.wait(self.TIMEOUT_STOP), -15)
        else:
            self.assertEquals(proc.wait(self.TIMEOUT_STOP), 143)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UDTC)))
        self.expect_and_no_warn("Eclipse is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()

    def test_doesnt_accept_wrong_path(self):
        """We don't accept a wrong path"""
        self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UDTC)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127)*100)
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127)*100 + "/")
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path), expect_warn=True)
        self.child.sendcontrol('C')
        self.wait_and_no_warn()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.exec_path))
        self.assertFalse(self.path_exists(self.full_icon_path))

    def test_eclipse_ide_reinstall(self):
        """Reinstall eclipse once installed"""
        for loop in ("install", "reinstall"):
            self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UDTC)))
            if loop == "reinstall":
                self.expect_and_no_warn("Eclipse is already installed.*\[.*\] ")
                self.child.sendline("y")
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_no_warn()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assertTrue(self.path_exists(self.exec_path))
            self.assertTrue(self.path_exists(self.full_icon_path))

            # launch it, send SIGTERM and check that it exits fine
            proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            # FIXME: disable on i386 jenkins for now (doesn't launch the java subprocess). Need kvm investigation
            if not (os.environ["USER"] == "ubuntu" and self.arch_option == "i686"):
                self.check_and_kill_process(["java", self.arch_option, self.installed_path],
                                            wait_before=self.TIMEOUT_START)
            if not self.in_container:
                self.check_and_kill_process([self.installed_path])  # we need to stop the parent as well for eclipse
                # android eclipse exits with 143 on SIGTERM, translated to -15
                self.assertEquals(proc.wait(self.TIMEOUT_STOP), -15)
            else:
                self.assertEquals(proc.wait(self.TIMEOUT_STOP), 143)

    def test_eclipse_reinstall_other_path(self):
        """Reinstall eclipse on another path once installed should remove the first version"""
        original_install_path = self.installed_path
        for loop in ("install", "reinstall"):
            if loop == "reinstall":
                self.installed_path = "/tmp/foo"
                self.child = pexpect.spawnu(self.command('{} ide eclipse {}'.format(UDTC, self.installed_path)))
                self.expect_and_no_warn("Eclipse is already installed.*\[.*\] ")
                self.child.sendline("y")
            else:
                self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UDTC)))
                self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_no_warn()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assertTrue(self.path_exists(self.exec_path))
            self.assertTrue(self.path_exists(self.full_icon_path))

        # ensure that version first isn't installed anymore
        self.assertFalse(self.path_exists(original_install_path))

    def test_eclipse_reinstall_other_non_empty_path(self):
        """Reinstall eclipse on another path (non empty) once installed should remove the first version"""
        original_install_path = self.installed_path
        if not self.in_container:
            self.reinstalled_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.reinstalled_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.create_file(os.path.join(self.reinstalled_path, "bar"), "foo")
        for loop in ("install", "reinstall"):
            if loop == "reinstall":
                self.installed_path = self.reinstalled_path
                self.child = pexpect.spawnu(self.command('{} ide eclipse {}'.format(UDTC, self.installed_path)))
                self.expect_and_no_warn("Eclipse is already installed.*\[.*\] ")
                self.child.sendline("y")
                self.expect_and_no_warn("{} isn't an empty directory.*there\? \[.*\] ".format(self.installed_path))
                self.child.sendline("y")
            else:
                self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UDTC)))
                self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_no_warn()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assertTrue(self.path_exists(self.exec_path))
            self.assertTrue(self.path_exists(self.full_icon_path))

        # ensure that version first isn't installed anymore
        self.assertFalse(self.path_exists(original_install_path))

    def test_custom_install_path(self):
        """We install eclipse in a custom path"""
        # We skip the existing directory prompt
        self.child = pexpect.spawnu(self.command('{} ide eclipse /tmp/foo'.format(UDTC)))
        self.accept_default_and_wait()

    def test_start_install_on_empty_dir(self):
        """We try to install on an existing empty dir"""
        if not self.in_container:
            self.installed_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.installed_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.child = pexpect.spawnu(self.command('{} ide eclipse {}'
                                                 .format(UDTC, self.installed_path)))
        self.accept_default_and_wait()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.exec_path))
        self.assertFalse(self.path_exists(self.full_icon_path))

    def test_start_install_on_existing_dir(self):
        """We prompt if we try to install on an existing directory which isn't empty"""
        if not self.in_container:
            self.installed_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.installed_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.create_file(os.path.join(self.installed_path, "bar"), "foo")
        self.child = pexpect.spawnu(self.command('{} ide eclipse {}'
                                                 .format(UDTC, self.installed_path)))
        self.expect_and_no_warn("{} isn't an empty directory.*there\? \[.*\] ".format(self.installed_path))
        self.accept_default_and_wait()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.exec_path))
        self.assertFalse(self.path_exists(self.full_icon_path))

    def test_removal(self):
        """Remove eclipse with default path"""
        self.child = pexpect.spawnu(self.command('{} ide eclipse'.format(UDTC)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.installed_path))
        self.assertTrue(self.path_exists(self.full_icon_path))

        # now, remove it
        self.child = pexpect.spawnu(self.command('{} ide eclipse --remove'.format(UDTC)))
        self.wait_and_no_warn()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.installed_path))
        self.assertFalse(self.path_exists(self.full_icon_path))

    def test_removal_non_default_path(self):
        """Remove eclipse with non default path"""
        self.installed_path = "/tmp/foo"
        self.child = pexpect.spawnu(self.command('{} ide eclipse {}'.format(UDTC, self.installed_path)))
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.installed_path))
        self.assertTrue(self.path_exists(self.full_icon_path))

        # now, remove it
        self.child = pexpect.spawnu(self.command('{} ide eclipse --remove'.format(UDTC)))
        self.wait_and_no_warn()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.installed_path))
        self.assertFalse(self.path_exists(self.full_icon_path))

