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

import contextlib
import json
import logging
import os

import pytest

import fabric.api
from fabric.contrib import files
from fabric import context_managers

from aria.modeling import models
from aria.orchestrator import events
from aria.orchestrator import workflow
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.executor import process
from aria.orchestrator.workflows.core import engine, graph_compiler
from aria.orchestrator.workflows.exceptions import ExecutorException
from aria.orchestrator.exceptions import TaskAbortException, TaskRetryException
from aria.orchestrator.execution_plugin import operations
from aria.orchestrator.execution_plugin import constants
from aria.orchestrator.execution_plugin.exceptions import ProcessException, TaskException
from aria.orchestrator.execution_plugin.ssh import operations as ssh_operations

from tests import mock, storage, resources
from tests.orchestrator.workflows.helpers import events_collector

_CUSTOM_BASE_DIR = '/tmp/new-aria-ctx'

import tests
KEY_FILENAME = os.path.join(tests.ROOT_DIR, 'tests/resources/keys/test')

_FABRIC_ENV = {
    'disable_known_hosts': True,
    'user': 'test',
    'key_filename': KEY_FILENAME
}


import mockssh
@pytest.fixture(scope='session')
def server():
    with mockssh.Server({'test': KEY_FILENAME}) as s:
        yield s


#@pytest.mark.skipif(not os.environ.get('TRAVIS'), reason='actual ssh server required')
class TestWithActualSSHServer(object):

    def test_run_script_basic(self):
        expected_attribute_value = 'some_value'
        props = self._execute(env={'test_value': expected_attribute_value})
        assert props['test_value'].value == expected_attribute_value

    @pytest.mark.skip(reason='sudo privileges are required')
    def test_run_script_as_sudo(self):
        self._execute(use_sudo=True)
        with self._ssh_env():
            assert files.exists('/opt/test_dir')
            fabric.api.sudo('rm -rf /opt/test_dir')

    def test_run_script_default_base_dir(self):
        props = self._execute()
        assert props['work_dir'].value == '{0}/work'.format(constants.DEFAULT_BASE_DIR)

    @pytest.mark.skip(reason='Re-enable once output from process executor can be captured')
    @pytest.mark.parametrize('hide_groups', [[], ['everything']])
    def test_run_script_with_hide(self, hide_groups):
        self._execute(hide_output=hide_groups)
        output = 'TODO'
        expected_log_message = ('[localhost] run: source {0}/scripts/'
                                .format(constants.DEFAULT_BASE_DIR))
        if hide_groups:
            assert expected_log_message not in output
        else:
            assert expected_log_message in output

    def test_run_script_process_config(self):
        expected_env_value = 'test_value_env'
        expected_arg1_value = 'test_value_arg1'
        expected_arg2_value = 'test_value_arg2'
        expected_cwd = '/tmp'
        expected_base_dir = _CUSTOM_BASE_DIR
        props = self._execute(
            env={'test_value_env': expected_env_value},
            process={
                'args': [expected_arg1_value, expected_arg2_value],
                'cwd': expected_cwd,
                'base_dir': expected_base_dir
            })
        assert props['env_value'].value == expected_env_value
        assert len(props['bash_version'].value) > 0
        assert props['arg1_value'].value == expected_arg1_value
        assert props['arg2_value'].value == expected_arg2_value
        assert props['cwd'].value == expected_cwd
        assert props['ctx_path'].value == '{0}/ctx'.format(expected_base_dir)

    def test_run_script_command_prefix(self):
        props = self._execute(process={'command_prefix': 'bash -i'})
        assert 'i' in props['dollar_dash'].value

    def test_run_script_reuse_existing_ctx(self):
        expected_test_value_1 = 'test_value_1'
        expected_test_value_2 = 'test_value_2'
        props = self._execute(
            test_operations=['{0}_1'.format(self.test_name),
                             '{0}_2'.format(self.test_name)],
            env={'test_value1': expected_test_value_1,
                 'test_value2': expected_test_value_2})
        assert props['test_value1'].value == expected_test_value_1
        assert props['test_value2'].value == expected_test_value_2

    def test_run_script_download_resource_plain(self, tmpdir):
        resource = tmpdir.join('resource')
        resource.write('content')
        self._upload(str(resource), 'test_resource')
        props = self._execute()
        assert props['test_value'].value == 'content'

    def test_run_script_download_resource_and_render(self, tmpdir):
        resource = tmpdir.join('resource')
        resource.write('{{ctx.service.name}}')
        self._upload(str(resource), 'test_resource')
        props = self._execute()
        assert props['test_value'].value == self._workflow_context.service.name

    @pytest.mark.parametrize('value', ['string-value', [1, 2, 3], {'key': 'value'}])
    def test_run_script_inputs_as_env_variables_no_override(self, value):
        props = self._execute(custom_input=value)
        return_value = props['test_value'].value
        expected = return_value if isinstance(value, basestring) else json.loads(return_value)
        assert value == expected

    @pytest.mark.parametrize('value', ['string-value', [1, 2, 3], {'key': 'value'}])
    def test_run_script_inputs_as_env_variables_process_env_override(self, value):
        props = self._execute(custom_input='custom-input-value',
                              env={'custom_env_var': value})
        return_value = props['test_value'].value
        expected = return_value if isinstance(value, basestring) else json.loads(return_value)
        assert value == expected

    def test_run_script_error_in_script(self):
        exception = self._execute_and_get_task_exception()
        assert isinstance(exception, TaskException)

    def test_run_script_abort_immediate(self):
        exception = self._execute_and_get_task_exception()
        assert isinstance(exception, TaskAbortException)
        assert exception.message == 'abort-message'

    def test_run_script_retry(self):
        exception = self._execute_and_get_task_exception()
        assert isinstance(exception, TaskRetryException)
        assert exception.message == 'retry-message'

    def test_run_script_abort_error_ignored_by_script(self):
        exception = self._execute_and_get_task_exception()
        assert isinstance(exception, TaskAbortException)
        assert exception.message == 'abort-message'

    def test_run_commands(self):
        temp_file_path = '/tmp/very_temporary_file'
        with self._ssh_env():
            if files.exists(temp_file_path):
                fabric.api.run('rm {0}'.format(temp_file_path))
        self._execute(commands=['touch {0}'.format(temp_file_path)])
        with self._ssh_env():
            assert files.exists(temp_file_path)
            fabric.api.run('rm {0}'.format(temp_file_path))

    @pytest.fixture(autouse=True)
    def _setup(self, request, workflow_context, executor, capfd, server):
        print 'HI!!!!!!!!!!', server.port
        self._workflow_context = workflow_context
        self._executor = executor
        self._capfd = capfd
        self.test_name = request.node.originalname or request.node.name
        with self._ssh_env(server):
            for directory in [constants.DEFAULT_BASE_DIR, _CUSTOM_BASE_DIR]:
                if files.exists(directory):
                    fabric.api.run('rm -rf {0}'.format(directory))

    @contextlib.contextmanager
    def _ssh_env(self, server):
        with self._capfd.disabled():
            with context_managers.settings(fabric.api.hide('everything'),
                                           host_string='localhost:{0}'.format(server.port),
                                           **_FABRIC_ENV):
                yield

    def _execute(self,
                 env=None,
                 use_sudo=False,
                 hide_output=None,
                 process=None,
                 custom_input='',
                 test_operations=None,
                 commands=None):
        process = process or {}
        if env:
            process.setdefault('env', {}).update(env)

        test_operations = test_operations or [self.test_name]

        local_script_path = os.path.join(resources.DIR, 'scripts', 'test_ssh.sh')
        script_path = os.path.basename(local_script_path)
        self._upload(local_script_path, script_path)

        if commands:
            operation = operations.run_commands_with_ssh
        else:
            operation = operations.run_script_with_ssh

        node = self._workflow_context.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
        arguments = {
            'script_path': script_path,
            'fabric_env': _FABRIC_ENV,
            'process': process,
            'use_sudo': use_sudo,
            'custom_env_var': custom_input,
            'test_operation': '',
        }
        if hide_output:
            arguments['hide_output'] = hide_output
        if commands:
            arguments['commands'] = commands
        interface = mock.models.create_interface(
            node.service,
            'test',
            'op',
            operation_kwargs=dict(
                function='{0}.{1}'.format(
                    operations.__name__,
                    operation.__name__),
                arguments=arguments)
        )
        node.interfaces[interface.name] = interface

        @workflow
        def mock_workflow(ctx, graph):
            ops = []
            for test_operation in test_operations:
                op_arguments = arguments.copy()
                op_arguments['test_operation'] = test_operation
                ops.append(api.task.OperationTask(
                    node,
                    interface_name='test',
                    operation_name='op',
                    arguments=op_arguments))

            graph.sequence(*ops)
            return graph
        tasks_graph = mock_workflow(ctx=self._workflow_context)  # pylint: disable=no-value-for-parameter
        graph_compiler.GraphCompiler(
            self._workflow_context, self._executor.__class__).compile(tasks_graph)
        eng = engine.Engine({self._executor.__class__: self._executor})
        eng.execute(self._workflow_context)
        return self._workflow_context.model.node.get_by_name(
            mock.models.DEPENDENCY_NODE_NAME).attributes

    def _execute_and_get_task_exception(self, *args, **kwargs):
        signal = events.on_failure_task_signal
        with events_collector(signal) as collected:
            with pytest.raises(ExecutorException):
                self._execute(*args, **kwargs)
        return collected[signal][0]['kwargs']['exception']

    def _upload(self, source, path):
        self._workflow_context.resource.service.upload(
            entry_id=str(self._workflow_context.service.id),
            source=source,
            path=path)

    @pytest.fixture
    def executor(self):
        result = process.ProcessExecutor()
        try:
            yield result
        finally:
            result.close()

    @pytest.fixture
    def workflow_context(self, tmpdir):
        workflow_context = mock.context.simple(str(tmpdir))
        workflow_context.states = []
        workflow_context.exception = None
        yield workflow_context
        storage.release_sqlite_storage(workflow_context.model)


