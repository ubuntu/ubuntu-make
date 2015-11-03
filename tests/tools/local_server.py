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
import http.cookies
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

    def __init__(self, path, multi_hosts=False, use_ssl=[], port=9876, ftp_redir=False):
        """path is the local path to server
        multi_hosts will transfer http://hostname/foo to path/hostname/foo. This is used when we potentially serve
        multiple paths.
        set use_ssl to a specific array of hostnames. We'll use the corresponding certificates.
        """
        self.port = port
        self.path = path
        self.use_ssl = use_ssl
        handler = RequestHandler
        handler.root_path = path
        handler.multi_hosts = multi_hosts
        handler.ftp_redir = ftp_redir
        # can be TCPServer, but we don't have a self.httpd.server_name then
        self.httpd = HTTPServer(("", self.port), RequestHandler)
        handler.hostname = self.httpd.server_name

        # create ssl certificate handling for SNI case (switching between different host name)
        self.ssl_contexts = {}
        context_associated = False
        for hostname in self.use_ssl:
            pem_file = os.path.join(get_data_dir(), "{}.pem".format(hostname))
            if os.path.isfile(pem_file):
                context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
                context.load_cert_chain(pem_file)
                self.ssl_contexts[hostname] = context
                if not context_associated:
                    context_associated = True
                    self.httpd.socket = context.wrap_socket(self.httpd.socket, server_side=True)
                    context.set_servername_callback(self._match_sni_context)

        executor = futures.ThreadPoolExecutor(max_workers=1)
        self.future = executor.submit(self._serve)

    def _match_sni_context(self, ssl_sock, server_name, initial_context):
        """return matching certificates to the current request"""
        logger.info("Request on {}".format(server_name))
        try:
            ssl_sock.context = self.ssl_contexts[server_name]
        except KeyError:
            logger.warning("Didn't find corresponding context on this server for {}, keeping default"
                           .format(server_name))

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

    def __init__(self, request, client_address, server):
        self.headers_to_send = []
        super().__init__(request, client_address, server)

    def end_headers(self):
        """don't send Content-Length header for a particular file"""
        if self.path.endswith("-with-no-content-length"):
            for current_header in self._headers_buffer:
                if current_header.decode("UTF-8").startswith("Content-Length"):
                    self._headers_buffer.remove(current_header)
        for key, value in self.headers_to_send:
            self.send_header(key, value)
        super().end_headers()

    def translate_path(self, path):
        """translate path given routes

        Most of it is a copy of the parent function which can't be override and
        uses cwd
        """
        # Before we actually abandon the query params, see if they match an
        # actual file.
        # Need to strip the leading '/' so the join will actually work.
        current_root_path = RequestHandler.root_path
        if RequestHandler.multi_hosts:
            current_root_path = os.path.join(RequestHandler.root_path, self.headers["Host"].split(":")[0])

        file_path = posixpath.normpath(urllib.parse.unquote(path))[1:]
        file_path = os.path.join(current_root_path, file_path)
        if os.path.exists(file_path):
            return file_path

        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = path.split('&', 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split('/')
        words = filter(None, words)

        # root path isn't cwd but the one we specified and translated
        path = current_root_path

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
        cookies = http.cookies.SimpleCookie(self.headers['Cookie'])
        if 'int' in cookies:
            cookies['int'] = int(cookies['int'].value) + 1
        for cookie in cookies.values():
            self.headers_to_send.append(('Set-Cookie', cookie.OutputString(None)))

        if self.path.endswith('-redirect'):
            self.send_response(302)
            self.send_header('Location', self.path[:-len('-redirect')])
            self.end_headers()
        elif 'setheaders' in self.path:
            # For paths that end with '-setheaders', we fish out the headers from the query
            # params and set them.
            url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(url.query)
            for key, values in params.items():
                for value in values:
                    self.headers_to_send.append((key, value))
            # Now we need to chop off the '-setheaders' part.
            self.path = url.path[:-len('-setheaders')]
            super().do_GET()
        elif 'headers' in self.path:
            # For paths that end with '-headers', we check if the request actually
            # contains the header with the specified value. The expected header key
            # and value are in the query params.
            url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(url.query)
            for key in params:
                if self.headers[key] != params[key][0]:
                    self.send_error(404)
            # Now we need to chop off the '-headers' part.
            self.path = url.path[:-len('-headers')]
            super().do_GET()
        else:
            # keep special ?file= to redirect the query
            if '?file=' in self.path:
                self.path = self.path.split('?file=', 1)[1]
                self.path = self.path.replace('&', '?', 1)  # Replace the first & with ? to make it valid.
            if RequestHandler.ftp_redir:
                self.send_response(302)
                # We need to remove the query parameters, so we actually parse the URL.
                parsed_url = urllib.parse.urlparse(self.path)
                new_loc = 'ftp://' + RequestHandler.hostname + parsed_url.path
                self.send_header('Location', new_loc)
                self.end_headers()
                return
            super().do_GET()

    def log_message(self, fmt, *args):
        """Log an arbitrary message.

        override from SimpleHTTPRequestHandler to not output to stderr but log in the logging system
        """

        logger.debug("%s - - [%s] %s\n" %
                     (self.address_string(),
                      self.log_date_time_string(),
                      fmt % args))
