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

import os
import urllib
from collections import OrderedDict
from urlparse import (urlparse, parse_qs)

from ..loading import LiteralLocation
from .. import install_aria_extensions
from .utils import (CommonArgumentParser,
                    create_context_from_namespace)
from ..consumption import (ConsumerChain, Read, Validate, Model, Inputs, Instance)
from ..utils import (RestServer, JsonAsRawEncoder, print_exception, start_daemon, stop_daemon,
                     status_daemon, puts, Colored)

VALIDATE_PATH = 'validate'
INDIRECT_VALIDATE_PATH = 'indirect/validate'
MODEL_PATH = 'model'
INDIRECT_MODEL_PATH = 'indirect/model'
INSTANCE_PATH = 'instance'
INDIRECT_INSTANCE_PATH = 'indirect/instance'

DEFAULT_PORT = 8080

#
# Utils
#

class Configuration(object):
    def __init__(self, arguments):
        self.arguments = arguments

    def create_context(self, uri):
        return create_context_from_namespace(self.arguments, uri=uri)

def parse_path(handler):
    parsed = urlparse(urllib.unquote(handler.path))
    uri = parsed.path[len(handler.matched_re):]
    query = parse_qs(parsed.query, keep_blank_values=True)
    return uri, query

def parse_indirect_payload(handler):
    try:
        payload = handler.json_payload
    except BaseException:
        handler.send_plain_text_response(400, 'Payload is not JSON\n')
        return None, None

    for key in payload.iterkeys():
        if key not in ('uri', 'inputs'):
            handler.send_plain_text_response(400, 'Payload has unsupported field: %s\n' % key)
            return None, None

    try:
        uri = payload['uri']
    except BaseException:
        handler.send_plain_text_response(400, 'Payload does not have required "uri" field\n')
        return None, None

    inputs = payload.get('inputs')

    return uri, inputs

def validate(handler, uri):
    context = handler.rest_server.configuration.create_context(uri)
    ConsumerChain(context, (Read, Validate)).consume()
    return context

def model(handler, uri):
    context = handler.rest_server.configuration.create_context(uri)
    ConsumerChain(context, (Read, Validate, Model)).consume()
    return context

def instance(handler, uri, inputs):
    context = handler.rest_server.configuration.create_context(uri)
    if inputs:
        if isinstance(inputs, dict):
            for name, value in inputs.iteritems():
                context.modeling.set_input(name, value)
        else:
            context.args.append('--inputs=%s' % inputs)
    ConsumerChain(context, (Read, Validate, Model, Inputs, Instance)).consume()
    return context

def issues(context):
    return {'issues': context.validation.issues_as_raw}

#
# Handlers
#

# Validate

def validate_get(handler):
    uri, _ = parse_path(handler)
    context = validate(handler, uri)
    return issues(context) if context.validation.has_issues else {}

def validate_post(handler):
    payload = handler.payload
    context = validate(handler, LiteralLocation(payload))
    return issues(context) if context.validation.has_issues else {}

def indirect_validate_post(handler):
    uri, _ = parse_indirect_payload(handler)
    if uri is None:
        return None
    context = validate(handler, uri)
    return issues(context) if context.validation.has_issues else {}

# Model

def model_get(handler):
    uri, _ = parse_path(handler)
    context = model(handler, uri)
    return issues(context) if context.validation.has_issues else {
        'types': context.modeling.types_as_raw,
        'model': context.modeling.model_as_raw
    }

def model_post(handler):
    payload = handler.payload
    context = model(handler, LiteralLocation(payload))
    return issues(context) if context.validation.has_issues else {
        'types': context.modeling.types_as_raw,
        'model': context.modeling.model_as_raw
    }

def indirect_model_post(handler):
    uri, _ = parse_indirect_payload(handler)
    if uri is None:
        return None
    context = model(handler, uri)
    return issues(context) if context.validation.has_issues else {
        'types': context.modeling.types_as_raw,
        'model': context.modeling.model_as_raw
    }

# Instance

