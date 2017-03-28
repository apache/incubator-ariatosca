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

from aria.logger import LoggerMixin, NullHandler
from . import sql_mapi

__all__ = (
    'Storage',
    'ModelStorage',
    'ResourceStorage'
)


class Storage(LoggerMixin):
    """
    Represents the storage
    """
    def __init__(self,
                 api_cls,
                 api_kwargs=None,
                 items=(),
                 initiator=None,
                 initiator_kwargs=None,
                 **kwargs):
        """

        :param api_cls: API cls for each model.
        :param api_kwargs:
        :param items: the items to register
        :param initiator: a func which initializes the storage before the first use.
        This function should return a dict, this dict would be passed in addition to the api kwargs.
        This enables the creation of any unpickable objects across process.
        :param initiator_kwargs:
        :param kwargs:
        """
        super(Storage, self).__init__(**kwargs)
        # Set the logger handler of any storage object to NullHandler.
        # This is since the absence of a handler shows up while using the CLI in the form of:
        # `No handlers could be found for logger "aria.ResourceStorage"`.
        self.logger.addHandler(NullHandler())
        self.api = api_cls
        self.registered = {}
        self._initiator = initiator
        self._initiator_kwargs = initiator_kwargs or {}
        self._api_kwargs = api_kwargs or {}
        self._additional_api_kwargs = {}
        if self._initiator:
            self._additional_api_kwargs = self._initiator(**self._initiator_kwargs)
        for item in items:
            self.register(item)
        self.logger.debug('{name} object is ready: {0!r}'.format(
            self, name=self.__class__.__name__))

    @property
    def _all_api_kwargs(self):
        kwargs = self._api_kwargs.copy()
        kwargs.update(self._additional_api_kwargs)
        return kwargs

    def __repr__(self):
        return '{name}(api={self.api})'.format(name=self.__class__.__name__, self=self)

    def __getattr__(self, item):
        try:
            return self.registered[item]
        except KeyError:
            return super(Storage, self).__getattribute__(item)

    @property
    def serialization_dict(self):
        return {
            'api': self.api,
            'api_kwargs': self._api_kwargs,
            'initiator': self._initiator,
            'initiator_kwargs': self._initiator_kwargs
        }

    def register(self, entry):
        """
        Register the entry to the storage
        :param name:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract register method')


class ResourceStorage(Storage):
    """
    Represents resource storage.
    """
    def register(self, name):
        """
        Register the resource type to resource storage.
        :param name:
        :return:
        """
        self.registered[name] = self.api(name=name, **self._all_api_kwargs)
        self.registered[name].create()
        self.logger.debug('setup {name} in storage {self!r}'.format(name=name, self=self))


class ModelStorage(Storage):
    """
    Represents model storage.
    """
    def __init__(self, *args, **kwargs):
        if kwargs.get('initiator', None) is None:
            kwargs['initiator'] = sql_mapi.init_storage
        super(ModelStorage, self).__init__(*args, **kwargs)

    def register(self, model_cls):
        """
        Register the model into the model storage.
        :param model_cls: the model to register.
        :return:
        """
        model_name = model_cls.__modelname__
        if model_name in self.registered:
            self.logger.debug('{name} in already storage {self!r}'.format(name=model_name,
                                                                          self=self))
            return
        self.registered[model_name] = self.api(name=model_name,
                                               model_cls=model_cls,
                                               **self._all_api_kwargs)
        self.registered[model_name].create()
        self.logger.debug('setup {name} in storage {self!r}'.format(name=model_name, self=self))

    def drop(self):
        """
        Drop all the tables from the model.
        :return:
        """
        for mapi in self.registered.values():
            mapi.drop()
