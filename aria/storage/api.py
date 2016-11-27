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
General storage API
"""


class StorageAPI(object):
    """
    General storage Base API
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
    A Base object for the model.
    """
    def __init__(self, model_cls, name=None, **kwargs):
        """
        Base model API

        :param model_cls: the representing class of the model
        :param str name: the name of the model
        :param kwargs:
        """
        super(ModelAPI, self).__init__(**kwargs)
        self._model_cls = model_cls
        self._name = name or generate_lower_name(model_cls)

    @property
    def name(self):
        """
        The name of the class
        :return: name of the class
        """
        return self._name

    @property
    def model_cls(self):
        """
        The class represting the model
        :return:
        """
        return self._model_cls

    def get(self, entry_id, filters=None, **kwargs):
        """
        Get entry from storage.

        :param entry_id:
        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract get method')

    def put(self, entry, **kwargs):
        """
        Store entry in storage

        :param entry:
        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract store method')

    def delete(self, entry_id, **kwargs):
        """
        Delete entry from storage.

        :param entry_id:
        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract delete method')

    def __iter__(self):
        return self.iter()

    def iter(self, **kwargs):
        """
        Iter over the entries in storage.

        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract iter method')

    def update(self, entry, **kwargs):
        """
        Update entry in storage.

        :param entry:
        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract update method')


class ResourceAPI(StorageAPI):
    """
    A Base object for the resource.
    """
    def __init__(self, name):
        """
        Base resource API
        :param str name: the resource type
        """
        self._name = name

    @property
    def name(self):
        """
        The name of the resource
        :return:
        """
        return self._name

    def read(self, entry_id, path=None, **kwargs):
        """
        Get a bytesteam from the storage.

        :param entry_id:
        :param path:
        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract data method')

    def download(self, entry_id, destination, path=None, **kwargs):
        """
        Download a resource from the storage.

        :param entry_id:
        :param destination:
        :param path:
        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract download method')

    def upload(self, entry_id, source, path=None, **kwargs):
        """
        Upload a resource to the storage.

        :param entry_id:
        :param source:
        :param path:
        :param kwargs:
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract upload method')


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
