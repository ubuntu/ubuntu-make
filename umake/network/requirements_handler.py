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

"""Module delivering a DownloadCenter to download in parallel multiple requests"""

import apt
import apt.progress
import apt.progress.base
from collections import namedtuple
from concurrent import futures
from contextlib import suppress
import fcntl
import logging
import os
import subprocess
import tempfile
import time
from umake.tools import Singleton, get_foreign_archs, get_current_arch, switch_to_current_user

logger = logging.getLogger(__name__)


class RequirementsHandler(object, metaclass=Singleton):
    """Handle platform requirements"""

    STATUS_DOWNLOADING, STATUS_INSTALLING = range(2)

    RequirementsResult = namedtuple("RequirementsResult", ["bucket", "error"])

    def __init__(self):
        logger.info("Create a new apt cache")
        self.cache = apt.Cache()
        self.executor = futures.ThreadPoolExecutor(max_workers=1)

    def is_bucket_installed(self, bucket):
        """Check if the bucket is installed

        The bucket is a list of packages to check if installed."""
        logger.debug("Check if {} is installed".format(bucket))
        is_installed = True
        for pkg_name in bucket:
            # /!\ danger: if current arch == ':appended_arch', on a non multiarch system, dpkg doesn't
            # understand that. strip :arch then
            if ":" in pkg_name:
                (pkg_without_arch_name, arch) = pkg_name.split(":", -1)
                if arch == get_current_arch():
                    pkg_name = pkg_without_arch_name
            if pkg_name not in self.cache or not self.cache[pkg_name].is_installed:
                logger.info("{} isn't installed".format(pkg_name))
                is_installed = False
        return is_installed

    def is_bucket_available(self, bucket):
        """Check if bucket available on the platform"""
        all_in_cache = True
        for pkg_name in bucket:
            if pkg_name not in self.cache:
                # this can be also a foo:arch and we don't have <arch> added. Tell is may be available
                if ":" in pkg_name:
                    # /!\ danger: if current arch == ':appended_arch', on a non multiarch system, dpkg doesn't
                    # understand that. strip :arch then
                    (pkg_without_arch_name, arch) = pkg_name.split(":", -1)
                    if arch == get_current_arch() and pkg_without_arch_name in self.cache:  # false positive, available
                        continue
                    elif arch not in get_foreign_archs():  # relax the constraint
                        logger.info("{} isn't available on this platform, but {} isn't enabled. So it may be available "
                                    "later on".format(pkg_name, arch))
                        continue
                logger.info("{} isn't available on this platform".format(pkg_name))
                all_in_cache = False
        return all_in_cache

    def is_bucket_uptodate(self, bucket):
        """Check if the bucket is installed and up to date

        The bucket is a list of packages to check if installed."""
        logger.debug("Check if {} is uptodate".format(bucket))
        is_installed_and_uptodate = True
        for pkg_name in bucket:
            # /!\ danger: if current arch == ':appended_arch', on a non multiarch system, dpkg doesn't
            # understand that. strip :arch then
            if ":" in pkg_name:
                (pkg_without_arch_name, arch) = pkg_name.split(":", -1)
                if arch == get_current_arch():
                    pkg_name = pkg_without_arch_name
            if pkg_name not in self.cache or not self.cache[pkg_name].is_installed:
                logger.info("{} isn't installed".format(pkg_name))
                is_installed_and_uptodate = False
            elif self.cache[pkg_name].is_upgradable:
                logger.info("We can update {}".format(pkg_name))
                is_installed_and_uptodate = False
        return is_installed_and_uptodate

    def install_bucket(self, bucket, progress_callback, installed_callback):
        """Install a specific bucket. If any other bucket is in progress, queue the request

        bucket is a list of packages to install.

        Return a tuple (num packages to install, size packages to download)"""
        logger.info("Installation {} pending".format(bucket))
        bucket_pack = {
            "bucket": bucket,
            "progress_callback": progress_callback,
            "installed_callback": installed_callback
        }

        pkg_to_install = not self.is_bucket_uptodate(bucket)

        future = self.executor.submit(self._really_install_bucket, bucket_pack)
        future.tag_bucket = bucket_pack
        future.add_done_callback(self._on_done)
        return pkg_to_install

    def _really_install_bucket(self, current_bucket):
        """Really install current bucket and bind signals"""
        bucket = current_bucket["bucket"]
        logger.debug("Starting {} installation".format(bucket))

        # exchange file output for apt and dpkg after the fork() call (open it empty)
        self.apt_fd = tempfile.NamedTemporaryFile(delete=False)
        self.apt_fd.close()

        if self.is_bucket_uptodate(bucket):
            return True

        for pkg_name in bucket:
            if ":" in pkg_name:
                arch = pkg_name.split(":", -1)[-1]
                # try to add the arch
                if arch not in get_foreign_archs() and arch != get_current_arch():
                    logger.info("Adding foreign arch: {}".format(arch))
                    with open(os.devnull, "w") as f:
                        try:
                            os.seteuid(0)
                            os.setegid(0)
                            if subprocess.call(["dpkg", "--add-architecture", arch], stdout=f) != 0:
                                msg = "Can't add foreign foreign architecture {}".format(arch)
                                raise BaseException(msg)
                            self.cache.update()
                        finally:
                            switch_to_current_user()
                        self._force_reload_apt_cache()

        # mark for install and so on
        for pkg_name in bucket:
            # /!\ danger: if current arch == ':appended_arch', on a non multiarch system, dpkg doesn't understand that
            # strip :arch then
            if ":" in pkg_name:
                (pkg_without_arch_name, arch) = pkg_name.split(":", -1)
                if arch == get_current_arch():
                    pkg_name = pkg_without_arch_name
            try:
                pkg = self.cache[pkg_name]
                if pkg.is_installed and pkg.is_upgradable:
                    logger.debug("Marking {} for upgrade".format(pkg_name))
                    pkg.mark_upgrade()
                else:
                    logger.debug("Marking {} for install".format(pkg_name))
                    pkg.mark_install(auto_fix=False)
            except Exception as msg:
                message = "Can't mark for install {}: {}".format(pkg_name, msg)
                raise BaseException(message)

        # this can raise on installedArchives() exception if the commit() fails
        try:
            os.seteuid(0)
            os.setegid(0)
            self.cache.commit(fetch_progress=self._FetchProgress(current_bucket,
                                                                 self.STATUS_DOWNLOADING,
                                                                 current_bucket["progress_callback"]),
                              install_progress=self._InstallProgress(current_bucket,
                                                                     self.STATUS_INSTALLING,
                                                                     current_bucket["progress_callback"],
                                                                     self._force_reload_apt_cache,
                                                                     self.apt_fd.name))
        finally:
            switch_to_current_user()

        return True

    def _on_done(self, future):
        """Call future associated bucket done callback"""
        result = self.RequirementsResult(bucket=future.tag_bucket["bucket"], error=None)
        if future.exception():
            error_message = str(future.exception())
            with suppress(FileNotFoundError):
                with open(self.apt_fd.name) as f:
                    subprocess_content = f.read()
                    if subprocess_content:
                        error_message = "{}\nSubprocess output: {}".format(error_message, subprocess_content)
            logger.error(error_message)
            result = result._replace(error=error_message)
        else:
            logger.debug("{} installed".format(future.tag_bucket["bucket"]))
        os.remove(self.apt_fd.name)
        future.tag_bucket["installed_callback"](result)

    def _force_reload_apt_cache(self):
        """Loop on loading apt cache in case something else is updating"""
        try:
            self.cache.open()
        except SystemError:
            time.sleep(1)
            self._force_reload_apt_cache()

    class _FetchProgress(apt.progress.base.AcquireProgress):
        """Progress handler for downloading a bucket"""
        def __init__(self, bucket, status, progress_callback,):
            apt.progress.base.AcquireProgress.__init__(self)
            self._bucket = bucket
            self._status = status
            self._progress_callback = progress_callback

        def pulse(self, owner):
            percent = (((self.current_bytes + self.current_items) * 100.0) /
                       float(self.total_bytes + self.total_items))
            logger.debug("{} download update: {}% of {}".format(self._bucket['bucket'], percent, self.total_bytes))
            report = {"step": self._status, "percentage": percent, "pkg_size_download": self.total_bytes}
            self._progress_callback(report)

    class _InstallProgress(apt.progress.base.InstallProgress):
        """Progress handler for installing a bucket"""
        def __init__(self, bucket, status, progress_callback, force_load_apt_cache, exchange_filename):
            apt.progress.base.InstallProgress.__init__(self)
            self._bucket = bucket
            self._status = status
            self._progress_callback = progress_callback
            self._force_reload_apt_cache = force_load_apt_cache
            self._exchange_filename = exchange_filename

        def error(self, pkg, msg):
            logger.error("{} installation finished with an error: {}".format(self._bucket['bucket'], msg))
            self._force_reload_apt_cache()  # reload apt cache
            raise BaseException(msg)

        def finish_update(self):
            # warning: this function can be called even if dpkg failed (it raised an exception around commit()
            # DO NOT CALL directly the callbacks from there.
            logger.debug("Install for {} ended.".format(self._bucket['bucket']))
            self._force_reload_apt_cache()  # reload apt cache

        def status_change(self, pkg, percent, status):
            logger.debug("{} install update: {}".format(self._bucket['bucket'], percent))
            self._progress_callback({"step": self._status, "percentage": percent})

        @staticmethod
        def _redirect_stdin():  # pragma: no cover (in a fork)
            os.dup2(os.open(os.devnull, os.O_RDWR), 0)

        def _redirect_output(self):  # pragma: no cover (in a fork)
            fd = os.open(self._exchange_filename, os.O_RDWR)
            os.dup2(fd, 1)
            os.dup2(fd, 2)

        def _fixup_fds(self):  # pragma: no cover (in a fork)
            required_fds = [0, 1, 2,  # stdin, stdout, stderr
                            self.writefd,
                            self.write_stream.fileno(),
                            self.statusfd,
                            self.status_stream.fileno()
                            ]
            # ensure that our required fds close on exec
            for fd in required_fds[3:]:
                old_flags = fcntl.fcntl(fd, fcntl.F_GETFD)
                fcntl.fcntl(fd, fcntl.F_SETFD, old_flags | fcntl.FD_CLOEXEC)
            # close all fds
            proc_fd = "/proc/self/fd"
            if os.path.exists(proc_fd):
                error_count = 0
                for fdname in os.listdir(proc_fd):
                    try:
                        fd = int(fdname)
                    except ValueError:
                        print("ERROR: can not get fd for '%s'" % fdname)
                    if fd in required_fds:
                        continue
                    try:
                        os.close(fd)
                    except OSError as e:
                        # there will be one fd that can not be closed
                        # as its the fd from pythons internal diropen()
                        # so its ok to ignore one close error
                        error_count += 1
                        if error_count > 1:
                            print("ERROR: os.close(%s): %s" % (fd, e))

        def fork(self):
            pid = os.fork()
            if pid == 0:  # pragma: no cover
                # be root
                os.seteuid(0)
                os.setegid(0)
                self._fixup_fds()
                self._redirect_stdin()
                self._redirect_output()
            return pid
