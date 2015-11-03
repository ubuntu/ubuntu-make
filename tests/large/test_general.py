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

"""General frameworks tests"""

from . import LargeFrameworkTests
import subprocess
from ..tools import UMAKE


class GeneralTests(LargeFrameworkTests):
    """This will test the General frameworks functionality"""

    def test_run_category_without_default_framework(self):
        """Trying to run a category without a default framework exits in error"""
        exception_raised = False
        try:
            subprocess.check_output(self.command_as_list([UMAKE, 'ide']), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.assertIn("ERROR:", e.output.decode("utf-8"))
            exception_raised = True
        self.assertTrue(exception_raised)
