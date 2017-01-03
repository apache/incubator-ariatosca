#! /usr/bin/env python
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

import argparse
import json
import os
import sys
import urllib2


# Environment variable for the socket url (used by clients to locate the socket)
CTX_SOCKET_URL = 'CTX_SOCKET_URL'


class _RequestError(RuntimeError):

    def __init__(self, ex_message, ex_type, ex_traceback):
        super(_RequestError, self).__init__(self, '{0}: {1}'.format(ex_type, ex_message))
        self.ex_type = ex_type
        self.ex_message = ex_message
        self.ex_traceback = ex_traceback


def _http_request(socket_url, request, timeout):
    response = urllib2.urlopen(
        url=socket_url,
        data=json.dumps(request),
        timeout=timeout)
    if response.code != 200:
        raise RuntimeError('Request failed: {0}'.format(response))
    return json.loads(response.read())


def _client_request(socket_url, args, timeout):
    response = _http_request(
        socket_url=socket_url,
        request={'args': args},
        timeout=timeout)
    payload = response['payload']
    response_type = response.get('type')
    if response_type == 'error':
        ex_type = payload['type']
        ex_message = payload['message']
        ex_traceback = payload['traceback']
        raise _RequestError(ex_message, ex_type, ex_traceback)
    elif response_type == 'stop_operation':
        raise SystemExit(payload['message'])
    else:
        return payload


def _parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--timeout', type=int, default=30)
    parser.add_argument('--socket-url', default=os.environ.get(CTX_SOCKET_URL))
    parser.add_argument('--json-arg-prefix', default='@')
    parser.add_argument('-j', '--json-output', action='store_true')
    parser.add_argument('args', nargs='*')
    args = parser.parse_args(args=args)
    if not args.socket_url:
        raise RuntimeError('Missing CTX_SOCKET_URL environment variable '
                           'or socket_url command line argument. (ctx is supposed to be executed '
                           'within an operation context)')
    return args


def _process_args(json_prefix, args):
    processed_args = []
    for arg in args:
        if arg.startswith(json_prefix):
            arg = json.loads(arg[1:])
        processed_args.append(arg)
    return processed_args


def main(args=None):
    args = _parse_args(args)
    response = _client_request(
        socket_url=args.socket_url,
        args=_process_args(args.json_arg_prefix, args.args),
        timeout=args.timeout)
    if args.json_output:
        response = json.dumps(response)
    else:
        if not response:
            response = ''
        response = str(response)
    sys.stdout.write(response)


if __name__ == '__main__':
    main()
