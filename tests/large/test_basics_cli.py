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

"""Tests for the decompressor module"""

from contextlib import suppress
import os
import pexpect
import shutil
import signal
import subprocess
from udtc.tools import launcher_exists_and_is_pinned, get_launcher_path
from ..tools import LoggedTestCase
from time import sleep
from unittest import TestCase


class BasicCLI(LoggedTestCase):
    """This will test the basic cli command class"""

    def test_global_help(self):
        """We display a global help message"""
        result = subprocess.check_output(['./developer-tools-center', '--help'])
        self.assertNotEquals(result, "")

    def test_setup_info_logging(self):
        """We display a global help message"""
        result = subprocess.check_output(['./developer-tools-center', '-v', '--help'], stderr=subprocess.STDOUT)
        self.assertIn("INFO:", result.decode("utf-8"))

    def test_setup_debug_logging(self):
        """We display a global help message"""
        result = subprocess.check_output(['./developer-tools-center', '-vv', '--help'], stderr=subprocess.STDOUT)
        self.assertIn("DEBUG:", result.decode("utf-8"))


class AndroidStudio(TestCase):
    """This will test the Android Studio base"""

    TIMEOUT_INSTALL=300
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().__init__()
        self.installed_path = os.path.expanduser("~/tools/android/android-studio")
        self.exec_path = os.path.join(self.installed_path, "bin", "studio.sh")
        self.conf_path = os.path.expanduser("~/.config/udtc")

    def tearDown(self):
        with suppress(FileNotFoundError):
            shutil.rmtree(self.installed_path)
        with suppress(FileNotFoundError):
            os.remove(self.conf_path)
        with suppress(FileNotFoundError):
            os.remove(get_launcher_path("android-studio.desktop"))

    def pid_for(self, process_grep, wait_before=0):
        """Return pid matching the process_grep elements"""
        sleep(wait_before)
        for pid in os.listdir('/proc'):
            if not pid.isdigit():
                continue
            # ignore processes that are closed in between
            with suppress(IOError):
                cmdline = open(os.path.join('/proc', pid, 'cmdline'), 'r').read()
                for process_elem in process_grep:
                    if process_elem not in cmdline:
                        break
                # we found it
                else:
                    return int(pid)
        raise BaseException("The process that we can find with {} isn't started".format(process_grep))

    def assert_for_warn(self, content, expect_warn=False):
        """assert if there is any warn"""
        if not expect_warn:
            self.assertNotIn("WARNING", content)
            self.assertNotIn("ERROR", content)
        else:
            for warn_tag in ("WARNING", "ERROR"):
                if warn_tag in content:
                    break
            else:  # nothing found:
                raise BaseException("We didn't find an expected WARNING or ERROR in {}".format(content))

    def expect_and_no_warn(self, expect_query, timeout=-1, expect_warn=False):
        """run the expect query and check that there is no warning or error"""
        self.child.expect(expect_query, timeout=timeout)
        self.assert_for_warn(self.child.before, expect_warn)

    def wait_and_no_warn(self, expect_warn=False):
        """run wait and check that there is no warning or error"""
        self.expect_and_no_warn(pexpect.EOF, expect_warn=expect_warn)

    def test_default_android_studio_install(self):
        """Install android studio from scratch test case"""
        self.child = pexpect.spawnu('./developer-tools-center android android-studio')
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[.*\] ")
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher
        self.assertTrue(launcher_exists_and_is_pinned("android-studio.desktop"))
        self.assertTrue(os.path.exists(self.exec_path))

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.exec_path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        pid = self.pid_for(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        os.kill(pid, signal.SIGTERM)
        self.assertEquals(proc.wait(self.TIMEOUT_STOP), 0)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu('./developer-tools-center android android-studio')
        self.expect_and_no_warn("Android Studio is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()

    def test_no_license_accept_android_studio(self):
        """We don't accept the license (default)"""
        self.child = pexpect.spawnu('./developer-tools-center android android-studio')
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[.*\] ")
        self.child.sendline("")
        self.wait_and_no_warn()

        self.assertFalse(launcher_exists_and_is_pinned("android-studio.desktop"))
        self.assertFalse(os.path.exists(self.exec_path))

    def test_doesnt_accept_wrong_path(self):
        """We don't accept a wrong path"""
        self.child = pexpect.spawnu('./developer-tools-center android android-studio')
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127)*100)
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127)*100 + "/")
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path), expect_warn=True)
        self.child.sendcontrol('C')
        self.wait_and_no_warn()

        self.assertFalse(launcher_exists_and_is_pinned("android-studio.desktop"))
        self.assertFalse(os.path.exists(self.exec_path))

    def test_android_studio_reinstall(self):
        """Reinstall android studio once installed"""
        for loop in ("install", "reinstall"):
            self.child = pexpect.spawnu('./developer-tools-center android android-studio')
            if loop == "reinstall":
                self.expect_and_no_warn("Android Studio is already installed.*\[.*\] ")
                self.child.sendline("y")
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL)
            self.wait_and_no_warn()

            # we have an installed launcher, added to the launcher
            self.assertTrue(launcher_exists_and_is_pinned("android-studio.desktop"))
            self.assertTrue(os.path.exists(self.exec_path))

            # launch it, send SIGTERM and check that it exits fine
            proc = subprocess.Popen(self.exec_path, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            pid = self.pid_for(["java", self.installed_path], wait_before=self.TIMEOUT_START)
            os.kill(pid, signal.SIGTERM)
            self.assertEquals(proc.wait(self.TIMEOUT_STOP), 0)
