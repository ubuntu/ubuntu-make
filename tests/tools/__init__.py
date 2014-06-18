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

from io import StringIO
from contextlib import contextmanager
from copy import deepcopy
import importlib
import logging
import os
import xdg.BaseDirectory
from unittest import TestCase
from unittest.mock import Mock

logger = logging.getLogger(__name__)


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
            self.assertNotEquals(self.error_warn_logs.getvalue(), "")
        else:
            self.assertEquals(self.error_warn_logs.getvalue(), "")
        self.error_warn_logs.close()


def get_data_dir():
    """Return absolute data dir path"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))


def get_root_dir():
    """Return absolute project root dir path"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


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
        return super(CopyingMock, self).__call__(*args, **kwargs)


def change_xdg_config_path(dirname):
    os.environ['XDG_CONFIG_HOME'] = dirname
    import udtc.tools
    importlib.reload(xdg.BaseDirectory)
    udtc.tools.xdg_config_home = xdg.BaseDirectory.xdg_config_home


@contextmanager
def patchelem(element, attr, value):
    old_value = getattr(element, attr)
    setattr(element, attr, value)
    yield
    setattr(element, attr, old_value)
