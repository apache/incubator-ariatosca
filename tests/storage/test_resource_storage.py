# Licensed to the Apache ftware Foundation (ASF) under one or more
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

from aria.storage.filesystem_rapi import FileSystemResourceAPI
from aria.storage import (
    exceptions,
    ResourceStorage
)
from . import TestFileSystem


class TestResourceStorage(TestFileSystem):
    def _create(self, storage):
        storage.register('service_template')

    def _upload(self, storage, tmp_path, id):
        with open(tmp_path, 'w') as f:
            f.write('fake context')

        storage.service_template.upload(entry_id=id, source=tmp_path)

    def _upload_dir(self, storage, tmp_dir, tmp_file_name, id):
        file_source = os.path.join(tmp_dir, tmp_file_name)
        with open(file_source, 'w') as f:
            f.write('fake context')

        storage.service_template.upload(entry_id=id, source=tmp_dir)

    def _create_storage(self):
        return ResourceStorage(FileSystemResourceAPI,
                               api_kwargs=dict(directory=self.path))

    def test_name(self):
        api = FileSystemResourceAPI
        storage = ResourceStorage(FileSystemResourceAPI,
                                  items=['service_template'],
                                  api_kwargs=dict(directory=self.path))
        assert repr(storage) == 'ResourceStorage(api={api})'.format(api=api)
        assert 'directory={resource_dir}'.format(resource_dir=self.path) in \
               repr(storage.registered['service_template'])

    def test_create(self):
        storage = self._create_storage()
        self._create(storage)
        assert os.path.exists(os.path.join(self.path, 'service_template'))

    def test_upload_file(self):
        storage = ResourceStorage(FileSystemResourceAPI, api_kwargs=dict(directory=self.path))
        self._create(storage)
        tmpfile_path = tempfile.mkstemp(suffix=self.__class__.__name__, dir=self.path)[1]
        self._upload(storage, tmpfile_path, id='service_template_id')

        storage_path = os.path.join(
            self.path,
            'service_template',
            'service_template_id',
            os.path.basename(tmpfile_path))
        assert os.path.exists(storage_path)

        with open(storage_path, 'rb') as f:
            assert f.read() == 'fake context'

    def test_download_file(self):
        storage = self._create_storage()
        self._create(storage)
        tmpfile_path = tempfile.mkstemp(suffix=self.__class__.__name__, dir=self.path)[1]
        tmpfile_name = os.path.basename(tmpfile_path)
        self._upload(storage, tmpfile_path, 'service_template_id')

        temp_dir = tempfile.mkdtemp(dir=self.path)
        storage.service_template.download(
            entry_id='service_template_id',
            destination=temp_dir,
            path=tmpfile_name)

        with open(os.path.join(self.path, os.path.join(temp_dir, tmpfile_name))) as f:
            assert f.read() == 'fake context'

    def test_download_non_existing_file(self):
        storage = self._create_storage()
        self._create(storage)
        with pytest.raises(exceptions.StorageError):
            storage.service_template.download(entry_id='service_template_id', destination='',
                                              path='fake_path')

    def test_data_non_existing_file(self):
        storage = self._create_storage()
        self._create(storage)
        with pytest.raises(exceptions.StorageError):
            storage.service_template.read(entry_id='service_template_id', path='fake_path')

    def test_data_file(self):
        storage = self._create_storage()
        self._create(storage)
        tmpfile_path = tempfile.mkstemp(suffix=self.__class__.__name__, dir=self.path)[1]
        self._upload(storage, tmpfile_path, 'service_template_id')

        assert storage.service_template.read(entry_id='service_template_id',
                                             path=os.path.basename(tmpfile_path)) == 'fake context'

    def test_upload_dir(self):
        storage = self._create_storage()
        self._create(storage)
        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        second_level_tmp_dir = tempfile.mkdtemp(dir=tmp_dir)
        tmp_filename = tempfile.mkstemp(dir=second_level_tmp_dir)[1]
        self._upload_dir(storage, tmp_dir, tmp_filename, id='service_template_id')

        destination = os.path.join(
            self.path,
            'service_template',
            'service_template_id',
            os.path.basename(second_level_tmp_dir),
            os.path.basename(tmp_filename))

        assert os.path.isfile(destination)

    def test_upload_path_in_dir(self):
        storage = self._create_storage()
        self._create(storage)
        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        second_level_tmp_dir = tempfile.mkdtemp(dir=tmp_dir)
        tmp_filename = tempfile.mkstemp(dir=second_level_tmp_dir)[1]
        self._upload_dir(storage, tmp_dir, tmp_filename, id='service_template_id')

        second_update_file = tempfile.mkstemp(dir=self.path)[1]
        with open(second_update_file, 'w') as f:
            f.write('fake context2')

        storage.service_template.upload(
            entry_id='service_template_id',
            source=second_update_file,
            path=os.path.basename(second_level_tmp_dir))

        assert os.path.isfile(os.path.join(
            self.path,
            'service_template',
            'service_template_id',
            os.path.basename(second_level_tmp_dir),
            os.path.basename(second_update_file)))

    def test_download_dir(self):
        storage = self._create_storage()
        self._create(storage)
        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        second_level_tmp_dir = tempfile.mkdtemp(dir=tmp_dir)
        tmp_filename = tempfile.mkstemp(dir=second_level_tmp_dir)[1]
        self._upload_dir(storage, tmp_dir, tmp_filename, id='service_template_id')

        temp_destination_dir = tempfile.mkdtemp(dir=self.path)
        storage.service_template.download(
            entry_id='service_template_id',
            destination=temp_destination_dir)

        destination_file_path = os.path.join(
            temp_destination_dir,
            os.path.basename(second_level_tmp_dir),
            os.path.basename(tmp_filename))

        assert os.path.isfile(destination_file_path)

        with open(destination_file_path) as f:
            assert f.read() == 'fake context'

    def test_data_dir(self):
        storage = self._create_storage()
        self._create(storage)

        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        tempfile.mkstemp(dir=tmp_dir)
        tempfile.mkstemp(dir=tmp_dir)

        storage.service_template.upload(entry_id='service_template_id', source=tmp_dir)

        with pytest.raises(exceptions.StorageError):
            storage.service_template.read(entry_id='service_template_id', path='')

    def test_delete_resource(self):
        storage = self._create_storage()
        self._create(storage)
        tmpfile_path = tempfile.mkstemp(suffix=self.__class__.__name__, dir=self.path)[1]
        self._upload(storage, tmpfile_path, 'service_template_id')
        tmpfile2_path = tempfile.mkstemp(suffix=self.__class__.__name__, dir=self.path)[1]
        self._upload(storage, tmpfile2_path, 'service_template_id')

        # deleting the first resource and expecting an error on read
        storage.service_template.delete(entry_id='service_template_id',
                                        path=os.path.basename(tmpfile_path))
        with pytest.raises(exceptions.StorageError):
            storage.service_template.read(entry_id='service_template_id',
                                          path=os.path.basename(tmpfile_path))
        # the second resource should still be available for reading
        assert storage.service_template.read(
            entry_id='service_template_id',
            path=os.path.basename(tmpfile2_path)) == 'fake context'

    def test_delete_directory(self):
        storage = self._create_storage()
        self._create(storage)
        temp_destination_dir = tempfile.mkdtemp(dir=self.path)

        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        second_level_tmp_dir = tempfile.mkdtemp(dir=tmp_dir)
        tmp_filename = tempfile.mkstemp(dir=second_level_tmp_dir)[1]
        self._upload_dir(storage, tmp_dir, tmp_filename, id='service_template_id')
        file_path_in_dir = os.path.join(
            os.path.basename(second_level_tmp_dir),
            os.path.basename(tmp_filename))

        # should be able to read the file and download the directory..
        assert storage.service_template.read(
            entry_id='service_template_id',
            path=file_path_in_dir) == 'fake context'
        storage.service_template.download(
            entry_id='service_template_id',
            path=os.path.basename(second_level_tmp_dir),
            destination=temp_destination_dir)

        # after deletion, the file and directory should both be gone
        storage.service_template.delete(
            entry_id='service_template_id',
            path=os.path.basename(second_level_tmp_dir))
        with pytest.raises(exceptions.StorageError):
            assert storage.service_template.read(
                entry_id='service_template_id',
                path=file_path_in_dir) == 'fake context'
        with pytest.raises(exceptions.StorageError):
            storage.service_template.download(
                entry_id='service_template_id',
                path=os.path.basename(second_level_tmp_dir),
                destination=temp_destination_dir)

    def test_delete_all_resources(self):
        storage = self._create_storage()
        self._create(storage)
        temp_destination_dir = tempfile.mkdtemp(dir=self.path)

        tmp_dir = tempfile.mkdtemp(suffix=self.__class__.__name__, dir=self.path)
        second_level_tmp_dir = tempfile.mkdtemp(dir=tmp_dir)
        tmp_filename = tempfile.mkstemp(dir=second_level_tmp_dir)[1]
        self._upload_dir(storage, tmp_dir, tmp_filename, id='service_template_id')
        file_path_in_dir = os.path.join(
            os.path.basename(second_level_tmp_dir),
            os.path.basename(tmp_filename))

        # deleting without specifying a path - delete all resources of this entry
        storage.service_template.delete(entry_id='service_template_id')
        with pytest.raises(exceptions.StorageError):
            assert storage.service_template.read(
                entry_id='service_template_id',
                path=file_path_in_dir) == 'fake context'
        with pytest.raises(exceptions.StorageError):
            storage.service_template.download(
                entry_id='service_template_id',
                path=os.path.basename(second_level_tmp_dir),
                destination=temp_destination_dir)

    def test_delete_nonexisting_resource(self):
        storage = self._create_storage()
        self._create(storage)
        # deleting a nonexisting resource - no effect is expected to happen
        assert storage.service_template.delete(entry_id='service_template_id',
                                               path='fake-file') is False
