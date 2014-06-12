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
        super(TestRequirementsHandler, cls).setUpClass()
        cls.handler = RequirementsHandler()

        apt.apt_pkg.config.clear("APT::Update::Post-Invoke")
        apt.apt_pkg.config.clear("APT::Update::Post-Invoke-Success")
        apt.apt_pkg.config.clear("DPkg::Post-Invoke")
        cls.apt_package_dir = os.path.join(get_data_dir(), "apt")

    def setUp(self):
        super(TestRequirementsHandler, self).setUp()
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
        super(TestRequirementsHandler, self).tearDown()
        shutil.rmtree(self.chroot_path)
        os.remove(self.dpkg)

    def count_number_progress_call(self, call_args_list, tag):
        """Count the number of tag in progress call and return it"""
        count = 0
        for call in call_args_list:
            if call[0][0] == tag:
                count += 1
        return count

    def wait_for_callback(self, mock_function_to_be_called, timeout=5):
        """wait for the callback to be called until a timeout.

        Add temp files to the clean file list afterwards"""
        timeout_time = time() + timeout
        while not mock_function_to_be_called.called:
            if time() > timeout_time:
                raise(BaseException("Function not called within 5 seconds"))

    def test_singleton(self):
        """Ensure we are delivering a singleton for RequirementsHandler"""
        other = RequirementsHandler()
        self.assertEquals(self.handler, other)

    def test_install(self):
        """Install one package"""
        self.handler.install_bucket(["testpackage"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0]["bucket"], ['testpackage'])
        self.assertIsNone(self.done_callback.call_args[0][0]["error"])
        self.assertTrue(self.handler.cache["testpackage"].is_installed)

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
        self.assertEquals(progress_callback.call_args_list[-1][0], (RequirementsHandler.STATUS_INSTALLING, 100))

    def test_install_multiple_packages(self):
        """Install multiple packages in one shot"""
        self.handler.install_bucket(["testpackage", "testpackage0"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0]["bucket"], ['testpackage', 'testpackage0'])
        self.assertIsNone(self.done_callback.call_args[0][0]["error"])
        self.assertTrue(self.handler.cache["testpackage"].is_installed)
        self.assertTrue(self.handler.cache["testpackage0"].is_installed)

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
        self.assertEquals(progress_callback.call_args_list[-1][0], (RequirementsHandler.STATUS_INSTALLING, 100))

    def test_install_twice(self):
        """Test appending two installations and wait for results"""
        self.handler.install_bucket(["testpackage"], lambda x, y: "", lambda x: "")
        self.handler.install_bucket(["testpackage1"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        # TODO: ensure done callback one is before done callback2

    def test_install_twice_same_packages(self):

        # TODO: ensure that progress isn't called the second time?
        pass

    def test_fail(self):
        pass

    def test_package_doesnt_exists(self):
        pass

    def test_error_in_dpkg(self):
        """Test that an error while installing a package is caught"""
        # try an error on dpkg
        with open(self.dpkg, mode='w') as f:
            f.write("#!/bin/sh\nexit 1")
        self.handler.install_bucket(["testpackage"], lambda x, y: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertIsNotNone(self.done_callback.call_args[0][0]["error"])
