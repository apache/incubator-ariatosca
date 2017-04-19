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
import uuid
import logging
from collections import namedtuple
from contextlib import contextmanager

from aria.modeling import models


class MockTask(object):

    INFINITE_RETRIES = models.Task.INFINITE_RETRIES

    def __init__(self, implementation, inputs=None, plugin=None):
        self.implementation = self.name = implementation
        self.plugin_fk = plugin.id if plugin else None
        self.plugin = plugin or None
        self.inputs = inputs or {}
        self.states = []
        self.exception = None
        self.id = str(uuid.uuid4())
        self.logger = logging.getLogger()
        self.context = MockContext()
        self.retry_count = 0
        self.max_attempts = 1
        self.ignore_failure = False
        self.interface_name = 'interface_name'
        self.operation_name = 'operation_name'
        self.actor = namedtuple('actor', 'name')(name='actor_name')
        self.model_task = None

        for state in models.Task.STATES:
            setattr(self, state.upper(), state)

    @contextmanager
    def _update(self):
        yield self


class MockContext(object):

    def __init__(self):
        self.logger = logging.getLogger('mock_logger')
        self.task = type('SubprocessMockTask', (object, ), {'plugin': None})
        self.serialization_dict = {'context_cls': self.__class__, 'context': {}}

    def __getattr__(self, item):
        return None

    @classmethod
    def deserialize_from_dict(cls, **kwargs):
        return cls()
