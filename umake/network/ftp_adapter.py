# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Tin Tvrtković
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
from ftplib import FTP, error_perm
from queue import Queue
from threading import Thread
import urllib.parse
from requests import Response
from requests.adapters import BaseAdapter
import requests.exceptions


class FTPAdapter(BaseAdapter):
    """An FTP adapter for requests. Supports streaming GETs and not much else."""

    @staticmethod
    def get_connection(hostname, timeout=None):
        return FTP(host=hostname, timeout=timeout, user='anonymous')

    def send(self, request, stream=False, timeout=None, **kwargs):

        parsed_url = urllib.parse.urlparse(request.url)
        file_path = parsed_url.path

        # Strip the leading slash, if present.
        if file_path.startswith('/'):
            file_path = file_path[1:]

        try:
            self.conn = self.get_connection(parsed_url.netloc, timeout)
        except ConnectionRefusedError as exc:
            # Wrap this in a requests exception.
            # in requests 2.2.1, ConnectionError does not take keyword args
            raise requests.exceptions.ConnectionError() from exc

        resp = Response()
        resp.url = request.url

        try:
            size = self.conn.size(file_path)
        except error_perm:
            resp.status_code = 404
            return resp

        if stream:
            # We have to do this in a background thread, since ftplib's and requests' approaches are the opposite:
            # ftplib is callback based, and requests needs to expose an iterable. (Push vs pull)

            # When the queue size is reached, puts will block. This provides some backpressure.
            queue = Queue(maxsize=100)
            done_sentinel = object()

            def handle_transfer():
                # Download all the chunks into a queue, then place a sentinel object into it to signal completion.
                self.conn.retrbinary('RETR ' + file_path, queue.put)
                queue.put(done_sentinel)

            Thread(target=handle_transfer).start()

            def stream(amt=8192, decode_content=False):
                """A generator, yielding chunks from the queue."""
                # We maintain a buffer so the consumer gets exactly the number of bytes requested.
                buffer = bytearray()
                while True:
                    data = queue.get()

                    if data is not done_sentinel:
                        buffer.extend(data)
                        if len(buffer) >= amt:
                            result = buffer[:amt]
                            buffer = buffer[amt:]

                            yield result
                    else:
                        if buffer:
                            yield buffer
                        return

            Raw = namedtuple('raw', 'stream')

            raw = Raw(stream)

            resp.status_code = 200
            resp.raw = raw
            resp.headers['content-length'] = size
            resp.close = lambda: self.conn.close()
            return resp

        else:
            # Not relevant for Ubuntu Make.
            raise NotImplementedError
