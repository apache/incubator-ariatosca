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

# TODO: this module will eventually be moved to a new "aria.instantiation" package

from ...utils.type import full_type_name
from ...utils.collections import OrderedDict
from ...parser import validation
from ...parser.consumption import ConsumptionContext


def configure_operation(operation):
    configuration = OrderedDict(operation.configuration) if operation.configuration else {}

    arguments = OrderedDict()
    arguments['script_path'] = operation.implementation
    arguments['process'] = _get_process(configuration.pop('process')) \
        if 'process' in configuration else dict()

    host = None
    interface = operation.interface
    if interface.node is not None:
        host = interface.node.host
    elif interface.relationship is not None:
        if operation.relationship_edge is True:
            host = interface.relationship.target_node.host
        else: # either False or None
            host = interface.relationship.source_node.host

    if host is None:
        _configure_local(operation)
    else:
        _configure_remote(operation, configuration, arguments)

    # Any remaining unhandled configuration values will become extra arguments, available as kwargs
    # in either "run_script_locally" or "run_script_with_ssh"
    arguments.update(configuration)

    return arguments

def _configure_local(operation):
    """
    Local operation.
    """
    from . import operations
    operation.implementation = '{0}.{1}'.format(operations.__name__,
                                                operations.run_script_locally.__name__)


def _configure_remote(operation, configuration, arguments):
    """
    Remote SSH operation via Fabric.
    """
    # TODO: find a way to configure these generally in the service template
    default_user = ''
    default_password = ''

    ssh = _get_ssh(configuration.pop('ssh')) if 'ssh' in configuration else {}
    if 'user' not in ssh:
        ssh['user'] = default_user
    if ('password' not in ssh) and ('key' not in ssh) and ('key_filename' not in ssh):
        ssh['password'] = default_password

    arguments['use_sudo'] = ssh.get('use_sudo', False)
    arguments['hide_output'] = ssh.get('hide_output', [])
    arguments['fabric_env'] = {}
    if 'warn_only' in ssh:
        arguments['fabric_env']['warn_only'] = ssh['warn_only']
    arguments['fabric_env']['user'] = ssh.get('user')
    arguments['fabric_env']['password'] = ssh.get('password')
    arguments['fabric_env']['key'] = ssh.get('key')
    arguments['fabric_env']['key_filename'] = ssh.get('key_filename')
    if 'address' in ssh:
        arguments['fabric_env']['host_string'] = ssh['address']

    if arguments['fabric_env'].get('user') is None:
        context = ConsumptionContext.get_thread_local()
        context.validation.report('must configure "ssh.user" for "{0}"'
                                  .format(operation.implementation),
                                  level=validation.Issue.BETWEEN_TYPES)
    if (arguments['fabric_env'].get('password') is None) and \
        (arguments['fabric_env'].get('key') is None) and \
        (arguments['fabric_env'].get('key_filename') is None):
        context = ConsumptionContext.get_thread_local()
        context.validation.report('must configure "ssh.password", "ssh.key", or "ssh.key_filename" '
                                  'for "{0}"'
                                  .format(operation.implementation),
                                  level=validation.Issue.BETWEEN_TYPES)

    from . import operations
    operation.implementation = '{0}.{1}'.format(operations.__name__,
                                                operations.run_script_with_ssh.__name__)


def _get_process(value):
    if value is None:
        return None
    _validate_type(value, dict, 'process')
    for k, v in value.iteritems():
        if k == 'eval_python':
            value[k] = _str_to_bool(v, 'process.eval_python')
        elif k == 'cwd':
            _validate_type(v, basestring, 'process.cwd')
        elif k == 'command_prefix':
            _validate_type(v, basestring, 'process.command_prefix')
        elif k == 'args':
            value[k] = _dict_to_list(v, 'process.args')
        elif k == 'env':
            _validate_type(v, dict, 'process.env')
        else:
            context = ConsumptionContext.get_thread_local()
            context.validation.report('unsupported configuration: "process.{0}"'.format(k),
                                      level=validation.Issue.BETWEEN_TYPES)
    return value


def _get_ssh(value):
    if value is None:
        return {}
    _validate_type(value, dict, 'ssh')
    for k, v in value.iteritems():
        if k == 'use_sudo':
            value[k] = _str_to_bool(v, 'ssh.use_sudo')
        elif k == 'hide_output':
            value[k] = _dict_to_list(v, 'ssh.hide_output')
        elif k == 'warn_only':
            value[k] = _str_to_bool(v, 'ssh.warn_only')
        elif k == 'user':
            _validate_type(v, basestring, 'ssh.user')
        elif k == 'password':
            _validate_type(v, basestring, 'ssh.password')
        elif k == 'key':
            _validate_type(v, basestring, 'ssh.key')
        elif k == 'key_filename':
            _validate_type(v, basestring, 'ssh.key_filename')
        elif k == 'address':
            _validate_type(v, basestring, 'ssh.address')
        else:
            context = ConsumptionContext.get_thread_local()
            context.validation.report('unsupported configuration: "ssh.{0}"'.format(k),
                                      level=validation.Issue.BETWEEN_TYPES)
    return value


def _validate_type(value, the_type, name):
    if not isinstance(value, the_type):
        context = ConsumptionContext.get_thread_local()
        context.validation.report('"{0}" configuration is not a {1}'
                                  .format(name, full_type_name(the_type)),
                                  level=validation.Issue.BETWEEN_TYPES)


def _str_to_bool(value, name):
    if value is None:
        return None
    _validate_type(value, basestring, name)
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        context = ConsumptionContext.get_thread_local()
        context.validation.report('"{0}" configuration is not "true" or "false": {1}'
                                  .format(name, repr(value)),
                                  level=validation.Issue.BETWEEN_TYPES)


def _dict_to_list(the_dict, name):
    _validate_type(the_dict, dict, name)
    value = []
    for k in sorted(the_dict):
        v = the_dict[k]
        if not isinstance(v, basestring):
            context = ConsumptionContext.get_thread_local()
            context.validation.report('"{0}.{1}" configuration is not a string: {2}'
                                      .format(name, k, repr(v)),
                                      level=validation.Issue.BETWEEN_TYPES)
        value.append(v)
    return value
