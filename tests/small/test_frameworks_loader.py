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

from contextlib import suppress
import importlib
import os
import sys
import tempfile
from ..tools import get_data_dir, change_xdg_config_path, patchelem, LoggedTestCase, ConfigHandler
import udtc
from udtc import frameworks
from udtc.tools import NoneDict
from unittest.mock import Mock


class BaseFrameworkLoader(LoggedTestCase):
    """Unload and reload the module to ensure we clean all class dict"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        importlib.reload(frameworks)
        cls.CategoryHandler = frameworks.BaseCategory

    def setUp(self):
        """Ensure we don't have any config file loaded"""
        super().setUp()
        change_xdg_config_path(self.config_dir_for_name("foo"))

    def tearDown(self):
        with suppress(KeyError):
            os.environ.pop('XDG_CONFIG_HOME')
        super().tearDown()

    def config_dir_for_name(self, name):
        """Return the config dir for this name"""
        return os.path.join(get_data_dir(), 'configs', name)

    def fake_arch_version(self, arch, version):
        """Help to mock the current arch and version on further calls"""
        self._saved_current_arch_fn = udtc.frameworks.get_current_arch
        self.get_current_arch_mock = Mock()
        self.get_current_arch_mock.return_value = arch
        udtc.frameworks.get_current_arch = self.get_current_arch_mock

        self._saved_current_ubuntu_version_fn = udtc.frameworks.get_current_ubuntu_version
        self.get_current_ubuntu_version_mock = Mock()
        self.get_current_ubuntu_version_mock.return_value = version
        udtc.frameworks.get_current_ubuntu_version = self.get_current_ubuntu_version_mock

    def restore_arch_version(self):
        """Restore initial current arch and version"""
        udtc.frameworks.get_current_arch = self._saved_current_arch_fn
        udtc.frameworks.get_current_ubuntu_version = self._saved_current_ubuntu_version_fn


class TestFrameworkLoader(BaseFrameworkLoader):
    """This will test the dynamic framework loader activity"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'testframeworks')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # fake versions and archs
        self.fake_arch_version("bar", "10.10.10")
        # load custom framework directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["Category A"]

    def tearDown(self):
        # we reset the loaded categories
        self.CategoryHandler.categories = NoneDict()
        self.restore_arch_version()
        super().tearDown()

    def test_load_main_category(self):
        """The main category is loaded"""
        self.assertEquals(len([1 for category in self.CategoryHandler.categories.values()
                               if category.is_main_category]), 1)

    def test_get_main_category(self):
        """main_category property returns main category"""
        main_category = [category for category in self.CategoryHandler.categories.values()
                         if category.is_main_category][0]
        self.assertEquals(self.CategoryHandler.main_category, main_category)

    def test_load_category(self):
        """There is at least one category (not main) loaded"""
        self.assertTrue(len([1 for category in self.CategoryHandler.categories.values()
                             if not category.is_main_category]) > 0)

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
        self.assertEquals(self.categoryA.is_installed, self.CategoryHandler.NOT_INSTALLED)

    def test_category_fully_installed(self):
        """Category returns than all frameworks are installed"""
        self.assertEquals(self.CategoryHandler.categories["Category/B"].is_installed,
                          self.CategoryHandler.FULLY_INSTALLED)

    def test_category_half_installed(self):
        """Category returns than half frameworks are installed"""
        self.assertEquals(self.CategoryHandler.categories["Category/C"].is_installed,
                          self.CategoryHandler.PARTIALLY_INSTALLED)

    def test_frameworks_loaded_in_main_category(self):
        """Some frameworks are loaded and attached to main category"""
        self.assertTrue(len(self.CategoryHandler.main_category.frameworks) > 1)
        self.assertIsNotNone(self.CategoryHandler.main_category.frameworks["Framework Free A"])
        self.assertIsNotNone(self.CategoryHandler.main_category.frameworks["Framework Free / B"])

    def test_frameworks_report_installed(self):
        """Frameworks have an is_installed property"""
        category = self.CategoryHandler.categories["Category/C"]
        self.assertFalse(category.frameworks["Framework A"].is_installed)
        self.assertTrue(category.frameworks["Framework/B"].is_installed)

    def test_default_framework(self):
        """Test that a default framework flag is accessible"""
        framework_default = self.categoryA.frameworks["Framework A"]
        self.assertEquals(self.categoryA.default_framework, framework_default)

    def test_default_install_path(self):
        """Default install path is what we expect, based on category and framework prog_name"""
        self.assertEquals(self.categoryA.frameworks["Framework/B"].install_path,
                          os.path.expanduser("~/tools/category-a/framework-b"))

    def test_specified_at_load_install_path(self):
        """Default install path is overriden by framework specified install path at load time"""
        self.assertEquals(self.categoryA.frameworks["Framework A"].install_path,
                          os.path.expanduser("~/tools/custom/frameworka"))

    def test_no_restriction_installable_framework(self):
        """Framework with an no arch or version restriction is installable"""
        self.assertTrue(self.categoryA.frameworks["Framework A"].is_installable)

    def test_right_arch_right_version_framework(self):
        """Framework with a correct arch and correct version is installable"""
        self.assertTrue(self.CategoryHandler.categories["Category D"].frameworks["Framework C"].is_installable)

    def test_unsupported_arch_framework(self):
        """Framework with an unsupported arch isn't registered"""
        self.assertIsNone(self.CategoryHandler.categories["Category D"].frameworks["Framework A"])

    def test_unsupported_version_framework(self):
        """Framework with an unsupported arch isn't registered"""
        self.assertIsNone(self.CategoryHandler.categories["Category D"].frameworks["Framework B"])


