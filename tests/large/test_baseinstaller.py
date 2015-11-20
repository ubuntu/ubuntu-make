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
import pexpect
import platform
import shutil
import subprocess
import tempfile

from ..tools import UMAKE, spawn_process, get_data_dir, swap_file_and_restore
from ..tools.local_server import LocalHttp


class BaseInstallerTests(LargeFrameworkTests):
    """This will test the base installer framework via a fake one"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 1
    TIMEOUT_STOP = 1

    server = None
    TEST_URL_FAKE_DATA = "http://localhost:8765/base-framework-fake64.tgz"
    TEST_CHECKSUM_FAKE_DATA = "4a582c6e35700f00332783b0b83783f73499aa60"
    JAVAEXEC = "java-fake64"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.proxy_env = {"http_proxy": None, "https_proxy": None}
        for key in cls.proxy_env:
            cls.proxy_env[key] = os.environ.pop(key, None)
        cls.download_page_file_path = os.path.join(get_data_dir(), "server-content", "localhost", "index.html")
        if not cls.in_container:
            server_dir = os.path.join(get_data_dir(), "server-content", "localhost")
            cls.server = LocalHttp(server_dir, port=8765)
            framework_dir = os.path.expanduser(os.path.join('~', '.umake', 'frameworks'))
            cls.testframework = (os.path.join(framework_dir, 'baseinstallerfake.py'))
            os.makedirs(framework_dir, exist_ok=True)
            shutil.copy(os.path.join(get_data_dir(), "testframeworks", "baseinstallerfake.py"), cls.testframework)
        if platform.machine() != "x86_64":
            cls.TEST_URL_FAKE_DATA = "http://localhost:8765/base-framework-fake32.tgz"
            cls.TEST_CHECKSUM_FAKE_DATA = "4f64664ebe496cc6d54f417f25a1707f156d74d2"
            cls.JAVAEXEC = "java-fake32"

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for key, value in cls.proxy_env.items():
            if value:
                os.environ[key] = value
        if not cls.in_container:
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

    def test_no_license_accept(self):
        """We don't accept the license (default)"""
        self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
        self.accept_default_and_wait()
        self.close_and_check_status()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_doesnt_accept_wrong_path(self):
        """We don't accept a wrong path"""
        self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127) * 100)
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline(chr(127) * 100 + "/")
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path), expect_warn=True)
        self.child.sendcontrol('C')
        self.wait_and_no_warn()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_reinstall(self):
        """Reinstall once installed"""
        for loop in ("install", "reinstall"):
            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            if loop == "reinstall":
                # we only have one question, not the one about existing dir.
                self.expect_and_no_warn("Base Framework is already installed.*\[.*\] ")
                self.child.sendline("y")
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_close()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assert_exec_exists()

            # launch it, send SIGTERM and check that it exits fine
            proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            self.check_and_kill_process([self.JAVAEXEC, self.installed_path], wait_before=self.TIMEOUT_START)

    def test_reinstall_other_path(self):
        """Reinstall Base Framework on another path once installed should remove the first version"""
        original_install_path = self.installed_path
        for loop in ("install", "reinstall"):
            if loop == "reinstall":
                self.installed_path = "/tmp/foo"
                self.child = spawn_process(self.command('{} base base-framework {}'.format(UMAKE,
                                                                                           self.installed_path)))
                self.expect_and_no_warn("Base Framework is already installed.*\[.*\] ")
                self.child.sendline("y")
            else:
                self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
                self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_close()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assert_exec_exists()

        # ensure that version first isn't installed anymore
        self.assertFalse(self.path_exists(original_install_path))

    def test_reinstall_other_non_empty_path(self):
        """Reinstall Base Framework on another path (non empty) once installed should remove the first version"""
        original_install_path = self.installed_path
        if not self.in_container:
            self.reinstalled_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.reinstalled_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.create_file(os.path.join(self.reinstalled_path, "bar"), "foo")
        for loop in ("install", "reinstall"):
            if loop == "reinstall":
                self.installed_path = self.reinstalled_path
                self.child = spawn_process(self.command('{} base base-framework {}'.format(UMAKE,
                                                                                           self.installed_path)))
                self.expect_and_no_warn("Base Framework is already installed.*\[.*\] ")
                self.child.sendline("y")
                self.expect_and_no_warn("{} isn't an empty directory.*there\? \[.*\] ".format(self.installed_path))
                self.child.sendline("y")
            else:
                self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
                self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_close()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assert_exec_exists()

        # ensure that version first isn't installed anymore
        self.assertFalse(self.path_exists(original_install_path))

    def test_reinstall_previous_install_removed(self):
        """Detect that removing Base Framework content, but still having a launcher, doesn't trigger a
           reinstall question"""
        for loop in ("install", "reinstall"):
            if loop == "reinstall":
                # remove code (but not laucher)
                self.remove_path(self.installed_path)

            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_close()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assert_exec_exists()

    def test_reinstall_previous_launcher_removed(self):
        """Detect that removing Base Framework launcher, but still having the code, doesn't trigger a
           reinstall question. However, we do have a dir isn't empty one."""
        for loop in ("install", "reinstall"):
            if loop == "reinstall":
                # remove launcher, but not code
                self.remove_path(self.get_launcher_path(self.desktop_filename))

            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            if loop == "reinstall":
                self.expect_and_no_warn("{} isn't an empty directory.*there\? \[.*\] ".format(self.installed_path))
                self.child.sendline("y")
            self.expect_and_no_warn("\[.*\] ")
            self.child.sendline("a")
            self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
            self.wait_and_close()

            # we have an installed launcher, added to the launcher
            self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assert_exec_exists()

    def test_xdg_data_install_path(self):
        """Install in path specified by XDG_DATA_HOME"""
        xdg_data_path = "/tmp/foo"
        self.installed_path = "{}/umake/base/base-framework".format(xdg_data_path)
        cmd = "XDG_DATA_HOME={} {} base base-framework".format(xdg_data_path, UMAKE)
        if not self.in_container:
            cmd = 'bash -c "{}"'.format(cmd)

        self.child = spawn_process(self.command(cmd))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[I Accept.*\]")
        self.accept_default_and_wait()
        self.close_and_check_status()
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_custom_install_path(self):
        """We install Base Framework in a custom path"""
        # We skip the existing directory prompt
        self.installed_path = "/tmp/foo"
        self.child = spawn_process(self.command('{} base base-framework {}'.format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
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

    def test_start_install_on_empty_dir(self):
        """We try to install on an existing empty dir"""
        if not self.in_container:
            self.installed_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.installed_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.child = spawn_process(self.command('{} base base-framework {}'.format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()
        self.close_and_check_status()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_start_install_on_existing_dir_refuse(self):
        """We prompt if we try to install on an existing directory which isn't empty. Refusing doesn't install"""
        if not self.in_container:
            self.installed_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.installed_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.create_file(os.path.join(self.installed_path, "bar"), "foo")
        self.child = spawn_process(self.command('{} base base-framework {}'.format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("{} isn't an empty directory.*there\? \[.*\] ".format(self.installed_path))
        self.accept_default_and_wait()
        self.close_and_check_status()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_start_install_on_existing_dir_accept(self):
        """We prompt if we try to install on an existing directory which isn't empty. Accepting install"""
        if not self.in_container:
            self.installed_path = tempfile.mkdtemp()
        else:  # we still give a path for the container
            self.installed_path = os.path.join(tempfile.gettempdir(), "tmptests")
        self.create_file(os.path.join(self.installed_path, "bar"), "foo")
        self.child = spawn_process(self.command('{} base base-framework {}'.format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("{} isn't an empty directory.*there\? \[.*\] ".format(self.installed_path))
        self.child.sendline("y")
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

    def test_is_default_framework(self):
        """Base Framework is chosen as the default framework"""
        self.child = spawn_process(self.command('{} base'.format(UMAKE)))
        # we ensure it thanks to installed_path being the base framework one
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendcontrol('C')
        self.wait_and_no_warn()

    def test_is_default_framework_with_options(self):
        """Base Framework options are sucked in as the default framework"""
        self.child = spawn_process(self.command('{} base /tmp/foo'.format(UMAKE)))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
        self.accept_default_and_wait()
        self.close_and_check_status()

    def test_not_default_framework_with_path_without_path_separator(self):
        """Base Framework isn't selected for default framework with path without separator"""
        self.child = spawn_process(self.command('{} base foo'.format(UMAKE)))
        self.expect_and_no_warn("error: argument framework: invalid choice")
        self.accept_default_and_wait()
        self.close_and_check_status(exit_status=2)

    def test_is_default_framework_with_user_path(self):
        """Base Framework isn't selected for default framework with path without separator"""
        self.installed_path = "/tmp/foo"
        self.child = spawn_process(self.command('{} base {}'.format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license as the first question
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

    def test_removal(self):
        """Remove Base Framework with default path"""
        self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[.*\] ")
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.installed_path))

        # now, remove it
        self.child = spawn_process(self.command('{} base base-framework --remove'.format(UMAKE)))
        self.wait_and_close()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.installed_path))

    def test_removal_non_default_path(self):
        """Remove Base Framework with non default path"""
        self.installed_path = "/tmp/foo"
        self.child = spawn_process(self.command('{} base base-framework {}'.format(UMAKE, self.installed_path)))
        self.expect_and_no_warn("\[.*\] ")
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.installed_path))

        # now, remove it
        self.child = spawn_process(self.command('{} base base-framework --remove'.format(UMAKE)))
        self.wait_and_close()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.installed_path))

    def test_removal_global_option(self):
        """Remove Base Framework via global option (before category) should delete it"""
        self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("\[.*\] ")
        self.child.sendline("a")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertTrue(self.path_exists(self.installed_path))

        # now, remove it
        self.child = spawn_process(self.command('{} --remove base base-framework'.format(UMAKE)))
        self.wait_and_close()

        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.path_exists(self.installed_path))

    def test_automated_install(self):
        """Install Base Framework automatically with no interactive options"""
        self.child = spawn_process(self.command('{} base base-framework {} --accept-license'.format(UMAKE,
                                                self.installed_path)))
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()

    def test_try_removing_uninstalled_framework(self):
        """Trying to remove an uninstalled framework will fail"""
        self.child = spawn_process(self.command('{} base base-framework --remove'.format(UMAKE)))
        self.wait_and_close(expect_warn=True, exit_status=1)

    # additional test with fake md5sum
    def test_install_with_wrong_md5sum(self):
        """Install requires a md5sum, and a wrong one is rejected"""
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace(self.TEST_CHECKSUM_FAKE_DATA,
                                              "c8362a0c2ffc07b1b19c4b9001c8532de5a4b8c3"))
            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
            self.child.sendline("a")
            self.expect_and_no_warn([pexpect.EOF, "Corrupted download? Aborting."],
                                    timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
            self.wait_and_close(exit_status=1)

            # we have nothing installed
            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_install_with_no_license_in_download_page(self):
        """Installing should fail if not even license i dowload page"""
        umake_command = self.command("{} base base-framework".format(UMAKE))
        self.bad_download_page_test(umake_command, self.download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_install_with_no_download_links(self):
        """Installing should fail if no valid download links are found"""
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace('id="linux-bundle', ""))
            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn([pexpect.EOF], timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
            self.wait_and_close(exit_status=1)

            # we have nothing installed
            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_install_with_404(self):
        """Installing should fail with a 404 download asset reported correctly"""
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace(self.TEST_URL_FAKE_DATA,
                                              "https://localhost:8765/android-studio-unexisting.tgz"))
            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("\[I Accept.*\]")  # ensure we have a license question
            self.child.sendline("a")
            self.expect_and_no_warn([pexpect.EOF, "ERROR: 404 Client Error: File not found"],
                                    timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
            self.wait_and_close(exit_status=1)

            # we have nothing installed
            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_download_page_404(self):
        """Download page changed address or is just 404 should be reported correctly"""
        with swap_file_and_restore(self.download_page_file_path):
            os.remove(self.download_page_file_path)
            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn([pexpect.EOF, "ERROR: 404 Client Error: File not found"],
                                    timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
            self.wait_and_close(exit_status=1)

            # we have nothing installed
            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
