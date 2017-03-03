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

from aria.orchestrator.runner import Runner
from aria.orchestrator.workflows.builtin import BUILTIN_WORKFLOWS
from aria.utils.imports import import_fullname
from aria.utils.collections import OrderedDict

from tests.parser.service_templates import consume_node_cellar


WORKFLOW_POLICY_INTERNAL_PROPERTIES = ('function', 'implementation', 'dependencies')


def test_install():
    _workflow('install')


def test_custom():
    _workflow('maintenance_on')


def _workflow(workflow_name):
    context, _ = consume_node_cellar()

    # TODO: this logic will eventually stabilize and be part of the ARIA API,
    # likely somewhere in aria.orchestrator.workflows
    if workflow_name in BUILTIN_WORKFLOWS:
        workflow_fn = import_fullname('aria.orchestrator.workflows.builtin.' + workflow_name)
        inputs = {}
    else:
        workflow = None
        for policy in context.modeling.instance.policies:
            if policy.name == workflow_name:
                workflow = policy
                break

        sys.path.append(workflow.properties['implementation'].value)
        workflow_fn = import_fullname(workflow.properties['function'].value)
        inputs = OrderedDict([
            (k, v.value) for k, v in workflow.properties.iteritems()
            if k not in WORKFLOW_POLICY_INTERNAL_PROPERTIES
        ])

    def _initialize_storage(model_storage):
        context.modeling.store(model_storage)

    runner = Runner(workflow_name, workflow_fn, inputs, _initialize_storage,
                    lambda: context.modeling.instance.id)
    runner.run()
