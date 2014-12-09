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

"""Tests for the cli module"""

import importlib
from ..tools import LoggedTestCase
from umake.ui.cli import mangle_args_for_default_framework
import os
import sys
from ..tools import get_data_dir, change_xdg_path, patchelem
import umake
from umake import frameworks


class TestCLIFromFrameworks(LoggedTestCase):
    """This will test the CLI module with loaded Frameworks"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        importlib.reload(umake.frameworks)

        change_xdg_path('XDG_CONFIG_HOME', os.path.join(get_data_dir(), 'configs', "foo"))

        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'testframeworks')

        with patchelem(umake.frameworks, '__file__', os.path.join(cls.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        # patch the BaseCategory dictionary from the umake.ui.cli one
        umake.ui.cli.BaseCategory = frameworks.BaseCategory

    @classmethod
    def tearDownClass(cls):
        change_xdg_path('XDG_CONFIG_HOME', remove=True)
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def test_mangle_args_none(self):
        """No option goes are preserved"""
        self.assertEquals(mangle_args_for_default_framework([]), [])

    def test_mangle_args_options_only(self):
        """Options only goes are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["--foo", "-b"]), ["--foo", "-b"])

    def test_mangle_args_unknown_category(self):
        """Unknown category are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["barframework", "-b"]), ["barframework", "-b"])

    def test_mangle_args_for_framework(self):
        """Well formatted framework command are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["category-a", "framework-a"]),
                          ["category-a", "framework-a"])

    def test_mangle_args_for_framework_none_default(self):
        """Well formatted none default framework command are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["category-a", "framework-b"]),
                          ["category-a", "framework-b"])

    def test_mangle_args_for_framework_with_framework_options(self):
        """Well formatted framework command with framework options are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["category-a", "framework-a", "--bar", "install_path",
                                                             "--foo"]),
                          ["category-a", "framework-a", "--bar", "install_path", "--foo"])

    def test_mangle_args_for_framework_global_options(self):
        """Well formatted framework with global options are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["category-a", "framework-a"]),
                          ["category-a", "framework-a"])

    def test_mangle_args_default_framework(self):
        """Choose default framework for the category"""
        self.assertEquals(mangle_args_for_default_framework(["category-a"]),
                          ["category-a", "framework-a"])

    def test_mangle_args_without_framework_with_framework_options(self):
        """Don't choose any framework for a category with default framework and framework options"""
        self.assertEquals(mangle_args_for_default_framework(["category-a", "install_path", "--foo"]),
                          ["category-a", "install_path", "--foo"])

    def test_mangle_args_for_framework_with_global_options(self):
        """Global options are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "--debug", "category-a", "framework-a"]),
                          ["-v", "--debug", "category-a", "framework-a"])

    def test_mangle_args_for_framework_with_global_and_framework_options(self):
        """Global options and framework options are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "category-a", "framework-a", "--bar",
                                                             "install", "--foo"]),
                          ["-v", "category-a", "framework-a", "--bar", "install", "--foo"])

    def test_mangle_args_for_default_framework_with_global_options(self):
        """Global options are preserved, completing with default framework"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "category-a"]),
                          ["-v", "category-a", "framework-a"])

    def test_mangle_args_for_default_framework_with_simple_options(self):
        """Global and framework simple options are preserved, completing with default framework with simple options"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "category-a", "--foo", "--bar"]),
                          ["-v", "category-a", "framework-a", "--foo", "--bar"])

    def test_mangle_args_with_global_framework_extended_options(self):
        """Global options and framework extended options are preserved, NOT completing with default framework"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "category-a", "--bar", "install_path", "--foo"]),
                          ["-v", "category-a", "--bar", "install_path", "--foo"])

    def test_mangle_args_with_global_framework_options_after_install(self):
        """Global and extended framework options are preserved after install_path, NOT completing with dft framework"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "category-a", "install_path", "--foo"]),
                          ["-v", "category-a", "install_path", "--foo"])

    def test_mangle_args_for_default_framework_after_install_with_sep(self):
        """Add the default framework if the install path has a sep"""
        self.assertEquals(mangle_args_for_default_framework(["category-a", "install/path"]),
                          ["category-a", "framework-a", "install/path"])

    def test_mangle_args_with_global_framework_options_after_install_with_sep(self):
        """Global and ext framework options are preserved after install_path with sep, completing with dft framework"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "category-a", "install/path", "--foo"]),
                          ["-v", "category-a", "framework-a", "install/path", "--foo"])

    def test_mangle_args_with_global_framework_options_between_install_with_sep(self):
        """Global and ext framework options are preserved before install_path with sep, completing with dft framework"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "category-a", "--bar", "install/path", "--foo"]),
                          ["-v", "category-a", "framework-a", "--bar", "install/path", "--foo"])

    def test_mangle_args_for_framework_in_main_category(self):
        """framework in main category is preserved"""
        self.assertEquals(mangle_args_for_default_framework(["framework-free-a"]), ["framework-free-a"])

    def test_mangle_args_for_framework_in_main_category_with_framework_options(self):
        """framework in main category with framework simple options are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["framework-free-a", "--foo"]),
                          ["framework-free-a", "--foo"])

    def test_mangle_args_for_framework_in_main_category_with_framework_extended_options(self):
        """framework in main category with framework extended options are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["framework-free-a", "--foo", "install_path"]),
                          ["framework-free-a", "--foo", "install_path"])

    def test_mangle_args_for_framework_in_main_category_with_global_and_framework_extended_options(self):
        """framework in main category with framework global and extended options are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "framework-free-a", "--foo", "install_path"]),
                          ["-v", "framework-free-a", "--foo", "install_path"])

    def test_mangle_args_for_framework_in_main_category_with_global_and_framework_extended_options_and_path(self):
        """framework in main category with framework global and extended options are preserved and path"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "framework-free-a", "--foo", "install/path"]),
                          ["-v", "framework-free-a", "--foo", "install/path"])

    def test_mangle_args_for_category_without_default_framework(self):
        """No framework in a category without default are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["category-f"]), ["category-f"])

    def test_mangle_args_for_category_without_default_framework_with_extended_options(self):
        """No framework in a category with ext. option without default are preserved"""
        self.assertEquals(mangle_args_for_default_framework(["category-f", "--foo", "install_path"]),
                          ["category-f", "--foo", "install_path"])

    def test_mangle_args_for_category_without_default_framework_with_install_path(self):
        """No framework in a category without default are preserved with install path"""
        self.assertEquals(mangle_args_for_default_framework(["category-f", "--foo", "install/path"]),
                          ["category-f", "--foo", "install/path"])

    def test_mangle_args_for_category_without_default_framework_with_global_and_extended_options(self):
        """No framework in a category without default are preserved with global and ext options"""
        self.assertEquals(mangle_args_for_default_framework(["-v", "category-f", "--foo", "install_path"]),
                          ["-v", "category-f", "--foo", "install_path"])
