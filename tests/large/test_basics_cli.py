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

from contextlib import suppress
import os
import subprocess
from . import LargeFrameworkTests
from ..tools import UMAKE, get_root_dir


class BasicCLI(LargeFrameworkTests):
    """This will test the basic cli command class"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.log_cfg = None
        with suppress(KeyError):
            cls.log_cfg = os.environ.pop("LOG_CFG")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if (cls.log_cfg):
            os.environ["LOG_CFG"] = cls.log_cfg

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

    def test_setup_logging_level_with_env(self):
        """Set logging option to debug via env var"""
        env = {"LOG_CFG": os.path.join(get_root_dir(), "confs", "info.logcfg")}
        env.update(os.environ)
        commands = [UMAKE]
        if self.in_container:
            commands.insert(0, "LOG_CFG={}".format(env["LOG_CFG"]))
        result = subprocess.check_output(self.command_as_list(commands), env=env,
                                         stderr=subprocess.STDOUT)
        self.assertIn("Logging level set to INFO", result.decode("utf-8"))

    def test_version(self):
        """We display a version"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '--version']))
        self.assertNotEqual(result, "")

    def test_category_help(self):
        """We display a category help"""
        result = subprocess.check_output(self.command_as_list([UMAKE, 'ide', '--help']))
        self.assertNotEqual(result, "")

    def test_framework_help(self):
        """We display a framework help"""
        result = subprocess.check_output(self.command_as_list([UMAKE, 'ide', 'pycharm', '--help']))
        self.assertNotEqual(result, "")

    def test_help_position_matters(self):
        """The help option position matters"""
        result1 = subprocess.check_output(self.command_as_list([UMAKE, 'ide', 'pycharm', '--help']))
        result2 = subprocess.check_output(self.command_as_list([UMAKE, 'ide', '--help', 'pycharm']))
        result3 = subprocess.check_output(self.command_as_list([UMAKE, '--help', 'ide', 'pycharm']))
        self.assertNotEqual(result1, result2)
        self.assertNotEqual(result2, result3)
        self.assertNotEqual(result1, result3)

    def test_category_with_default_framework_help(self):
        """We display a help when there is a default framework"""
        result = subprocess.check_output(self.command_as_list([UMAKE, 'android', '--help']))
        self.assertNotEqual(result, "")

    def test_only_category_help_with_default_framework(self):
        """We display a category help which is different from the default framework one"""
        result1 = subprocess.check_output(self.command_as_list([UMAKE, 'android', '--help']))
        result2 = subprocess.check_output(self.command_as_list([UMAKE, 'android', 'android-studio', '--help']))
        self.assertNotEqual(result1, result2)

    def test_listing_all_frameworks(self):
        """We display all the frameworks"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '--list']))
        self.assertNotEqual(result, "")

        result = subprocess.check_output(self.command_as_list([UMAKE, '-l']))
        self.assertNotEqual(result, "")

    def test_listing_installed_frameworks(self):
        """We display just installed frameworks"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '--list-installed']))
        self.assertNotEqual(result, "")

    def test_listing_available_frameworks(self):
        """We display just available frameworks"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '--list-available']))
        self.assertNotEqual(result, "")

    def test_combine_listing_all_frameworks_and_available_frameworks(self):
        """Try to list all frameworks and available frameworks"""
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output(self.command_as_list([UMAKE, '--list', '--list-available']),
                                    stderr=subprocess.STDOUT)

    def test_combine_listing_all_frameworks_and_installed_frameworks(self):
        """Try to list all frameworks and installed frameworks"""
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output(self.command_as_list([UMAKE, '--list', '--list-installed']),
                                    stderr=subprocess.STDOUT)

    def test_combine_listing_available_frameworks_and_installed_frameworks(self):
        """Try to list available frameworks and installed frameworks"""
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output(self.command_as_list([UMAKE, '--list-available', '--list-installed']),
                                    stderr=subprocess.STDOUT)

    def test_listing_all_frameworks_and_check_categories_by_order(self):
        """List all frameworks and check if categories appear by order"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '--list']))

        previous_category = None
        for element in result.split(b"\n"):
            if element and not element.startswith(b"\t"):
                current_category = element[:element.find(b":")]
                # Skip the empty category since it' not in alphabetic order
                if previous_category and current_category is not b'':
                    self.assertTrue(previous_category < current_category)
                previous_category = current_category

    def test_listing_all_frameworks_and_check_frameworks_by_order(self):
        """List all frameworks and check if frameworks appear by order"""
        result = subprocess.check_output(self.command_as_list([UMAKE, '--list']))

        previous_framework = None
        for element in result.split(b"\n"):
            if element.startswith(b"\t"):
                current_framework = element[:element.find(b":")]
                if previous_framework:
                    self.assertTrue(previous_framework < current_framework)

                previous_framework = current_framework
            else:
                previous_framework = None
