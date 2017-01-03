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
import time
import sys
import subprocess
import StringIO

import pytest

from aria.orchestrator.execution_plugin import ctx_proxy


class TestCtxProxy(object):

    def test_attribute_access(self, server):
        response = self.request(server, 'stub_attr', 'some_property')
        assert response == 'some_value'

    def test_sugared_attribute_access(self, server):
        response = self.request(server, 'stub-attr', 'some-property')
        assert response == 'some_value'

    def test_dict_prop_access_get_key(self, server):
        response = self.request(server, 'node', 'properties', 'prop1')
        assert response == 'value1'

    def test_dict_prop_access_get_key_nested(self, server):
        response = self.request(server, 'node', 'properties', 'prop2.nested_prop1')
        assert response == 'nested_value1'

    def test_dict_prop_access_get_with_list_index(self, server):
        response = self.request(server, 'node', 'properties', 'prop3[2].value')
        assert response == 'value_2'

    def test_dict_prop_access_set(self, server, ctx):
        self.request(server, 'node', 'properties', 'prop4.key', 'new_value')
        self.request(server, 'node', 'properties', 'prop3[2].value', 'new_value_2')
        self.request(server, 'node', 'properties', 'prop4.some.new.path',
                     'some_new_value')
        assert ctx.node.properties['prop4']['key'] == 'new_value'
        assert ctx.node.properties['prop3'][2]['value'] == 'new_value_2'
        assert ctx.node.properties['prop4']['some']['new']['path'] == 'some_new_value'

    def test_illegal_dict_access(self, server):
        self.request(server, 'node', 'properties', 'prop4.key', 'new_value')
        with pytest.raises(RuntimeError):
            self.request(server, 'node', 'properties', 'prop4.key', 'new_value', 'what')

    def test_method_invocation(self, server):
        args = ['arg1', 'arg2', 'arg3']
        response_args = self.request(server, 'stub-method', *args)
        assert response_args == args

    def test_method_invocation_no_args(self, server):
        response = self.request(server, 'stub-method')
        assert response == []

    def test_method_invocation_kwargs(self, server):
        arg1 = 'arg1'
        arg2 = 'arg2'
        arg4 = 'arg4_override'
        arg5 = 'arg5'
        kwargs = dict(
            arg4=arg4,
            arg5=arg5)
        response = self.request(server, 'stub_args', arg1, arg2, kwargs)
        assert response == dict(
            arg1=arg1,
            arg2=arg2,
            arg3='arg3',
            arg4=arg4,
            args=[],
            kwargs=dict(
                arg5=arg5))

    def test_empty_return_value(self, server):
        response = self.request(server, 'stub_none')
        assert response is None

    def test_client_request_timeout(self, server):
        with pytest.raises(IOError):
            ctx_proxy.client._client_request(server.socket_url,
                                             args=['stub-sleep', '0.5'],
                                             timeout=0.1)

    def test_processing_exception(self, server):
        with pytest.raises(ctx_proxy.client._RequestError):
            self.request(server, 'property_that_does_not_exist')

    def test_not_json_serializable(self, server):
        with pytest.raises(ctx_proxy.client._RequestError):
            self.request(server, 'logger')

    def test_no_string_arg(self, server):
        args = ['stub_method', 1, 2]
        response = self.request(server, *args)
        assert response == args[1:]

    class StubAttribute(object):
        some_property = 'some_value'

    class NodeAttribute(object):
        def __init__(self, properties):
            self.properties = properties

    @staticmethod
    def stub_method(*args):
        return args

    @staticmethod
    def stub_sleep(seconds):
        time.sleep(float(seconds))

    @staticmethod
    def stub_args(arg1, arg2, arg3='arg3', arg4='arg4', *args, **kwargs):
        return dict(
            arg1=arg1,
            arg2=arg2,
            arg3=arg3,
            arg4=arg4,
            args=args,
            kwargs=kwargs)

    @pytest.fixture
    def ctx(self):
        class MockCtx(object):
            pass
        ctx = MockCtx()
        properties = {
            'prop1': 'value1',
            'prop2': {
                'nested_prop1': 'nested_value1'
            },
            'prop3': [
                {'index': 0, 'value': 'value_0'},
                {'index': 1, 'value': 'value_1'},
                {'index': 2, 'value': 'value_2'}
            ],
            'prop4': {
                'key': 'value'
            }
        }
        ctx.stub_none = None
        ctx.stub_method = self.stub_method
        ctx.stub_sleep = self.stub_sleep
        ctx.stub_args = self.stub_args
        ctx.stub_attr = self.StubAttribute()
        ctx.node = self.NodeAttribute(properties)
        return ctx

    @pytest.fixture
    def server(self, ctx):
        result = ctx_proxy.server.CtxProxy(ctx)
        yield result
        result.close()

    def request(self, server, *args):
        return ctx_proxy.client._client_request(server.socket_url, args, timeout=5)