class TestFabricEnvHideGroupsAndRunCommands(object):

    def test_fabric_env_default_override(self):
        # first sanity for no override
        self._run()
        assert self.mock.settings_merged['timeout'] == constants.FABRIC_ENV_DEFAULTS['timeout']
        # now override
        invocation_fabric_env = self.default_fabric_env.copy()
        timeout = 1000000
        invocation_fabric_env['timeout'] = timeout
        self._run(fabric_env=invocation_fabric_env)
        assert self.mock.settings_merged['timeout'] == timeout

    def test_implicit_host_string(self, mocker):
        expected_host_address = '1.1.1.1'
        mocker.patch.object(self._Ctx.task.actor, 'host')
        mocker.patch.object(self._Ctx.task.actor.host, 'host_address', expected_host_address)
        fabric_env = self.default_fabric_env.copy()
        del fabric_env['host_string']
        self._run(fabric_env=fabric_env)
        assert self.mock.settings_merged['host_string'] == expected_host_address

    def test_explicit_host_string(self):
        fabric_env = self.default_fabric_env.copy()
        host_string = 'explicit_host_string'
        fabric_env['host_string'] = host_string
        self._run(fabric_env=fabric_env)
        assert self.mock.settings_merged['host_string'] == host_string

    def test_override_warn_only(self):
        fabric_env = self.default_fabric_env.copy()
        self._run(fabric_env=fabric_env)
        assert self.mock.settings_merged['warn_only'] is True
        fabric_env = self.default_fabric_env.copy()
        fabric_env['warn_only'] = False
        self._run(fabric_env=fabric_env)
        assert self.mock.settings_merged['warn_only'] is False

    def test_missing_host_string(self):
        with pytest.raises(TaskAbortException) as exc_ctx:
            fabric_env = self.default_fabric_env.copy()
            del fabric_env['host_string']
            self._run(fabric_env=fabric_env)
        assert '`host_string` not supplied' in str(exc_ctx.value)

    def test_missing_user(self):
        with pytest.raises(TaskAbortException) as exc_ctx:
            fabric_env = self.default_fabric_env.copy()
            del fabric_env['user']
            self._run(fabric_env=fabric_env)
        assert '`user` not supplied' in str(exc_ctx.value)

    def test_missing_key_or_password(self):
        with pytest.raises(TaskAbortException) as exc_ctx:
            fabric_env = self.default_fabric_env.copy()
            del fabric_env['key_filename']
            self._run(fabric_env=fabric_env)
        assert 'Access credentials not supplied' in str(exc_ctx.value)

    def test_hide_in_settings_and_non_viable_groups(self):
        groups = ('running', 'stdout')
        self._run(hide_output=groups)
        assert set(self.mock.settings_merged['hide_output']) == set(groups)
        with pytest.raises(TaskAbortException) as exc_ctx:
            self._run(hide_output=('running', 'bla'))
        assert '`hide_output` must be a subset of' in str(exc_ctx.value)

    def test_run_commands(self):
        def test(use_sudo):
            commands = ['command1', 'command2']
            self._run(
                commands=commands,
                use_sudo=use_sudo)
            assert all(item in self.mock.settings_merged.items() for
                       item in self.default_fabric_env.items())
            assert self.mock.settings_merged['warn_only'] is True
            assert self.mock.settings_merged['use_sudo'] == use_sudo
            assert self.mock.commands == commands
            self.mock.settings_merged = {}
            self.mock.commands = []
        test(use_sudo=False)
        test(use_sudo=True)

    def test_failed_command(self):
        with pytest.raises(ProcessException) as exc_ctx:
            self._run(commands=['fail'])
        exception = exc_ctx.value
        assert exception.stdout == self.MockCommandResult.stdout
        assert exception.stderr == self.MockCommandResult.stderr
        assert exception.command == self.MockCommandResult.command
        assert exception.exit_code == self.MockCommandResult.return_code

    class MockCommandResult(object):
        stdout = 'mock_stdout'
        stderr = 'mock_stderr'
        command = 'mock_command'
        return_code = 1

        def __init__(self, failed):
            self.failed = failed

    class MockFabricApi(object):

        def __init__(self):
            self.commands = []
            self.settings_merged = {}

        @contextlib.contextmanager
        def settings(self, *args, **kwargs):
            self.settings_merged.update(kwargs)
            if args:
                groups = args[0]
                self.settings_merged.update({'hide_output': groups})
            yield

        def run(self, command):
            self.commands.append(command)
            self.settings_merged['use_sudo'] = False
            return TestFabricEnvHideGroupsAndRunCommands.MockCommandResult(command == 'fail')

        def sudo(self, command):
            self.commands.append(command)
            self.settings_merged['use_sudo'] = True
            return TestFabricEnvHideGroupsAndRunCommands.MockCommandResult(command == 'fail')

        def hide(self, *groups):
            return groups

        def exists(self, *args, **kwargs):
            raise RuntimeError

    class _Ctx(object):
        INSTRUMENTATION_FIELDS = ()

        class Task(object):
            @staticmethod
            def abort(message=None):
                models.Task.abort(message)
            actor = None

        class Actor(object):
            host = None

        class Model(object):
            @contextlib.contextmanager
            def instrument(self, *args, **kwargs):
                yield
        task = Task
        task.actor = Actor
        model = Model()
        logger = logging.getLogger()

    @staticmethod
    @contextlib.contextmanager
    def _mock_self_logging(*args, **kwargs):
        yield
    _Ctx.logging_handlers = _mock_self_logging

    @pytest.fixture(autouse=True)
    def _setup(self, mocker):
        self.default_fabric_env = {
            'host_string': 'test',
            'user': 'test',
            'key_filename': 'test',
        }
        self.mock = self.MockFabricApi()
        mocker.patch('fabric.api', self.mock)

    def _run(self,
             commands=(),
             fabric_env=None,
             process=None,
             use_sudo=False,
             hide_output=None):
        operations.run_commands_with_ssh(
            ctx=self._Ctx,
            commands=commands,
            process=process,
            fabric_env=fabric_env or self.default_fabric_env,
            use_sudo=use_sudo,
            hide_output=hide_output)


