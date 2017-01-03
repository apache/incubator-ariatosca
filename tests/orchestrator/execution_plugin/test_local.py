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

import json
import os

import pytest

from aria import workflow
from aria.orchestrator import events
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.exceptions import ExecutorException
from aria.orchestrator.exceptions import TaskAbortException, TaskRetryException
from aria.orchestrator.execution_plugin import operations
from aria.orchestrator.execution_plugin.exceptions import ProcessException
from aria.orchestrator.execution_plugin import local
from aria.orchestrator.execution_plugin import constants
from aria.orchestrator.workflows.executor import process
from aria.orchestrator.workflows.core import engine

from tests import mock, storage
from tests.orchestrator.workflows.helpers import events_collector

IS_WINDOWS = os.name == 'nt'


class TestLocalRunScript(object):

    def test_script_path_parameter(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx node-instance runtime-properties map.key value
            ''',
            windows_script='''
            ctx node-instance runtime-properties map.key value
        ''')
        props = self._run(
            executor, workflow_context,
            script_path=script_path)
        assert props['map']['key'] == 'value'

    def test_process_env(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx node-instance runtime-properties map.key1 $key1
            ctx node-instance runtime-properties map.key2 $key2
            ''',
            windows_script='''
            ctx node-instance runtime-properties map.key1 %key1%
            ctx node-instance runtime-properties map.key2 %key2%
        ''')
        props = self._run(
            executor, workflow_context,
            script_path=script_path,
            process={
                'env': {
                    'key1': 'value1',
                    'key2': 'value2'
                }
            })
        p_map = props['map']
        assert p_map['key1'] == 'value1'
        assert p_map['key2'] == 'value2'

    def test_process_cwd(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx node-instance runtime-properties map.cwd $PWD
            ''',
            windows_script='''
            ctx node-instance runtime-properties map.cwd %CD%
            ''')
        tmpdir = str(tmpdir)
        props = self._run(
            executor, workflow_context,
            script_path=script_path,
            process={
                'cwd': tmpdir
            })
        p_map = props['map']
        assert p_map['cwd'] == tmpdir

    def test_process_command_prefix(self, executor, workflow_context, tmpdir):
        use_ctx = 'ctx node-instance runtime-properties map.key value'
        python_script = ['import subprocess',
                         'subprocess.Popen("{0}".split(' ')).communicate()[0]'.format(use_ctx)]
        python_script = '\n'.join(python_script)
        script_path = self._create_script(
            tmpdir,
            linux_script=python_script,
            windows_script=python_script,
            windows_suffix='',
            linux_suffix='')
        props = self._run(
            executor, workflow_context,
            script_path=script_path,
            process={
                'env': {'TEST_KEY': 'value'},
                'command_prefix': 'python'
            })
        p_map = props['map']
        assert p_map['key'] == 'value'

    def test_process_args(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx node-instance runtime-properties map.arg1 "$1"
            ctx node-instance runtime-properties map.arg2 $2
            ''',
            windows_script='''
            ctx node-instance runtime-properties map.arg1 %1
            ctx node-instance runtime-properties map.arg2 %2
            ''')
        props = self._run(
            executor, workflow_context,
            script_path=script_path,
            process={
                'args': ['"arg with spaces"', 'arg2']
            })
        assert props['map']['arg1'] == 'arg with spaces'
        assert props['map']['arg2'] == 'arg2'

    def test_no_script_path(self, executor, workflow_context):
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=None)
        assert isinstance(exception, TaskAbortException)
        assert 'script_path' in exception.message

    def test_script_error(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            echo 123123
            command_that_does_not_exist
            ''',
            windows_script='''
            @echo off
            echo 123123
            command_that_does_not_exist
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, ProcessException)
        assert os.path.basename(script_path) in exception.command
        assert exception.exit_code == 1 if IS_WINDOWS else 127
        assert exception.stdout.strip() == '123123'
        assert 'command_that_does_not_exist' in exception.stderr

    def test_script_error_from_bad_ctx_request(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx property_that_does_not_exist
            ''',
            windows_script='''
            ctx property_that_does_not_exist
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, ProcessException)
        assert os.path.basename(script_path) in exception.command
        assert exception.exit_code == 1
        assert 'RequestError' in exception.stderr
        assert 'property_that_does_not_exist' in exception.stderr

    def test_python_script(self, executor, workflow_context, tmpdir):
        script = '''
from aria.orchestrator.execution_plugin import ctx, inputs
if __name__ == '__main__':
    ctx.node_instance.runtime_properties['key'] = inputs['key']
'''
        suffix = '.py'
        script_path = self._create_script(
            tmpdir,
            linux_script=script,
            windows_script=script,
            linux_suffix=suffix,
            windows_suffix=suffix)
        props = self._run(
            executor, workflow_context,
            script_path=script_path,
            inputs={'key': 'value'})
        assert props['key'] == 'value'

    @pytest.mark.parametrize(
        'value', ['string-value', [1, 2, 3], 999, 3.14, False,
                  {'complex1': {'complex2': {'key': 'value'}, 'list': [1, 2, 3]}}])
    def test_inputs_as_environment_variables(self, executor, workflow_context, tmpdir, value):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx node-instance runtime-properties key "${input_as_env_var}"
            ''',
            windows_script='''
            ctx node-instance runtime-properties key "%input_as_env_var%"
        ''')
        props = self._run(
            executor, workflow_context,
            script_path=script_path,
            env_var=value)
        expected = props['key'] if isinstance(value, basestring) else json.loads(props['key'])
        assert expected == value

    @pytest.mark.parametrize('value', ['override', {'key': 'value'}])
    def test_explicit_env_variables_inputs_override(
            self, executor, workflow_context, tmpdir, value):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx node-instance runtime-properties key "${input_as_env_var}"
            ''',
            windows_script='''
            ctx node-instance runtime-properties key "%input_as_env_var%"
        ''')

        props = self._run(
            executor, workflow_context,
            script_path=script_path,
            env_var='test-value',
            process={
                'env': {
                    'input_as_env_var': value
                }
            })
        expected = props['key'] if isinstance(value, basestring) else json.loads(props['key'])
        assert expected == value

    def test_get_nonexistent_runtime_property(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx node-instance runtime-properties nonexistent
            ''',
            windows_script='''
            ctx node-instance runtime-properties nonexistent
        ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, ProcessException)
        assert os.path.basename(script_path) in exception.command
        assert 'RequestError' in exception.stderr
        assert 'nonexistent' in exception.stderr

    def test_get_nonexistent_runtime_property_json(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx -j instance runtime-properties nonexistent
            ''',
            windows_script='''
            ctx -j instance runtime-properties nonexistent
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, ProcessException)
        assert os.path.basename(script_path) in exception.command
        assert 'RequestError' in exception.stderr
        assert 'nonexistent' in exception.stderr

    def test_abort(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx task abort abort-message
            ''',
            windows_script='''
            ctx task abort abort-message
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, TaskAbortException)
        assert exception.message == 'abort-message'

    def test_retry(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx task retry retry-message
            ''',
            windows_script='''
            ctx task retry retry-message
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, TaskRetryException)
        assert exception.message == 'retry-message'

    def test_retry_with_interval(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx task retry retry-message @100
            ''',
            windows_script='''
            ctx task retry retry-message @100
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, TaskRetryException)
        assert exception.message == 'retry-message'
        assert exception.retry_interval == 100

    def test_crash_abort_after_retry(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash
            ctx task retry retry-message
            ctx task abort should-raise-a-runtime-error
            ''',
            windows_script='''
            ctx task retry retry-message
            ctx task abort should-raise-a-runtime-error
        ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, TaskAbortException)
        assert exception.message == constants.ILLEGAL_CTX_OPERATION_MESSAGE

    def test_crash_retry_after_abort(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash
            ctx task abort abort-message
            ctx task retry should-raise-a-runtime-error
            ''',
            windows_script='''
            ctx task abort abort-message
            ctx task retry should-raise-a-runtime-error
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, TaskAbortException)
        assert exception.message == constants.ILLEGAL_CTX_OPERATION_MESSAGE

    def test_crash_abort_after_abort(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash
            ctx task abort abort-message
            ctx task abort should-raise-a-runtime-error
            ''',
            windows_script='''
            ctx task abort abort-message
            ctx task abort should-raise-a-runtime-error
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, TaskAbortException)
        assert exception.message == constants.ILLEGAL_CTX_OPERATION_MESSAGE

    def test_crash_retry_after_retry(self, executor, workflow_context, tmpdir):
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash
            ctx task retry retry-message
            ctx task retry should-raise-a-runtime-error
            ''',
            windows_script='''
            ctx task retry retry-message
            ctx task retry should-raise-a-runtime-error
            ''')
        exception = self._run_and_get_task_exception(
            executor, workflow_context,
            script_path=script_path)
        assert isinstance(exception, TaskAbortException)
        assert exception.message == constants.ILLEGAL_CTX_OPERATION_MESSAGE

    def test_retry_returns_a_nonzero_exit_code(self, executor, workflow_context, tmpdir):
        log_path = tmpdir.join('temp.log')
        message = 'message'
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx task retry '{0}' 2> {1}
            echo should-not-run > {1}
            '''.format(message, log_path),
            windows_script='''
            ctx task retry "{0}" 2> {1}
            if %errorlevel% neq 0 exit /b %errorlevel%
            echo should-not-run > {1}
            '''.format(message, log_path))
        with pytest.raises(ExecutorException):
            self._run(
                executor, workflow_context,
                script_path=script_path)
        assert log_path.read().strip() == message

    def test_abort_returns_a_nonzero_exit_code(self, executor, workflow_context, tmpdir):
        log_path = tmpdir.join('temp.log')
        message = 'message'
        script_path = self._create_script(
            tmpdir,
            linux_script='''#! /bin/bash -e
            ctx task abort '{0}' 2> {1}
            echo should-not-run > {1}
            '''.format(message, log_path),
            windows_script='''
            ctx task abort "{0}" 2> {1}
            if %errorlevel% neq 0 exit /b %errorlevel%
            echo should-not-run > {1}
            '''.format(message, log_path))
        with pytest.raises(ExecutorException):
            self._run(
                executor, workflow_context,
                script_path=script_path)
        assert log_path.read().strip() == message

    def _create_script(self,
                       tmpdir,
                       linux_script,
                       windows_script,
                       windows_suffix='.bat',
                       linux_suffix=''):
        suffix = windows_suffix if IS_WINDOWS else linux_suffix
        script = windows_script if IS_WINDOWS else linux_script
        script_path = tmpdir.join('script{0}'.format(suffix))
        script_path.write(script)
        return str(script_path)

    def _run_and_get_task_exception(self, *args, **kwargs):
        signal = events.on_failure_task_signal
        with events_collector(signal) as collected:
            with pytest.raises(ExecutorException):
                self._run(*args, **kwargs)
        return collected[signal][0]['kwargs']['exception']

    def _run(self,
             executor,
             workflow_context,
             script_path,
             process=None,
             env_var='value',
             inputs=None):
        local_script_path = script_path
        script_path = os.path.basename(local_script_path) if local_script_path else None
        if script_path:
            workflow_context.resource.deployment.upload(
                entry_id=str(workflow_context.deployment.id),
                source=local_script_path,
                path=script_path)

        inputs = inputs or {}
        inputs.update({
            'script_path': script_path,
            'process': process,
            'input_as_env_var': env_var
        })

        @workflow
        def mock_workflow(ctx, graph):
            op = 'test.op'
            node_instance = ctx.model.node_instance.get_by_name(
                mock.models.DEPENDENCY_NODE_INSTANCE_NAME)
            node_instance.node.operations[op] = {
                'operation': '{0}.{1}'.format(operations.__name__,
                                              operations.run_script_locally.__name__)}
            graph.add_tasks(api.task.OperationTask.node_instance(
                instance=node_instance,
                name=op,
                inputs=inputs))
            return graph
        tasks_graph = mock_workflow(ctx=workflow_context)  # pylint: disable=no-value-for-parameter
        eng = engine.Engine(
            executor=executor,
            workflow_context=workflow_context,
            tasks_graph=tasks_graph)
        eng.execute()
        return workflow_context.model.node_instance.get_by_name(
            mock.models.DEPENDENCY_NODE_INSTANCE_NAME).runtime_properties

    @pytest.fixture
    def executor(self):
        result = process.ProcessExecutor()
        yield result
        result.close()

    @pytest.fixture
    def workflow_context(self, tmpdir):
        workflow_context = mock.context.simple(
            storage.get_sqlite_api_kwargs(str(tmpdir)),
            resources_dir=str(tmpdir.join('resources')))
        workflow_context.states = []
        workflow_context.exception = None
        yield workflow_context
        storage.release_sqlite_storage(workflow_context.model)


