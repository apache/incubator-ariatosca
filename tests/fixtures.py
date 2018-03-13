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

import shutil

import pytest

from aria import (
    application_model_storage,
    application_resource_storage
)
from aria import type_definition_manager as type_definition
from aria.orchestrator import plugin
from aria.storage import (
    sql_mapi,
    filesystem_rapi
)

from . import storage


@pytest.fixture
def inmemory_model():
    model = application_model_storage(sql_mapi.SQLAlchemyModelAPI,
                                      initiator=storage.init_inmemory_model_storage)
    yield model
    storage.release_sqlite_storage(model)


@pytest.fixture
def fs_model(tmpdir):
    result = application_model_storage(sql_mapi.SQLAlchemyModelAPI,
                                       initiator_kwargs=dict(base_dir=str(tmpdir)),
                                       initiator=sql_mapi.init_storage)
    yield result
    storage.release_sqlite_storage(result)


@pytest.fixture
def resource_storage(tmpdir):
    result = tmpdir.join('resources')
    result.mkdir()
    resource_storage = application_resource_storage(
        filesystem_rapi.FileSystemResourceAPI,
        api_kwargs=dict(directory=str(result)))
    yield resource_storage
    shutil.rmtree(str(result))


@pytest.fixture
def plugins_dir(tmpdir):
    result = tmpdir.join('plugins')
    result.mkdir()
    return str(result)


@pytest.fixture
def plugin_manager(model, plugins_dir):
    return plugin.PluginManager(model=model, plugins_dir=plugins_dir)


@pytest.fixture
def type_definitions_dir(tmpdir):
    result = tmpdir.join('type_definitions')
    result.mkdir()
    return str(result)


@pytest.fixture
def type_definition_manager(model, type_definitions_dir):
    return type_definition.\
        TypeDefinitionManager(model_storage=model, type_definitions_dir=type_definitions_dir)