class TestFrameworkLoaderWithValidConfig(BaseFrameworkLoader):
    """This will test the dynamic framework loader activity with a valid configuration"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'testframeworks')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        # load valid configuration
        super().setUp()
        change_xdg_config_path(self.config_dir_for_name("valid"))
        # load custom framework directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["Category A"]

    def tearDown(self):
        # we reset the loaded categories
        self.CategoryHandler.categories = NoneDict()
        super().tearDown()

    def test_config_override_defaults(self):
        """Configuration override defaults (explicit or implicit). If not present in config, still load default"""
        # was overridden with at load time
        self.assertEquals(self.categoryA.frameworks["Framework A"].install_path,
                          "/home/didrocks/quickly/ubuntu-developer-tools/adt-eclipse")
        # was default
        self.assertEquals(self.categoryA.frameworks["Framework/B"].install_path,
                          "/home/didrocks/foo/bar/android-studio")
        # isn't in the config
        self.assertEquals(self.CategoryHandler.categories['Category/C'].frameworks["Framework A"].install_path,
                          os.path.expanduser("~/tools/category-c/framework-a"))


class TestFrameworkLoaderSaveConfig(BaseFrameworkLoader):
    """This will test the dynamic framework loader activity being able to save some configurations"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'testframeworks')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # load custom framework directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["Category A"]

    def tearDown(self):
        # we reset the loaded categories
        self.CategoryHandler.categories = NoneDict()
        super().tearDown()

    def test_call_setup_save_config(self):
        """Calling setup with a custom install path save it in the configuration"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            # load custom framework directory
            change_xdg_config_path(tmpdirname)
            self.categoryA.frameworks["Framework/B"].setup()

            self.assertEquals(ConfigHandler().config,
                              {'frameworks': {
                                  'Category A': {
                                      'Framework/B': {'path': os.path.expanduser('~/tools/category-a/framework-b')}
                                  }}})

    def test_call_setup_save_tweaked_path(self):
        """Calling setup with a custom install path save it in the configuration"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            # load custom framework directory
            change_xdg_config_path(tmpdirname)
            self.categoryA.frameworks["Framework/B"].setup(install_path="/home/foo/bar")

            self.assertEquals(ConfigHandler().config,
                              {'frameworks': {
                                  'Category A': {
                                      'Framework/B': {'path': '/home/foo/bar'}
                                  }}})


class TestFrameworkLoadOnDemandLoader(BaseFrameworkLoader):
    """This will test the dynamic framework loader activity. This class doesn't load frameworks before the tests does"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'testframeworks')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # fake versions and archs
        self.fake_arch_version("foo", "10.04")

    def tearDown(self):
        # we reset the loaded categories
        self.CategoryHandler.categories = NoneDict()
        self.restore_arch_version()
        super().tearDown()

        self.categoryA = self.CategoryHandler.categories["Category A"]

    def test_arch_report_issue_framework(self):
        """Framework where we can't reach arch and having a restriction isn't installable"""
        self.get_current_arch_mock.side_effect = BaseException('arch detection failure!')
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()

        # restricted arch framework isn't installable
        self.assertIsNone(self.CategoryHandler.categories["Category D"].frameworks["Framework A"])
        # framework with no arch restriction but others are still installable
        self.assertTrue(self.CategoryHandler.categories["Category D"].frameworks["Framework B"].is_installable)
        # framework without any restriction is still installable
        self.assertTrue(self.CategoryHandler.categories["Category A"].frameworks["Framework A"].is_installable)
        self.expect_warn_error = True

    def test_version_report_issue_framework(self):
        """Framework where we can't reach version and having a restriction isn't installable"""
        self.get_current_ubuntu_version_mock.side_effect = BaseException('version detection failure!')
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()

        # restricted version framework isn't installable
        self.assertIsNone(self.CategoryHandler.categories["Category D"].frameworks["Framework B"])
        # framework with no version restriction but others are still installable
        self.assertTrue(self.CategoryHandler.categories["Category D"].frameworks["Framework A"].is_installable)
        # framework without any restriction is still installable
        self.assertTrue(self.CategoryHandler.categories["Category A"].frameworks["Framework A"].is_installable)
        self.expect_warn_error = True

class TestEmptyFrameworkLoader(BaseFrameworkLoader):
    """This will test the dynamic framework loader activity with an empty set of frameworks"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'testframeworksdoesntexist')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # load custom unexisting framework directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworksdoesntexist"):
            frameworks.load_frameworks()

    def tearDown(self):
        # we reset the loaded categories
        frameworks.BaseCategory.categories = NoneDict()
        super().tearDown()

    def test_invalid_framework(self):
        """There is one main category, but nothing else"""
        main_category = [category for category in self.CategoryHandler.categories.values()
                         if category.is_main_category][0]
        self.assertEquals(self.CategoryHandler.main_category, main_category)
        self.assertEquals(len(self.CategoryHandler.categories), 1)


