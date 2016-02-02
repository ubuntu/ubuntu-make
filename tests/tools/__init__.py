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

"""Common tools between tests"""

# DO NOT IMPORT HERE umake.* directly, only lazy import it in function.
# This file is imported by runtests, before the coverage is enabled.
from io import StringIO
from contextlib import contextmanager, suppress
from copy import deepcopy
import grp
import importlib
import logging
import os
import re
import shutil
import xdg.BaseDirectory
import pexpect
from unittest import TestCase
from unittest.mock import Mock

logger = logging.getLogger(__name__)

BRANCH_TESTS = False
DOCKER = None
UMAKE = "umake"
INSTALL_DIR = ".local/share/umake"
SYSTEM_UMAKE_DIR = "/usr/lib/python3/dist-packages/umake"
BINARY_DIR = "bin"


class LoggedTestCase(TestCase):
    """A base TestCase class which asserts if there is a warning or error unless self.expect_warn_error is True"""

    def setUp(self):
        super().setUp()
        self.error_warn_logs = StringIO()
        self.__handler = logging.StreamHandler(self.error_warn_logs)
        self.__handler.setLevel(logging.WARNING)
        logging.root.addHandler(self.__handler)
        self.expect_warn_error = False

    def tearDown(self):
        super().tearDown()
        logging.root.removeHandler(self.__handler)
        if self.expect_warn_error:
            self.assertNotEqual(self.error_warn_logs.getvalue(), "")
        else:
            self.assertEqual(self.error_warn_logs.getvalue(), "")
        self.error_warn_logs.close()


def get_data_dir():
    """Return absolute data dir path"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))


def get_root_dir():
    """Return absolute project root dir path"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_tools_helper_dir():
    """Return an absolute path to where the runner helpers are"""
    return os.path.abspath(os.path.dirname(__file__))


def assert_files_identicals(filename1, filename2):
    """Assert if the files content are identical"""
    if open(filename1).read() != open(filename2).read():
        logger.error("{}: {}\n{}: {}".format(filename1, open(filename1).read(),
                                             filename2, open(filename2).read()))
        raise AssertionError("{} and {} aren't identical".format(filename1, filename2))


class CopyingMock(Mock):
    """Mock for recording calls with mutable arguments"""
    def __call__(self, *args, **kwargs):
        args = deepcopy(args)
        kwargs = deepcopy(kwargs)
        return super().__call__(*args, **kwargs)


def change_xdg_path(key, value=None, remove=False):
    if value:
        os.environ[key] = value
    if remove:
        with suppress(KeyError):
            os.environ.pop(key)
    import umake.tools
    importlib.reload(xdg.BaseDirectory)
    with suppress(KeyError):
        umake.tools.Singleton._instances.pop(umake.tools.ConfigHandler)
    umake.tools.xdg_config_home = xdg.BaseDirectory.xdg_config_home
    umake.tools.xdg_data_home = xdg.BaseDirectory.xdg_data_home


@contextmanager
def patchelem(element, attr, value):
    old_value = getattr(element, attr)
    setattr(element, attr, value)
    yield
    setattr(element, attr, old_value)


def manipulate_path_env(value, remove=False):
    """prepend value to PATH environment. If remove is true, remove it"""
    path = os.environ["PATH"].split(os.pathsep)
    if remove:
        path.remove(value)
    else:
        path.insert(0, value)
    os.environ["PATH"] = os.pathsep.join(path)


@contextmanager
def swap_file_and_restore(filepath):
    """Let changing the file in the context manager and restore to original one if needed"""
    try:
        original_content = open(filepath).read()
        yield original_content
    finally:
        open(filepath, 'w').write(original_content)


def set_local_umake():
    global UMAKE
    global BRANCH_TESTS
    UMAKE = "./bin/umake"
    BRANCH_TESTS = True


def get_docker_path():
    global DOCKER
    if DOCKER is None:
        DOCKER = shutil.which("docker.io")
        if not DOCKER:
            DOCKER = shutil.which("docker")
    return DOCKER


def local_which(filename):
    """Find filename in $PATH and return it if present"""
    for dir in os.environ["PATH"].split(os.pathsep):
        file_path = os.path.join(dir, filename)
        if os.path.isfile(file_path):
            return file_path
    return None


def get_desktop_file_path(desktop_filename):
    """get the desktop file path"""
    if not desktop_filename:
        return ""

    from umake.tools import get_launcher_path
    importlib.reload(xdg.BaseDirectory)

    return get_launcher_path(desktop_filename)


def get_path_from_desktop_file(desktop_filename, key):
    """get the path referred as key in the desktop filename exists"""
    desktop_file_path = get_desktop_file_path(desktop_filename)
    if not get_desktop_file_path(desktop_file_path):
        return ""

    path = ""
    with open(desktop_file_path) as f:
        for line in f:
            p = re.search(r'{}=(.*)'.format(key), line)
            with suppress(AttributeError):
                path = p.group(1)

    # sanitize the field with unescaped quotes
    for separator in ('"', "'", " "):
        elem_paths = path.split(separator)
        path = ""
        for elem in elem_paths:
            if not elem:
                continue
            # the separator was escaped, read the separator element
            if elem[-1] == "\\":
                elem += separator
            path += elem
            # stop for current sep at first unescaped separator
            if not path.endswith("\\" + separator):
                break
    return path


def is_in_group(group):
    """return if current user is in a group"""
    for group_name in [g.gr_name for g in grp.getgrall() if os.environ["USER"] in g.gr_mem]:
        print(group_name)
        if group_name == group:
            return True
    return False


def spawn_process(command):
    """return a handle to a new controllable child process"""
    return pexpect.spawnu(command, dimensions=(24, 250))