def instance_get(handler):
    uri, query = parse_path(handler)
    inputs = query.get('inputs')
    if inputs:
        inputs = inputs[0]
    context = instance(handler, uri, inputs)
    return issues(context) if context.validation.has_issues else {
        'types': context.modeling.types_as_raw,
        'model': context.modeling.model_as_raw,
        'instance': context.modeling.instance_as_raw
    }

def instance_post(handler):
    _, query = parse_path(handler)
    inputs = query.get('inputs')
    if inputs:
        inputs = inputs[0]
    payload = handler.payload
    context = instance(handler, LiteralLocation(payload), inputs)
    return issues(context) if context.validation.has_issues else {
        'types': context.modeling.types_as_raw,
        'model': context.modeling.model_as_raw,
        'instance': context.modeling.instance_as_raw
    }

def indirect_instance_post(handler):
    uri, inputs = parse_indirect_payload(handler)
    if uri is None:
        return None
    context = instance(handler, uri, inputs)
    return issues(context) if context.validation.has_issues else {
        'types': context.modeling.types_as_raw,
        'model': context.modeling.model_as_raw,
        'instance': context.modeling.instance_as_raw
    }

#
# Server
#

ROUTES = OrderedDict((
    ('^/$', {'file': 'index.html', 'media_type': 'text/html'}),
    ('^/' + VALIDATE_PATH, {'GET': validate_get,
                            'POST': validate_post,
                            'media_type': 'application/json'}),
    ('^/' + MODEL_PATH, {'GET': model_get, 'POST': model_post, 'media_type': 'application/json'}),
    ('^/' + INSTANCE_PATH, {'GET': instance_get,
                            'POST': instance_post,
                            'media_type': 'application/json'}),
    ('^/' + INDIRECT_VALIDATE_PATH, {'POST': indirect_validate_post,
                                     'media_type': 'application/json'}),
    ('^/' + INDIRECT_MODEL_PATH, {'POST': indirect_model_post, 'media_type': 'application/json'}),
    ('^/' + INDIRECT_INSTANCE_PATH, {'POST': indirect_instance_post,
                                     'media_type': 'application/json'})))

class ArgumentParser(CommonArgumentParser):
    def __init__(self):
        super(ArgumentParser, self).__init__(description='REST Server', prog='aria-rest')
        self.add_argument('command',
                          nargs='?',
                          help='daemon command: start, stop, restart, or status')
        self.add_argument('--port', type=int, default=DEFAULT_PORT, help='HTTP port')
        self.add_argument('--root', help='web root directory')
        self.add_argument('--rundir',
                          help='pid and log files directory for daemons (defaults to user home)')

def main():
    try:
        install_aria_extensions()

        arguments, _ = ArgumentParser().parse_known_args()

        rest_server = RestServer()
        rest_server.configuration = Configuration(arguments)
        rest_server.port = arguments.port
        rest_server.routes = ROUTES
        rest_server.static_root = arguments.root or os.path.join(os.path.dirname(__file__), 'web')
        rest_server.json_encoder = JsonAsRawEncoder(ensure_ascii=False, separators=(',', ':'))

        if arguments.command:
            rundir = os.path.abspath(arguments.rundir or os.path.expanduser('~'))
            pidfile_path = os.path.join(rundir, 'aria-rest.pid')

            def start():
                log_path = os.path.join(rundir, 'aria-rest.log')
                context = start_daemon(pidfile_path, log_path)
                if context is not None:
                    with context:
                        rest_server.start(daemon=True)

            if arguments.command == 'start':
                start()
            elif arguments.command == 'stop':
                stop_daemon(pidfile_path)
            elif arguments.command == 'restart':
                stop_daemon(pidfile_path)
                start()
            elif arguments.command == 'status':
                status_daemon(pidfile_path)
            else:
                puts(Colored.red('Unknown command: %s' % arguments.command))
        else:
            rest_server.start()

    except Exception as e:
        print_exception(e)

if __name__ == '__main__':
    main()
