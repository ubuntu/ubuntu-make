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
import subprocess
import tempfile
from time import time
from ..tools import get_data_dir, LoggedTestCase, manipulate_path_env
from unittest.mock import Mock, call, patch
import umake
from umake.network.requirements_handler import RequirementsHandler
from umake import tools


class TestRequirementsHandler(LoggedTestCase):
    """This will test the download center by sending one or more download requests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = RequirementsHandler()

        apt.apt_pkg.config.set("Dir::Cache::pkgcache", "")
        apt.apt_pkg.config.set("Dir::Cache::srcpkgcache", "")
        apt.apt_pkg.config.clear("APT::Update::Post-Invoke")
        apt.apt_pkg.config.clear("APT::Update::Post-Invoke-Success")
        apt.apt_pkg.config.clear("DPkg::Post-Invoke")
        cls.apt_package_dir = os.path.join(get_data_dir(), "apt")
        cls.apt_status_dir = os.path.join(cls.apt_package_dir, "states")

    def setUp(self):
        super().setUp()
        self.chroot_path = tempfile.mkdtemp()

        # create the fake dpkg wrapper
        os.makedirs(os.path.join(self.chroot_path, "usr", "bin"))
        self.dpkg = os.path.join(self.chroot_path, "usr", "bin", "dpkg")
        with open(self.dpkg, "w") as f:
            f.write("#!/bin/sh\nfakeroot /usr/bin/dpkg --root={root} --force-not-root --force-bad-path "
                    "--log={root}/var/log/dpkg.log \"$@\"".format(root=self.chroot_path))
        st = os.stat(self.dpkg)
        os.chmod(self.dpkg, st.st_mode | stat.S_IEXEC)

        # for arch cache support
        tools._current_arch = None
        tools._foreign_arch = None
        manipulate_path_env(os.path.dirname(self.dpkg))

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
        self.dpkg_dir = dpkg_dir

        cache = apt.Cache(rootdir=self.chroot_path)
        apt.apt_pkg.config.set("Dir::Bin::dpkg", self.dpkg)  # must be called after initializing the rootdir cache
        cache.update()
        cache.open()
        self.handler.cache = cache

        self.done_callback = Mock()

        self._saved_seteuid_fn = os.seteuid
        self._saved_setegid_fn = os.setegid
        self._saved_geteuid_fn = os.geteuid
        self._saved_getenv = os.getenv

        self.user_uid, self.user_gid = (4242, 4242)

        os.seteuid = Mock()
        os.setegid = Mock()
        os.geteuid = Mock()
        os.geteuid.return_value = self.user_uid
        os.getenv = Mock(side_effect=self._mock_get_env)

    def tearDown(self):
        # remove arch cache support
        manipulate_path_env(os.path.dirname(self.dpkg), remove=True)

        tools._current_arch = None
        tools._foreign_arch = None

        shutil.rmtree(self.chroot_path)

        os.seteuid = self._saved_seteuid_fn
        os.setegid = self._saved_setegid_fn
        os.geteuid = self._saved_geteuid_fn
        os.getenv = self._saved_getenv

        super().tearDown()

    def _mock_get_env(self, env, default=None):
        if os.geteuid() == 0:
            if env == "SUDO_UID":
                return str(self.user_uid)
            elif env == "SUDO_GID":
                return str(self.user_gid)
        return self._saved_getenv(env)

    def count_number_progress_call(self, call_args_list, tag):
        """Count the number of tag in progress call and return it"""
        count = 0
        for call in call_args_list:
            if call[0][0]['step'] == tag:
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
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0].bucket, ['testpackage'])
        self.assertIsNone(self.done_callback.call_args[0][0].error)
        self.assertTrue(self.handler.is_bucket_installed(["testpackage"]))

    def test_install_multi_arch_current_arch(self):
        """We install a multi_arch package corresponding to current arch"""
        multi_arch_name = "testpackage:{}".format(tools.get_current_arch())
        self.handler.install_bucket([multi_arch_name], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0].bucket, [multi_arch_name])
        self.assertIsNone(self.done_callback.call_args[0][0].error)
        self.assertTrue(self.handler.is_bucket_installed(["testpackage"]))

    def test_install_perm(self):
        """When we install one package, we first switch to root"""
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        os.seteuid.assert_called_once_with(0)
        os.setegid.assert_called_once_with(0)

    def test_install_return_error_if_no_perm(self):
        """Return an exception when we try to install and we can't switch to root"""
        os.seteuid.side_effect = PermissionError()
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertIsNotNone(self.done_callback.call_args[0][0].error)
        self.assertFalse(self.handler.is_bucket_installed(["testpackage"]))
        self.expect_warn_error = True

    def test_install_perm_switch_back_user(self):
        """When we install one package, we switch back to user at the end"""
        umake.network.requirements_handler.os.geteuid.return_value = 0
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        # we call it twice and the latest is the user id
        self.assertEquals(os.seteuid.call_count, 2)
        self.assertEquals(os.seteuid.call_args, call(self.user_uid))
        self.assertEquals(os.setegid.call_args, call(self.user_gid))

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
        # the first download call is at 0% of progress. testpackage is 1byte to download
        self.assertEquals(progress_callback.call_args_list[0][0][0],
                          {'step': 0, 'pkg_size_download': 1, 'percentage': 0.0})
        self.assertEquals(progress_callback.call_args_list[2][0][0],
                          {'step': 1, 'percentage': 0.0})

    def test_install_multiple_packages(self):
        """Install multiple packages in one shot"""
        self.handler.install_bucket(["testpackage", "testpackage0"], lambda x: "", self.done_callback)
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
        # the first download call is at 0% of progress. testpackage is 1byte to download
        self.assertEquals(progress_callback.call_args_list[0][0][0],
                          {'step': 0, 'pkg_size_download': 1, 'percentage': 0.0})

    def test_install_pending(self):
        """Appending two installations and wait for results. Only the first call should have progress"""
        done_callback0 = Mock()
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.handler.install_bucket(["testpackage0"], lambda x: "", done_callback0)
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
            if current_call[0][0]['step'] != current_status:
                current_status = current_call[0][0]['step']
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
        self.handler.install_bucket(["testpackage1"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertTrue(self.handler.is_bucket_installed(["testpackage1", "testpackage"]))

    def test_fail(self):
        """An error is caught when asking for the impossible (installing 2 packages in conflicts)"""
        self.handler.install_bucket(["testpackage", "testpackage2"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertIsNotNone(self.done_callback.call_args[0][0].error)
        both_package_installed = self.handler.is_bucket_installed(["testpackage"]) and \
            self.handler.is_bucket_installed(["testpackage2"])
        self.assertFalse(both_package_installed)
        self.expect_warn_error = True

    def test_install_shadow_pkg(self):
        """We return an error if we try to install a none existing package"""
        self.handler.install_bucket(["foo"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertIsNotNone(self.done_callback.call_args[0][0].error)
        self.expect_warn_error = True

    def test_error_in_dpkg(self):
        """An error while installing a package is caught"""
        with open(self.dpkg, mode='w') as f:
            f.write("#!/bin/sh\nexit 1")  # Simulate an error in dpkg
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertIsNotNone(self.done_callback.call_args[0][0].error)
        self.expect_warn_error = True

    def test_is_installed_bucket_installed(self):
        """Install bucket should return True if a bucket is installed"""
        self.handler.install_bucket(["testpackage", "testpackage1"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)
        self.assertTrue(self.handler.is_bucket_installed(['testpackage', 'testpackage1']))

    def test_is_installed_bucket_half_installed(self):
        """Install bucket shouldn't be considered installed if not fully installed"""
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)
        self.assertFalse(self.handler.is_bucket_installed(['testpackage', 'testpackage1']))

    def test_is_installed_bucket_not_installed(self):
        """Install bucket should return False if a bucket is not installed"""
        self.assertFalse(self.handler.is_bucket_installed(['testpackage', 'testpackage1']))

    def test_is_bucket_installed_multi_arch_current_arch(self):
        """Installed bucket should return True even if contains multi-arch part with current package"""
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)
        self.assertTrue(self.handler.is_bucket_installed(["testpackage:{}".format(tools.get_current_arch())]))

    def test_is_bucket_installed_with_unavailable_package(self):
        """Bucket isn't installed if some package are even not in the cache"""
        self.assertFalse(self.handler.is_bucket_installed(["testpackagedoesntexist"]))

    def test_is_bucket_installed_with_unavailable_multiarch_package(self):
        """Bucket isn't installed if some multiarch package are even not in the cache"""
        self.assertFalse(self.handler.is_bucket_installed(["testpackagedoesntexist:foo"]))

    def test_is_bucket_installed_with_foreign_archs_package_not_installed(self):
        """After adding a foreign arch, test that the package is not installed and report so"""
        subprocess.call([self.dpkg, "--add-architecture", "foo"])
        self.handler.cache.open()   # reopen the cache with the new added architecture

        self.assertFalse(self.handler.is_bucket_installed(['testpackagefoo:foo']))

    def test_is_bucket_uptodate_bucket_uptodate(self):
        """Up to date bucket is reported as such"""
        self.handler.install_bucket(["testpackage", "testpackage1"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)
        self.assertTrue(self.handler.is_bucket_uptodate(['testpackage', 'testpackage1']))

    def test_is_bucket_uptodate_bucket_not_installed(self):
        """Not installed bucket is not uptodate"""
        self.assertFalse(self.handler.is_bucket_uptodate(['testpackage', 'testpackage1']))

    def test_is_bucket_uptodate_bucket_half_installed(self):
        """bucket shouldn't be considered up to date if not fully installed"""
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)
        self.assertFalse(self.handler.is_bucket_uptodate(['testpackage', 'testpackage1']))

    def test_is_bucket_uptodate_multi_arch_current_arch(self):
        """Installed bucket should return as being uptodate even if contains multi-arch part with current package"""
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)
        self.assertTrue(self.handler.is_bucket_uptodate(["testpackage:{}".format(tools.get_current_arch())]))

    def test_is_bucket_uptodate_with_unavailable_package(self):
        """Bucket isn't uptodate if some package are even not in the cache"""
        self.assertFalse(self.handler.is_bucket_uptodate(["testpackagedoesntexist"]))

    def test_is_bucket_uptodate_with_unavailable_multiarch_package(self):
        """Bucket isn't uptodate if some multiarch package are even not in the cache"""
        self.assertFalse(self.handler.is_bucket_uptodate(["testpackagedoesntexist:foo"]))

    def test_is_bucket_uptodate_with_foreign_archs(self):
        """After adding a foreign arch, test that the package is uptodate and report so"""
        subprocess.call([self.dpkg, "--add-architecture", "foo"])
        self.handler.cache.open()   # reopen the cache with the new added architecture
        self.handler.install_bucket(["testpackagefoo:foo"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertTrue(self.handler.is_bucket_uptodate(['testpackagefoo:foo']))

    def test_is_bucket_uptodate_with_foreign_archs_package_not_installed(self):
        """After adding a foreign arch, test that the package is not uptodate and report so"""
        subprocess.call([self.dpkg, "--add-architecture", "foo"])
        self.handler.cache.open()   # reopen the cache with the new added architecture

        self.assertFalse(self.handler.is_bucket_uptodate(['testpackagefoo:foo']))

    def test_is_bucket_uptodate_with_possible_upgrade(self):
        """If one package of the bucket can be upgraded, tell it's not up to date"""
        shutil.copy(os.path.join(self.apt_status_dir, "testpackage_installed_dpkg_status"),
                    os.path.join(self.dpkg_dir, "status"))
        self.handler.cache.open()
        self.assertFalse(self.handler.is_bucket_uptodate(["testpackage"]))

    def test_is_bucket_available(self):
        """An available bucket on that platform is reported"""
        self.assertTrue(self.handler.is_bucket_available(['testpackage', 'testpackage1']))

    def test_is_bucket_available_multi_arch_current_arch(self):
        """We return a package is available on the current platform"""
        self.assertTrue(self.handler.is_bucket_available(['testpackage:{}'.format(tools.get_current_arch())]))

    def test_unavailable_bucket(self):
        """An unavailable bucket on that platform is reported"""
        self.assertFalse(self.handler.is_bucket_available(['testpackage42', 'testpackage404']))

    def test_is_bucket_available_foreign_archs(self):
        """After adding a foreign arch, test that the package is available on it"""
        subprocess.call([self.dpkg, "--add-architecture", "foo"])
        self.handler.cache.open()  # reopen the cache with the new added architecture

        self.assertTrue(self.handler.is_bucket_available(['testpackagefoo:foo', 'testpackage1']))

    def test_is_bucket_unavailable_with_foreign_archs(self):
        """After adding a foreign arch, test that the package is unavailable and report so"""
        subprocess.call([self.dpkg, "--add-architecture", "foo"])
        self.handler.cache.open()   # reopen the cache with the new added architecture

        self.assertFalse(self.handler.is_bucket_available(['testpackagebar:foo', 'testpackage1']))

    def test_bucket_unavailable_but_foreign_archs_no_added(self):
        """Bucket is set as available when foreign arch not added"""
        self.assertTrue(self.handler.is_bucket_available(['testpackagefoo:foo', 'testpackage1']))

    def test_bucket_unavailable_foreign_archs_no_added_another_package_not_available(self):
        """Bucket is set as unavailable when foreign arch not added, but another package on current arch is
         unavailable"""
        self.assertFalse(self.handler.is_bucket_available(['testpackagefoo:foo', 'testpackage123']))

    def test_apt_cache_not_ready(self):
        """When the first apt.Cache() access tells it's not ready, we wait and recover"""
        origin_open = self.handler.cache.open
        raise_returned = False

        def cache_call(*args, **kwargs):
            nonlocal raise_returned
            if raise_returned:
                return origin_open()
            else:
                raise_returned = True
                raise SystemError

        with patch.object(self.handler.cache, 'open', side_effect=cache_call) as openaptcache_mock:
            self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
            self.wait_for_callback(self.done_callback)
            self.assertEquals(openaptcache_mock.call_count, 2)

    def test_upgrade(self):
        """Upgrade one package already installed"""
        shutil.copy(os.path.join(self.apt_status_dir, "testpackage_installed_dpkg_status"),
                    os.path.join(self.dpkg_dir, "status"))
        self.handler.cache.open()
        self.assertTrue(self.handler.is_bucket_installed(["testpackage"]))
        self.assertEquals(self.handler.cache["testpackage"].installed.version, "0.0.0")
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0].bucket, ['testpackage'])
        self.assertIsNone(self.done_callback.call_args[0][0].error)
        self.assertTrue(self.handler.is_bucket_installed(["testpackage"]))
        self.assertEquals(self.handler.cache["testpackage"].installed.version, "0.0.1")

    def test_one_install_one_upgrade(self):
        """Install and Upgrade one package in the same bucket"""
        shutil.copy(os.path.join(self.apt_status_dir, "testpackage_installed_dpkg_status"),
                    os.path.join(self.dpkg_dir, "status"))
        self.handler.cache.open()
        self.assertTrue(self.handler.is_bucket_installed(["testpackage"]))
        self.assertEquals(self.handler.cache["testpackage"].installed.version, "0.0.0")
        self.assertFalse(self.handler.is_bucket_installed(["testpackage0"]))
        self.handler.install_bucket(["testpackage", "testpackage0"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0].bucket, ['testpackage', 'testpackage0'])
        self.assertIsNone(self.done_callback.call_args[0][0].error)
        self.assertTrue(self.handler.is_bucket_installed(["testpackage", "testpackage0"]))
        self.assertEquals(self.handler.cache["testpackage"].installed.version, "0.0.1")

    def test_install_with_foreign_foreign_arch_added(self):
        """Install packages with a foreign arch added"""
        subprocess.call([self.dpkg, "--add-architecture", "foo"])
        self.handler.cache.open()  # reopen the cache with the new added architecture

        bucket = ["testpackagefoo:foo", "testpackage1"]
        with patch("umake.network.requirements_handler.subprocess") as subprocess_mock:
            self.handler.install_bucket(bucket, lambda x: "", self.done_callback)
            self.wait_for_callback(self.done_callback)

            self.assertFalse(subprocess_mock.call.called)
            self.assertEqual(self.done_callback.call_args[0][0].bucket, bucket)
            self.assertIsNone(self.done_callback.call_args[0][0].error)
            self.assertTrue(self.handler.is_bucket_installed(bucket))

    def test_install_with_foreign_foreign_arch_not_added(self):
        """Install packages with a foreign arch, while the foreign arch wasn't added"""
        bucket = ["testpackagefoo:foo", "testpackage1"]
        self.handler.install_bucket(bucket, lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0].bucket, bucket)
        self.assertIsNone(self.done_callback.call_args[0][0].error)
        self.assertTrue(self.handler.is_bucket_installed(bucket))

    def test_install_with_foreign_foreign_arch_add_fails(self):
        """Install packages with a foreign arch, where adding a foreign arch fails"""
        bucket = ["testpackagefoo:foo", "testpackage1"]
        with patch("umake.network.requirements_handler.subprocess") as subprocess_mock:
            subprocess_mock.call.return_value = 1
            self.handler.install_bucket(bucket, lambda x: "", self.done_callback)
            self.wait_for_callback(self.done_callback)

            self.assertTrue(subprocess_mock.call.called)
            self.assertFalse(self.handler.is_bucket_installed(bucket))
            self.expect_warn_error = True

    def test_cant_change_seteuid(self):
        """Not being able to change the euid to root returns an error"""
        os.seteuid.side_effect = PermissionError()
        self.handler.install_bucket(["testpackage"], lambda x: "", self.done_callback)
        self.wait_for_callback(self.done_callback)

        self.assertEqual(self.done_callback.call_args[0][0].bucket, ['testpackage'])
        self.assertIsNotNone(self.done_callback.call_args[0][0].error)
        self.assertFalse(self.handler.is_bucket_installed(["testpackage"]))
        self.expect_warn_error = True
