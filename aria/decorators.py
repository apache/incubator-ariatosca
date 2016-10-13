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

from uuid import uuid4
from functools import partial, wraps

from aria.tools.validation import validate_function_arguments


def workflow(
        func=None,
        workflow_context=True,
        simple_workflow=True,
        suffix_template=''):
    if func is None:
        return partial(
            workflow,
            workflow_context=workflow_context,
            simple_workflow=simple_workflow,
            suffix_template=suffix_template)

    @wraps(func)
    def wrapper(context, **custom_kwargs):
        workflow_name = _generate_workflow_name(
            func_name=func.__name__,
            suffix_template=suffix_template,
            context=context,
            **custom_kwargs)
        func_kwargs = _create_func_kwargs(
            custom_kwargs,
            context,
            add_context=workflow_context,
            workflow_name=workflow_name)
        validate_function_arguments(func, func_kwargs)
        func(**func_kwargs)
        return func_kwargs['graph']
    return wrapper


def operation(
        func=None,
        operation_context=True):
    if func is None:
        return partial(operation)

    @wraps(func)
    def wrapper(context, **custom_kwargs):
        func_kwargs = _create_func_kwargs(
            custom_kwargs,
            context,
            add_context=operation_context)
        validate_function_arguments(func, func_kwargs)
        context.description = func.__doc__
        return func(**func_kwargs)
    return wrapper


def _generate_workflow_name(func_name, context, suffix_template, **custom_kwargs):
    return '{func_name}.{suffix}'.format(
        func_name=func_name,
        context=context,
        suffix=suffix_template.format(context=context, **custom_kwargs) or str(uuid4()))


def _create_func_kwargs(
        kwargs,
        context,
        add_context=True,
        workflow_name=None):
    if add_context:
        kwargs['context'] = context
    kwargs.setdefault('graph', context.task_graph(workflow_name))
    return kwargs
