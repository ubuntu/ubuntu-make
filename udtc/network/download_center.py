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
import logging
import tempfile
from urllib.request import urlretrieve

logger = logging.getLogger(__name__)


class DownloadCenter:
    """A DownloadCenter enables to download requested urls in separate threads."""

    def __init__(self, urls, callback, report=lambda x: None):
        """Generate a threaded download machine.
        urls is a list of urls to download
        callback is the callback that will be called once all those urls are downloaded.
        report, if not None, will be called once any download is in progress, reporting
        a dict of current download with current/size parameters

        The callback will get a dictionary of path of source files and value is the corresponding tmp files.
        """

        self._wired_callback = callback
        self._wired_report = report

        self._urls = urls
        self._downloaded_files = {}

        self._download_progress = {}

        executor = futures.ThreadPoolExecutor(max_workers=3)
        for url in urls:
            future = executor.submit(self._download, url)
            future.tag_url = url
            future.add_done_callback(self._one_callback)

    def _download(self, url):
        """Download an url and save it into a tmp file.

        Return this tmp file path"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            logger.info("Start downloading {} as {}".format(url, tmp_file.name))

            def _report(block_no, block_size, file_size):
                logger.debug("Current download update: {}*{}".format(block_no, block_size))
                self._download_progress[url] = {"current": min(int(block_no * block_size), file_size), "size": file_size}
                logger.debug("Deliver download update: {}".format(self._download_progress))
                self._wired_report(self._download_progress)

            urlretrieve(url=url,
                        filename=tmp_file.name,
                        reporthook=_report)
        return tmp_file.name

    def _one_callback(self, future):
        """Callback that will be called once the download finishes.

        (will be wired on the constructor)
        """
        logger.info("{} download finished".format(future.result()))
        self._downloaded_files[future.tag_url] = future.result()
        if len(self._urls) == len(self._downloaded_files):
            self._callback()

    def _callback(self):
        """Callback that will be called once all download finishes.

        uris of the temporary files will be passed on the wired callback
        """
        logger.info("All pending downloads for {} done".format(self._urls))
        self._wired_callback(self._downloaded_files)
