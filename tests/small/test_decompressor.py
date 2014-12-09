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

"""Tests for the decompressor module"""

import os
from time import time
from unittest.mock import Mock
import shutil
import stat
import tempfile
from ..tools import get_data_dir, LoggedTestCase
from umake.decompressor import Decompressor


class TestDecompressor(LoggedTestCase):
    """This will test the decompressor class"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.compressfiles_dir = os.path.join(get_data_dir(), "compress-files")

    def setUp(self):
        super().setUp()
        self.on_done = Mock()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def wait_for_callback(self, mock_function_to_be_called, timeout=10):
        """wait for the callback to be called until a timeout.

        Add temp files to the clean file list afterwards"""
        timeout_time = time() + 5
        while not mock_function_to_be_called.called:
            if time() > timeout_time:
                raise(BaseException("Function not called within {} seconds".format(timeout)))

    def test_decompress(self):
        """We decompress a valid .tgz file successfully"""
        filepath = os.path.join(self.compressfiles_dir, "valid.tgz")
        self.tempdir = tempfile.mkdtemp()
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir=None)}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEquals(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content', 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'subdir', 'otherfile')))

    def test_decompress_move_dir_content(self):
        """We decompress a valid file decompressing one subdir content (other files in root are kept in place)"""
        filepath = os.path.join(self.compressfiles_dir, "valid.tgz")
        self.tempdir = tempfile.mkdtemp()
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='server-content')},
                     self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEquals(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(self.tempdir))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'subdir', 'otherfile')))

    def test_decompress_invalid_file(self):
        """We return an error if the compressed file is invalid"""
        filepath = os.path.join(self.compressfiles_dir, "invalid.tgz")
        self.tempdir = tempfile.mkdtemp()
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir=None)}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEquals(len(results), 1, str(results))
        for fd in results:
            self.assertIsNotNone(results[fd].error)

    def test_decompress_content_glob(self):
        """We decompress a valid file decompressing one subdir content with a glob schema"""
        filepath = os.path.join(self.compressfiles_dir, "valid.tgz")
        self.tempdir = tempfile.mkdtemp()
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='server-*')},
                     self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEquals(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(self.tempdir))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'subdir', 'otherfile')))

    def test_decompress_zip(self):
        """We decompress a valid zip file successfully"""
        filepath = os.path.join(self.compressfiles_dir, "valid.zip")
        self.tempdir = tempfile.mkdtemp()
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir=None)}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEquals(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'simplefile')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'executablefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content', 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'subdir', 'otherfile')))

    def test_decompress_zip_good_permission(self):
        """We decompress a valid zip file successfully, retaining the right permissions"""
        filepath = os.path.join(self.compressfiles_dir, "valid.zip")
        self.tempdir = tempfile.mkdtemp()
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir=None)}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEquals(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content')))
        simplefile = os.path.join(self.tempdir, 'server-content', 'simplefile')
        self.assertTrue(os.path.isfile(simplefile))
        execfile = os.path.join(self.tempdir, 'server-content', 'executablefile')
        self.assertTrue(os.path.isfile(execfile))
        self.assertEquals(oct(stat.S_IMODE(os.lstat(simplefile).st_mode)), '0o664')
        self.assertEquals(oct(stat.S_IMODE(os.lstat(execfile).st_mode)), '0o775')
