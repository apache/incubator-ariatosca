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

import pkgutil

try:
    import pkg_resources
except ImportError:
    pkg_resources = None

from .VERSION import version as __version__

from .orchestrator.decorators import workflow, operation
from . import (
    extension,
    utils,
    parser,
    storage,
    modeling,
    orchestrator,
    cli
)
__all__ = (
    '__version__',
    'workflow',
    'operation',
)


def install_aria_extensions():
    """
    Iterates all Python packages with names beginning with :code:`aria_extension_` and all
    :code:`aria_extension` entry points and loads them.
    It then invokes all registered extension functions.
    """
    for loader, module_name, _ in pkgutil.iter_modules():
        if module_name.startswith('aria_extension_'):
            loader.find_module(module_name).load_module(module_name)
    if pkg_resources:
        for entry_point in pkg_resources.iter_entry_points(group='aria_extension'):
            entry_point.load()
    extension.init()


def application_model_storage(api, api_kwargs=None, initiator=None, initiator_kwargs=None):
    """
    Initiate model storage
    """
    models_to_register = [
        modeling.models.ServiceTemplate,
        modeling.models.NodeTemplate,
        modeling.models.GroupTemplate,
        modeling.models.PolicyTemplate,
        modeling.models.SubstitutionTemplate,
        modeling.models.SubstitutionTemplateMapping,
        modeling.models.RequirementTemplate,
        modeling.models.RelationshipTemplate,
        modeling.models.CapabilityTemplate,
        modeling.models.InterfaceTemplate,
        modeling.models.OperationTemplate,
        modeling.models.ArtifactTemplate,

        modeling.models.Parameter,
        modeling.models.Metadata,

        modeling.models.Service,
        modeling.models.Node,
        modeling.models.Group,
        modeling.models.Policy,
        modeling.models.SubstitutionMapping,
        modeling.models.Substitution,
        modeling.models.Relationship,
        modeling.models.Capability,
        modeling.models.Interface,
        modeling.models.Operation,
        modeling.models.Artifact,

        modeling.models.Execution,
        modeling.models.ServiceUpdate,
        modeling.models.ServiceUpdateStep,
        modeling.models.ServiceModification,
        modeling.models.Plugin,
        modeling.models.Task
    ]
    return storage.ModelStorage(api_cls=api,
                                api_kwargs=api_kwargs,
                                items=models_to_register,
                                initiator=initiator,
                                initiator_kwargs=initiator_kwargs or {})


def application_resource_storage(api, api_kwargs=None, initiator=None, initiator_kwargs=None):
    """
    Initiate resource storage
    """

    return storage.ResourceStorage(api_cls=api,
                                   api_kwargs=api_kwargs,
                                   items=['blueprint', 'deployment', 'plugin'],
                                   initiator=initiator,
                                   initiator_kwargs=initiator_kwargs)
