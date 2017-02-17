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
Workflow runner
"""

import tempfile
import os

from .context.workflow import WorkflowContext
from .workflows.core.engine import Engine
from .workflows.executor.thread import ThreadExecutor
from ..storage import (
    sql_mapi,
    filesystem_rapi,
)
from .. import (
    application_model_storage,
    application_resource_storage
)


class Runner(object):
    """
    Runs workflows on a deployment. By default uses temporary storage (either on disk or in memory)
    but can also be used with existing storage.

    Handles the initialization of the storage engine and provides convenience methods for
    sub-classes to create tasks.

    :param path: path to Sqlite database file; use '' (the default) to use a temporary file,
                 and None to use an in-memory database
    :type path: string
    """

    def __init__(self, workflow_name, workflow_fn, inputs, initialize_model_storage_fn,
                 service_id_fn, storage_path='', is_storage_temporary=True):
        if storage_path == '':
            # Temporary file storage
            the_file, storage_path = tempfile.mkstemp(suffix='.db', prefix='aria-')
            os.close(the_file)

        self._storage_path = storage_path
        self._storage_dir = os.path.dirname(storage_path)
        self._storage_name = os.path.basename(storage_path)
        self._is_storage_temporary = is_storage_temporary

        workflow_context = self.create_workflow_context(workflow_name, initialize_model_storage_fn,
                                                        service_id_fn)

        tasks_graph = workflow_fn(ctx=workflow_context, **inputs)

        self._engine = Engine(
            executor=ThreadExecutor(),
            workflow_context=workflow_context,
            tasks_graph=tasks_graph)

    def run(self):
        try:
            self._engine.execute()
        finally:
            self.cleanup()

    def create_workflow_context(self,
                                workflow_name,
                                initialize_model_storage_fn,
                                service_id_fn):
        self.cleanup()
        model_storage = application_model_storage(
            sql_mapi.SQLAlchemyModelAPI,
            initiator_kwargs=dict(base_dir=self._storage_dir, filename=self._storage_name))
        if initialize_model_storage_fn:
            initialize_model_storage_fn(model_storage)
        resource_storage = application_resource_storage(
            filesystem_rapi.FileSystemResourceAPI, api_kwargs=dict(directory='.'))
        return WorkflowContext(
            name=workflow_name,
            model_storage=model_storage,
            resource_storage=resource_storage,
            service_id=service_id_fn(),
            workflow_name=self.__class__.__name__,
            task_max_attempts=1,
            task_retry_interval=1)

    def cleanup(self):
        if (self._is_storage_temporary and (self._storage_path is not None) and
                os.path.isfile(self._storage_path)):
            os.remove(self._storage_path)
