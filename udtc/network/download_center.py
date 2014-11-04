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

from collections import namedtuple
from concurrent import futures
from contextlib import suppress, closing
import hashlib
from io import BytesIO
import logging
import os
import tempfile

import requests
import requests.exceptions
from udtc.tools import ChecksumType

logger = logging.getLogger(__name__)


class DownloadItem(namedtuple('DownloadItem', ['url', 'checksum'])):
    """An individual item to be downloaded and checked.

    Checksum should be an instance of tools.Checksum, if provided."""
    pass


class DownloadCenter:
    """Read or download requested urls in separate threads."""

    BLOCK_SIZE = 1024*8  # from urlretrieve code
    DownloadResult = namedtuple("DownloadResult", ["buffer", "error", "fd"])

    def __init__(self, urls, on_done, download=True, report=lambda x: None):
        """Generate a threaded download machine.

        urls is a list of DownloadItems to download or read from.
        on_done is the callback that will be called once all those urls are downloaded.
        report, if not None, will be called once any download is in progress, reporting
        a dict of current download with current/size parameters

        The callback will get a dictionary parameter like:
        {
            "url":
                DownloadResult(buffer=page content as bytes if download is set to False. close() will clean it from
                                      memory,
                               error=string detailing the error which occurred (path and content would be empty),
                               fd=temporary file descriptor. close() will delete it from disk
                )
        }
        """

        self._done_callback = on_done
        self._wired_report = report
        self._download_to_file = download

        self._urls = list(set(urls))
        self._downloaded_content = {}

        self._download_progress = {}

        executor = futures.ThreadPoolExecutor(max_workers=3)
        for url_request in self._urls:
            url, checksum = (url_request, None)
            # grab the md5sum if any
            with suppress(ValueError):
                (url, checksum) = url_request
            # switch between inline memory and temp file
            if download:
                # Named because shutils and tarfile library needs a .name property
                # http://bugs.python.org/issue21044
                # also, ensure we keep the same suffix
                path, ext = os.path.splitext(url)
                dest = tempfile.NamedTemporaryFile(suffix=ext)
                logger.info("Start downloading {} to a temp file".format(url))
            else:
                dest = BytesIO()
                logger.info("Start downloading {} in memory".format(url))
            future = executor.submit(self._fetch, url, checksum, dest)
            future.tag_url = url
            future.tag_download = download
            future.tag_dest = dest
            future.add_done_callback(self._one_done)

    def _fetch(self, url, checksum, dest):
        """Get an url content and close the connexion.

        This write the content to dest return it, after seeking at start and check for md5sum
        """

        def _report(block_no, block_size, total_size):
            current_size = int(block_no * block_size)
            if total_size != -1:
                current_size = min(current_size, total_size)
            self._download_progress[url] = {"current": current_size, "size": total_size}
            logger.debug("Deliver download update: {} of {}".format(self._download_progress, total_size))
            self._wired_report(self._download_progress)

        # Requests support redirection out of the box.
        try:
            with closing(requests.get(url, stream=True)) as r:
                if r.status_code != 200:
                    raise(BaseException("Can't download ({}): {}".format(r.status_code, r.reason)))
                content_size = int(r.headers.get('content-length', -1))

                # read in chunk and send report updates
                block_num = 0
                _report(block_num, self.BLOCK_SIZE, content_size)
                for data in r.iter_content(chunk_size=self.BLOCK_SIZE):
                    dest.write(data)
                    block_num += 1
                    _report(block_num, self.BLOCK_SIZE, content_size)
        except requests.exceptions.InvalidSchema as exc:
            # Wrap this for a nicer error message.
            raise BaseException("Protocol not supported.") from exc

        if checksum:
            checksum_type = checksum.checksum_type
            checksum_value = checksum.checksum_value
            logger.debug("Checking checksum ({}).".format(checksum_type.name))
            dest.seek(0)

            if checksum_type is ChecksumType.sha1:
                actual_checksum = self.sha1_for_fd(dest)
            elif checksum_type is ChecksumType.md5:
                actual_checksum = self.md5_for_fd(dest)
            else:
                msg = "Unsupported checksum type: {}.".format(checksum_type)
                raise BaseException(msg)

            logger.debug("Expected: {}, actual: {}.".format(checksum_value,
                                                            actual_checksum))
            if checksum_value != actual_checksum:
                msg = ("The checksum of {} doesn't match. Corrupted download? "
                       "Aborting.").format(url)
                raise BaseException(msg)
        return dest

    def _one_done(self, future):
        """Callback that will be called once the download finishes.

        (will be wired on the constructor)
        """

        result = self.DownloadResult(buffer=None, error=None, fd=None)
        if future.exception():
            logger.error("{} couldn't finish download: {}".format(future.tag_url, future.exception()))
            result = result._replace(error=str(future.exception()))
            # cleaned unusable temp file as something bad happened
            future.tag_dest.close()
        else:
            logger.info("{} download finished".format(future.tag_url))
            fd = future.result()
            fd.seek(0)
            if future.tag_download:
                result = result._replace(fd=fd)
            else:
                result = result._replace(buffer=fd)
        self._downloaded_content[future.tag_url] = result
        if len(self._urls) == len(self._downloaded_content):
            self._done()

    def _done(self):
        """Callback that will be called once all download finishes.

        uris of the temporary files will be passed on the wired callback
        """
        logger.info("All pending downloads for {} done".format(self._urls))
        self._done_callback(self._downloaded_content)

    @classmethod
    def _checksum_for_fd(cls, algorithm, f, block_size=2**20):
        checksum = algorithm()
        while True:
            data = f.read(block_size)
            if not data:
                break
            checksum.update(data)
        return checksum.hexdigest()

    @classmethod
    def md5_for_fd(cls, f, block_size=2**20):
        return cls._checksum_for_fd(hashlib.md5, f, block_size)

    @classmethod
    def sha1_for_fd(cls, f, block_size=2**20):
        return cls._checksum_for_fd(hashlib.sha1, f, block_size)