class TestDuplicatedFrameworkLoader(BaseFrameworkLoader):
    """This will test the dynamic framework loader activity with some duplicated categories and frameworks"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'duplicatedframeworks')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "duplicatedframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["Category A"]
        self.expect_warn_error = True  # as we load multiple duplicate categories and frameworks

    def tearDown(self):
        # we reset the loaded categories
        frameworks.BaseCategory.categories = NoneDict()
        super().tearDown()

    def test_duplicated_categories(self):
        """We only load one category when a second with same name is met"""
        # main + categoryA
        self.assertEquals(len(self.CategoryHandler.categories), 2)
        self.assertEquals(self.CategoryHandler.categories["Category A"].name, "Category A")

    def test_duplicated_frameworks(self):
        """We only load one framework when a second with the same name is met"""
        self.assertEquals(len(self.categoryA.frameworks), 1)

    def test_main_category_empty(self):
        """The main category (unused here) is empty by default"""
        self.assertEquals(len(self.CategoryHandler.main_category.frameworks), 0)


class TestMultipleDefaultFrameworkLoader(BaseFrameworkLoader):
    """This will test if we try to load multiple default frameworsk in loader"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'multipledefaultsframeworks')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "multipledefaultsframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["Category A"]
        self.expect_warn_error = True  # as we load multiple default frameworks in a category

    def tearDown(self):
        # we reset the loaded categories
        frameworks.BaseCategory.categories = NoneDict()
        super().tearDown()

    def test_multiple_defaults(self):
        """Setting multiple defaults frameworks to a category should void any default"""
        self.assertIsNone(self.categoryA.default_framework)
        self.assertEquals(len(self.categoryA.frameworks), 2)  # ensure they are still loaded

    def test_one_default_in_main_category(self):
        """Reject default framework for main category"""
        self.assertIsNone(self.CategoryHandler.main_category.default_framework)
        self.assertEquals(len(self.CategoryHandler.main_category.frameworks), 1)  # ensure it's still loaded


class TestNotLoadedFrameworkLoader(BaseFrameworkLoader):

    def setUp(self):
        super().setUp()
        self.CategoryHandler = frameworks.BaseCategory

    def test_get_no_main_category(self):
        """main_category returns None when there is no main category"""
        self.assertIsNone(self.CategoryHandler.main_category)

    def test_get_with_no_category(self):
        """categories is empty when there is no category loaded"""
        self.assertEquals(len(self.CategoryHandler.categories), 0)


class TestInvalidFrameworkLoader(BaseFrameworkLoader):
    """This will test the dynamic framework loader activity with some invalid (interface not fullfilled) frameworks"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'invalidframeworks')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # load custom unexisting framework directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "invalidframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["Category A"]

    def tearDown(self):
        # we reset the loaded categories
        frameworks.BaseCategory.categories = NoneDict()
        super().tearDown()

    def test_load(self):
        """Previous loading should have been successful"""
        self.assertFalse(self.categoryA.has_frameworks())
        self.expect_warn_error = True  # It errors the fact that it ignores one invalid framework


class TestProductionFrameworkLoader(BaseFrameworkLoader):
    """Load production framework and ensure there is no warning and no error"""

    def test_load(self):
        frameworks.load_frameworks()
        self.assertTrue(len(frameworks.BaseCategory.categories) > 0)
        self.assertIsNotNone(frameworks.BaseCategory.main_category)
        self.assertEquals(len(frameworks.BaseCategory.categories["Android"].frameworks), 2)
