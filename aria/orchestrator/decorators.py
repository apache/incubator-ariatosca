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
Workflow and operation decorators
"""

from functools import partial, wraps

from ..utils.validation import validate_function_arguments
from ..utils.uuid import generate_uuid

from . import context
from .workflows.api import task_graph


WORKFLOW_DECORATOR_RESERVED_ARGUMENTS = set(('ctx', 'graph'))
OPERATION_DECORATOR_RESERVED_ARGUMENTS = set(('ctx', 'toolbelt'))


def workflow(func=None, suffix_template=''):
    """
    Workflow decorator
    """
    if func is None:
        return partial(workflow, suffix_template=suffix_template)

    @wraps(func)
    def _wrapper(ctx, **workflow_parameters):

        workflow_name = _generate_name(
            func_name=func.__name__,
            suffix_template=suffix_template,
            ctx=ctx,
            **workflow_parameters)

        workflow_parameters.setdefault('ctx', ctx)
        workflow_parameters.setdefault('graph', task_graph.TaskGraph(workflow_name))
        validate_function_arguments(func, workflow_parameters)
        with context.workflow.current.push(ctx):
            func(**workflow_parameters)
        return workflow_parameters['graph']
    return _wrapper


def operation(func=None, toolbelt=False, suffix_template='', logging_handlers=None):
    """
    Operation decorator
    """

    if func is None:
        return partial(operation,
                       suffix_template=suffix_template,
                       toolbelt=toolbelt,
                       logging_handlers=logging_handlers)

    @wraps(func)
    def _wrapper(**func_kwargs):
        if toolbelt:
            operation_toolbelt = context.toolbelt(func_kwargs['ctx'])
            func_kwargs.setdefault('toolbelt', operation_toolbelt)
        validate_function_arguments(func, func_kwargs)
        return func(**func_kwargs)
    return _wrapper


def _generate_name(func_name, ctx, suffix_template, **custom_kwargs):
    return '{func_name}.{suffix}'.format(
        func_name=func_name,
        suffix=suffix_template.format(ctx=ctx, **custom_kwargs) or generate_uuid(variant='uuid'))
