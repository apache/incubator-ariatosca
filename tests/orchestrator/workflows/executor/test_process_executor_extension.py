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

import pytest

from aria import extension
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.core import engine, graph_compiler
from aria.orchestrator.workflows.executor import process
from aria.orchestrator import workflow, operation

import tests
from tests import mock
from tests import storage


def test_decorate_extension(context, executor):
    arguments = {'arg1': 1, 'arg2': 2}

    def get_node(ctx):
        return ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)

    node = get_node(context)
    interface_name = 'test_interface'
    operation_name = 'operation'
    interface = mock.models.create_interface(
        context.service,
        interface_name,
        operation_name,
        operation_kwargs=dict(function='{0}.{1}'.format(__name__, _mock_operation.__name__),
                              arguments=arguments)
    )
    node.interfaces[interface.name] = interface
    context.model.node.update(node)


    @workflow
    def mock_workflow(ctx, graph):
        node = get_node(ctx)
        task = api.task.OperationTask(
            node,
            interface_name=interface_name,
            operation_name=operation_name,
            arguments=arguments)
        graph.add_tasks(task)
        return graph
    graph = mock_workflow(ctx=context)  # pylint: disable=no-value-for-parameter
    graph_compiler.GraphCompiler(context, executor.__class__).compile(graph)
    eng = engine.Engine({executor.__class__: executor})
    eng.execute(context)
    out = get_node(context).attributes.get('out').value
    assert out['wrapper_arguments'] == arguments
    assert out['function_arguments'] == arguments


@extension.process_executor
class MockProcessExecutorExtension(object):

    def decorate(self):
        def decorator(function):
            def wrapper(ctx, **operation_arguments):
                with ctx.model.instrument(ctx.model.node.model_cls.attributes):
                    ctx.node.attributes['out'] = {'wrapper_arguments': operation_arguments}
                function(ctx=ctx, **operation_arguments)
            return wrapper
        return decorator


@operation
def _mock_operation(ctx, **operation_arguments):
    ctx.node.attributes['out']['function_arguments'] = operation_arguments


@pytest.fixture
def executor():
    result = process.ProcessExecutor(python_path=[tests.ROOT_DIR])
    yield result
    result.close()


@pytest.fixture
def context(tmpdir):
    result = mock.context.simple(str(tmpdir))
    yield result
    storage.release_sqlite_storage(result.model)
