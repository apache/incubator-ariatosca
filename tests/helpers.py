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
import json

from . import ROOT_DIR
from .resources import DIR as RESOURCES_DIR


def get_example_uri(*args):
    return os.path.join(ROOT_DIR, 'examples', *args)


def get_resource_uri(*args):
    return os.path.join(RESOURCES_DIR, *args)


def get_service_template_uri(*args):
    return os.path.join(RESOURCES_DIR, 'service-templates', *args)


def get_type_definition_uri(*args):
    return os.path.join(RESOURCES_DIR, 'type-definitions', *args)


class FilesystemDataHolder(object):

    def __init__(self, path, reset=False):
        self._path = path
        if reset or not os.path.exists(self._path) or open(self._path).read() == '':
            self._dump({})

    def _load(self):
        with open(self._path) as f:
            return json.load(f)

    def _dump(self, value):
        with open(self._path, 'w') as f:
            return json.dump(value, f)

    def __contains__(self, item):
        return item in self._load()

    def __setitem__(self, key, value):
        dict_ = self._load()
        dict_[key] = value
        self._dump(dict_)

    def __getitem__(self, item):
        return self._load()[item]

    def __iter__(self):
        return iter(self._load())

    def get(self, item, default=None):
        return self._load().get(item, default)

    def setdefault(self, key, value):
        dict_ = self._load()
        return_value = dict_.setdefault(key, value)
        self._dump(dict_)
        return return_value

    def update(self, dict_=None, **kwargs):
        current_dict = self._load()
        if dict_:
            current_dict.update(dict_)
        current_dict.update(**kwargs)
        self._dump(current_dict)

    @property
    def path(self):
        return self._path
