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
# This program is distributed in he hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""Tests the various udtc tools"""

from concurrent import futures
from contextlib import contextmanager, suppress
from gi.repository import GLib
import os
import shutil
import subprocess
import stat
import sys
import tempfile
from textwrap import dedent
from time import time
import threading
from ..tools import change_xdg_path, get_data_dir, LoggedTestCase
from udtc import settings, tools
from udtc.tools import ConfigHandler, Singleton, get_current_arch, get_foreign_archs, get_current_ubuntu_version,\
    create_launcher, launcher_exists_and_is_pinned, launcher_exists, get_icon_path, get_launcher_path, copy_icon
from unittest.mock import patch


class TestConfigHandler(LoggedTestCase):
    """This will test the config handler using xdg dirs"""

    def setUp(self):
        super().setUp()
        self.config_dir = tempfile.mkdtemp()
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir)

    def tearDown(self):
        # remove caching
        Singleton._instances = {}
        change_xdg_path('XDG_CONFIG_HOME', remove=True)
        shutil.rmtree(self.config_dir)
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
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir_for_name("valid"))
        self.assertEquals(ConfigHandler().config,
                          {'frameworks': {
                              'category-a': {
                                  'framework-a': {'path': '/home/didrocks/quickly/ubuntu-developer-tools/adt-eclipse'},
                                  'framework-b': {'path': '/home/didrocks/foo/bar/android-studio'}
                              }
                          }})

    def test_load_no_config(self):
        """No existing file gives an empty result"""
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir_for_name("foo"))
        self.assertEquals(ConfigHandler().config, {})

    def test_load_invalid_config(self):
        """Existing invalid file gives an empty result"""
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir_for_name("invalid"))
        self.assertEquals(ConfigHandler().config, {})
        self.expect_warn_error = True

    def test_save_new_config(self):
        """Save a new config in a vanilla directory"""
        content = {'foo': 'bar'}
        ConfigHandler().config = content

        self.assertEquals(ConfigHandler().config, content)
        with open(os.path.join(self.config_dir, settings.CONFIG_FILENAME)) as f:
            self.assertEquals(f.read(), 'foo: bar\n')

    def test_save_config_without_xdg_dir(self):
        """Save a new config file with an unexisting directory"""
        os.removedirs(self.config_dir)
        self.test_save_new_config()

    def test_save_config_existing(self):
        """Replace an existing config with a new one"""
        shutil.copy(os.path.join(self.config_dir_for_name('valid'), settings.CONFIG_FILENAME), self.config_dir)
        content = {'foo': 'bar'}
        ConfigHandler().config = content

        self.assertEquals(ConfigHandler().config, content)
        with open(os.path.join(self.config_dir, settings.CONFIG_FILENAME)) as f:
            self.assertEquals(f.read(), 'foo: bar\n')

    def test_dont_create_file_without_assignment(self):
        """We don't create any file without an assignment"""
        ConfigHandler()

        self.assertEquals(len(os.listdir(self.config_dir)), 0)