class BaseTestConfiguration(object):

    @pytest.fixture(autouse=True)
    def mock_execute(self, mocker):
        def eval_func(**_):
            self.called = 'eval'

        def execute_func(process, **_):
            self.process = process
            self.called = 'execute'
        self.process = {}
        self.called = None
        mocker.patch.object(local, '_execute_func', execute_func)
        mocker.patch.object(local, '_eval_script_func', eval_func)

    class Ctx(object):
        @staticmethod
        def download_resource(destination, *args, **kwargs):
            return destination

    def _run(self, script_path, process=None):
        local.run_script(
            script_path=script_path,
            process=process,
            ctx=self.Ctx)


class TestPowerShellConfiguration(BaseTestConfiguration):

    def test_implicit_powershell_call_with_ps1_extension(self):
        self._run(script_path='script_path.ps1')
        assert self.process['command_prefix'] == 'powershell'

    def test_command_prefix_is_overridden_for_ps1_extension(self):
        self._run(script_path='script_path.ps1',
                  process={'command_prefix': 'bash'})
        assert self.process['command_prefix'] == 'bash'

    def test_explicit_powershell_call(self):
        self._run(script_path='script_path.ps1',
                  process={'command_prefix': 'powershell'})
        assert self.process['command_prefix'] == 'powershell'


class TestEvalPythonConfiguration(BaseTestConfiguration):

    def test_explicit_eval_without_py_extension(self):
        self._run(script_path='script_path',
                  process={'eval_python': True})
        assert self.called == 'eval'

    def test_explicit_eval_with_py_extension(self):
        self._run(script_path='script_path.py',
                  process={'eval_python': True})
        assert self.called == 'eval'

    def test_implicit_eval(self):
        self._run(script_path='script_path.py')
        assert self.called == 'eval'

    def test_explicit_execute_without_py_extension(self):
        self._run(script_path='script_path',
                  process={'eval_python': False})
        assert self.called == 'execute'

    def test_explicit_execute_with_py_extension(self):
        self._run(script_path='script_path.py',
                  process={'eval_python': False})
        assert self.called == 'execute'

    def test_implicit_execute(self):
        self._run(script_path='script_path')
        assert self.called == 'execute'
