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

import pytest
import mock

from aria.cli.env import _Environment
from aria.core import Core
from aria.exceptions import DependentActiveExecutionsError, DependentAvailableNodesError
from aria.modeling.exceptions import ParameterException
from aria.storage import exceptions as storage_exceptions

from .base_test import (  # pylint: disable=unused-import
    TestCliBase,
    raise_exception,
    assert_exception_raised,
    mock_storage
)
from ..mock import models as mock_models


class TestServicesList(TestCliBase):

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'created_at', 'asc'),
        ('', ' --descending', 'created_at', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_no_specified_service_template(self, monkeypatch, mock_storage, sort_by, order,
                                           sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services list{sort_by}{order}'.format(sort_by=sort_by, order=order))
        assert 'Listing all services...' in self.logger_output_string
        assert 'Listing services for service template' not in self.logger_output_string

        mock_storage.service.list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                                          filters={})
        assert 'Services:' in self.logger_output_string
        assert mock_models.SERVICE_TEMPLATE_NAME in self.logger_output_string
        assert mock_models.SERVICE_NAME in self.logger_output_string

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'created_at', 'asc'),
        ('', ' --descending', 'created_at', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_specified_service_template(self, monkeypatch, mock_storage, sort_by, order,
                                        sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services list -t test_st{sort_by}{order}'.format(sort_by=sort_by, order=order))
        assert 'Listing services for service template test_st...' in self.logger_output_string
        assert 'Listing all services...' not in self.logger_output_string

        mock_storage.service.list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                                          filters={'service_template': mock.ANY})
        assert 'Services:' in self.logger_output_string
        assert mock_models.SERVICE_TEMPLATE_NAME in self.logger_output_string
        assert mock_models.SERVICE_NAME in self.logger_output_string


class TestServicesCreate(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services create -t test_st test_s')
        assert 'Creating new service from service template test_st...' in self.logger_output_string

    def test_no_exception(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)

        m = mock.MagicMock(return_value=mock_models.create_service_with_dependencies())
        monkeypatch.setattr(Core, 'create_service', m)
        self.invoke('services create -t test_st test_s')
        assert "Service created. The service's name is test_s" in self.logger_output_string

    def test_raises_storage_error_resulting_from_name_uniqueness(self, monkeypatch,
                                                                 mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        monkeypatch.setattr(Core,
                            'create_service',
                            raise_exception(storage_exceptions.NotFoundError,
                                            msg='UNIQUE constraint failed'))
        assert_exception_raised(
            self.invoke('services create -t test_st test_s'),
            expected_exception=storage_exceptions.NotFoundError,
            expected_msg='There already a exists a service with the same name')

        assert "Service created. The service's name is test_s" not in self.logger_output_string

    def test_raises_other_storage_error(self, monkeypatch, mock_object):
        monkeypatch.setattr(_Environment, 'model_storage', mock_object)
        monkeypatch.setattr(Core,
                            'create_service',
                            raise_exception(storage_exceptions.NotFoundError))

        assert_exception_raised(
            self.invoke('services create -t test_st test_s'),
            expected_exception=storage_exceptions.NotFoundError)

        assert "Service created. The service's name is test_s" not in self.logger_output_string

    def test_raises_inputs_exception(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        monkeypatch.setattr(Core,
                            'create_service',
                            raise_exception(ParameterException))

        assert_exception_raised(
            self.invoke('services create -t with_inputs test_s'),
            expected_exception=ParameterException)

        assert "Service created. The service's name is test_s" not in self.logger_output_string


class TestServicesDelete(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services delete test_s')
        assert 'Deleting service test_s...' in self.logger_output_string

    def test_delete_no_exception(self, monkeypatch, mock_storage, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        monkeypatch.setattr(Core, 'delete_service', mock_object)
        self.invoke('services delete test_s')
        assert 'Service test_s deleted' in self.logger_output_string

    def test_delete_active_execution_error(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        mock_service_with_execution = \
            mock.MagicMock(return_value=mock_models.create_service_with_dependencies(
                include_execution=True))
        monkeypatch.setattr(mock_storage.service, 'get', mock_service_with_execution)
        assert_exception_raised(
            self.invoke('services delete test_s'),
            expected_exception=DependentActiveExecutionsError,
            expected_msg="Can't delete service `{name}` - there is an active execution "
                         "for this service. Active execution ID: 1".format(
                             name=mock_models.SERVICE_NAME))

    def test_delete_available_nodes_error(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        assert_exception_raised(
            self.invoke('services delete test_s'),
            expected_exception=DependentAvailableNodesError,
            expected_msg="Can't delete service `{name}` - there are available nodes "
                         "for this service. Available node IDs: 1".format(
                             name=mock_models.SERVICE_NAME))

    def test_delete_available_nodes_error_with_force(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services delete service_with_available_nodes --force')

        assert mock_storage.service.delete.call_count == 1
        assert 'Service service_with_available_nodes deleted' in self.logger_output_string


class TestServicesOutputs(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services outputs test_s')
        assert 'Showing outputs for service test_s...' in self.logger_output_string

    def test_outputs_no_outputs(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services outputs service_with_no_outputs')

        assert 'No outputs' in self.logger_output_string
        assert 'output1' not in self.logger_output_string
        assert 'value1' not in self.logger_output_string

    def test_outputs_one_output(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        s = mock_models.create_service_with_dependencies(include_output=True)
        monkeypatch.setattr(mock_storage.service, 'get_by_name', mock.MagicMock(return_value=s))

        self.invoke('services outputs test_s')

        assert 'output1' in self.logger_output_string
        assert 'value1' in self.logger_output_string
        assert 'No outputs' not in self.logger_output_string


class TestServicesInputs(TestCliBase):

    def test_header_string(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services inputs test_s')
        assert 'Showing inputs for service test_s...' in self.logger_output_string

    def test_inputs_no_inputs(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services inputs service_with_no_inputs')

        assert 'No inputs' in self.logger_output_string
        assert 'input1' not in self.logger_output_string
        assert 'value1' not in self.logger_output_string

    def test_inputs_one_input(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        s = mock_models.create_service_with_dependencies(include_input=True)
        monkeypatch.setattr(mock_storage.service, 'get_by_name', mock.MagicMock(return_value=s))

        self.invoke('services inputs test_s')

        assert 'input1' in self.logger_output_string
        assert 'value1' in self.logger_output_string
        assert 'No inputs' not in self.logger_output_string
