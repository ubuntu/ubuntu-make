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

from collections import namedtuple
from concurrent import futures
from glob import glob
import logging
import os
import shutil
import stat
import subprocess
import tarfile
import zipfile


logger = logging.getLogger(__name__)


class Decompressor:
    """Handle decompression of various file in separate threads"""

    DecompressOrder = namedtuple("DecompressOrder", ["dir", "dest"])
    DecompressResult = namedtuple("DecompressResult", ["error"])

    # override _extract_member to preserve file permissions:
    # http://bugs.python.org/issue15795
    class ZipFileWithPerm(zipfile.ZipFile):
        def _extract_member(self, member, targetpath, pwd):
            targetpath = super()._extract_member(member, targetpath, pwd)
            mode = member.external_attr >> 16 & 0x1FF
            os.chmod(targetpath, mode)
            return targetpath

    def __init__(self, orders, on_done):
        """Decompress all fds in threads and send on_done callback once finished


        order is:
        {
            "fd":
                DecompressOrder(dir=directory to decompress (this will become the new root)
                                dest=destination directory to use for decompressing)
                                )
        }

        Return a dict of DecompressResult on the on_done callback:
        {
            "fd":
                DecompressResult(error=optional error if anything went wrong"
        }
        """
        self._orders = orders
        self._decompressed = {}
        self._done_callback = on_done

        executor = futures.ThreadPoolExecutor(max_workers=3)
        for fd in orders:
            logger.info("Requesting decompression to {}".format(orders[fd].dest))
            future = executor.submit(self._decompress, fd, orders[fd].dir, orders[fd].dest)
            future.tag_fd = fd
            future.tag_dest = orders[fd].dest
            future.add_done_callback(self._one_done)

    def _decompress(self, fd, dir, dest):
        """decompress one entry

        dir can be a regexp"""
        logger.debug("Extracting to {}".format(dest))
        # We don't use shutil to automatically select the right codec as we need to ensure that zipfile
        # will keep the original perms.
        archive = None
        try:
            try:
                archive = tarfile.open(fileobj=fd)
                logger.debug("tar file")
            except tarfile.ReadError:
                archive = self.ZipFileWithPerm(fd.name)
                logger.debug("zip file")
            archive.extractall(dest)
        except:
            # try to treat it as self-extractable, some format don't like being opened at the same time though, so link
            # it.
            name = "{}.safe".format(fd.name)
            os.link(fd.name, name)
            fd.close()
            st = os.stat(name)
            os.chmod(name, st.st_mode | stat.S_IEXEC)
            archive = subprocess.Popen([name, "-o{}".format(dest)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            archive.communicate()
            logger.debug("executable file")
            os.remove(name)

        # we want the content of dir to be the root of dest, rename and move content
        if dir is not None:
            dir_path = glob(os.path.join(dest, dir))[0]
            if not dir_path:
                raise BaseException("Couldn't find {} in tarball".format(dir_path))
            tempdir = os.path.join(dest, "footemp")
            os.rename(dir_path, tempdir)
            for filename in os.listdir(tempdir):
                shutil.move(os.path.join(tempdir, filename), os.path.join(dest, filename))
            os.rmdir(tempdir)

    def _one_done(self, future):
        """Callback that will be called once one decompress finishes.

        (will be wired on the constructor)
        """

        result = self.DecompressResult(error=None)
        if future.exception():
            logger.error("A decompression to {} failed: {}".format(future.tag_dest, future.exception()),
                         exc_info=future.exception())
            result = result._replace(error=str(future.exception()))

        logger.info("Decompression to {} finished".format(future.tag_dest))
        self._decompressed[future.tag_fd] = result
        if len(self._orders) == len(self._decompressed):
            self._done()

    def _done(self):
        """Callback that will be called once all download finishes.

        uris of the temporary files will be passed on the wired callback
        """
        logger.info("All pending decompression done to {} done.".format([self._orders[fd].dest for fd in self._orders]))
        self._done_callback(self._decompressed)
