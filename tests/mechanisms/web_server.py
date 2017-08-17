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

import logging
import threading

import tornado.web
import tornado.ioloop
import tornado.netutil
import tornado.httpserver


logging.getLogger('tornado.access').disabled = True


class WebServer(threading.Thread):
    def __init__(self):
        super(WebServer, self).__init__()
        self.daemon = True

        self.content = []

        # Arbitrary free socket
        self.sockets = tornado.netutil.bind_sockets(0, '')
        for s in self.sockets:
            name = s.getsockname()
            if name[0] == '0.0.0.0': # IPv4 (IPv6 would be '::')
                self.port = name[1]
                break

    @property
    def root(self):
        return 'http://localhost:{0}'.format(self.port)

    def add_text(self, url, content, content_type='text/plain'):
        self.content.append((url, TextHandler, dict(content=content, content_type=content_type)))

    def add_text_yaml(self, url, content):
        self.add_text(url, content, 'application/x-yaml')

    def stop(self):
        self.ioloop.add_callback(self.ioloop.stop)

    def run(self): # Thread override
        application = tornado.web.Application(self.content)
        server = tornado.httpserver.HTTPServer(application)
        server.add_sockets(self.sockets)
        self.ioloop = tornado.ioloop.IOLoop.current()
        print 'Tornado starting'
        self.ioloop.start()
        print 'Tornado stopped'

    @staticmethod
    def escape(segment):
        return tornado.escape.url_escape(segment)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class TextHandler(tornado.web.RequestHandler):
    def initialize(self, content, content_type):                                                    # pylint: disable=arguments-differ
        self.content = content
        self.content_type = content_type

    def get(self):
        self.write(self.content)
        self.set_header('Content-Type', self.content_type)
