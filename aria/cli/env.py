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
Environment (private)
"""

import os
import shutil
from aria.type_definition_manager import TypeDefinitionManager
from .config import config
from .logger import Logging
from .. import (application_model_storage, application_resource_storage)
from ..orchestrator.plugin import PluginManager
from ..storage.sql_mapi import SQLAlchemyModelAPI
from ..storage.filesystem_rapi import FileSystemResourceAPI


ARIA_DEFAULT_WORKDIR_NAME = '.aria'


class _Environment(object):

    def __init__(self, workdir):

        self._workdir = workdir
        self._init_workdir()

        self._config = config.CliConfig.create_config(workdir)
        self._logging = Logging(self._config)

        self._model_storage_dir = os.path.join(workdir, 'models')
        self._resource_storage_dir = os.path.join(workdir, 'resources')
        self._plugins_dir = os.path.join(workdir, 'plugins')
        self._type_definitions_dir = os.path.join(workdir, 'type_definitions')

        # initialized lazily
        self._model_storage = None
        self._resource_storage = None
        self._plugin_manager = None
        self._type_definition_manager = None

    @property
    def workdir(self):
        return self._workdir

    @property
    def config(self):
        return self._config

    @property
    def logging(self):
        return self._logging

    @property
    def model_storage(self):
        if not self._model_storage:
            self._model_storage = self._init_sqlite_model_storage()
        return self._model_storage

    @property
    def resource_storage(self):
        if not self._resource_storage:
            self._resource_storage = self._init_fs_resource_storage()
        return self._resource_storage

    @property
    def plugin_manager(self):
        if not self._plugin_manager:
            self._plugin_manager = self._init_plugin_manager()
        return self._plugin_manager

    @property
    def type_definition_manager(self):
        if not self._type_definition_manager:
            self._type_definition_manager = self._init_type_definition_manager()
        return self._type_definition_manager

    def reset(self, reset_config):
        if reset_config:
            shutil.rmtree(self._workdir)
        else:
            _, dirs, files = next(os.walk(self._workdir))
            files.remove(config.CONFIG_FILE_NAME)

            for dir_ in dirs:
                shutil.rmtree(os.path.join(self._workdir, dir_))
            for file_ in files:
                os.remove(os.path.join(self._workdir, file_))

    def _init_workdir(self):
        if not os.path.exists(self._workdir):
            os.makedirs(self._workdir)

    def _init_sqlite_model_storage(self):
        if not os.path.exists(self._model_storage_dir):
            os.makedirs(self._model_storage_dir)

        initiator_kwargs = dict(base_dir=self._model_storage_dir)
        return application_model_storage(
            SQLAlchemyModelAPI,
            initiator_kwargs=initiator_kwargs)

    def _init_fs_resource_storage(self):
        if not os.path.exists(self._resource_storage_dir):
            os.makedirs(self._resource_storage_dir)

        fs_kwargs = dict(directory=self._resource_storage_dir)
        return application_resource_storage(
            FileSystemResourceAPI,
            api_kwargs=fs_kwargs)

    def _init_plugin_manager(self):
        if not os.path.exists(self._plugins_dir):
            os.makedirs(self._plugins_dir)

        return PluginManager(self.model_storage, self._plugins_dir)

    def _init_type_definition_manager(self):
        if not os.path.exists(self._type_definitions_dir):
            os.makedirs(self._type_definitions_dir)

        return TypeDefinitionManager(self.model_storage, self._type_definitions_dir)

env = _Environment(os.path.join(
    os.environ.get('ARIA_WORKDIR', os.path.expanduser('~')), ARIA_DEFAULT_WORKDIR_NAME))

logger = env.logging.logger
