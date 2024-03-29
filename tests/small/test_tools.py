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

"""Tests the various umake tools"""

from concurrent import futures
from gi.repository import GLib
import os
import shutil
import subprocess
import sys
import tempfile
from textwrap import dedent
from time import time
import threading
from . import DpkgAptSetup
from ..tools import change_xdg_path, get_data_dir, LoggedTestCase, INSTALL_DIR
from umake import settings, tools
from umake.tools import ConfigHandler, Singleton, get_current_arch, get_foreign_archs, get_current_distro_version,\
    create_launcher, launcher_exists, get_icon_path, get_launcher_path, copy_icon,\
    add_exec_link
from unittest.mock import patch, Mock
from contextlib import suppress


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
        self.assertEqual(config1, config2)

    def test_load_config(self):
        """Valid config loads correct content"""
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir_for_name("valid"))
        self.assertEqual(ConfigHandler().config,
                         {'frameworks': {
                             'category-a': {
                                 'framework-a': {'path': '/home/didrocks/quickly/ubuntu-make/adt-eclipse'},
                                 'framework-b': {'path': '/home/didrocks/foo/bar/android-studio'}
                             }
                         }})

    def test_load_no_config(self):
        """No existing file gives an empty result"""
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir_for_name("foo"))
        self.assertEqual(ConfigHandler().config, {})

    def test_load_invalid_config(self):
        """Existing invalid file gives an empty result"""
        change_xdg_path('XDG_CONFIG_HOME', self.config_dir_for_name("invalid"))
        self.assertEqual(ConfigHandler().config, {})
        self.expect_warn_error = True

    def test_save_new_config(self):
        """Save a new config in a vanilla directory"""
        content = {'foo': 'bar'}
        ConfigHandler().config = content

        self.assertEqual(ConfigHandler().config, content)
        with open(os.path.join(self.config_dir, settings.CONFIG_FILENAME)) as f:
            self.assertEqual(f.read(), 'foo: bar\n')

    def test_save_config_without_xdg_dir(self):
        """Save a new config file with an unexisting directory"""
        os.removedirs(self.config_dir)
        self.test_save_new_config()

    def test_save_config_existing(self):
        """Replace an existing config with a new one"""
        shutil.copy(os.path.join(self.config_dir_for_name('valid'), settings.CONFIG_FILENAME), self.config_dir)
        content = {'foo': 'bar'}
        ConfigHandler().config = content

        self.assertEqual(ConfigHandler().config, content)
        with open(os.path.join(self.config_dir, settings.CONFIG_FILENAME)) as f:
            self.assertEqual(f.read(), 'foo: bar\n')

    def test_dont_create_file_without_assignment(self):
        """We don't create any file without an assignment"""
        ConfigHandler()

        self.assertEqual(len(os.listdir(self.config_dir)), 0)

    def test_transition_old_config(self):
        """Transition udtc old config to new umake one"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            shutil.copy(os.path.join(self.config_dir_for_name("old"), "udtc"), tmpdirname)
            change_xdg_path('XDG_CONFIG_HOME', tmpdirname)
            self.assertEqual(ConfigHandler().config,
                             {'frameworks': {
                                 'category-a': {
                                     'framework-a': {'path': '/home/didrocks/quickly/ubuntu-make/adt-eclipse'},
                                     'framework-b': {'path': '/home/didrocks/foo/bar/android-studio'}
                                 }
                             }})

            # file has been renamed
            self.assertTrue(os.path.exists(os.path.join(tmpdirname, "umake")), "New umake config file exists")
            self.assertFalse(os.path.exists(os.path.join(tmpdirname, "udtc")), "Old udtc config file is removed")


class TestGetUbuntuVersion(LoggedTestCase):

    def setUp(self):
        """Reset previously cached values"""
        super().setUp()
        tools._version = None

    def tearDown(self):
        """Reset cached values"""
        tools._version = None
        super().tearDown()

    def get_os_release_filepath(self, name):
        return os.path.join(get_data_dir(), 'os_releases', name)

    @patch("umake.tools.settings")
    def test_get_current_distro_version(self, settings_module):
        """Current ubuntu version is reported from our os_releases local file"""
        settings_module.OS_RELEASE_FILE = self.get_os_release_filepath("valid")
        self.assertEqual(get_current_distro_version(), '14.04')

    @patch("umake.tools.settings")
    def test_get_current_distro_version_invalid(self, settings_module):
        """Raise an error when parsing an invalid os_releases file"""
        settings_module.OS_RELEASE_FILE = self.get_os_release_filepath("invalid")
        self.assertRaises(BaseException, get_current_distro_version)
        self.expect_warn_error = True

    @patch("umake.tools.settings")
    def test_get_current_distro_version_no_os_releases(self, settings_module):
        """Raise an error when there is no os_releases file"""
        settings_module.OS_RELEASE_FILE = self.get_os_release_filepath("notexist")
        self.assertRaises(BaseException, get_current_distro_version)
        self.expect_warn_error = True

    @patch("umake.tools.settings")
    def test_get_current_distro_version_debian(self, settings_module):
        """Report the proper debian release if requested.
        Report an issue on ubuntu check"""
        settings_module.OS_RELEASE_FILE = self.get_os_release_filepath("debian")
        self.assertEqual(get_current_distro_version(distro_name="debian"), '10')


class TestCompletion(LoggedTestCase):

    def setUp(self):
        super().setUp()
        self.initial_env = os.environ.copy()

    def tearDown(self):
        # restore original environment. Do not use the dict copy which erases the object and doesn't have the magical
        # _Environ which setenv() for subprocess
        os.environ.clear()
        os.environ.update(self.initial_env)
        super().tearDown()

    def test_in_completion_mode(self):
        """We return if we are in completion mode"""
        os.environ["_ARGCOMPLETE"] = "1"
        self.assertTrue(tools.is_completion_mode())

    def test_not_incompletion_mode(self):
        """We are not in completion mode by default"""
        self.assertFalse(tools.is_completion_mode())


class TestArchVersion(DpkgAptSetup):

    def setUp(self):
        """Reset previously cached values"""
        super().setUp()
        tools._current_arch = None
        tools._foreign_arch = None

    def tearDown(self):
        """Reset cached values"""
        tools._current_arch = None
        tools._foreign_arch = None
        super().tearDown()

    def dpkg_error(self, *args, **kwargs):
        """Simulate a dpkg failure"""
        raise subprocess.CalledProcessError("dpkg failure", cmd="dpkg")

    def test_get_current_arch(self):
        """Current arch is reported"""
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.check_output.return_value = "fooarch"
            self.assertEqual(get_current_arch(), "fooarch")

    def test_get_current_arch_twice(self):
        """Current arch is reported twice and the same"""
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.check_output.return_value = "fooarch"
            self.assertEqual(get_current_arch(), "fooarch")
            self.assertEqual(get_current_arch(), "fooarch")
            self.assertEqual(subprocess_mock.check_output.call_count, 1, "We cache older value")

    def test_get_current_arch_no_dpkg(self):
        """Assert an error if dpkg exit with an error"""
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.check_output.side_effect = self.dpkg_error
            self.assertRaises(subprocess.CalledProcessError, get_current_arch)

    def test_get_foreign_arch(self):
        """Get current foreign arch (one)"""
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.check_output.return_value = "fooarch"
            self.assertEqual(get_foreign_archs(), ["fooarch"])

    def test_get_foreign_archs(self):
        """Get current foreign arch (multiple)"""
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.check_output.return_value = "fooarch\nbararch\nbazarch"
            self.assertEqual(get_foreign_archs(), ["fooarch", "bararch", "bazarch"])

    def test_get_foreign_archs_error(self):
        """Get current foreign arch raises an exception if dpkg is in error"""
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.check_output.side_effect = self.dpkg_error
            self.assertRaises(subprocess.CalledProcessError, get_foreign_archs)

    def test_add_new_foreign_arch(self):
        """Add a new foreign arch and check that we can retrieve it (cache invalidated)"""
        with suppress(KeyError):
            if os.environ["CI"]:
                tools.add_foreign_arch("foo")
                self.assertEqual(get_foreign_archs(), ["foo"])

    def test_add_foreign_arch_already_in(self):
        """Add a foreign arch which was already there should be a noop"""
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.check_output.return_value = "foo"
            subprocess_mock.call.side_effect = subprocess.call
            tools.add_foreign_arch("foo")

            self.assertFalse(subprocess_mock.call.called)

    def test_add_current_arch(self):
        """Add the current arch should be a noop"""
        tools._current_arch = "foo"
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.call.side_effect = subprocess.call
            tools.add_foreign_arch("foo")

    def test_add_new_foreign_arch_fail(self):
        """Add a new foreign arch, but failing should raise an exception"""
        with patch("umake.tools.subprocess") as subprocess_mock:
            subprocess_mock.call.return_value = 1

            self.assertRaises(BaseException, tools.add_foreign_arch, "foo")


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

    @patch("umake.tools.sys")
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
        self.assertEqual(self.mainloop_thread, self.function_thread)

    @patch("umake.tools.sys")
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
        self.assertNotEqual(self.mainloop_thread, self.function_thread)

    def test_singleton(self):
        """Ensure we are delivering a singleton for RequirementsHandler"""
        second = tools.MainLoop()
        self.assertEqual(self.mainloop_object, second)

    def test_mainloop_run(self):
        """We effectively executes the mainloop"""
        with patch.object(self.mainloop_object, "mainloop") as mockmainloop:
            self.mainloop_object.run()
            self.assertTrue(mockmainloop.run.called)

    @patch("umake.tools.sys")
    def test_mainloop_quit(self, mocksys):
        """We quit the process"""
        def _quit_ignoring_exception():
            self.mainloop_object.quit(raise_exception=False)  # as we don't run that from the mainloop

        GLib.idle_add(_quit_ignoring_exception)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        mocksys.exit.assert_called_once_with(0)

    @patch("umake.tools.sys")
    def test_mainloop_quit_with_exit_value(self, mocksys):
        """We quit the process with a return code"""
        def _quit_ignoring_exception():
            self.mainloop_object.quit(42, raise_exception=False)  # as we don't run that from the mainloop

        GLib.idle_add(_quit_ignoring_exception)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        mocksys.exit.assert_called_once_with(42)

    @patch("umake.tools.sys")
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
        self.tmpHome = tempfile.mkdtemp()
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
               Icon=/home/didrocks/{install_dir}/android-studio/bin/studio.png
               Exec="/home/didrocks/{install_dir}/android-studio/bin/studio.sh" %f
               Comment=Develop with pleasure!
               Categories=Development;IDE;
               Terminal=false
               StartupWMClass=jetbrains-android-studio
               """.format(install_dir=INSTALL_DIR))

    def write_desktop_file(self, filename):
        """Write a dummy filename to the applications dir and return filepath"""
        result_file = os.path.join(self.local_dir, "applications", filename)
        with open(result_file, 'w') as f:
            f.write("Foo Bar Baz")
        return result_file

    @patch("umake.tools.Gio.Settings")
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
        self.assertEqual(open(get_launcher_path("foo.desktop")).read(), self.get_generic_desktop_content())

    @patch("umake.tools.Gio.Settings")
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
               Icon=/home/didrocks/{install_dir}/android-studio/bin/idea2.png
               Exec="/home/didrocks/{install_dir}/android-studio/bin/studio2.sh" %f
               Comment=Develop with pleasure!
               Categories=Development;IDE;
               Terminal=false
               StartupWMClass=jetbrains-android-studio
               """.format(install_dir=INSTALL_DIR))
        create_launcher("foo.desktop", new_content)

        self.assertTrue(os.path.exists(get_launcher_path("foo.desktop")))
        self.assertEqual(open(get_launcher_path("foo.desktop")).read(), new_content)

    @patch("umake.tools.Gio.Settings")
    def test_can_install_without_unity_running(self, SettingsMock):
        """Install a basic launcher icon, without a running apps entry (so will be last)"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "application://baz.desktop"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertTrue(SettingsMock.list_schemas.called)
        SettingsMock.return_value.set_strv.assert_called_with("favorites", ["application://bar.desktop",
                                                                            "application://baz.desktop",
                                                                            "application://foo.desktop"])

    @patch("umake.tools.Gio.Settings")
    def test_can_install_already_in_launcher(self, SettingsMock):
        """A file listed in launcher still install the files, but the entry isn't changed"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "com.canonical.Unity.Launcher", "baz"]
        SettingsMock.return_value.get_strv.return_value = ["application://bar.desktop", "application://foo.desktop",
                                                           "unity://running-apps"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertFalse(SettingsMock.return_value.set_strv.called)
        self.assertTrue(os.path.exists(get_launcher_path("foo.desktop")))

    @patch("umake.tools.Gio.Settings")
    def test_install_no_schema_file(self, SettingsMock):
        """No schema file still installs the file"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "baz"]
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertFalse(SettingsMock.return_value.get_strv.called)
        self.assertFalse(SettingsMock.return_value.set_strv.called)
        self.assertTrue(os.path.exists(get_launcher_path("foo.desktop")))

    @patch("umake.tools.Gio.Settings")
    def test_already_existing_file_different_content(self, SettingsMock):
        """A file with a different file content already exists and is updated"""
        SettingsMock.list_schemas.return_value = ["foo", "bar", "baz"]
        result_file = self.write_desktop_file("foo.desktop")
        create_launcher("foo.desktop", self.get_generic_desktop_content())

        self.assertEqual(open(result_file).read(), self.get_generic_desktop_content())

    @patch("umake.tools.Gio.Settings")
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

    def test_can_copy_icon(self):
        """Copy a basic icon"""
        # we copy any file and treat it as an icon
        copy_icon(os.path.join(self.server_dir, "simplefile"), "foo.png")

        self.assertTrue(os.path.exists(get_icon_path("foo.png")))
        self.assertEqual(open(os.path.join(self.server_dir, "simplefile")).read(),
                         open(get_icon_path("foo.png")).read())

    def test_can_update_icon(self):
        """Update a basic icon with a new content"""
        copy_icon(os.path.join(self.server_dir, "simplefile"), "foo.png")
        copy_icon(os.path.join(self.server_dir, "biggerfile"), "foo.png")

        self.assertTrue(os.path.exists(get_icon_path("foo.png")))
        self.assertEqual(open(os.path.join(self.server_dir, "biggerfile")).read(),
                         open(get_icon_path("foo.png")).read())

    def test_can_copy_icon_with_glob(self):
        """Copy an icon with glob pattern matching"""
        # we copy any file and treat it as an icon
        copy_icon(os.path.join(self.server_dir, "sim*file"), "foo.png")

        self.assertTrue(os.path.exists(get_icon_path("foo.png")))
        self.assertEqual(open(os.path.join(self.server_dir, "simplefile")).read(),
                         open(get_icon_path("foo.png")).read())

    def test_create_icon_without_xdg_dir(self):
        """Save a new icon in an unexisting directory"""
        shutil.rmtree(self.local_dir)
        copy_icon(os.path.join(self.server_dir, "simplefile"), "foo.png")

        self.assertTrue(os.path.exists(get_icon_path("foo.png")))

    def test_get_icon_path(self):
        """Get correct launcher path"""
        self.assertEqual(get_icon_path("foo.png"), os.path.join(self.local_dir, "icons", "foo.png"))

    def test_get_launcher_path(self):
        """Get correct launcher path"""
        self.assertEqual(get_launcher_path("foo.desktop"), os.path.join(self.local_dir, "applications", "foo.desktop"))

    @patch("umake.tools.settings")
    @patch.dict(os.environ, {'HOME': tempfile.mkdtemp()})
    def test_create_exec_path(self, settings_module):
        """Create link to the executable"""
        settings_module.DEFAULT_BINARY_LINK_PATH = os.path.join(self.local_dir, ".local", "share", "umake", "bin")
        add_exec_link(os.path.join(self.server_dir, "simplefile"), "foo")
        self.assertTrue(os.path.exists(os.path.join(settings_module.DEFAULT_BINARY_LINK_PATH, "foo")))


