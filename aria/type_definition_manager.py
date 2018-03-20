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

"""
Type Definition management.
"""
from datetime import datetime
import os
from distutils import dir_util  # pylint: disable=no-name-in-module
from aria.utils.yaml import yaml
from aria.utils import collections
from aria.exceptions import (
    ParsingError,
    TypeDefinitionException,
    TypeDefinitionAlreadyExistsException,
    TypeDefinitionNotFoundException,
    InvalidTypeDefinitionException
    )
from aria.parser import consumption
from aria.parser.loading.location import UriLocation

class TypeDefinitionManager(object):
    """TypeDefinitionManager class handles the type definition related management"""

    def __init__(self, model_storage, type_definitions_dir):
        """
        :param model_storage: model storage object
        :param type_definitions_dir: root directory in which to load type definitions
        """
        self._model_storage = model_storage
        self._type_definitions_dir = type_definitions_dir

    @property
    def model_storage(self):
        """Return model storage object"""
        return self._model_storage

    def load_type_definition(self, type_definition_path):
        """
        Load a type definition into model as well as into file system.
        """
        type_definition = self.create_type_definition(type_definition_path)

        return type_definition

    def get_type_definition(self, type_definition_name, type_definition_version):
        """
        Get type definition details based on name and version
        """
        type_definition_query = self._model_storage.type_definition.\
        _get_query(None, {'name': type_definition_name, 'version': type_definition_version},\
                   None)
        type_definition_id = type_definition_query.value('id')
        type_definition = self._model_storage.type_definition.get(type_definition_id)
        return type_definition

    def delete_type_definition(self, type_definition_name, type_definition_version):
        """
        Delete a type definition from model as well as from file system
        """
        try:
            type_definition_query = self._model_storage.type_definition.\
            _get_query(None, {'name': type_definition_name, 'version': type_definition_version},
                       None)
            type_definition_id = type_definition_query.value('id')

            if type_definition_id is None:
                raise TypeDefinitionNotFoundException("Type definition name '{0}' version '{1}' "
                                                      "does not exist.".\
                                                      format(type_definition_name,\
                                                             type_definition_version))
            else:
                type_definition = self._model_storage.type_definition.get(type_definition_id)
                type_def_dir = self.get_type_definition_dir(type_definition)

                if os.path.exists(type_def_dir) and os.path.isdir(type_def_dir):
                    dir_util.remove_tree(type_def_dir)

                self._model_storage.type_definition.delete(type_definition)
        except Exception, e:
            raise e

    def list_type_definition(self, sort_by, descending):
        """Lists the type definitions that are loaded"""
        type_definitions_list = self._model_storage.type_definition.list(
            sort={sort_by: 'desc' if descending else 'asc'})
        return type_definitions_list

    def get_type_definition_dir(self, type_definition_object):
        """
        Get the particular type definition's file system directory.
        """
        return os.path.join(self._type_definitions_dir,
                            '{0}-{1}'.format(type_definition_object.name,
                                             type_definition_object.version))

    def create_type_definition(self, type_definition_path):

        """validates & stores the type definition file/csar into model & resource storage"""

        context = self.validate_type_definition(type_definition_path)
        service_template = context.modeling.template

        metadata = service_template.meta_data
        template_name = metadata['template_name'].value
        template_version = metadata['template_version'].value.value
        main_file_name = service_template.main_file_name

        cls = self._model_storage.type_definition.model_cls
        type_definition = cls(
            name=template_name,
            version=template_version,
            main_file_name=main_file_name,
            uploaded_at=datetime.now()
        )
        number_of_rows_matched = len(self._model_storage.type_definition.list \
                                     (filters={'name': type_definition.name,
                                               'version': type_definition.version}))
        if number_of_rows_matched:
            raise TypeDefinitionAlreadyExistsException(
                "Type Definition '{0}' with version '{1}' already exists".format(
                    type_definition.name, type_definition.version))

        type_definition_directory = self.get_type_definition_dir(type_definition)
        if os.path.exists(type_definition_directory):
            raise TypeDefinitionAlreadyExistsException(
                ("Type Definition '{0}' with version '{1}' already exists").
                format(type_definition.name, type_definition.version))

        try:
            os.mkdir(type_definition_directory)
            type_def_src_dir = os.path.dirname(type_definition_path)
            dir_util.copy_tree(type_def_src_dir, type_definition_directory)
        except (IOError, OSError):
            raise \
                TypeDefinitionException("Could not store type definition into directory")

        self._model_storage.type_definition.put(type_definition)

        return type_definition

    def validate_type_definition(self, type_definition_path):
        """ Validates the provided type definition archive"""
        try:
            with open(type_definition_path, 'r') as type_definition_yaml_file:
                type_definition_yaml = yaml.load(type_definition_yaml_file)
        except (IOError, OSError) as e:
            raise \
                TypeDefinitionException("Could not open/load type definition file", e)

        if ('metadata' not in type_definition_yaml) or \
           ('template_name' not in type_definition_yaml['metadata']) or \
           ('template_version' not in type_definition_yaml['metadata']):
            raise InvalidTypeDefinitionException('Type definition is invalid. '
                                                 'It should have metadata information')

        name = type_definition_yaml['metadata']['template_name']
        version = type_definition_yaml['metadata']['template_version']
        try:
            TypeDefinitionManager._check_topology_template_exists(type_definition_path, \
                                                                  type_definition_yaml, \
                                                                  name, version)
        except InvalidTypeDefinitionException as e:
            raise e
        except TypeDefinitionException as e:
            raise e
        except Exception as e:
            raise e

        type_definitions_dir = (self._type_definitions_dir).split()
        context = consumption.ConsumptionContext()
        context.presentation.location = UriLocation(type_definition_path)
        context.loading.prefixes = collections.StrictList(type_definitions_dir)
        consumption.ConsumerChain(
            context,
            (
                consumption.Read,
                consumption.Validate,
                consumption.ServiceTemplate
            )).consume()
        if context.validation.dump_issues():
            raise ParsingError('Failed to parse type definition')
        return context

    @staticmethod
    def _check_topology_template_exists(td_path, td_yaml, main_td_name, main_td_version):

        if 'topology_template' in td_yaml:
            td_file_name = os.path.split(td_path)[1]
            error_message = ("Type definition '{0}' with version '{1}' is invalid."
                             " It contains topology template in '{2}'.").\
                             format(main_td_name, main_td_version, td_file_name)
            raise InvalidTypeDefinitionException(error_message)

        if 'imports' not in td_yaml:
            return

        main_type_definition_dir = os.path.dirname(td_path)
        for td_import_file in td_yaml['imports']:
            try:
                td_import_file_path = os.path.join(main_type_definition_dir, td_import_file or ' ')
                with open(td_import_file_path, 'r') as td_yaml_file:
                    td_import_yaml = yaml.load(td_yaml_file)
                    TypeDefinitionManager.\
                    _check_topology_template_exists(td_import_file_path, td_import_yaml,\
                                                     main_td_name, main_td_version)
            except (IOError, OSError) as e:
                raise TypeDefinitionException("Could not open/load type definition file",\
                                                     e.message)
            except InvalidTypeDefinitionException as e:
                raise e
            except Exception as e:
                raise TypeDefinitionException("Failed to parse type definition")
