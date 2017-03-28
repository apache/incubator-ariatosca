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
import tempfile
import subprocess
import sys
from datetime import datetime

import wagon

from . import exceptions


class PluginManager(object):

    def __init__(self, model, plugins_dir):
        """
        :param plugins_dir: Root directory to install plugins in.
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
                'Plugin {0}, version {1} already exists'.format(plugin.package_name,
                                                                plugin.package_version))
        self._install_wagon(source=source, prefix=self.get_plugin_prefix(plugin))
        self._model.plugin.put(plugin)
        return plugin

    def get_plugin_prefix(self, plugin):
        return os.path.join(
            self._plugins_dir,
            '{0}-{1}'.format(plugin.package_name, plugin.package_version))

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
