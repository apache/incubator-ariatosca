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

import os
import sys
import types

try:
    import ruamel                                                               # pylint: disable=unused-import
except ImportError:
    if sys.version_info[0] > 2:
        raise

    # Traverse all of the site-packages and try to load ruamel.
    for packages_dir in sys.path:
        ruamel_path = os.path.join(packages_dir, 'ruamel')
        if not os.path.exists(ruamel_path):
            continue

        # If the top dir has an __init__.py file, the loading should have
        # succeeded automatically
        if os.path.exists(os.path.join(ruamel_path, '__init__.py')):
            raise

        # Dynamically create mapping to the ruamel package
        ruamel_module = sys.modules.setdefault(
            'ruamel',
            types.ModuleType('ruamel')
        )
        # add path to the mapped package
        ruamel_module.__dict__.setdefault('__path__', []).append(ruamel_path)

finally:
    from ruamel import yaml                                                     # pylint: disable=unused-import
