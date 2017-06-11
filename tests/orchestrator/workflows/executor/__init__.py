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
import logging
import uuid
from contextlib import contextmanager

import aria
from aria.modeling import models


class MockContext(object):

    def __init__(self, storage, task_kwargs=None):
        self.logger = logging.getLogger('mock_logger')
        self._task_kwargs = task_kwargs or {}
        self._storage = storage
        self.task = MockTask(storage, **task_kwargs)
        self.states = []
        self.exception = None

    @property
    def serialization_dict(self):
        return {
            'context_cls': self.__class__,
            'context': {
                'storage_kwargs': self._storage.serialization_dict,
                'task_kwargs': self._task_kwargs
            }
        }

    def __getattr__(self, item):
        return None

    def close(self):
        pass

    @classmethod
    def instantiate_from_dict(cls, storage_kwargs=None, task_kwargs=None):
        return cls(storage=aria.application_model_storage(**(storage_kwargs or {})),
                   task_kwargs=(task_kwargs or {}))

    @property
    @contextmanager
    def persist_changes(self):
        yield


class MockActor(object):
    def __init__(self):
        self.name = 'actor_name'


class MockTask(object):

    INFINITE_RETRIES = models.Task.INFINITE_RETRIES

    def __init__(self, model, function, arguments=None, plugin_fk=None):
        self.function = self.name = function
        self.plugin_fk = plugin_fk
        self.arguments = arguments or {}
        self.states = []
        self.exception = None
        self.id = str(uuid.uuid4())
        self.logger = logging.getLogger()
        self.attempts_count = 1
        self.max_attempts = 1
        self.ignore_failure = False
        self.interface_name = 'interface_name'
        self.operation_name = 'operation_name'
        self.actor = MockActor()
        self.node = self.actor
        self.model = model

        for state in models.Task.STATES:
            setattr(self, state.upper(), state)

    @property
    def plugin(self):
        return self.model.plugin.get(self.plugin_fk) if self.plugin_fk else None
