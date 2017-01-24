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

import aria
from aria.orchestrator import context
from aria.storage.filesystem_rapi import FileSystemResourceAPI
from aria.storage.sql_mapi import SQLAlchemyModelAPI

from . import models
from .topology import create_simple_topology_two_nodes


def simple(mapi_kwargs, resources_dir=None, **kwargs):
    model_storage = aria.application_model_storage(SQLAlchemyModelAPI, api_kwargs=mapi_kwargs)

    deployment_id = create_simple_topology_two_nodes(model_storage)

    # pytest tmpdir
    if resources_dir:
        resource_storage = aria.application_resource_storage(
            FileSystemResourceAPI,
            api_kwargs={'directory': resources_dir}
        )
    else:
        resource_storage = None

    final_kwargs = dict(
        name='simple_context',
        model_storage=model_storage,
        resource_storage=resource_storage,
        deployment_id=deployment_id,
        workflow_name=models.WORKFLOW_NAME,
        task_max_attempts=models.TASK_MAX_ATTEMPTS,
        task_retry_interval=models.TASK_RETRY_INTERVAL
    )
    final_kwargs.update(kwargs)
    return context.workflow.WorkflowContext(**final_kwargs)
