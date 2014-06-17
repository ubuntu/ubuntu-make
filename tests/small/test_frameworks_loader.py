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

"""Tests the framework loader"""

import os
import sys
from ..tools import get_data_dir, patchelem
from unittest import TestCase
import udtc
from udtc import frameworks
from udtc.tools import NoneDict


class TestFrameworkLoader(TestCase):
    """This will test the dynamic framework loader activity"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'testframeworks')
        cls.CategoryHandler = frameworks.BaseCategory

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        sys.path.remove(get_data_dir())

    def setUp(self):
        # load custom framework directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["Category A"]

    def tearDown(self):
        # we reset the loaded categories
        frameworks.BaseCategory.categories = NoneDict()

    def test_load_main_category(self):
        """The main category is loaded"""
        self.assertEquals(len([1 for category in self.CategoryHandler.categories.values()
                               if category.main_category]), 1)

    def test_get_main_category(self):
        """get_main_category functions returns main category"""
        main_category = [category for category in self.CategoryHandler.categories.values() if category.main_category][0]
        self.assertEquals(self.CategoryHandler.get_main_category(), main_category)

    def test_get_main_category_with_none(self):
        """get_main_category functions returns None when there is no main category"""
        frameworks.BaseCategory.categories = NoneDict()
        self.assertIsNone(self.CategoryHandler.get_main_category())

    def test_load_category(self):
        """There is at least one category (not main) loaded"""
        self.assertTrue(len([1 for category in self.CategoryHandler.categories.values()
                             if not category.main_category]) > 0)

    def test_get_category_by_name(self):
        """categories index returns matching category"""
        name = "Category A"
        category = self.CategoryHandler.categories[name]
        self.assertEquals(category.name, name)

    def test_get_category_not_existing(self):
        """the call to get category returns None when there is no match"""
        self.assertIsNone(self.CategoryHandler.categories["foo"])

    def test_get_category_prog_name(self):
        """prog_name for category is what we expect"""
        self.assertEquals(self.categoryA.prog_name, "category-a")
        self.assertEquals(self.CategoryHandler.categories["Category/B"].prog_name, "category-b")

    def test_multiple_files_loaded(self):
        """We load multiple categories in different files"""
        # main category, + at least 2 other categories
        self.assertTrue(len(self.CategoryHandler.categories) > 2)
        self.assertIsNotNone(self.categoryA)
        self.assertIsNotNone(self.CategoryHandler.categories["Category/B"])

    def test_frameworks_loaded(self):
        """We have frameworks attached to a category"""
        self.assertTrue(len(self.categoryA.frameworks) > 1)
        self.assertTrue(self.categoryA.frameworks["Framework A"].name, "Framework A")
        self.assertTrue(self.categoryA.has_frameworks())

    def test_framework_not_existing(self):
        """the call  to get a framework returns None when there is no match"""
        self.assertIsNone(self.categoryA.frameworks["foo"])

    def test_frameworks_doesn_t_mix(self):
        """Frameworks, even with the same name, don't mix between categories"""
        self.assertNotEquals(self.categoryA.frameworks["Framework A"],
                             self.CategoryHandler.categories["Category/B"].frameworks["Framework A"])

    def test_has_more_than_one_framework(self):
        """more than one frameworks in a category is correctly reported"""
        self.assertFalse(self.categoryA.has_one_framework())

    def test_empty_category_loaded(self):
        """We still load an empty category"""
        self.assertIsNotNone(self.CategoryHandler.categories["Empty category"])

    def test_has_frameworks_on_empty_category(self):
        """has_frameworks return False on empty category"""
        self.assertFalse(self.CategoryHandler.categories["Empty category"].has_frameworks())
        self.assertFalse(self.CategoryHandler.categories["Empty category"].has_one_framework())

    def test_one_framework_category(self):
        """A category with one framework is reported as so"""
        self.assertTrue(self.CategoryHandler.categories["One framework category"].has_one_framework())

    def test_framework_prog_name(self):
        """prog_name for framework is what we expect"""
        self.assertEquals(self.categoryA.frameworks["Framework A"].prog_name, "framework-a")
        self.assertEquals(self.categoryA.frameworks["Framework/B"].prog_name, "framework-b")

    def test_nothing_installed(self):
        """Category returns that no framework is installed"""
        self.assertEquals(self.categoryA.is_installed(), self.CategoryHandler.NOT_INSTALLED)

    def test_category_fully_installed(self):
        """Category returns than all frameworks are installed"""
        self.assertEquals(self.CategoryHandler.categories["Category/B"].is_installed(),
                          self.CategoryHandler.FULLY_INSTALLED)

    def test_category_half_installed(self):
        """Category returns than half frameworks are installed"""
        self.assertEquals(self.CategoryHandler.categories["Category/C"].is_installed(),
                          self.CategoryHandler.PARTIALLY_INSTALLED)


class TestEmptyFrameworkLoader(TestCase):
    """This will test the dynamic framework loader activity with an empty set of frameworks"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'testframeworksdoesntexist')
        cls.CategoryHandler = frameworks.BaseCategory

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        sys.path.remove(get_data_dir())

    def setUp(self):
        # load custom unexisting framework directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworksdoesntexist"):
            frameworks.load_frameworks()

    def test_invalid_framework(self):
        """There is one main category, but nothing else"""
        main_category = [category for category in self.CategoryHandler.categories.values() if category.main_category][0]
        self.assertEquals(self.CategoryHandler.get_main_category(), main_category)
        self.assertEquals(len(self.CategoryHandler.categories), 1)

# TODO: test load file without the abstract interface filed up
# TODO: test load framework in main category
# TODO: add another class to just try loading real production directories
