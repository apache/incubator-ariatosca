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
from aria.orchestrator.workflows.core import engine
from aria.orchestrator.workflows.executor import process
from aria.orchestrator import workflow, operation

import tests
from tests import mock
from tests import storage


def test_decorate_extension(context, executor):
    inputs = {'input1': 1, 'input2': 2}

    def get_node(ctx):
        return ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)

    @workflow
    def mock_workflow(ctx, graph):
        node = get_node(ctx)
        interface_name = 'test_interface'
        operation_name = 'operation'
        interface = mock.models.create_interface(
            ctx.service,
            interface_name,
            operation_name,
            operation_kwargs=dict(implementation='{0}.{1}'.format(__name__,
                                                                  _mock_operation.__name__))
        )
        node.interfaces[interface.name] = interface
        task = api.task.OperationTask.for_node(node=node,
                                               interface_name=interface_name,
                                               operation_name=operation_name,
                                               inputs=inputs)
        graph.add_tasks(task)
        return graph
    graph = mock_workflow(ctx=context)  # pylint: disable=no-value-for-parameter
    eng = engine.Engine(executor=executor, workflow_context=context, tasks_graph=graph)
    eng.execute()
    out = get_node(context).runtime_properties['out']
    assert out['wrapper_inputs'] == inputs
    assert out['function_inputs'] == inputs


@extension.process_executor
class MockProcessExecutorExtension(object):

    def decorate(self):
        def decorator(function):
            def wrapper(ctx, **operation_inputs):
                ctx.node.runtime_properties['out'] = {'wrapper_inputs': operation_inputs}
                function(ctx=ctx, **operation_inputs)
            return wrapper
        return decorator


@operation
def _mock_operation(ctx, **operation_inputs):
    ctx.node.runtime_properties['out']['function_inputs'] = operation_inputs


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
