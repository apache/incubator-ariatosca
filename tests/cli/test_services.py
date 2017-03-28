import pytest
from mock import ANY
from aria.cli.exceptions import AriaCliError
from aria.cli.env import _Environment
from aria.core import Core
from aria.exceptions import (AriaException, DependentActiveExecutionsError,
                             DependentAvailableNodesError)
from aria.storage import exceptions as storage_exceptions
from tests.cli.base_test import TestCliBase, raise_exception, assert_exception_raised, mock_storage  #pylint: disable=unused-import
from tests.mock.models import create_service, create_service_template


class TestServicesList(TestCliBase):

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'created_at', 'asc'),
        ('', ' --descending', 'created_at', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_list_no_specified_service_template(self, monkeypatch, mock_storage, sort_by, order,
                                                sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services list{sort_by}{order}'.format(sort_by=sort_by, order=order))
        assert 'Listing all services...' in self.logger_output_string
        assert 'Listing services for service template' not in self.logger_output_string

        mock_storage.service.list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                                          filters={})
        assert 'Services:' in self.logger_output_string
        assert 'test_st' in self.logger_output_string
        assert 'test_s' in self.logger_output_string

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'created_at', 'asc'),
        ('', ' --descending', 'created_at', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_list_specified_service_template(self, monkeypatch, mock_storage, sort_by, order,
                                             sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services list -t test_st{sort_by}{order}'.format(sort_by=sort_by, order=order))
        assert 'Listing services for service template test_st...' in self.logger_output_string
        assert 'Listing all services...' not in self.logger_output_string

        mock_storage.service.list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                                          filters={'service_template': ANY})
        assert 'Services:' in self.logger_output_string
        assert 'test_st' in self.logger_output_string
        assert 'test_s' in self.logger_output_string


class TestServicesCreate(TestCliBase):

    def test_create_no_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_object)

        test_st = create_service_template('test_st')
        mock_object.return_value = create_service(test_st, 'test_s')
        monkeypatch.setattr(Core, 'create_service', mock_object)
        self.invoke('services create -t test_st test_s')

        assert 'Creating new service from service template test_st...' in self.logger_output_string
        assert "Service created. The service's name is test_s" in self.logger_output_string

    def test_store_raises_storage_error_resulting_from_name_uniqueness(self, monkeypatch,
                                                                       mock_object):
        monkeypatch.setattr(_Environment, 'model_storage', mock_object)
        monkeypatch.setattr(Core,
                            'create_service',
                            raise_exception(storage_exceptions.NotFoundError,
                                            msg='UNIQUE constraint failed'))
        assert_exception_raised(
            self.invoke('services create -t test_st test_s'),
            expected_exception=AriaCliError,
            expected_msg='Could not store service `test_s`\n'
                         'There already a exists a service with the same name')

        assert 'Creating new service from service template test_st...' in self.logger_output_string
        assert "Service created. The service's name is test_s" not in self.logger_output_string

    def test_store_raises_other_storage_error(self, monkeypatch, mock_object):
        monkeypatch.setattr(_Environment, 'model_storage', mock_object)
        monkeypatch.setattr(Core,
                            'create_service',
                            raise_exception(storage_exceptions.NotFoundError))

        assert_exception_raised(
            self.invoke('services create -t test_st test_s'),
            expected_exception=AriaCliError)

        assert 'Creating new service from service template test_st...' in self.logger_output_string
        assert "Service created. The service's name is test_s" not in self.logger_output_string

    def test_store_raises_aria_exception(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        monkeypatch.setattr(Core,
                            'create_service',
                            raise_exception(AriaException, msg='error creating service `test_s`'))

        assert_exception_raised(
            self.invoke('services create -t with_inputs test_s'),
            expected_exception=AriaCliError,
            expected_msg='error creating service `test_s`')

        assert 'Creating new service from service template with_inputs...' in \
               self.logger_output_string
        assert 'error creating service `test_s`' in self.logger_output_string
        assert 'input1' in self.logger_output_string and 'value1' in self.logger_output_string
        assert "Service created. The service's name is test_s" not in self.logger_output_string


class TestServicesDelete(TestCliBase):

    def test_delete_no_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_object)
        monkeypatch.setattr(Core, 'delete_service', mock_object)
        self.invoke('services delete test_s')
        assert 'Deleting service test_s...' in self.logger_output_string
        assert 'Service test_s deleted' in self.logger_output_string

    def test_delete_active_execution_error(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        assert_exception_raised(
            self.invoke('services delete service_with_active_executions'),
            expected_exception=DependentActiveExecutionsError,
            expected_msg="Can't delete service test_s - there is an active "
                         "execution for this service. Active execution id: 1"
        )
        assert 'Deleting service service_with_active_executions...' in self.logger_output_string

    def test_delete_available_nodes_error(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        assert_exception_raised(
            self.invoke('services delete service_with_available_nodes'),
            expected_exception=DependentAvailableNodesError,
            expected_msg="Can't delete service test_s - "
                         "there are available nodes for this service. Available node ids: 1"
        )
        assert 'Deleting service service_with_available_nodes...' in self.logger_output_string

    def test_delete_available_nodes_error_with_force(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services delete service_with_available_nodes --force')

        assert mock_storage.service.delete.call_count == 1
        assert 'Deleting service service_with_available_nodes...' in self.logger_output_string
        assert 'Service service_with_available_nodes deleted' in self.logger_output_string

class TestServicesOutputs(TestCliBase):
    pass


class TestServicesInputs(TestCliBase):

    def test_inputs_no_inputs(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services inputs service_with_no_inputs')

        assert 'Showing inputs for service service_with_no_inputs...' in self.logger_output_string
        assert 'No inputs' in self.logger_output_string
        assert 'input1' not in self.logger_output_string
        assert 'value1' not in self.logger_output_string

    def test_inputs_one_input(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('services inputs service_with_one_input')

        assert 'Showing inputs for service service_with_one_input...' in self.logger_output_string
        assert 'input1' in self.logger_output_string
        assert 'value1' in self.logger_output_string
        assert 'No inputs' not in self.logger_output_string
