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
import pytest
from tests.fixtures import (# pylint: disable=unused-import
    inmemory_model as model,
    type_definition_manager,
    type_definitions_dir
)
from aria.exceptions import(
    TypeDefinitionException,
    InvalidTypeDefinitionException,
    ParsingError,
    TypeDefinitionNotFoundException
    )
from tests.helpers import get_type_definition_uri # pylint: disable=ungrouped-imports
from aria.storage.exceptions import NotFoundError # pylint: disable=ungrouped-imports

TYPE_DEFINITION_NAME = 'test10'
TYPE_DEFINITION_VERSION = '1.0'
TYPE_DEFINITION_MAIN_FILE_NAME = 'type_definitions_main.yaml'

class TestTypeDefinitionManager(object):
    def test_load_type_definition(self, type_definition_manager, model, type_definitions_dir):
        type_definition = type_definition_manager.\
        load_type_definition(get_type_definition_uri('valid_type_definition', 'definitions', \
                                                     'type_definitions_main.yaml'))
        assert type_definition.name == TYPE_DEFINITION_NAME
        assert type_definition.version == TYPE_DEFINITION_VERSION
        assert type_definition.main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition == model.type_definition.get(type_definition.id)
        type_definition_dir = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format(TYPE_DEFINITION_NAME, TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir)
        assert type_definition_dir == type_definition_manager.\
        get_type_definition_dir(type_definition)

    def test_invalid_load_type_definition_with_no_file_exist(self, type_definition_manager):
        with pytest.raises(TypeDefinitionException) as excinfo:
            type_definition_manager.\
            load_type_definition(\
                                 get_type_definition_uri('valid_type_definition',\
                                                         'definitions', 'invalid'))
            assert str(excinfo.value) == 'Could not open/load type definition file'

    def test_invalid_load_type_definition_with_topology_template(self, type_definition_manager):
        with pytest.raises(InvalidTypeDefinitionException) as excinfo:
            type_definition_manager.\
            load_type_definition(\
                                 get_type_definition_uri(('invalid_type_definition_with_'
                                                          'topology_template'),\
                                                         'definitions',\
                                                         'type_definitions_main.yaml'))
            assert str(excinfo.value) == ("Type definition '{0}' with version '{1}' is invalid."
                                          " It contains topology template in '{2}'.").\
                                          format(TYPE_DEFINITION_MAIN_FILE_NAME,\
                                                 TYPE_DEFINITION_VERSION, 'inner_type1.yaml')

    def test_invalid_load_type_definition_with_no_metadata(self, type_definition_manager):
        with pytest.raises(InvalidTypeDefinitionException) as excinfo:
            type_definition_manager.\
            load_type_definition(\
                                 get_type_definition_uri('invalid_type_definition_with_no_metadata',
                                                         'definitions',\
                                                         'type_definitions_main.yaml'))
            assert str(excinfo.value) == ('Type definition is invalid.'
                                          ' It should have metadata information')

    def test_invalid_load_type_definition_with_parsing_error(self, type_definition_manager):
        with pytest.raises(ParsingError) as excinfo:
            type_definition_manager.\
            load_type_definition(\
                                 get_type_definition_uri(('invalid_type_definition_with_'
                                                          'parsing_error'),
                                                         'definitions',\
                                                         'type_definitions_main.yaml'))
            assert str(excinfo.value) == 'Failed to parse type definition'

    def test_get_type_definition(self, type_definition_manager, model, type_definitions_dir):
        type_definition_manager.\
        load_type_definition(get_type_definition_uri('valid_type_definition', 'definitions', \
                                                     'type_definitions_main.yaml'))
        type_definition = type_definition_manager.get_type_definition(TYPE_DEFINITION_NAME, \
                                                                      TYPE_DEFINITION_VERSION)
        assert type_definition.name == TYPE_DEFINITION_NAME
        assert type_definition.version == TYPE_DEFINITION_VERSION
        assert type_definition.main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition == model.type_definition.get(type_definition.id)
        type_definition_dir = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format(TYPE_DEFINITION_NAME, TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir)
        assert type_definition_dir == type_definition_manager.\
        get_type_definition_dir(type_definition)

    def test_get_type_definition_not_exist(self, type_definition_manager):
        with pytest.raises(NotFoundError):
            type_definition_manager.get_type_definition('test', '1.0')

    def test_delete_type_definition(self, type_definition_manager, model, type_definitions_dir):
        type_definition_manager.\
        load_type_definition(get_type_definition_uri('valid_type_definition', 'definitions', \
                                                     'type_definitions_main.yaml'))
        type_definition = type_definition_manager.\
        get_type_definition(TYPE_DEFINITION_NAME, TYPE_DEFINITION_VERSION)
        assert type_definition.name == TYPE_DEFINITION_NAME
        assert type_definition.version == TYPE_DEFINITION_VERSION
        assert type_definition.main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition == model.type_definition.get(type_definition.id)
        type_definition_dir = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format(TYPE_DEFINITION_NAME, TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir)
        assert type_definition_dir == type_definition_manager.\
        get_type_definition_dir(type_definition)
        type_definition_manager.\
        delete_type_definition(TYPE_DEFINITION_NAME, TYPE_DEFINITION_VERSION)
        with pytest.raises(NotFoundError):
            type_definition_manager.get_type_definition(TYPE_DEFINITION_NAME,\
                                                        TYPE_DEFINITION_VERSION)

    def test_delete_type_definition_not_exist(self, type_definition_manager):
        with pytest.raises(TypeDefinitionNotFoundException) as excinfo:
            type_definition_manager.delete_type_definition('test', '1.0')
            assert str(excinfo.value) == "Type definition name 'test' version '1.0' does not exist."

    def test_list_type_definition(self, type_definition_manager, model, type_definitions_dir):
        type_definition_manager.\
        load_type_definition(get_type_definition_uri('valid_type_definition', 'definitions', \
                                                     'type_definitions_main.yaml'))
        type_definition = type_definition_manager.\
        get_type_definition(TYPE_DEFINITION_NAME, TYPE_DEFINITION_VERSION)
        assert type_definition.name == TYPE_DEFINITION_NAME
        assert type_definition.version == TYPE_DEFINITION_VERSION
        assert type_definition.main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition == model.type_definition.get(type_definition.id)
        type_definition_dir = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format(TYPE_DEFINITION_NAME, TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir)
        assert type_definition_dir == type_definition_manager.\
        get_type_definition_dir(type_definition)
        type_definition_list = type_definition_manager.\
        list_type_definition(sort_by='uploaded_at', descending=False)
        assert type_definition_list[0].name == TYPE_DEFINITION_NAME
        assert type_definition_list[0].version == TYPE_DEFINITION_VERSION
        assert type_definition_list[0].main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition_list[0] == model.type_definition.get(type_definition.id)
        type_definition_dir = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format(TYPE_DEFINITION_NAME, \
                                                  TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir)
        assert type_definition_dir == type_definition_manager.\
        get_type_definition_dir(type_definition)

    def test_list_type_definition_sort_order(self, type_definition_manager,\
                                             model, type_definitions_dir):
        type_definition1 = type_definition_manager.\
        load_type_definition(get_type_definition_uri('valid_type_definition1', 'definitions', \
                                                     'type_definitions_main.yaml'))
        type_definition2 = type_definition_manager.\
        load_type_definition(get_type_definition_uri('valid_type_definition2', 'definitions', \
                                                     'type_definitions_main.yaml'))

        type_definition_list = type_definition_manager.\
        list_type_definition(sort_by='name', descending=True)

        assert type_definition_list[0].name == 'ball'
        assert type_definition_list[0].version == TYPE_DEFINITION_VERSION
        assert type_definition_list[0].main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition_list[0] == model.type_definition.get(type_definition2.id)
        type_definition_dir1 = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format('ball', \
                                                  TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir1)
        assert type_definition_dir1 == type_definition_manager.\
        get_type_definition_dir(type_definition2)

        assert type_definition_list[1].name == 'apple'
        assert type_definition_list[1].version == TYPE_DEFINITION_VERSION
        assert type_definition_list[1].main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition_list[1] == model.type_definition.get(type_definition1.id)
        type_definition_dir2 = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format('apple', \
                                                  TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir2)
        assert type_definition_dir2 == type_definition_manager.\
        get_type_definition_dir(type_definition1)

        type_definition_list = type_definition_manager.\
        list_type_definition(sort_by='uploaded_at', descending=False)

        assert type_definition_list[0].name == 'apple'
        assert type_definition_list[0].version == TYPE_DEFINITION_VERSION
        assert type_definition_list[0].main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition_list[0] == model.type_definition.get(type_definition1.id)
        type_definition_dir3 = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format('apple', \
                                                  TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir3)
        assert type_definition_dir3 == type_definition_manager.\
        get_type_definition_dir(type_definition1)

        assert type_definition_list[1].name == 'ball'
        assert type_definition_list[1].version == TYPE_DEFINITION_VERSION
        assert type_definition_list[1].main_file_name == TYPE_DEFINITION_MAIN_FILE_NAME
        assert type_definition_list[1] == model.type_definition.get(type_definition2.id)
        type_definition_dir4 = os.path.join(type_definitions_dir, '{0}-{1}'.\
                                           format('ball', \
                                                  TYPE_DEFINITION_VERSION))
        assert os.path.isdir(type_definition_dir4)
        assert type_definition_dir4 == type_definition_manager.\
        get_type_definition_dir(type_definition2)