class TestMiscTools(LoggedTestCase):

    def test_get_application_desktop_file(self):
        """We return expect results with normal content"""
        self.assertEqual(tools.get_application_desktop_file(name="Name 1", icon_path="/to/icon/path",
                                                            try_exec="/to/exec/path", exec="command %f",
                                                            comment="Comment for Name 1",
                                                            categories="Cat1:Cat2"),
                         dedent("""\
                           [Desktop Entry]
                           Version=1.0
                           Type=Application
                           Name=Name 1
                           Icon=/to/icon/path
                           TryExec=/to/exec/path
                           Exec=command %f
                           Comment=Comment for Name 1
                           Categories=Cat1:Cat2
                           Terminal=false

                           """))

    def test_get_application_desktop_file_with_extra(self):
        """We return expect results with extra content"""
        self.assertEqual(tools.get_application_desktop_file(name="Name 1", icon_path="/to/icon/path",
                                                            try_exec="/to/exec/path", exec="command %f",
                                                            comment="Comment for Name 1", categories="Cat1:Cat2",
                                                            extra="Extra=extra1\nFoo=foo"),
                         dedent("""\
                           [Desktop Entry]
                           Version=1.0
                           Type=Application
                           Name=Name 1
                           Icon=/to/icon/path
                           TryExec=/to/exec/path
                           Exec=command %f
                           Comment=Comment for Name 1
                           Categories=Cat1:Cat2
                           Terminal=false
                           Extra=extra1
                           Foo=foo
                           """))

    def test_get_application_desktop_file_all_empty(self):
        """We return expect results without any content"""
        self.assertEqual(tools.get_application_desktop_file(),
                         dedent("""\
                           [Desktop Entry]
                           Version=1.0
                           Type=Application
                           Name=
                           Icon=
                           TryExec=
                           Exec=
                           Comment=
                           Categories=
                           Terminal=false

                           """))

    def test_strip_tags(self):
        """We return strip tags from content"""
        self.assertEqual(tools.strip_tags("content <a foo bar>content content content</a><b><c>content\n content</c>"
                                          "\n</b>content content"),
                         "content content content contentcontent\n content\ncontent content")

    def test_strip_invalid_tags(self):
        """We return trip tags even if invalid"""
        self.assertEqual(tools.strip_tags("content <a foo bar>content content content</a><b>content\n content</c>"
                                          "\n</b>content content"),
                         "content content content contentcontent\n content\ncontent content")

    def test_strip_without_tags(self):
        """We return unmodified content if there is no tag"""
        self.assertEqual(tools.strip_tags("content content content contentcontent\n content"
                                          "\ncontent content"),
                         "content content content contentcontent\n content\ncontent content")

    def test_raise_inputerror(self):
        def foo():
            raise tools.InputError("Foo bar")
        self.assertRaises(tools.InputError, foo)

    def test_print_inputerror(self):
        self.assertEqual(str(tools.InputError("Foo bar")), "'Foo bar'")

    @patch("umake.tools.os")
    def test_switch_user_from_sudo(self, osmock):
        """Test switch user account from root to previous user under SUDO"""
        osmock.getenv.return_value = 1234
        osmock.geteuid.return_value = 0
        tools.switch_to_current_user()

        osmock.setegid.assert_called_once_with(1234)
        osmock.seteuid.assert_called_once_with(1234)

    @patch("umake.tools.os")
    def test_switch_user_from_non_sudo(self, osmock):
        """Test switch user from a non sudo command (non root), doesn't call anything"""
        osmock.getenv.return_value = 1234
        osmock.geteuid.return_value = 1234
        tools.switch_to_current_user()

        self.assertFalse(osmock.setegid.called)
        self.assertFalse(osmock.seteuid.called)
        self.assertFalse(osmock.getenv.called)

    @patch("umake.tools.os")
    def test_switch_user_from_root(self, osmock):
        """Test switch user from root, let it as root"""
        osmock.getenv.return_value = 0
        osmock.geteuid.return_value = 0
        tools.switch_to_current_user()

        osmock.setegid.assert_called_once_with(0)
        osmock.seteuid.assert_called_once_with(0)

    @patch("umake.tools.os")
    @patch("umake.tools.switch_to_current_user")
    def test_as_root(self, switch_to_current_usermock, osmock):
        """Switch as root when everything is permitted"""
        with tools.as_root():
            osmock.seteuid.assert_called_once_with(0)
            osmock.setegid.assert_called_once_with(0)
            self.assertFalse(switch_to_current_usermock.called, "didn't switch to current user in context")
        self.assertTrue(switch_to_current_usermock.called, "switch back to user when exiting context")

    @patch("umake.tools.os")
    @patch("umake.tools.switch_to_current_user")
    def test_as_root_euid_perm_denied(self, switch_to_current_usermock, osmock):
        """Switch as root raise exception when euid permission is denied"""
        def raiseException(self):
            raise PermissionError("")
        osmock.seteuid.side_effect = raiseException
        exception_raised = False
        try:
            with tools.as_root():
                pass
        except PermissionError:
            exception_raised = True
        self.assertTrue(exception_raised, "Permission Error was raised")
        self.assertTrue(switch_to_current_usermock.called, "switch back to user when exiting context")

    @patch("umake.tools.os")
    @patch("umake.tools.switch_to_current_user")
    def test_as_root_egid_perm_denied(self, switch_to_current_usermock, osmock):
        """Switch as root raise exception when egid permission is denied"""
        def raiseException(self):
            raise PermissionError("")
        osmock.setegid.side_effect = raiseException
        exception_raised = False
        try:
            with tools.as_root():
                pass
        except PermissionError:
            exception_raised = True
        self.assertTrue(exception_raised, "Permission Error was raised")
        self.assertTrue(switch_to_current_usermock.called, "switch back to user when exiting context")

    @patch("umake.tools.os")
    @patch("umake.tools.switch_to_current_user")
    def test_as_root_with_lock(self, switch_to_current_usermock, osmock):
        """Ensure we don't try to switch as root before the lock is released"""
        def as_root_function():
            with tools.as_root():
                method_called_as_root()

        method_called_as_root = Mock()
        executor = futures.ThreadPoolExecutor(max_workers=1)

        # take main lock in that thread and start other one
        tools.root_lock.acquire()
        future = executor.submit(as_root_function)

        # we didn't get any root switch
        self.assertFalse(osmock.seteuid.called, "we didn't switch to root yet with seteuid")
        self.assertFalse(osmock.setegid.called, "we didn't switch to root yet with setegid")

        # release it
        tools.root_lock.release()

        # wait for the executor to finish in 1s and ensure that root was called
        future.result(1)
        osmock.seteuid.assert_called_once_with(0)
        osmock.setegid.assert_called_once_with(0)
        self.assertTrue(switch_to_current_usermock.called, "switch back to user when exiting context")


