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
ARIA top level package
"""

import sys

import pkg_resources
__version__ = pkg_resources.get_distribution('aria').version

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

if sys.version_info < (2, 7):
    # pkgutil in python2.6 has a bug where it fails to import from protected modules, which causes
    # the entire process to fail. In order to overcome this issue we use our custom iter_modules
    from .utils.imports import iter_modules
else:
    from pkgutil import iter_modules

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
    for loader, module_name, _ in iter_modules():
        if module_name.startswith('aria_extension_'):
            loader.find_module(module_name).load_module(module_name)
    for entry_point in pkg_resources.iter_entry_points(group='aria_extension'):
        entry_point.load()
    extension.init()


def application_model_storage(api, api_kwargs=None, initiator=None, initiator_kwargs=None):
    """
    Initiate model storage
    """
    return storage.ModelStorage(api_cls=api,
                                api_kwargs=api_kwargs,
                                items=modeling.models.models_to_register,
                                initiator=initiator,
                                initiator_kwargs=initiator_kwargs or {})


def application_resource_storage(api, api_kwargs=None, initiator=None, initiator_kwargs=None):
    """
    Initiate resource storage
    """

    return storage.ResourceStorage(api_cls=api,
                                   api_kwargs=api_kwargs,
                                   items=['service_template', 'service', 'plugin'],
                                   initiator=initiator,
                                   initiator_kwargs=initiator_kwargs)
