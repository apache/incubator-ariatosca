# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import  # so we can import standard 'collections'

import os
import re
import shutil
import json
import sys
import BaseHTTPServer
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from ..utils import (puts, Colored)

class RestServer(object):
    """
    Straightforward REST server.

    Supports custom handling of all HTTP verbs, with special (optional) support for JSON, as well
    as serving straightforward static files via GET.

    Properties:

    * :code:`configuration`: An optional configuration object
    * :code:`port`: HTTP server port
    * :code:`routes`: :class:`OrderedDict` of routes (see below)
    * :code:`static_root`: Root directory for static files
    * :code:`json_encoder`: :class:`JSONEncoder` for responses
    * :code:`json_decoder`: :class:`JSONDecoder` for requests
    * :code:`unicode`: True to support Unicode

    The route keys are regular expressions for matching the path. They are checked in order, which
    is why it's important to use :class:`OrderedDict`.

    The route values are dicts with the following optional fields:

    * :code:`GET`: Function to handle GET for this route
    * :code:`PUT`: Function to handle PUT for this route
    * :code:`POST`: Function to handle POST for this route
    * :code:`DELETE`: Function to handle DELETE for this route
    * :code:`file`: Attach a static file to this route; it is the path to
            the file to return relative to :code:`static_root` (if :code:`file` is
            set then :code:`GET`/:code:`PUT`/:code:`POST`/:code:`DELETE` are ignored)
    * :code:`media_type`: Media type to set for responses to this
            route (except error message, which will be in "text/plan")

    The :code:`GET`/:code:`PUT`/:code:`POST`/:code:`DELETE` handler functions all receive a single
    argument: an instance of :class:`RestRequestHandler`.

    If you return None, then a 404 error will be generated. Otherwise, it will be a 200 response
    with the return value will be written to it. If the :code:`media_type` for the route was set to
    "application/json", then the return value will first be encoded into JSON using the configured
    :code:`json_encoder`.

    If you want to write the response yourself, set :code:`handled=True` on the
    :class:`RestRequestHandler`, which will cause the return value to be ignored (you won't have to
    return anything). If all you want to do is send an error message, then use
    :code:`send_plain_text_response`.

    If you raise an (uncaught) exception, then a 500 error will be generated with the exception
    message.

    To get the payload (for :code:`PUT`/:code:`POST`) use :code:`payload` on the
    :class:`RestRequestHandler` for plain text, or :code:`json_payload` to use the configured
    :code:`json_decoder`. Note that it's up to you to check for JSON decoding exceptions and return
    an appropriate 400 error message.
    """

    def __init__(self):
        self.configuration = None
        self.port = 8080
        self.routes = OrderedDict()
        self.static_root = '.'
        self.json_encoder = json.JSONEncoder(ensure_ascii=False, separators=(',', ':'))
        self.json_decoder = json.JSONDecoder(object_pairs_hook=OrderedDict)
        self.unicode = True

    def start(self, daemon=False):
        """
        Starts the REST server.
        """

        if self.unicode:
            # Fixes issues with decoding HTTP responses
            # (Not such a great solution! But there doesn't seem to be a better way)
            reload(sys)
            sys.setdefaultencoding('utf8')  # @UndefinedVariable

        http_server = BaseHTTPServer.HTTPServer(('', self.port), rest_request_handler(self))
        if daemon:
            print 'Running HTTP server daemon at port %d' % self.port
        else:
            puts(Colored.red('Running HTTP server at port %d, use CTRL-C to exit' % self.port))
        try:
            http_server.serve_forever()
        except KeyboardInterrupt:
            pass
        puts(Colored.red('Stopping HTTP server'))
        http_server.server_close()

class RestRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    Handler for :class:`RestServer`.
    """

    def __init__(self, rest_server, *args, **kwargs):
        self.rest_server = rest_server
        self.handled = False
        self.matched_re = None
        self.matched_route = None
        # Old-style Python classes don't support super
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    @property
    def content_length(self):
        return int(self.headers.getheader('content-length', 0))

    @property
    def payload(self):
        return self.rfile.read(self.content_length)

    @property
    def json_payload(self):
        return self.rest_server.json_decoder.decode(self.payload)

    def match_route(self):
        for path_re, route in self.rest_server.routes.iteritems():
            if re.match(path_re, self.path):
                return path_re, route
        return None, None

    def send_plain_text_response(self, status, content):
        self.send_response(status)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(content)
        self.handled = True

    def send_content_type(self, route=None):
        if route is None:
            _, route = self.match_route()
        media_type = route.get('media_type')
        if media_type is not None:
            self.send_header('Content-type', media_type)
        return media_type

    def _handle_file(self, method):
        if method != 'GET':
            self.send_plain_text_response(405, '%s is not supported\n' % method)
            return

        try:
            matched_route_file = open(os.path.join(
                self.rest_server.static_root,
                self.matched_route['file']))
            try:
                self.send_response(200)
                self.send_content_type(self.matched_route)
                self.end_headers()
                shutil.copyfileobj(matched_route_file, self.wfile)
            finally:
                matched_route_file.close()
        except IOError:
            self.send_plain_text_response(404, 'Not found\n')
        return

    def handle_method(self, method):
        # pylint: disable=too-many-return-statements
        self.matched_re, self.matched_route = self.match_route()

        if self.matched_route is None:
            self.send_plain_text_response(404, 'Not found\n')
            return

        if method == 'HEAD':
            self.send_response(200)
            self.send_content_type(self.matched_route)
            self.end_headers()
            return

        if 'file' in self.matched_route:
            self._handle_file(method)
            return

        if method not in self.matched_route:
            self.send_plain_text_response(405, '%s is not supported\n' % method)
            return

        try:
            content = self.matched_route[method](self)
        except Exception as e:
            self.send_plain_text_response(500, 'Internal error: %s\n' % e)
            return

        if self.handled:
            return

        if content is None:
            self.send_plain_text_response(404, 'Not found\n')
            return

        self.send_response(200)
        media_type = self.send_content_type(self.matched_route)
        self.end_headers()

        if method == 'DELETE':
            # No content for DELETE
            return

        if media_type == 'application/json':
            self.wfile.write(self.rest_server.json_encoder.encode(content))
        else:
            self.wfile.write(content)

    # BaseHTTPRequestHandler
    # pylint: disable=invalid-name
    def do_HEAD(self):
        self.handle_method('HEAD')

    def do_GET(self):
        self.handle_method('GET')

    def do_POST(self):
        self.handle_method('POST')

    def do_PUT(self):
        self.handle_method('PUT')

    def do_DELETE(self):
        self.handle_method('DELETE')

#
# Utils
#

def rest_request_handler(rest_server):
    return lambda *args, **kwargs: RestRequestHandler(rest_server, *args, **kwargs)
