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
from unittest.mock import Mock, call
from ..tools import *
from ..tools.local_server import LocalHttp
from udtc.network.download_center import DownloadCenter


class TestDownloadCenter(TestCase):
    """This will test the download center by sending one or more download requests"""

    BLOCK_SIZE = 1024*8 # from urlretrieve code

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
        """wait for the callback to be called until a timeout.

        Add temp files to the clean file list afterwards"""
        timeout = time() + 5
        while(not mock_function_to_be_called.called):
            if time() > timeout:
                raise(BaseException("Function not called within 5 seconds"))
        for calls in mock_function_to_be_called.call_args[0]:
            for request in calls:
                self.files_to_clean.append(calls[request])

    def test_download(self):
        """we deliver one successful download"""
        filename = "simplefile"
        request = self.build_server_address(filename)
        foo = DownloadCenter([request], self.callback)
        self.wait_for_callback(self.callback)

        temp_file = self.callback.call_args[0][0][request]
        self.assertTrue(self.callback.called)
        self.assertEqual(self.callback.call_count, 1)
        assertFilesIdenticals(os.path.join(self.server_dir, filename),
                              temp_file)

    def test_download_with_progress(self):
        """we deliver progress hook while downloading"""
        filename = "simplefile"
        filesize = os.path.getsize(os.path.join(self.server_dir, filename))
        report = CopyingMock()
        request = self.build_server_address(filename)
        foo = DownloadCenter([request], self.callback, report=report)
        self.wait_for_callback(self.callback)

        self.assertEqual(report.call_count, 2)
        self.assertEqual(report.call_args_list,
                         [call({self.build_server_address(filename): {'size': filesize, 'current': 0}}),
                          call({self.build_server_address(filename): {'size': filesize, 'current': filesize}})])

    def test_download_with_multiple_progress(self):
        """we deliver multiple progress hooks on bigger files"""
        filename = "biggerfile"
        filesize = os.path.getsize(os.path.join(self.server_dir, filename))
        report = CopyingMock()
        request = self.build_server_address(filename)
        foo = DownloadCenter([request], self.callback, report=report)
        self.wait_for_callback(self.callback)

        self.assertEqual(report.call_count, 3)
        self.assertEqual(report.call_args_list,
                         [call({self.build_server_address(filename): {'size': filesize, 'current': 0}}),
                          call({self.build_server_address(filename): {'size': filesize, 'current': self.BLOCK_SIZE}}),
                          call({self.build_server_address(filename): {'size': filesize, 'current': filesize}})])

    def test_multiple_downloads(self):
        """we deliver more than on download in parallel"""
        requests = [self.build_server_address("biggerfile"), self.build_server_address("simplefile")]
        foo = DownloadCenter(requests, self.callback)
        self.wait_for_callback(self.callback)

        # ensure we saw 2 different requests
        callback_args, callback_kwargs = self.callback.call_args
        map_result = callback_args[0]
        self.assertIn(self.build_server_address("biggerfile"), map_result)
        self.assertIn(self.build_server_address("simplefile"), map_result)
        # ensure each temp file corresponds to the source content
        for filename in ("biggerfile", "simplefile"):
            assertFilesIdenticals(os.path.join(self.server_dir, filename),
                                  map_result[self.build_server_address(filename)])

    def test_multiple_downloads_with_reports(self):
        """we deliver more than on download in parallel"""
        requests = [self.build_server_address("biggerfile"), self.build_server_address("simplefile")]
        report = CopyingMock()
        foo = DownloadCenter(requests, self.callback, report=report)
        self.wait_for_callback(self.callback)

        self.assertEqual(report.call_count, 5)
        # ensure that first call only contains one file
        callback_args, callback_kwargs = report.call_args_list[0]
        map_result = callback_args[0]
        self.assertTrue(len(map_result) == 1)
        # ensure that last call is what we expect
        result_dict = {}
        for filename in ("biggerfile", "simplefile"):
            file_size = os.path.getsize(os.path.join(self.server_dir, filename))
            result_dict[self.build_server_address(filename)] = {'size': file_size,
                                                                'current': file_size}
        self.assertEqual(report.call_args, call(result_dict))


    def test_wrong_url(self):
        pass

    def test_download_same_file_multiple_times(self):
        pass