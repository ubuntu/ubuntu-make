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

"""Tests the various udtc tools"""

from contextlib import suppress
import os
import shutil
import subprocess
import stat
import sys
import tempfile
from ..tools import change_xdg_config_path, get_data_dir, LoggedTestCase
from udtc import settings, tools
from udtc.tools import ConfigHandler, Singleton, get_current_arch, get_current_ubuntu_version
from unittest.mock import patch


class TestConfigHandler(LoggedTestCase):
    """This will test the config handler using xdg dirs"""

    def tearDown(self):
        # remove caching
        Singleton._instances = {}
        with suppress(KeyError):
            os.environ.pop('XDG_CONFIG_HOME')
        super().tearDown()

    def config_dir_for_name(self, name):
        """Return the config dir for this name"""
        return os.path.join(get_data_dir(), 'configs', name)

    def test_singleton(self):
        """Ensure we are delivering a singleton for TestConfigHandler"""
        config1 = ConfigHandler()
        config2 = ConfigHandler()
        self.assertEquals(config1, config2)

    def test_load_config(self):
        """Valid config loads correct content"""
        change_xdg_config_path(self.config_dir_for_name("valid"))
        self.assertEquals(ConfigHandler().config,
                          {'frameworks': {
                              'Category A': {
                                  'Framework A': {'path': '/home/didrocks/quickly/ubuntu-developer-tools/adt-eclipse'},
                                  'Framework/B': {'path': '/home/didrocks/foo/bar/android-studio'}
                              }
                          }})

    def test_load_no_config(self):
        """No existing file gives an empty result"""
        change_xdg_config_path(self.config_dir_for_name("foo"))
        self.assertEquals(ConfigHandler().config, {})

    def test_load_invalid_config(self):
        """Existing invalid file gives an empty result"""
        change_xdg_config_path(self.config_dir_for_name("invalid"))
        self.assertEquals(ConfigHandler().config, {})
        self.expect_warn_error = True

    def test_save_new_config(self):
        """Save a new config in a vanilla directory"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            change_xdg_config_path(tmpdirname)
            content = {'foo': 'bar'}
            ConfigHandler().config = content

            self.assertEquals(ConfigHandler().config, content)
            with open(os.path.join(tmpdirname, settings.CONFIG_FILENAME)) as f:
                self.assertEquals(f.read(), 'foo: bar\n')

    def test_save_config_existing(self):
        """Replace an existing config with a new one"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            change_xdg_config_path(tmpdirname)
            shutil.copy(os.path.join(self.config_dir_for_name('valid'), settings.CONFIG_FILENAME), tmpdirname)
            content = {'foo': 'bar'}
            ConfigHandler().config = content

            self.assertEquals(ConfigHandler().config, content)
            with open(os.path.join(tmpdirname, settings.CONFIG_FILENAME)) as f:
                self.assertEquals(f.read(), 'foo: bar\n')

    def test_dont_create_file_without_assignment(self):
        """We don't create any file without an assignment"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            change_xdg_config_path(tmpdirname)
            ConfigHandler()

            self.assertEquals(len(os.listdir(tmpdirname)), 0)

class TestTools(LoggedTestCase):

    def tearDown(self):
        """Reset cached values"""
        tools._current_arch = None
        tools._version = None

    def get_lsb_release_filepath(self, name):
        return os.path.join(get_data_dir(), 'lsb_releases', name)

    def local_current_arch(self):
        return subprocess.check_output(["dpkg", "--print-architecture"], universal_newlines=True).rstrip("\n")

    def test_get_current_arch(self):
        """Current arch is reported"""
        self.assertEquals(get_current_arch(), self.local_current_arch())

    def test_get_current_arch_twice(self):
        """Current arch is reported twice and the same"""
        current_arch = self.local_current_arch()
        self.assertEquals(get_current_arch(), current_arch)
        self.assertEquals(get_current_arch(), current_arch)

    def test_get_current_arch_no_dpkg(self):
        """Assert an error if dpkg exit with an error"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            sys.path.insert(0, tmpdirname)
            dpkg_file_path = os.path.join(tmpdirname, "dpkg")
            with open(dpkg_file_path, mode='w') as f:
                f.write("#!/bin/sh\nexit 1")  # Simulate an error in dpkg
            os.environ['PATH'] = '{}:{}'.format(tmpdirname, os.getenv('PATH'))
            st = os.stat(dpkg_file_path)
            os.chmod(dpkg_file_path, st.st_mode | stat.S_IEXEC)
            self.assertRaises(subprocess.CalledProcessError, get_current_arch)
        sys.path.remove(tmpdirname)

    @patch("udtc.tools.settings")
    def test_get_current_ubuntu_version(self, settings_module):
        """Current ubuntu version is reported from our lsb_release local file"""
        settings_module.LSB_RELEASE_FILE = self.get_lsb_release_filepath("valid")
        self.assertEquals(get_current_ubuntu_version(), '14.04')

    @patch("udtc.tools.settings")
    def test_get_current_ubuntu_version_invalid(self, settings_module):
        """Raise an error when parsing an invalid lsb release file"""
        settings_module.LSB_RELEASE_FILE = self.get_lsb_release_filepath("invalid")
        self.assertRaises(BaseException, get_current_ubuntu_version)
        self.expect_warn_error = True

    @patch("udtc.tools.settings")
    def test_get_current_ubuntu_version_no_lsb_release(self, settings_module):
        """Raise an error when there is no lsb release file"""
        settings_module.LSB_RELEASE_FILE = self.get_lsb_release_filepath("notexist")
        self.assertRaises(BaseException, get_current_ubuntu_version)
        self.expect_warn_error = True
