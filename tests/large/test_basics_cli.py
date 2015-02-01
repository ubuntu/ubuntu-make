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
from ..tools import LoggedTestCase, UMAKE


class BasicCLI(LoggedTestCase):
    """This will test the basic cli command class"""

    def command_as_list(self, commands_input):
        """passthrough, return args"""
        return commands_input

    def return_without_first_output(self, stdout):
        """We return ignoring the first line which is INFO: set logging level to"""
        return "\n".join(stdout.split('\n')[1:])

    def test_global_help(self):
        """We display a global help message"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '--help']))
        self.assertNotEqual(result, "")

    def test_setup_info_logging(self):
        """We display info logs"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '-v', '--help']),
                                         stderr=subprocess.STDOUT)
        self.assertIn("INFO:", self.return_without_first_output(result.decode("utf-8")))

    def test_setup_debug_logging(self):
        """We display debug logs"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '-vv', '--help']),
                                         stderr=subprocess.STDOUT)
        self.assertIn("DEBUG:", self.return_without_first_output(result.decode("utf-8")))

    def test_setup_with_option_logging(self):
        """We don't mix info or debug logs with a -v<something> option"""
        exception_raised = False
        try:
            subprocess.check_output(self.command_as_list([UMAKE, '-vouep', '--help']),
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            self.assertNotIn("INFO:", self.return_without_first_output(e.output.decode("utf-8")))
            self.assertNotIn("DEBUG:", self.return_without_first_output(e.output.decode("utf-8")))
            exception_raised = True
        self.assertTrue(exception_raised)
