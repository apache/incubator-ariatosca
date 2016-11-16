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
Utility methods for dynamically loading python code
"""

import importlib


def import_fullname(name, paths=None):
    """
    Imports a variable or class based on a full name, optionally searching for it in the paths.
    """
    paths = paths or []
    if name is None:
        return None

    def do_import(name):
        if name and ('.' in name):
            module_name, name = name.rsplit('.', 1)
            return getattr(__import__(module_name, fromlist=[name], level=0), name)
        else:
            raise ImportError('import not found: %s' % name)

    try:
        return do_import(name)
    except ImportError:
        for path in paths:
            try:
                return do_import('%s.%s' % (path, name))
            except Exception as e:
                raise ImportError('cannot import %s, because %s' % (name, e))

    raise ImportError('import not found: %s' % name)


def import_modules(name):
    """
    Imports a module and all its sub-modules, recursively.
    Relies on modules defining a 'MODULES' attribute listing their sub-module names.
    """

    module = __import__(name, fromlist=['MODULES'], level=0)
    if hasattr(module, 'MODULES'):
        for module_ in module.MODULES:
            import_modules('%s.%s' % (name, module_))


# TODO merge with import_fullname
def load_attribute(attribute_path):
    """
    Dynamically load an attribute based on the path to it.
    e.g. some_package.some_module.some_attribute, will load the some_attribute from the
    some_package.some_module module
    """
    module_name, attribute_name = attribute_path.rsplit('.', 1)
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attribute_name)
    except ImportError:
        # TODO: handle
        raise
    except AttributeError:
        # TODO: handle
        raise
