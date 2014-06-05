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

from concurrent import futures
from http.client import HTTPSConnection, HTTPConnection
from io import BytesIO
import logging
import os
import ssl
import tempfile
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DownloadCenter:
    """A DownloadCenter enables to read or download requested urls in separate threads."""

    BLOCK_SIZE = 1024*8 # from urlretrieve code

    def __init__(self, urls, callback, download=True, report=lambda x: None):
        """Generate a threaded download machine.
        urls is a list of urls to download or read from
        callback is the callback that will be called once all those urls are downloaded.
        report, if not None, will be called once any download is in progress, reporting
        a dict of current download with current/size parameters

        The callback will get a dictionary parameter like:
        {
            "url": {
                "content": page content as bytes if download is set to False. close() will clean it from memory
                "error": string detailing the error which occurred (path and content would be empty).
                "fd": temporary file descriptor. close() will delete it from disk.
            }
        }
        """

        self._wired_callback = callback
        self._wired_report = report
        self._download_to_file = download

        self._urls = list(set(urls))
        self._downloaded_content = {}

        self._download_progress = {}

        executor = futures.ThreadPoolExecutor(max_workers=3)
        for url in self._urls:
            # switch between inline memory and temp file
            if download:
                dest = tempfile.TemporaryFile()
                logger.info("Start downloading {} as a temporary file".format(url))
            else:
                dest = BytesIO()
                logger.info("Start downloading {} in memory".format(url))
            future = executor.submit(self._fetch, url, dest)
            future.tag_url = url
            future.tag_download = download
            future.tag_dest = dest
            future.add_done_callback(self._one_callback)

    def _fetch(self, url, dest):
        """Get an url.content and close the connexion.

        This write the content to dest return it, after seeking at start
        """

        def _report(block_no, block_size, total_size):
            self._download_progress[url] = {"current": min(int(block_no * block_size), total_size), "size": total_size}
            logger.debug("Deliver download update: {}".format(self._download_progress))
            self._wired_report(self._download_progress)

        # choose protocol
        url_details = urlparse(url)
        if url_details.scheme == 'http':
            conn = HTTPConnection(url_details.hostname, url_details.port)
        elif url_details.scheme == 'https':
            context = ssl.create_default_context()
            conn = HTTPSConnection(url_details.hostname, url_details.port, context=context)
        else:
            raise(BaseException("Protocol not supported: {}".format(url_details.scheme)))

        conn.request("GET", url_details.path)
        resp = conn.getresponse()

        # TODO: support redirection: 301 and 302
        if resp.status != 200:
            conn.close()
            raise(BaseException("Error {}: {}".format(resp.status, resp.reason)))

        total_size = int(resp.headers["Content-Length"])
        # read in chunk and send report updates
        block_num = 0
        _report(block_num, self.BLOCK_SIZE, total_size)
        while True:
            data = resp.read(self.BLOCK_SIZE)
            if not data:
                break
            dest.write(data)
            block_num += 1
            _report(block_num, self.BLOCK_SIZE, total_size)

        dest.seek(0)
        conn.close()
        return dest

    def _one_callback(self, future):
        """Callback that will be called once the download finishes.

        (will be wired on the constructor)
        """

        result = { "buffer": None, "error": None, "fd": None }
        if future.exception():
            logger.warn("{} couldn't finish download: {}".format(future.tag_url, future.exception()))
            result["error"] = str(future.exception())
            # cleaned unusable temp file as something bad happened
            future.tag_dest.close()
        else:
            logger.info("{} download finished".format(future.tag_url))
            if future.tag_download:
                result["fd"] = future.result()
            else:
                result["buffer"] = future.result()
        self._downloaded_content[future.tag_url] = result
        if len(self._urls) == len(self._downloaded_content):
            self._callback()

    def _callback(self):
        """Callback that will be called once all download finishes.

        uris of the temporary files will be passed on the wired callback
        """
        logger.info("All pending downloads for {} done".format(self._urls))
        self._wired_callback(self._downloaded_content)
