from mock import ANY
import pytest

from aria.cli.env import _Environment
from tests.cli.base_test import TestCliBase, mock_storage  # pylint: disable=unused-import


class TestNodeTemplatesShow(TestCliBase):

    def test_no_properties_no_nodes(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('node_templates show 1')
        assert 'Showing node template 1' in self.logger_output_string
        assert 'Node template properties:' in self.logger_output_string
        assert 'No properties' in self.logger_output_string
        assert 'prop1' not in self.logger_output_string
        assert 'value1' not in self.logger_output_string
        assert 'No nodes' in self.logger_output_string
        assert 'node1' not in self.logger_output_string

    def test_one_property_no_nodes(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('node_templates show 2')
        assert 'Showing node template 2' in self.logger_output_string
        assert 'Node template properties:' in self.logger_output_string
        assert 'No properties' not in self.logger_output_string
        assert 'prop1' in self.logger_output_string and 'value1' in self.logger_output_string
        assert 'No nodes' in self.logger_output_string
        assert 'node1' not in self.logger_output_string

    def test_no_properties_one_node(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('node_templates show 3')
        assert 'Showing node template 3' in self.logger_output_string
        assert 'Node template properties:' in self.logger_output_string
        assert 'No properties' in self.logger_output_string
        assert 'prop1' not in self.logger_output_string
        assert 'value1' not in self.logger_output_string
        assert 'No nodes' not in self.logger_output_string
        assert 'node1' in self.logger_output_string

    def test_one_property_one_node(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('node_templates show 4')
        assert 'Showing node template 4' in self.logger_output_string
        assert 'Node template properties:' in self.logger_output_string
        assert 'No properties' not in self.logger_output_string
        assert 'prop1' in self.logger_output_string and 'value1' in self.logger_output_string
        assert 'No nodes' not in self.logger_output_string
        assert 'node1' in self.logger_output_string


class TestNodeTemplatesList(TestCliBase):

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'service_template_name', 'asc'),
        ('', ' --descending', 'service_template_name', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_list_specified_service_template(self, monkeypatch, mock_storage, sort_by, order,
                                             sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('node_templates list -t test_st{sort_by}{order}'.format(sort_by=sort_by,
                                                                            order=order))
        assert 'Listing node templates for service template test_st...' in self.logger_output_string
        assert 'Listing all node templates...' not in self.logger_output_string

        node_templates_list = mock_storage.node_template.list
        node_templates_list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                                    filters={'service_template': ANY})
        assert 'Node templates:' in self.logger_output_string
        assert 'test_st' in self.logger_output_string
        assert 'test_nt' in self.logger_output_string

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'service_template_name', 'asc'),
        ('', ' --descending', 'service_template_name', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_list_no_specified_service_template(self, monkeypatch, mock_storage, sort_by, order,
                                                sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('node_templates list{sort_by}{order}'.format(sort_by=sort_by, order=order))
        assert 'Listing all node templates...' in self.logger_output_string
        assert 'Listing node templates for service template test_st...' not in \
               self.logger_output_string

        node_templates_list = mock_storage.node_template.list
        node_templates_list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                                    filters={})
        assert 'Node templates:' in self.logger_output_string
        assert 'test_st' in self.logger_output_string
        assert 'test_nt' in self.logger_output_string
