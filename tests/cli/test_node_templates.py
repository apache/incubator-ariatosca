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
from mock import ANY, MagicMock

from aria.cli.env import _Environment

from .base_test import (                                                                            # pylint: disable=unused-import
    TestCliBase,
    mock_storage
)
from ..mock import models as mock_models


class TestNodeTemplatesShow(TestCliBase):

    def test_header_strings(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('node_templates show 1')
        assert 'Showing node template 1' in self.logger_output_string
        assert 'Node template properties:' in self.logger_output_string
        assert 'Nodes:' in self.logger_output_string

    def test_no_properties_no_nodes(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('node_templates show 1')

        assert 'No properties' in self.logger_output_string
        assert 'prop1' not in self.logger_output_string
        assert 'value1' not in self.logger_output_string
        assert 'No nodes' in self.logger_output_string
        assert mock_models.NODE_NAME not in self.logger_output_string

    def test_one_property_no_nodes(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        m = MagicMock(return_value=mock_models.create_node_template_with_dependencies(
            include_property=True))
        monkeypatch.setattr(mock_storage.node_template, 'get', m)
        self.invoke('node_templates show 2')
        assert 'No properties' not in self.logger_output_string
        assert 'prop1' in self.logger_output_string and 'value1' in self.logger_output_string
        assert 'No nodes' in self.logger_output_string
        assert mock_models.NODE_NAME not in self.logger_output_string

    def test_no_properties_one_node(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        m = MagicMock(return_value=mock_models.create_node_template_with_dependencies(
            include_node=True))
        monkeypatch.setattr(mock_storage.node_template, 'get', m)
        self.invoke('node_templates show 3')
        assert 'No properties' in self.logger_output_string
        assert 'prop1' not in self.logger_output_string
        assert 'value1' not in self.logger_output_string
        assert 'No nodes' not in self.logger_output_string
        assert mock_models.NODE_NAME in self.logger_output_string

    def test_one_property_one_node(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        m = MagicMock(return_value=mock_models.create_node_template_with_dependencies(
            include_node=True, include_property=True))
        monkeypatch.setattr(mock_storage.node_template, 'get', m)
        self.invoke('node_templates show 4')
        assert 'No properties' not in self.logger_output_string
        assert 'prop1' in self.logger_output_string and 'value1' in self.logger_output_string
        assert 'No nodes' not in self.logger_output_string
        assert mock_models.NODE_NAME in self.logger_output_string


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
        self.invoke('node_templates list -t {service_template_name}{sort_by}{order}'
                    .format(service_template_name=mock_models.SERVICE_TEMPLATE_NAME,
                            sort_by=sort_by,
                            order=order))
        assert 'Listing node templates for service template {name}...'\
               .format(name=mock_models.SERVICE_TEMPLATE_NAME) in self.logger_output_string
        assert 'Listing all node templates...' not in self.logger_output_string

        node_templates_list = mock_storage.node_template.list
        node_templates_list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                                    filters={'service_template': ANY})
        assert 'Node templates:' in self.logger_output_string
        assert mock_models.SERVICE_TEMPLATE_NAME in self.logger_output_string
        assert mock_models.NODE_TEMPLATE_NAME in self.logger_output_string

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
        assert 'Listing node templates for service template {name}...'\
               .format(name=mock_models.SERVICE_TEMPLATE_NAME) not in self.logger_output_string

        node_templates_list = mock_storage.node_template.list
        node_templates_list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                                    filters={})
        assert 'Node templates:' in self.logger_output_string
        assert mock_models.SERVICE_TEMPLATE_NAME in self.logger_output_string
        assert mock_models.NODE_TEMPLATE_NAME in self.logger_output_string
