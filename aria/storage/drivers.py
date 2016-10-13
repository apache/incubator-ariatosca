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
Aria's storage.drivers module
Path: aria.storage.driver

drivers module holds a generic abstract implementation of drivers.

classes:
    * Driver - abstract storage driver implementation.
    * ModelDriver - abstract model base storage driver.
    * ResourceDriver - abstract resource base storage driver.
    * FileSystemModelDriver - file system implementation for model storage driver.
    * FileSystemResourceDriver - file system implementation for resource storage driver.
"""

import os
import shutil
# pylint has an issue with distutils and virtualenvs: https://github.com/PyCQA/pylint/issues/73
import distutils.dir_util                                                                           # pylint: disable=no-name-in-module, import-error
from functools import partial
from multiprocessing import RLock

import jsonpickle

from ..exceptions import StorageError
from ..logger import LoggerMixin


__all__ = (
    'ModelDriver',
    'FileSystemModelDriver',
    'ResourceDriver',
    'FileSystemResourceDriver',
)


class Driver(LoggerMixin):
    """
    Driver: storage driver context manager - abstract driver implementation.
    In the implementation level, It is a good practice to raise StorageError on Errors.
    """

    def __enter__(self):
        """
        Context manager entry method, executes connect.
        :return: context manager instance
        :rtype: Driver
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method, executes disconnect.
        """
        self.disconnect()
        if not exc_type:
            return
        # self.logger.debug(
        #     '{name} had an error'.format(name=self.__class__.__name__),
        #     exc_info=(exc_type, exc_val, exc_tb))
        if StorageError in exc_type.mro():
            return
        raise StorageError('Exception had occurred, {type}: {message}'.format(
            type=exc_type, message=str(exc_val)))

    def connect(self):
        """
        Open storage connection.
        In some cases, This method can get the connection from a connection pool.
        """
        pass

    def disconnect(self):
        """
        Close storage connection.
        In some cases, This method can release the connection to the connection pool.
        """
        pass

    def create(self, name, *args, **kwargs):
        """
        Create table/document in storage by name.
        :param str name: name of table/document in storage.
        """
        pass


class ModelDriver(Driver):
    """
    ModelDriver context manager.
    Base Driver for Model based storage.
    """

    def get(self, name, entry_id, **kwargs):
        """
        Getter from storage.
        :param str name: name of table/document in storage.
        :param str entry_id: id of the document to get from storage.
        :return: value of entity from the storage.
        """
        raise NotImplementedError('Subclass must implement abstract get method')

    def delete(self, name, entry_id, **kwargs):
        """
        Delete from storage.
        :param str name: name of table/document in storage.
        :param str entry_id: id of the entity to delete from storage.
        :param dict kwargs: extra kwargs if needed.
        """
        raise NotImplementedError('Subclass must implement abstract delete method')

    def store(self, name, entry_id, entry, **kwargs):
        """
        Setter to storage.
        :param str name: name of table/document in storage.
        :param str entry_id: id of the entity to store in the storage.
        :param dict entry: content to store.
        """
        raise NotImplementedError('Subclass must implement abstract store method')

    def iter(self, name, **kwargs):
        """
        Generator over the entries of table/document in storage.
        :param str name: name of table/document/file in storage to iter over.
        """
        raise NotImplementedError('Subclass must implement abstract iter method')

    def update(self, name, entry_id, **kwargs):
        """
        Updates and entry in storage.

        :param str name: name of table/document in storage.
        :param str entry_id: id of the document to get from storage.
        :param kwargs: the fields to update.
        :return:
        """
        raise NotImplementedError('Subclass must implement abstract store method')


class ResourceDriver(Driver):
    """
    ResourceDriver context manager.
    Base Driver for Resource based storage.

    Resource storage structure is a file system base.
    <resource root directory>/<resource_name>/<entry_id>/<entry>
    entry: can be one single file or multiple files and directories.
    """

    def data(self, entry_type, entry_id, path=None, **kwargs):
        """
        Get the binary data from a file in a resource entry.
        If the entry is a single file no path needed,
        If the entry contain number of files the path will gide to the relevant file.

        resource path:
            <resource root directory>/<name>/<entry_id>/<path>

        :param basestring entry_type: resource name.
        :param basestring entry_id: id of the entity to resource in the storage.
        :param basestring path: path to resource relative to entry_id folder in the storage.
        :return: entry file object.
        :rtype: bytes
        """
        raise NotImplementedError('Subclass must implement abstract get method')

    def download(self, entry_type, entry_id, destination, path=None, **kwargs):
        """
        Download the resource to a destination.
        Like data method bat this method isn't returning data,
        Instead it create a new file in local file system.

        resource path:
            <resource root directory>/<name>/<entry_id>/<path>
        copy to:
            /<destination>
        destination can be file or directory

        :param basestring entry_type: resource name.
        :param basestring entry_id: id of the entity to resource in the storage.
        :param basestring destination: path in local file system to download to.
        :param basestring path: path to resource relative to entry_id folder in the storage.
        """
        raise NotImplementedError('Subclass must implement abstract get method')

    def upload(self, entry_type, entry_id, source, path=None, **kwargs):
        """
        Upload the resource from source.
        source can be file or directory with files.

        copy from:
            /<source>
        to resource path:
            <resource root directory>/<name>/<entry_id>/<path>

        :param basestring entry_type: resource name.
        :param basestring entry_id: id of the entity to resource in the storage.
        :param basestring source: source can be file or directory with files.
        :param basestring path: path to resource relative to entry_id folder in the storage.
        """
        raise NotImplementedError('Subclass must implement abstract get method')


class BaseFileSystemDriver(Driver):
    """
    Base class which handles storage on the file system.
    """
    def __init__(self, *args, **kwargs):
        super(BaseFileSystemDriver, self).__init__(*args, **kwargs)
        self._lock = RLock()

    def connect(self):
        self._lock.acquire()

    def disconnect(self):
        self._lock.release()

    def __getstate__(self):
        obj_dict = super(BaseFileSystemDriver, self).__getstate__()
        del obj_dict['_lock']
        return obj_dict

    def __setstate__(self, obj_dict):
        super(BaseFileSystemDriver, self).__setstate__(obj_dict)
        vars(self).update(_lock=RLock(), **obj_dict)


class FileSystemModelDriver(ModelDriver, BaseFileSystemDriver):
    """
    FileSystemModelDriver context manager.
    """

    def __init__(self, directory, **kwargs):
        """
        File system implementation for storage driver.
        :param str directory: root dir for storage.
        """
        super(FileSystemModelDriver, self).__init__(**kwargs)
        self.directory = directory

        self._join_path = partial(os.path.join, self.directory)

    def __repr__(self):
        return '{cls.__name__}(directory={self.directory})'.format(
            cls=self.__class__, self=self)

    def create(self, name):
        """
        Create directory in storage by path.
        tries to create the root directory as well.
        :param str name: path of file in storage.
        """
        try:
            os.makedirs(self.directory)
        except (OSError, IOError):
            pass
        os.makedirs(self._join_path(name))

    def get(self, name, entry_id, **kwargs):
        """
        Getter from storage.
        :param str name: name of directory in storage.
        :param str entry_id: id of the file to get from storage.
        :return: value of file from storage.
        :rtype: dict
        """
        with open(self._join_path(name, entry_id)) as file_obj:
            return jsonpickle.loads(file_obj.read())

    def store(self, name, entry_id, entry, **kwargs):
        """
        Delete from storage.
        :param str name: name of directory in storage.
        :param str entry_id: id of the file to delete from storage.
        """
        with open(self._join_path(name, entry_id), 'w') as file_obj:
            file_obj.write(jsonpickle.dumps(entry))

    def delete(self, name, entry_id, **kwargs):
        """
        Delete from storage.
        :param str name: name of directory in storage.
        :param str entry_id: id of the file to delete from storage.
        """
        os.remove(self._join_path(name, entry_id))

    def iter(self, name, filters=None, **kwargs):
        """
        Generator over the entries of directory in storage.
        :param str name: name of directory in storage to iter over.
        :param dict filters: filters for query
        """
        filters = filters or {}

        for entry_id in os.listdir(self._join_path(name)):
            value = self.get(name, entry_id=entry_id)
            for filter_name, filter_value in filters.items():
                if value.get(filter_name) != filter_value:
                    break
            else:
                yield value

    def update(self, name, entry_id, **kwargs):
        """
        Updates and entry in storage.

        :param str name: name of table/document in storage.
        :param str entry_id: id of the document to get from storage.
        :param kwargs: the fields to update.
        :return:
        """
        entry_dict = self.get(name, entry_id)
        entry_dict.update(**kwargs)
        self.store(name, entry_id, entry_dict)


class FileSystemResourceDriver(ResourceDriver, BaseFileSystemDriver):
    """
    FileSystemResourceDriver context manager.
    """

    def __init__(self, directory, **kwargs):
        """
        File system implementation for storage driver.
        :param str directory: root dir for storage.
        """
        super(FileSystemResourceDriver, self).__init__(**kwargs)
        self.directory = directory
        self._join_path = partial(os.path.join, self.directory)

    def __repr__(self):
        return '{cls.__name__}(directory={self.directory})'.format(
            cls=self.__class__, self=self)

    def create(self, name):
        """
        Create directory in storage by path.
        tries to create the root directory as well.
        :param basestring name: path of file in storage.
        """
        try:
            os.makedirs(self.directory)
        except (OSError, IOError):
            pass
        os.makedirs(self._join_path(name))

    def data(self, entry_type, entry_id, path=None):
        """
        Retrieve the content of a file system storage resource.

        :param basestring entry_type: the type of the entry.
        :param basestring entry_id: the id of the entry.
        :param basestring path: a path to a specific resource.
        :return: the content of the file
        :rtype: bytes
        """
        resource = os.path.join(self.directory, entry_type, entry_id, path or '')
        if not os.path.isfile(resource):
            resources = os.listdir(resource)
            if len(resources) != 1:
                raise StorageError('No resource in path: {0}'.format(resource))
            resource = os.path.join(resource, resources[0])
        with open(resource, 'rb') as resource_file:
            return resource_file.read()

    def download(self, entry_type, entry_id, destination, path=None):
        """
        Download a specific file or dir from the file system resource storage.

        :param basestring entry_type: the name of the entry.
        :param basestring entry_id: the id of the entry
        :param basestring destination: the destination of the files.
        :param basestring path: a path on the remote machine relative to the root of the entry.
        """
        resource = os.path.join(self.directory, entry_type, entry_id, path or '')
        if os.path.isfile(resource):
            shutil.copy2(resource, destination)
        else:
            distutils.dir_util.copy_tree(resource, destination)                                     # pylint: disable=no-member

    def upload(self, entry_type, entry_id, source, path=None):
        """
        Uploads a specific file or dir to the file system resource storage.

        :param basestring entry_type: the name of the entry.
        :param basestring entry_id: the id of the entry
        :param source: the source of  the files to upload.
        :param path: the destination of the file/s relative to the entry root dir.
        """
        resource_directory = os.path.join(self.directory, entry_type, entry_id)
        if not os.path.exists(resource_directory):
            os.makedirs(resource_directory)
        destination = os.path.join(resource_directory, path or '')
        if os.path.isfile(source):
            shutil.copy2(source, destination)
        else:
            distutils.dir_util.copy_tree(source, destination)                                       # pylint: disable=no-member
