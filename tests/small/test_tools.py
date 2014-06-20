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

from gi.repository import GLib, GObject
from concurrent import futures
from contextlib import suppress
import os
import shutil
import subprocess
import stat
import sys
import tempfile
from time import time
import threading
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
        super().tearDown()

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


class TestToolsThreads(LoggedTestCase):
    """Test main loop threading helpers"""

    def setUp(self):
        super().setUp()
        self.mainloop = None
        self.mainloop_thread = None
        self.function_thread = None
        self.parallel_function_thread = None

    # function that will complete once the mainloop is started
    def wait_for_mainloop_function(self):
        self.parallel_function_thread = threading.current_thread().ident
        timeout_time = time() + 5
        while not self.mainloop or not self.mainloop.is_running():
            if time() > timeout_time:
                raise(BaseException("Mainloop not started in 5 seconds"))

    def get_mainloop_thread(self):
        self.mainloop_thread = threading.current_thread().ident

    def start_glib_mainloop(self):
        GObject.threads_init()
        self.mainloop = GLib.MainLoop()
        # quit after 5 seconds if nothing made the mainloop to end
        GLib.timeout_add_seconds(5, self.mainloop.quit)
        GLib.idle_add(self.get_mainloop_thread)
        self.mainloop.run()

    def test_run_function_in_mainloop_thread(self):
        """Test that decorated mainloop thread functions are really running in that thread"""

        # function supposed to run in the mainloop thread
        @tools.in_mainloop_thread
        def _function_in_mainloop_thread(future):
            self.function_thread = threading.current_thread().ident
            self.mainloop.quit()

        executor = futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.wait_for_mainloop_function)
        future.add_done_callback(_function_in_mainloop_thread)
        self.start_glib_mainloop()

        # mainloop and thread were started
        self.assertIsNotNone(self.mainloop_thread)
        self.assertIsNotNone(self.parallel_function_thread)
        self.assertEquals(self.mainloop_thread, self.function_thread)
        self.assertNotEquals(self.mainloop_thread, self.parallel_function_thread)

    def test_run_function_not_in_mainloop_thread(self):
        """Test that non decorated callback functions are not running in the mainloop thread"""

        # function not supposed to run in the mainloop thread
        def _function_not_in_mainloop_thread(future):
            self.function_thread = threading.current_thread().ident
            self.mainloop.quit()

        executor = futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.wait_for_mainloop_function)
        future.add_done_callback(_function_not_in_mainloop_thread)
        self.start_glib_mainloop()

        # mainloop and thread were started
        self.assertIsNotNone(self.mainloop_thread)
        self.assertIsNotNone(self.parallel_function_thread)
        self.assertNotEquals(self.mainloop_thread, self.function_thread)
        self.assertNotEquals(self.mainloop_thread, self.parallel_function_thread)
        # the function parallel thread id was reused
        self.assertEquals(self.function_thread, self.parallel_function_thread)
