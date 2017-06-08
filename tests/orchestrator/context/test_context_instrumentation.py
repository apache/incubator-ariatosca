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

from aria.modeling import models
from aria.storage import collection_instrumentation
from aria.orchestrator.context import operation

from tests import (
    mock,
    storage
)


class TestContextInstrumentation(object):

    @pytest.fixture
    def workflow_ctx(self, tmpdir):
        context = mock.context.simple(str(tmpdir), inmemory=True)
        yield context
        storage.release_sqlite_storage(context.model)

    def test_workflow_context_instrumentation(self, workflow_ctx):
        with workflow_ctx.model.instrument(models.Node.attributes):
            self._run_common_assertions(workflow_ctx, True)
        self._run_common_assertions(workflow_ctx, False)

    def test_operation_context_instrumentation(self, workflow_ctx):
        node = workflow_ctx.model.node.list()[0]
        task = models.Task(node=node)
        workflow_ctx.model.task.put(task)

        ctx = operation.NodeOperationContext(
            task.id, node.id, name='', service_id=workflow_ctx.model.service.list()[0].id,
            model_storage=workflow_ctx.model, resource_storage=workflow_ctx.resource,
            execution_id=1)


        with ctx.model.instrument(models.Node.attributes):
            self._run_op_assertions(ctx, True)
            self._run_common_assertions(ctx, True)

        self._run_op_assertions(ctx, False)
        self._run_common_assertions(ctx, False)
    @staticmethod
    def ctx_assert(expr, is_under_ctx):
        if is_under_ctx:
            assert expr
        else:
            assert not expr

    def _run_op_assertions(self, ctx, is_under_ctx):
        self.ctx_assert(isinstance(ctx.node.attributes,
                                   collection_instrumentation._InstrumentedDict), is_under_ctx)
        assert not isinstance(ctx.node.properties,
                              collection_instrumentation._InstrumentedCollection)

        for rel in ctx.node.inbound_relationships:
            self.ctx_assert(
                isinstance(rel, collection_instrumentation._WrappedModel), is_under_ctx)
            self.ctx_assert(
                isinstance(rel.source_node.attributes,
                           collection_instrumentation._InstrumentedDict),
                is_under_ctx)
            self.ctx_assert(
                isinstance(rel.target_node.attributes,
                           collection_instrumentation._InstrumentedDict),
                is_under_ctx)

    def _run_common_assertions(self, ctx, is_under_ctx):

        for node in ctx.model.node:
            self.ctx_assert(
                isinstance(node.attributes, collection_instrumentation._InstrumentedDict),
                is_under_ctx)
            assert not isinstance(node.properties,
                                  collection_instrumentation._InstrumentedCollection)

        for rel in ctx.model.relationship:
            self.ctx_assert(
                isinstance(rel, collection_instrumentation._WrappedModel), is_under_ctx)

            self.ctx_assert(
                isinstance(rel.source_node.attributes,
                           collection_instrumentation._InstrumentedDict),
                is_under_ctx)
            self.ctx_assert(
                isinstance(rel.target_node.attributes,
                           collection_instrumentation._InstrumentedDict),
                is_under_ctx)

            assert not isinstance(rel.source_node.properties,
                                  collection_instrumentation._InstrumentedCollection)
            assert not isinstance(rel.target_node.properties,
                                  collection_instrumentation._InstrumentedCollection)
