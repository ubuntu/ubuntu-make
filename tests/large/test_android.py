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
import subprocess
from ..tools import UMAKE, spawn_process


class AndroidStudioTests(LargeFrameworkTests):
    """This will test the Android Studio base"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "android", "android-studio")
        self.desktop_filename = "android-studio.desktop"

    def test_default_android_studio_install(self):
        """Install android studio from scratch test case"""
        self.child = spawn_process(self.command('{} android android-studio'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"\[I Accept.*\]")  # ensure we have a license question
        self.child.sendline("a")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assert_exec_link_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.communicate()
        self.assertEqual(proc.wait(self.TIMEOUT_STOP), 143)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} android android-studio'.format(UMAKE)))
        self.expect_and_no_warn(r"Android Studio is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class AndroidSDKTests(LargeFrameworkTests):
    """This will test the Android SDK installation"""

    TIMEOUT_INSTALL_PROGRESS = 120

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "android", "android-sdk")

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "tools", "bin", "sdkmanager")

    def test_default_android_sdk_install(self):
        """Install android sdk from scratch test case"""
        self.child = spawn_process(self.command('{} android android-sdk'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"\[I Accept.*\]")  # ensure we have a license question
        self.child.sendline("a")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed sdk exec
        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))

        # launch it, send SIGTERM and check that it exits fine
        self.assertEqual(subprocess.check_call(self.command_as_list([self.exec_path, "--list"]),
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL),
                         0)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} android android-sdk'.format(UMAKE)))
        self.expect_and_no_warn(r"Android SDK is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class AndroidPlatformToolsTests(LargeFrameworkTests):
    """This will test the Android Platform Tools installation"""

    TIMEOUT_INSTALL_PROGRESS = 120

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "android", "android-platform-tools")

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "platform-tools", "adb")

    def test_default_android_platform_tools_install(self):
        """Install android sdk from scratch test case"""
        self.child = spawn_process(self.command('{} android android-platform-tools'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"\[I Accept.*\]")  # ensure we have a license question
        self.child.sendline("a")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed sdk exec
        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))

        # launch it, send SIGTERM and check that it exits fine
        self.assertEqual(subprocess.check_call(self.command_as_list([self.exec_path, "devices"]),
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL),
                         0)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} android android-platform-tools'.format(UMAKE)))
        self.expect_and_no_warn(r"Android Platform Tools is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class AndroidNDKTests(LargeFrameworkTests):
    """This will test the Android NDK installation"""

    TIMEOUT_INSTALL_PROGRESS = 120

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "android", "android-ndk")

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "ndk-build")

    def test_default_android_ndk_install(self):
        """Install android ndk from scratch test case"""
        self.child = spawn_process(self.command('{} android android-ndk'.format(UMAKE)))
        self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn(r"\[I Accept.*\]")  # ensure we have a license question
        self.child.sendline("a")
        self.expect_and_no_warn(r"Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed ndk exec
        self.assert_exec_exists()
        self.assertTrue(self.is_in_path(self.exec_path))

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} android android-ndk'.format(UMAKE)))
        self.expect_and_no_warn(r"Android NDK is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()
