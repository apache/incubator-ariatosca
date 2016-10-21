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

from aria import context, application_model_storage

from . import models
from ..storage import InMemoryModelDriver


def simple():
    storage = application_model_storage(InMemoryModelDriver())
    storage.setup()
    return context.workflow.WorkflowContext(
        name='simple_context',
        model_storage=storage,
        resource_storage=None,
        deployment_id=models.DEPLOYMENT_ID,
        workflow_id=models.WORKFLOW_ID,
        execution_id=models.EXECUTION_ID
    )
