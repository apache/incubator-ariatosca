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

import sys
import pkgutil

from .exceptions import AriaException, InvalidValueError
from .specification import (DSL_SPECIFICATION, DSL_SPECIFICATION_PACKAGES, dsl_specification,
                            iter_spec)

VERSION = '0.1'


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

MODULES = (
    'consumption',
    'loading',
    'modeling',
    'presentation',
    'reading',
    'tools',
    'utils',
    'validation')

__all__ = (
    'MODULES',
    'VERSION',
    'install_aria_extensions',
    'AriaException',
    'InvalidValueError',
    'DSL_SPECIFICATION',
    'DSL_SPECIFICATION_PACKAGES',
    'dsl_specification',
    'iter_spec')
