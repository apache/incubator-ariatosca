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
SQLalchemy based RAPI
"""
import os
import shutil
from contextlib import contextmanager
from functools import partial
from distutils import dir_util                                # https://github.com/PyCQA/pylint/issues/73; pylint: disable=no-name-in-module
from multiprocessing import RLock

from aria.storage import (
    api,
    exceptions
)


class FileSystemResourceAPI(api.ResourceAPI):
    """
    File system resource storage.
    """

    def __init__(self, directory, **kwargs):
        """
        File system implementation for storage api.
        :param str directory: root dir for storage.
        """
        super(FileSystemResourceAPI, self).__init__(**kwargs)
        self.directory = directory
        self.base_path = os.path.join(self.directory, self.name)
        self._join_path = partial(os.path.join, self.base_path)
        self._lock = RLock()

    @contextmanager
    def connect(self):
        """
        Established a connection and destroys it after use.
        :return:
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
        Establish a conenction. used in the 'connect' contextmanager.
        :return:
        """
        self._lock.acquire()


    def _destroy_connection(self):
        """
        Destroy a connection. used in the 'connect' contextmanager.
        :return:
        """
        self._lock.release()

    def __repr__(self):
        return '{cls.__name__}(directory={self.directory})'.format(
            cls=self.__class__, self=self)

    def create(self, **kwargs):
        """
        Create directory in storage by path.
        tries to create the root directory as well.
        :param str name: path of file in storage.
        """
        try:
            os.makedirs(self.directory)
        except (OSError, IOError):
            pass
        try:
            os.makedirs(self.base_path)
        except (OSError, IOError):
            pass

    def read(self, entry_id, path=None, **_):
        """
        Retrieve the content of a file system storage resource.

        :param str entry_type: the type of the entry.
        :param str entry_id: the id of the entry.
        :param str path: a path to a specific resource.
        :return: the content of the file
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
                raise exceptions.StorageError('No resource in path: {0}'.format(resource))
            resource = os.path.join(resource, resources[0])
        with open(resource, 'rb') as resource_file:
            return resource_file.read()

    def download(self, entry_id, destination, path=None, **_):
        """
        Download a specific file or dir from the file system resource storage.

        :param str entry_type: the name of the entry.
        :param str entry_id: the id of the entry
        :param str destination: the destination of the files.
        :param str path: a path on the remote machine relative to the root of the entry.
        """
        resource_relative_path = os.path.join(self.name, entry_id, path or '')
        resource = os.path.join(self.directory, resource_relative_path)
        if not os.path.exists(resource):
            raise exceptions.StorageError("Resource {0} does not exist".
                                          format(resource_relative_path))
        if os.path.isfile(resource):
            shutil.copy2(resource, destination)
        else:
            dir_util.copy_tree(resource, destination)                                     # pylint: disable=no-member

    def upload(self, entry_id, source, path=None, **_):
        """
        Uploads a specific file or dir to the file system resource storage.

        :param str entry_type: the name of the entry.
        :param str entry_id: the id of the entry
        :param source: the source of  the files to upload.
        :param path: the destination of the file/s relative to the entry root dir.
        """
        resource_directory = os.path.join(self.directory, self.name, entry_id)
        if not os.path.exists(resource_directory):
            os.makedirs(resource_directory)
        destination = os.path.join(resource_directory, path or '')
        if os.path.isfile(source):
            shutil.copy2(source, destination)
        else:
            dir_util.copy_tree(source, destination)                                       # pylint: disable=no-member
