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


class BaseTask(object):

    def __init__(self, id, name, context):
        self.id = id
        self.name = name
        self.context = context


class StartWorkflowTask(BaseTask):
    pass


class EndWorkflowTask(BaseTask):
    pass


class StartSubWorkflowTask(BaseTask):
    pass


class EndSubWorkflowTask(BaseTask):
    pass


class OperationTask(BaseTask):
    def __init__(self, *args, **kwargs):
        super(OperationTask, self).__init__(*args, **kwargs)
        self._create_operation_in_storage()

    def _create_operation_in_storage(self):
        Operation = self.context.storage.operation.model_cls
        operation = Operation(
            id=self.context.id,
            execution_id=self.context.execution_id,
            max_retries=self.context.parameters.get('max_retries', 1),
            status=Operation.PENDING,
        )
        self.context.operation = operation

    def __getattr__(self, attr):
        try:
            return getattr(self.context, attr)
        except AttributeError:
            return super(OperationTask, self).__getattribute__(attr)

