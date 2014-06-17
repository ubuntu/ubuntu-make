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

import apt
import os
import shutil
import stat
import tempfile
from time import time
from ..tools import get_data_dir
from unittest import TestCase
from unittest.mock import Mock, call
from udtc.network.requirements_handler import RequirementsHandler


class TestRequirementsHandler(TestCase):
    """This will test the download center by sending one or more download requests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = RequirementsHandler()

        apt.apt_pkg.config.clear("APT::Update::Post-Invoke")
        apt.apt_pkg.config.clear("APT::Update::Post-Invoke-Success")
        apt.apt_pkg.config.clear("DPkg::Post-Invoke")
        cls.apt_package_dir = os.path.join(get_data_dir(), "apt")

    def setUp(self):
        super().setUp()
        self.chroot_path = tempfile.mkdtemp()

        # create the fake dpkg wrapper
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("#!/bin/sh\nfakeroot dpkg --root={root} --force-not-root --force-bad-path "
                    "--log={root}/var/log/dpkg.log \"$@\"".format(root=self.chroot_path))
            self.dpkg = f.name
        st = os.stat(self.dpkg)
        os.chmod(self.dpkg, st.st_mode | stat.S_IEXEC)

        # apt requirements
        apt_etc = os.path.join(self.chroot_path, 'etc', 'apt')
        os.makedirs(apt_etc)
        os.makedirs(os.path.join(self.chroot_path, 'var', 'log', 'apt'))
        with open(os.path.join(apt_etc, 'sources.list'), 'w') as f:
            f.write('deb file:{} /'.format(self.apt_package_dir))

        # dpkg requirements
        dpkg_dir = os.path.join(self.chroot_path, 'var', 'lib', 'dpkg')
        os.makedirs(dpkg_dir)
        os.mkdir(os.path.join(os.path.join(dpkg_dir, 'info')))
        os.mkdir(os.path.join(os.path.join(dpkg_dir, 'triggers')))
        os.mkdir(os.path.join(os.path.join(dpkg_dir, 'updates')))
        open(os.path.join(dpkg_dir, 'status'), 'w').close()
        open(os.path.join(dpkg_dir, 'available'), 'w').close()

        cache = apt.Cache(rootdir=self.chroot_path)
        apt.apt_pkg.config.set("Dir::Bin::dpkg", self.dpkg)  # must be called after initializing the rootdir bcache
        cache.update()
        self.handler.cache = apt.Cache()

        self.done_callback = Mock()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.chroot_path)
        os.remove(self.dpkg)

    def count_number_progress_call(self, call_args_list, tag):
        """Count the number of tag in progress call and return it"""
        count = 0
        for call in call_args_list:
            if call[0][0] == tag:
                count += 1
        return count

    def wait_for_callback(self, mock_function_to_be_called, timeout=10):
        """wait for the callback to be called until a timeout.

        Add temp files to the clean file list afterwards"""
        timeout_time = time() + timeout
        while not mock_function_to_be_called.called:
            if time() > timeout_time:
                raise(BaseException("Function not called within {} seconds".format(timeout)))

    def test_singleton(self):
        """Ensure we are delivering a singleton for RequirementsHandler"""
        other = RequirementsHandler()
        self.assertEquals(self.handler, other)

    def test_install(self):
        """Install one package"""
        self.handler.install_bucket(["testpackage"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0].bucket, ['testpackage'])
        self.assertIsNone(self.done_callback.call_args[0][0].error)
        self.assertTrue(self.handler.is_bucket_installed(["testpackage"]))

    def test_install_progress(self):
        """Install one package and get progress feedback"""
        progress_callback = Mock()
        self.handler.install_bucket(["testpackage"], progress_callback, self.done_callback)
        self.wait_for_callback(self.done_callback)

        downloading_msg = self.count_number_progress_call(progress_callback.call_args_list,
                                                          RequirementsHandler.STATUS_DOWNLOADING)
        installing_msg = self.count_number_progress_call(progress_callback.call_args_list,
                                                         RequirementsHandler.STATUS_INSTALLING)
        self.assertTrue(downloading_msg > 1)
        self.assertTrue(installing_msg > 1)

    def test_install_multiple_packages(self):
        """Install multiple packages in one shot"""
        self.handler.install_bucket(["testpackage", "testpackage0"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0].bucket, ['testpackage', 'testpackage0'])
        self.assertIsNone(self.done_callback.call_args[0][0].error)
        self.assertTrue(self.handler.is_bucket_installed(["testpackage", "testpackage0"]))

    def test_install_multiple_packages_progress(self):
        """Install multiple packages in one shot and ensure that progress is global"""
        progress_callback = Mock()
        self.handler.install_bucket(["testpackage", "testpackage0"], progress_callback, self.done_callback)
        self.wait_for_callback(self.done_callback)

        downloading_msg = self.count_number_progress_call(progress_callback.call_args_list,
                                                          RequirementsHandler.STATUS_DOWNLOADING)
        installing_msg = self.count_number_progress_call(progress_callback.call_args_list,
                                                         RequirementsHandler.STATUS_INSTALLING)
        self.assertTrue(downloading_msg > 1)
        self.assertTrue(installing_msg > 1)

    def test_install_pending(self):
        """Appending two installations and wait for results. Only the first call should have progress"""
        done_callback0 = Mock()
        self.handler.install_bucket(["testpackage"], lambda x, y: "", self.done_callback)
        self.handler.install_bucket(["testpackage0"], lambda x, y: "", done_callback0)
        self.wait_for_callback(self.done_callback)
        self.wait_for_callback(done_callback0)

        self.assertTrue(self.handler.is_bucket_installed(["testpackage", "testpackage0"]))

    def test_install_pending_order(self):
        """Installation order of pending requests are respected"""
        done_callback = Mock()
        done_callback.side_effect = self.done_callback
        done_callback0 = Mock()
        done_callback0.side_effect = self.done_callback
        ordered_progress_callback = Mock()
        progress_callback = Mock()
        progress_callback.side_effect = ordered_progress_callback
        progress_callback0 = Mock()
        progress_callback0.side_effect = ordered_progress_callback
        self.handler.install_bucket(["testpackage"], progress_callback, done_callback)
        self.handler.install_bucket(["testpackage0"], progress_callback0, done_callback0)
        self.wait_for_callback(done_callback)
        self.wait_for_callback(done_callback0)

        self.assertEqual(self.done_callback.call_args_list,
                         [call(RequirementsHandler.RequirementsResult(bucket=['testpackage'], error=None)),
                          call(RequirementsHandler.RequirementsResult(bucket=['testpackage0'], error=None))])
        # we will get progress with 0, 1 (first bucket), 0, 1 (second bucket). So 4 progress signal status change
        current_status = RequirementsHandler.STATUS_DOWNLOADING
        current_status_change_count = 1
        calls = ordered_progress_callback.call_args_list
        for current_call in calls[1:]:
            if current_call[0][0] != current_status:
                current_status = current_call[0][0]
                current_status_change_count += 1
        self.assertEqual(current_status_change_count, 4)

    def test_install_pending_callback_not_mixed(self):
        """Callbacks are separated on pending requests"""
        done_callback = Mock()
        done_callback.side_effect = self.done_callback
        done_callback0 = Mock()
        done_callback0.side_effect = self.done_callback
        global_progress_callback = Mock()
        progress_callback = Mock()
        progress_callback.side_effect = global_progress_callback
        progress_callback0 = Mock()
        progress_callback0.side_effect = global_progress_callback
        self.handler.install_bucket(["testpackage"], progress_callback, done_callback)
        self.handler.install_bucket(["testpackage0"], progress_callback0, done_callback0)
        self.wait_for_callback(done_callback)
        self.wait_for_callback(done_callback0)

        self.assertTrue(progress_callback.call_count < global_progress_callback.call_count)
        self.assertTrue(progress_callback0.call_count < global_progress_callback.call_count)
        self.assertTrue(done_callback.call_count < self.done_callback.call_count)
        self.assertTrue(done_callback0.call_count < self.done_callback.call_count)

    def test_install_twice(self):
        """Test appending two installations and wait for results. Only the first call should have progress"""
        progress_callback = Mock()
        progress_second_callback = Mock()
        done_callback = Mock()
        self.handler.install_bucket(["testpackage"], progress_callback, done_callback)
        self.handler.install_bucket(["testpackage"], progress_second_callback, self.done_callback)
        self.wait_for_callback(done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertTrue(self.handler.is_bucket_installed(["testpackage"]))
        self.assertFalse(progress_second_callback.called)

    def test_deps(self):
        """Installing one package, ensure the dep (even with auto_fix=False) is installed"""
        self.handler.install_bucket(["testpackage1"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertTrue(self.handler.is_bucket_installed(["testpackage1", "testpackage"]))

    def test_fail(self):
        """An error is caught when asking for the impossible (installing 2 packages in conflicts)"""
        self.handler.install_bucket(["testpackage", "testpackage2"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertIsNotNone(self.done_callback.call_args[0][0].error)
        self.assertTrue(self.handler.is_bucket_installed(["testpackage"]))
        self.assertFalse(self.handler.is_bucket_installed(["testpackage2"]))

    def test_install_shadow_pkg(self):
        """An error is caught if we try to install a none existing package"""
        self.handler.install_bucket(["foo"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertIsNotNone(self.done_callback.call_args[0][0].error)

    def test_error_in_dpkg(self):
        """An error while installing a package is caught"""
        with open(self.dpkg, mode='w') as f:
            f.write("#!/bin/sh\nexit 1")  # Simulate an error in dpkg
        self.handler.install_bucket(["testpackage"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertIsNotNone(self.done_callback.call_args[0][0].error)

    def test_is_installed_bucket_installed(self):
        """Install bucket should return True if a bucket is installed"""
        self.handler.install_bucket(["testpackage", "testpackage1"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)
        self.assertTrue(self.handler.is_bucket_installed(['testpackage', 'testpackage1']))

    def test_is_installed_bucket_half_installed(self):
        """Install bucket shouldn't be considered installed if not fully installed"""
        self.handler.install_bucket(["testpackage"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)
        self.assertFalse(self.handler.is_bucket_installed(['testpackage', 'testpackage1']))

    def test_is_installed_bucket_not_installed(self):
        """Install bucket should return False if a bucket is installed"""
        self.assertFalse(self.handler.is_bucket_installed(['testpackage', 'testpackage1']))
