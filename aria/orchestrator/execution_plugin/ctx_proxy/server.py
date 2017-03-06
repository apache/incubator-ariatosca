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

import collections
import json
import re
import socket
import threading
import traceback
import Queue
import StringIO
import wsgiref.simple_server

import bottle

from .. import exceptions


class CtxProxy(object):

    def __init__(self, ctx, ctx_patcher=(lambda *args, **kwargs: None)):
        self.ctx = ctx
        self._ctx_patcher = ctx_patcher
        self.port = _get_unused_port()
        self.socket_url = 'http://localhost:{0}'.format(self.port)
        self.server = None
        self._started = Queue.Queue(1)
        self.thread = self._start_server()
        self._started.get(timeout=5)

    def _start_server(self):
        proxy = self

        class BottleServerAdapter(bottle.ServerAdapter):
            def run(self, app):
                class Server(wsgiref.simple_server.WSGIServer):
                    allow_reuse_address = True

                    def handle_error(self, request, client_address):
                        pass

                class Handler(wsgiref.simple_server.WSGIRequestHandler):
                    def address_string(self):
                        return self.client_address[0]

                    def log_request(*args, **kwargs):  # pylint: disable=no-method-argument
                        if not self.quiet:
                            return wsgiref.simple_server.WSGIRequestHandler.log_request(*args,
                                                                                        **kwargs)
                server = wsgiref.simple_server.make_server(
                    host=self.host,
                    port=self.port,
                    app=app,
                    server_class=Server,
                    handler_class=Handler)
                proxy.server = server
                proxy._started.put(True)
                server.serve_forever(poll_interval=0.1)

        def serve():
            # Since task is a thread_local object, we need to patch it inside the server thread.
            self._ctx_patcher(self.ctx)

            bottle_app = bottle.Bottle()
            bottle_app.post('/', callback=self._request_handler)
            bottle.run(
                app=bottle_app,
                host='localhost',
                port=self.port,
                quiet=True,
                server=BottleServerAdapter)
        thread = threading.Thread(target=serve)
        thread.daemon = True
        thread.start()
        return thread

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

    def _request_handler(self):
        request = bottle.request.body.read()  # pylint: disable=no-member
        response = self._process(request)
        return bottle.LocalResponse(
            body=response,
            status=200,
            headers={'content-type': 'application/json'})

    def _process(self, request):
        try:
            typed_request = json.loads(request)
            args = typed_request['args']
            payload = _process_ctx_request(self.ctx, args)
            result_type = 'result'
            if isinstance(payload, exceptions.ScriptException):
                payload = dict(message=str(payload))
                result_type = 'stop_operation'
            result = json.dumps({
                'type': result_type,
                'payload': payload
            })
        except Exception as e:
            traceback_out = StringIO.StringIO()
            traceback.print_exc(file=traceback_out)
            payload = {
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback_out.getvalue()
            }
            result = json.dumps({
                'type': 'error',
                'payload': payload
            })
        return result

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()


def _process_ctx_request(ctx, args):
    current = ctx
    num_args = len(args)
    index = 0
    while index < num_args:
        arg = args[index]
        attr = _desugar_attr(current, arg)
        if attr:
            current = getattr(current, attr)
        elif isinstance(current, collections.MutableMapping):
            key = arg
            path_dict = _PathDictAccess(current)
            if index + 1 == num_args:
                # read dict prop by path
                value = path_dict.get(key)
                current = value
            elif index + 2 == num_args:
                # set dict prop by path
                value = args[index + 1]
                path_dict.set(key, value)
                current = None
            else:
                raise RuntimeError('Illegal argument while accessing dict')
            break
        elif callable(current):
            kwargs = {}
            remaining_args = args[index:]
            if isinstance(remaining_args[-1], collections.MutableMapping):
                kwargs = remaining_args[-1]
                remaining_args = remaining_args[:-1]
            current = current(*remaining_args, **kwargs)
            break
        else:
            raise RuntimeError('{0} cannot be processed in {1}'.format(arg, args))
        index += 1
    if callable(current):
        current = current()
    return current


def _desugar_attr(obj, attr):
    if not isinstance(attr, basestring):
        return None
    if hasattr(obj, attr):
        return attr
    attr = attr.replace('-', '_')
    if hasattr(obj, attr):
        return attr
    return None


class _PathDictAccess(object):
    pattern = re.compile(r"(.+)\[(\d+)\]")

    def __init__(self, obj):
        self.obj = obj

    def set(self, prop_path, value):
        obj, prop_name = self._get_parent_obj_prop_name_by_path(prop_path)
        obj[prop_name] = value

    def get(self, prop_path):
        value = self._get_object_by_path(prop_path)
        return value

    def _get_object_by_path(self, prop_path, fail_on_missing=True):
        # when setting a nested object, make sure to also set all the
        # intermediate path objects
        current = self.obj
        for prop_segment in prop_path.split('.'):
            match = self.pattern.match(prop_segment)
            if match:
                index = int(match.group(2))
                property_name = match.group(1)
                if property_name not in current:
                    self._raise_illegal(prop_path)
                if not isinstance(current[property_name], list):
                    self._raise_illegal(prop_path)
                current = current[property_name][index]
            else:
                if prop_segment not in current:
                    if fail_on_missing:
                        self._raise_illegal(prop_path)
                    else:
                        current[prop_segment] = {}
                current = current[prop_segment]
        return current

    def _get_parent_obj_prop_name_by_path(self, prop_path):
        split = prop_path.split('.')
        if len(split) == 1:
            return self.obj, prop_path
        parent_path = '.'.join(split[:-1])
        parent_obj = self._get_object_by_path(parent_path, fail_on_missing=False)
        prop_name = split[-1]
        return parent_obj, prop_name

    @staticmethod
    def _raise_illegal(prop_path):
        raise RuntimeError('illegal path: {0}'.format(prop_path))


def _get_unused_port():
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    _, port = sock.getsockname()
    sock.close()
    return port
