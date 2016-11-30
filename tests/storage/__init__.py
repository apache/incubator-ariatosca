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

from tempfile import mkdtemp
from shutil import rmtree

from aria.storage import ModelDriver


class InMemoryModelDriver(ModelDriver):
    def __init__(self, **kwargs):
        super(InMemoryModelDriver, self).__init__(**kwargs)
        self.storage = {}

    def create(self, name, *args, **kwargs):
        self.storage[name] = {}

    def get(self, name, entry_id, **kwargs):
        return self.storage[name][entry_id].copy()

    def store(self, name, entry_id, entry, **kwargs):
        self.storage[name][entry_id] = entry

    def delete(self, name, entry_id, **kwargs):
        self.storage[name].pop(entry_id)

    def iter(self, name, **kwargs):
        for item in self.storage[name].itervalues():
            yield item.copy()

    def update(self, name, entry_id, **kwargs):
        self.storage[name][entry_id].update(**kwargs)


class TestFileSystem(object):

    def setup_method(self):
        self.path = mkdtemp('{0}'.format(self.__class__.__name__))

    def teardown_method(self):
        rmtree(self.path, ignore_errors=True)
