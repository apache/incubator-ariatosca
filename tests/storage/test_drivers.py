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
import pytest

from aria.storage.drivers import FileSystemModelDriver, Driver, ModelDriver, ResourceDriver
from aria.storage.exceptions import StorageError

from . import InMemoryModelDriver, TestFileSystem


def test_base_storage_driver():
    driver = Driver()
    driver.connect()
    driver.disconnect()
    driver.create('name')
    with driver as connection:
        assert driver is connection
    with pytest.raises(StorageError):
        with driver:
            raise StorageError()


def test_model_base_driver():
    driver = ModelDriver()
    with pytest.raises(NotImplementedError):
        driver.get('name', 'id')
    with pytest.raises(NotImplementedError):
        driver.store('name', entry={}, entry_id=None)
    with pytest.raises(NotImplementedError):
        driver.update('name', 'id', update_field=1)
    with pytest.raises(NotImplementedError):
        driver.delete('name', 'id')
    with pytest.raises(NotImplementedError):
        driver.iter('name')


def test_resource_base_driver():
    driver = ResourceDriver()
    with pytest.raises(NotImplementedError):
        driver.download('name', 'id', destination='dest')
    with pytest.raises(NotImplementedError):
        driver.upload('name', 'id', source='')
    with pytest.raises(NotImplementedError):
        driver.data('name', 'id')


def test_custom_driver():
    entry_dict = {
        'id': 'entry_id',
        'entry_value': 'entry_value'
    }

    with InMemoryModelDriver() as driver:
        driver.create('entry')
        assert driver.storage['entry'] == {}

        driver.store(name='entry', entry=entry_dict, entry_id=entry_dict['id'])
        assert driver.get(name='entry', entry_id='entry_id') == entry_dict

        assert list(node for node in driver.iter('entry')) == [entry_dict]

        driver.update(name='entry', entry_id=entry_dict['id'], entry_value='new_value')
        assert driver.get(name='entry', entry_id='entry_id') == entry_dict

        driver.delete(name='entry', entry_id='entry_id')

        with pytest.raises(KeyError):
            driver.get(name='entry', entry_id='entry_id')


class TestFileSystemDriver(TestFileSystem):

    def setup_method(self):
        super(TestFileSystemDriver, self).setup_method()
        self.driver = FileSystemModelDriver(directory=self.path)

    def test_name(self):
        assert repr(self.driver) == (
            'FileSystemModelDriver(directory={self.path})'.format(self=self))

    def test_create(self):
        self.driver.create(name='node')
        assert os.path.exists(os.path.join(self.path, 'node'))

    def test_store(self):
        self.test_create()
        self.driver.store(name='node', entry_id='test_id', entry={'test': 'test'})
        assert os.path.exists(os.path.join(self.path, 'node', 'test_id'))

    def test_update(self):
        self.test_store()
        self.driver.update(name='node', entry_id='test_id', test='updated_test')
        entry = self.driver.get(name='node', entry_id='test_id')
        assert entry == {'test': 'updated_test'}

    def test_get(self):
        self.test_store()
        entry = self.driver.get(name='node', entry_id='test_id')
        assert entry == {'test': 'test'}

    def test_delete(self):
        self.test_store()
        self.driver.delete(name='node', entry_id='test_id')
        assert not os.path.exists(os.path.join(self.path, 'node', 'test_id'))

    def test_iter(self):
        self.test_create()
        entries = [
            {'test': 'test0'},
            {'test': 'test1'},
            {'test': 'test2'},
            {'test': 'test3'},
            {'test': 'test4'},
        ]
        for entry_id, entry in enumerate(entries):
            self.driver.store('node', str(entry_id), entry)

        for entry in self.driver.iter('node'):
            entries.pop(entries.index(entry))

        assert not entries
