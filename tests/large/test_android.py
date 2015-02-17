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
import platform
import subprocess
import tempfile
from umake.tools import get_icon_path
from ..tools import UMAKE


class AndroidStudioTests(LargeFrameworkTests):
    """This will test the Android Studio base"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/android/android-studio")
        self.desktop_filename = "android-studio.desktop"

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "bin", "studio.sh")

    def test_default_android_studio_install(self):
        """Install android studio from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} android android-studio'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.exec_path))

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        self.assertEqual(proc.wait(self.TIMEOUT_STOP), 0)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} android android-studio'.format(UMAKE)))
        self.expect_and_no_warn("Android Studio is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()

    def test_no_license_accept_android_studio(self):
        """We don't accept the license (default)"""
        self.child = pexpect.spawnu(self.command('{} android android-studio'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
        self.accept_default_and_wait()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.exec_path))

    def test_doesnt_accept_wrong_path(self):
        """We don't accept a wrong path"""
        self.child = pexpect.spawnu(self.command('{} android android-studio'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127)*100)
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127)*100 + "/")
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path), expect_warn=True)
        self.child.sendcontrol('C')
        self.wait_and_no_warn()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.exec_path))

    def test_android_studio_reinstall(self):
        """Reinstall android studio once installed"""
        for loop in ("install", "reinstall"):
            self.child = pexpect.spawnu(self.command('{} android android-studio'.format(UMAKE)))
            if loop == "reinstall":
                # we only have one question, not the one about existing dir.
                self.expect_and_no_warn("Android Studio is already installed.*\[.*\] ")
                self.child.sendline("y")
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_no_warn()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assertTrue(self.path_exists(self.exec_path))

            # launch it, send SIGTERM and check that it exits fine
            proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
            self.assertEqual(proc.wait(self.TIMEOUT_STOP), 0)

    def test_android_studio_reinstall_other_path(self):
        """Reinstall android studio on another path once installed should remove the first version"""
        original_install_path = self.installed_path
        for loop in ("install", "reinstall"):
            if loop == "reinstall":
                self.installed_path = "/tmp/foo"
                self.child = pexpect.spawnu(self.command('{} android android-studio {}'.format(UMAKE,
                                                                                               self.installed_path)))
                self.expect_and_no_warn("Android Studio is already installed.*\[.*\] ")
                self.child.sendline("y")
            else:
                self.child = pexpect.spawnu(self.command('{} android android-studio'.format(UMAKE)))
                self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_no_warn()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assertTrue(self.path_exists(self.exec_path))

        # ensure that version first isn't installed anymore
        self.assertFalse(self.path_exists(original_install_path))

    def test_android_studio_reinstall_other_non_empty_path(self):
        """Reinstall android studio on another path (non empty) once installed should remove the first version"""
        original_install_path = self.installed_path
        if not self.in_container:
            self.reinstalled_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.reinstalled_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.create_file(os.path.join(self.reinstalled_path, "bar"), "foo")
        for loop in ("install", "reinstall"):
            if loop == "reinstall":
                self.installed_path = self.reinstalled_path
                self.child = pexpect.spawnu(self.command('{} android android-studio {}'.format(UMAKE,
                                                                                               self.installed_path)))
                self.expect_and_no_warn("Android Studio is already installed.*\[.*\] ")
                self.child.sendline("y")
                self.expect_and_no_warn("{} isn't an empty directory.*there\? \[.*\] ".format(self.installed_path))
                self.child.sendline("y")
            else:
                self.child = pexpect.spawnu(self.command('{} android android-studio'.format(UMAKE)))
                self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_no_warn()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assertTrue(self.path_exists(self.exec_path))

        # ensure that version first isn't installed anymore
        self.assertFalse(self.path_exists(original_install_path))

    def test_custom_install_path(self):
        """We install android studio in a custom path"""
        # We skip the existing directory prompt
        self.child = pexpect.spawnu(self.command('{} android android-studio /tmp/foo'.format(UMAKE)))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()

    def test_start_install_on_empty_dir(self):
        """We try to install on an existing empty dir"""
        if not self.in_container:
            self.installed_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.installed_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.child = pexpect.spawnu(self.command('{} android android-studio {}'
                                                 .format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.exec_path))

    # FIXME: should do a real install to check everything's fine
    def test_start_install_on_existing_dir(self):
        """We prompt if we try to install on an existing directory which isn't empty"""
        if not self.in_container:
            self.installed_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.installed_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.create_file(os.path.join(self.installed_path, "bar"), "foo")
        self.child = pexpect.spawnu(self.command('{} android android-studio {}'
                                                 .format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("{} isn't an empty directory.*there\? \[.*\] ".format(self.installed_path))
        self.accept_default_and_wait()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.exec_path))

    def test_is_default_framework(self):
        """Android Studio is chosen as the default framework"""
        self.child = pexpect.spawnu(self.command('{} android'.format(UMAKE)))
        # we ensure it thanks to installed_path being the android-studio one
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendcontrol('C')
        self.wait_and_no_warn()

    def test_is_default_framework_with_options(self):
        """Android Studio options are sucked in as the default framework"""
        self.child = pexpect.spawnu(self.command('{} android /tmp/foo'.format(UMAKE)))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()

    def test_not_default_framework_with_path_without_path_separator(self):
        """Android Studio isn't selected for default framework with path without separator"""
        self.child = pexpect.spawnu(self.command('{} android foo'.format(UMAKE)))
        self.expect_and_no_warn("error: argument framework: invalid choice")
        self.accept_default_and_wait()

    def test_is_default_framework_with_user_path(self):
        """Android Studio isn't selected for default framework with path without separator"""
        # TODO: once a baseinstaller test: do a real install to check the path
        self.child = pexpect.spawnu(self.command('{} android ~/foo'.format(UMAKE)))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()

    def test_removal(self):
        """Remove android studio with default path"""
        self.child = pexpect.spawnu(self.command('{} android android-studio'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[.*\] ")
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.installed_path))

        # now, remove it
        self.child = pexpect.spawnu(self.command('{} android android-studio --remove'.format(UMAKE)))
        self.wait_and_no_warn()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.installed_path))

    def test_removal_non_default_path(self):
        """Remove android studio with non default path"""
        self.installed_path = "/tmp/foo"
        self.child = pexpect.spawnu(self.command('{} android android-studio {}'.format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("\[.*\] ")
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.installed_path))

        # now, remove it
        self.child = pexpect.spawnu(self.command('{} android android-studio --remove'.format(UMAKE)))
        self.wait_and_no_warn()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.installed_path))


class AndroidNDKTests(LargeFrameworkTests):
    """This will test the Android NDK installation"""

    TIMEOUT_INSTALL_PROGRESS = 120

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/android/android-ndk")

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "ndk-which")

    def test_default_android_ndk_install(self):
        """Install android ndk from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} android android-ndk'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.path_exists(self.exec_path))

        # launch it, send SIGTERM and check that it exits fine
        self.assertEqual(subprocess.check_call(self.command_as_list([self.exec_path, "gcc"]),
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL),
                         0)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} android android-ndk'.format(UMAKE)))
        self.expect_and_no_warn("Android NDK is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()
