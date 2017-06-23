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
Storage API management.
"""

import copy
from contextlib import contextmanager

from aria.logger import LoggerMixin
from . import sql_mapi

__all__ = (
    'Storage',
    'ModelStorage',
    'ResourceStorage'
)


class Storage(LoggerMixin):
    """
    Base class for storage managers.
    """
    def __init__(self,
                 api_cls,
                 api_kwargs=None,
                 items=(),
                 initiator=None,
                 initiator_kwargs=None,
                 **kwargs):
        """
        :param api_cls: API class for each entry
        :param api_kwargs:
        :param items: items to register
        :param initiator: function which initializes the storage before the first use; this function
         should return a dict, this dict would be passed in addition to the API kwargs; this enables
         the creation of non-serializable objects
        :param initiator_kwargs:
        :param kwargs:
        """
        super(Storage, self).__init__(**kwargs)
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
        Register an API.

        :param entry:
        """
        raise NotImplementedError('Subclass must implement abstract register method')


class ResourceStorage(Storage):
    """
    Manages storage resource APIs ("RAPIs").
    """
    def register(self, name):
        """
        Register a storage resource API ("RAPI").

        :param name: name
        """
        self.registered[name] = self.api(name=name, **self._all_api_kwargs)
        self.registered[name].create()
        self.logger.debug('setup {name} in storage {self!r}'.format(name=name, self=self))


class ModelStorage(Storage):
    """
    Manages storage model APIs ("MAPIs").
    """
    def __init__(self, *args, **kwargs):
        if kwargs.get('initiator', None) is None:
            kwargs['initiator'] = sql_mapi.init_storage
        super(ModelStorage, self).__init__(*args, **kwargs)

    def register(self, model_cls):
        """
        Register a storage model API ("MAPI").

        :param model_cls: model API to register
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
        Drop all the tables.
        """
        for mapi in self.registered.values():
            mapi.drop()

    @contextmanager
    def instrument(self, *instrumentation):
        original_instrumentation = {}

        try:
            for mapi in self.registered.values():
                original_instrumentation[mapi] = copy.copy(mapi._instrumentation)
                mapi._instrumentation.extend(instrumentation)
            yield self
        finally:
            for mapi in self.registered.values():
                mapi._instrumentation[:] = original_instrumentation[mapi]
