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
from concurrent import futures
import fcntl
import logging
import os
import time

logger = logging.getLogger(__name__)


class RequirementsHandler(object):
    """Handle platform requirements"""

    class _RequirementsHandlers:

        STATUS_DOWNLOADING, STATUS_INSTALLING = range(2)

        """Private implementation"""
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
            logger.info("Pend {} for installation".format(bucket))
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
            for pkg_name in current_bucket["bucket"]:
                try:
                    pkg = self.cache[pkg_name]
                    if pkg.is_installed and pkg.is_upgradable:
                        pkg.mark_upgrade()
                    else:
                        pkg.mark_install()
                except Exception as msg:
                    logger.error("Can't install {}: {}".format(pkg_name, msg))
                    raise
                    # TODO: the root check should be here:
                    # apt.cache.LockFailedException: Failed to lock /var/cache/apt/archives/lock

            self.cache.commit(fetch_progress=self._FetchProgress(current_bucket,
                                                                 self.STATUS_DOWNLOADING,
                                                                 current_bucket["progress_callback"]),
                              install_progress=self._InstallProgress(current_bucket,
                                                                     self.STATUS_INSTALLING,
                                                                     current_bucket["progress_callback"],
                                                                     self._force_load_apt_cache))
            return True

        @staticmethod
        def _on_done(future):
            """Call future associated bucket done callback"""
            result = {"bucket": future.tag_bucket["bucket"],
                      "error": None}
            if future.exception():
                result["error"] = str(future.exception())
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
                progress = self.fetched_bytes / self.total_bytes * 100
                logger.debug("{} download update: {}%".format(self._bucket['bucket'], progress))
                self._progress_callback(self._status, progress)

        class _InstallProgress(apt.progress.base.InstallProgress):
            """Progress handler for installing a bucket"""
            def __init__(self, bucket, status, progress_callback, force_load_apt_cache):
                apt.progress.base.InstallProgress.__init__(self)
                self._bucket = bucket
                self._status = status
                self._progress_callback = progress_callback
                self._force_load_apt_cache = force_load_apt_cache

            def error(self, pkg, msg):
                logger.error("{} installation finished with an error: {}".format(self._bucket['bucket'], msg))
                self._force_load_apt_cache()  # reload apt cache
                raise BaseException(msg)

            def finish_update(self):
                logger.debug("Install for {} done with success.".format(self._bucket['bucket']))
                self._force_load_apt_cache()  # reload apt cache

            def status_change(self, pkg, percent, status):
                logger.debug("{} install update: {}".format(self._bucket['bucket'], percent))
                self._progress_callback(self._status, percent)

            @staticmethod
            def _redirect_stdin():
                os.dup2(os.open(os.devnull, os.O_RDWR), 0)

            @staticmethod
            def _redirect_output():
                fd = os.open(os.devnull, os.O_RDWR)
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
                            #print("closed: ", fd)
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

    # singleton
    _instance = None

    def __new__(cls):
        if not RequirementsHandler._instance:
            RequirementsHandler._instance = RequirementsHandler._RequirementsHandlers()
        else:
            logger.debug("Reusing existing apt instance")
        return RequirementsHandler._instance

    def __getattr__(self, name):
        return getattr(self._instance, name)

    def __setattr__(self, name, value):
        return setattr(self._instance, name, value)


# import udtc.network.requirements_handler
# p = udtc.network.requirements_handler.RequirementsHandler()
# p.install_bucket(["oneconf", "ubuntu-desktop"], lambda step,
# progress: print("Progress in step ({}): {}".format(step, progress)),
# lambda result: print("DONE with result: {}".format(result)))
