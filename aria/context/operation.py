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
Workflow and operation contexts
"""

from uuid import uuid4

from aria.logger import LoggerMixin

class OperationContext(LoggerMixin):
    """
    Context object used during operation creation and execution
    """

    def __init__(
            self,
            name,
            operation_details,
            workflow_context,
            node_instance,
            inputs=None):
        super(OperationContext, self).__init__()
        self.name = name
        self.id = str(uuid4())
        self.operation_details = operation_details
        self.workflow_context = workflow_context
        self.node_instance = node_instance
        self.inputs = inputs or {}

    def __repr__(self):
        details = ', '.join(
            '{0}={1}'.format(key, value)
            for key, value in self.operation_details.items())
        return '{name}({0})'.format(details, name=self.name)

    def __getattr__(self, attr):
        try:
            return getattr(self.workflow_context, attr)
        except AttributeError:
            return super(OperationContext, self).__getattribute__(attr)

    @property
    def operation(self):
        """
        The model operation
        """
        return self.storage.operation.get(self.id)

    @operation.setter
    def operation(self, value):
        """
        Store the operation in the model storage
        """
        self.storage.operation.store(value)
