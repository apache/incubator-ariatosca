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
Builtin uninstall workflow
"""

from .workflows import uninstall_node_instance
from .utils import create_node_instance_task_dependencies
from ..api.task import WorkflowTask
from ... import workflow


@workflow
def uninstall(ctx, graph):
    tasks_and_node_instances = []
    for node_instance in ctx.model.node_instance.iter():
        tasks_and_node_instances.append((
            WorkflowTask(uninstall_node_instance, node_instance=node_instance),
            node_instance))
    graph.add_tasks([task for task, _ in tasks_and_node_instances])
    create_node_instance_task_dependencies(graph, tasks_and_node_instances, reverse=True)
