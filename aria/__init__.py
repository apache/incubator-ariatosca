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
Aria top level package
"""

from .VERSION import version as __version__
from .storage.drivers import (
    ResourceDriver,
    ModelDriver,
    FileSystemModelDriver,
    FileSystemResourceDriver,
)
from .storage import ModelStorage, ResourceStorage, models
from .decorators import workflow, operation

__all__ = (
    '__version__',
    'workflow',
    'operation',
)

_model_storage = {}
_resource_storage = {}


def application_model_storage(driver):
    """
    Initiate model storage for the supplied storage driver
    """

    assert isinstance(driver, ModelDriver)
    if driver not in _model_storage:
        _model_storage[driver] = ModelStorage(
            driver, model_classes=[
                models.Node,
                models.NodeInstance,
                models.Plugin,
                models.Blueprint,
                models.Snapshot,
                models.Deployment,
                models.DeploymentUpdate,
                models.DeploymentModification,
                models.Execution,
                models.ProviderContext,
                models.Operation,
            ])
    return _model_storage[driver]


def application_resource_storage(driver):
    """
    Initiate resource storage for the supplied storage driver
    """
    assert isinstance(driver, ResourceDriver)
    if driver not in _resource_storage:
        _resource_storage[driver] = ResourceStorage(
            driver,
            resources=[
                'blueprint',
                'deployment',
                'plugin',
                'snapshot',
            ])
    return _resource_storage[driver]