class TestArgumentParsing(object):

    def test_socket_url_arg(self):
        self.expected.update(dict(socket_url='sock_url'))
        ctx_proxy.client.main(['--socket-url', self.expected.get('socket_url')])

    def test_socket_url_env(self):
        expected_socket_url = 'env_sock_url'
        os.environ['CTX_SOCKET_URL'] = expected_socket_url
        self.expected.update(dict(socket_url=expected_socket_url))
        ctx_proxy.client.main([])

    def test_socket_url_missing(self):
        del os.environ['CTX_SOCKET_URL']
        with pytest.raises(RuntimeError):
            ctx_proxy.client.main([])

    def test_args(self):
        self.expected.update(dict(args=['1', '2', '3']))
        ctx_proxy.client.main(self.expected.get('args'))

    def test_timeout(self):
        self.expected.update(dict(timeout='10'))
        ctx_proxy.client.main(['--timeout', self.expected.get('timeout')])
        self.expected.update(dict(timeout='15'))
        ctx_proxy.client.main(['-t', self.expected.get('timeout')])

    def test_mixed_order(self):
        self.expected.update(dict(
            args=['1', '2', '3'], timeout='20', socket_url='mixed_socket_url'))
        ctx_proxy.client.main(
            ['-t', self.expected.get('timeout')] +
            ['--socket-url', self.expected.get('socket_url')] +
            self.expected.get('args'))
        ctx_proxy.client.main(
            ['-t', self.expected.get('timeout')] +
            self.expected.get('args') +
            ['--socket-url', self.expected.get('socket_url')])
        ctx_proxy.client.main(
            self.expected.get('args') +
            ['-t', self.expected.get('timeout')] +
            ['--socket-url', self.expected.get('socket_url')])

    def test_json_args(self):
        args = ['@1', '@[1,2,3]', '@{"key":"value"}']
        expected_args = [1, [1, 2, 3], {'key': 'value'}]
        self.expected.update(dict(args=expected_args))
        ctx_proxy.client.main(args)

    def test_json_arg_prefix(self):
        args = ['_1', '@1']
        expected_args = [1, '@1']
        self.expected.update(dict(args=expected_args))
        ctx_proxy.client.main(args + ['--json-arg-prefix', '_'])

    def test_json_output(self):
        self.assert_valid_output('string', 'string', '"string"')
        self.assert_valid_output(1, '1', '1')
        self.assert_valid_output([1, '2'], "[1, '2']", '[1, "2"]')
        self.assert_valid_output({'key': 1},
                                 "{'key': 1}",
                                 '{"key": 1}')
        self.assert_valid_output(False, '', 'false')
        self.assert_valid_output(True, 'True', 'true')
        self.assert_valid_output([], '', '[]')
        self.assert_valid_output({}, '', '{}')

    def assert_valid_output(self, response, ex_typed_output, ex_json_output):
        self.mock_response = response
        current_stdout = sys.stdout

        def run(args, expected):
            output = StringIO.StringIO()
            sys.stdout = output
            ctx_proxy.client.main(args)
            assert output.getvalue() == expected

        try:
            run([], ex_typed_output)
            run(['-j'], ex_json_output)
            run(['--json-output'], ex_json_output)
        finally:
            sys.stdout = current_stdout

    def mock_client_request(self, socket_url, args, timeout):
        assert socket_url == self.expected.get('socket_url')
        assert args == self.expected.get('args')
        assert timeout == int(self.expected.get('timeout'))
        return self.mock_response

    @pytest.fixture(autouse=True)
    def patch_client_request(self, mocker):
        mocker.patch.object(ctx_proxy.client,
                            ctx_proxy.client._client_request.__name__,
                            self.mock_client_request)
        mocker.patch.dict('os.environ', {'CTX_SOCKET_URL': 'stub'})

    @pytest.fixture(autouse=True)
    def defaults(self):
        self.expected = dict(args=[], timeout=30, socket_url='stub')
        self.mock_response = None


class TestCtxEntryPoint(object):

    def test_ctx_in_path(self):
        p = subprocess.Popen(['ctx', '--help'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        p.communicate()
        assert not p.wait()


class TestPathDictAccess(object):
    def test_simple_set(self):
        obj = {}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        path_dict.set('foo', 42)
        assert obj == {'foo': 42}

    def test_nested_set(self):
        obj = {'foo': {}}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        path_dict.set('foo.bar', 42)
        assert obj == {'foo': {'bar': 42}}

    def test_set_index(self):
        obj = {'foo': [None, {'bar': 0}]}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        path_dict.set('foo[1].bar', 42)
        assert obj == {'foo': [None, {'bar': 42}]}

    def test_set_nonexistent_parent(self):
        obj = {}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        path_dict.set('foo.bar', 42)
        assert obj == {'foo': {'bar': 42}}

    def test_set_nonexistent_parent_nested(self):
        obj = {}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        path_dict.set('foo.bar.baz', 42)
        assert obj == {'foo': {'bar': {'baz': 42}}}

    def test_simple_get(self):
        obj = {'foo': 42}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        result = path_dict.get('foo')
        assert result == 42

    def test_nested_get(self):
        obj = {'foo': {'bar': 42}}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        result = path_dict.get('foo.bar')
        assert result == 42

    def test_nested_get_shadows_dotted_name(self):
        obj = {'foo': {'bar': 42}, 'foo.bar': 58}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        result = path_dict.get('foo.bar')
        assert result == 42

    def test_index_get(self):
        obj = {'foo': [0, 1]}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        result = path_dict.get('foo[1]')
        assert result == 1

    def test_get_nonexistent(self):
        obj = {}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        with pytest.raises(RuntimeError):
            path_dict.get('foo')

    def test_get_by_index_not_list(self):
        obj = {'foo': {0: 'not-list'}}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        with pytest.raises(RuntimeError):
            path_dict.get('foo[0]')

    def test_get_by_index_nonexistent_parent(self):
        obj = {}
        path_dict = ctx_proxy.server._PathDictAccess(obj)
        with pytest.raises(RuntimeError):
            path_dict.get('foo[1]')
