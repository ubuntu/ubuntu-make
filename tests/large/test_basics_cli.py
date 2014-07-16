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

"""Tests for basic CLI commands"""

import subprocess
from ..tools import LoggedTestCase


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
