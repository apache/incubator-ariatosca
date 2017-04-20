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
from ...utils.formatting import safe_repr
from ...utils.collections import OrderedDict
from ...parser import validation
from ...parser.consumption import ConsumptionContext
from ...modeling.functions import Function


def configure_operation(operation):
    host = None
    interface = operation.interface
    if interface.node is not None:
        host = interface.node.host
    elif interface.relationship is not None:
        if operation.relationship_edge is True:
            host = interface.relationship.target_node.host
        else: # either False or None (None meaning that edge was not specified)
            host = interface.relationship.source_node.host

    _configure_common(operation)
    if host is None:
        _configure_local(operation)
    else:
        _configure_remote(operation)

    # Any remaining un-handled configuration parameters will become extra arguments, available as
    # kwargs in either "run_script_locally" or "run_script_with_ssh"
    for key, value in operation.configuration.iteritems():
        if key not in ('process', 'ssh'):
            operation.arguments[key] = value.instantiate(None)


def _configure_common(operation):
    """
    Local and remote operations.
    """

    from ...modeling.models import Parameter
    operation.arguments['script_path'] = Parameter.wrap('script_path', operation.implementation,
                                                        'Relative path to the executable file.')
    operation.arguments['process'] = Parameter.wrap('process', _get_process(operation),
                                                    'Sub-process configuration.')


def _configure_local(operation):
    """
    Local operation.
    """

    from . import operations
    operation.function = '{0}.{1}'.format(operations.__name__,
                                          operations.run_script_locally.__name__)


def _configure_remote(operation):
    """
    Remote SSH operation via Fabric.
    """

    from ...modeling.models import Parameter
    from . import operations

    ssh = _get_ssh(operation)

    # Defaults
    # TODO: find a way to configure these generally in the service template
    default_user = ''
    default_password = ''
    if 'user' not in ssh:
        ssh['user'] = default_user
    if ('password' not in ssh) and ('key' not in ssh) and ('key_filename' not in ssh):
        ssh['password'] = default_password

    operation.arguments['use_sudo'] = Parameter.wrap('use_sudo', ssh.get('use_sudo', False),
                                                     'Whether to execute with sudo.')

    operation.arguments['hide_output'] = Parameter.wrap('hide_output', ssh.get('hide_output', []),
                                                        'Hide output of these Fabric groups.')

    fabric_env = {}
    if 'warn_only' in ssh:
        fabric_env['warn_only'] = ssh['warn_only']
    fabric_env['user'] = ssh.get('user')
    fabric_env['password'] = ssh.get('password')
    fabric_env['key'] = ssh.get('key')
    fabric_env['key_filename'] = ssh.get('key_filename')
    if 'address' in ssh:
        fabric_env['host_string'] = ssh['address']

    # Make sure we have a user
    if fabric_env.get('user') is None:
        context = ConsumptionContext.get_thread_local()
        context.validation.report('must configure "ssh.user" for "{0}"'
                                  .format(operation.implementation),
                                  level=validation.Issue.BETWEEN_TYPES)

    # Make sure we have an authentication value
    if (fabric_env.get('password') is None) and \
        (fabric_env.get('key') is None) and \
        (fabric_env.get('key_filename') is None):
        context = ConsumptionContext.get_thread_local()
        context.validation.report('must configure "ssh.password", "ssh.key", or "ssh.key_filename" '
                                  'for "{0}"'
                                  .format(operation.implementation),
                                  level=validation.Issue.BETWEEN_TYPES)

    operation.arguments['fabric_env'] = Parameter.wrap('fabric_env', fabric_env,
                                                       'Fabric configuration.')

    operation.function = '{0}.{1}'.format(operations.__name__,
                                          operations.run_script_with_ssh.__name__)


def _get_process(operation):
    value = operation.configuration.get('process')._value \
        if 'process' in operation.configuration else None
    if value is None:
        return {}
    _validate_type(value, dict, 'process')
    value = OrderedDict(value)
    for k, v in value.iteritems():
        if k == 'eval_python':
            value[k] = _coerce_bool(v, 'process.eval_python')
        elif k == 'cwd':
            _validate_type(v, basestring, 'process.cwd')
        elif k == 'command_prefix':
            _validate_type(v, basestring, 'process.command_prefix')
        elif k == 'args':
            value[k] = _dict_to_list_of_strings(v, 'process.args')
        elif k == 'env':
            _validate_type(v, dict, 'process.env')
        else:
            context = ConsumptionContext.get_thread_local()
            context.validation.report('unsupported configuration parameter: "process.{0}"'
                                      .format(k),
                                      level=validation.Issue.BETWEEN_TYPES)
    return value


def _get_ssh(operation):
    value = operation.configuration.get('ssh')._value \
        if 'ssh' in operation.configuration else None
    if value is None:
        return {}
    _validate_type(value, dict, 'ssh')
    value = OrderedDict(value)
    for k, v in value.iteritems():
        if k == 'use_sudo':
            value[k] = _coerce_bool(v, 'ssh.use_sudo')
        elif k == 'hide_output':
            value[k] = _dict_to_list_of_strings(v, 'ssh.hide_output')
        elif k == 'warn_only':
            value[k] = _coerce_bool(v, 'ssh.warn_only')
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
            context.validation.report('unsupported configuration parameter: "ssh.{0}"'.format(k),
                                      level=validation.Issue.BETWEEN_TYPES)
    return value


def _validate_type(value, the_type, name):
    if isinstance(value, Function):
        return
    if not isinstance(value, the_type):
        context = ConsumptionContext.get_thread_local()
        context.validation.report('"{0}" configuration is not a {1}: {2}'
                                  .format(name, full_type_name(the_type), safe_repr(value)),
                                  level=validation.Issue.BETWEEN_TYPES)


def _coerce_bool(value, name):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    _validate_type(value, basestring, name)
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        context = ConsumptionContext.get_thread_local()
        context.validation.report('"{0}" configuration is not "true" or "false": {1}'
                                  .format(name, safe_repr(value)),
                                  level=validation.Issue.BETWEEN_TYPES)


def _dict_to_list_of_strings(the_dict, name):
    _validate_type(the_dict, dict, name)
    value = []
    for k in sorted(the_dict):
        v = the_dict[k]
        _validate_type(v, basestring, '{0}.{1}'.format(name, k))
        value.append(v)
    return value
