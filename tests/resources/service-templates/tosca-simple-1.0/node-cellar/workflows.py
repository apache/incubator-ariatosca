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


from aria import workflow
from aria.orchestrator.workflows.api import task
from aria.orchestrator.workflows.exceptions import TaskException


INTERFACE_NAME = 'Maintenance'
ENABLE_OPERATION_NAME = 'enable'
DISABLE_OPERATION_NAME = 'disable'


@workflow
def maintenance(ctx, graph, enabled):
    """
    Custom workflow to call the operations on the Maintenance interface.
    """

    for node in ctx.model.node.iter():
        try:
            graph.add_tasks(task.OperationTask(node,
                                               interface_name=INTERFACE_NAME,
                                               operation_name=ENABLE_OPERATION_NAME if enabled
                                               else DISABLE_OPERATION_NAME))
        except TaskException:
            pass
