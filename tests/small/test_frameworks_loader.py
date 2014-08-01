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

import argparse
import importlib
import os
import shutil
import sys
import tempfile
from ..data.testframeworks.uninstantiableframework import Uninstantiable, InheritedFromUninstantiable
from ..tools import get_data_dir, change_xdg_path, patchelem, LoggedTestCase, ConfigHandler
import udtc
from udtc import frameworks
from udtc.frameworks.baseinstaller import BaseInstaller
from udtc.tools import NoneDict
from unittest.mock import Mock, patch, call


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
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir_for_name("foo"))

    def tearDown(self):
        change_xdg_path('XDG_CONFIG_HOME', remove=True)
        self.CategoryHandler.categories = NoneDict()
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
        # load custom framework-directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]

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

    def test_get_category_by_prog_name(self):
        """categories index returns matching category"""
        category = self.CategoryHandler.categories["category-a"]
        self.assertEquals(category.name, "Category A")

    def test_get_framework_by_prog_name(self):
        """Framework index returns matching framework"""
        framework = self.categoryA.frameworks["framework-a"]
        self.assertEquals(framework.name, "Framework A")

    def test_get_category_not_existing(self):
        """the call to get category returns None when there is no match"""
        self.assertIsNone(self.CategoryHandler.categories["foo"])

    def test_get_category_prog_name(self):
        """prog_name for category is what we expect"""
        self.assertEquals(self.categoryA.prog_name, "category-a")
        self.assertEquals(self.CategoryHandler.categories["category-b"].prog_name, "category-b")

    def test_multiple_files_loaded(self):
        """We load multiple categories in different files"""
        # main category, + at least 2 other categories
        self.assertTrue(len(self.CategoryHandler.categories) > 2)
        self.assertIsNotNone(self.categoryA)
        self.assertIsNotNone(self.CategoryHandler.categories["category-b"])

    def test_frameworks_loaded(self):
        """We have frameworks attached to a category"""
        self.assertTrue(len(self.categoryA.frameworks) > 1)
        self.assertTrue(self.categoryA.frameworks["framework-a"].name, "framework-a")
        self.assertTrue(self.categoryA.has_frameworks())

    def test_framework_not_existing(self):
        """the call  to get a framework returns None when there is no match"""
        self.assertIsNone(self.categoryA.frameworks["foo"])

    def test_frameworks_doesn_t_mix(self):
        """Frameworks, even with the same name, don't mix between categories"""
        self.assertNotEquals(self.categoryA.frameworks["framework-a"],
                             self.CategoryHandler.categories["category-b"].frameworks["framework-a"])

    def test_has_more_than_one_framework(self):
        """more than one frameworks in a category is correctly reported"""
        self.assertFalse(self.categoryA.has_one_framework())

    def test_empty_category_loaded(self):
        """We still load an empty category"""
        self.assertIsNotNone(self.CategoryHandler.categories["empty-category"])

    def test_has_frameworks_on_empty_category(self):
        """has_frameworks return False on empty category"""
        self.assertFalse(self.CategoryHandler.categories["empty-category"].has_frameworks())
        self.assertFalse(self.CategoryHandler.categories["empty-category"].has_one_framework())

    def test_one_framework_category(self):
        """A category with one framework is reported as so"""
        self.assertTrue(self.CategoryHandler.categories["one-framework-category"].has_one_framework())

    def test_framework_prog_name(self):
        """prog_name for framework is what we expect"""
        self.assertEquals(self.categoryA.frameworks["framework-a"].prog_name, "framework-a")
        self.assertEquals(self.categoryA.frameworks["framework-b"].prog_name, "framework-b")

    def test_nothing_installed(self):
        """Category returns that no framework is installed"""
        self.assertEquals(self.categoryA.is_installed, self.CategoryHandler.NOT_INSTALLED)

    def test_category_fully_installed(self):
        """Category returns than all frameworks are installed"""
        self.assertEquals(self.CategoryHandler.categories["category-b"].is_installed,
                          self.CategoryHandler.FULLY_INSTALLED)

    def test_category_half_installed(self):
        """Category returns than half frameworks are installed"""
        self.assertEquals(self.CategoryHandler.categories["category-c"].is_installed,
                          self.CategoryHandler.PARTIALLY_INSTALLED)

    def test_frameworks_loaded_in_main_category(self):
        """Some frameworks are loaded and attached to main category"""
        self.assertTrue(len(self.CategoryHandler.main_category.frameworks) > 1)
        self.assertIsNotNone(self.CategoryHandler.main_category.frameworks["framework-free-a"])
        self.assertIsNotNone(self.CategoryHandler.main_category.frameworks["framework-free---b"])

    def test_frameworks_report_installed(self):
        """Frameworks have an is_installed property"""
        category = self.CategoryHandler.categories["category-c"]
        self.assertFalse(category.frameworks["framework-a"].is_installed)
        self.assertTrue(category.frameworks["framework-b"].is_installed)

    def test_default_framework(self):
        """Test that a default framework flag is accessible"""
        framework_default = self.categoryA.frameworks["framework-a"]
        self.assertEquals(self.categoryA.default_framework, framework_default)

    def test_default_install_path(self):
        """Default install path is what we expect, based on category-and framework prog_name"""
        self.assertEquals(self.categoryA.frameworks["framework-b"].install_path,
                          os.path.expanduser("~/tools/category-a/framework-b"))

    def test_specified_at_load_install_path(self):
        """Default install path is overriden by framework specified install path at load time"""
        self.assertEquals(self.categoryA.frameworks["framework-a"].install_path,
                          os.path.expanduser("~/tools/custom/frameworka"))

    def test_no_restriction_installable_framework(self):
        """Framework with an no arch or version restriction is installable"""
        self.assertTrue(self.categoryA.frameworks["framework-a"].is_installable)

    def test_right_arch_right_version_framework(self):
        """Framework with a correct arch and correct version is installable"""
        self.assertTrue(self.CategoryHandler.categories["category-d"].frameworks["framework-c"].is_installable)

    def test_unsupported_arch_framework(self):
        """Framework with an unsupported arch isn't registered"""
        self.assertIsNone(self.CategoryHandler.categories["category-d"].frameworks["framework-a"])

    def test_unsupported_version_framework(self):
        """Framework with an unsupported arch isn't registered"""
        self.assertIsNone(self.CategoryHandler.categories["category-d"].frameworks["framework-b"])

    def test_child_installable_chained_parent(self):
        """Framework with an is_installable chained to parent"""
        self.assertTrue(self.CategoryHandler.categories["category-e"].frameworks["framework-a"].is_installable)

    def test_child_installable_overridden(self):
        """Framework with an is_installable override to True from children (with unmatched restrictions)"""
        self.assertTrue(self.CategoryHandler.categories["category-e"].frameworks["framework-b"].is_installable)

    def test_child_installable_overridden_false(self):
        """Framework with an is_installable override to False from children (with no restrictions)"""
        self.assertIsNone(self.CategoryHandler.categories["category-e"].frameworks["framework-c"])

    def test_check_not_installed_wrong_path(self):
        """Framework isn't installed path doesn't exist"""
        self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-a"].is_installed)

    def test_check_installed_right_path_no_package_req(self):
        """Framework is installed if right path but no package req."""
        self.assertTrue(self.CategoryHandler.categories["category-f"].frameworks["framework-b"].is_installed)

    def test_check_unmatched_requirements_not_installed(self):
        """Framework with unmatched requirements are not registered"""
        self.assertIsNone(self.CategoryHandler.categories["category-f"].frameworks["framework-c"])

    def test_no_root_need_if_no_requirements(self):
        """Framework with not requirements don't need root access"""
        self.assertFalse(self.categoryA.frameworks["framework-a"].need_root_access)

    def test_parse_category_and_framework_run_correct_framework(self):
        """Parsing category and framework return right category and framework"""
        args = Mock()
        args.category = "category-a"
        args.framework = "framework-b"
        with patch.object(self.CategoryHandler.categories[args.category].frameworks["framework-b"], "setup")\
                as setup_call:
            self.CategoryHandler.categories[args.category].run_for(args)

            self.assertTrue(setup_call.called)
            self.assertEquals(setup_call.call_args, call(args.destdir))

    def test_parse_no_framework_run_default_for_category(self):
        """Parsing category will run default framework"""
        args = Mock()
        args.category = "category-a"
        args.framework = None
        with patch.object(self.CategoryHandler.categories[args.category].frameworks["framework-a"], "setup")\
                as setup_call:
            self.CategoryHandler.categories[args.category].run_for(args)

            self.assertTrue(setup_call.called)
            self.assertEquals(setup_call.call_args, call(args.destdir))

    def test_parse_no_framework_with_no_default_returns_errors(self):
        """Parsing a category with no default returns an error when calling run"""
        args = Mock()
        args.category = "category-b"
        args.framework = None
        self.assertRaises(BaseException, self.CategoryHandler.categories[args.category].run_for, args)
        self.expect_warn_error = True

    def test_uninstantiable_framework(self):
        """A uninstantiable framework isn't loaded"""
        # use the string as we fake the package when loading them
        self.assertNotIn(str(Uninstantiable).split('.')[-1],
                         [str(type(framework)).split('.')[-1] for framework in
                          self.CategoryHandler.main_category.frameworks.values()])

    def test_inherited_from_uninstantiable_framework(self):
        """We can attach a framework which inherit from an uninstantiable one"""
        # use the string as we fake the package when loading them
        self.assertIn(str(InheritedFromUninstantiable).split('.')[-1],
                      [str(type(framework)).split('.')[-1] for framework in
                       self.CategoryHandler.main_category.frameworks.values()])


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
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir_for_name("valid"))
        # load custom framework-directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]

    def tearDown(self):
        # we reset the loaded categories
        self.CategoryHandler.categories = NoneDict()
        change_xdg_path('XDG_CONFIG_HOME', remove=True)
        super().tearDown()

    def test_config_override_defaults(self):
        """Configuration override defaults (explicit or implicit). If not present in config, still load default"""
        # was overridden with at load time
        self.assertEquals(self.categoryA.frameworks["framework-a"].install_path,
                          "/home/didrocks/quickly/ubuntu-developer-tools/adt-eclipse")
        # was default
        self.assertEquals(self.categoryA.frameworks["framework-b"].install_path,
                          "/home/didrocks/foo/bar/android-studio")
        # isn't in the config
        self.assertEquals(self.CategoryHandler.categories['category-c'].frameworks["framework-a"].install_path,
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
        # load custom framework-directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]
        self.config_dir = tempfile.mkdtemp()
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir)

    def tearDown(self):
        # we reset the loaded categories
        self.CategoryHandler.categories = NoneDict()
        change_xdg_path('XDG_CONFIG_HOME', remove=True)
        shutil.rmtree(self.config_dir)
        super().tearDown()

    def test_call_mark_in_config_save_config(self):
        """Calling mark_in_config save path in the configuration"""
        # load custom framework-directory
        self.categoryA.frameworks["framework-b"].mark_in_config()

        self.assertEquals(ConfigHandler().config,
                          {'frameworks': {
                              'category-a': {
                                  'framework-b': {'path': os.path.expanduser('~/tools/category-a/framework-b')}
                              }}})

    def test_call_setup_save_and_then_mark_in_config_tweaked_path(self):
        """Calling mark_in_config with a custom install path save it in the configuration"""
            # load custom framework-directory
        self.categoryA.frameworks["framework-b"].setup(install_path="/home/foo/bar")
        self.categoryA.frameworks["framework-b"].mark_in_config()

        self.assertEquals(ConfigHandler().config,
                          {'frameworks': {
                              'category-a': {
                                  'framework-b': {'path': '/home/foo/bar'}
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

    def loadFramework(self, framework_name):
        """Load framework name"""
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', framework_name):
            frameworks.load_frameworks()

    def install_category_parser(self, main_parser, categories=[]):
        """Install parser for those categories"""
        categories_parser = main_parser.add_subparsers(dest="category")
        category_parsers = []
        for category in categories:
            with patch('udtc.frameworks.is_completion_mode') as completionmode_mock:
                completionmode_mock.return_value = False
                self.loadFramework("testframeworks")
                category_parsers.append(self.CategoryHandler.categories[category]
                                        .install_category_parser(categories_parser))
        return category_parsers

    def test_arch_report_issue_framework(self):
        """Framework where we can't reach arch and having a restriction isn't installable"""
        self.get_current_arch_mock.side_effect = BaseException('arch detection failure!')
        self.loadFramework("testframeworks")

        # restricted arch framework isn't installable
        self.assertIsNone(self.CategoryHandler.categories["category-d"].frameworks["framework-a"])
        # framework with no arch restriction but others are still installable
        self.assertTrue(self.CategoryHandler.categories["category-d"].frameworks["framework-b"].is_installable)
        # framework without any restriction is still installable
        self.assertTrue(self.CategoryHandler.categories["category-a"].frameworks["framework-a"].is_installable)
        self.expect_warn_error = True

    def test_version_report_issue_framework(self):
        """Framework where we can't reach version and having a restriction isn't installable"""
        self.get_current_ubuntu_version_mock.side_effect = BaseException('version detection failure!')
        self.loadFramework("testframeworks")

        # restricted version framework isn't installable
        self.assertIsNone(self.CategoryHandler.categories["category-d"].frameworks["framework-b"])
        # framework with no version restriction but others are still installable
        self.assertTrue(self.CategoryHandler.categories["category-d"].frameworks["framework-a"].is_installable)
        # framework without any restriction is still installable
        self.assertTrue(self.CategoryHandler.categories["category-a"].frameworks["framework-a"].is_installable)
        self.expect_warn_error = True

    def test_check_not_installed_wrong_requirements(self):
        """Framework isn't installed if path and package requirements aren't met"""
        with patch('udtc.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = False
            self.loadFramework("testframeworks")
            self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].is_installed)
            requirement_mock.return_value.is_bucket_installed.assert_called_with(['foo', 'bar'])
            # is_bucket_available is called when it's not installed
            requirement_mock.return_value.is_bucket_available.assert_any_calls(call(['foo', 'bar']))

    def test_check_installed_with_matched_requirements(self):
        """Framework is installed if path and package requirements are met"""
        with patch('udtc.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = True
            self.loadFramework("testframeworks")
            self.assertTrue(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].is_installed)
            requirement_mock.return_value.is_bucket_installed.assert_called_with(['foo', 'bar'])
            # we don't call is_bucket_available if requirements are met
            self.assertFalse(call(['foo', 'bar']) in requirement_mock.return_value.is_bucket_available.call_args_list)

    def test_check_requirements_inherited_from_category(self):
        """Framework without package requirements are inherited from category"""
        with patch('udtc.frameworks.RequirementsHandler') as requirement_mock:
            self.loadFramework("testframeworks")
            self.assertEquals(self.CategoryHandler.categories["category-g"].frameworks["framework-b"]
                              .packages_requirements, ["baz"])

    def test_check_requirements_from_category_merge_into_exiting(self):
        """Framework with package requirements merged them from the associated category"""
        with patch('udtc.frameworks.RequirementsHandler') as requirement_mock:
            self.loadFramework("testframeworks")
            self.assertEquals(self.CategoryHandler.categories["category-g"].frameworks["framework-a"]
                              .packages_requirements, ["buz", "biz", "baz"])

    def test_root_needed_if_not_matched_requirements(self):
        """Framework with unmatched requirements need root access"""
        with patch('udtc.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = False
            self.loadFramework("testframeworks")
            self.assertTrue(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].need_root_access)

    def test_no_root_needed_if_matched_requirements_even_uninstalled(self):
        """Framework which are uninstalled but with matched requirements doesn't need root access"""
        with patch('udtc.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = True
            self.loadFramework("testframeworks")
            # ensure the framework isn't installed, but the bucket being installed, we don't need root access
            self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-a"].is_installed)
            self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-a"].need_root_access)

    def test_root_needed_setup_call_root(self):
        """Framework with root access needed call sudo"""
        with patch('udtc.frameworks.subprocess') as subprocess_mock,\
                patch.object(udtc.frameworks.os, 'geteuid', return_value=1000) as geteuid,\
                patch('udtc.frameworks.MainLoop') as mainloop_mock,\
                patch('udtc.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = False
            self.loadFramework("testframeworks")
            self.assertTrue(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].need_root_access)
            self.CategoryHandler.categories["category-f"].frameworks["framework-c"].setup()

            self.assertEquals(subprocess_mock.call.call_args[0][0][0], "sudo")
            self.assertTrue(mainloop_mock.return_value.quit.called)

    def test_no_root_needed_setup_doesnt_call_root(self):
        """Framework without root access needed don't call sudo"""
        with patch('udtc.frameworks.subprocess') as subprocess_mock,\
                patch.object(udtc.frameworks.os, 'geteuid', return_value=1000) as geteuid,\
                patch.object(udtc.frameworks.sys, 'exit', return_value=True) as sys_exit_mock,\
                patch('udtc.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = True
            self.loadFramework("testframeworks")
            self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].need_root_access)
            self.CategoryHandler.categories["category-f"].frameworks["framework-c"].setup()

            self.assertFalse(subprocess_mock.call.called)
            self.assertFalse(sys_exit_mock.called)

    def test_root_needed_setup_doesnt_call_root(self):
        """setup doesn't call sudo if we are already root"""
        with patch('udtc.frameworks.subprocess') as subprocess_mock,\
                patch.object(udtc.frameworks.sys, 'exit', return_value=True) as sys_exit_mock,\
                patch.object(udtc.frameworks.os, 'geteuid', return_value=0) as geteuid,\
                patch('udtc.frameworks.RequirementsHandler') as requirement_mock,\
                patch('udtc.frameworks.switch_to_current_user') as switch_to_current_use_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = False
            self.loadFramework("testframeworks")
            self.assertTrue(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].need_root_access)
            self.CategoryHandler.categories["category-f"].frameworks["framework-c"].setup()

            self.assertFalse(subprocess_mock.call.called)
            self.assertFalse(sys_exit_mock.called)
            geteuid.assert_called_once_with()
            switch_to_current_use_mock.assert_called_once_with()

    def test_completion_mode_dont_use_expensive_calls(self):
        """Completion mode bypass expensive calls and so, register all frameworks"""
        with patch('udtc.frameworks.ConfigHandler') as config_handler_mock,\
                patch('udtc.frameworks.RequirementsHandler') as requirementhandler_mock,\
                patch('udtc.frameworks.is_completion_mode') as completionmode_mock:
            completionmode_mock.return_value = True
            self.loadFramework("testframeworks")

            self.assertTrue(completionmode_mock.called)
            self.assertFalse(len(config_handler_mock.return_value.config.mock_calls) > 0)
            self.assertFalse(requirementhandler_mock.return_value.is_bucket_installed.called)
            # test that a non installed framework is registered
            self.assertIsNotNone(self.CategoryHandler.categories["category-e"].frameworks["framework-c"])

    def test_use_expensive_calls_when_not_in_completion_mode(self):
        """Non completion mode have expensive calls and don't register all frameworks"""
        with patch('udtc.frameworks.ConfigHandler') as config_handler_mock,\
                patch('udtc.frameworks.RequirementsHandler') as requirementhandler_mock,\
                patch('udtc.frameworks.is_completion_mode') as completionmode_mock:
            completionmode_mock.return_value = False
            self.loadFramework("testframeworks")

            self.assertTrue(completionmode_mock.called)
            self.assertTrue(len(config_handler_mock.return_value.config.mock_calls) > 0)
            self.assertTrue(requirementhandler_mock.return_value.is_bucket_installed.called)
            # test that a non installed framework is registered
            self.assertIsNone(self.CategoryHandler.categories["category-e"].frameworks["framework-c"])

    def test_install_category_and_framework_parsers(self):
        """Install category and framework parsers contains works"""
        main_parser = argparse.ArgumentParser()
        categories_parser = main_parser.add_subparsers()
        with patch('udtc.frameworks.is_completion_mode') as completionmode_mock:
            completionmode_mock.return_value = False
            self.loadFramework("testframeworks")
            category_parser = self.CategoryHandler.categories['category-a'].install_category_parser(categories_parser)

            self.assertTrue('category-a' in categories_parser.choices)
            self.assertTrue('framework-a' in category_parser.choices)
            self.assertTrue('framework-b' in category_parser.choices)

    def test_parse_category_and_framework(self):
        """Parsing category and framework return right category and framework"""
        main_parser = argparse.ArgumentParser()
        self.install_category_parser(main_parser, ['category-a'])
        args = main_parser.parse_args(["category-a", "framework-a"])
        self.assertEquals(args.category, "category-a")
        self.assertEquals(args.framework, "framework-a")
        self.assertEquals(args.destdir, None)

    def test_parse_invalid_categories_raise_exit_error(self):
        """Invalid categories parse requests exit"""
        def error_without_message(x):
            raise SystemExit()
        main_parser = argparse.ArgumentParser()
        main_parser.print_usage = lambda x: ""
        main_parser.error = error_without_message
        self.install_category_parser(main_parser, [])

        self.assertRaises(SystemExit, main_parser.parse_args, ["category-a", "framework-a"])

    def test_parse_invalid_frameworks_return_error(self):
        """Invalid framework parse requests exit"""
        def error_without_message(x):
            raise SystemExit()
        main_parser = argparse.ArgumentParser()
        self.install_category_parser(main_parser, ["category-a"])
        category_parser = main_parser._actions[1].choices["category-a"]
        category_parser.print_usage = lambda x: ""
        category_parser.error = error_without_message

        self.assertRaises(SystemExit, main_parser.parse_args, ["category-a", "framework-aa"])

    def test_parse_no_category_return_empty_namespace(self):
        """No category or framework returns an empty namespace"""
        main_parser = argparse.ArgumentParser()
        self.install_category_parser(main_parser, ['category-a'])
        self.assertEquals(main_parser.parse_args([]), argparse.Namespace(category=None))

    def test_install_category_with_no_framework(self):
        """Install category with no framework returns None"""
        main_parser = argparse.ArgumentParser()
        self.assertEquals(self.install_category_parser(main_parser, ['empty-category']), [None])

    def test_install_main_category(self):
        """Main category install directly at root of the parser"""
        main_parser = argparse.ArgumentParser()
        main_cat_parser = self.install_category_parser(main_parser, ['main'])[0]

        self.assertTrue('framework-free---b' in main_cat_parser.choices)
        self.assertTrue('framework-free-a' in main_cat_parser.choices)
        self.assertFalse('framework-a' in main_cat_parser.choices)

    def test_parse_main_category(self):
        """Main category elements can be directly accessed"""
        main_parser = argparse.ArgumentParser()
        self.install_category_parser(main_parser, ['main'])
        args = main_parser.parse_args(["framework-free-a"])
        self.assertEquals(args.category, "framework-free-a")
        self.assertEquals(args.destdir, None)
        self.assertFalse("framework" in args)

    def test_run_framework_in_main_category(self):
        """Frameworks command from main category can be run as usual"""
        main_parser = argparse.ArgumentParser()
        self.install_category_parser(main_parser, ['main'])
        args = main_parser.parse_args(["framework-free-a"])
        with patch.object(self.CategoryHandler.main_category.frameworks["framework-free-a"], "setup") as setup_call:
            self.CategoryHandler.main_category.frameworks["framework-free-a"].run_for(args)
            self.assertTrue(setup_call.called)


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
        # load custom unexisting framework-directory
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
        self.categoryA = self.CategoryHandler.categories["category-a"]
        self.expect_warn_error = True  # as we load multiple duplicate categories and frameworks

    def tearDown(self):
        # we reset the loaded categories
        frameworks.BaseCategory.categories = NoneDict()
        super().tearDown()

    def test_duplicated_categories(self):
        """We only load one category when a second with same name is met"""
        # main + categoryA
        self.assertEquals(len(self.CategoryHandler.categories), 2)
        self.assertEquals(self.CategoryHandler.categories["category-a"].name, "Category A")

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
        self.categoryA = self.CategoryHandler.categories["category-a"]
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
        # load custom unexisting framework-directory
        with patchelem(udtc.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(udtc.frameworks, '__package__', "invalidframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]

    def tearDown(self):
        # we reset the loaded categories
        frameworks.BaseCategory.categories = NoneDict()
        super().tearDown()

    def test_load(self):
        """Previous loading should have been successful"""
        self.assertFalse(self.categoryA.has_frameworks())
        self.expect_warn_error = True  # It errors the fact that it ignores one invalid framework


class TestProductionFrameworkLoader(BaseFrameworkLoader):
    """Load production framework-and ensure there is no warning and no error"""

    def test_load(self):
        """Can load production frameworks"""
        frameworks.load_frameworks()
        self.assertTrue(len(self.CategoryHandler.categories) > 0)
        self.assertIsNotNone(self.CategoryHandler.main_category)
        self.assertEquals(len(self.CategoryHandler.categories["android"].frameworks), 2)

    def test_ignored_frameworks(self):
        """Ignored frameworks aren't loaded"""
        frameworks.load_frameworks()
        self.assertNotIn(BaseInstaller, frameworks.BaseCategory.main_category.frameworks.values())


class TestCustomFrameworkCantLoad(BaseFrameworkLoader):
    """Get custom unloadable automatically frameworks to test custom corner cases"""

    class _CustomFramework(udtc.frameworks.BaseFramework):

        def __init__(self):
            super().__init__(name="Custom", description="Custom uninstallable framework",
                             category=udtc.frameworks.MainCategory())

        def setup(self):
            super().setup()

        @property
        def is_installable(self):
            return False

    def test_call_setup_on_uninstallable_framework(self):
        """Calling setup on uninstallable framework return to main UI"""
        fw = self._CustomFramework()
        with patch("udtc.frameworks.UI") as UIMock:
            fw.setup()
            self.assertTrue(UIMock.return_main_screen.called)
        self.expect_warn_error = True