class TestUserENV(LoggedTestCase):

    def setUp(self):
        super().setUp()
        self.orig_environ = os.environ.copy()
        self.local_dir = tempfile.mkdtemp()
        os.environ['SHELL'] = '/bin/bash'

    def tearDown(self):
        shutil.rmtree(self.local_dir)
        # restore original environment. Do not use the dict copy which erases the object and doesn't have the magical
        # _Environ which setenv() for subprocess
        os.environ.clear()
        os.environ.update(self.orig_environ)
        super().tearDown()

    @patch("umake.tools.os.path.expanduser")
    def test_add_env_to_user(self, expanderusermock):
        """Test that adding to user env appending to an existing .profile file"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("one path addition", {"FOOO": {"value": "bar"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=bar\n" in profile_content, profile_content)
        self.assertTrue("bar" in os.environ["FOOO"], os.environ["FOOO"])

    @patch("umake.tools.os.path.expanduser")
    def test_add_env_to_user(self, expanderusermock):
        """Test that adding to user env a list concatenate them to an existing .profile file"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("one path addition", {"FOOO": {"value": ["bar", "baz"]}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=bar:baz\n" in profile_content, profile_content)
        self.assertTrue("bar" in os.environ["FOOO"], os.environ["FOOO"])

    @patch("umake.tools.os.path.expanduser")
    def test_add_env_to_user_with_shell_zsh(self, expanderusermock):
        """Test that adding to user env appending to an existing .zprofile file"""
        os.environ['SHELL'] = '/bin/zsh'
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".zprofile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("one path addition", {"FOOO": {"value": "bar"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=bar\n" in profile_content, profile_content)
        self.assertTrue("bar" in os.environ["FOOO"], os.environ["FOOO"])

    @patch("umake.tools.os.path.expanduser")
    def test_add_env_to_user_keep(self, expanderusermock):
        """Test that adding to user env appending to an existing env"""
        os.environ["FOOO"] = "foo"
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("one path addition", {"FOOO": {"value": "bar"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=bar:$FOOO\n" in profile_content, profile_content)
        self.assertEqual(os.environ["FOOO"], "bar:foo")

    @patch("umake.tools.os.path.expanduser")
    def test_add_env_to_user_not_keep(self, expanderusermock):
        """Test that adding to user env without keep replace an existing env"""
        os.environ["FOOO"] = "foo"
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("one path addition", {"FOOO": {"value": "bar", "keep": False}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=bar\n" in profile_content, profile_content)
        self.assertTrue("bar" in os.environ["FOOO"], os.environ["FOOO"])
        self.assertFalse("foo" in os.environ["FOOO"], os.environ["FOOO"])
        self.assertEqual(os.environ["FOOO"], "bar")

    @patch("umake.tools.os.path.expanduser")
    def test_add_env_to_user_empty_file(self, expanderusermock):
        """Test that adding to user env append to an non existing .profile file"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        tools.add_env_to_user("one path addition", {"FOOO": {"value": "/tmp/foo"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("export FOOO=/tmp/foo\n" in profile_content, profile_content)
        self.assertTrue("/tmp/foo" in os.environ["FOOO"], os.environ["FOOO"])

    @patch("umake.tools.os.path.expanduser")
    def test_add_to_user_path_twice(self, expanderusermock):
        """Test that adding to user env twice doesn't add it twice in the file"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("add twice", {"FOOO": {"value": "/tmp/foo"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=/tmp/foo\n" in profile_content, profile_content)

        tools.add_env_to_user("add twice", {"FOOO": {"value": "/tmp/foo"}})

        # ensure, it's only there once
        profile_content = open(profile_file).read()
        self.assertEqual(profile_content.count("export FOOO=/tmp/foo"), 1, profile_content)

    @patch("umake.tools.os.path.expanduser")
    def test_add_to_user_path_twice_with_new_content(self, expanderusermock):
        """Test that adding to some env twice for same framework only add the latest"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("add twice", {"FOOO": {"value": "/tmp/foo"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=/tmp/foo\n" in profile_content, profile_content)

        tools.add_env_to_user("add twice", {"FOOO": {"value": "/tmp/bar"}})

        # ensure, it's only there once
        profile_content = open(profile_file).read()
        self.assertEqual(profile_content.count("export FOOO=/tmp/bar"), 1, profile_content)

    @patch("umake.tools.os.path.expanduser")
    def test_add_to_user_path_twice_other_framework(self, expanderusermock):
        """Test that adding to user env with another framework add them twice"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("add twice", {"FOOO": {"value": "/tmp/foo"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=/tmp/foo\n" in profile_content, profile_content)

        tools.add_env_to_user("add twice with other framework", {"BAR": {"value": "/tmp/bar"}})

        # ensure, it's only there once
        profile_content = open(profile_file).read()
        self.assertTrue("export FOOO=/tmp/foo\n" in profile_content, profile_content)
        self.assertTrue("export BAR=/tmp/bar\n" in profile_content, profile_content)

    @patch("umake.tools.os.path.expanduser")
    def test_add_env_to_user_multiple(self, expanderusermock):
        """Test that adding to user with multiple env for same framework appending to an existing .profile file"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("one path addition", {"FOOO": {"value": "bar"}, "BAR": {"value": "foo"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("export FOOO=bar\n" in profile_content, profile_content)
        self.assertTrue("export BAR=foo\n" in profile_content, profile_content)
        self.assertEqual(os.environ["FOOO"], "bar")
        self.assertEqual(os.environ["BAR"], "foo")

    @patch("umake.tools.os.path.expanduser")
    def test_add_path_to_user(self, expanderusermock):
        """Test that adding to user path doesn't export as PATH is already exported"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n")
        tools.add_env_to_user("one path addition", {"PATH": {"value": "/tmp/bar"}})

        expanderusermock.assert_called_with('~')
        profile_content = open(profile_file).read()
        self.assertTrue("Foo\nBar\n" in profile_content, profile_content)  # we kept previous content
        self.assertTrue("\nPATH=/tmp/bar:$PATH\n" in profile_content, profile_content)
        self.assertTrue("/tmp/bar" in os.environ["PATH"], os.environ["PATH"])

    @patch("umake.tools.os.path.expanduser")
    def test_remove_user_env(self, expanderusermock):
        """Remove an env from a user setup"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n# Ubuntu make installation of framework A"
                                      "\nexport FOO=bar\n\nexport BAR=baz")
        tools.remove_framework_envs_from_user("framework A")

        profile_content = open(profile_file).read()
        self.assertEqual(profile_content, "Foo\nBar\nexport BAR=baz")

    @patch("umake.tools.os.path.expanduser")
    def test_remove_user_env_end(self, expanderusermock):
        """Remove an env from a user setup being at the end of profile file"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n# Ubuntu make installation of framework A"
                                      "\nexport FOO=bar\n\n")
        tools.remove_framework_envs_from_user("framework A")

        profile_content = open(profile_file).read()
        self.assertEqual(profile_content, "Foo\nBar\n")

    @patch("umake.tools.os.path.expanduser")
    def test_remove_user_env_not_found(self, expanderusermock):
        """Remove an env from a user setup with no matching content found"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\nexport BAR=baz")
        tools.remove_framework_envs_from_user("framework A")

        profile_content = open(profile_file).read()
        self.assertEqual(profile_content, "Foo\nBar\nexport BAR=baz")

    @patch("umake.tools.os.path.expanduser")
    def test_remove_user_env_no_file(self, expanderusermock):
        """Remove an env from a user setup with no profile file"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        tools.remove_framework_envs_from_user("framework A")

        self.assertRaises(FileNotFoundError, open, profile_file)

    @patch("umake.tools.os.path.expanduser")
    def test_remove_user_env_multiple_frameworks(self, expanderusermock):
        """Remove an env from a user setup restraining to the correct framework"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n# Ubuntu make installation of framework B\nexport BAR=bar\n\n"
                                      "# Ubuntu make installation of framework A\nexport FOO=bar\n\nexport BAR=baz")
        tools.remove_framework_envs_from_user("framework A")

        profile_content = open(profile_file).read()
        self.assertEqual(profile_content, "Foo\nBar\n# Ubuntu make installation of framework B\nexport BAR=bar\n\n"
                                          "export BAR=baz")

    @patch("umake.tools.os.path.expanduser")
    def test_remove_user_env_multiple_lines(self, expanderusermock):
        """Remove an env from a user setup having multiple lines"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n# Ubuntu make installation of framework A"
                                      "\nexport FOO=bar\nexport BOO=foo\n\nexport BAR=baz")
        tools.remove_framework_envs_from_user("framework A")

        profile_content = open(profile_file).read()
        self.assertEqual(profile_content, "Foo\nBar\nexport BAR=baz")

    @patch("umake.tools.os.path.expanduser")
    def test_remove_user_multiple_same_framework(self, expanderusermock):
        """Remove an env from a user setup, same framework being repeated multiple times"""
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".profile")
        open(profile_file, 'w').write("Foo\nBar\n# Ubuntu make installation of framework A\nexport BAR=bar\n\n"
                                      "# Ubuntu make installation of framework A\nexport FOO=bar\n\nexport BAR=baz")
        tools.remove_framework_envs_from_user("framework A")

        profile_content = open(profile_file).read()
        self.assertEqual(profile_content, "Foo\nBar\nexport BAR=baz")

    @patch("umake.tools.os.path.expanduser")
    def test_remove_user_env_zsh(self, expanderusermock):
        """Remove an env from a user setup using zsh"""
        os.environ['SHELL'] = '/bin/zsh'
        expanderusermock.return_value = self.local_dir
        profile_file = os.path.join(self.local_dir, ".zprofile")
        open(profile_file, 'w').write("Foo\nBar\n# Ubuntu make installation of framework A"
                                      "\nexport FOO=bar\n\nexport BAR=baz")
        tools.remove_framework_envs_from_user("framework A")

        profile_content = open(profile_file).read()
        self.assertEqual(profile_content, "Foo\nBar\nexport BAR=baz")


class TestUserShell(LoggedTestCase):

    def setUp(self):
        super().setUp()
        self.orig_environ = os.environ.copy()
        os.environ['SHELL'] = '/bin/bash'

    def tearDown(self):
        os.environ = self.orig_environ.copy()
        super().tearDown()

    def test_return_shell_bash(self):
        """Default setup should change the bash profile"""
        self.assertTrue(tools._get_shell_profile_file_path().endswith(".profile"))

    def test_can_override_zsh_with_SHELL(self):
        """Can return zsh profile if set"""
        os.environ['SHELL'] = '/bin/zsh'
        self.assertTrue(tools._get_shell_profile_file_path().endswith(".zprofile"))

    def test_return_bash_if_nosense(self):
        """Return bash if content is garbage"""
        os.environ['SHELL'] = 'contain_nothing'
        self.assertTrue(tools._get_shell_profile_file_path().endswith(".profile"))

    def test_return_bash_if_empty(self):
        """Return bash if no key"""
        os.environ.pop('SHELL')
        self.assertTrue(tools._get_shell_profile_file_path().endswith(".profile"))
