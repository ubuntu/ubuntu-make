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

"""Tests for base installer framework in container"""

from . import ContainerTests
import os
import subprocess
from ..large import test_baseinstaller
from ..tools import UMAKE, spawn_process, get_data_dir, swap_file_and_restore


class BaseInstallerInContainer(ContainerTests, test_baseinstaller.BaseInstallerTests):
    """This will install the Base Framework inside a container"""

    TIMEOUT_START = 10
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {8765: ["localhost"], 443: ["github.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        self.additional_local_frameworks = [os.path.join("tests", "data", "testframeworks", "baseinstallerfake.py")]
        self.umake_download_page = os.path.join(get_data_dir(), "server-content", "github.com",
                                                "ubuntu", "ubuntu-make", "releases")
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "base", "base-framework")

    def test_install_wrong_download_link_update(self):
        """Install wrong download link, update available"""
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace('id="linux-bundle', ""))
            # umake download page can't match any version (LATESTRELEASE)
            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn(r"To get the latest version",
                                    timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
            self.wait_and_close(exit_status=1)

            # we have nothing installed
            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_install_wrong_download_link_no_update(self):
        """Install wrong download link, no update available"""
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace('id="linux-bundle', ""))
            with swap_file_and_restore(self.umake_download_page) as content:
                with open(self.umake_download_page, "w") as newfile:
                    # Note: our version will have +unknown, testing the git/snap case
                    version = subprocess.check_output(self.command_as_list([UMAKE, '--version']),
                                                      stderr=subprocess.STDOUT).decode("utf-8")
                    newfile.write(content.replace('LATESTRELEASE', version.strip().split("+")[0]))
                self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
                self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
                self.wait_and_close(exit_status=1, expect_warn=True)
                self.assertIn("Download page changed its syntax or is not parsable (url missing)",
                              self.child.before)
                self.assertNotIn("To get the latest version", self.child.before)

                # we have nothing installed
                self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_install_wrong_download_link_404_update(self):
        """Install wrong download link, github giving 404"""
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace('id="linux-bundle', ""))
            with swap_file_and_restore(self.umake_download_page):
                os.remove(self.umake_download_page)

                self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
                self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
                self.wait_and_close(exit_status=1, expect_warn=True)
                self.assertIn("\r\nERROR: 404 Client Error:", self.child.before)

                # we have nothing installed
                self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_install_wrong_download_link_github_missing(self):
        # TODO: cut all network connection on the container to enable that test
        return
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace('id="linux-bundle', ""))
            self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
            self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn(r"\r\nERROR: Connection Error\r\n",
                                    timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
            self.wait_and_close(exit_status=1)

            # we have nothing installed
            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
