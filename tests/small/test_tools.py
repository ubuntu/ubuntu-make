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
import tempfile
from ..tools import change_xdg_config_path, get_data_dir, LoggedTestCase
from udtc import settings
from udtc.tools import ConfigHandler, Singleton


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
