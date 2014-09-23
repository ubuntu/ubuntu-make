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

from contextlib import suppress
from gettext import gettext as _
from gi.repository import GLib, Gio
from glob import glob
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
from textwrap import dedent
from udtc import settings
from xdg.BaseDirectory import load_first_config, xdg_config_home, xdg_data_home
import yaml
import yaml.scanner
import yaml.parser

logger = logging.getLogger(__name__)

# cache current arch. Shouldn't change in the life of the process ;)
_current_arch = None
_foreign_arch = None
_version = None


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigHandler(metaclass=Singleton):

    def __init__(self):
        """Load the config"""
        self._config = {}
        config_file = load_first_config(settings.CONFIG_FILENAME)
        logger.debug("Opening {}".format(config_file))
        try:
            with open(config_file) as f:
                self._config = yaml.load(f)
        except (TypeError, FileNotFoundError):
            logger.info("No configuration file found")
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            logger.error("Invalid configuration file found: {}".format(e))

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        config_file = os.path.join(xdg_config_home, settings.CONFIG_FILENAME)
        logging.debug("Saving new configuration: {} in {}".format(config, config_file))
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        self._config = config


class NoneDict(dict):
    """We don't use a defaultdict(lambda: None) as it's growing everytime something is requested"""
    def __getitem__(self, key):
        return dict.get(self, key)


class classproperty(object):
    """Class property, similar to instance properties"""
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class MainLoop(object, metaclass=Singleton):
    """Mainloop simple wrapper"""

    def __init__(self):
        self.mainloop = GLib.MainLoop()
        # Glib steals the SIGINT handler and so, causes issue in the callback
        # https://bugzilla.gnome.org/show_bug.cgi?id=622084
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def run(self):
        self.mainloop.run()

    def quit(self, status_code=0, raise_exception=True):
        GLib.timeout_add(80, self._clean_up, status_code)
        # only raises exception if not turned down (like in tests, where we are not in the mainloop for sure)
        if raise_exception:
            raise self.ReturnMainLoop()

    def _clean_up(self, exit_code):
        self.mainloop.quit()
        sys.exit(exit_code)

    @staticmethod
    def in_mainloop_thread(function):
        """Decorator to run a function in a mainloop thread"""

        # GLib.idle_add doesn't propagate try: except in the mainloop, so we handle it there for all functions
        def wrapper(*args, **kwargs):
            try:
                function(*args, **kwargs)
            except MainLoop.ReturnMainLoop:
                pass
            except BaseException:
                logger.exception("Unhandled exception")
                GLib.idle_add(MainLoop().quit, 1, False)

        def inner(*args, **kwargs):
            return GLib.idle_add(wrapper, *args, **kwargs)
        return inner

    class ReturnMainLoop(BaseException):
        """Exception raised only to return to MainLoop without finishing the function"""


class InputError(BaseException):
    """Exception raised for errors in the input.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_current_arch():
    """Get current configuration dpkg architecture"""
    global _current_arch
    if _current_arch is None:
        _current_arch = subprocess.check_output(["dpkg", "--print-architecture"], universal_newlines=True).rstrip("\n")
    return _current_arch


def get_foreign_archs():
    """Get foreign architectures that were enabled"""
    global _foreign_arch
    if _foreign_arch is None:
        _foreign_arch = subprocess.check_output(["dpkg", "--print-foreign-architectures"], universal_newlines=True)\
            .rstrip("\n").split()
    return _foreign_arch


def get_current_ubuntu_version():
    """Return current ubuntu version or raise an error if couldn't find any"""
    global _version
    if _version is None:
        try:
            with open(settings.LSB_RELEASE_FILE) as lsb_release_file:
                for line in lsb_release_file:
                    line = line.strip()
                    if line.startswith('DISTRIB_RELEASE='):
                        tag, release = line.split('=', 1)
                        _version = release
                        break
                else:
                    message = "Couldn't find DISTRIB_RELEASE in {}".format(settings.LSB_RELEASE_FILE)
                    logger.error(message)
                    raise BaseException(message)
        except (FileNotFoundError, IOError) as e:
            message = "Can't open lsb-release file: {}".format(e)
            logger.error(message)
            raise BaseException(message)
    return _version


def is_completion_mode():
    """Return true if we are in completion mode"""
    if os.environ.get('_ARGCOMPLETE') == '1':
        return True
    return False


def get_user_frameworks_path():
    """Return user frameworks local path"""
    return os.path.expanduser(os.path.join('~', '.udtc', 'frameworks'))


