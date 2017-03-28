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

from .base_test import (  # pylint: disable=unused-import
    TestCliBase,
    mock_storage
)
from ..mock import models as mock_models


class TestNodesShow(TestCliBase):

    def test_header_strings(self, monkeypatch, mock_storage):
        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('nodes show 1')
        assert 'Showing node 1' in self.logger_output_string
        assert 'Node:' in self.logger_output_string
        assert 'Node attributes:' in self.logger_output_string

    def test_no_attributes(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('nodes show 2')
        assert 'No attributes' in self.logger_output_string
        assert 'attribute1' not in self.logger_output_string
        assert 'value1' not in self.logger_output_string

    def test_one_attribute(self, monkeypatch, mock_storage):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        m = mock.MagicMock(
            return_value=mock_models.create_node_with_dependencies(include_attribute=True))
        monkeypatch.setattr(mock_storage.node, 'get', m)
        self.invoke('nodes show 3')
        assert 'No attributes' not in self.logger_output_string
        assert 'attribute1' in self.logger_output_string
        assert 'value1' in self.logger_output_string


class TestNodesList(TestCliBase):

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'service_name', 'asc'),
        ('', ' --descending', 'service_name', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_list_specified_service(self, monkeypatch, mock_storage, sort_by, order,
                                    sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('nodes list -s test_s{sort_by}{order}'.format(sort_by=sort_by,
                                                                  order=order))
        assert 'Listing nodes for service test_s...' in self.logger_output_string
        assert 'Listing all nodes...' not in self.logger_output_string

        nodes_list = mock_storage.node.list
        nodes_list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                           filters={'service': mock.ANY})
        assert 'Nodes:' in self.logger_output_string
        assert 'test_s' in self.logger_output_string
        assert 'test_n' in self.logger_output_string

    @pytest.mark.parametrize('sort_by, order, sort_by_in_output, order_in_output', [
        ('', '', 'service_name', 'asc'),
        ('', ' --descending', 'service_name', 'desc'),
        (' --sort-by name', '', 'name', 'asc'),
        (' --sort-by name', ' --descending', 'name', 'desc')
    ])
    def test_list_no_specified_service(self, monkeypatch, mock_storage, sort_by, order,
                                       sort_by_in_output, order_in_output):

        monkeypatch.setattr(_Environment, 'model_storage', mock_storage)
        self.invoke('nodes list{sort_by}{order}'.format(sort_by=sort_by,
                                                        order=order))
        assert 'Listing nodes for service test_s...' not in self.logger_output_string
        assert 'Listing all nodes...' in self.logger_output_string

        nodes_list = mock_storage.node.list
        nodes_list.assert_called_once_with(sort={sort_by_in_output: order_in_output},
                                           filters={})
        assert 'Nodes:' in self.logger_output_string
        assert 'test_s' in self.logger_output_string
        assert 'test_n' in self.logger_output_string
