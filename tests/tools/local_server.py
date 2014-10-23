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
import ssl
from . import get_data_dir
import urllib
import urllib.parse

logger = logging.getLogger(__name__)


# TO CREATE THE CERTIFICATES:
# openssl req -new -x509 -nodes -days 3600 -out server.crt -keyout server.key (file the fqdn name)
# cat server.key server.crt > server.pem
# server loads the server.pem
# put the .crt file in /usr/local/share/ca-certificates and run sudo update-ca-certificates

class LocalHttp:
    """Local threaded http server. will be serving path content"""

    def __init__(self, path, use_ssl=False, port=9876):
        """path is the local path to server
        set use_ssl to a specific filename turn on the use of the local certificate
        """
        self.port = port
        self.path = path
        self.use_ssl = use_ssl
        handler = RequestHandler
        handler.root_path = path
        # can be TCPServer, but we don't have a self.httpd.server_name then
        self.httpd = HTTPServer(("", self.port), RequestHandler)
        if self.use_ssl:
            self.httpd.socket = ssl.wrap_socket(self.httpd.socket,
                                                certfile=os.path.join(get_data_dir(), self.use_ssl),
                                                server_side=True)
        executor = futures.ThreadPoolExecutor(max_workers=1)
        self.future = executor.submit(self._serve)

    def _serve(self):
        logger.info("Serving locally from {} on {}".format(self.path, self.get_address()))
        self.httpd.serve_forever()

    def get_address(self, localhost=False):
        """Get public address"""
        server_name = 'localhost' if localhost else self.httpd.server_name
        return "http{}://{}:{}".format("s" if self.use_ssl else "",
                                       server_name, self.port)

    def stop(self):
        """Stop local server"""
        logger.info("Stopping serving on {}".format(self.port))
        self.httpd.shutdown()
        self.httpd.socket.close()


class RequestHandler(SimpleHTTPRequestHandler):

    root_path = os.getcwd()

    def end_headers(self):
        """don't send Content-Length header for a particular file"""
        if self.path.endswith("-with-no-content-length"):
            for current_header in self._headers_buffer:
                if current_header.decode("UTF-8").startswith("Content-Length"):
                    self._headers_buffer.remove(current_header)
        super().end_headers()

    def translate_path(self, path):
        """translate path given routes

        Most of it is a copy of the parent function which can't be override and
        uses cwd
        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = path.split('&', 1)[0]
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
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path

    def do_GET(self):
        """Override this to enable redirecting paths that end in -redirect or rewrite in presence of ?file="""
        if self.path.endswith('-redirect'):
            self.send_response(302)
            self.send_header('Location', self.path[:-len('-redirect')])
            self.end_headers()
        else:
            # keep special ?file= to redirect the query
            if '?file=' in self.path:
                self.path = self.path.split('?file=', 1)[1]
            super().do_GET()

    def log_message(self, fmt, *args):
        """Log an arbitrary message.

        override from SimpleHTTPRequestHandler to not output to stderr but log in the logging system
        """

        logger.debug("%s - - [%s] %s\n" %
                     (self.address_string(),
                      self.log_date_time_string(),
                      fmt % args))
