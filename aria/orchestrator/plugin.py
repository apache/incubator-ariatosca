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
Plugin management.
"""

import os
import tempfile
import subprocess
import sys
import zipfile
from datetime import datetime

import wagon

from . import exceptions
from ..utils import process as process_utils

_IS_WIN = os.name == 'nt'


class PluginManager(object):

    def __init__(self, model, plugins_dir):
        """
        :param plugins_dir: root directory in which to install plugins
        """
        self._model = model
        self._plugins_dir = plugins_dir

    def install(self, source):
        """
        Install a wagon plugin.
        """
        metadata = wagon.show(source)
        cls = self._model.plugin.model_cls

        os_props = metadata['build_server_os_properties']

        plugin = cls(
            name=metadata['package_name'],
            archive_name=metadata['archive_name'],
            supported_platform=metadata['supported_platform'],
            supported_py_versions=metadata['supported_python_versions'],
            distribution=os_props.get('distribution'),
            distribution_release=os_props['distribution_version'],
            distribution_version=os_props['distribution_release'],
            package_name=metadata['package_name'],
            package_version=metadata['package_version'],
            package_source=metadata['package_source'],
            wheels=metadata['wheels'],
            uploaded_at=datetime.now()
        )
        if len(self._model.plugin.list(filters={'package_name': plugin.package_name,
                                                'package_version': plugin.package_version})):
            raise exceptions.PluginAlreadyExistsError(
                u'Plugin {0}, version {1} already exists'.format(plugin.package_name,
                                                                 plugin.package_version))
        self._install_wagon(source=source, prefix=self.get_plugin_dir(plugin))
        self._model.plugin.put(plugin)
        return plugin

    def load_plugin(self, plugin, env=None):
        """
        Load the plugin into an environment.

        Loading the plugin means the plugin's code and binaries paths will be appended to the
        environment's ``PATH`` and ``PYTHONPATH``, thereby allowing usage of the plugin.

        :param plugin: plugin to load
        :param env: environment to load the plugin into; If ``None``, :obj:`os.environ` will be
         used
        """
        env = env or os.environ
        plugin_dir = self.get_plugin_dir(plugin)

        # Update PATH environment variable to include plugin's bin dir
        bin_dir = 'Scripts' if _IS_WIN else 'bin'
        process_utils.append_to_path(os.path.join(plugin_dir, bin_dir), env=env)

        # Update PYTHONPATH environment variable to include plugin's site-packages
        # directories
        if _IS_WIN:
            pythonpath_dirs = [os.path.join(plugin_dir, 'Lib', 'site-packages')]
        else:
            # In some linux environments, there will be both a lib and a lib64 directory
            # with the latter, containing compiled packages.
            pythonpath_dirs = [os.path.join(
                plugin_dir, 'lib{0}'.format(b),
                'python{0}.{1}'.format(sys.version_info[0], sys.version_info[1]),
                'site-packages') for b in ('', '64')]

        process_utils.append_to_pythonpath(*pythonpath_dirs, env=env)

    def get_plugin_dir(self, plugin):
        return os.path.join(
            self._plugins_dir,
            '{0}-{1}'.format(plugin.package_name, plugin.package_version))

    @staticmethod
    def validate_plugin(source):
        """
        Validate a plugin archive.

        A valid plugin is a `wagon <http://github.com/cloudify-cosmo/wagon>`__ in the zip format
        (suffix may also be ``.wgn``).
        """
        if not zipfile.is_zipfile(source):
            raise exceptions.InvalidPluginError(
                u'Archive {0} is of an unsupported type. Only '
                u'zip/wgn is allowed'.format(source))
        with zipfile.ZipFile(source, 'r') as zip_file:
            infos = zip_file.infolist()
            try:
                package_name = infos[0].filename[:infos[0].filename.index('/')]
                package_json_path = "{0}/{1}".format(package_name, 'package.json')
                zip_file.getinfo(package_json_path)
            except (KeyError, ValueError, IndexError):
                raise exceptions.InvalidPluginError(
                    u'Failed to validate plugin {0} '
                    u'(package.json was not found in archive)'.format(source))

    def _install_wagon(self, source, prefix):
        pip_freeze_output = self._pip_freeze()
        file_descriptor, constraint_path = tempfile.mkstemp(prefix='constraint-', suffix='.txt')
        os.close(file_descriptor)
        try:
            with open(constraint_path, 'wb') as constraint:
                constraint.write(pip_freeze_output)
            # Install the provided wagon.
            # * The --prefix install_arg will cause the plugin to be installed under
            #   plugins_dir/{package_name}-{package_version}, So different plugins don't step on
            #   each other and don't interfere with the current virtualenv
            # * The --constraint flag points a file containing the output of ``pip freeze``.
            #   It is required, to handle cases where plugins depend on some python package with
            #   a different version than the one installed in the current virtualenv. Without this
            #   flag, the existing package will be **removed** from the parent virtualenv and the
            #   new package will be installed under prefix. With the flag, the existing version will
            #   remain, and the version requested by the plugin will be ignored.
            wagon.install(
                source=source,
                install_args='--prefix="{prefix}" --constraint="{constraint}"'.format(
                    prefix=prefix,
                    constraint=constraint.name),
                venv=os.environ.get('VIRTUAL_ENV'))
        finally:
            os.remove(constraint_path)

    @staticmethod
    def _pip_freeze():
        """Run pip freeze in current environment and return the output"""
        bin_dir = 'Scripts' if os.name == 'nt' else 'bin'
        pip_path = os.path.join(sys.prefix, bin_dir,
                                'pip{0}'.format('.exe' if os.name == 'nt' else ''))
        pip_freeze = subprocess.Popen([pip_path, 'freeze'], stdout=subprocess.PIPE)
        pip_freeze_output, _ = pip_freeze.communicate()
        assert not pip_freeze.poll()
        return pip_freeze_output
