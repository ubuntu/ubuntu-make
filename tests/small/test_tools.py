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

import importlib
import os
import shutil
import tempfile
from ..tools import get_data_dir
from unittest import TestCase
import udtc
from udtc import settings
from udtc.tools import ConfigHandler, Singleton
import xdg.BaseDirectory


class TestConfigHandler(TestCase):
    """This will test the config handler using xdg dirs"""

    def tearDown(self):
        # remove caching
        Singleton._instances = {}
        try:
            os.environ.pop('XDG_CONFIG_HOME')
        except KeyError:
            pass

    def install_config_dir(self, name):
        """Set this config directory to xdg variables"""
        os.environ['XDG_CONFIG_HOME'] = os.path.join(get_data_dir(), 'configs', name)
        importlib.reload(xdg.BaseDirectory)

    def test_singleton(self):
        """Ensure we are delivering a singleton for TestConfigHandler"""
        config1 = ConfigHandler()
        config2 = ConfigHandler()
        self.assertEquals(config1, config2)

    def test_load_config(self):
        """Valid config loads correct content"""
        self.install_config_dir("valid")
        self.assertEquals(ConfigHandler().config,
                          {'frameworks': {
                              'Android': {
                                  'ADT': {'path': '/home/didrocks/tools/android/adt-eclipse'},
                                  'Android Studio': {'path': '/home/didrocks/foo/bar/android'}
                              }
                          }})

    def test_load_no_config(self):
        """No existing file gives an empty result"""
        self.install_config_dir("foo")
        self.assertIsNone(ConfigHandler().config)

    def test_load_invalid_config(self):
        """Existing invalid file gives an empty result"""
        self.install_config_dir("invalid")
        self.assertIsNone(ConfigHandler().config)

    def test_save_new_config(self):
        """Save a new config in a vanilla directory"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.environ['XDG_CONFIG_HOME'] = tmpdirname
            importlib.reload(xdg.BaseDirectory)
            udtc.tools.xdg_config_home = xdg.BaseDirectory.xdg_config_home
            content = {'foo': 'bar'}
            ConfigHandler().config = content

            self.assertEquals(ConfigHandler().config, content)
            with open(os.path.join(tmpdirname, settings.CONFIG_FILENAME)) as f:
                self.assertEquals(f.read(), 'foo: bar\n')

    def test_save_config_existing(self):
        """Replace an existing config with a new one"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            os.environ['XDG_CONFIG_HOME'] = tmpdirname
            importlib.reload(xdg.BaseDirectory)
            udtc.tools.xdg_config_home = xdg.BaseDirectory.xdg_config_home
            shutil.copy(os.path.join(get_data_dir(), 'configs', 'valid', settings.CONFIG_FILENAME), tmpdirname)
            content = {'foo': 'bar'}
            ConfigHandler().config = content

            self.assertEquals(ConfigHandler().config, content)
            with open(os.path.join(tmpdirname, settings.CONFIG_FILENAME)) as f:
                self.assertEquals(f.read(), 'foo: bar\n')
