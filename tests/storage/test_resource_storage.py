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

import os
import tempfile

import pytest

from aria.exceptions import StorageError
from aria.storage import ResourceStorage, FileSystemResourceDriver
from . import TestFileSystem


class TestResourceStorage(TestFileSystem):
    def _create(self, storage):
        storage.register('blueprint')
        storage.setup()

    def _upload(self, storage, tmp_path, id):
        with open(tmp_path, 'w') as f:
            f.write('fake context')

        storage.blueprint.upload(entry_id=id, source=tmp_path)

    def _upload_dir(self, storage, tmp_dir, tmp_file_name, id):
        file_source = os.path.join(tmp_dir, tmp_file_name)
        with open(file_source, 'w') as f:
            f.write('fake context')

        storage.blueprint.upload(entry_id=id, source=tmp_dir)

    def test_name(self):
        driver = FileSystemResourceDriver(directory=self.path)
        storage = ResourceStorage(driver, resources=['blueprint'])
        assert repr(storage) == 'ResourceStorage(driver={driver})'.format(
            driver=driver
        )
        assert repr(storage.registered['blueprint']) == (
            'ResourceApi(driver={driver}, resource={resource_name})'.format(
                driver=driver,
                resource_name='blueprint'))

    def test_create(self):
        storage = ResourceStorage(FileSystemResourceDriver(directory=self.path))
        self._create(storage)
        assert os.path.exists(os.path.join(self.path, 'blueprint'))

    def test_upload_file(self):
        storage = ResourceStorage(FileSystemResourceDriver(directory=self.path))
        self._create(storage)
        tmpfile_path = tempfile.mkstemp(suffix=self.__class__.__name__, dir=self.path)[1]
        self._upload(storage, tmpfile_path, id='blueprint_id')

        storage_path = os.path.join(
            self.path,
            'blueprint',
            'blueprint_id',
            os.path.basename(tmpfile_path))
        assert os.path.exists(storage_path)

        with open(storage_path, 'rb') as f:
            assert f.read() == 'fake context'

    def test_download_file(self):
        storage = ResourceStorage(FileSystemResourceDriver(directory=self.path))
        self._create(storage)
        tmpfile_path = tempfile.mkstemp(suffix=self.__class__.__name__, dir=self.path)[1]
        tmpfile_name = os.path.basename(tmpfile_path)
        self._upload(storage, tmpfile_path, 'blueprint_id')

        temp_dir = tempfile.mkdtemp(dir=self.path)
        storage.blueprint.download(
            entry_id='blueprint_id',
            destination=temp_dir,
            path=tmpfile_name)

        with open(os.path.join(self.path, os.path.join(temp_dir, tmpfile_name))) as f:
            assert f.read() == 'fake context'

    def test_data_file(self):
        storage = ResourceStorage(FileSystemResourceDriver(directory=self.path))
        self._create(storage)
        tmpfile_path = tempfile.mkstemp(suffix=self.__class__.__name__, dir=self.path)[1]
        self._upload(storage, tmpfile_path, 'blueprint_id')

        assert storage.blueprint.data(entry_id='blueprint_id') == 'fake context'

    def test_upload_dir(self):
        storage = ResourceStorage(FileSystemResourceDriver(directory=self.path))
        self._create(storage)
        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        second_level_tmp_dir = tempfile.mkdtemp(dir=tmp_dir)
        tmp_filename = tempfile.mkstemp(dir=second_level_tmp_dir)[1]
        self._upload_dir(storage, tmp_dir, tmp_filename, id='blueprint_id')

        destination = os.path.join(
            self.path,
            'blueprint',
            'blueprint_id',
            os.path.basename(second_level_tmp_dir),
            os.path.basename(tmp_filename))

        assert os.path.isfile(destination)

    def test_upload_path_in_dir(self):
        storage = ResourceStorage(FileSystemResourceDriver(directory=self.path))
        self._create(storage)
        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        second_level_tmp_dir = tempfile.mkdtemp(dir=tmp_dir)
        tmp_filename = tempfile.mkstemp(dir=second_level_tmp_dir)[1]
        self._upload_dir(storage, tmp_dir, tmp_filename, id='blueprint_id')

        second_update_file = tempfile.mkstemp(dir=self.path)[1]
        with open(second_update_file, 'w') as f:
            f.write('fake context2')

        storage.blueprint.upload(
            entry_id='blueprint_id',
            source=second_update_file,
            path=os.path.basename(second_level_tmp_dir))

        assert os.path.isfile(os.path.join(
            self.path,
            'blueprint',
            'blueprint_id',
            os.path.basename(second_level_tmp_dir),
            os.path.basename(second_update_file)))

    def test_download_dir(self):
        storage = ResourceStorage(FileSystemResourceDriver(directory=self.path))
        self._create(storage)
        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        second_level_tmp_dir = tempfile.mkdtemp(dir=tmp_dir)
        tmp_filename = tempfile.mkstemp(dir=second_level_tmp_dir)[1]
        self._upload_dir(storage, tmp_dir, tmp_filename, id='blueprint_id')

        temp_destination_dir = tempfile.mkdtemp(dir=self.path)
        storage.blueprint.download(
            entry_id='blueprint_id',
            destination=temp_destination_dir)

        destination_file_path = os.path.join(
            temp_destination_dir,
            os.path.basename(second_level_tmp_dir),
            os.path.basename(tmp_filename))

        assert os.path.isfile(destination_file_path)

        with open(destination_file_path) as f:
            assert f.read() == 'fake context'

    def test_data_dir(self):
        storage = ResourceStorage(FileSystemResourceDriver(directory=self.path))
        self._create(storage)

        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        tempfile.mkstemp(dir=tmp_dir)
        tempfile.mkstemp(dir=tmp_dir)

        storage.blueprint.upload(entry_id='blueprint_id', source=tmp_dir)

        with pytest.raises(StorageError):
            storage.blueprint.data(entry_id='blueprint_id')
