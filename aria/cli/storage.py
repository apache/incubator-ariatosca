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
Filesystem related CLI storage location and configuration
"""

import os
import getpass
from shutil import rmtree

work_space_directory = '.aria'
storage_directory_name = 'local-storage'


def user_space(user_name=getpass.getuser()):
    """
    Base work directory
    """
    user_path = '~{0}'.format(user_name)
    real_path = os.path.expanduser(user_path)
    if os.path.exists(real_path):
        return os.path.join(real_path, work_space_directory)
    return os.path.join(os.getcwd(), work_space_directory)


def local_storage(user_name=getpass.getuser()):
    """
    Base storage directory
    """
    return os.path.join(user_space(user_name), storage_directory_name)


def local_model_storage():
    """
    Model storage directory
    """
    return os.path.join(local_storage(), 'models')


def local_resource_storage():
    """
    Resource storage directory
    """
    return os.path.join(local_storage(), 'resources')


def config_file_path():
    """
    Configuration file path
    """
    path = os.path.join(user_space(), 'config.yaml')
    if not os.path.exists(path):
        open(path, 'w').close()
    return path


def create_user_space(user_name=getpass.getuser(), override=False):
    """
    Creates the base work directory
    """
    path = user_space(user_name)
    if os.path.exists(path):
        if override:
            rmtree(path, ignore_errors=True)
        else:
            raise IOError('user space {0} already exists'.format(path))
    os.mkdir(path)
    return path


def create_local_storage(user_name=getpass.getuser(), override=False):
    """
    Creates the base storage directory
    """
    path = local_storage(user_name)
    if os.path.exists(path):
        if override:
            rmtree(path, ignore_errors=True)
        else:
            raise IOError('local storage {0} already exists'.format(path))
    os.mkdir(path)
    return path
