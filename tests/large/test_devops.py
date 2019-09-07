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

"""Tests for the Devops category"""
import logging
import os
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE, spawn_process

logger = logging.getLogger(__name__)


class TerraformTests(LargeFrameworkTests):
    """Tests for Terraform"""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 20
    TIMEOUT_STOP = 20

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.join(self.install_base_path, "devops", "terraform")
        self.command_args = '{} devops terraform'.format(UMAKE)

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "terraform")

    def test_default_install(self):
        self.child = spawn_process(self.command(self.command_args))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_close()

        self.assert_exec_exists()

        # ensure that it's detected as installed:
        self.child = spawn_process(self.command(self.command_args))
        self.expect_and_no_warn("Terraform is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_close()
        self.assert_exec_exists()
