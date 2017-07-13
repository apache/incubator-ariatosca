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
Instantiation of :class:`~aria.modeling.models.Operation` models.
"""

# TODO: this module will eventually be moved to a new "aria.instantiation" package
from ...modeling.functions import Function
from ... import utils


def configure_operation(operation, reporter):
    host = None
    interface = operation.interface
    if interface.node is not None:
        host = interface.node.host
    elif interface.relationship is not None:
        if operation.relationship_edge is True:
            host = interface.relationship.target_node.host
        else: # either False or None (None meaning that edge was not specified)
            host = interface.relationship.source_node.host

    _configure_common(operation, reporter)
    if host is None:
        _configure_local(operation)
    else:
        _configure_remote(operation, reporter)

    # Any remaining un-handled configuration parameters will become extra arguments, available as
    # kwargs in either "run_script_locally" or "run_script_with_ssh"
    for key, value in operation.configurations.iteritems():
        if key not in ('process', 'ssh'):
            operation.arguments[key] = value.instantiate(None)


def _configure_common(operation, reporter):
    """
    Local and remote operations.
    """

    from ...modeling.models import Argument
    operation.arguments['script_path'] = Argument.wrap('script_path', operation.implementation,
                                                       'Relative path to the executable file.')
    operation.arguments['process'] = Argument.wrap('process', _get_process(operation, reporter),
                                                   'Sub-process configuration.')


def _configure_local(operation):
    """
    Local operation.
    """

    from . import operations
    operation.function = '{0}.{1}'.format(operations.__name__,
                                          operations.run_script_locally.__name__)


def _configure_remote(operation, reporter):
    """
    Remote SSH operation via Fabric.
    """

    from ...modeling.models import Argument
    from . import operations

    ssh = _get_ssh(operation, reporter)

    # Defaults
    # TODO: find a way to configure these generally in the service template
    default_user = ''
    default_password = ''
    if 'user' not in ssh:
        ssh['user'] = default_user
    if ('password' not in ssh) and ('key' not in ssh) and ('key_filename' not in ssh):
        ssh['password'] = default_password

    operation.arguments['use_sudo'] = Argument.wrap('use_sudo', ssh.get('use_sudo', False),
                                                    'Whether to execute with sudo.')

    operation.arguments['hide_output'] = Argument.wrap('hide_output', ssh.get('hide_output', []),
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
        reporter.report('must configure "ssh.user" for "{0}"'.format(operation.implementation),
                        level=reporter.Issue.BETWEEN_TYPES)

    # Make sure we have an authentication value
    if (fabric_env.get('password') is None) and \
        (fabric_env.get('key') is None) and \
        (fabric_env.get('key_filename') is None):
        reporter.report(
            'must configure "ssh.password", "ssh.key", or "ssh.key_filename" for "{0}"'
            .format(operation.implementation),
            level=reporter.Issue.BETWEEN_TYPES)

    operation.arguments['fabric_env'] = Argument.wrap('fabric_env', fabric_env,
                                                      'Fabric configuration.')

    operation.function = '{0}.{1}'.format(operations.__name__,
                                          operations.run_script_with_ssh.__name__)


def _get_process(operation, reporter):
    value = (operation.configurations.get('process')._value
             if 'process' in operation.configurations
             else None)
    if value is None:
        return {}
    _validate_type(value, dict, 'process', reporter)
    value = utils.collections.OrderedDict(value)
    for k, v in value.iteritems():
        if k == 'eval_python':
            value[k] = _coerce_bool(v, 'process.eval_python', reporter)
        elif k == 'cwd':
            _validate_type(v, basestring, 'process.cwd', reporter)
        elif k == 'command_prefix':
            _validate_type(v, basestring, 'process.command_prefix', reporter)
        elif k == 'args':
            value[k] = _dict_to_list_of_strings(v, 'process.args', reporter)
        elif k == 'env':
            _validate_type(v, dict, 'process.env', reporter)
        else:
            reporter.report('unsupported configuration parameter: "process.{0}"'.format(k),
                            level=reporter.Issue.BETWEEN_TYPES)
    return value


def _get_ssh(operation, reporter):
    value = (operation.configurations.get('ssh')._value
             if 'ssh' in operation.configurations
             else None)
    if value is None:
        return {}
    _validate_type(value, dict, 'ssh', reporter)
    value = utils.collections.OrderedDict(value)
    for k, v in value.iteritems():
        if k == 'use_sudo':
            value[k] = _coerce_bool(v, 'ssh.use_sudo', reporter)
        elif k == 'hide_output':
            value[k] = _dict_to_list_of_strings(v, 'ssh.hide_output', reporter)
        elif k == 'warn_only':
            value[k] = _coerce_bool(v, 'ssh.warn_only', reporter)
        elif k == 'user':
            _validate_type(v, basestring, 'ssh.user', reporter)
        elif k == 'password':
            _validate_type(v, basestring, 'ssh.password', reporter)
        elif k == 'key':
            _validate_type(v, basestring, 'ssh.key', reporter)
        elif k == 'key_filename':
            _validate_type(v, basestring, 'ssh.key_filename', reporter)
        elif k == 'address':
            _validate_type(v, basestring, 'ssh.address', reporter)
        else:
            reporter.report('unsupported configuration parameter: "ssh.{0}"'.format(k),
                            level=reporter.Issue.BETWEEN_TYPES)
    return value


def _validate_type(value, the_type, name, reporter):
    if isinstance(value, Function):
        return
    if not isinstance(value, the_type):
        reporter.report(
            '"{0}" configuration is not a {1}: {2}'.format(
                name, utils.type.full_type_name(the_type), utils.formatting.safe_repr(value)),
            level=reporter.Issue.BETWEEN_TYPES)


def _coerce_bool(value, name, reporter):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    _validate_type(value, basestring, name, reporter)
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        reporter.report(
            '"{0}" configuration is not "true" or "false": {1}'.format(
                name, utils.formatting.safe_repr(value)),
            level=reporter.Issue.BETWEEN_TYPES)


def _dict_to_list_of_strings(the_dict, name, reporter):
    _validate_type(the_dict, dict, name, reporter)
    value = []
    for k in sorted(the_dict):
        v = the_dict[k]
        _validate_type(v, basestring, '{0}.{1}'.format(name, k), reporter)
        value.append(v)
    return value
