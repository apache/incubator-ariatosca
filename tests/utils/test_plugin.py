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

import os

import pytest

from aria import application_model_storage
from aria.orchestrator import exceptions
from aria.orchestrator import plugin
from aria.utils.plugin import create as create_plugin
from aria.storage.sql_mapi import SQLAlchemyModelAPI

from .. import storage


PACKAGE_NAME = 'mock-plugin'
PACKAGE_VERSION = '100'


class TestPluginManager(object):

    def test_install(self, plugin_manager, mock_plugin, model, plugins_dir):
        plugin = plugin_manager.install(mock_plugin)
        assert plugin.package_name == PACKAGE_NAME
        assert plugin.package_version == PACKAGE_VERSION
        assert plugin == model.plugin.get(plugin.id)
        plugin_prefix = os.path.join(plugins_dir, '{0}-{1}'.format(PACKAGE_NAME, PACKAGE_VERSION))
        assert os.path.isdir(plugin_prefix)
        assert plugin_prefix == plugin_manager.get_plugin_prefix(plugin)

    def test_install_already_exits(self, plugin_manager, mock_plugin):
        plugin_manager.install(mock_plugin)
        with pytest.raises(exceptions.PluginAlreadyExistsError):
            plugin_manager.install(mock_plugin)


@pytest.fixture
def model():
    api_kwargs = storage.get_sqlite_api_kwargs()
    model = application_model_storage(SQLAlchemyModelAPI, api_kwargs=api_kwargs)
    yield model
    storage.release_sqlite_storage(model)


@pytest.fixture
def plugins_dir(tmpdir):
    result = tmpdir.join('plugins')
    result.mkdir()
    return str(result)


@pytest.fixture
def plugin_manager(model, plugins_dir):
    return plugin.PluginManager(model=model, plugins_dir=plugins_dir)


@pytest.fixture
def mock_plugin(tmpdir):
    source_dir = tmpdir.join('mock_plugin')
    source_dir.mkdir()
    setup_py = source_dir.join('setup.py')
    setup_py.write('from setuptools import setup; setup(name="{0}", version="{1}")'
                   .format(PACKAGE_NAME, PACKAGE_VERSION))
    return create_plugin(source=str(source_dir), destination_dir=str(tmpdir))
