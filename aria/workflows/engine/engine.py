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

import time
from datetime import datetime

from contextlib import contextmanager
from networkx import DiGraph

from aria.events import (
    start_workflow_signal,
    on_success_workflow_signal,
    on_failure_workflow_signal,
    start_task_signal,
    on_success_task_signal,
    on_failure_task_signal,
)
from aria.logger import LoggerMixin


class Engine(LoggerMixin):

    def __init__(self, executor, workflow_context, tasks_graph, **kwargs):
        super(Engine, self).__init__(**kwargs)
        self._workflow_context = workflow_context
        self._tasks_graph = tasks_graph
        self._execution_graph = DiGraph()
        self._executor = executor
        self._build_execution_graph(self._workflow_context, self._tasks_graph)

    def _build_execution_graph(self, workflow_context, graph):
        pass

    def execute(self):
        execution_id = self._workflow_context.execution_id
        with self._connect_signals():
            try:
                start_workflow_signal.send(self, execution_id=execution_id)
                while True:
                    for task in self._ended_tasks():
                        self._handle_ended_tasks(task)
                    for task in self._executable_tasks():
                        self._handle_executable_task(task)
                    if self._all_tasks_consumed():
                        break
                    else:
                        time.sleep(0.1)
                on_success_workflow_signal.send(self, execution_id=execution_id)
            except BaseException as e:
                on_failure_workflow_signal.send(self, execution_id=execution_id, exception=e)
                raise

    def _executable_tasks(self):
        now = time.time()
        return (task for task in self._tasks_iter()
                if task.status == task.PENDING and
                task.eta <= now and
                not self._task_has_dependencies(task))

    def _ended_tasks(self):
        return (task for task in self._tasks_iter() if task.status in task.END_STATES)

    def _task_has_dependencies(self, task):
        return len(self._execution_graph.succ.get(task.id, {})) > 0

    def _all_tasks_consumed(self):
        len(self._execution_graph.node) == 0

    def _tasks_iter(self):
        return (data['task'] for _, data in self._execution_graph.nodes_iter(data=True))

    def _get_task(self, task_id):
        return self._execution_graph.node[task_id]['task']

    def _handle_executable_task(self, task):
        self._executor.execute(task)

    def _handle_ended_tasks(self, task):
        if task.status == task.FAILED:
            raise RuntimeError('Workflow failed')
        else:
            self._execution_graph.remove_node(task.id)

    def _task_started_receiver(self, task_id, *args, **kwargs):
        task = self._get_task(task_id)
        operation_context = task.operation_context
        operation = operation_context.operation
        operation.started_at = datetime.utcnow()
        operation.status = operation.STARTED
        operation_context.operation = operation

    def _task_failed_receiver(self, task_id, *args, **kwargs):
        task = self._get_task(task_id)
        operation_context = task.operation_context
        operation = operation_context.operation
        operation.ended_at = datetime.utcnow()
        operation.status = operation.FAILED
        operation_context.operation = operation

    def _task_succeeded_receiver(self, task_id, *args, **kwargs):
        task = self._get_task(task_id)
        operation_context = task.operation_context
        operation = operation_context.operation
        operation.ended_at = datetime.utcnow()
        operation.status = operation.SUCCESS
        operation_context.operation = operation

    def _start_workflow_receiver(self, *args, **kwargs):
        Execution = self._workflow_context.storage.execution.model_cls
        execution = Execution(
            id=self._workflow_context.execution_id,
            deployment_id=self._workflow_context.deployment_id,
            workflow_id=self._workflow_context.workflow_id,
            blueprint_id=self._workflow_context.blueprint_id,
            status=Execution.PENDING,
            created_at=datetime.utcnow(),
            error='',
            parameters=self._workflow_context.parameters,
            is_system_workflow=False
        )
        self._workflow_context.execution = execution

    def _workflow_failed_receiver(self, exception, *args, **kwargs):
        execution = self._workflow_context.execution
        execution.error = str(exception)
        execution.status = execution.FAILED
        self._workflow_context.execution = execution

    def _workflow_succeeded_receiver(self, *args, **kwargs):
        execution = self._workflow_context.execution
        execution.status = execution.TERMINATED
        self._workflow_context.execution = execution

    @contextmanager
    def _connect_signals(self):
        start_workflow_signal.connect(self._start_workflow_receiver)
        on_success_workflow_signal.connect(self._workflow_succeeded_receiver)
        on_failure_workflow_signal.connect(self._workflow_failed_receiver)
        start_task_signal.connect(self._task_started_receiver)
        on_success_task_signal.connect(self._task_succeeded_receiver)
        on_failure_task_signal.connect(self._task_failed_receiver)
        try:
            yield
        finally:
            start_workflow_signal.disconnect(self._start_workflow_receiver)
            on_success_workflow_signal.disconnect(self._workflow_succeeded_receiver)
            on_failure_workflow_signal.disconnect(self._workflow_failed_receiver)
            start_task_signal.disconnect(self._task_started_receiver)
            on_success_task_signal.disconnect(self._task_succeeded_receiver)
            on_failure_task_signal.disconnect(self._task_failed_receiver)


class Task(object):

    def __init__(self, operation_context):
        self.operation_context = operation_context
        self._create_operation_in_storage()

    def _create_operation_in_storage(self):
        Operation = self.operation_context.storage.operation.model_cls
        operation = Operation(
            id=self.operation_context.id,
            execution_id=self.operation_context.execution_id,
            max_retries=self.operation_context.parameters.get('max_retries', 1),
            status=Operation.PENDING,
        )
        self.operation_context.operation = operation

    def __getattr__(self, attr):
        try:
            return getattr(self.operation_context, attr)
        except AttributeError:
            return super(Task, self).__getattribute__(attr)
