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

import platform
import tempfile
import os

from sqlalchemy import (create_engine, orm) # @UnresolvedImport
from sqlalchemy.pool import StaticPool # @UnresolvedImport

from .context.workflow import WorkflowContext
from .workflows.core.engine import Engine
from .workflows.executor.thread import ThreadExecutor
from ..storage import model
from ..storage.sql_mapi import SQLAlchemyModelAPI
from ..storage.filesystem_rapi import FileSystemResourceAPI
from .. import (application_model_storage, application_resource_storage)


SQLITE_IN_MEMORY = 'sqlite:///:memory:'


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
                 deployment_id, storage_path='', is_storage_temporary=True):
        if storage_path == '':
            # Temporary file storage
            the_file, storage_path = tempfile.mkstemp(suffix='.db', prefix='aria-')
            os.close(the_file)

        self._storage_path = storage_path
        self._is_storage_temporary = is_storage_temporary

        workflow_context = self.create_workflow_context(workflow_name, deployment_id,
                                                        initialize_model_storage_fn)

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

    def create_workflow_context(self, workflow_name, deployment_id, initialize_model_storage_fn):
        model_storage = self.create_sqlite_model_storage()
        initialize_model_storage_fn(model_storage)
        resource_storage = self.create_fs_resource_storage()
        return WorkflowContext(
            name=workflow_name,
            model_storage=model_storage,
            resource_storage=resource_storage,
            deployment_id=deployment_id,
            workflow_name=self.__class__.__name__,
            task_max_attempts=1,
            task_retry_interval=1)

    def create_sqlite_model_storage(self): # pylint: disable=no-self-use
        self.cleanup()

        # Engine
        if self._storage_path is None:
            # In memory
            # Causes serious threading problems:
            # https://gehrcke.de/2015/05/in-memory-sqlite-database-and-flask-a-threading-trap/
            sqlite_engine = create_engine(
                SQLITE_IN_MEMORY,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool)
        else:
            path_prefix = '' if 'Windows' in platform.system() else '/'
            sqlite_engine = create_engine(
                'sqlite:///%s%s' % (path_prefix, self._storage_path))

        # Models
        model.DeclarativeBase.metadata.create_all(bind=sqlite_engine) # @UndefinedVariable

        # Session
        sqlite_session_factory = orm.sessionmaker(bind=sqlite_engine)
        if self._storage_path is None:
            sqlite_session = sqlite_session_factory()
        else:
            # File-based storage only
            sqlite_session = orm.scoped_session(session_factory=sqlite_session_factory)

        # Storage
        sqlite_kwargs = dict(engine=sqlite_engine, session=sqlite_session)
        return application_model_storage(
            SQLAlchemyModelAPI,
            api_kwargs=sqlite_kwargs)

    def create_fs_resource_storage(self, directory='.'): # pylint: disable=no-self-use
        fs_kwargs = dict(directory=directory)
        return application_resource_storage(
            FileSystemResourceAPI,
            api_kwargs=fs_kwargs)

    def cleanup(self):
        if self._is_storage_temporary \
            and (self._storage_path is not None) \
            and os.path.isfile(self._storage_path):
            os.remove(self._storage_path)
