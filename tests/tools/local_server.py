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

"""Class enabling having a local http(s) server"""

from concurrent import futures
from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging
import os
import posixpath
import urllib
import socketserver

logger = logging.getLogger(__name__)


class LocalHttp:
    """Local threaded http server. will be serving path content"""

    def __init__(self, path):
        self.port = 9876
        self.path = path
        handler = RequestHandler
        handler.root_path = path
        # can be TCPServer, but we don't have a self.httpd.server_name then
        self.httpd = HTTPServer(("", self.port), RequestHandler)
        executor = futures.ThreadPoolExecutor(max_workers=1)
        self.future = executor.submit(self._serve)

    def _serve(self):
        logger.warning("Serving locally from {} on {}".format(self.path, self.get_address()))
        self.httpd.serve_forever()

    def get_address(self):
        """Get public address"""
        return "http://{}:{}".format(self.httpd.server_name, self.port)

    def stop(self):
        """Stop local server"""
        logger.debug("Stopping serving on {}".format(self.port))
        self.httpd.shutdown()
        self.httpd.socket.close()


class RequestHandler(SimpleHTTPRequestHandler):

    root_path = os.getcwd()

    def translate_path(self, path):
        """translate path given routes

    Most of it is a copy of the parent function which can't be override and
    uses cwd
    """
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = filter(None, words)

        # root path isn't cwd but the one we specified
        path = RequestHandler.root_path

        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path

    def log_message(self, format, *args):
        """Log an arbitrary message.

        override from SimpleHTTPRequestHandler to not output to stderr but log in the logging system
        """

        logger.debug("%s - - [%s] %s\n" %
                     (self.address_string(),
                      self.log_date_time_string(),
                      format%args))
