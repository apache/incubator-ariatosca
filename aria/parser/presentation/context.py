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


from .source import DefaultPresenterSource


class PresentationContext(object):
    """
    Properties:

    * :code:`presenter`: The generated presenter instance
    * :code:`location`: From where we will generate the presenter
    * :code:`presenter_source`: For finding presenter classes
    * :code:`presenter_class`: Overrides :code:`presenter_source` with a specific class
    * :code:`import_profile`: Whether to import the profile by default (defaults to true)
    * :code:`threads`: Number of threads to use when reading data
    * :code:`timeout`: Timeout in seconds for loading data
    * :code:`print_exceptions`: Whether to print exceptions while reading data
    """

    def __init__(self):
        self.presenter = None
        self.location = None
        self.presenter_source = DefaultPresenterSource()
        self.presenter_class = None  # overrides
        self.import_profile = True
        self.threads = 8  # reasonable default for networking multithreading
        self.timeout = 10  # in seconds
        self.print_exceptions = False

    def get(self, *names):
        """
        Gets attributes recursively from the presenter.
        """

        return self.presenter._get(*names) if self.presenter is not None else None

    def get_from_dict(self, *names):
        """
        Gets attributes recursively from the presenter, except for the last name which is used
        to get a value from the last dict.
        """

        return self.presenter._get_from_dict(*names) if self.presenter is not None else None
