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

from collections import namedtuple

import requests
import pytest

from aria.storage.modeling import model
from aria.orchestrator import exceptions
from aria.orchestrator.execution_plugin import common


class TestDownloadScript(object):

    @pytest.fixture(autouse=True)
    def patch_requests(self, mocker):
        def _mock_requests_get(url):
            response = namedtuple('Response', 'text status_code')
            return response(url, self.status_code)
        self.status_code = 200
        mocker.patch.object(requests, 'get', _mock_requests_get)

    def _test_url(self, url):
        class Ctx(object):
            task = model.Task

        script_path = url
        result = common.download_script(Ctx, script_path)
        with open(result) as f:
            assert script_path == f.read()
        assert result.endswith('-some_script.py')

    def test_http_url(self):
        self._test_url('http://localhost/some_script.py')

    def test_https_url(self):
        self._test_url('https://localhost/some_script.py')

    def test_url_status_code_404(self):
        self.status_code = 404
        with pytest.raises(exceptions.TaskAbortException) as exc_ctx:
            self.test_http_url()
        exception = exc_ctx.value
        assert 'status code: 404' in str(exception)

    def test_blueprint_resource(self):
        test_script_path = 'my_script.py'

        class Ctx(object):
            @staticmethod
            def download_resource(destination, path):
                assert path == test_script_path
                return destination
        result = common.download_script(Ctx, test_script_path)
        assert result.endswith(test_script_path)


class TestCreateProcessConfig(object):

    def test_plain_command(self):
        script_path = 'path'
        process = common.create_process_config(
            script_path=script_path,
            process={},
            operation_kwargs={})
        assert process['command'] == script_path

    def test_command_with_args(self):
        script_path = 'path'
        process = {'args': [1, 2, 3]}
        process = common.create_process_config(
            script_path=script_path,
            process=process,
            operation_kwargs={})
        assert process['command'] == '{0} 1 2 3'.format(script_path)

    def test_command_prefix(self):
        script_path = 'path'
        command_prefix = 'prefix'
        process = {'command_prefix': command_prefix}
        process = common.create_process_config(
            script_path=script_path,
            process=process,
            operation_kwargs={})
        assert process['command'] == '{0} {1}'.format(command_prefix, script_path)

    def test_command_with_args_and_prefix(self):
        script_path = 'path'
        command_prefix = 'prefix'
        process = {'command_prefix': command_prefix,
                   'args': [1, 2, 3]}
        process = common.create_process_config(
            script_path=script_path,
            process=process,
            operation_kwargs={})
        assert process['command'] == '{0} {1} 1 2 3'.format(command_prefix, script_path)

    def test_ctx_is_removed(self):
        process = common.create_process_config(
            script_path='',
            process={},
            operation_kwargs={'ctx': 1})
        assert 'ctx' not in process['env']

    def test_env_passed_explicitly(self):
        env = {'one': '1', 'two': '2'}
        process = common.create_process_config(
            script_path='',
            process={'env': env},
            operation_kwargs={})
        assert process['env'] == env

    def test_env_populated_from_operation_kwargs(self):
        operation_kwargs = {'one': '1', 'two': '2'}
        process = common.create_process_config(
            script_path='',
            process={},
            operation_kwargs=operation_kwargs)
        assert process['env'] == operation_kwargs

    def test_env_merged_from_operation_kwargs_and_process(self):
        operation_kwargs = {'one': '1', 'two': '2'}
        env = {'three': '3', 'four': '4'}
        process = common.create_process_config(
            script_path='',
            process={'env': env},
            operation_kwargs=operation_kwargs)
        assert process['env'] == dict(operation_kwargs.items() + env.items())

    def test_process_env_gets_precedence_over_operation_kwargs(self):
        operation_kwargs = {'one': 'from_kwargs'}
        env = {'one': 'from_env_process'}
        process = common.create_process_config(
            script_path='',
            process={'env': env},
            operation_kwargs=operation_kwargs)
        assert process['env'] == env

    def test_json_env_vars(self, mocker):
        mocker.patch.object(common, 'is_windows', lambda: False)
        operation_kwargs = {'a_dict': {'key': 'value'},
                            'a_list': ['a', 'b', 'c'],
                            'a_tuple': (4, 5, 6),
                            'a_bool': True}
        process = common.create_process_config(
            script_path='',
            process={},
            operation_kwargs=operation_kwargs)
        assert process['env'] == {'a_dict': '{"key": "value"}',
                                  'a_list': '["a", "b", "c"]',
                                  'a_tuple': '[4, 5, 6]',
                                  'a_bool': 'true'}

    def test_quote_json_env_vars(self):
        operation_kwargs = {'one': []}
        process = common.create_process_config(
            script_path='',
            process={},
            operation_kwargs=operation_kwargs,
            quote_json_env_vars=True)
        assert process['env']['one'] == "'[]'"

    def test_env_keys_converted_to_string_on_windows(self, mocker):
        mocker.patch.object(common, 'is_windows', lambda: True)
        env = {u'one': '1'}
        process = common.create_process_config(
            script_path='',
            process={'env': env},
            operation_kwargs={})
        print type(process['env'].keys()[0])
        assert isinstance(process['env'].keys()[0], str)

    def test_env_values_quotes_are_escaped_on_windows(self, mocker):
        mocker.patch.object(common, 'is_windows', lambda: True)
        env = {'one': '"hello"'}
        process = common.create_process_config(
            script_path='',
            process={'env': env},
            operation_kwargs={})
        assert process['env']['one'] == '\\"hello\\"'
