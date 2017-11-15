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

import aria
from aria.orchestrator import context
from aria.storage import (
    sql_mapi,
    filesystem_rapi,
)

from . import models
from ..storage import init_inmemory_model_storage
from .topology import create_simple_topology_two_nodes

from tests.rest_mapi.core import ARESTClient


def simple(tmpdir, inmemory=False, context_kwargs=None, topology=None):
    initiator = init_inmemory_model_storage if inmemory else None
    initiator_kwargs = {} if inmemory else dict(base_dir=tmpdir)
    topology = topology or create_simple_topology_two_nodes

    model_storage = aria.application_model_storage(
        sql_mapi.SQLAlchemyModelAPI, initiator=initiator, initiator_kwargs=initiator_kwargs)
    resource_storage = aria.application_resource_storage(
        filesystem_rapi.FileSystemResourceAPI,
        api_kwargs=dict(directory=os.path.join(tmpdir, 'resources'))
    )

    service_id = topology(model_storage)
    execution = models.create_execution(model_storage.service.get(service_id))
    model_storage.execution.put(execution)

    final_kwargs = dict(
        name='simple_context',
        model_storage=model_storage,
        resource_storage=resource_storage,
        service_id=service_id,
        workflow_name=models.WORKFLOW_NAME,
        execution_id=execution.id,
        task_max_attempts=models.TASK_MAX_ATTEMPTS,
        task_retry_interval=models.TASK_RETRY_INTERVAL
    )
    final_kwargs.update(context_kwargs or {})
    return context.workflow.WorkflowContext(**final_kwargs)
