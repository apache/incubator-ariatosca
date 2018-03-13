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
CLI ``type-definitions`` sub-commands.
"""
from aria import exceptions
from ..core import aria
from .. import service_template_utils
from .. import table

TYPE_DEFINITION_COLUMNS = \
    ('id', 'name', 'version', 'main_file_name', 'uploaded_at')


@aria.group(name='type-definitions')
@aria.options.verbose()
def type_definitions():
    """
    Manage type definitions
    """
    pass

@type_definitions.command(name='load',
                          short_help='Parse and load a type definition archive')
@aria.argument('type-definition-path')
@aria.options.verbose()
@aria.pass_type_definition_manager
@aria.pass_logger
def load(type_definition_path, type_definition_manager, logger):
    """
    Parse and store a type definition archive

    TYPE_DEFINITION_PATH is the path to the type definition archive.

    """
    logger.info('Loading type definition {0}...'.format(type_definition_path))
    valid_extension = ('.yaml', '.csar')
    if not type_definition_path.endswith(valid_extension):
        raise exceptions.\
            TypeDefinitionException('Type definition file has invalid extension')

    type_definition_file_path = service_template_utils.get(type_definition_path, None)
    type_definition = type_definition_manager.load_type_definition(type_definition_file_path)
    logger.info("Type definition loaded. The type definition's name is {0} and version is {1}".\
                format(type_definition.name, type_definition.version))

@type_definitions.command(name='list',
                          short_help='List all stored type definitions')
@aria.options.sort_by('uploaded_at')
@aria.options.descending
@aria.options.verbose()
@aria.pass_type_definition_manager
@aria.pass_logger
def list(sort_by, descending, type_definition_manager, logger):
    """
    List all stored type definitions
    """

    logger.info('Listing all type definitions...')
    type_definitions_list = type_definition_manager.list_type_definition(sort_by, descending)
    table.print_data(TYPE_DEFINITION_COLUMNS, type_definitions_list, 'Type definitions:')

@type_definitions.command(name='show',
                          short_help='Show information for a stored type definition')
@aria.argument('type-definition-name')
@aria.argument('type-definition-version')
@aria.options.verbose()
@aria.pass_type_definition_manager
@aria.pass_logger
def show(type_definition_name, type_definition_version, type_definition_manager, logger):
    """
    Show information for a stored type definition

    TYPE_DEFINITION_NAME is name of the stored type definition
    TYPE_DEFINITION_VERSION is version of the stored type definition
    """
    logger.info("Showing type definition name '{0}' version '{1}'...".\
                format(type_definition_name, type_definition_version))
    type_definition = type_definition_manager.get_type_definition(type_definition_name,\
                                                                  type_definition_version)
    table.print_data(TYPE_DEFINITION_COLUMNS, type_definition, 'Type definition:')

@type_definitions.command(name='delete',
                          short_help='Delete a stored type definition')
@aria.argument('type-definition-name')
@aria.argument('type-definition-version')
@aria.options.verbose()
@aria.pass_type_definition_manager
@aria.pass_logger
def delete(type_definition_name, type_definition_version, type_definition_manager, logger):
    """
    Delete a stored type definition

    TYPE_DEFINITION_NAME is name of the stored type definition
    TYPE_DEFINITION_VERSION is version of the stored type definition
    """
    logger.info("Deleting type definition name '{0}' version '{1}'...".\
                format(type_definition_name, type_definition_version))
    type_definition_manager.delete_type_definition(type_definition_name, type_definition_version)
    logger.info("Type definition name '{0}' version '{1}' deleted".\
                format(type_definition_name, type_definition_version))

@type_definitions.command(name='validate',
                          short_help='Validate a type definition archive')
@aria.argument('type-definition-path')
@aria.options.verbose()
@aria.pass_type_definition_manager
@aria.pass_logger
def validate(type_definition_path, type_definition_manager, logger):
    """
    Validate a type definition archive

    TYPE_DEFINITION_PATH is the path to the type definition archive.
    """
    logger.info('Validating type definition: {0}'.format(type_definition_path))
    valid_extension = ('.yaml', '.csar')
    if not type_definition_path.endswith(valid_extension):
        raise exceptions.\
            TypeDefinitionException('Type definition file has invalid extension')

    type_definition_file_path = service_template_utils.get(type_definition_path, None)
    type_definition_manager.validate_type_definition(type_definition_file_path)
    logger.info('Type definition validated successfully')
