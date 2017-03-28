import pytest

from aria.cli import service_template_utils, csar
from aria.cli.env import _Environment
from aria.cli.exceptions import AriaCliError
from aria.core import Core
from aria.exceptions import AriaException
from aria.storage import exceptions as storage_exceptions
from tests.cli.base_test import TestCliBase, assert_exception_raised, raise_exception, mock_storage  # pylint: disable=unused-import


class TestServiceTemplatesShow(TestCliBase):

    def test_show_no_services_no_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates show no_services_no_description')

        assert 'Showing service template no_services_no_description...' in self.logger_output_string
        assert 'Description:' not in self.logger_output_string
        assert 'Existing services:\n[]' in self.logger_output_string

    def test_show_no_services_yes_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates show no_services_yes_description')

        assert 'Showing service template no_services_yes_description...' in \
               self.logger_output_string
        assert 'Description:\ntest_description' in self.logger_output_string
        assert 'Existing services:\n[]' in self.logger_output_string

    def test_show_one_service_no_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates show one_service_no_description')

        assert 'Showing service template one_service_no_description...' in self.logger_output_string
        assert 'Description:' not in self.logger_output_string
        assert "Existing services:\n['test_s']" in self.logger_output_string

    def test_show_one_service_yes_description(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates show one_service_yes_description')

        assert 'Showing service template one_service_yes_description...' in \
               self.logger_output_string
        assert 'Description:\ntest_description' in self.logger_output_string
        assert "Existing services:\n['test_s']" in self.logger_output_string


class TestServiceTemplatesList(TestCliBase):

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
        assert 'Listing all service templates...' in self.logger_output_string
        assert 'test_st' in self.logger_output_string


class TestServiceTemplatesStore(TestCliBase):

    def test_store_no_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(Core, 'create_service_template', mock_object)
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        self.invoke('service_templates store stubpath test_st')
        assert 'Storing service template test_st...' in self.logger_output_string
        assert 'Service template test_st stored' in self.logger_output_string

    def test_store_raises_exception_resulting_from_name_uniqueness(self, monkeypatch, mock_object):

        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(Core,
                            'create_service_template',
                            raise_exception(storage_exceptions.NotFoundError,
                                            msg='UNIQUE constraint failed'))

        assert_exception_raised(
            self.invoke('service_templates store stubpath test_st'),
            expected_exception=AriaCliError,
            expected_msg='Could not store service template `test_st`\n'
                         'There already a exists a service template with the same name')
        assert 'Storing service template test_st...' in self.logger_output_string

    def test_store_raises_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        monkeypatch.setattr(Core,
                            'create_service_template',
                            raise_exception(storage_exceptions.NotFoundError))

        assert_exception_raised(
            self.invoke('service_templates store stubpath test_st'),
            expected_exception=AriaCliError)
        assert 'Storing service template test_st...' in self.logger_output_string


class TestServiceTemplatesDelete(TestCliBase):

    def test_delete_no_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_object)
        monkeypatch.setattr(Core, 'delete_service_template', mock_object)
        self.invoke('service_templates delete test_st')
        assert 'Deleting service template test_st...' in self.logger_output_string
        assert 'Service template test_st deleted' in self.logger_output_string

    def test_delete_raises_exception(self, monkeypatch, mock_object):

        monkeypatch.setattr(_Environment, 'model_storage', mock_object)
        monkeypatch.setattr(Core,
                            'delete_service_template',
                            raise_exception(storage_exceptions.NotFoundError))

        assert_exception_raised(
            self.invoke('service_templates delete test_st'),
            expected_exception=AriaCliError,
            expected_msg='')
        assert 'Deleting service template test_st...' in self.logger_output_string


class TestServiceTemplatesInputs(TestCliBase):

    def test_inputs_existing_inputs(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates inputs with_inputs')
        assert 'Showing inputs for service template with_inputs...' in self.logger_output_string
        assert 'input1' in self.logger_output_string and 'value1' in self.logger_output_string

    def test_inputs_no_inputs(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('service_templates inputs without_inputs')
        assert 'Showing inputs for service template without_inputs...' in self.logger_output_string
        assert 'No inputs' in self.logger_output_string


class TestServiceTemplatesValidate(TestCliBase):

    def test_validate_no_exception(self, monkeypatch, mock_object):
        monkeypatch.setattr(Core, 'validate_service_template', mock_object)
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        self.invoke('service_templates validate stubpath')
        assert 'Validating service template: stubpath' in self.logger_output_string
        assert 'Service template validated successfully' in self.logger_output_string

    def test_validate_raises_exception(self, monkeypatch, mock_object):
        monkeypatch.setattr(Core, 'validate_service_template', raise_exception(AriaException))
        monkeypatch.setattr(service_template_utils, 'get', mock_object)
        assert_exception_raised(
            self.invoke('service_templates validate stubpath'),
            expected_exception=AriaCliError)
        assert 'Validating service template: stubpath' in self.logger_output_string


class TestServiceTemplatesCreateArchive(TestCliBase):

    def test_create_archive_successful(self, monkeypatch, mock_object):
        monkeypatch.setattr(csar, 'write', mock_object)
        self.invoke('service_templates create_archive stubpath stubdest')
        assert 'Creating a csar archive' in self.logger_output_string
        assert 'Csar archive created at stubdest' in self.logger_output_string
