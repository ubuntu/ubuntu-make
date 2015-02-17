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
from contextlib import suppress
import importlib
import os
import shutil
import sys
import tempfile
from ..data.testframeworks.uninstantiableframework import Uninstantiable, InheritedFromUninstantiable
from ..tools import get_data_dir, change_xdg_path, patchelem, LoggedTestCase
import umake
from umake import frameworks
from umake.frameworks.baseinstaller import BaseInstaller
from umake.settings import UMAKE_FRAMEWORKS_ENVIRON_VARIABLE
from umake.tools import NoneDict, ConfigHandler
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
        # we reset the loaded categories
        self.CategoryHandler.categories = NoneDict()
        super().tearDown()

    def config_dir_for_name(self, name):
        """Return the config dir for this name"""
        return os.path.join(get_data_dir(), 'configs', name)

    def fake_arch_version(self, arch, version):
        """Help to mock the current arch and version on further calls"""
        self._saved_current_arch_fn = umake.frameworks.get_current_arch
        self.get_current_arch_mock = Mock()
        self.get_current_arch_mock.return_value = arch
        umake.frameworks.get_current_arch = self.get_current_arch_mock

        self._saved_current_ubuntu_version_fn = umake.frameworks.get_current_ubuntu_version
        self.get_current_ubuntu_version_mock = Mock()
        self.get_current_ubuntu_version_mock.return_value = version
        umake.frameworks.get_current_ubuntu_version = self.get_current_ubuntu_version_mock

    def restore_arch_version(self):
        """Restore initial current arch and version"""
        umake.frameworks.get_current_arch = self._saved_current_arch_fn
        umake.frameworks.get_current_ubuntu_version = self._saved_current_ubuntu_version_fn


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
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]

    def tearDown(self):
        self.restore_arch_version()
        super().tearDown()

    def test_load_main_category(self):
        """The main category is loaded"""
        self.assertEqual(len([1 for category in self.CategoryHandler.categories.values()
                              if category.is_main_category]), 1, str(self.CategoryHandler.categories.values()))

    def test_get_main_category(self):
        """main_category property returns main category"""
        main_category = [category for category in self.CategoryHandler.categories.values()
                         if category.is_main_category][0]
        self.assertEqual(self.CategoryHandler.main_category, main_category)

    def test_load_category(self):
        """There is at least one category (not main) loaded"""
        self.assertTrue(len([1 for category in self.CategoryHandler.categories.values()
                             if not category.is_main_category]) > 0, str(self.CategoryHandler.categories.values()))

    def test_get_category_by_prog_name(self):
        """categories index returns matching category"""
        category = self.CategoryHandler.categories["category-a"]
        self.assertEqual(category.name, "Category A")

    def test_get_framework_by_prog_name(self):
        """Framework index returns matching framework"""
        framework = self.categoryA.frameworks["framework-a"]
        self.assertEqual(framework.name, "Framework A")

    def test_get_category_not_existing(self):
        """the call to get category returns None when there is no match"""
        self.assertIsNone(self.CategoryHandler.categories["foo"])

    def test_get_category_prog_name(self):
        """prog_name for category is what we expect"""
        self.assertEqual(self.categoryA.prog_name, "category-a")
        self.assertEqual(self.CategoryHandler.categories["category-b"].prog_name, "category-b")

    def test_multiple_files_loaded(self):
        """We load multiple categories in different files"""
        # main category, + at least 2 other categories
        self.assertTrue(len(self.CategoryHandler.categories) > 2, str(self.CategoryHandler.categories))
        self.assertIsNotNone(self.categoryA)
        self.assertIsNotNone(self.CategoryHandler.categories["category-b"])

    def test_frameworks_loaded(self):
        """We have frameworks attached to a category"""
        self.assertTrue(len(self.categoryA.frameworks) > 1, str(self.categoryA.frameworks))
        self.assertTrue(self.categoryA.has_frameworks())

    def test_framework_not_existing(self):
        """the call  to get a framework returns None when there is no match"""
        self.assertIsNone(self.categoryA.frameworks["foo"])

    def test_frameworks_doesn_t_mix(self):
        """Frameworks, even with the same name, don't mix between categories"""
        self.assertNotEqual(self.categoryA.frameworks["framework-a"],
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
        self.assertEqual(self.categoryA.frameworks["framework-a"].prog_name, "framework-a")
        self.assertEqual(self.categoryA.frameworks["framework-b"].prog_name, "framework-b")

    def test_nothing_installed(self):
        """Category returns that no framework is installed"""
        self.assertEqual(self.categoryA.is_installed, self.CategoryHandler.NOT_INSTALLED)

    def test_category_fully_installed(self):
        """Category returns than all frameworks are installed"""
        self.assertEqual(self.CategoryHandler.categories["category-b"].is_installed,
                         self.CategoryHandler.FULLY_INSTALLED)

    def test_category_half_installed(self):
        """Category returns than half frameworks are installed"""
        self.assertEqual(self.CategoryHandler.categories["category-c"].is_installed,
                         self.CategoryHandler.PARTIALLY_INSTALLED)

    def test_frameworks_loaded_in_main_category(self):
        """Some frameworks are loaded and attached to main category"""
        self.assertTrue(len(self.CategoryHandler.main_category.frameworks) > 1,
                        str(self.CategoryHandler.main_category.frameworks))
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
        self.assertEqual(self.categoryA.default_framework, framework_default)

    def test_default_install_path(self):
        """Default install path is what we expect, based on category-and framework prog_name"""
        self.assertEqual(self.categoryA.frameworks["framework-b"].install_path,
                         os.path.expanduser("~/tools/category-a/framework-b"))

    def test_specified_at_load_install_path(self):
        """Default install path is overriden by framework specified install path at load time"""
        self.assertEqual(self.categoryA.frameworks["framework-a"].install_path,
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
        args.destdir = None
        args.framework = "framework-b"
        args.remove = False
        with patch.object(self.CategoryHandler.categories[args.category].frameworks["framework-b"], "setup")\
                as setup_call:
            self.CategoryHandler.categories[args.category].run_for(args)

            self.assertTrue(setup_call.called)
            self.assertEqual(setup_call.call_args, call(args.destdir))

    def test_parse_no_framework_run_default_for_category(self):
        """Parsing category will run default framework"""
        args = Mock()
        args.category = "category-a"
        args.destdir = None
        args.framework = None
        args.remove = False
        with patch.object(self.CategoryHandler.categories[args.category].frameworks["framework-a"], "setup")\
                as setup_call:
            self.CategoryHandler.categories[args.category].run_for(args)

            self.assertTrue(setup_call.called)
            self.assertEqual(setup_call.call_args, call(args.destdir))

    def test_parse_category_and_framework_run_correct_remove_framework(self):
        """Parsing category and frameworkwwith --remove run remove on right category and framework"""
        args = Mock()
        args.category = "category-a"
        args.destdir = None
        args.framework = "framework-b"
        args.remove = True
        with patch.object(self.CategoryHandler.categories[args.category].frameworks["framework-b"], "remove")\
                as remove_call:
            self.CategoryHandler.categories[args.category].run_for(args)

            self.assertTrue(remove_call.called)
            remove_call.assert_called_with()

    def test_parse_no_framework_run_default_remove_for_category(self):
        """Parsing category with --remove will run default framework removal action"""
        args = Mock()
        args.category = "category-a"
        args.framework = None
        args.remove = True
        args.destdir = None
        with patch.object(self.CategoryHandler.categories[args.category].frameworks["framework-a"], "remove")\
                as remove_call:
            self.CategoryHandler.categories[args.category].run_for(args)

            self.assertTrue(remove_call.called)
            remove_call.assert_called_with()

    def test_parse_no_framework_with_no_default_returns_errors(self):
        """Parsing a category with no default returns an error when calling run"""
        args = Mock()
        args.category = "category-b"
        args.framework = None
        args.remove = False
        self.assertRaises(BaseException, self.CategoryHandler.categories[args.category].run_for, args)
        self.expect_warn_error = True

    def test_parse_category_and_framework_cannot_run_remove_with_destdir_framework(self):
        """Parsing category and framework with remove and destdir raises an error"""
        args = Mock()
        args.category = "category-a"
        args.framework = "framework-b"
        args.remove = True
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
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]

    def tearDown(self):
        change_xdg_path('XDG_CONFIG_HOME', remove=True)
        super().tearDown()

    def test_config_override_defaults(self):
        """Configuration override defaults (explicit or implicit). If not present in config, still load default"""
        # was overridden with at load time
        self.assertEqual(self.categoryA.frameworks["framework-a"].install_path,
                         "/home/didrocks/quickly/ubuntu-make/adt-eclipse")
        # was default
        self.assertEqual(self.categoryA.frameworks["framework-b"].install_path,
                         "/home/didrocks/foo/bar/android-studio")
        # isn't in the config
        self.assertEqual(self.CategoryHandler.categories['category-c'].frameworks["framework-a"].install_path,
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
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]
        self.config_dir = tempfile.mkdtemp()
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir)

    def tearDown(self):
        change_xdg_path('XDG_CONFIG_HOME', remove=True)
        shutil.rmtree(self.config_dir)
        super().tearDown()

    def test_call_mark_in_config_save_config(self):
        """Calling mark_in_config save path in the configuration"""
        # load custom framework-directory
        self.categoryA.frameworks["framework-b"].mark_in_config()

        self.assertEqual(ConfigHandler().config,
                         {'frameworks': {
                             'category-a': {
                                 'framework-b': {'path': os.path.expanduser('~/tools/category-a/framework-b')}
                             }}})

    def test_call_setup_save_and_then_mark_in_config_tweaked_path(self):
        """Calling mark_in_config with a custom install path save it in the configuration"""
        # load custom framework-directory
        fw = self.categoryA.frameworks["framework-b"]
        fw.setup()
        fw.install_path = "/home/foo/bar"
        self.categoryA.frameworks["framework-b"].mark_in_config()

        self.assertEqual(ConfigHandler().config,
                         {'frameworks': {
                             'category-a': {
                                 'framework-b': {'path': '/home/foo/bar'}
                             }}})

    def test_call_remove_from_config(self):
        """Calling remove_from_config remove a framework from the config"""
        ConfigHandler().config = {'frameworks': {
            'category-a': {
                'framework-b': {'path': os.path.expanduser('~/tools/category-a/framework-b')}
            }}}
        self.categoryA.frameworks["framework-b"].remove_from_config()

        self.assertEqual(ConfigHandler().config, {'frameworks': {'category-a': {}}})

    def test_call_remove_from_config_keep_other(self):
        """Calling remove_from_config remove a framework from the config but keep others"""
        ConfigHandler().config = {'frameworks': {
            'category-a': {
                'framework-b': {'path': os.path.expanduser('~/tools/category-a/framework-b')},
                'framework-c': {'path': os.path.expanduser('~/tools/category-a/framework-c')}
            },
            'category-b': {
                'framework-b': {'path': os.path.expanduser('~/tools/category-a/framework-b')}
            }}}
        self.categoryA.frameworks["framework-b"].remove_from_config()

        self.assertEqual(ConfigHandler().config,
                         {'frameworks': {
                             'category-a': {
                                 'framework-c': {'path': os.path.expanduser('~/tools/category-a/framework-c')}
                             },
                             'category-b': {
                                 'framework-b': {'path': os.path.expanduser('~/tools/category-a/framework-b')}
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
        self.restore_arch_version()
        super().tearDown()

    def loadFramework(self, framework_name):
        """Load framework name"""
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', framework_name):
            frameworks.load_frameworks()

    def install_category_parser(self, main_parser, categories=[]):
        """Install parser for those categories"""
        categories_parser = main_parser.add_subparsers(dest="category")
        category_parsers = []
        for category in categories:
            with patch('umake.frameworks.is_completion_mode') as completionmode_mock:
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
        with patch('umake.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = False
            self.loadFramework("testframeworks")
            self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].is_installed)
            requirement_mock.return_value.is_bucket_installed.assert_called_with(['foo', 'bar'])
            # is_bucket_available is called when it's not installed
            requirement_mock.return_value.is_bucket_available.assert_any_calls(call(['foo', 'bar']))

    def test_check_installed_with_matched_requirements(self):
        """Framework is installed if path and package requirements are met"""
        with patch('umake.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = True
            self.loadFramework("testframeworks")
            self.assertTrue(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].is_installed)
            requirement_mock.return_value.is_bucket_installed.assert_called_with(['foo', 'bar'])
            # we don't call is_bucket_available if requirements are met
            self.assertFalse(call(['foo', 'bar']) in requirement_mock.return_value.is_bucket_available.call_args_list)

    def test_check_requirements_inherited_from_category(self):
        """Framework without package requirements are inherited from category"""
        with patch('umake.frameworks.RequirementsHandler') as requirement_mock:
            self.loadFramework("testframeworks")
            self.assertEqual(self.CategoryHandler.categories["category-g"].frameworks["framework-b"]
                             .packages_requirements, ["baz"])

    def test_check_requirements_from_category_merge_into_exiting(self):
        """Framework with package requirements merged them from the associated category"""
        with patch('umake.frameworks.RequirementsHandler') as requirement_mock:
            self.loadFramework("testframeworks")
            self.assertEqual(self.CategoryHandler.categories["category-g"].frameworks["framework-a"]
                             .packages_requirements, ["buz", "biz", "baz"])

    def test_root_needed_if_not_matched_requirements(self):
        """Framework with unmatched requirements need root access"""
        with patch('umake.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = False
            self.loadFramework("testframeworks")
            self.assertTrue(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].need_root_access)

    def test_no_root_needed_if_matched_requirements_even_uninstalled(self):
        """Framework which are uninstalled but with matched requirements doesn't need root access"""
        with patch('umake.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = True
            self.loadFramework("testframeworks")
            # ensure the framework isn't installed, but the bucket being installed, we don't need root access
            self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-a"].is_installed)
            self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-a"].need_root_access)

    def test_root_needed_setup_call_root(self):
        """Framework with root access needed call sudo"""
        with patch('umake.frameworks.subprocess') as subprocess_mock,\
                patch.object(umake.frameworks.os, 'geteuid', return_value=1000) as geteuid,\
                patch('umake.frameworks.MainLoop') as mainloop_mock,\
                patch('umake.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = False
            self.loadFramework("testframeworks")
            self.assertTrue(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].need_root_access)
            self.CategoryHandler.categories["category-f"].frameworks["framework-c"].setup()

            self.assertEqual(subprocess_mock.call.call_args[0][0][0], "sudo")
            self.assertTrue(mainloop_mock.return_value.quit.called)

    def test_no_root_needed_setup_doesnt_call_root(self):
        """Framework without root access needed don't call sudo"""
        with patch('umake.frameworks.subprocess') as subprocess_mock,\
                patch.object(umake.frameworks.os, 'geteuid', return_value=1000) as geteuid,\
                patch.object(umake.frameworks.sys, 'exit', return_value=True) as sys_exit_mock,\
                patch('umake.frameworks.RequirementsHandler') as requirement_mock:
            requirement_mock.return_value.is_bucket_installed.return_value = True
            self.loadFramework("testframeworks")
            self.assertFalse(self.CategoryHandler.categories["category-f"].frameworks["framework-c"].need_root_access)
            self.CategoryHandler.categories["category-f"].frameworks["framework-c"].setup()

            self.assertFalse(subprocess_mock.call.called)
            self.assertFalse(sys_exit_mock.called)

    def test_root_needed_setup_doesnt_call_root(self):
        """setup doesn't call sudo if we are already root"""
        with patch('umake.frameworks.subprocess') as subprocess_mock,\
                patch.object(umake.frameworks.sys, 'exit', return_value=True) as sys_exit_mock,\
                patch.object(umake.frameworks.os, 'geteuid', return_value=0) as geteuid,\
                patch('umake.frameworks.RequirementsHandler') as requirement_mock,\
                patch('umake.frameworks.switch_to_current_user') as switch_to_current_use_mock:
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
        with patch('umake.frameworks.ConfigHandler') as config_handler_mock,\
                patch('umake.frameworks.RequirementsHandler') as requirementhandler_mock,\
                patch('umake.frameworks.is_completion_mode') as completionmode_mock:
            completionmode_mock.return_value = True
            self.loadFramework("testframeworks")

            self.assertTrue(completionmode_mock.called)
            self.assertFalse(len(config_handler_mock.return_value.config.mock_calls) > 0,
                             str(config_handler_mock.return_value.config.mock_calls))
            self.assertFalse(requirementhandler_mock.return_value.is_bucket_installed.called)
            # test that a non installed framework is registered
            self.assertIsNotNone(self.CategoryHandler.categories["category-e"].frameworks["framework-c"])

    def test_use_expensive_calls_when_not_in_completion_mode(self):
        """Non completion mode have expensive calls and don't register all frameworks"""
        with patch('umake.frameworks.ConfigHandler') as config_handler_mock,\
                patch('umake.frameworks.RequirementsHandler') as requirementhandler_mock,\
                patch('umake.frameworks.is_completion_mode') as completionmode_mock:
            completionmode_mock.return_value = False
            self.loadFramework("testframeworks")

            self.assertTrue(completionmode_mock.called)
            self.assertTrue(len(config_handler_mock.return_value.config.mock_calls) > 0,
                            str(config_handler_mock.return_value.config.mock_calls))
            self.assertTrue(requirementhandler_mock.return_value.is_bucket_installed.called)
            # test that a non installed framework is registered
            self.assertIsNone(self.CategoryHandler.categories["category-e"].frameworks["framework-c"])

    def test_install_category_and_framework_parsers(self):
        """Install category and framework parsers contains works"""
        main_parser = argparse.ArgumentParser()
        categories_parser = main_parser.add_subparsers()
        with patch('umake.frameworks.is_completion_mode') as completionmode_mock:
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
        self.assertEqual(args.category, "category-a")
        self.assertEqual(args.framework, "framework-a")
        self.assertEqual(args.destdir, None)

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
        self.assertEqual(main_parser.parse_args([]), argparse.Namespace(category=None))

    def test_install_category_with_no_framework(self):
        """Install category with no framework returns None"""
        main_parser = argparse.ArgumentParser()
        self.assertEqual(self.install_category_parser(main_parser, ['empty-category']), [None])

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
        self.assertEqual(args.category, "framework-free-a")
        self.assertEqual(args.destdir, None)
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
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworksdoesntexist"):
            frameworks.load_frameworks()

    def test_invalid_framework(self):
        """There is one main category, but nothing else"""
        main_category = [category for category in self.CategoryHandler.categories.values()
                         if category.is_main_category][0]
        self.assertEqual(self.CategoryHandler.main_category, main_category)
        self.assertEqual(len(self.CategoryHandler.categories), 1, str(self.CategoryHandler.categories))


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
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "duplicatedframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]
        self.expect_warn_error = True  # as we load multiple duplicate categories and frameworks

    def test_duplicated_categories(self):
        """We only load one category when a second with same name is met"""
        # main + categoryA
        self.assertEqual(len(self.CategoryHandler.categories), 2, str(self.CategoryHandler.categories))
        self.assertEqual(self.CategoryHandler.categories["category-a"].name, "Category A")

    def test_duplicated_frameworks(self):
        """We only load one framework when a second with the same name is met"""
        self.assertEqual(len(self.categoryA.frameworks), 1, str(self.categoryA.frameworks))

    def test_main_category_empty(self):
        """The main category (unused here) is empty by default"""
        self.assertEqual(len(self.CategoryHandler.main_category.frameworks), 0,
                         str(self.CategoryHandler.main_category.frameworks))


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
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "multipledefaultsframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]
        self.expect_warn_error = True  # as we load multiple default frameworks in a category

    def test_multiple_defaults(self):
        """Setting multiple defaults frameworks to a category should void any default"""
        self.assertIsNone(self.categoryA.default_framework)
        self.assertEqual(len(self.categoryA.frameworks), 2,
                         str(self.categoryA.frameworks))  # ensure they are still loaded

    def test_one_default_in_main_category(self):
        """Reject default framework for main category"""
        self.assertIsNone(self.CategoryHandler.main_category.default_framework)
        self.assertEqual(len(self.CategoryHandler.main_category.frameworks), 1,
                         str(self.CategoryHandler.main_category.frameworks))  # ensure it's still loaded


class TestNotLoadedFrameworkLoader(BaseFrameworkLoader):

    def setUp(self):
        super().setUp()
        self.CategoryHandler = frameworks.BaseCategory

    def test_get_no_main_category(self):
        """main_category returns None when there is no main category"""
        self.assertIsNone(self.CategoryHandler.main_category)

    def test_get_with_no_category(self):
        """categories is empty when there is no category loaded"""
        self.assertEqual(len(self.CategoryHandler.categories), 0, str(self.CategoryHandler.categories))


class TestAbstractFrameworkLoader(BaseFrameworkLoader):
    """Test the loader skips abstract frameworks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.append(get_data_dir())
        cls.testframeworks_dir = os.path.join(get_data_dir(), 'abstractframeworks')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove(get_data_dir())
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        # load custom unexisting framework-directory
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "abstractframeworks"):
            frameworks.load_frameworks()
        self.categoryA = self.CategoryHandler.categories["category-a"]

    def test_load(self):
        """Previous loading should have been successful"""
        self.assertFalse(self.categoryA.has_frameworks())
        self.expect_warn_error = False  # Should be silent.


class TestFrameworkLoaderCustom(BaseFrameworkLoader):
    """This will test the dynamic framework loader activity with custom path"""

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
        self.dirs_to_remove = []

    def tearDown(self):
        self.restore_arch_version()
        with suppress(KeyError):
            os.environ.pop(UMAKE_FRAMEWORKS_ENVIRON_VARIABLE)
        for path in self.dirs_to_remove:
            sys.path.remove(path)
            with suppress(FileNotFoundError):
                shutil.rmtree(path)
            with suppress(ValueError):
                sys.path.remove(path)
        super().tearDown()

    @patch("umake.frameworks.get_user_frameworks_path")
    def test_load_additional_frameworks_in_home_dir(self, get_user_frameworks_path):
        """Ensure we load additional frameworks from home directory"""
        temp_path = tempfile.mkdtemp()
        self.dirs_to_remove.append(temp_path)
        shutil.copy(os.path.join(get_data_dir(), "overlayframeworks", "overlayframeworks.py"), temp_path)
        get_user_frameworks_path.return_value = temp_path
        # load home framework-directory
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()

        # ensure that the overlay is loaded
        self.assertEqual(self.CategoryHandler.categories["category-a-overlay"].name, "Category A overlay")
        # ensure that the other frameworks are still loaded
        self.assertEqual(self.CategoryHandler.categories["category-a"].name, "Category A")

    def test_load_additional_frameworks_with_env_var(self):
        """Ensure we load additional frameworks set in an environment variable"""
        temp_path = tempfile.mkdtemp()
        self.dirs_to_remove.append(temp_path)
        os.environ[UMAKE_FRAMEWORKS_ENVIRON_VARIABLE] = temp_path
        shutil.copy(os.path.join(get_data_dir(), "overlayframeworks", "overlayframeworks.py"), temp_path)
        # load env framework-directory
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()

        # ensure that the overlay is loaded
        self.assertEqual(self.CategoryHandler.categories["category-a-overlay"].name, "Category A overlay")
        # ensure that the other frameworks are still loaded
        self.assertEqual(self.CategoryHandler.categories["category-a"].name, "Category A")

    @patch("umake.frameworks.get_user_frameworks_path")
    def test_load_additional_frameworks_with_two_categories(self, get_user_frameworks_path):
        """Ensure we load additional frameworks in a path with two categories"""
        temp_path = tempfile.mkdtemp()
        self.dirs_to_remove.append(temp_path)
        shutil.copy(os.path.join(get_data_dir(), "overlayframeworks", "overlayframeworks.py"), temp_path)
        shutil.copy(os.path.join(get_data_dir(), "overlayframeworks", "withcategory2.py"), temp_path)
        get_user_frameworks_path.return_value = temp_path
        # load home framework-directory
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()

        # ensure that both overlay are loaded
        self.assertEqual(self.CategoryHandler.categories["category-a-overlay"].name, "Category A overlay")
        self.assertEqual(self.CategoryHandler.categories["category-a2-overlay"].name, "Category A2 overlay")
        # ensure that the other frameworks are still loaded
        self.assertEqual(self.CategoryHandler.categories["category-a"].name, "Category A")

    @patch("umake.frameworks.get_user_frameworks_path")
    def test_load_additional_frameworks_with_same_filename(self, get_user_frameworks_path):
        """Ensure we load additional frameworks in a path with same filename"""
        temp_path = tempfile.mkdtemp()
        self.dirs_to_remove.append(temp_path)
        shutil.copy(os.path.join(get_data_dir(), "overlayframeworks", "withcategory.py"), temp_path)
        get_user_frameworks_path.return_value = temp_path
        # load home framework-directory
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()

        # ensure that the duplicated filename (but not category) is loaded
        self.assertEqual(self.CategoryHandler.categories["category-a-overlay"].name, "Category A overlay")
        # ensure that the other frameworks with the same name is still loaded
        self.assertEqual(self.CategoryHandler.categories["category-a"].name, "Category A")

    @patch("umake.frameworks.get_user_frameworks_path")
    def test_load_additional_frameworks_with_duphome_before_system(self, get_user_frameworks_path):
        """Ensure we load additional frameworks from home before system if they have the same names"""
        temp_path = tempfile.mkdtemp()
        self.dirs_to_remove.append(temp_path)
        shutil.copy(os.path.join(get_data_dir(), "overlayframeworks", "duplicatedcategory.py"), temp_path)
        get_user_frameworks_path.return_value = temp_path
        # load home framework-directory
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()

        # ensure that the overlay one is loaded
        categoryA = self.CategoryHandler.categories["category-a"]
        self.assertEqual(categoryA.name, "Category A")
        self.assertEqual(categoryA.frameworks["framework-a-from-overlay"].name, "Framework A from overlay")
        # ensure that the other frameworks are still loaded
        self.assertEqual(self.CategoryHandler.categories["category-b"].name, "Category/B")
        self.expect_warn_error = True  # expect warning due to duplication

    @patch("umake.frameworks.get_user_frameworks_path")
    def test_load_additional_frameworks_with_dup_progname_env_before_home_before_system(self, get_user_frameworks_path):
        """Ensure we load additional frameworks from env before home and system if they have the same names"""
        # env var
        temp_path = tempfile.mkdtemp()
        self.dirs_to_remove.append(temp_path)
        os.environ[UMAKE_FRAMEWORKS_ENVIRON_VARIABLE] = temp_path
        shutil.copy(os.path.join(get_data_dir(), "overlayframeworks", "duplicatedcategory2.py"), temp_path)
        # home dir
        temp_path = tempfile.mkdtemp()
        self.dirs_to_remove.append(temp_path)
        shutil.copy(os.path.join(get_data_dir(), "overlayframeworks", "duplicatedcategory.py"), temp_path)
        get_user_frameworks_path.return_value = temp_path
        # load env and home framework-directory
        with patchelem(umake.frameworks, '__file__', os.path.join(self.testframeworks_dir, '__init__.py')),\
                patchelem(umake.frameworks, '__package__', "testframeworks"):
            frameworks.load_frameworks()

        # ensure that the env overlay one is loaded
        categoryA = self.CategoryHandler.categories["category-a"]
        self.assertEqual(categoryA.name, "Category A")
        self.assertEqual(categoryA.frameworks["framework-a-from-overlay-2"].name, "Framework A from overlay 2")
        # ensure that the other frameworks are still loaded
        self.assertEqual(self.CategoryHandler.categories["category-b"].name, "Category/B")
        self.expect_warn_error = True  # expect warning due to duplication


class TestProductionFrameworkLoader(BaseFrameworkLoader):
    """Load production framework-and ensure there is no warning and no error"""

    def test_load_android(self):
        """Can load production frameworks"""
        frameworks.load_frameworks()
        self.assertTrue(len(self.CategoryHandler.categories) > 0, str(self.CategoryHandler.categories))
        self.assertIsNotNone(self.CategoryHandler.main_category)
        self.assertEqual(len(self.CategoryHandler.categories["android"].frameworks), 2,
                         str(self.CategoryHandler.categories["android"].frameworks))

    def test_ignored_frameworks(self):
        """Ignored frameworks aren't loaded"""
        frameworks.load_frameworks()
        self.assertNotIn(BaseInstaller, frameworks.BaseCategory.main_category.frameworks.values())


class TestCustomFrameworkCantLoad(BaseFrameworkLoader):
    """Get custom unloadable automatically frameworks to test custom corner cases"""

    class _CustomFramework(umake.frameworks.BaseFramework):

        def __init__(self):
            super().__init__(name="Custom", description="Custom uninstallable framework",
                             category=umake.frameworks.MainCategory())

        def setup(self):
            super().setup()

        def remove(self):
            super().remove()

        @property
        def is_installable(self):
            return False

    def test_call_setup_on_uninstallable_framework(self):
        """Calling setup on uninstallable framework return to main UI"""
        fw = self._CustomFramework()
        with patch("umake.frameworks.UI") as UIMock:
            fw.setup()
            self.assertTrue(UIMock.return_main_screen.called)
        self.expect_warn_error = True
