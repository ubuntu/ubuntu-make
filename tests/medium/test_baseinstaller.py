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
import pexpect
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
        self.umake_download_page = os.path.join(get_data_dir(), "server-content", "github.com", "ubuntu", "ubuntu-make", "releases", "index.html")
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "base", "base-framework")

    def test_install_no_download_link_update(self):
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace('id="linux-bundle', ""))
            with swap_file_and_restore(self.umake_download_page) as content:
                with open(self.umake_download_page, "w") as newfile:
                    newfile.write(content.replace('16.11.1', "LATESTVERSION"))
                self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
                self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
                self.expect_and_no_warn("To get the latest version you can read the instructions at https://github.com/ubuntu/ubuntu-make\r\n\r\n",
                                        timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
                self.wait_and_close(exit_status=1)

                # we have nothing installed
                self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))

    def test_install_no_download_link_no_update(self):
        with swap_file_and_restore(self.download_page_file_path) as content:
            with open(self.download_page_file_path, "w") as newfile:
                newfile.write(content.replace('id="linux-bundle', ""))
            with swap_file_and_restore(self.umake_download_page) as content:
                with open(self.umake_download_page, "w") as newfile:
                    version = pexpect.run(self.command('{} --version'.format(UMAKE)))
                    newfile.write(content.replace('16.11.1', version.decode().rstrip()))
                self.child = spawn_process(self.command('{} base base-framework'.format(UMAKE)))
                self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
                self.child.sendline("")
                self.expect_and_no_warn([pexpect.EOF, "\r\nERROR: Download page changed its syntax or is not parsable (url missing)\r\n"],
                                        timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
                self.wait_and_close(exit_status=1)
                self.assertNotIn('To get the latest version you can read the instructions at https://github.com/ubuntu/ubuntu-make\r\n\r\n', self.child.before)

                # we have nothing installed
                self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