class TestCompletionArchVersion(LoggedTestCase):

    def setUp(self):
        """Reset previously cached values"""
        super().setUp()
        tools._current_arch = None
        tools._foreign_arch = None
        tools._version = None

    def tearDown(self):
        """Reset cached values"""
        tools._current_arch = None
        tools._foreign_arch = None
        tools._version = None
        with suppress(KeyError):
            os.environ.pop("_ARGCOMPLETE")
        super().tearDown()

    def get_lsb_release_filepath(self, name):
        return os.path.join(get_data_dir(), 'lsb_releases', name)

    @contextmanager
    def create_dpkg(self, content):
        """Create a temporary dpkg which can be used as context"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            sys.path.insert(0, tmpdirname)
            dpkg_file_path = os.path.join(tmpdirname, "dpkg")
            with open(dpkg_file_path, mode='w') as f:
                f.write("#!/bin/sh\n{}".format(content))
            os.environ['PATH'] = '{}:{}'.format(tmpdirname, os.getenv('PATH'))
            st = os.stat(dpkg_file_path)
            os.chmod(dpkg_file_path, st.st_mode | stat.S_IEXEC)
            yield
            sys.path.remove(tmpdirname)

    def test_get_current_arch(self):
        """Current arch is reported"""
        with self.create_dpkg("echo fooarch"):
            self.assertEquals(get_current_arch(), "fooarch")

    def test_get_current_arch_twice(self):
        """Current arch is reported twice and the same"""
        with self.create_dpkg("echo fooarch"):
            self.assertEquals(get_current_arch(), "fooarch")
            self.assertEquals(get_current_arch(), "fooarch")

    def test_get_current_arch_no_dpkg(self):
        """Assert an error if dpkg exit with an error"""
        with self.create_dpkg("exit 1"):
            self.assertRaises(subprocess.CalledProcessError, get_current_arch)

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

    def test_get_foreign_arch(self):
        """Get current foreign arch (one)"""
        with self.create_dpkg("echo fooarch"):
            self.assertEquals(get_foreign_archs(), ["fooarch"])

    def test_get_foreign_archs(self):
        """Get current foreign arch (multiple)"""
        with self.create_dpkg("echo fooarch\necho bararch\necho bazarch"):
            self.assertEquals(get_foreign_archs(), ["fooarch", "bararch", "bazarch"])

    def test_get_foreign_archs_error(self):
        """Get current foreign arch raises an exception if dpkg is in error"""
        with self.create_dpkg("exit 1"):
            self.assertRaises(subprocess.CalledProcessError, get_foreign_archs)

    def test_in_completion_mode(self):
        """We return if we are in completion mode"""
        os.environ["_ARGCOMPLETE"] = "1"
        self.assertTrue(tools.is_completion_mode())

    def test_not_incompletion_mode(self):
        """We are not in completion mode by default"""
        self.assertFalse(tools.is_completion_mode())


class TestToolsThreads(LoggedTestCase):
    """Test main loop threading helpers"""

    def setUp(self):
        super().setUp()
        self.mainloop_object = tools.MainLoop()
        self.mainloop_thread = None
        self.function_thread = None
        self.saved_stderr = sys.stderr

    def tearDown(self):
        Singleton._instances = {}
        sys.stderr = self.saved_stderr
        super().tearDown()

    def patch_stderr(self):
        class writer(object):
            def write(self, data):
                print(data)
        sys.stderr = writer()

    # function that will complete once the mainloop is started
    def wait_for_mainloop_function(self):
        timeout_time = time() + 5
        while not self.mainloop_object.mainloop.is_running():
            if time() > timeout_time:
                raise(BaseException("Mainloop not started in 5 seconds"))

    def wait_for_mainloop_shutdown(self):
        timeout_time = time() + 5
        while self.mainloop_object.mainloop.is_running():
            if time() > timeout_time:
                raise(BaseException("Mainloop not stopped in 5 seconds"))

    def get_mainloop_thread(self):
        self.mainloop_thread = threading.current_thread().ident

    def start_glib_mainloop(self):
        # quit after 5 seconds if nothing made the mainloop to end
        GLib.timeout_add_seconds(5, self.mainloop_object.mainloop.quit)
        GLib.idle_add(self.get_mainloop_thread)
        self.mainloop_object.run()

    @patch("udtc.tools.sys")
    def test_run_function_in_mainloop_thread(self, mocksys):
        """Decorated mainloop thread functions are really running in that thread"""

        # function supposed to run in the mainloop thread
        @tools.MainLoop.in_mainloop_thread
        def _function_in_mainloop_thread(future):
            self.function_thread = threading.current_thread().ident
            self.mainloop_object.quit()

        executor = futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.wait_for_mainloop_function)
        future.add_done_callback(_function_in_mainloop_thread)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        # mainloop and thread were started
        self.assertIsNotNone(self.mainloop_thread)
        self.assertIsNotNone(self.function_thread)
        self.assertEquals(self.mainloop_thread, self.function_thread)

    @patch("udtc.tools.sys")
    def test_run_function_not_in_mainloop_thread(self, mocksys):
        """Non decorated callback functions are not running in the mainloop thread"""

        # function not supposed to run in the mainloop thread
        def _function_not_in_mainloop_thread(future):
            self.function_thread = threading.current_thread().ident
            self.mainloop_object.quit(raise_exception=False)  # as we don't run that from the mainloop

        executor = futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.wait_for_mainloop_function)
        future.add_done_callback(_function_not_in_mainloop_thread)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        # mainloop and thread were started
        self.assertIsNotNone(self.mainloop_thread)
        self.assertIsNotNone(self.function_thread)
        self.assertNotEquals(self.mainloop_thread, self.function_thread)

    def test_singleton(self):
        """Ensure we are delivering a singleton for RequirementsHandler"""
        second = tools.MainLoop()
        self.assertEquals(self.mainloop_object, second)

    def test_mainloop_run(self):
        """We effectively executes the mainloop"""
        with patch.object(self.mainloop_object, "mainloop") as mockmainloop:
            self.mainloop_object.run()
            self.assertTrue(mockmainloop.run.called)

    @patch("udtc.tools.sys")
    def test_mainloop_quit(self, mocksys):
        """We quit the process"""
        def _quit_ignoring_exception():
            self.mainloop_object.quit(raise_exception=False)  # as we don't run that from the mainloop

        GLib.idle_add(_quit_ignoring_exception)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        mocksys.exit.assert_called_once_with(0)

    @patch("udtc.tools.sys")
    def test_mainloop_quit_with_exit_value(self, mocksys):
        """We quit the process with a return code"""
        def _quit_ignoring_exception():
            self.mainloop_object.quit(42, raise_exception=False)  # as we don't run that from the mainloop

        GLib.idle_add(_quit_ignoring_exception)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        mocksys.exit.assert_called_once_with(42)

    @patch("udtc.tools.sys")
    def test_unhandled_exception_in_mainloop_thead_exit(self, mocksys):
        """We quit the process in error for any unhandled exception, logging it"""

        @tools.MainLoop.in_mainloop_thread
        def _function_raising_exception():
            raise BaseException("foo bar")

        _function_raising_exception()
        self.patch_stderr()
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        mocksys.exit.assert_called_once_with(1)
        self.expect_warn_error = True


class TestLauncherIcons(LoggedTestCase):
    """Test module for launcher icons handling"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server_dir = os.path.join(get_data_dir(), "server-content")

    def setUp(self):
        super().setUp()
        self.local_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.local_dir, "applications"))
        os.mkdir(os.path.join(self.local_dir, "icons"))
        change_xdg_path('XDG_DATA_HOME', self.local_dir)
        self.current_desktop = os.environ.get("XDG_CURRENT_DESKTOP")
        os.environ["XDG_CURRENT_DESKTOP"] = "Unity"

    def tearDown(self):
        change_xdg_path('XDG_DATA_HOME', remove=True)
        shutil.rmtree(self.local_dir)
        if self.current_desktop:
            os.environ["XDG_CURRENT_DESKTOP"] = self.current_desktop
        super().tearDown()

    def get_generic_desktop_content(self):
        """Return a generic desktop content to win spaces"""
        return dedent("""\
               [Desktop Entry]
               Version=1.0
               Type=Application
               Name=Android Studio
               Icon=/home/didrocks/tools/android-studio/bin/idea.png
               Exec="/home/didrocks/tools/android-studio/bin/studio.sh" %f
               Comment=Develop with pleasure!
               Categories=Development;IDE;
               Terminal=false
               StartupWMClass=jetbrains-android-studio
               """)

    def write_desktop_file(self, filename):
        """Write a dummy filename to the applications dir and return filepath"""
        result_file = os.path.join(self.local_dir, "applications", filename)
        with open(result_file, 'w') as f:
            f.write("Foo Bar Baz")
        return result_file

    @patch("udtc.tools.Gio.Settings")
    def test_can_install(self, SettingsMock):
        """Install a basic launcher, default case with unity://running"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "unity://running-apps"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertTrue(SettingsMock.list_schemas.called)
        SettingsMock.return_value.get_strv.assert_called_with("favorites")
        SettingsMock.return_value.set_strv.assert_called_with("favorites", ["application://bar.desktop",
                                                                            "application://foo.desktop",
                                                                            "unity://running-apps"])
        self.assertTrue(os.path.exists(get_launcher_path("foo.desktop")))
        self.assertEquals(open(get_launcher_path("foo.desktop")).read(), self.get_generic_desktop_content())

    @patch("udtc.tools.Gio.Settings")
    def test_can_update_launcher(self, SettingsMock):
        """Update a launcher file"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "unity://running-apps"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())
        new_content = dedent("""\
               [Desktop Entry]
               Version=1.0
               Type=Application
               Name=Android Studio 2
               Icon=/home/didrocks/tools/android-studio/bin/idea2.png
               Exec="/home/didrocks/tools/android-studio/bin/studio2.sh" %f
               Comment=Develop with pleasure!
               Categories=Development;IDE;
               Terminal=false
               StartupWMClass=jetbrains-android-studio
               """)
        create_launcher("foo.desktop", new_content)

        self.assertTrue(os.path.exists(get_launcher_path("foo.desktop")))
        self.assertEquals(open(get_launcher_path("foo.desktop")).read(), new_content)

    @patch("udtc.tools.Gio.Settings")
    def test_can_install_without_unity_running(self, SettingsMock):
        """Install a basic launcher icon, without a running apps entry (so will be last)"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "application://baz.desktop"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertTrue(SettingsMock.list_schemas.called)
        SettingsMock.return_value.set_strv.assert_called_with("favorites", ["application://bar.desktop",
                                                                            "application://baz.desktop",
                                                                            "application://foo.desktop"])

    @patch("udtc.tools.Gio.Settings")
    def test_can_install_already_in_launcher(self, SettingsMock):
        """A file listed in launcher still install the files, but the entry isn't changed"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "application://foo.desktop",
                                                           "unity://running-apps"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertFalse(SettingsMock.return_value.set_strv.called)
        self.assertTrue(os.path.exists(get_launcher_path("foo.desktop")))

    @patch("udtc.tools.Gio.Settings")
    def test_install_no_schema_file(self, SettingsMock):
        """No schema file still installs the file"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "baz"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertFalse(SettingsMock.return_value.get_strv.called)
        self.assertFalse(SettingsMock.return_value.set_strv.called)
        self.assertTrue(os.path.exists(get_launcher_path("foo.desktop")))

    @patch("udtc.tools.Gio.Settings")
    def test_already_existing_file_different_content(self, SettingsMock):
        """A file with a different file content already exists and is updated"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "baz"]
        result_file = self.write_desktop_file("foo.desktop")
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertEquals(open(result_file).read(), self.get_generic_desktop_content())

    @patch("udtc.tools.Gio.Settings")
    def test_create_launcher_without_xdg_dir(self, SettingsMock):
        """Save a new launcher in an unexisting directory"""
        shutil.rmtree(self.local_dir)
        SettingsMock.list_schemas.return_value = ["foo", "bar", "baz"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertTrue(os.path.exists(get_launcher_path("foo.desktop")))

    def test_desktop_file_exists(self):
        """Launcher exists"""
        self.write_desktop_file("foo.desktop")
        self.assertTrue(launcher_exists("foo.desktop"))

    def test_desktop_file_doesnt_exist(self):
        """Launcher file doesn't exists"""
        self.assertFalse(launcher_exists("foo.desktop"))

    @patch("udtc.tools.Gio.Settings")
    def test_launcher_exists_and_is_pinned(self, SettingsMock):
        """Launcher exists and is pinned if the file exists and is in favorites list"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "application://foo.desktop",
                                                           "unity://running-apps"]
        self.write_desktop_file("foo.desktop")

        self.assertTrue(launcher_exists_and_is_pinned("foo.desktop"))

    @patch("udtc.tools.Gio.Settings")
    def test_launcher_isnt_pinned(self, SettingsMock):
        """Launcher doesn't exists and is pinned if the file exists but not in favorites list"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "unity://running-apps"]
        self.write_desktop_file("foo.desktop")

        self.assertFalse(launcher_exists_and_is_pinned("foo.desktop"))

    @patch("udtc.tools.Gio.Settings")
    def test_launcher_exists_but_isnt_pinned_in_none_unity(self, SettingsMock):
        """Launcher exists return True if file exists, not pinned but not in Unity"""
        os.environ["XDG_CURRENT_DESKTOP"] = "FOOenv"
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "unity://running-apps"]
        self.write_desktop_file("foo.desktop")

        self.assertTrue(launcher_exists_and_is_pinned("foo.desktop"))

    @patch("udtc.tools.Gio.Settings")
    def test_launcher_exists_but_not_schema_in_none_unity(self, SettingsMock):
        """Launcher exists return True if file exists, even if Unity schema isn't installed"""
        os.environ["XDG_CURRENT_DESKTOP"] = "FOOenv"
        SettingsMock.list_schemas.return_value = ["foo", "bar", "baz"]
        self.write_desktop_file("foo.desktop")

        self.assertTrue(launcher_exists_and_is_pinned("foo.desktop"))

    @patch("udtc.tools.Gio.Settings")
    def test_launcher_exists_but_not_schema_in_unity(self, SettingsMock):
        """Launcher exists return False if file exists, but no Unity schema installed"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "baz"]
        self.write_desktop_file("foo.desktop")

        self.assertFalse(launcher_exists_and_is_pinned("foo.desktop"))

    @patch("udtc.tools.Gio.Settings")
    def test_launcher_doesnt_exists_but_pinned(self, SettingsMock):
        """Launcher doesn't exist if no file, even if pinned"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "application://foo.desktop",
                                                           "unity://running-apps"]

        self.assertFalse(launcher_exists_and_is_pinned("foo.desktop"))

    def test_can_copy_icon(self):
        """Copy a basic icon"""
        # we copy any file and treat it as an icon
        copy_icon(os.path.join(self.server_dir, "simplefile"), "foo.png")

        self.assertTrue(os.path.exists(get_icon_path("foo.png")))
        self.assertEquals(open(os.path.join(self.server_dir, "simplefile")).read(),
                          open(get_icon_path("foo.png")).read())

    def test_can_update_icon(self):
        """Update a basic icon with a new content"""
        copy_icon(os.path.join(self.server_dir, "simplefile"), "foo.png")
        copy_icon(os.path.join(self.server_dir, "biggerfile"), "foo.png")

        self.assertTrue(os.path.exists(get_icon_path("foo.png")))
        self.assertEquals(open(os.path.join(self.server_dir, "biggerfile")).read(),
                          open(get_icon_path("foo.png")).read())

    def test_can_copy_icon_with_glob(self):
        """Copy an icon with glob pattern matching"""
        # we copy any file and treat it as an icon
        copy_icon(os.path.join(self.server_dir, "sim*file"), "foo.png")

        self.assertTrue(os.path.exists(get_icon_path("foo.png")))
        self.assertEquals(open(os.path.join(self.server_dir, "simplefile")).read(),
                          open(get_icon_path("foo.png")).read())

    def test_create_icon_without_xdg_dir(self):
        """Save a new icon in an unexisting directory"""
        shutil.rmtree(self.local_dir)
        copy_icon(os.path.join(self.server_dir, "simplefile"), "foo.png")

        self.assertTrue(os.path.exists(get_icon_path("foo.png")))

    def test_get_icon_path(self):
        """Get correct launcher path"""
        self.assertEquals(get_icon_path("foo.png"), os.path.join(self.local_dir, "icons", "foo.png"))

    def test_get_launcher_path(self):
        """Get correct launcher path"""
        self.assertEquals(get_launcher_path("foo.desktop"), os.path.join(self.local_dir, "applications", "foo.desktop"))


