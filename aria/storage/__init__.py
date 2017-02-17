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
ARIA's storage Sub-Package
Path: aria.storage

Storage package is a generic abstraction over different storage types.
We define this abstraction with the following components:

1. storage: simple mapi to use
2. driver: implementation of the database client mapi.
3. model: defines the structure of the table/document.
4. field: defines a field/item in the model.

API:
    * application_storage_factory - function, default ARIA storage factory.
    * Storage - class, simple storage mapi.
    * models - module, default ARIA standard models.
    * structures - module, default ARIA structures - holds the base model,
                   and different fields types.
    * Model - class, abstract model implementation.
    * Field - class, base field implementation.
    * IterField - class, base iterable field implementation.
    * drivers - module, a pool of ARIA standard drivers.
    * StorageDriver - class, abstract model implementation.
"""
from .core import (
    Storage,
    ModelStorage,
    ResourceStorage,
)
from . import (
    exceptions,
    api,
    core,
    filesystem_rapi,
    sql_mapi,
)

__all__ = (
    'exceptions',
    'Storage',
    'ModelStorage',
    'ResourceStorage',
    'filesystem_rapi',
    'sql_mapi',
    'api',
)
