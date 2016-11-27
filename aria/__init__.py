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

import sys
import pkgutil

from .VERSION import version as __version__

from .orchestrator.decorators import workflow, operation
from . import (
    utils,
    parser,
    storage,
    orchestrator,
    cli
)
__all__ = (
    '__version__',
    'workflow',
    'operation',
)

_resource_storage = {}


def install_aria_extensions():
    """
    Iterates all Python packages with names beginning with :code:`aria_extension_` and calls
    their :code:`install_aria_extension` function if they have it.
    """

    for loader, module_name, _ in pkgutil.iter_modules():
        if module_name.startswith('aria_extension_'):
            module = loader.find_module(module_name).load_module(module_name)

            if hasattr(module, 'install_aria_extension'):
                module.install_aria_extension()

            # Loading the module has contaminated sys.modules, so we'll clean it up
            del sys.modules[module_name]


def application_model_storage(api, api_kwargs=None):
    """
    Initiate model storage for the supplied storage driver
    """
    models = [
        storage.models.Plugin,
        storage.models.ProviderContext,

        storage.models.Blueprint,
        storage.models.Deployment,
        storage.models.DeploymentUpdate,
        storage.models.DeploymentUpdateStep,
        storage.models.DeploymentModification,

        storage.models.Node,
        storage.models.NodeInstance,
        storage.models.Relationship,
        storage.models.RelationshipInstance,

        storage.models.Execution,
        storage.models.Task,
    ]
    # if api not in _model_storage:
    return storage.ModelStorage(api, items=models, api_kwargs=api_kwargs or {})


def application_resource_storage(driver):
    """
    Initiate resource storage for the supplied storage driver
    """
    if driver not in _resource_storage:
        _resource_storage[driver] = storage.ResourceStorage(
            driver,
            resources=[
                'blueprint',
                'deployment',
                'plugin',
                'snapshot',
            ])
    return _resource_storage[driver]