class TestUtilityFunctions(object):

    def test_paths(self):
        base_dir = '/path'
        local_script_path = '/local/script/path.py'
        paths = ssh_operations._Paths(base_dir=base_dir,
                                      local_script_path=local_script_path)
        assert paths.local_script_path == local_script_path
        assert paths.remote_ctx_dir == base_dir
        assert paths.base_script_path == 'path.py'
        assert paths.remote_ctx_path == '/path/ctx'
        assert paths.remote_scripts_dir == '/path/scripts'
        assert paths.remote_work_dir == '/path/work'
        assert paths.remote_env_script_path.startswith('/path/scripts/env-path.py-')
        assert paths.remote_script_path.startswith('/path/scripts/path.py-')

    def test_write_environment_script_file(self):
        base_dir = '/path'
        local_script_path = '/local/script/path.py'
        paths = ssh_operations._Paths(base_dir=base_dir,
                                      local_script_path=local_script_path)
        env = {'one': "'1'"}
        local_socket_url = 'local_socket_url'
        remote_socket_url = 'remote_socket_url'
        env_script_lines = set([l for l in ssh_operations._write_environment_script_file(
            process={'env': env},
            paths=paths,
            local_socket_url=local_socket_url,
            remote_socket_url=remote_socket_url
        ).getvalue().split('\n') if l])
        expected_env_script_lines = set([
            'export PATH=/path:$PATH',
            'export PYTHONPATH=/path:$PYTHONPATH',
            'chmod +x /path/ctx',
            'chmod +x {0}'.format(paths.remote_script_path),
            'export CTX_SOCKET_URL={0}'.format(remote_socket_url),
            'export LOCAL_CTX_SOCKET_URL={0}'.format(local_socket_url),
            'export one=\'1\''
        ])
        assert env_script_lines == expected_env_script_lines
