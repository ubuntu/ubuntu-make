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
        cls.compressfiles_dir_orig = os.path.join(get_data_dir(), "compress-files")

    def setUp(self):
        super().setUp()
        self.on_done = Mock()
        self.tempdir = tempfile.mkdtemp()
        self.compressfiles_dir = os.path.join(self.tempdir, "source-files")
        shutil.copytree(self.compressfiles_dir_orig, self.compressfiles_dir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        super().tearDown()

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
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='')}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content', 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'subdir', 'otherfile')))
        self.assertEqual(self.on_done.call_count, 1, "Global done callback is only called once")

    def test_decompress_move_dir_content(self):
        """We decompress a valid file decompressing one subdir content (other files in root are kept in place)"""
        filepath = os.path.join(self.compressfiles_dir, "valid.tgz")
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='server-content')},
                     self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(self.tempdir))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'subdir', 'otherfile')))

    def test_decompress_invalid_file(self):
        """We return an error if the compressed file is invalid"""
        self.expect_warn_error = True
        filepath = os.path.join(self.compressfiles_dir, "invalid.tgz")
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='')}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNotNone(results[fd].error)
        self.assertEqual(self.on_done.call_count, 1, "Global done callback is only called once")

    def test_decompress_content_glob(self):
        """We decompress a valid file decompressing one subdir content with a glob schema"""
        filepath = os.path.join(self.compressfiles_dir, "valid.tgz")
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='server-*')},
                     self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(self.tempdir))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'subdir', 'otherfile')))

    def test_decompress_zip(self):
        """We decompress a valid zip file successfully"""
        filepath = os.path.join(self.compressfiles_dir, "valid.zip")
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='')}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
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
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='')}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content')))
        simplefile = os.path.join(self.tempdir, 'server-content', 'simplefile')
        self.assertTrue(os.path.isfile(simplefile))
        execfile = os.path.join(self.tempdir, 'server-content', 'executablefile')
        self.assertTrue(os.path.isfile(execfile))
        self.assertEqual(oct(stat.S_IMODE(os.lstat(simplefile).st_mode)), '0o664')
        self.assertEqual(oct(stat.S_IMODE(os.lstat(execfile).st_mode)), '0o775')

    def test_decompress_exec(self):
        """We decompress a valid executable file successfully"""
        filepath = os.path.join(self.compressfiles_dir, "simple.bin")
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='')}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)

        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'android-ndk-foo')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'android-ndk-foo', 'ndk-which')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'android-ndk-foo', 'ndk-build')))

    def test_decompress_file_with_archive(self):
        """We decompress a .sh file containing an archive successfully"""
        filepath = os.path.join(self.compressfiles_dir, "script_with_archive.sh")
        with open(filepath, 'rb') as fd:
            for line in fd:
                if line.startswith(b"== ARCHIVE TAG =="):
                    break
            Decompressor({fd: Decompressor.DecompressOrder(dest=self.tempdir, dir='')}, self.on_done)
            self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content', 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'subdir', 'otherfile')))

    def test_decompress_wrong_dir_content(self):
        """We decompress a valid file, but the selected subdir isn't valid"""
        self.expect_warn_error = True
        filepath = os.path.join(self.compressfiles_dir, "valid.tgz")
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='doesnt-exists')},
                     self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNotNone(results[fd].error)

    def test_decompress_content_keep_existing_files(self):
        """We decompress a valid file in a directory which already have some content. This one is left."""
        filepath = os.path.join(self.compressfiles_dir, "valid.tgz")
        open(os.path.join(self.tempdir, "foo"), 'w').write('')
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='')},
                     self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(self.tempdir))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content', 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'subdir', 'otherfile')))
        # the original file is there here
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'foo')))

    def test_decompress_move_dir_content_keep_existing_files(self):
        """We decompress a valid file changing dir in a directory which already have some content. This one is left."""
        filepath = os.path.join(self.compressfiles_dir, "valid.tgz")
        open(os.path.join(self.tempdir, "foo"), 'w').write('')
        Decompressor({open(filepath, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='server-content')},
                     self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 1, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(self.tempdir))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'subdir', 'otherfile')))
        # the original file is there here
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'foo')))

    def test_decompress_multiple(self):
        """We decompress multiple valid .tgz file successfully"""
        filepath1 = os.path.join(self.compressfiles_dir, "valid.tgz")
        filepath2 = os.path.join(self.compressfiles_dir, "valid2.tgz")
        Decompressor({open(filepath1, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir=''),
                      open(filepath2, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='')}, self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 2, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content', 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content', 'subdir', 'otherfile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content2')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content2', 'simplefile2')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'server-content2', 'subdir2')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'server-content2', 'subdir2', 'otherfile')))
        self.assertEqual(self.on_done.call_count, 1, "Global done callback is only called once")

    def test_decompress_multiple_with_dir(self):
        """We decompress multiple valid .tgz file successfully with different dir to extract"""
        filepath1 = os.path.join(self.compressfiles_dir, "valid.tgz")
        filepath2 = os.path.join(self.compressfiles_dir, "valid2.tgz")
        Decompressor({open(filepath1, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='server-content'),
                      open(filepath2, 'rb'): Decompressor.DecompressOrder(dest=self.tempdir, dir='server-content2')},
                     self.on_done)
        self.wait_for_callback(self.on_done)

        results = self.on_done.call_args[0][0]
        self.assertEqual(len(results), 2, str(results))
        for fd in results:
            self.assertIsNone(results[fd].error)
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'simplefile')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'subdir')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'subdir', 'otherfile')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'simplefile2')))
        self.assertTrue(os.path.isdir(os.path.join(self.tempdir, 'subdir2')))
        self.assertTrue(os.path.isfile(os.path.join(self.tempdir, 'subdir2', 'otherfile')))
        self.assertEqual(self.on_done.call_count, 1, "Global done callback is only called once")
