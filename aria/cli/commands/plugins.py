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

from .. import table
from .. import utils
from ..core import aria


PLUGIN_COLUMNS = ['id', 'package_name', 'package_version', 'supported_platform',
                  'distribution', 'distribution_release', 'uploaded_at']


@aria.group(name='plugins')
@aria.options.verbose()
def plugins():
    """Handle plugins
    """
    pass


@plugins.command(name='validate',
                 short_help='Validate a plugin')
@aria.argument('plugin-path')
@aria.options.verbose()
@aria.pass_plugin_manager
@aria.pass_logger
def validate(plugin_path, plugin_manager, logger):
    """Validate a plugin archive

    A valid plugin is a wagon (http://github.com/cloudify-cosmo/wagon)
    in the zip format (suffix may also be .wgn).

    `PLUGIN_PATH` is the path to wagon archive to validate.
    """
    logger.info('Validating plugin {0}...'.format(plugin_path))
    plugin_manager.validate_plugin(plugin_path)
    logger.info('Plugin validated successfully')


@plugins.command(name='install',
                 short_help='Install a plugin')
@aria.argument('plugin-path')
@aria.options.verbose()
@aria.pass_context
@aria.pass_plugin_manager
@aria.pass_logger
def install(ctx, plugin_path, plugin_manager, logger):
    """Install a plugin

    `PLUGIN_PATH` is the path to wagon archive to install.
    """
    ctx.invoke(validate, plugin_path=plugin_path)
    logger.info('Installing plugin {0}...'.format(plugin_path))
    plugin = plugin_manager.install(plugin_path)
    logger.info("Plugin installed. The plugin's id is {0}".format(plugin.id))


@plugins.command(name='show',
                 short_help='show plugin information')
@aria.argument('plugin-id')
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def show(plugin_id, model_storage, logger):
    """Show information for a specific plugin

    `PLUGIN_ID` is the id of the plugin to show information on.
    """
    logger.info('Showing plugin {0}...'.format(plugin_id))
    plugin = model_storage.plugin.get(plugin_id)
    table.print_data(PLUGIN_COLUMNS, plugin, 'Plugin:')


@plugins.command(name='list',
                 short_help='List plugins')
@aria.options.sort_by('uploaded_at')
@aria.options.descending
@aria.options.verbose()
@aria.pass_model_storage
@aria.pass_logger
def list(sort_by, descending, model_storage, logger):
    """List all plugins on the manager
    """
    logger.info('Listing all plugins...')
    plugins_list = model_storage.plugin.list(
        sort=utils.storage_sort_param(sort_by, descending)).items
    table.print_data(PLUGIN_COLUMNS, plugins_list, 'Plugins:')
