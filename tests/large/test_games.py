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
import platform
import subprocess
from ..tools import UMAKE, spawn_process


class StencylTests(LargeFrameworkTests):
    """This will test the Stencyl installation"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "games", "stencyl")
        self.desktop_filename = "stencyl.desktop"

    def test_default_stencyl_install(self):
        """Install stencyl from scratch test case"""
        self.child = spawn_process(self.command('{} games stencyl'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assert_exec_link_exists()

        # launch it, send SIGTERM and check that it exits fine
        use_cwd = self.installed_path
        if self.in_container:
            use_cwd = None
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, cwd=use_cwd)
        self.check_and_kill_process([self.exec_path], wait_before=self.TIMEOUT_START)
        proc.communicate()
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} games stencyl'.format(UMAKE)))
        self.expect_and_no_warn("Stencyl is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class BlenderTests(LargeFrameworkTests):
    """This will test the Blender installation"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "games", "blender")
        self.desktop_filename = "blender.desktop"

    def test_default_blender_install(self):
        """Install blender from scratch test case"""
        self.child = spawn_process(self.command('{} games blender'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assert_exec_link_exists()

        # launch it, send SIGTERM and check that it exits fine
        use_cwd = self.installed_path
        if self.in_container:
            use_cwd = None
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, cwd=use_cwd)
        self.check_and_kill_process([self.exec_path], wait_before=self.TIMEOUT_START)
        proc.communicate()
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} games blender'.format(UMAKE)))
        self.expect_and_no_warn("Blender is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class Unity3DTests(LargeFrameworkTests):
    """This will test the Unity 3D editor installation"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "games", "unity3d")
        self.desktop_filename = "unity3d-editor.desktop"

    def test_default_unity3D_install(self):
        """Install unity3D editor from scratch test case"""

        # only an amd64 test
        if platform.machine() != "x86_64":
            return

        self.child = spawn_process(self.command('{} games unity3d'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assert_exec_link_exists()

        # ensure setuid
        self.assertEqual(self.get_file_perms(os.path.join(self.installed_path, "chrome-sandbox")),
                         '-rwsr-xr-x')

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.check_and_kill_process([self.exec_path], wait_before=self.TIMEOUT_START)
        proc.communicate()
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} games unity3d'.format(UMAKE)))
        self.expect_and_no_warn("Unity3d is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class TwineTests(LargeFrameworkTests):
    """This will test the Twine installation"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "games", "twine")
        self.desktop_filename = "twine.desktop"

    def test_default_twine_install(self):
        """Install twine editor from scratch test case"""

        self.child = spawn_process(self.command('{} games twine'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assert_exec_link_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.check_and_kill_process([self.exec_path], wait_before=self.TIMEOUT_START)
        proc.communicate()
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command('{} games twine'.format(UMAKE)))
        self.expect_and_no_warn("Twine is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class SuperpowersTests(LargeFrameworkTests):
    """This will test the Superpowers installation"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "games", "superpowers")
        self.desktop_filename = "superpowers.desktop"
        self.command_args = '{} games superpowers'.format(UMAKE)

    def test_default_superpowers_install(self):
        """Install Superpowers editor from scratch test case"""

        self.child = spawn_process(self.command(self.command_args))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assert_exec_link_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.check_and_kill_process([self.exec_path], wait_before=self.TIMEOUT_START)
        proc.communicate()
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command(self.command_args))
        self.expect_and_no_warn("Superpowers is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class GDevelopTests(LargeFrameworkTests):
    """This will test the GDevelop installation"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "games", "gdevelop")
        self.desktop_filename = "gdevelop.desktop"
        self.command_args = '{} games gdevelop'.format(UMAKE)

    def test_default_gdevelop_install(self):
        """Install GDevelop editor from scratch test case"""

        self.child = spawn_process(self.command(self.command_args))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assert_exec_link_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.check_and_kill_process([self.exec_path], wait_before=self.TIMEOUT_START)
        proc.communicate()
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command(self.command_args))
        self.expect_and_no_warn("GDevelop is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()


class GodotTests(LargeFrameworkTests):
    """This will test the Godot installation"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "games", "godot")
        self.desktop_filename = "godot.desktop"
        self.command_args = '{} games godot'.format(UMAKE)

    def test_default_godot_install(self):
        """Install Godot editor from scratch test case"""

        self.child = spawn_process(self.command(self.command_args))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        # we have an installed launcher, added to the launcher
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assert_exec_link_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        self.check_and_kill_process([self.exec_path], wait_before=self.TIMEOUT_START)
        proc.communicate()
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command(self.command_args))
        self.expect_and_no_warn("Godot is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()
