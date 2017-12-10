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
The ARIA root package provides entry points for extension and storage initialization.
"""


from pkgutil import iter_modules
import pkg_resources
aria_package_name = 'apache-ariatosca'
__version__ = pkg_resources.get_distribution(aria_package_name).version

from .orchestrator.decorators import (workflow, operation)                                          # pylint: disable=wrong-import-position
from . import (                                                                                     # pylint: disable=wrong-import-position
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
    'install_aria_extensions',
    'application_model_storage',
    'application_resource_storage'
)


def install_aria_extensions(strict=True):
    """
    Loads all Python packages with names beginning with ``aria_extension_`` and calls their
    ``aria_extension`` initialization entry points if they have them.

    :param strict: if ``True`` tries to load extensions while taking into account the versions
     of their dependencies, otherwise ignores versions
    :type strict: bool
    """
    for loader, module_name, _ in iter_modules():
        if module_name.startswith('aria_extension_'):
            loader.find_module(module_name).load_module(module_name)
    for entry_point in pkg_resources.iter_entry_points(group='aria_extension'):
        # It should be possible to enable non strict loading - use the package that is already
        # installed inside the environment, and forgo the version demand
        if strict:
            entry_point.load()
        else:
            entry_point.resolve()
    extension.init()


def application_model_storage(api, api_kwargs=None, initiator=None, initiator_kwargs=None,
                              models_prefix=None):
    """
    Initiate model storage.
    """
    if models_prefix:
        # The metadata is the same for all models,
        # so we're just extracting the metadata from the first model
        metadata = modeling.models.models_to_register[0].metadata
        for table in metadata.sorted_tables:
            if not table.name.startswith(models_prefix):
                table.name = models_prefix + table.name
    return storage.ModelStorage(api_cls=api,
                                api_kwargs=api_kwargs,
                                items=modeling.models.models_to_register,
                                initiator=initiator,
                                initiator_kwargs=initiator_kwargs or {})


def application_resource_storage(api, api_kwargs=None, initiator=None, initiator_kwargs=None):
    """
    Initiate resource storage.
    """

    return storage.ResourceStorage(api_cls=api,
                                   api_kwargs=api_kwargs,
                                   items=['service_template', 'service', 'plugin'],
                                   initiator=initiator,
                                   initiator_kwargs=initiator_kwargs)
