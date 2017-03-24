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

from aria.orchestrator.workflows.api import task
from aria.orchestrator.workflows.builtin.execute_operation import execute_operation

from tests import mock, storage


@pytest.fixture
def ctx(tmpdir):
    context = mock.context.simple(str(tmpdir), inmemory=False)
    yield context
    storage.release_sqlite_storage(context.model)


def test_execute_operation(ctx):
    node = ctx.model.node.get_by_name(mock.models.DEPENDENCY_NODE_NAME)
    interface_name, operation_name = mock.operations.NODE_OPERATIONS_INSTALL[0]
    interface = mock.models.create_interface(
        ctx.service,
        interface_name,
        operation_name,
        operation_kwargs={'implementation': 'test'}
    )
    node.interfaces[interface.name] = interface
    ctx.model.node.update(node)

    execute_tasks = list(
        task.WorkflowTask(
            execute_operation,
            ctx=ctx,
            interface_name=interface_name,
            operation_name=operation_name,
            operation_kwargs={},
            allow_kwargs_override=False,
            run_by_dependency_order=False,
            type_names=[],
            node_template_ids=[],
            node_ids=[node.id]
        ).topological_order()
    )

    assert len(execute_tasks) == 1
    assert execute_tasks[0].name == task.OperationTask.NAME_FORMAT.format(
        type='node',
        name=node.name,
        interface=interface_name,
        operation=operation_name
    )


# TODO: add more scenarios
