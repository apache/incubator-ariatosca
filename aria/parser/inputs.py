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

import json
import os

from glob import glob
from ruamel import yaml # @UnresolvedImport

from ..api.cli.exceptions import (
    AriaCliFormatInputsError,
    AriaCliYAMLInputsError,
    AriaCliInvalidInputsError
)


class InputsParser(object):
    """
    Parser of 'inputs' section in blueprint processing.
     Returns a dictionary of inputs `resources` can be:
    - A list of files.
    - A single file
    - A directory containing multiple input files
    - A key1=value1;key2=value2 pairs string.
    - Wildcard based string (e.g. *-inputs.yaml)
    """

    @staticmethod
    def as_dict(inputs, logger):
        if inputs:
            if not isinstance(inputs, dict):
                return InputsParser(logger).parse(inputs)
            else:
                return inputs

        return {}

    def __init__(self, logger):
        self.logger = logger
        self.parsed_dict = {}

    def _handle_inputs_source(self, input_path):
        self.logger.info('Processing inputs source: {0}'.format(input_path))

        try:
            with open(input_path) as input_file:
                content = yaml.safe_load(input_file)
        except yaml.YAMLError as exc:
            raise AriaCliYAMLInputsError(
                '"{0}" is not a valid YAML. {1}'.format(input_path, str(exc)))

        if isinstance(content, dict):
            self.parsed_dict.update(content)
            return
        if content is None:
            return

        raise AriaCliInvalidInputsError('Invalid inputs', inputs=input_path)

    def _format_to_dict(self, input_string):
        self.logger.info('Processing inputs source: {0}'.format(input_string))

        try:
            input_string = input_string.strip()

            try:
                self.parsed_dict.update(json.loads(input_string))
            except BaseException:
                self.parsed_dict.update((
                    i.split('=')
                    for i in input_string.split(';')
                    if i))

        except Exception as exc:
            raise AriaCliFormatInputsError(str(exc), inputs=input_string)

    def parse(self, inputs):
        for input_string in inputs if isinstance(inputs, list) else [inputs]:
            if os.path.isdir(input_string):
                for input_file in os.listdir(input_string):
                    self._handle_inputs_source(os.path.join(input_string, input_file))
                continue

            input_files = glob(input_string)
            if input_files:
                for input_file in input_files:
                    self._handle_inputs_source(input_file)
                continue

            self._format_to_dict(input_string)

        return self.parsed_dict
