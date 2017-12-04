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

from ...utils.formatting import safe_repr
from ..loading import UriLocation, LiteralLocation
from ..reading import JsonReader
from .consumer import Consumer


class Inputs(Consumer):
    """
    Fills in the inputs if provided as arguments.
    """

    def consume(self):
        inputs = self.context.get_arg_value('inputs')
        if inputs is None:
            return

        if inputs.endswith('.json') or inputs.endswith('.yaml'):
            location = UriLocation(inputs)
        else:
            location = LiteralLocation(inputs)

        loader = self.context.loading.loader_source.get_loader(self.context.loading, location, None)

        if isinstance(location, LiteralLocation):
            reader = JsonReader(self.context.reading, location, loader)
        else:
            reader = self.context.reading.reader_source.get_reader(self.context.reading,
                                                                   location, loader)

        inputs = reader.read()

        if not isinstance(inputs, dict):
            self.context.validation.report(
                u'Inputs consumer: inputs are not a dict: {0}'.format(safe_repr(inputs)))
            return

        for name, value in inputs.iteritems():
            self.context.modeling.set_input(name, value)