class TestMiscTools(LoggedTestCase):

    def test_get_application_desktop_file(self):
        """We return expect results with normal content"""
        self.assertEquals(tools.get_application_desktop_file(name="Name 1", icon_path="/to/icon/path",
                                                             exec="/to/exec/path %f", comment="Comment for Name 1",
                                                             categories="Cat1:Cat2"),
                          dedent("""\
                            [Desktop Entry]
                            Version=1.0
                            Type=Application
                            Name=Name 1
                            Icon=/to/icon/path
                            Exec=/to/exec/path %f
                            Comment=Comment for Name 1
                            Categories=Cat1:Cat2
                            Terminal=false

                            """))

    def test_get_application_desktop_file_with_extra(self):
        """We return expect results with extra content"""
        self.assertEquals(tools.get_application_desktop_file(name="Name 1", icon_path="/to/icon/path",
                                                             exec="/to/exec/path %f", comment="Comment for Name 1",
                                                             categories="Cat1:Cat2", extra="Extra=extra1\nFoo=foo"),
                          dedent("""\
                            [Desktop Entry]
                            Version=1.0
                            Type=Application
                            Name=Name 1
                            Icon=/to/icon/path
                            Exec=/to/exec/path %f
                            Comment=Comment for Name 1
                            Categories=Cat1:Cat2
                            Terminal=false
                            Extra=extra1
                            Foo=foo
                            """))

    def test_get_application_desktop_file_all_empty(self):
        """We return expect results without any content"""
        self.assertEquals(tools.get_application_desktop_file(),
                          dedent("""\
                            [Desktop Entry]
                            Version=1.0
                            Type=Application
                            Name=
                            Icon=
                            Exec=
                            Comment=
                            Categories=
                            Terminal=false

                            """))

    def test_strip_tags(self):
        """We return strip tags from content"""
        self.assertEquals(tools.strip_tags("content <a foo bar>content content content</a><b><c>content\n content</c>"
                                           "\n</b>content content"),
                          "content content content contentcontent\n content\ncontent content")

    def test_strip_invalid_tags(self):
        """We return trip tags even if invalid"""
        self.assertEquals(tools.strip_tags("content <a foo bar>content content content</a><b>content\n content</c>"
                                           "\n</b>content content"),
                          "content content content contentcontent\n content\ncontent content")

    def test_strip_without_tags(self):
        """We return unmodified content if there is no tag"""
        self.assertEquals(tools.strip_tags("content content content contentcontent\n content"
                                           "\ncontent content"),
                          "content content content contentcontent\n content\ncontent content")

    def test_raise_inputerror(self):
        def foo():
            raise tools.InputError("Foo bar")
        self.assertRaises(tools.InputError, foo)

    def test_print_inputerror(self):
        self.assertEquals(str(tools.InputError("Foo bar")), "'Foo bar'")

    @patch("udtc.tools.os")
    def test_switch_user_from_sudo(self, osmock):
        """Test switch user account from root to previous user under SUDO"""
        osmock.getenv.return_value = 1234
        osmock.geteuid.return_value = 0
        tools.switch_to_current_user()

        osmock.setegid.assert_called_once_with(1234)
        osmock.seteuid.assert_called_once_with(1234)

    @patch("udtc.tools.os")
    def test_switch_user_from_non_sudo(self, osmock):
        """Test switch user from a non sudo command (non root), dosen't call anything"""
        osmock.getenv.return_value = 1234
        osmock.geteuid.return_value = 1234
        tools.switch_to_current_user()

        self.assertFalse(osmock.setegid.called)
        self.assertFalse(osmock.seteuid.called)
        self.assertFalse(osmock.getenv.called)

    @patch("udtc.tools.os")
    def test_switch_user_from_root(self, osmock):
        """Test switch user from root, let it as root"""
        osmock.getenv.return_value = 0
        osmock.geteuid.return_value = 0
        tools.switch_to_current_user()

        osmock.setegid.assert_called_once_with(0)
        osmock.seteuid.assert_called_once_with(0)


