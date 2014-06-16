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
import fcntl
import logging
import os
import tempfile
import time
from udtc.tools import Singleton

logger = logging.getLogger(__name__)


class RequirementsHandler(object, metaclass=Singleton):
    """Handle platform requirements"""

    STATUS_DOWNLOADING, STATUS_INSTALLING = range(2)

    RequirementsResult = namedtuple("RequirementsResult", ["bucket", "error"])

    def __init__(self):
        logger.info("Create a new apt cache")
        self._force_load_apt_cache()
        self.executor = futures.ThreadPoolExecutor(max_workers=1)

    def is_bucket_installed(self, bucket):
        """Check if the bucket is installed

        The bucket is a list of packages to check if installed."""
        logger.debug("Check if {} is installed".format(bucket))
        is_installed = True
        for pkg_name in bucket:
            if not self.cache[pkg_name].is_installed:
                logger.info("{} isn't installed".format(pkg_name))
                is_installed = False
        return is_installed

    def install_bucket(self, bucket, progress_callback, installed_callback):
        """Install a specific bucket. If any other bucket is in progress, queue the request

        bucket is a list of packages to install"""
        # TODO: check/move to root
        logger.info("Installation {} pending".format(bucket))
        bucket_pack = {
            "bucket": bucket,
            "progress_callback": progress_callback,
            "installed_callback": installed_callback
        }

        future = self.executor.submit(self._really_install_bucket, bucket_pack)
        future.tag_bucket = bucket_pack
        future.add_done_callback(self._on_done)

    def _really_install_bucket(self, current_bucket):
        """Really install current bucket and bind signals"""
        logger.debug("Starting {} installation".format(current_bucket["bucket"]))
        # exchange file output for apt and dpkg after the fork() call (open it empty)
        self.apt_fd = tempfile.NamedTemporaryFile(delete=False)
        self.apt_fd.close()

        for pkg_name in current_bucket["bucket"]:
            try:
                pkg = self.cache[pkg_name]
                if pkg.is_installed and pkg.is_upgradable:
                    pkg.mark_upgrade()
                else:
                    pkg.mark_install(auto_fix=False)
            except Exception as msg:
                logger.error("Can't mark for install {}: {}".format(pkg_name, msg))
                raise
                # TODO: the root check should be here:
                # apt.cache.LockFailedException: Failed to lock /var/cache/apt/archives/lock

        # this can raise on installedArchives() exception if the commit() fails
        self.cache.commit(fetch_progress=self._FetchProgress(current_bucket,
                                                             self.STATUS_DOWNLOADING,
                                                             current_bucket["progress_callback"]),
                          install_progress=self._InstallProgress(current_bucket,
                                                                 self.STATUS_INSTALLING,
                                                                 current_bucket["progress_callback"],
                                                                 self._force_load_apt_cache,
                                                                 self.apt_fd.name))
        return True

    def _on_done(self, future):
        """Call future associated bucket done callback"""
        result = self.RequirementsResult(bucket=future.tag_bucket["bucket"], error=None)
        if future.exception():
            error_message = str(future.exception())
            try:
                with open(self.apt_fd.name) as f:
                    subprocess_content = f.read()
                    if subprocess_content:
                        error_message = "{}\nSubprocess output: {}".format(error_message, subprocess_content)
            except FileNotFoundError:
                pass
            logger.error(error_message)
            result = result._replace(error=error_message)
        os.remove(self.apt_fd.name)
        future.tag_bucket["installed_callback"](result)

    def _force_load_apt_cache(self):
        """Loop on loading apt cache in case something else is updating"""
        try:
            self.cache = apt.Cache()
        except SystemError:
            time.sleep(1)
            self._force_load_apt_cache()

    class _FetchProgress(apt.progress.base.AcquireProgress):
        """Progress handler for downloading a bucket"""
        def __init__(self, bucket, status, progress_callback):
            apt.progress.base.AcquireProgress.__init__(self)
            self._bucket = bucket
            self._status = status
            self._progress_callback = progress_callback

        def pulse(self, owner):
            percent = (((self.current_bytes + self.current_items) * 100.0) /
                       float(self.total_bytes + self.total_items))
            logger.debug("{} download update: {}%".format(self._bucket['bucket'], percent))
            self._progress_callback(self._status, percent)

    class _InstallProgress(apt.progress.base.InstallProgress):
        """Progress handler for installing a bucket"""
        def __init__(self, bucket, status, progress_callback, force_load_apt_cache, exchange_filename):
            apt.progress.base.InstallProgress.__init__(self)
            self._bucket = bucket
            self._status = status
            self._progress_callback = progress_callback
            self._force_load_apt_cache = force_load_apt_cache
            self._exchange_filename = exchange_filename

        def error(self, pkg, msg):
            logger.error("{} installation finished with an error: {}".format(self._bucket['bucket'], msg))
            self._force_load_apt_cache()  # reload apt cache
            raise BaseException(msg)

        def finish_update(self):
            # warning: this function can be called even if dpkg failed (it raised an exception around commit()
            # DO NOT CALL directly the callbacks from there.
            logger.debug("Install for {} ended.".format(self._bucket['bucket']))
            self._force_load_apt_cache()  # reload apt cache

        def status_change(self, pkg, percent, status):
            logger.debug("{} install update: {}".format(self._bucket['bucket'], percent))
            self._progress_callback(self._status, percent)

        @staticmethod
        def _redirect_stdin():
            os.dup2(os.open(os.devnull, os.O_RDWR), 0)

        def _redirect_output(self):
            fd = os.open(self._exchange_filename, os.O_RDWR)
            os.dup2(fd, 1)
            os.dup2(fd, 2)

        def _fixup_fds(self):
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
            if pid == 0:
                self._fixup_fds()
                self._redirect_stdin()
                self._redirect_output()
            return pid
