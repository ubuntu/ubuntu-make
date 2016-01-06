# -*- coding: utf-8 -*-
# Copyright (C) 2016 Canonical
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

"""Some common tools between small tests"""

import apt
import os
import shutil
import stat
import tempfile
from ..tools import get_data_dir, LoggedTestCase, manipulate_path_env
from unittest.mock import Mock
from umake import tools


class DpkgAptSetup(LoggedTestCase):
    """This parent class is there to setup and teardown a dpkg chroot test environment"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
            # Don't nest fakeroot calls when having some dpkg hook scripts
            f.write("#!/bin/sh\nprependfakeroot=''\nif [ -z \"$FAKEROOTKEY\" ]; then\nprependfakeroot=fakeroot\nfi\n "
                    "$prependfakeroot /usr/bin/dpkg --root={root} --force-not-root --force-bad-path "
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
        if hasattr(self, "handler"):
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
