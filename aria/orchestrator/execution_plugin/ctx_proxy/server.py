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

"""
``ctx`` proxy server implementation.
"""

import json
import socket
import Queue
import StringIO
import threading
import traceback
import wsgiref.simple_server

import bottle
from aria import modeling

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

        class BottleServerAdapter(bottle.ServerAdapter):
            proxy = self

            def close_session(self):
                self.proxy.ctx.model.log._session.remove()

            def run(self, app):

                class Server(wsgiref.simple_server.WSGIServer):
                    allow_reuse_address = True
                    bottle_server = self

                    def handle_error(self, request, client_address):
                        pass

                    def serve_forever(self, poll_interval=0.5):
                        try:
                            wsgiref.simple_server.WSGIServer.serve_forever(self, poll_interval)
                        finally:
                            # Once shutdown is called, we need to close the session.
                            # If the session is not closed properly, it might raise warnings,
                            # or even lock the database.
                            self.bottle_server.close_session()

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
                self.proxy.server = server
                self.proxy._started.put(True)
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
            body=json.dumps(response, cls=modeling.utils.ModelJSONEncoder),
            status=200,
            headers={'content-type': 'application/json'}
        )

    def _process(self, request):
        try:
            with self.ctx.model.instrument(*self.ctx.INSTRUMENTATION_FIELDS):
                payload = _process_request(self.ctx, request)
                result_type = 'result'
                if isinstance(payload, exceptions.ScriptException):
                    payload = dict(message=str(payload))
                    result_type = 'stop_operation'
                result = {'type': result_type, 'payload': payload}
        except Exception as e:
            traceback_out = StringIO.StringIO()
            traceback.print_exc(file=traceback_out)
            payload = {
                'type': type(e).__name__,
                'message': str(e),
                'traceback': traceback_out.getvalue()
            }
            result = {'type': 'error', 'payload': payload}

        return result

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()


class CtxError(RuntimeError):
    pass


class CtxParsingError(CtxError):
    pass


def _process_request(ctx, request):
    request = json.loads(request)
    args = request['args']
    return _process_arguments(ctx, args)


def _process_arguments(obj, args):
    # Modifying?
    try:
        # TODO: should there be a way to escape "=" in case it is needed as real argument?
        equals_index = args.index('=') # raises ValueError if not found
    except ValueError:
        equals_index = None
    if equals_index is not None:
        if equals_index == 0:
            raise CtxParsingError('The "=" argument cannot be first')
        elif equals_index != len(args) - 2:
            raise CtxParsingError('The "=" argument must be penultimate')
        modifying = True
        modifying_key = args[-3]
        modifying_value = args[-1]
        args = args[:-3]
    else:
        modifying = False
        modifying_key = None
        modifying_value = None

    # Parse all arguments
    while len(args) > 0:
        obj, args = _process_next_operation(obj, args, modifying)

    if modifying:
        if hasattr(obj, '__setitem__'):
            # Modify item value (dict, list, and similar)
            if isinstance(obj, (list, tuple)):
                modifying_key = int(modifying_key)
            obj[modifying_key] = modifying_value
        elif hasattr(obj, modifying_key):
            # Modify object attribute
            setattr(obj, modifying_key, modifying_value)
        else:
            raise CtxError('Cannot modify `{0}` of `{1!r}`'.format(modifying_key, obj))

    return obj


def _process_next_operation(obj, args, modifying):
    args = list(args)
    arg = args.pop(0)

    # Call?
    if arg == '[':
        # TODO: should there be a way to escape "[" and "]" in case they are needed as real
        # arguments?
        try:
            closing_index = args.index(']') # raises ValueError if not found
        except ValueError:
            raise CtxParsingError('Opening "[" without a closing "]')
        callable_args = args[:closing_index]
        args = args[closing_index + 1:]
        if not callable(obj):
            raise CtxError('Used "[" and "] on an object that is not callable')
        return obj(*callable_args), args

    # Attribute?
    if isinstance(arg, basestring):
        if hasattr(obj, arg):
            return getattr(obj, arg), args
        token_sugared = arg.replace('-', '_')
        if hasattr(obj, token_sugared):
            return getattr(obj, token_sugared), args

    # Item? (dict, lists, and similar)
    if hasattr(obj, '__getitem__'):
        if modifying and (arg not in obj) and hasattr(obj, '__setitem__'):
            # Create nested dict
            obj[arg] = {}
        return obj[arg], args

    raise CtxParsingError('Cannot parse argument: `{0!r}`'.format(arg))


def _get_unused_port():
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    _, port = sock.getsockname()
    sock.close()
    return port
