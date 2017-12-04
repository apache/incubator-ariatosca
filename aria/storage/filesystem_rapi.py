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
File system implementation of the storage resource API ("RAPI").
"""

import os
import shutil
from multiprocessing import RLock
from contextlib import contextmanager
from functools import partial
from distutils import dir_util                                # https://github.com/PyCQA/pylint/issues/73; pylint: disable=no-name-in-module

from aria.storage import (
    api,
    exceptions
)


class FileSystemResourceAPI(api.ResourceAPI):
    """
    File system implementation of the storage resource API ("RAPI").
    """

    def __init__(self, directory, **kwargs):
        """
        :param directory: root dir for storage
        """
        super(FileSystemResourceAPI, self).__init__(**kwargs)
        self.directory = directory
        self.base_path = os.path.join(self.directory, self.name)
        self._join_path = partial(os.path.join, self.base_path)
        self._lock = RLock()

    @contextmanager
    def connect(self):
        """
        Establishes a connection and destroys it after use.
        """
        try:
            self._establish_connection()
            yield self
        except BaseException as e:
            raise exceptions.StorageError(str(e))
        finally:
            self._destroy_connection()

    def _establish_connection(self):
        """
        Establishes a connection. Used in the ``connect`` context manager.
        """
        self._lock.acquire()

    def _destroy_connection(self):
        """
        Destroys a connection. Used in the ``connect`` context manager.
        """
        self._lock.release()

    def __repr__(self):
        return '{cls.__name__}(directory={self.directory})'.format(
            cls=self.__class__, self=self)

    def create(self, **kwargs):
        """
        Creates a directory in by path. Tries to create the root directory as well.

        :param name: path of directory
        """
        try:
            os.makedirs(self.directory)
        except (OSError, IOError):
            pass
        try:
            os.makedirs(self.base_path)
        except (OSError, IOError):
            pass

    def read(self, entry_id, path, **_):
        """
        Retrieves the contents of a file.

        :param entry_id: entry ID
        :param path: path to resource
        :return: contents of the file
        :rtype: bytes
        """
        resource_relative_path = os.path.join(self.name, entry_id, path or '')
        resource = os.path.join(self.directory, resource_relative_path)
        if not os.path.exists(resource):
            raise exceptions.StorageError("Resource {0} does not exist".
                                          format(resource_relative_path))
        if not os.path.isfile(resource):
            resources = os.listdir(resource)
            if len(resources) != 1:
                raise exceptions.StorageError(
                    'Failed to read {0}; Reading a directory is '
                    'only allowed when it contains a single resource'.format(resource))
            resource = os.path.join(resource, resources[0])
        with open(resource, 'rb') as resource_file:
            return resource_file.read()

    def download(self, entry_id, destination, path=None, **_):
        """
        Downloads a file or directory.

        :param entry_id: entry ID
        :param destination: download destination
        :param path: path to download relative to the root of the entry (otherwise all)
        """
        resource_relative_path = os.path.join(self.name, entry_id, path or '')
        resource = os.path.join(self.directory, resource_relative_path)
        if not os.path.exists(resource):
            raise exceptions.StorageError("Resource {0} does not exist".
                                          format(resource_relative_path))
        if os.path.isfile(resource):
            shutil.copy2(resource, destination)
        else:
            dir_util.copy_tree(resource, destination)                                               # pylint: disable=no-member

    def upload(self, entry_id, source, path=None, **_):
        """
        Uploads a file or directory.

        :param entry_id: entry ID
        :param source: source of the files to upload
        :param path: the destination of the file/s relative to the entry root dir.
        """
        resource_directory = os.path.join(self.directory, self.name, entry_id)
        if not os.path.exists(resource_directory):
            os.makedirs(resource_directory)
        destination = os.path.join(resource_directory, path or '')
        if os.path.isfile(source):
            shutil.copy2(source, destination)
        else:
            dir_util.copy_tree(source, destination)                                                 # pylint: disable=no-member

    def delete(self, entry_id, path=None, **_):
        """
        Deletes a file or directory.

        :param entry_id: entry ID
        :param path: path to delete relative to the root of the entry (otherwise all)
        """
        destination = os.path.join(self.directory, self.name, entry_id, path or '')
        if os.path.exists(destination):
            if os.path.isfile(destination):
                os.remove(destination)
            else:
                shutil.rmtree(destination)
            return True
        return False
