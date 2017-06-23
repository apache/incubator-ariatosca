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

"""
Built-in uninstall workflow.
"""

from ... import workflow
from ..api import task as api_task
from . import workflows


@workflow
def uninstall(ctx, graph):
    """
    Built-in uninstall workflow.
    """
    tasks_and_nodes = []
    for node in ctx.nodes:
        tasks_and_nodes.append((api_task.WorkflowTask(workflows.uninstall_node, node=node), node))
    graph.add_tasks([task for task, _ in tasks_and_nodes])
    workflows.create_node_task_dependencies(graph, tasks_and_nodes, reverse=True)
