# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
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

"""Tests the umake settings handler"""

import os
import shutil
import tempfile
from ..tools import get_data_dir, LoggedTestCase
from unittest.mock import patch

from umake import settings


class TestVersionHandler(LoggedTestCase):
    """This will test the version handler"""

    def setUp(self):
        super().setUp()
        self.from_dev_opt = settings.from_dev
        self.version_dir = tempfile.mkdtemp()
        self.initial_env = os.environ.copy()
        self.initial_os_path_join = os.path.join
        os.environ["PATH"] = "{}:{}".format(os.path.join(get_data_dir(), "mocks"), os.getenv("PATH"))
        self.version_file_path = os.path.join(self.version_dir, "version")
        open(self.version_file_path, "w").write("42.02")

    def tearDown(self):
        # remove caching
        shutil.rmtree(self.version_dir)
        settings.from_dev = self.from_dev_opt
        # restore original environment. Do not use the dict copy which erases the object and doesn't have the magical
        # _Environ which setenv() for subprocess
        os.environ.clear()
        os.environ.update(self.initial_env)
        os.path.join = self.initial_os_path_join
        super().tearDown()

    def return_fake_version_path(self, *args):
        '''Only return fake version path if the request was for that one'''
        if args[-1] == "version":
            return self.version_file_path
        return self.initial_os_path_join(*args)

    @patch("os.path.join")
    def test_version_release(self, path_join_result):
        """Ensure we are returning the right version for a release"""
        path_join_result.side_effect = self.return_fake_version_path
        os.environ.clear()
        os.environ.update(self.initial_env)
        self.assertEqual(settings.get_version(), "42.02")

    @patch("os.path.join")
    def test_version_git(self, path_join_result):
        """Ensure we are returning the right version for a git repo"""
        settings.from_dev = True
        path_join_result.side_effect = self.return_fake_version_path
        self.assertEqual(settings.get_version(), "42.03-25-g1fd9507")

    @patch("os.path.join")
    def test_version_snap(self, path_join_result):
        """Ensure we are returning the right version for a snap"""
        path_join_result.side_effect = self.return_fake_version_path
        os.environ.clear()
        os.environ.update(self.initial_env)
        os.environ["SNAP_REVISION"] = "42"
        self.assertEqual(settings.get_version(), "42.02+snap42")

    @patch("os.path.join")
    def test_version_git_fail(self, path_join_result):
        """Ensure we are returning last known version + unknown if git fails"""
        settings.from_dev = True
        path_join_result.side_effect = self.return_fake_version_path
        os.environ["PATH"] = "{}:{}".format(os.path.join(get_data_dir(), "mocks", "fails"), os.getenv("PATH"))
        self.assertEqual(settings.get_version(), "42.02+unknown")

    @patch("os.path.join")
    def test_version_git_not_installed(self, path_join_result):
        """Ensure we are returning last known version + unknown if git isn't installed"""
        settings.from_dev = True
        path_join_result.side_effect = self.return_fake_version_path
        os.environ["PATH"] = ""
        self.assertEqual(settings.get_version(), "42.02+unknown")
