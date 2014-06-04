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

"""Tests for the download center module using a local server"""

import os
from time import time
from unittest import TestCase
from unittest.mock import Mock
from ..tools import *
from ..tools.local_server import LocalHttp
from udtc.download_center import DownloadCenter


class TestDownloadCenter(TestCase):
    """This will test the download center by sending one or more download requests"""

    @classmethod
    def setUpClass(cls):
        super(TestDownloadCenter, cls).setUpClass()
        cls.server_dir = os.path.join(get_data_dir(), "server-content")
        cls.server = LocalHttp(cls.server_dir)

    @classmethod
    def tearDownClass(cls):
        super(TestDownloadCenter, cls).tearDownClass()
        cls.server.stop()

    def setUp(self):
        super(TestDownloadCenter, self).setUp()
        self.callback = Mock()
        self.files_to_clean = []
        for file in self.files_to_clean:
            os.remove(file)

    def tearDown(self):
        super(TestDownloadCenter, self).tearDown()
        for file in self.files_to_clean:
            os.remove(file)

    def build_server_address(self, path):
        """build server address to path to get requested"""
        return "{}/{}".format(self.server.get_address(), path)

    def wait_for_callback(self, mock_function_to_be_called):
        """wait for the callback to be called until a timeout"""
        timeout = time() + 5
        while(not mock_function_to_be_called.called):
            if time() > timeout:
                raise(BaseException("Function not called within 5 seconds"))

    def test_download(self):
        """we deliver one successful download"""
        request = self.build_server_address("foo")
        foo = DownloadCenter([request], self.callback)
        self.wait_for_callback(self.callback)

        temp_file = self.callback.call_args[0][0][request]
        self.assertTrue(self.callback.called)
        self.assertEqual(self.callback.call_count, 1)
        self.files_to_clean.append(temp_file)
        assertFilesIdenticals(os.path.join(self.server_dir, "foo"),
                              temp_file)

    def test_multiple_downloads(self):
        pass

    def test_download_with_progress(self):
        pass

    def test_download_with_multiple_progress(self):
        pass

    def test_wrong_url(self):
        pass