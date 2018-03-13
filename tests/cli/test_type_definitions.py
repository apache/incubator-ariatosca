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
from aria.exceptions import (
    TypeDefinitionException,
    TypeDefinitionAlreadyExistsException,
    TypeDefinitionNotFoundException,
    AriaException
    )
from aria.cli.env import _Environment
from aria.storage import exceptions as storage_exceptions
from aria.type_definition_manager import TypeDefinitionManager
from aria.cli import service_template_utils
from ..mock import models as mock_models
from .base_test import ( # pylint: disable=unused-import
    TestCliBase,
    assert_exception_raised,
    raise_exception,
    mock_storage
)

class TestTypeDefinitionsLoad(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('type_definitions load stubpath.csar')
        assert 'Loading type definition stubpath.csar...' in self.logger_output_string

    def test_load_no_exception(self, monkeypatch, mock_object, mock_storage):

        monkeypatch.setattr(TypeDefinitionManager, 'load_type_definition', mock_object)
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(os.path, 'dirname', mock_object)
        self.invoke('type_definitions load stubpath.csar')
        assert 'Loading type definition stubpath.csar...' in self.logger_output_string
        assert 'Type definition loaded.' in self.logger_output_string

    def test_load_relative_path_single_yaml_file(self, monkeypatch, mock_object):

        monkeypatch.setattr(TypeDefinitionManager, 'load_type_definition', mock_object)
        monkeypatch.setattr(os.path, 'isfile', lambda x: True)
        monkeypatch.setattr(service_template_utils, '_is_archive', lambda x: False)

        self.invoke('type_definitions load stubpath.yaml')

        mock_object.assert_called_with(os.path.join(os.getcwd(), 'stubpath.yaml'))

    def test_load_raises_exception_resulting_from_name_uniqueness(self, monkeypatch, mock_object):

        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(TypeDefinitionManager,
                            'load_type_definition',
                            raise_exception(TypeDefinitionAlreadyExistsException,
                                            msg=("Type Definition '{0}' with version '{1}'"
                                                 " already exists.".\
                                                 format(mock_models.TYPE_DEFINITION_NAME,\
                                                        mock_models.TYPE_DEFINITION_VERSION))))
        monkeypatch.setattr(os.path, 'dirname', mock_object)

        assert_exception_raised(
            self.invoke('type_definitions load stubpath.yaml'),
            expected_exception=TypeDefinitionAlreadyExistsException,
            expected_msg=("Type Definition '{0}' with version '{1}' already exists.".\
            format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION)))

    def test_load_raises_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(TypeDefinitionManager,
                            'load_type_definition',
                            raise_exception(storage_exceptions.NotFoundError))
        monkeypatch.setattr(os.path, 'dirname', mock_object)

        assert_exception_raised(
            self.invoke('type_definitions load stubpath.yaml'),
            expected_exception=storage_exceptions.StorageError)

    def test_load_raises_invalid_format_exception(self):

        assert_exception_raised(
            self.invoke('type_definitions load stubpath'),
            expected_exception=TypeDefinitionException,
            expected_msg='Type definition file has invalid extension')

class TestTypeDefinitionsShow(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('type_definitions show {0} {1}'.\
                    format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION))
        assert "Showing type definition name '{0}' version '{1}'...".\
        format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION) in \
        self.logger_output_string

    def test_no_services_no_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('type_definitions show {0} {1}'.\
                    format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION))

        assert "Showing type definition name '{0}' version '{1}'...".\
        format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION) in \
        self.logger_output_string
        assert 'Description:' not in self.logger_output_string
        assert 'Existing services:' not in self.logger_output_string

    def test_details(self, monkeypatch, mock_storage, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        monkeypatch.setattr(mock_storage.type_definition, '_get_query', mock_object)
        self.invoke('type_definitions show {0} {1}'.\
                    format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION))

        assert "Showing type definition name '{0}' version '{1}'...".\
        format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION) in \
        self.logger_output_string
        assert 'id' in self.logger_output_string
        assert 'name' in self.logger_output_string
        assert 'version' in self.logger_output_string
        assert 'main_file_name' in self.logger_output_string
        assert 'uploaded_at' in self.logger_output_string

        assert mock_models.TYPE_DEFINITION_NAME in self.logger_output_string
        assert mock_models.TYPE_DEFINITION_VERSION in self.logger_output_string
        assert mock_models.TYPE_DEFINITION_MAIN_FILE_NAME in self.logger_output_string

class TestTypeDefinitionsList(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('type_definitions list')
        assert 'Listing all type definitions...' in self.logger_output_string

class TestTypeDefinitionsDelete(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('type_definitions delete {0} {1}'.\
                    format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION))
        assert "Deleting type definition name '{0}' version '{1}'...".\
        format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION) in \
        self.logger_output_string

    def test_delete_no_exception(self, monkeypatch, mock_storage, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        monkeypatch.setattr(TypeDefinitionManager, 'delete_type_definition', mock_object)
        self.invoke('type_definitions delete {0} {1}'.\
                    format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION))

        assert "Type definition name '{0}' version '{1}' deleted".\
        format(mock_models.TYPE_DEFINITION_NAME, mock_models.TYPE_DEFINITION_VERSION) in \
        self.logger_output_string

    def test_delete_raises_exception(self, monkeypatch):

        monkeypatch.setattr(TypeDefinitionManager,
                            'delete_type_definition',
                            raise_exception(storage_exceptions.StorageError))

        assert_exception_raised(
            self.invoke('type_definitions delete {0} {1}'.\
                        format(mock_models.TYPE_DEFINITION_NAME,\
                               mock_models.TYPE_DEFINITION_VERSION)),
            expected_exception=storage_exceptions.StorageError,
            expected_msg='')

    def test_delete_raises_not_found_exception(self, monkeypatch):

        monkeypatch.setattr(TypeDefinitionManager,
                            'delete_type_definition',
                            raise_exception(TypeDefinitionNotFoundException,
                                            msg='Type definition does not exist.'))

        assert_exception_raised(
            self.invoke('type_definitions delete {0} {1}'.\
                        format(mock_models.TYPE_DEFINITION_NAME,\
                               mock_models.TYPE_DEFINITION_VERSION)),
            expected_exception=TypeDefinitionNotFoundException,
            expected_msg='Type definition does not exist.')

class TestTypeDefinitionsValidate(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('type_definitions validate stubpath.csar')
        assert 'Validating type definition: stubpath.csar' in self.logger_output_string

    def test_validate_no_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(TypeDefinitionManager, 'validate_type_definition', mock_object)
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        self.invoke('type_definitions validate stubpath.csar')
        assert 'Type definition validated successfully' in self.logger_output_string

    def test_validate_raises_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(TypeDefinitionManager, 'validate_type_definition',\
                            raise_exception(AriaException))
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        assert_exception_raised(
            self.invoke('type_definitions validate stubpath.csar'),
            expected_exception=AriaException)

    def test_validate_raises_invalid_format_exception(self):

        assert_exception_raised(
            self.invoke('type_definitions load stubpath'),
            expected_exception=TypeDefinitionException,
            expected_msg='Type definition file has invalid extension')
