# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
#
# Authors:
#  Alexander Sidorenko
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

"""Tests for Devops category"""

from . import ContainerTests
import os
from ..large import test_devops
from ..tools import get_data_dir, UMAKE


class TerraformInContainer(ContainerTests, test_devops.TerraformTests):
    """This will test the Terraform integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["api.github.com", "releases.hashicorp.com"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "devops", "terraform")

    def test_install_with_changed_download_page(self):
        """Installing Terraform should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "api.github.com",
                                               "repos", "hashicorp", "terraform", "releases", "latest")
        self.command('{} devops terraform'.format(UMAKE))
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))
