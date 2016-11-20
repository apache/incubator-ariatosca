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


from .structures import Storage, Field, Model, IterField, PointerField
from .drivers import (
    ModelDriver,
    ResourceDriver,
    FileSystemResourceDriver,
    FileSystemModelDriver,
)
from . import models, exceptions

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
    """
    Managing the models storage.
    """
    def __init__(self, driver, model_classes=(), **kwargs):
        """
        Simple storage client api for Aria applications.
        The storage instance defines the tables/documents/code api.

        :param ModelDriver driver: model storage driver.
        :param model_classes: the models to register.
        """
        assert isinstance(driver, ModelDriver)
        super(ModelStorage, self).__init__(driver, model_classes, **kwargs)

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
        """
        Registers the model type in the resource storage manager.
        :param model_cls: the model to register.
        """
        model_name = _generate_lower_name(model_cls)
        model_api = _ModelApi(model_name, self._driver, model_cls)
        self._registered[model_name] = model_api


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
        self._name = name
        self._driver = driver
        self._model_cls = model_cls

    @property
    def name(self):
        return self._name

    @property
    def model_cls(self):
        return self._model_cls

    def __iter__(self):
        return self.iter()

    def __repr__(self):
        return '{self.name}(driver={self._driver}, model={self.model_cls})'.format(self=self)

    def create(self):
        """
        Creates the model in the storage.
        """
        with self._driver as connection:
            connection.create(name=self._name, model_cls=self._model_cls)

    def get(self, entry_id, **kwargs):
        """
        Getter for the model from the storage.

        :param basestring entry_id: the id of the table/document.
        :return: model instance
        :rtype: Model
        """
        with self._driver as connection:
            return connection.get(
                name=self._name,
                entry_id=entry_id,
                model_cls=self._model_cls,
                **kwargs)

    def store(self, entry, **kwargs):
        """
        Setter for the model in the storage.

        :param Model entry: the table/document to store.
        """
        assert isinstance(entry, self._model_cls)
        with self._driver as connection:
            connection.store(
                name=self._name,
                entry_id=entry.id,
                entry=entry,
                **kwargs)

    def delete(self, entry_id, **kwargs):
        """
        Delete the model from storage.

        :param basestring entry_id: id of the entity to delete from storage.
        """
        with self._driver as connection:
            connection.delete(
                name=self._name,
                entry_id=entry_id,
                **kwargs)

    def iter(self, **kwargs):
        """
        Generator over the entries of model in storage.
        """
        with self._driver as connection:
            for data in connection.iter(name=self._name, model_cls=self._model_cls, **kwargs):
                yield data

    def update(self, entry_id, **kwargs):
        """
        Updates and entry in storage.

        :param str entry_id: the id of the table/document.
        :param kwargs: the fields to update.
        :return:
        """
        with self._driver as connection:
            connection.update(
                name=self._name,
                entry_id=entry_id,
                **kwargs
            )


class ResourceApi(object):
    """
    Managing the resource in the storage, using the driver.

    :param ResourceDriver driver: the driver which supports this resource in the storage.
    :param basestring resource_name: the name of the resource.
    """
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


def _generate_lower_name(model_cls):
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
    """
    Managing the resource storage.
    """
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
        """
        Registers the resource type in the resource storage manager.
        :param resource: the resource to register.
        """
        self._registered[resource] = ResourceApi(self._driver, resource_name=resource)

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
