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

import sys

from aria.orchestrator.workflows.core import engine


def op_path(func, module_path=None):
    module_path = module_path or sys.modules[__name__].__name__
    return '{0}.{1}'.format(module_path, func.__name__)


def execute(workflow_func, workflow_context, executor):
    graph = workflow_func(ctx=workflow_context)
    eng = engine.Engine(executor=executor, workflow_context=workflow_context, tasks_graph=graph)
    eng.execute()
