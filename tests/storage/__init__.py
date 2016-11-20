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
from collections import namedtuple
from tempfile import mkdtemp
from shutil import rmtree

from aria.storage import ModelDriver, PointerField, IterField, _generate_lower_name, exceptions


_Pointer = namedtuple('_Pointer', 'name, is_iter')


class InMemoryModelDriver(ModelDriver):
    def __init__(self, **kwargs):
        super(InMemoryModelDriver, self).__init__(**kwargs)
        self.storage = {}
        self.pointers = {}
        self.model_cls = {}

    def create(self, name, model_cls, *args, **kwargs):
        self.storage[name] = {}
        self.pointers[name] = {}
        self.model_cls[name] = model_cls
        self._create_pointer_mapping(name=name, model_cls=model_cls)

    def get(self, name, entry_id, **kwargs):
        base_entry = self.storage[name][entry_id].copy()
        base_entry.update(self._get_pointers(name, base_entry))
        return self.model_cls[name](**base_entry.copy())

    def _get_pointers(self, name, base_entry, **kwargs):
        pointers = {}
        for field, field_cls in self.pointers[name].items():
            pointer_storage_name = _generate_lower_name(field_cls.type)
            if field.is_iter:
                pointers[field.name] = [self.storage[pointer_storage_name][pointer_id]
                                        for pointer_id in base_entry[field.name]
                                        if pointer_id]
            elif base_entry[field.name]:
                pointers[field.name] = self.storage[pointer_storage_name][base_entry[field.name]]
        return pointers

    def store(self, name, entry_id, entry, **kwargs):
        pointers = self._store_pointers(name, entry)
        dict_entry = entry.fields_dict
        dict_entry.update(pointers)
        self.storage[name][entry_id] = dict_entry

    def _store_pointers(self, name, base_entry, **kwargs):
        pointers = {}
        for field, field_cls in self.pointers[name].items():
            pointer_storage_name = _generate_lower_name(field_cls.type)
            entry_field_value = getattr(base_entry, field.name)
            if field.is_iter:
                pointers[field.name] = []
                for iter_entry_field in entry_field_value:
                    pointers[field.name].append(iter_entry_field.id)
                    self.storage[pointer_storage_name][iter_entry_field.id] = \
                        iter_entry_field.fields_dict
            else:
                pointers[field.name] = entry_field_value.id
                self.storage[pointer_storage_name][entry_field_value.id] = \
                    entry_field_value.fields_dict
        return pointers.copy()

    def delete(self, name, entry_id, **kwargs):
        base_entry = self.storage[name].pop(entry_id)
        self._delete_pointers(name, base_entry)

    def _delete_pointers(self, name, base_entry, **kwargs):
        for field, field_cls in self.pointers[name].items():
            pointer_storage_name = _generate_lower_name(field_cls.type)
            if field.is_iter:
                for iter_entry in base_entry[field.name]:
                    del self.storage[pointer_storage_name][iter_entry]['id']
            else:
                del self.storage[pointer_storage_name]

    def iter(self, name, **kwargs):
        for base_entry in self.storage[name].values():
            base_entry = base_entry.copy()
            base_entry.update(self._get_pointers(name, base_entry, **kwargs))
            yield self.model_cls[name](**base_entry.copy())

    def update(self, name, entry_id, **kwargs):
        self.storage[name][entry_id].update(**kwargs)

    def _create_pointer_mapping(self, name, model_cls, **kwargs):
        for field_name, field_cls in vars(model_cls).items():
            if not(isinstance(field_cls, PointerField) and field_cls.type):
                continue
            pointer_name = _Pointer(field_name, is_iter=isinstance(field_cls, IterField))
            pointer_storage_name = _generate_lower_name(field_cls.type)
            if pointer_storage_name in self.storage:
                raise exceptions.StorageError("{0} is not yet in storage"
                                              .format(pointer_storage_name))
            self.pointers[name][pointer_name] = field_cls


class TestFileSystem(object):

    def setup_method(self):
        self.path = mkdtemp('{0}'.format(self.__class__.__name__))

    def teardown_method(self):
        rmtree(self.path)