class TestAppendPATH(LoggedTestCase):

    def setUp(self):
        super().setUp()
        self.local_dir = tempfile.mkdtemp()
        self.initial_path = os.environ['PATH']

    def tearDown(self):
        shutil.rmtree(self.local_dir)
        os.environ['PATH'] = self.initial_path
        super().tearDown()

    @patch("udtc.tools.os.path.expanduser")
    def test_add_to_user_path(self, expanderusermock):
        """Test that adding to user path append to an existing .bashrc file"""
        expanderusermock.return_value = self.local_dir
        bashrc_file = os.path.join(self.local_dir, ".bashrc")
        open(bashrc_file, 'w').write("Foo\nBar\n")
        tools.add_to_user_path(["/tmp/foo"], "one path addition")

        expanderusermock.assert_called_once_with('~')
        bashrc_content = open(bashrc_file).read()
        self.assertTrue("Foo\nBar\n" in bashrc_content, bashrc_content)  # we kept previous content
        self.assertTrue("PATH=/tmp/foo:$PATH" in bashrc_content, bashrc_content)
        self.assertTrue("/tmp/foo" in os.environ["PATH"], os.environ["PATH"])

    @patch("udtc.tools.os.path.expanduser")
    def test_add_to_user_path_multiple_paths(self, expanderusermock):
        """Test that adding multiple paths to user path append to an existing .bashrc file"""
        expanderusermock.return_value = self.local_dir
        bashrc_file = os.path.join(self.local_dir, ".bashrc")
        open(bashrc_file, 'w').write("Foo\nBar\n")
        tools.add_to_user_path(["/tmp/foo", "/tmp/bar"], "one path addition")

        expanderusermock.assert_called_once_with('~')
        bashrc_content = open(bashrc_file).read()
        self.assertTrue("Foo\nBar\n" in bashrc_content, bashrc_content)  # we kept previous content
        self.assertTrue("PATH=/tmp/foo:/tmp/bar:$PATH" in bashrc_content, bashrc_content)
        self.assertTrue("/tmp/foo" in os.environ["PATH"], os.environ["PATH"])
        self.assertTrue("/tmp/bar" in os.environ["PATH"], os.environ["PATH"])

    @patch("udtc.tools.os.path.expanduser")
    def test_add_to_user_path_empty_file(self, expanderusermock):
        """Test that adding to user path append to an non existing .bashrc file"""
        expanderusermock.return_value = self.local_dir
        bashrc_file = os.path.join(self.local_dir, ".bashrc")
        tools.add_to_user_path(["/tmp/foo"], "one path addition")

        expanderusermock.assert_called_once_with('~')
        bashrc_content = open(bashrc_file).read()
        self.assertTrue("PATH=/tmp/foo:$PATH" in bashrc_content, bashrc_content)
        self.assertTrue("/tmp/foo" in os.environ["PATH"], os.environ["PATH"])

    @patch("udtc.tools.os.path.expanduser")
    def test_add_to_user_path_twice(self, expanderusermock):
        """Test that adding to user path twice doesn't add it twice in the file"""
        expanderusermock.return_value = self.local_dir
        bashrc_file = os.path.join(self.local_dir, ".bashrc")
        open(bashrc_file, 'w').write("Foo\nBar\n")
        tools.add_to_user_path(["/tmp/foo"], "one path addition")

        expanderusermock.assert_called_once_with('~')
        bashrc_content = open(bashrc_file).read()
        self.assertTrue("Foo\nBar\n" in bashrc_content, bashrc_content)  # we kept previous content
        self.assertTrue("PATH=/tmp/foo:$PATH" in bashrc_content, bashrc_content)
        self.assertTrue("/tmp/foo" in os.environ["PATH"], os.environ["PATH"])

        tools.add_to_user_path(["/tmp/foo"], "one path addition")

        # ensure, it's only there once
        bashrc_content = open(bashrc_file).read()
        self.assertEquals(bashrc_content.count("PATH=/tmp/foo:$PATH"), 1, bashrc_content)
        self.assertTrue("/tmp/foo" in os.environ["PATH"], os.environ["PATH"])

    @patch("udtc.tools.os.path.expanduser")
    def test_add_to_user_path_twice_with_new_content(self, expanderusermock):
        """Test that adding to user path twice but with new paths add only the new path to the file"""
        expanderusermock.return_value = self.local_dir
        bashrc_file = os.path.join(self.local_dir, ".bashrc")
        open(bashrc_file, 'w').write("Foo\nBar\n")
        tools.add_to_user_path(["/tmp/foo"], "one path addition")

        expanderusermock.assert_called_once_with('~')
        bashrc_content = open(bashrc_file).read()
        self.assertTrue("Foo\nBar\n" in bashrc_content, bashrc_content)  # we kept previous content
        self.assertTrue("PATH=/tmp/foo:$PATH" in bashrc_content, bashrc_content)
        self.assertTrue("/tmp/foo" in os.environ["PATH"], os.environ["PATH"])

        tools.add_to_user_path(["/tmp/foo", "/tmp/bar"], "even more addition")

        # we only added the new element
        bashrc_content = open(bashrc_file).read()
        self.assertEquals(bashrc_content.count("PATH=/tmp/foo:$PATH"), 1, bashrc_content)
        self.assertEquals(bashrc_content.count("/tmp/foo"), 1, bashrc_content)
        self.assertTrue("PATH=/tmp/bar:$PATH" in bashrc_content, bashrc_content)
        self.assertTrue("/tmp/foo" in os.environ["PATH"], os.environ["PATH"])
        self.assertTrue("/tmp/bar" in os.environ["PATH"], os.environ["PATH"])
