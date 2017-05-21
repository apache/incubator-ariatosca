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
import zipfile

import pytest
import mock

from aria.cli import service_template_utils, csar
from aria.cli.env import _Environment
from aria.core import Core
from aria.exceptions import AriaException
from aria.storage import exceptions as storage_exceptions

from .base_test import (  # pylint: disable=unused-import
    TestCliBase,
    assert_exception_raised,
    raise_exception,
    mock_storage
)
from ..mock import models as mock_models


class TestServiceTemplatesShow(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates show test_st')
        assert 'Showing service template test_st...' in self.logger_output_string

    def test_no_services_no_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates show test_st')

        assert 'Description:' not in self.logger_output_string
        assert 'Existing services:' not in self.logger_output_string

    def test_no_services_yes_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        st = mock_models.create_service_template(description='test_description')
        monkeypatch.setattr(mock_storage.service_template, 'get_by_name',
                            mock.MagicMock(return_value=st))

        self.invoke('service_templates show test_st')
        assert 'Description:' in self.logger_output_string
        assert 'test_description' in self.logger_output_string
        assert 'Existing services:' not in self.logger_output_string

    def test_one_service_no_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        st = mock_models.create_service_template()
        s = mock_models.create_service(st)
        st.services = {s.name: s}
        monkeypatch.setattr(mock_storage.service_template, 'get_by_name',
                            mock.MagicMock(return_value=st))

        self.invoke('service_templates show test_st')

        assert 'Description:' not in self.logger_output_string
        assert 'Existing services:' in self.logger_output_string
        assert mock_models.SERVICE_NAME in self.logger_output_string

    def test_one_service_yes_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        st = mock_models.create_service_template(description='test_description')
        s = mock_models.create_service(st)
        st.services = {s.name: s}
        monkeypatch.setattr(mock_storage.service_template, 'get_by_name',
                            mock.MagicMock(return_value=st))

        self.invoke('service_templates show test_st')

        assert 'Description:' in self.logger_output_string
        assert 'test_description' in self.logger_output_string
        assert 'Existing services:' in self.logger_output_string
        assert 'test_s' in self.logger_output_string


class TestServiceTemplatesList(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates list')
        assert 'Listing all service templates...' in self.logger_output_string

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'created_at', 'asc'),
        ('', ' --descending', 'created_at', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_all_sorting_combinations(self, monkeypatch, mock_storage, sort_by, order,
                                      sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates list{sort_by}{order}'.format(sort_by=sort_by, order=order))

        mock_storage.service_template.list.assert_called_with(
            sort={sort_by_in_output: order_in_output})
        assert mock_models.SERVICE_TEMPLATE_NAME in self.logger_output_string


class TestServiceTemplatesStore(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates store stubpath test_st')
        assert 'Storing service template test_st...' in self.logger_output_string

    def test_store_no_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(Core, 'create_service_template', mock_object)
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(os.path, 'dirname', mock_object)
        self.invoke('service_templates store stubpath {name}'.format(
            name=mock_models.SERVICE_TEMPLATE_NAME))
        assert 'Service template {name} stored'.format(
            name=mock_models.SERVICE_TEMPLATE_NAME) in self.logger_output_string

    def test_store_relative_path_single_yaml_file(self, monkeypatch, mock_object):
        monkeypatch.setattr(Core, 'create_service_template', mock_object)
        monkeypatch.setattr(os.path, 'isfile', lambda x: True)
        monkeypatch.setattr(service_template_utils, '_is_archive', lambda x: False)

        self.invoke('service_templates store service_template.yaml {name}'.format(
            name=mock_models.SERVICE_TEMPLATE_NAME))

        mock_object.assert_called_with(os.path.join(os.getcwd(), 'service_template.yaml'),
                                       mock.ANY,
                                       mock.ANY)

    def test_store_raises_exception_resulting_from_name_uniqueness(self, monkeypatch, mock_object):

        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(Core,
                            'create_service_template',
                            raise_exception(storage_exceptions.NotFoundError,
                                            msg='UNIQUE constraint failed'))
        monkeypatch.setattr(os.path, 'dirname', mock_object)

        assert_exception_raised(
            self.invoke('service_templates store stubpath test_st'),
            expected_exception=storage_exceptions.NotFoundError,
            expected_msg='There already a exists a service template with the same name')

    def test_store_raises_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(Core,
                            'create_service_template',
                            raise_exception(storage_exceptions.NotFoundError))
        monkeypatch.setattr(os.path, 'dirname', mock_object)

        assert_exception_raised(
            self.invoke('service_templates store stubpath test_st'),
            expected_exception=storage_exceptions.StorageError)


class TestServiceTemplatesDelete(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates delete test_st')
        assert 'Deleting service template test_st...' in self.logger_output_string

    def test_delete_no_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_object)
        monkeypatch.setattr(Core, 'delete_service_template', mock_object)
        self.invoke('service_templates delete {name}'.format(
            name=mock_models.SERVICE_TEMPLATE_NAME))
        assert 'Service template {name} deleted'.format(
            name=mock_models.SERVICE_TEMPLATE_NAME) in self.logger_output_string

    def test_delete_raises_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_object)
        monkeypatch.setattr(Core,
                            'delete_service_template',
                            raise_exception(storage_exceptions.StorageError))

        assert_exception_raised(
            self.invoke('service_templates delete test_st'),
            expected_exception=storage_exceptions.StorageError,
            expected_msg='')


class TestServiceTemplatesInputs(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates inputs test_st')
        assert 'Showing inputs for service template test_st...' in self.logger_output_string

    def test_inputs_existing_inputs(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        input = mock_models.create_input(name='input1', value='value1')
        st = mock_models.create_service_template(inputs={'input1': input})
        monkeypatch.setattr(mock_storage.service_template, 'get_by_name',
                            mock.MagicMock(return_value=st))

        self.invoke('service_templates inputs with_inputs')
        assert 'input1' in self.logger_output_string and 'value1' in self.logger_output_string

    def test_inputs_no_inputs(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates inputs without_inputs')
        assert 'No inputs' in self.logger_output_string


class TestServiceTemplatesValidate(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates validate stubpath')
        assert 'Validating service template: stubpath' in self.logger_output_string

    def test_validate_no_exception(self, monkeypatch, mock_object):
        monkeypatch.setattr(Core, 'validate_service_template', mock_object)
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        self.invoke('service_templates validate stubpath')
        assert 'Service template validated successfully' in self.logger_output_string

    def test_validate_raises_exception(self, monkeypatch, mock_object):
        monkeypatch.setattr(Core, 'validate_service_template', raise_exception(AriaException))
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        assert_exception_raised(
            self.invoke('service_templates validate stubpath'),
            expected_exception=AriaException)


class TestServiceTemplatesCreateArchive(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates create_archive stubpath stubdest')
        assert 'Creating a CSAR archive' in self.logger_output_string

    def test_create_archive_successful(self, monkeypatch, mock_object):
        monkeypatch.setattr(csar, 'write', mock_object)
        self.invoke('service_templates create_archive stubpath stubdest')
        assert 'CSAR archive created at stubdest' in self.logger_output_string

    def test_create_archive_from_relative_path(self, monkeypatch, mock_object):

        monkeypatch.setattr(os.path, 'isfile', mock_object)
        monkeypatch.setattr(zipfile, 'ZipFile', mock.MagicMock)

        self.invoke('service_templates create_archive archive stubdest')
        mock_object.assert_called_with(os.path.join(os.getcwd(), 'archive'))
