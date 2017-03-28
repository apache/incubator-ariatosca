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
import yaml
import pkg_resources

from jinja2.environment import Template


class CliConfig(object):

    def __init__(self, config_path):
        with open(config_path) as f:
            self._config = yaml.safe_load(f.read())

    @classmethod
    def create_config(cls, workdir):
        config_path = os.path.join(workdir, 'config.yaml')
        if not os.path.isfile(config_path):
            config_template = pkg_resources.resource_string(
                __package__,
                'config_template.yaml')

            default_values = {
                'log_path': os.path.join(workdir, 'cli.log'),
                'enable_colors': True
            }

            template = Template(config_template)
            rendered = template.render(**default_values)
            with open(config_path, 'w') as f:
                f.write(rendered)
                f.write(os.linesep)

        return cls(config_path)

    @property
    def colors(self):
        return self._config.get('colors', False)

    @property
    def logging(self):
        return self.Logging(self._config.get('logging'))

    class Logging(object):

        def __init__(self, logging):
            self._logging = logging or {}

        @property
        def filename(self):
            return self._logging.get('filename')

        @property
        def loggers(self):
            return self._logging.get('loggers', {})
