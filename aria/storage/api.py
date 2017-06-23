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
Storage APIs.
"""

import threading


class StorageAPI(object):
    """
    Base class for storage APIs.
    """
    def create(self, **kwargs):
        """
        Create a storage API.
        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract create method')


class ModelAPI(StorageAPI):
    """
    Base class for model APIs ("MAPI").
    """
    def __init__(self, model_cls, name=None, **kwargs):
        """
        :param model_cls: representing class of the model
        :param name: name of the model
        """
        super(ModelAPI, self).__init__(**kwargs)
        self._model_cls = model_cls
        self._name = name or model_cls.__modelname__
        self._thread_local = threading.local()
        self._thread_local._instrumentation = []

    @property
    def _instrumentation(self):
        if not hasattr(self._thread_local, '_instrumentation'):
            self._thread_local._instrumentation = []
        return self._thread_local._instrumentation


    @property
    def name(self):
        """
        Name of the class.

        :type: :obj:`basestring`
        """
        return self._name

    @property
    def model_cls(self):
        """
        Class representing the model

        :type: :obj:`Type`
        """
        return self._model_cls

    def get(self, entry_id, filters=None, **kwargs):
        """
        Gets a model from storage.

        :param entry_id:
        """
        raise NotImplementedError('Subclass must implement abstract get method')

    def put(self, entry, **kwargs):
        """
        Puts a model in storage.

        :param entry:
        """
        raise NotImplementedError('Subclass must implement abstract store method')

    def delete(self, entry_id, **kwargs):
        """
        Deletes a model from storage.

        :param entry_id:
        """
        raise NotImplementedError('Subclass must implement abstract delete method')

    def __iter__(self):
        return self.iter()

    def iter(self, **kwargs):
        """
        Iterate over all models in storage.
        """
        raise NotImplementedError('Subclass must implement abstract iter method')

    def update(self, entry, **kwargs):
        """
        Update a model in storage.

        :param entry:
        :param kwargs:
        """
        raise NotImplementedError('Subclass must implement abstract update method')


class ResourceAPI(StorageAPI):
    """
    Base class for resource APIs ("RAPI").
    """
    def __init__(self, name, **kwargs):
        """
        :param name: resource type
        """
        super(ResourceAPI, self).__init__(**kwargs)
        self._name = name

    @property
    def name(self):
        """
        Name of resource.

        :type: :obj:`basestring`
        """
        return self._name

    def read(self, entry_id, path, **kwargs):
        """
        Get a bytesteam for a resource from storage.

        :param entry_id:
        :param path:
        """
        raise NotImplementedError('Subclass must implement abstract read method')

    def delete(self, entry_id, path, **kwargs):
        """
        Delete a resource from storage.

        :param entry_id:
        :param path:
        """
        raise NotImplementedError('Subclass must implement abstract delete method')

    def download(self, entry_id, destination, path=None, **kwargs):
        """
        Download a resource from storage.

        :param entry_id:
        :param destination:
        :param path:
        """
        raise NotImplementedError('Subclass must implement abstract download method')

    def upload(self, entry_id, source, path=None, **kwargs):
        """
        Upload a resource to storage.

        :param entry_id:
        :param source:
        :param path:
        """
        raise NotImplementedError('Subclass must implement abstract upload method')


def generate_lower_name(model_cls):
    """
    Generates the name of the class from the class object, e.g. ``SomeClass`` -> ``some_class``

    :param model_cls: class to evaluate
    :return: lowercase name
    :rtype: basestring
    """
    return getattr(model_cls, '__mapiname__', model_cls.__tablename__)
