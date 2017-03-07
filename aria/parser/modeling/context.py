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

import itertools

from ...utils.collections import StrictDict, prune
from ...utils.uuid import generate_uuid


class IdType(object):
    LOCAL_SERIAL = 0
    """
    Locally unique serial ID: a running integer.
    """

    LOCAL_RANDOM = 1
    """
    Locally unique ID: 6 random safe characters.
    """

    UNIVERSAL_RANDOM = 2
    """
    Universally unique ID (UUID): 22 random safe characters.
    """


class ModelingContext(object):
    """
    Properties:

    * :code:`template`: The generated service template
    * :code:`instance`: The generated service instance
    * :code:`node_id_format`: Format for node instance IDs
    * :code:`id_type`: Type of IDs to use for instances
    * :code:`id_max_length`: Maximum allowed instance ID length
    * :code:`inputs`: Dict of inputs values
    """

    def __init__(self):
        self.template = None
        self.instance = None
        self.node_id_format = '{template}_{id}'
        #self.id_type = IdType.LOCAL_SERIAL
        #self.id_type = IdType.LOCAL_RANDOM
        self.id_type = IdType.UNIVERSAL_RANDOM
        self.id_max_length = 63 # See: http://www.faqs.org/rfcs/rfc1035.html
        self.inputs = StrictDict(key_class=basestring)

        self._serial_id_counter = itertools.count(1)
        self._locally_unique_ids = set()

    def store(self, model_storage):
        if self.template is not None:
            model_storage.service_template.put(self.template)
        if self.instance is not None:
            model_storage.service.put(self.instance)

    def generate_node_id(self, template_name):
        return self.node_id_format.format(
            template=template_name,
            id=self.generate_id())

    def generate_id(self):
        if self.id_type == IdType.LOCAL_SERIAL:
            return self._serial_id_counter.next()

        elif self.id_type == IdType.LOCAL_RANDOM:
            the_id = generate_uuid(6)
            while the_id in self._locally_unique_ids:
                the_id = generate_uuid(6)
            self._locally_unique_ids.add(the_id)
            return the_id

        return generate_uuid()

    def set_input(self, name, value):
        self.inputs[name] = value
        # TODO: coerce to validate type

    @property
    def template_as_raw(self):
        raw = self.template.as_raw
        prune(raw)
        return raw

    @property
    def instance_as_raw(self):
        raw = self.instance.as_raw
        prune(raw)
        return raw
