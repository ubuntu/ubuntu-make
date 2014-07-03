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
import logging
import os
import shutil
import tarfile


logger = logging.getLogger(__name__)


class Decompressor:
    """Handle decompression of various file in separate threads"""

    DecompressOrder = namedtuple("DecompressOrder", ["dir", "dest"])
    DecompressResult = namedtuple("DecompressResult", ["error"])

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
        """decompress one entry"""
        logger.debug("Extracting to {}".format(dest))
        tfile = tarfile.open(fileobj=fd)
        tfile.extractall(dest)

        # we want the content of dir to be the root of dest, rename and move content
        if dir is not None:
            tempdir = os.path.join(dest, "footemp")
            os.rename(os.path.join(dest, dir), tempdir)
            for filename in os.listdir(tempdir):
                shutil.move(os.path.join(tempdir, filename), os.path.join(dest, filename))
            os.rmdir(tempdir)

    def _one_done(self, future):
        """Callback that will be called once one decompress finishes.

        (will be wired on the constructor)
        """

        result = self.DecompressResult(error=None)
        if future.exception():
            logger.debug("A decompression failed to {}: {}".format(future.tag_dest, future.exception()))
            result = result._replace(error=str(future.exception()))

        logger.info("Decompression to {} finished".format(future.tag_dest))
        self._decompressed[future.tag_fd] = result
        if len(self._orders) == len(self._decompressed):
            self._done()

    def _done(self):
        """Callback that will be called once all download finishes.

        uris of the temporary files will be passed on the wired callback
        """
        logger.info("All pending decompression done to {} done.".format(self._orders[fd].dest for fd in self._orders))
        self._done_callback(self._decompressed)