def get_icon_path(icon_filename):
    """Return local icon path"""
    return os.path.join(xdg_data_home, "icons", icon_filename)


def get_launcher_path(desktop_filename):
    """Return launcher path"""
    return os.path.join(xdg_data_home, "applications", desktop_filename)


def launcher_exists(desktop_filename):
    """Return true if the desktop filename exists"""
    exists = os.path.exists(get_launcher_path(desktop_filename))
    if not exists:
        logger.debug("{} doesn't exists".format(desktop_filename))
        return False
    return True


def launcher_exists_and_is_pinned(desktop_filename):
    """Return true if the desktop filename is pinned in the launcher"""
    if not launcher_exists(desktop_filename):
        return False
    if os.environ.get("XDG_CURRENT_DESKTOP") != "Unity":
        logger.debug("Don't check launcher as current environment isn't Unity")
        return True
    if "com.canonical.Unity.Launcher" not in Gio.Settings.list_schemas():
        logger.debug("In an Unity environment without the Launcher schema file")
        return False
    gsettings = Gio.Settings(schema_id="com.canonical.Unity.Launcher", path="/com/canonical/unity/launcher/")
    launcher_list = gsettings.get_strv("favorites")
    return "application://" + desktop_filename in launcher_list


def copy_icon(source_icon_filepath, icon_filename):
    """copy icon from source filepath to xdg destination as icon_filename

    globs are accepted in the filepath"""
    icon_path = get_icon_path(icon_filename)
    os.makedirs(os.path.dirname(icon_path), exist_ok=True)
    for file_path in glob(source_icon_filepath):
        logger.debug("Copy icon from {} to {}".format(file_path, icon_path))
        shutil.copy(file_path, icon_path)
        break
    else:
        logger.warning("Didn't find any icon for the launcher.")


def create_launcher(desktop_filename, content):
    """Create a desktop file and an unity launcher icon"""

    # Create file in standard location
    launcher_path = get_launcher_path(desktop_filename)
    os.makedirs(os.path.dirname(launcher_path), exist_ok=True)
    logger.debug("Create launcher as {}".format(launcher_path))
    with open(launcher_path, "w") as f:
        f.write(content)

    if "com.canonical.Unity.Launcher" not in Gio.Settings.list_schemas():
        logger.info("Don't create a launcher icon, as we are not under Unity")
        return
    gsettings = Gio.Settings(schema_id="com.canonical.Unity.Launcher", path="/com/canonical/unity/launcher/")
    launcher_list = gsettings.get_strv("favorites")
    launcher_tag = "application://{}".format(desktop_filename)
    if launcher_tag not in launcher_list:
        index = len(launcher_list)
        with suppress(ValueError):
            index = launcher_list.index("unity://running-apps")
        launcher_list.insert(index, launcher_tag)
        gsettings.set_strv("favorites", launcher_list)


def get_application_desktop_file(name="", icon_path="", exec="", comment="", categories="", extra=""):
    """Get a desktop file string content"""
    return dedent("""\
                [Desktop Entry]
                Version=1.0
                Type=Application
                Name={name}
                Icon={icon_path}
                Exec={exec}
                Comment={comment}
                Categories={categories}
                Terminal=false
                {extra}
                """).format(name=name, icon_path=icon_path, exec=exec,
                            comment=comment, categories=categories, extra=extra)


def strip_tags(content):
    """Strip all HTML tags from content"""
    return re.sub('<[^<]+?>', '', content)


def switch_to_current_user():
    """Switch euid and guid to current user if current user is root"""
    if os.geteuid() != 0:
        return
    # fallback to root user if no SUDO_GID (should be su - root)
    os.setegid(int(os.getenv("SUDO_GID", default=0)))
    os.seteuid(int(os.getenv("SUDO_UID", default=0)))


def add_to_user_path(paths, framework_tag):
    """Add paths to user path in .bashrc if path isn't already in PATH"""
    paths_to_add = []
    for path in paths:
        if path not in os.environ['PATH']:  # we don't care how, but the path already covers it
            paths_to_add.append(path)
    path_string = os.pathsep.join(paths_to_add)

    if not path_string:
        return

    os.environ['PATH'] = path_string + os.pathsep + os.environ['PATH']
    logger.debug("Adding {} to user PATH for {}".format(path_string, framework_tag))
    with open(os.path.join(os.path.expanduser('~'), ".bashrc"), "a", encoding='utf-8') as f:
        f.write("\n")
        f.write(_("# UDTC installation of {}\n").format(framework_tag))
        f.write("PATH={}:$PATH\n".format(path_string))
