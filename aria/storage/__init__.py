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
Aria's storage Sub-Package
Path: aria.storage

Storage package is a generic abstraction over different storage types.
We define this abstraction with the following components:

1. storage: simple api to use
2. driver: implementation of the database client api.
3. model: defines the structure of the table/document.
4. field: defines a field/item in the model.

API:
    * application_storage_factory - function, default Aria storage factory.
    * Storage - class, simple storage api.
    * models - module, default Aria standard models.
    * structures - module, default Aria structures - holds the base model,
                   and different fields types.
    * Model - class, abstract model implementation.
    * Field - class, base field implementation.
    * IterField - class, base iterable field implementation.
    * drivers - module, a pool of Aria standard drivers.
    * StorageDriver - class, abstract model implementation.
"""
# todo: rewrite the above package documentation
# (something like explaning the two types of storage - models and resources)

from collections import namedtuple

from .structures import Storage, Field, Model, IterField, PointerField
from .drivers import (
    ModelDriver,
    ResourceDriver,
    FileSystemResourceDriver,
    FileSystemModelDriver,
)
from . import models

__all__ = (
    'ModelStorage',
    'ResourceStorage',
    'FileSystemModelDriver',
    'models',
    'structures',
    'Field',
    'IterField',
    'PointerField',
    'Model',
    'drivers',
    'ModelDriver',
    'ResourceDriver',
    'FileSystemResourceDriver',
)
# todo: think about package output api's...
# todo: in all drivers name => entry_type
# todo: change in documentation str => basestring


class ModelStorage(Storage):
    def __init__(self, driver, models=(), **kwargs):
        """
        Simple storage client api for Aria applications.
        The storage instance defines the tables/documents/code api.

        :param ModelDriver driver: model storage driver.
        :param models: the models to register.
        """
        assert isinstance(driver, ModelDriver)
        super(ModelStorage, self).__init__(driver, models, **kwargs)

    def __getattr__(self, table):
        """
        getattr is a shortcut to simple api

        for Example:
        >> storage = ModelStorage(driver=FileSystemModelDriver('/tmp'))
        >> node_table = storage.node
        >> for node in node_table:
        >>     print node

        :param str table: table name to get
        :return: a storage object that mapped to the table name
        """
        return super(ModelStorage, self).__getattr__(table)

    def register(self, model_cls):
        # todo: add documentation
        model_name = generate_lower_name(model_cls)
        model_api = _ModelApi(model_name, self.driver, model_cls)
        self.registered[model_name] = model_api

        for pointer, pointer_schema_register in model_api.pointer_mapping.items():
            model_cls = pointer_schema_register.model_cls
            self.register(model_cls)

_Pointer = namedtuple('_Pointer', 'name, is_iter')


class _ModelApi(object):
    def __init__(self, name, driver, model_cls):
        """
        Managing the model in the storage, using the driver.

        :param basestring name: the name of the model.
        :param ModelDriver driver: the driver which supports this model in the storage.
        :param Model model_cls: table/document class model.
        """
        assert isinstance(driver, ModelDriver)
        assert issubclass(model_cls, Model)
        self.name = name
        self.driver = driver
        self.model_cls = model_cls
        self.pointer_mapping = {}
        self._setup_pointers_mapping()

    def _setup_pointers_mapping(self):
        for field_name, field_cls in vars(self.model_cls).items():
            if not(isinstance(field_cls, PointerField) and field_cls.type):
                continue
            pointer_key = _Pointer(field_name, is_iter=isinstance(field_cls, IterField))
            self.pointer_mapping[pointer_key] = self.__class__(
                name=generate_lower_name(field_cls.type),
                driver=self.driver,
                model_cls=field_cls.type)

    def __iter__(self):
        return self.iter()

    def __repr__(self):
        return '{self.name}(driver={self.driver}, model={self.model_cls})'.format(self=self)

    def create(self):
        """
        Creates the model in the storage.
        """
        with self.driver as connection:
            connection.create(self.name)

    def get(self, entry_id, **kwargs):
        """
        Getter for the model from the storage.

        :param basestring entry_id: the id of the table/document.
        :return: model instance
        :rtype: Model
        """
        with self.driver as connection:
            data = connection.get(
                name=self.name,
                entry_id=entry_id,
                **kwargs)
            data.update(self._get_pointers(data, **kwargs))
        return self.model_cls(**data)

    def store(self, entry, **kwargs):
        """
        Setter for the model in the storage.

        :param Model entry: the table/document to store.
        """
        assert isinstance(entry, self.model_cls)
        with self.driver as connection:
            data = entry.fields_dict
            data.update(self._store_pointers(data, **kwargs))
            connection.store(
                name=self.name,
                entry_id=entry.id,
                entry=data,
                **kwargs)

    def delete(self, entry_id, **kwargs):
        """
        Delete the model from storage.

        :param basestring entry_id: id of the entity to delete from storage.
        """
        entry = self.get(entry_id)
        with self.driver as connection:
            self._delete_pointers(entry, **kwargs)
            connection.delete(
                name=self.name,
                entry_id=entry_id,
                **kwargs)

    def iter(self, **kwargs):
        """
        Generator over the entries of model in storage.
        """
        with self.driver as connection:
            for data in connection.iter(name=self.name, **kwargs):
                data.update(self._get_pointers(data, **kwargs))
                yield self.model_cls(**data)

    def update(self, entry_id, **kwargs):
        """
        Updates and entry in storage.

        :param str entry_id: the id of the table/document.
        :param kwargs: the fields to update.
        :return:
        """
        with self.driver as connection:
            connection.update(
                name=self.name,
                entry_id=entry_id,
                **kwargs
            )

    def _get_pointers(self, data, **kwargs):
        pointers = {}
        for field, schema in self.pointer_mapping.items():
            if field.is_iter:
                pointers[field.name] = [
                    schema.get(entry_id=pointer_id, **kwargs)
                    for pointer_id in data[field.name]
                    if pointer_id]
            elif data[field.name]:
                pointers[field.name] = schema.get(entry_id=data[field.name], **kwargs)
        return pointers

    def _store_pointers(self, data, **kwargs):
        pointers = {}
        for field, model_api in self.pointer_mapping.items():
            if field.is_iter:
                pointers[field.name] = []
                for iter_entity in data[field.name]:
                    pointers[field.name].append(iter_entity.id)
                    model_api.store(iter_entity, **kwargs)
            else:
                pointers[field.name] = data[field.name].id
                model_api.store(data[field.name], **kwargs)
        return pointers

    def _delete_pointers(self, entry, **kwargs):
        for field, schema in self.pointer_mapping.items():
            if field.is_iter:
                for iter_entry in getattr(entry, field.name):
                    schema.delete(iter_entry.id, **kwargs)
            else:
                schema.delete(getattr(entry, field.name).id, **kwargs)


class ResourceApi(object):
    def __init__(self, driver, resource_name):
        """
        Managing the resources in the storage, using the driver.

        :param ResourceDriver driver: the driver which supports this model in the storage.
        :param basestring resource_name: the type of the entry this resourceAPI manages.
        """
        assert isinstance(driver, ResourceDriver)
        self.driver = driver
        self.resource_name = resource_name

    def __repr__(self):
        return '{name}(driver={self.driver}, resource={self.resource_name})'.format(
            name=self.__class__.__name__, self=self)

    def create(self):
        """
        Create the resource dir in the storage.
        """
        with self.driver as connection:
            connection.create(self.resource_name)

    def data(self, entry_id, path=None, **kwargs):
        """
        Retrieve the content of a storage resource.

        :param basestring entry_id: the id of the entry.
        :param basestring path: path of the resource on the storage.
        :param kwargs: resources to be passed to the driver..
        :return the content of a single file:
        """
        with self.driver as connection:
            return connection.data(
                entry_type=self.resource_name,
                entry_id=entry_id,
                path=path,
                **kwargs)

    def download(self, entry_id, destination, path=None, **kwargs):
        """
        Download a file/dir from the resource storage.

        :param basestring entry_id: the id of the entry.
        :param basestring destination: the destination of the file/dir.
        :param basestring path: path of the resource on the storage.
        """
        with self.driver as connection:
            connection.download(
                entry_type=self.resource_name,
                entry_id=entry_id,
                destination=destination,
                path=path,
                **kwargs)

    def upload(self, entry_id, source, path=None, **kwargs):
        """
        Upload a file/dir from the resource storage.

        :param basestring entry_id: the id of the entry.
        :param basestring source: the source path of the file to upload.
        :param basestring path: the destination of the file, relative to the root dir
                                of the resource
        """
        with self.driver as connection:
            connection.upload(
                entry_type=self.resource_name,
                entry_id=entry_id,
                source=source,
                path=path,
                **kwargs)


def generate_lower_name(model_cls):
    """
    Generates the name of the class from the class object. e.g. SomeClass -> some_class
    :param model_cls: the class to evaluate.
    :return: lower name
    :rtype: basestring
    """
    return ''.join(
        character if character.islower() else '_{0}'.format(character.lower())
        for character in model_cls.__name__)[1:]


class ResourceStorage(Storage):
    def __init__(self, driver, resources=(), **kwargs):
        """
        Simple storage client api for Aria applications.
        The storage instance defines the tables/documents/code api.

        :param ResourceDriver driver: resource storage driver
        :param resources: the resources to register.
        """
        assert isinstance(driver, ResourceDriver)
        super(ResourceStorage, self).__init__(driver, resources, **kwargs)

    def register(self, resource):
        self.registered[resource] = ResourceApi(self.driver, resource_name=resource)

    def __getattr__(self, resource):
        """
        getattr is a shortcut to simple api

        for Example:
        >> storage = ResourceStorage(driver=FileSystemResourceDriver('/tmp'))
        >> blueprint_resources = storage.blueprint
        >> blueprint_resources.download(blueprint_id, destination='~/blueprint/')

        :param str resource: resource name to download
        :return: a storage object that mapped to the resource name
        :rtype: ResourceApi
        """
        return super(ResourceStorage, self).__getattr__(resource)
