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


class AriaCliError(Exception):
    pass


class AriaCliFormatInputsError(AriaCliError):
    def __init__(self, message, inputs):
        self.inputs = inputs
        super(AriaCliFormatInputsError, self).__init__(message)

    def user_message(self):
        return (
            'Invalid input format: {0}, '
            'the expected format is: '
            'key1=value1;key2=value2'.format(self.inputs))


class AriaCliYAMLInputsError(AriaCliError):
    pass


class AriaCliInvalidInputsError(AriaCliFormatInputsError):
    def user_message(self):
        return (
            'Invalid input: {0}. input must represent a dictionary.\n'
            'Valid values can be one of:\n'
            '- a path to a YAML file\n'
            '- a path to a directory containing YAML files\n'
            '- a single quoted wildcard based path (e.g. "*-inputs.yaml")\n'
            '- a string formatted as JSON\n'
            '- a string formatted as key1=value1;key2=value2'.format(self.inputs)
        )
